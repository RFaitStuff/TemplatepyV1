# =============================================================================
# Requirement Helpers
# -----------------------------------------------------------------------------
# One shared requirement language for locations, interactables, dialogue,
# choices, quests, items, gallery, and UI feedback.
#
# Writer-facing examples:
#   req("flag:noticeboard_done", "Alice.Love>=10", "stat:Coolness>=10")
#   can("item:library_key", "quest_done:noticeboard_intro")
#   requirement_summary(req("time:afternoon|evening", "no_item:flyer"))
#
# Advanced dictionary form is also supported:
#   {"flags": ["intro_done"], "stats": {"Coolness": 10}}
# =============================================================================

init -85 python:

    import re as _req_re

    _REQ_COMPARE_RE = _req_re.compile(r"^(.+?)(>=|<=|==|!=|>|<)(.+)$")

    def req(*rules):
        """Return a compact requirement list.

        Keeping this as a plain list makes it easy to pass into existing Ren'Py
        data structures and keeps debugging readable.
        """
        if len(rules) == 1 and isinstance(rules[0], (list, tuple, set)):
            return list(rules[0])
        return list(rules)

    def can(*rules, **kwargs):
        """Short choice/menu helper."""
        actor = kwargs.get("actor", None)
        if len(rules) == 1:
            return meets_requirements(rules[0], actor=actor)
        return meets_requirements(req(*rules), actor=actor)

    def _req_as_list(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    def _req_str(value):
        try:
            return str(value).strip()
        except Exception:
            return ""

    def _req_norm_id(value):
        return _req_str(value).strip().lower().replace(" ", "_")

    def _req_display_id(value):
        return _req_str(value).replace("_", " ").title()

    def _req_int(value, default=0):
        try:
            return int(value)
        except Exception:
            try:
                return int(float(value))
            except Exception:
                return default

    def _req_compare(left, op, right):
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == "!=":
            return left != right
        return left == right

    def _req_player_stat_value(stat_name):
        # Player stats are currently default variables such as Coolness.
        if hasattr(store, stat_name):
            return getattr(store, stat_name, 0)
        # Allow forgiving case-insensitive lookup.
        try:
            for key, data in PLAYER_STAT_DEFS.items():
                if key.lower() == stat_name.lower():
                    return getattr(store, key, 0)
                aliases = data.get("aliases", []) if isinstance(data, dict) else []
                for alias in aliases:
                    if str(alias).lower() == stat_name.lower():
                        return getattr(store, key, 0)
        except Exception:
            pass
        return getattr(store, stat_name[:1].upper() + stat_name[1:], 0)

    def _req_char_id(name, actor=None):
        if name in (None, "", "self", "actor"):
            return actor
        raw = _req_str(name)
        norm = _req_norm_id(raw)
        try:
            if norm in character_stats:
                return norm
            for cid in character_stats.keys():
                try:
                    if character_display_name(cid).lower() == raw.lower():
                        return cid
                except Exception:
                    pass
        except Exception:
            pass
        return norm

    def _req_char_stat_value(char_name, stat_name, actor=None):
        cid = _req_char_id(char_name, actor=actor)
        if cid in ("player", "mc"):
            return _req_player_stat_value(stat_name)
        stat_id = _req_norm_id(stat_name)
        try:
            return char_stat(cid, stat_id)
        except Exception:
            try:
                return character_stats.get(cid, {}).get(stat_id, 0)
            except Exception:
                return 0

    def _req_mood_value(char_name, mood_name, actor=None):
        cid = _req_char_id(char_name, actor=actor)
        mood_id = _req_norm_id(mood_name)
        try:
            return character_stats.get(cid, {}).get("moods", {}).get(mood_id, 0)
        except Exception:
            return 0

    def _req_has_flag(flag):
        try:
            return has_flag(flag)
        except Exception:
            try:
                return flag in story_flags
            except Exception:
                return False

    def _req_quest_state(qid):
        try:
            q = quest(qid)
            return q.state if q else "inactive"
        except Exception:
            try:
                return _quest_state(qid).get("state", "inactive")
            except Exception:
                return "inactive"

    def _req_quest_discovered(qid):
        try:
            q = quest(qid)
            return bool(q and q.is_discovered)
        except Exception:
            try:
                return bool(_quest_state(qid).get("discovered", False))
            except Exception:
                return False

    def _req_quest_step_done(text):
        qid, sep, oid = _req_str(text).partition(".")
        if not sep:
            qid, sep, oid = _req_str(text).partition(":")
        if not qid or not oid:
            return False
        try:
            q = quest(qid)
            if q:
                obj = q.get(oid)
                return bool(obj and obj.done)
        except Exception:
            pass
        try:
            return oid in set(_quest_state(qid).get("done", []))
        except Exception:
            return False

    def _req_current_time_bucket():
        try:
            return get_time_of_day(time)
        except Exception:
            try:
                h = int(time)
                if h < 6:
                    return "night"
                if h < 12:
                    return "morning"
                if h < 18:
                    return "afternoon"
                if h < 22:
                    return "evening"
                return "night"
            except Exception:
                return "day"

    def _req_item_has_tag(item_id, tag):
        try:
            tags = item_defs.get(item_id, {}).get("tags", [])
            return tag in tags
        except Exception:
            return False

    def _req_eval_compare_rule(rule, actor=None):
        m = _REQ_COMPARE_RE.match(rule)
        if not m:
            return None
        left = m.group(1).strip()
        op = m.group(2)
        right_text = m.group(3).strip()
        right = _req_int(right_text, 0)

        if left.lower().startswith("stat:"):
            value = _req_player_stat_value(left.split(":", 1)[1].strip())
            return _req_compare(value, op, right)

        if left.lower().startswith("day"):
            try:
                value = int(day)
            except Exception:
                value = 1
            return _req_compare(value, op, right)

        if left.lower().startswith("hour") or left.lower().startswith("time"):
            try:
                value = int(time)
            except Exception:
                value = 0
            return _req_compare(value, op, right)

        if "." in left:
            char_name, stat_name = left.split(".", 1)
            value = _req_char_stat_value(char_name, stat_name, actor=actor)
            return _req_compare(value, op, right)

        # Bare player stat: "Coolness>=10".
        value = _req_player_stat_value(left)
        return _req_compare(value, op, right)

    def _req_eval_string(rule, actor=None):
        raw = _req_str(rule)
        if not raw:
            return True

        compared = _req_eval_compare_rule(raw, actor=actor)
        if compared is not None:
            return compared

        key, sep, value = raw.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if not sep:
            return _req_has_flag(raw)

        if key in ("flag", "has_flag"):
            return _req_has_flag(value)
        if key in ("blocked_by_flag", "blocked_by_flags", "unless", "no_flag"):
            return not _req_has_flag(value)
        if key in ("item", "has_item"):
            item_id, _, count = value.partition(">=")
            return has_item(item_id.strip(), _req_int(count, 1))
        if key == "no_item":
            return not has_item(value)
        if key == "tag":
            try:
                return any(_req_item_has_tag(iid, value) for iid, count in inventory_list())
            except Exception:
                return False
        if key in ("quest_done", "quest_completed"):
            return _req_quest_state(value) == "completed"
        if key == "quest_active":
            return _req_quest_state(value) == "active"
        if key in ("quest_started", "quest_unlocked"):
            return _req_quest_state(value) in ("active", "completed", "failed") or _req_quest_discovered(value)
        if key in ("quest_discovered", "discover"):
            return _req_quest_discovered(value)
        if key in ("quest_step", "step"):
            return _req_quest_step_done(value)
        if key in ("loc", "location"):
            return current_location == value
        if key == "area":
            return current_area_id() == value
        if key == "time":
            options = [v.strip().lower() for v in value.split("|")]
            bucket = _req_current_time_bucket().lower()
            if bucket in options:
                return True
            try:
                return str(int(time)) in options
            except Exception:
                return False
        if key == "weekday":
            try:
                return weekday_name().lower() in [v.strip().lower() for v in value.split("|")]
            except Exception:
                return False
        if key in ("mood", "char_mood"):
            char_name, _, mood_name = value.partition(".")
            if not mood_name:
                char_name = actor
                mood_name = value
            return _req_mood_value(char_name, mood_name, actor=actor) > 0
        if key in ("present", "character_present", "npc"):
            try:
                return value in npcs_here()
            except Exception:
                return False
        if key == "system":
            return system_enabled(value)

        return False

    def _req_eval_dict(requirements, actor=None):
        for flag in _req_as_list(requirements.get("flags")):
            if not _req_has_flag(flag):
                return False
        for flag in _req_as_list(requirements.get("blocked_by_flags") or requirements.get("unless")):
            if _req_has_flag(flag):
                return False
        for stat_name, minimum in (requirements.get("stats") or {}).items():
            if _req_player_stat_value(stat_name) < _req_int(minimum):
                return False
        for char_name, stats in (requirements.get("character_stats") or {}).items():
            for stat_name, minimum in (stats or {}).items():
                if _req_char_stat_value(char_name, stat_name, actor=actor) < _req_int(minimum):
                    return False
        for item_id, count in (requirements.get("items") or {}).items():
            if not has_item(item_id, _req_int(count, 1)):
                return False
        for qid in _req_as_list(requirements.get("quests_completed")):
            if _req_quest_state(qid) != "completed":
                return False
        for qid in _req_as_list(requirements.get("quests_active")):
            if _req_quest_state(qid) != "active":
                return False
        for qid, oids in (requirements.get("quest_objectives") or {}).items():
            for oid in _req_as_list(oids):
                if not _req_quest_step_done("%s.%s" % (qid, oid)):
                    return False
        times = _req_as_list(requirements.get("time"))
        if times and _req_current_time_bucket() not in times and str(time) not in [str(t) for t in times]:
            return False
        locs = _req_as_list(requirements.get("locations"))
        if locs and current_location not in locs:
            return False
        areas_req = _req_as_list(requirements.get("areas"))
        if areas_req and current_area_id() not in areas_req:
            return False
        return True

    def meets_requirements(requirements=None, actor=None, explain=False):
        """Return True/False, or (bool, reason) when explain=True."""
        missing = first_missing_requirement(requirements, actor=actor)
        ok = missing is None
        if explain:
            return (ok, missing)
        return ok

    def _req_rule_missing(rule, actor=None):
        if isinstance(rule, dict):
            if _req_eval_dict(rule, actor=actor):
                return None
            return requirement_summary(rule)
        if _req_eval_string(rule, actor=actor):
            return None
        return requirement_summary(rule)

    def first_missing_requirement(requirements=None, actor=None):
        if requirements is None:
            return None
        if callable(requirements):
            try:
                return None if requirements() else "Requirement not met"
            except Exception:
                return "Requirement error"
        if isinstance(requirements, dict):
            return None if _req_eval_dict(requirements, actor=actor) else requirement_summary(requirements)
        for rule in _req_as_list(requirements):
            missing = _req_rule_missing(rule, actor=actor)
            if missing:
                return missing
        return None

    def requirement_summary(requirements=None):
        if requirements is None:
            return ""
        if callable(requirements):
            return "Requirement not met"
        if isinstance(requirements, dict):
            parts = []
            for flag in _req_as_list(requirements.get("flags")):
                parts.append("Requires " + _req_display_id(flag))
            for flag in _req_as_list(requirements.get("blocked_by_flags") or requirements.get("unless")):
                parts.append("Unavailable after " + _req_display_id(flag))
            for stat_name, minimum in (requirements.get("stats") or {}).items():
                parts.append("Requires %s %s" % (_req_display_id(stat_name), minimum))
            for char_name, stats in (requirements.get("character_stats") or {}).items():
                for stat_name, minimum in (stats or {}).items():
                    parts.append("Requires %s %s %s" % (_req_display_id(char_name), _req_display_id(stat_name), minimum))
            for item_id, count in (requirements.get("items") or {}).items():
                parts.append("Needs %s" % _req_display_id(item_id) if _req_int(count, 1) <= 1 else "Needs %s x%s" % (_req_display_id(item_id), count))
            for qid in _req_as_list(requirements.get("quests_completed")):
                parts.append("Complete " + _req_display_id(qid))
            return ", ".join(parts) if parts else "Requirement not met"
        if isinstance(requirements, (list, tuple, set)):
            return ", ".join(requirement_summary(r) for r in requirements)

        raw = _req_str(requirements)
        compared = _REQ_COMPARE_RE.match(raw)
        if compared:
            left = compared.group(1).replace("stat:", "").replace(".", " ")
            return "Requires %s %s %s" % (_req_display_id(left), compared.group(2), compared.group(3))
        key, sep, value = raw.partition(":")
        if not sep:
            return "Requires " + _req_display_id(raw)
        key = key.strip().lower()
        value = value.strip()
        if key in ("flag", "has_flag"):
            return "Requires " + _req_display_id(value)
        if key in ("blocked_by_flag", "blocked_by_flags", "unless", "no_flag"):
            return "Unavailable after " + _req_display_id(value)
        if key in ("item", "has_item"):
            item_id, _, count = value.partition(">=")
            return "Needs %s" % _req_display_id(item_id) if not count else "Needs %s x%s" % (_req_display_id(item_id), count)
        if key == "no_item":
            return "Requires not having " + _req_display_id(value)
        if key in ("quest_done", "quest_completed"):
            return "Complete " + _req_display_id(value)
        if key == "quest_active":
            return "Requires active quest " + _req_display_id(value)
        if key in ("quest_started", "quest_unlocked", "quest_discovered", "discover"):
            return "Discover " + _req_display_id(value)
        if key in ("quest_step", "step"):
            return "Complete " + _req_display_id(value)
        if key in ("loc", "location"):
            return "Go to " + _req_display_id(value)
        if key == "area":
            return "Go to " + _req_display_id(value)
        if key == "time":
            return "Come back at " + value.replace("|", " or ")
        if key == "weekday":
            return "Come back on " + value.replace("|", " or ")
        if key in ("mood", "char_mood"):
            return "Requires mood " + _req_display_id(value)
        if key in ("present", "character_present", "npc"):
            return "Needs " + _req_display_id(value)
        if key == "system":
            return "Requires system " + _req_display_id(value)
        if key == "tag":
            return "Needs item tagged " + _req_display_id(value)
        return "Requirement not met"
