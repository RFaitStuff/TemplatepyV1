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
        # Returns the target dict of the tracked quest, or fallback active quest.
        if not quest_guide_enabled:
            return None
        tq = None
        try:
            tq = tracked_quest()
        except Exception:
            tq = None
        if tq:
            t = _first_quest_target(tq)
            if t:
                t = dict(t)
                t["_quest"] = tq
                return t

        active = []
        try:
            active = [q for q in active_quests()]
        except Exception:
            return None
        if not active:
            return None
        # Sort: main first, then side, then char/misc; among same category, by id.
        order = {"main": 0, "side": 1}
        active.sort(key=lambda q: (order.get(q.category, 5), q.id))
        for q in active:
            t = _first_quest_target(q)
            if t:
                # Tag the target with the quest itself so the HUD can show its title.
                t = dict(t)
                t["_quest"] = q
                return t
        return None

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
        t = active_quest_target()
        if not t:
            return False
        return t.get("npc") == iid or t.get("item") == iid or t.get("object") == iid

    def quest_marker_for_exit(loc_id):
        t = active_quest_target()
        if not t:
            return False
        target_loc = t.get("location")
        if not target_loc:
            npc = t.get("npc")
            if npc:
                try:
                    target_loc = npc_location(npc)
                except Exception:
                    target_loc = None
        if not target_loc or target_loc == current_location:
            return False
        next_step = _path_next_step(current_location, target_loc)
        if not next_step:
            return False
        return loc_id == next_step

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
        t = active_quest_target()
        if not t:
            return None
        q = t.get("_quest")
        if q:
            for o in q.objectives:
                if not o.done and not o.optional:
                    return o.text
            return q.title
        return None
