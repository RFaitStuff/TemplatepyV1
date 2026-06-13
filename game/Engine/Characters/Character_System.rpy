# Character engine internals. User-authored character data lives in Game/Characters/Characters.rpy.

# Choice records and reward cooldowns.
default character_choices = {}
default character_choice_counters = {}
default _reward_log = {}
default _reward_once_ever = set()
default _last_speaker = None

# =============================================================================
# Character factory + Character objects
# =============================================================================
init -25 python:
    perk_defs = {}

    def _player_stat_defs():
        global PLAYER_STAT_DEFS
        try:
            PLAYER_STAT_DEFS
        except NameError:
            PLAYER_STAT_DEFS = {}
        return PLAYER_STAT_DEFS

    def stat_def(stat_id, label=None, default=0, icon=None, color=None, min=0, max=None, hidden=False, aliases=None, **extra):
        data = _player_stat_defs().setdefault(stat_id, {})
        data.update({
            "id": stat_id,
            "label": label or stat_id,
            "default": default if default is not None else data.get("default", 0),
            "icon": icon,
            "color": color,
            "min": min,
            "max": max,
            "hidden": bool(hidden),
            "aliases": list(aliases or []),
        })
        data.update(extra)
        return data

    def perk(perk_id, stat=None, requires=None, title=None, desc=None, **extra):
        data = perk_defs.setdefault(perk_id, {})
        if requires is None and stat:
            requires = "{}>=1".format(stat)
        data.update({
            "id": perk_id,
            "title": title or str(perk_id).replace("_", " ").title(),
            "desc": desc or "",
            "stat": stat,
            "requires": requires,
        })
        data.update(extra)
        return data


init -5 python:

    def tracked_character(name, char_id, **kwargs):
        """Character wrapper that auto-tags itself as the last speaker.
        Used so menus can auto-record choices and player stat gains can be
        attributed to whoever caused them."""
        def _cb(event, **k):
            if event == "begin":
                store._last_speaker = char_id
                try:
                    dialogue_ensure_speaker(char_id)
                except Exception:
                    pass
        return Character(name, callback=_cb, **kwargs)


# =============================================================================
# Helpers
# =============================================================================
init python:

    import re as _re
    _CD_RE = _re.compile(r"^(?:(\d+)d(a)?|(no)(a)?)$", _re.IGNORECASE)
    RELATIONSHIP_STATS = tuple(CHARACTER_STAT_DEFS.keys())
    MOOD_AXES = tuple(MOOD_DEFS.keys())
    REACTION_TAGS = tuple(REACTION_DEFS.keys())
    STATUS_TAGS = tuple(STATUS_DEFS.keys())

    def ensure_character_state(char):
        d = character_stats.setdefault(char, {})
        for stat_name in RELATIONSHIP_STATS:
            d.setdefault(stat_name, CHARACTER_STAT_DEFS.get(stat_name, {}).get("default", 0))
        moods = d.setdefault("moods", {})
        if not isinstance(moods, dict):
            moods = {}
            d["moods"] = moods
        for mood_name in MOOD_AXES:
            moods.setdefault(mood_name, 0)
        reactions = d.setdefault("reactions", {})
        if not isinstance(reactions, dict):
            reactions = {}
            d["reactions"] = reactions
        for reaction_name in REACTION_TAGS:
            reactions.setdefault(reaction_name, REACTION_DEFS.get(reaction_name, {}).get("default", False))
        statuses = d.setdefault("statuses", {})
        if not isinstance(statuses, dict):
            statuses = {}
            d["statuses"] = statuses
        for status_name in STATUS_TAGS:
            statuses.setdefault(status_name, STATUS_DEFS.get(status_name, {}).get("default", 0))
        unlocked_character_facts.setdefault(char, set())
        return d

    def ensure_all_character_states():
        for char in list(character_stats.keys()):
            ensure_character_state(char)


    # ---- stats -----------------------------------------------------------
    def char_stat(char, stat, default=0):
        if char != "player":
            ensure_character_state(char)
        return character_stats.get(char, {}).get(stat, default)

    def set_stat(char, stat, value):
        if char == "player":
            value = clamp_player_stat(stat, value)
        if char == "player":
            setattr(store, stat, value)
        else:
            ensure_character_state(char)[stat] = value

    def _apply_stat_delta(char, stat, amount, source=None):
        # Add `amount` to a stat (negative removes).
        # For player stats, also bumps a source-tagged mirror stat
        # (e.g. AliceLust) so you can see who contributed. `source` defaults
        # to the most recent speaker; pass source=False to disable tagging.
        if amount == 0:
            return
        if char == "player":
            cur = getattr(store, stat, 0)
            new = clamp_player_stat(stat, cur + amount)
            setattr(store, stat, new)
            if source is None:
                source = store._last_speaker
            if source:
                tagged = source[:1].upper() + source[1:] + stat
                cur_t = getattr(store, tagged, 0)
                setattr(store, tagged, cur_t + amount)
            try:
                emit("stat_changed", "player", stat, amount, new, source=source)
            except NameError:
                pass
        else:
            d = ensure_character_state(char)
            new = d.get(stat, 0) + amount
            d[stat] = new
            # Trigger HUD Characters-button glow when love or lust grow.
            if amount > 0 and stat in RELATIONSHIP_STATS:
                try:
                    _hud_trigger_char_glow(stat)
                except NameError:
                    pass
            try:
                emit("stat_changed", char, stat, amount, new)
            except NameError:
                pass

    def _parse_cd_token(tok):
        """Return (cd_value, is_global) or None. cd_value is int days or 'no'."""
        if not isinstance(tok, str):
            return None
        m = _CD_RE.match(tok.strip())
        if not m:
            return None
        if m.group(3):
            return ("no", bool(m.group(4)))
        return (int(m.group(1)), bool(m.group(2)))

    def stat(char, *args, **kwargs):
        """Add (or remove) one or more stats in a single call, with optional
        cooldowns. Works for character stats AND player stats.

        Forms (all valid):
            stat("alice", "lust", 1)
            stat("alice", "lust", 1, "love", 1)
            stat("alice", "lust", -1)                  # negative removes
            stat("alice", "lust", 1, "3d")             # 3d cooldown for lust
            stat("alice", "lust", 1, "3d", "love", 1, "2d")
            stat("alice", "lust", 1, "love", 1, "3da")  # 3d for ALL
            stat("alice", "lust", 1, "no")             # once ever for lust
            stat("alice", "lust", 1, "love", 1, "noa")  # once ever, all
            stat("player", "Strength", 1)              # player stats too

        Cooldown grammar:
            "<N>d"   per-stat:  cooldown of N in-game days for THIS stat
            "<N>da"  global:    cooldown of N days for EVERY stat in this call
            "no"     per-stat:  grant only once ever (per stat, per playthrough)
            "noa"    global:    grant once ever for every stat in this call

        Optional kwargs:
            source="alex"   force player-stat source tag (default: last speaker)
            source=False      disable source-tag mirroring entirely

        Returns list of (stat, applied_bool).
        """
        source = kwargs.get("source", None)

        # Pre-scan for global cooldown token.
        global_cd = None
        for a in args:
            p = _parse_cd_token(a)
            if p is not None and p[1]:
                global_cd = p[0]
                break

        items = []          # (stat, amount, per_item_cd_or_None)
        i = 0
        while i < len(args):
            stat = args[i]
            amount = args[i + 1] if i + 1 < len(args) else 0
            i += 2
            cd = None
            if i < len(args):
                p = _parse_cd_token(args[i])
                if p is not None:
                    if not p[1]:
                        cd = p[0]
                    i += 1
            items.append((stat, amount, cd))

        results = []
        for stat, amount, cd in items:
            effective = cd if cd is not None else global_cd
            applied = False
            if effective is None:
                _apply_stat_delta(char, stat, amount, source=source)
                applied = True
            elif effective == "no":
                if reward_once_ever(char, stat):
                    _apply_stat_delta(char, stat, amount, source=source)
                    applied = True
            else:
                if reward_once(char, stat, effective):
                    _apply_stat_delta(char, stat, amount, source=source)
                    applied = True
            results.append((stat, applied))
        return results

    # Backward-compat alias.
    def add_stat(char, *args, **kwargs):
        return stat(char, *args, **kwargs)

    def register_character_fact(char, fact_id, label, text):
        facts = character_fact_defs.setdefault(char, [])
        for fact in facts:
            if fact.get("id") == fact_id:
                fact["label"] = label
                fact["text"] = text
                return None
        facts.append({"id": fact_id, "label": label, "text": text})
        return None

    def unlock_character_fact(char, fact_id):
        ensure_character_state(char)
        unlocked_character_facts.setdefault(char, set()).add(fact_id)
        return None

    def lock_character_fact(char, fact_id):
        unlocked_character_facts.setdefault(char, set()).discard(fact_id)
        return None

    def character_fact_unlocked(char, fact_id):
        return fact_id in unlocked_character_facts.get(char, set())

    def character_fact_rows(char):
        rows = []
        for fact in character_fact_defs.get(char, []):
            fid = fact.get("id")
            unlocked = character_fact_unlocked(char, fid)
            rows.append({
                "id": fid,
                "label": fact.get("label", fid),
                "text": fact.get("text", "???") if unlocked else "???",
                "unlocked": unlocked,
            })
        return rows

    def set_reaction(char, reaction_name, active=True):
        if reaction_name not in REACTION_TAGS:
            return None
        ensure_character_state(char)["reactions"][reaction_name] = bool(active)
        return None

    def clear_reaction(char, reaction_name=None):
        ensure_character_state(char)
        if reaction_name is None:
            for name in REACTION_TAGS:
                character_stats[char]["reactions"][name] = False
        elif reaction_name in REACTION_TAGS:
            character_stats[char]["reactions"][reaction_name] = False
        return None

    def active_reactions(char):
        ensure_character_state(char)
        reactions = character_stats.get(char, {}).get("reactions", {})
        return [name for name in REACTION_TAGS if reactions.get(name)]

    def set_status(char, status_name, value=True):
        if status_name not in STATUS_TAGS:
            return None
        ensure_character_state(char)["statuses"][status_name] = value
        return None

    def clear_status(char, status_name):
        if status_name in STATUS_TAGS:
            ensure_character_state(char)["statuses"][status_name] = 0
        return None

    def active_statuses(char):
        ensure_character_state(char)
        statuses = character_stats.get(char, {}).get("statuses", {})
        return [(name, statuses.get(name)) for name in STATUS_TAGS if statuses.get(name)]

    def character_display_name(char_id):
        # Return the display name from the Character() object if available,
        # otherwise capitalize the id. Used by hover bubbles and similar UI.
        try:
            c = character_speakers.get(char_id)
        except Exception:
            c = None
        if c is None:
            c = getattr(store, char_id, None)
        nm = getattr(c, "name", None) if c is not None else None
        if isinstance(nm, str) and nm:
            return nm
        return char_id[:1].upper() + char_id[1:]

    def player_stat_breakdown(stat):
        """Inspect how much of a player stat each character contributed.
        Returns {source_id: amount, "<total>": total}."""
        out = {}
        total = getattr(store, stat, 0)
        for char in list(character_stats.keys()):
            tagged = char[:1].upper() + char[1:] + stat
            v = getattr(store, tagged, 0)
            if v:
                out[char] = v
        out["<total>"] = total
        return out

    def player_stat_def(stat):
        return (globals().get("PLAYER_STAT_DEFS", {}) or {}).get(stat, {})

    def clamp_player_stat(stat, value):
        data = player_stat_def(stat)
        try:
            value = int(value)
        except Exception:
            value = 0
        if data.get("min") is not None:
            value = max(int(data.get("min")), value)
        if data.get("max") is not None:
            value = min(int(data.get("max")), value)
        return value

    def perk_unlocked(perk_id):
        data = perk_defs.get(perk_id)
        if not data:
            return False
        requires = data.get("requires")
        if not requires:
            return True
        try:
            return meets_requirements(requires)
        except Exception:
            return False

    def active_perks(stat=None):
        rows = []
        for perk_id, data in perk_defs.items():
            if stat and data.get("stat") != stat:
                continue
            if perk_unlocked(perk_id):
                rows.append(data)
        rows.sort(key=lambda item: item.get("title", item.get("id", "")))
        return rows

    def perk_rows(stat=None, include_locked=True):
        rows = []
        for perk_id, data in perk_defs.items():
            if stat and data.get("stat") != stat:
                continue
            unlocked = perk_unlocked(perk_id)
            if not unlocked and not include_locked:
                continue
            row = dict(data)
            row["unlocked"] = unlocked
            row["requirement_text"] = str(data.get("requires") or "")
            rows.append(row)
        rows.sort(key=lambda item: (not item.get("unlocked"), item.get("title", item.get("id", ""))))
        return rows


    # ---- response randomization & mood-gated lines ----------------------
    def rline(*lines):
        return renpy.random.choice(lines) if lines else ""

    def mline(char, default=None, **moods_to_lines):
        """Pick a line based on `char`'s current dominant mood.
        Falls back to `default` if the mood has no specific bucket.

            mline("alice", default=["Hi."], happy=["Yo!"], sad=["...hi."])
        """
        m = mood(char)
        opts = moods_to_lines.get(m)
        if opts is None:
            for name in active_reactions(char):
                if name in moods_to_lines:
                    opts = moods_to_lines.get(name)
                    break
        if opts is None:
            for name, value in active_statuses(char):
                if name in moods_to_lines:
                    opts = moods_to_lines.get(name)
                    break
        if opts is None:
            opts = default
        if opts is None:
            return ""
        if isinstance(opts, (list, tuple)):
            return renpy.random.choice(opts)
        return opts


    # ---- reward cooldowns ------------------------------------------------
    def reward_once(char, key, cooldown_days=1):
        """True the first call and once every `cooldown_days` thereafter."""
        try:
            today = day
        except NameError:
            today = 0
        last = _reward_log.get((char, key))
        if last is None or (today - last) >= cooldown_days:
            _reward_log[(char, key)] = today
            return True
        return False

    def reward_once_ever(char, key):
        """True only the first time this (char, key) pair is asked."""
        k = (char, key)
        if k in _reward_once_ever:
            return False
        _reward_once_ever.add(k)
        return True


    # ---- schedule lookup -------------------------------------------------
    def npc_location(char):
        """Where is `char` right now according to their schedule? Or None."""
        if not system_enabled("schedules"):
            return None
        try:
            tod = get_time_of_day(time)
        except NameError:
            tod = "day"
        return character_schedules.get(char, {}).get(tod)

    def is_npc_here(char):
        """Is `char` in the player's current location?"""
        return npc_location(char) == current_location

    def npcs_here():
        """List of every NPC currently in the player's location (by id)."""
        return [c for c in character_schedules if is_npc_here(c)]


    # ---- choice tracker --------------------------------------------------
    def choose(char, answer, branch=None, qid=None):
        """Manually record a choice. Usually unnecessary - the auto-recorder
        handles this for you whenever a menu follows a character's line."""
        if qid is None:
            n = character_choice_counters.get(char, 0) + 1
            character_choice_counters[char] = n
            qid = str(n)
            if branch is not None:
                qid = "%s.%s" % (qid, branch)
        entry = "%s-%s" % (qid, answer)
        character_choices.setdefault(char, []).append(entry)
        return entry

    def has_chosen(char, entry):
        return entry in character_choices.get(char, [])

    def chose_answer(char, qid, answer):
        return has_chosen(char, "%s-%s" % (qid, answer))

    def choices_for(char):
        return list(character_choices.get(char, []))

    def reset_choices(char=None):
        if char is None:
            character_choices.clear()
            character_choice_counters.clear()
        else:
            character_choices.pop(char, None)
            character_choice_counters.pop(char, None)

    # Called from the choice screen override - records the picked option index
    # for whichever character spoke most recently.
    def _auto_record_choice(idx):
        char = store._last_speaker
        if char:
            choose(char, idx)


    # ---- validation ------------------------------------------------------
    def _character_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _character_requirement_valid(requirements):
        if requirements in (None, "", {}, [], ()):
            return True
        try:
            return first_missing_requirement(requirements) is None
        except Exception:
            return False

    def _schedule_locations_from_value(value):
        if value in (None, ""):
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple, set)):
            out = []
            for item in value:
                out.extend(_schedule_locations_from_value(item))
            return out
        if isinstance(value, dict):
            out = []
            for key in ("location", "loc", "to"):
                out.extend(_schedule_locations_from_value(value.get(key)))
            for key in ("locations", "choices", "options"):
                out.extend(_schedule_locations_from_value(value.get(key)))
            for key in ("default", "fallback"):
                out.extend(_schedule_locations_from_value(value.get(key)))
            for rule in value.get("rules", []) or []:
                out.extend(_schedule_locations_from_value(rule))
            return out
        return []

    def character_validation_issues():
        issues = []
        locations_data = globals().get("locations", {}) or {}
        schedules = globals().get("character_schedules", {}) or {}
        speakers = globals().get("character_speakers", {}) or {}
        character_data = globals().get("character_stats", {}) or {}
        known_locations = set(locations_data.keys())
        known_chars = set(character_data.keys()) | set(speakers.keys()) | set(schedules.keys()) | set((globals().get("character_fact_defs", {}) or {}).keys())
        known_times = set(("day", "afternoon", "evening", "night", "midnight", "morning"))

        for stat_id, data in (globals().get("CHARACTER_STAT_DEFS", {}) or {}).items():
            if not isinstance(data, dict):
                issues.append("Character stat '{}' should be a dictionary definition.".format(stat_id))
                continue
            if not _character_number(data.get("default", 0)):
                issues.append("Character stat '{}' has a non-numeric default.".format(stat_id))
            if data.get("min") is not None and not _character_number(data.get("min")):
                issues.append("Character stat '{}' has a non-numeric min.".format(stat_id))
            if data.get("max") is not None and not _character_number(data.get("max")):
                issues.append("Character stat '{}' has a non-numeric max.".format(stat_id))
            if data.get("min") is not None and data.get("max") is not None and _character_number(data.get("min")) and _character_number(data.get("max")) and data.get("max") < data.get("min"):
                issues.append("Character stat '{}' has max lower than min.".format(stat_id))

        for mood_id, data in (globals().get("MOOD_DEFS", {}) or {}).items():
            if not isinstance(data, dict):
                issues.append("Mood '{}' should be a dictionary definition.".format(mood_id))
                continue
            if not _character_number(data.get("default", 0)):
                issues.append("Mood '{}' has a non-numeric default.".format(mood_id))
            if not _character_number(data.get("priority", 0)):
                issues.append("Mood '{}' has a non-numeric priority.".format(mood_id))
            for limit_key in ("min", "max"):
                if data.get(limit_key) is not None and not _character_number(data.get(limit_key)):
                    issues.append("Mood '{}' has a non-numeric {}.".format(mood_id, limit_key))

        known_moods = set((globals().get("MOOD_DEFS", {}) or {}).keys())
        for mood_id, rows in (globals().get("MOOD_INCOMPAT", {}) or {}).items():
            if mood_id not in known_moods:
                issues.append("Mood incompatibility references unknown mood '{}'.".format(mood_id))
            for other_id, amount in (rows or {}).items():
                if other_id not in known_moods:
                    issues.append("Mood incompatibility '{} -> {}' references an unknown mood.".format(mood_id, other_id))
                if not _character_number(amount):
                    issues.append("Mood incompatibility '{} -> {}' has a non-numeric amount.".format(mood_id, other_id))

        for stat_id, data in (globals().get("PLAYER_STAT_DEFS", {}) or {}).items():
            if not isinstance(data, dict):
                issues.append("Player stat '{}' should be a dictionary definition.".format(stat_id))
                continue
            if not _character_number(data.get("default", 0)):
                issues.append("Player stat '{}' has a non-numeric default.".format(stat_id))
            if data.get("min") is not None and not _character_number(data.get("min")):
                issues.append("Player stat '{}' has a non-numeric min.".format(stat_id))
            if data.get("max") is not None and not _character_number(data.get("max")):
                issues.append("Player stat '{}' has a non-numeric max.".format(stat_id))
            if data.get("aliases") is not None and not isinstance(data.get("aliases"), (list, tuple, set)):
                issues.append("Player stat '{}' aliases should be a list.".format(stat_id))

        for cid in sorted(known_chars):
            if cid not in speakers:
                issues.append("Character '{}' has no speaker in character_speakers.".format(cid))
            if cid not in character_data:
                issues.append("Character '{}' has no character_stats entry.".format(cid))
            if cid not in schedules:
                issues.append("Character '{}' has no schedule entry.".format(cid))

        for cid, stats in character_data.items():
            if not isinstance(stats, dict):
                issues.append("character_stats['{}'] should be a dictionary.".format(cid))
                continue
            for stat_id in stats.keys():
                if stat_id in ("moods", "reactions", "statuses"):
                    continue
                if stat_id not in (globals().get("CHARACTER_STAT_DEFS", {}) or {}):
                    issues.append("Character '{}' uses unknown stat '{}'.".format(cid, stat_id))

        for cid, rows in schedules.items():
            if not isinstance(rows, dict):
                issues.append("Schedule for '{}' should be a dictionary.".format(cid))
                continue
            for time_id, value in rows.items():
                if str(time_id) not in known_times:
                    issues.append("Schedule for '{}' uses unknown time bucket '{}'.".format(cid, time_id))
                for loc_id in _schedule_locations_from_value(value):
                    if loc_id and loc_id not in known_locations:
                        issues.append("Schedule for '{}' at '{}' points to missing location '{}'.".format(cid, time_id, loc_id))

        for cid, rows in (globals().get("character_fact_defs", {}) or {}).items():
            seen = set()
            for index_value, fact in enumerate(rows or []):
                if not isinstance(fact, dict):
                    issues.append("Character fact {}[{}] should be a dictionary.".format(cid, index_value))
                    continue
                fid = fact.get("id")
                if not fid:
                    issues.append("Character fact {}[{}] is missing id.".format(cid, index_value))
                elif fid in seen:
                    issues.append("Character '{}' has duplicate fact id '{}'.".format(cid, fid))
                seen.add(fid)
                if not fact.get("label"):
                    issues.append("Character fact '{}.{}' is missing label.".format(cid, fid or index_value))

        player_stats = set((globals().get("PLAYER_STAT_DEFS", {}) or {}).keys())
        for perk_id, data in (globals().get("perk_defs", {}) or {}).items():
            if not isinstance(data, dict):
                issues.append("Perk '{}' should be a dictionary definition.".format(perk_id))
                continue
            stat_id = data.get("stat")
            if stat_id and stat_id not in player_stats:
                issues.append("Perk '{}' references unknown player stat '{}'.".format(perk_id, stat_id))
            if not _character_requirement_valid(data.get("requires")):
                issues.append("Perk '{}' has invalid requirements '{}'.".format(perk_id, data.get("requires")))

        return issues


init 999 python:
    try:
        register_project_tac_validator(character_validation_issues)
    except Exception:
        pass
