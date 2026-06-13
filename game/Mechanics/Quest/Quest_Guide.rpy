# =============================================================================
# Engine/Quest_Guide.rpy - automatic quest markers
# -----------------------------------------------------------------------------
# Reads the active quest's target hints and tells the HUD where to draw a
# floating marker - over an NPC, over an item, over an exit, or over a
# location entrance on the map. No per-quest screen code required.
#
# How a quest declares targets:
#   define_quest(
#       "find_alice",
#       title="Find Alice",
#       start_flag="quest_find_alice",
#       target={"npc": "alice"},                # global default
#       objectives=[
#           {"oid": "find",  "text": "Find her", "flag": "met_alice",
#            "target": {"npc": "alice", "location": "art_room"}},
#           {"oid": "talk",  "text": "Have a real chat", "flag": "talked_alice",
#            "target": {"npc": "alice"}},
#       ],
#   )
#
# Active target picking:
#   - First incomplete objective with a target wins.
#   - Else, the quest-level target wins.
#
# Works with locations too:
#   target={"location": "roof"}    -> marker over the roof exit on this map.
# =============================================================================


define quest_guide_enabled = True
default tracked_character_id = None


init python:

    def _location_graph():
        g = {}
        for lid, data in locations.items():
            tos = []
            for ex in data.get("exits", []):
                to = ex.get("to")
                if to in locations:
                    tos.append(to)
            g[lid] = tos
        return g

    def _path_next_step(src, dst):
        if not src or not dst:
            return None
        if src == dst:
            return src
        g = _location_graph()
        seen = set([src])
        queue = [(src, None)]
        while queue:
            node, first = queue.pop(0)
            for nxt in g.get(node, []):
                if nxt in seen:
                    continue
                seen.add(nxt)
                first_step = first or nxt
                if nxt == dst:
                    return first_step
                queue.append((nxt, first_step))
        return None

    def set_tracked_character(cid):
        # NOTE: returns None on purpose. See note in set_tracked_quest:
        # truthy returns from an action close the underlying `call screen`
        # which then falls through to nav_left and teleports the player.
        global tracked_character_id
        if cid in character_stats:
            tracked_character_id = cid
        return None

    def toggle_tracked_character(cid):
        global tracked_character_id
        if tracked_character_id == cid:
            tracked_character_id = None
        elif cid in character_stats:
            tracked_character_id = cid
        return None

    def clear_tracked_character():
        global tracked_character_id
        tracked_character_id = None
        return None

    def tracked_character_location():
        cid = tracked_character_id
        if not cid:
            return None
        try:
            return npc_location(cid)
        except Exception:
            return None

    def active_quest_target():
        # Returns the target dict of the explicitly tracked quest.
        targets = active_quest_targets()
        return targets[0] if targets else None

    def active_quest_targets():
        # Returns normalized target dicts of the explicitly tracked quest.
        if not quest_guide_enabled:
            return []
        tq = None
        try:
            tq = tracked_quest()
        except Exception:
            tq = None
        if tq:
            t = _first_quest_target(tq)
            if t:
                return _normalize_quest_targets(tq, t)
        return []

    def _normalize_quest_targets(q, raw_target):
        if not raw_target:
            return []
        raw_targets = raw_target.get("targets") if isinstance(raw_target, dict) else None
        if raw_targets:
            inherited = dict(raw_target)
            inherited.pop("targets", None)
            out = []
            for target in raw_targets:
                merged = dict(inherited)
                merged.update(target)
                for normalized in _normalize_quest_targets(q, merged):
                    if not _target_duplicate(out, normalized):
                        out.append(normalized)
            return out
        t = dict(raw_target)
        t["_quest"] = q
        t["_guide_precision"] = _quest_target_precision(q, t)
        return [t]

    def _target_duplicate(targets, candidate):
        keys = ("npc", "item", "object", "location", "area")
        for target in targets:
            if all(target.get(k) == candidate.get(k) for k in keys):
                return True
        return False

    def _quest_target_precision(q, target=None):
        target = target or {}
        value = target.get("guide_precision", target.get("tracking", None))
        if value is None:
            value = getattr(q, "guide_precision", "exact")
        value = str(value or "exact").lower()
        if value in ("off", "hidden", "none"):
            return "none"
        if value in ("area", "region"):
            return "area"
        if value in ("location", "loc"):
            return "location"
        if value in ("characters", "multi_character", "multi-character"):
            return "characters"
        return "exact"

    def _target_locations(t):
        out = []
        loc = t.get("location")
        if loc:
            out.append(loc)
        npc = t.get("npc")
        if npc:
            try:
                nloc = npc_location(npc)
                if nloc and nloc not in out:
                    out.append(nloc)
            except Exception:
                pass
        for cid in (t.get("characters") or []):
            try:
                cloc = npc_location(cid)
                if cloc and cloc not in out:
                    out.append(cloc)
            except Exception:
                pass
        return out

    def _target_display_name(t):
        if t.get("npc"):
            return character_display_name(t.get("npc"))
        if t.get("characters"):
            return ", ".join(character_display_name(cid) for cid in t.get("characters") if cid)
        if t.get("item"):
            try:
                return item_name(t.get("item"))
            except Exception:
                return str(t.get("item")).replace("_", " ").title()
        if t.get("object"):
            obj = get_interactable(t.get("object"))
            return (obj or {}).get("title") or str(t.get("object")).replace("_", " ").title()
        if t.get("location"):
            return location_name(t.get("location"))
        if t.get("area"):
            return area_data(t.get("area")).get("name", str(t.get("area")).title())
        return "Target"

    def _first_quest_target(q):
        # First incomplete objective target, else quest-level target.
        for o in q.objectives:
            if o.done or o.optional:
                continue
            t = getattr(o, "target", None)
            if t:
                return t
        return getattr(q, "target", None)

    def quest_marker_for_iid(iid):
        # True if the active quest target points at this interactable.
        return quest_marker_text_for_iid(iid) is not None

    def quest_marker_text_for_iid(iid):
        matches = []
        for t in active_quest_targets():
            precision = t.get("_guide_precision", "exact")
            if precision in ("none", "area", "location"):
                continue
            if precision == "characters":
                if iid in (t.get("characters") or []) or t.get("npc") == iid:
                    matches.append(t)
            elif t.get("npc") == iid or t.get("item") == iid or t.get("object") == iid:
                matches.append(t)
        if not matches:
            return None
        if len(matches) > 1:
            return str(len(matches))
        return matches[0].get("icon") or "!"

    def quest_marker_for_exit(loc_id):
        return quest_marker_text_for_exit(loc_id) is not None

    def quest_marker_text_for_exit(loc_id):
        t = active_quest_target()
        if not t:
            return None
        matches = []
        for target in active_quest_targets():
            if _quest_target_points_to_exit(target, loc_id):
                matches.append(target)
        if not matches:
            return None
        if len(matches) > 1:
            return str(len(matches))
        precision = matches[0].get("_guide_precision", "exact")
        if precision == "area":
            return "~"
        if precision == "location":
            return "?"
        return matches[0].get("icon") or "!"

    def _quest_target_points_to_exit(t, loc_id):
        precision = t.get("_guide_precision", "exact")
        if precision == "none":
            return False
        target_locs = _target_locations(t)
        target_area = t.get("area")
        if not target_area and target_locs:
            try:
                target_area = location_area_id(target_locs[0])
            except Exception:
                target_area = None

        if precision == "area":
            if not target_area or current_area_id() == target_area:
                return False
            area_locs = [lid for lid in location_order if location_area_id(lid) == target_area]
            for target_loc in area_locs:
                next_step = _path_next_step(current_location, target_loc)
                if next_step and loc_id == next_step:
                    return True
            return False

        for target_loc in target_locs:
            if not target_loc or target_loc == current_location:
                continue
            next_step = _path_next_step(current_location, target_loc)
            if next_step and loc_id == next_step:
                return True
        return False

    def character_marker_for_exit(loc_id):
        target_loc = tracked_character_location()
        if not target_loc or target_loc == current_location:
            return False
        next_step = _path_next_step(current_location, target_loc)
        if not next_step:
            return False
        return loc_id == next_step

    def character_marker_for_iid(iid):
        return bool(tracked_character_id and iid == tracked_character_id)

    def active_quest_title():
        t = active_quest_target()
        if not t:
            return None
        q = t.get("_quest")
        return q.title if q else None

    def tracked_character_label():
        cid = tracked_character_id
        if not cid:
            return None
        return character_display_name(cid)

    def quest_target_for_current_location():
        if getattr(store, "_in_dialogue", None):
            return None
        return quest_target_label()

    def character_target_for_current_location():
        if getattr(store, "_in_dialogue", None):
            return None
        cid = tracked_character_id
        if not cid:
            return None
        cloc = tracked_character_location()
        if cloc == current_location:
            return "Track: " + character_display_name(cid) + " (here)"
        if cloc:
            return "Track: " + character_display_name(cid) + " (" + location_name(cloc) + ")"
        return "Track: " + character_display_name(cid)

    def quest_target_label():
        # Short label for the HUD (e.g. "Find Alice"). None if no active target.
        targets = active_quest_targets()
        if not targets:
            return None
        t = targets[0]
        if t.get("_guide_precision") == "none":
            return None
        q = t.get("_quest")
        if q:
            for o in q.objectives:
                if not o.done and not o.optional:
                    if len(targets) > 1:
                        names = [_target_display_name(target) for target in targets[:3]]
                        suffix = "" if len(targets) <= 3 else " +" + str(len(targets) - 3)
                        if t.get("_guide_precision") == "area":
                            return "Search areas: " + ", ".join(names) + suffix
                        if t.get("_guide_precision") == "location":
                            return "Search: " + ", ".join(names) + suffix
                        return "Targets: " + ", ".join(names) + suffix
                    if t.get("_guide_precision") == "area":
                        area = t.get("area")
                        if not area:
                            locs = _target_locations(t)
                            area = location_area_id(locs[0]) if locs else None
                        return "Search: " + area_data(area).get("name", str(area).title()) if area else o.text
                    if t.get("_guide_precision") == "location":
                        locs = _target_locations(t)
                        return "Search: " + location_name(locs[0]) if locs else o.text
                    if t.get("_guide_precision") == "characters":
                        return "Find: " + ", ".join(character_display_name(c) for c in (t.get("characters") or [t.get("npc")]) if c)
                    return o.text
            return q.title
        return None
