# =============================================================================
# Dialogue Registry
# -----------------------------------------------------------------------------
# Mixed authoring:
#   - Data entries for repeatable talk pools.
#   - Normal Ren'Py labels for longer scenes, choices, interactions, quests.
#
# Talk kinds:
#   fact  -> blocked for 5 days after seen.
#   extra -> blocked for 3 days after seen.
#   basic -> always reusable fallback, used when richer talk is exhausted.
# =============================================================================


default character_talk_seen = {}


init -60 python:
    character_talk_entries = {}
    character_interact_entries = {}


init python:

    def _as_list(v):
        if v is None:
            return None
        if isinstance(v, (list, tuple, set)):
            return list(v)
        return [v]

    def _current_tod():
        try:
            return get_time_of_day(time)
        except Exception:
            return "day"

    def _entry_matches(entry, char):
        locs = _as_list(entry.get("locations"))
        if locs is not None and current_location not in locs:
            return False
        times = _as_list(entry.get("times"))
        if times is not None and _current_tod() not in times:
            return False
        moods = _as_list(entry.get("moods"))
        if moods is not None:
            try:
                if mood_state(char) not in moods and mood(char) not in moods:
                    return False
            except Exception:
                return False
        avail = entry.get("available_if")
        if avail is not None:
            try:
                if not avail():
                    return False
            except Exception:
                return False
        return True

    def _talk_cooldown(entry):
        if entry.get("cooldown_days") is not None:
            return int(entry.get("cooldown_days"))
        kind = entry.get("kind", "basic")
        if kind == "fact":
            return 5
        if kind == "extra":
            return 3
        return 0

    def _talk_seen_key(char, entry):
        return (char, entry.get("id"))

    def _talk_available_by_cooldown(char, entry):
        cd = _talk_cooldown(entry)
        if cd <= 0:
            return True
        try:
            today = day
        except Exception:
            today = 0
        last = character_talk_seen.get(_talk_seen_key(char, entry))
        return last is None or (today - last) >= cd

    def _upsert_registry_entry(registry, char, entry):
        entries = registry.setdefault(char, [])
        entry_id = entry.get("id")
        for i, old in enumerate(entries):
            if old.get("id") == entry_id:
                entries[i] = entry
                return entry
        entries.append(entry)
        return entry

    def register_character_talk(
        char,
        id,
        kind="basic",
        line=None,
        label=None,
        locations=None,
        times=None,
        moods=None,
        available_if=None,
        cooldown_days=None,
        weight=1,
    ):
        entry = {
            "id": id,
            "kind": kind,
            "line": line,
            "label": label,
            "locations": locations,
            "times": times,
            "moods": moods,
            "available_if": available_if,
            "cooldown_days": cooldown_days,
            "weight": weight,
        }
        return _upsert_registry_entry(character_talk_entries, char, entry)

    def register_character_interact(
        char,
        id,
        label,
        locations=None,
        times=None,
        moods=None,
        available_if=None,
        priority=0,
    ):
        entry = {
            "id": id,
            "label": label,
            "locations": locations,
            "times": times,
            "moods": moods,
            "available_if": available_if,
            "priority": priority,
        }
        return _upsert_registry_entry(character_interact_entries, char, entry)

    def choose_character_talk(char):
        entries = [e for e in character_talk_entries.get(char, []) if _entry_matches(e, char)]
        rich = [e for e in entries if e.get("kind") != "basic" and _talk_available_by_cooldown(char, e)]
        if rich:
            return renpy.random.choice(rich)
        basics = [e for e in entries if e.get("kind") == "basic"]
        if basics:
            return renpy.random.choice(basics)
        fallback_label = "talk_" + char
        if renpy.has_label(fallback_label):
            return {"id": "legacy_" + char, "kind": "basic", "label": fallback_label}
        return None

    def mark_character_talk_seen(char, entry):
        if not entry or not entry.get("id"):
            return
        try:
            today = day
        except Exception:
            today = 0
        character_talk_seen[_talk_seen_key(char, entry)] = today

    def character_talk_exhausted(char):
        for e in character_talk_entries.get(char, []):
            if e.get("kind") == "basic":
                continue
            if _entry_matches(e, char) and _talk_available_by_cooldown(char, e):
                return False
        return True

    def character_has_seen_basic_talk(char):
        for e in character_talk_entries.get(char, []):
            if e.get("kind") != "basic":
                continue
            if character_talk_seen.get(_talk_seen_key(char, e)) is not None:
                return True
        return False

    def character_has_any_talk(char):
        entries = [e for e in character_talk_entries.get(char, []) if _entry_matches(e, char)]
        if not entries:
            fallback_label = "talk_" + char
            return bool(renpy.has_label(fallback_label))
        rich = [e for e in entries if e.get("kind") != "basic" and _talk_available_by_cooldown(char, e)]
        if rich:
            return True
        basics = [e for e in entries if e.get("kind") == "basic"]
        return bool(basics)

    def character_interact_label(char):
        entries = [e for e in character_interact_entries.get(char, []) if _entry_matches(e, char)]
        if entries:
            entries.sort(key=lambda e: e.get("priority", 0), reverse=True)
            return entries[0].get("label")
        label = "interact_" + char
        return label if renpy.has_label(label) else None

    def character_quest_label(char):
        target = current_quest_target_for(char) or {}
        if target.get("label"):
            return target.get("label")
        label = "quest_" + char
        return label if renpy.has_label(label) else None

    def say_character(char, line):
        try:
            speaker = character_speakers.get(char)
        except Exception:
            speaker = None
        if speaker is not None:
            renpy.say(speaker, line)
        else:
            renpy.say(None, line)
