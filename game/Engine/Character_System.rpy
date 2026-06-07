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
    RELATIONSHIP_STATS = ("love", "lust", "trust", "respect")
    MOOD_AXES = ("happy", "sad", "angry", "nervous")
    REACTION_TAGS = ("embarrassed", "jealous", "shy", "confused", "confident")
    STATUS_TAGS = ("tired", "sick", "hurt")

    def ensure_character_state(char):
        d = character_stats.setdefault(char, {})
        for stat_name in RELATIONSHIP_STATS:
            d.setdefault(stat_name, 0)
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
            reactions.setdefault(reaction_name, False)
        statuses = d.setdefault("statuses", {})
        if not isinstance(statuses, dict):
            statuses = {}
            d["statuses"] = statuses
        for status_name in STATUS_TAGS:
            statuses.setdefault(status_name, 0)
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
            new = cur + amount
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
            if amount > 0 and stat in ("love", "lust"):
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
