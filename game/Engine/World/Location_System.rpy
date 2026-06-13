# Location engine internals. User-authored area/location registration lives in Game/World/Locations.rpy.

# Registry containers - plain init-time dicts/lists, NOT defaults. They hold
# pure registration data identical for every playthrough.
init -3 python:
    areas               = {}
    locations           = {}
    location_order      = []
    unlocked_rooms_init = set()


# Player state (resets per playthrough).
default unlocked_rooms    = set()
default current_location  = "homeroom"
default _location_session = {}
default location_visits   = {}
default location_visit_days = {}
default _last_entered_location = None
default _last_location_enter_context = {}


# =============================================================================
# REGISTRATION HELPERS
# =============================================================================
init -3 python:

    def register_area(area_id, name=None, outfit=None, **extra):
        # Register or update an area.
        # area_id - short id (e.g. 'school')
        # name    - display name
        # outfit  - outfit id used by every location in this area
        a = areas.setdefault(area_id, {})
        if name is not None:
            a["name"] = name
        if outfit is not None:
            a["outfit"] = outfit
        a.setdefault("name", area_id.title())
        a.setdefault("outfit", None)
        a.update(extra)

    def register_location(loc_id, name=None, bg=None, area=None, variants=None, unlocked=True, order_after=None, **extra):
        # Register or update a location at the registry level.
        # variants     - {char_id: ['', '1', ...]}  pose variants allowed here
        # unlocked     - locked rooms are skipped by nav arrows
        # order_after  - existing loc_id to insert this one after in nav order
        # Per-location DATA (positions, items, on_enter, talk overrides) goes
        # in the location's own file via configure_location().
        loc = locations.setdefault(loc_id, {})
        if name is not None:
            loc["name"] = name
        if bg is not None:
            loc["bg"] = bg
        if area is not None:
            loc["area"] = area
        if variants is not None:
            loc["variants"] = dict(variants)
        loc.setdefault("name", loc_id.replace("_", " ").title())
        loc.setdefault("bg", loc_id)
        loc.setdefault("area", None)
        loc.setdefault("variants", {})
        loc.setdefault("positions", {})
        loc.setdefault("items", [])
        loc.setdefault("on_enter", None)
        loc.setdefault("talk", {})
        loc.setdefault("exits", [])     # [{"to": loc_id, "label": "Hallway", "pos": (x,y), "size": (w,h)}, ...]
        loc.setdefault("objects", [])   # [{"id": iid, "pos": (x,y), "size": (w,h)}, ...]
        loc.setdefault("layers", [])    # Optional visual overlays for exploration.
        loc.update(extra)

        if loc_id not in location_order:
            if order_after and order_after in location_order:
                location_order.insert(location_order.index(order_after) + 1, loc_id)
            else:
                location_order.append(loc_id)

        if unlocked:
            unlocked_rooms_init.add(loc_id)

    def configure_location(loc_id, positions=None, items=None, on_enter=None, talk=None, exits=None, objects=None, layers=None, **extra):
        # Add per-location runtime data (called from the location's own file).
        # positions - {char_id: [(xalign, yalign), ...]}
        # items     - [{item, while_flag, hide_flag, label, pos}, ...]
        # on_enter  - label to call when the player walks in
        # talk      - {char_id: label}  per-location talk override
        # exits     - [{"to": loc_id, "label": "Hallway",
        #               "pos": (x, y), "size": (w, h)}, ...]
        # objects   - [{"id": iid, "label": "Noticeboard",
        #               "pos": (x, y), "size": (w, h)}, ...]
        # Each object's `id` should ALSO be registered with
        # register_interactable() so the action menu / smart mode can resolve
        # its actions.
        if loc_id not in locations:
            raise Exception("configure_location: '%s' not registered yet." % loc_id)
        loc = locations[loc_id]
        if positions is not None:
            loc["positions"] = dict(positions)
        if items is not None:
            loc["items"] = list(items)
        if on_enter is not None:
            loc["on_enter"] = on_enter
        if talk is not None:
            loc["talk"] = dict(talk)
        if exits is not None:
            loc["exits"] = list(exits)
        if objects is not None:
            loc["objects"] = list(objects)
        if layers is not None:
            loc["layers"] = list(layers)
        loc.update(extra)



# =============================================================================
# Seed the saveable `unlocked_rooms` set from `unlocked_rooms_init` at start.
# Called once from the `start` label in script.rpy.
# =============================================================================
init python:
    def _seed_unlocked_rooms():
        for r in unlocked_rooms_init:
            unlocked_rooms.add(r)


# =============================================================================
# LOOKUP HELPERS
# =============================================================================
init python:

    def location_data(loc_id=None):
        return locations.get(loc_id or current_location, {})

    def location_name(loc_id=None):
        return location_data(loc_id).get("name", loc_id or current_location)

    def location_bg(loc_id=None):
        return location_data(loc_id).get("bg", "")

    def location_layers(loc_id=None, slot=None):
        out = []
        for layer in location_data(loc_id).get("layers", []) or []:
            if slot is not None and layer.get("slot", "overlay") != slot:
                continue
            requires = layer.get("requires") or layer.get("show_when")
            if requires is not None:
                try:
                    if not meets_requirements(requires):
                        continue
                except Exception:
                    continue
            avail = layer.get("available_if")
            if avail is not None:
                try:
                    if not avail():
                        continue
                except Exception:
                    continue
            out.append(layer)
        out.sort(key=lambda item: item.get("order", 0))
        return out

    def location_area_id(loc_id=None):
        return location_data(loc_id).get("area")

    def current_area_id():
        return location_area_id(current_location)

    def area_data(area_id):
        return areas.get(area_id, {})

    def area_outfit(area_id):
        if not area_id:
            return None
        return areas.get(area_id, {}).get("outfit")

    # ---- nav -------------------------------------------------------------
    def is_room_unlocked(loc_id):
        return loc_id in unlocked_rooms

    def unlock_room(loc_id):
        unlocked_rooms.add(loc_id)

    def lock_room(loc_id):
        unlocked_rooms.discard(loc_id)

    def _next_unlocked_index(start_idx, step):
        n = len(location_order)
        if n == 0:
            return 0
        i = start_idx
        for _ in range(n):
            i = (i + step) % n
            if location_order[i] in unlocked_rooms:
                return i
        return start_idx

    def _change_location(new_loc):
        global current_location
        if new_loc != current_location:
            _location_session.pop(new_loc, None)   # re-roll poses/positions
        current_location = new_loc

    def go_next_location():
        try:
            i = location_order.index(current_location)
        except ValueError:
            i = 0
        _change_location(location_order[_next_unlocked_index(i, 1)])

    def go_prev_location():
        try:
            i = location_order.index(current_location)
        except ValueError:
            i = 0
        _change_location(location_order[_next_unlocked_index(i, -1)])

    def goto_location(loc_id):
        if loc_id in locations:
            _change_location(loc_id)

    # ---- per-location runtime data getters ------------------------------
    def location_character_pose(loc_id, char):
        loc = locations.get(loc_id, {})
        pool = loc.get("variants", {}).get(char)
        if not pool:
            return ""
        sess = _location_session.setdefault(loc_id, {}).setdefault("poses", {})
        if char not in sess:
            sess[char] = renpy.random.choice(pool)
        return sess[char]

    def location_character_pos(loc_id, char):
        loc = locations.get(loc_id, {})
        pool = loc.get("positions", {}).get(char)
        if not pool:
            return (0.5, 1.0)
        sess = _location_session.setdefault(loc_id, {}).setdefault("positions", {})
        if char not in sess:
            sess[char] = renpy.random.choice(pool)
        return sess[char]

    def reroll_location(loc_id=None):
        _location_session.pop(loc_id or current_location, None)

    def location_active_items(loc_id=None):
        # Items currently visible (their while_flag is set, hide_flag is not).
        loc = location_data(loc_id)
        out = []
        for it in loc.get("items", []):
            requires = it.get("requires") or it.get("show_when") or it.get("unlock_when")
            if requires is not None and not meets_requirements(requires):
                continue
            flag = it.get("while_flag")
            if flag and not has_flag(flag):
                continue
            anti = it.get("hide_flag")
            if anti and has_flag(anti):
                continue
            out.append((it.get("item", ""), it.get("label", ""), it.get("pos", (0.5, 0.5))))
        return out

    def location_on_enter_label(loc_id=None):
        return location_data(loc_id).get("on_enter")

    def location_first_visit_label(loc_id=None):
        return location_data(loc_id).get("first_visit")

    def location_first_visit_today_label(loc_id=None):
        return location_data(loc_id).get("first_visit_today")

    def location_main_loop_label(loc_id=None):
        return location_data(loc_id).get("main_loop")

    def location_talk_label(char, loc_id=None):
        # Per-location override label for talking to `char`. None if not set.
        return location_data(loc_id).get("talk", {}).get(char)

    def record_location_entry(loc_id=None):
        global _last_entered_location, _last_location_enter_context
        loc_id = loc_id or current_location
        if _last_entered_location == loc_id:
            return False
        previous_count = location_visits.get(loc_id, 0)
        today = globals().get("day", 0)
        previous_day = location_visit_days.get(loc_id)
        location_visits[loc_id] = previous_count + 1
        location_visit_days[loc_id] = today
        _last_entered_location = loc_id
        _last_location_enter_context = {
            "location": loc_id,
            "first_visit": previous_count == 0,
            "first_visit_today": previous_day != today,
            "visit_count": previous_count + 1,
        }
        try:
            emit("location_entered", loc_id)
        except Exception:
            pass
        return True

    def location_visit_count(loc_id=None):
        return location_visits.get(loc_id or current_location, 0)

    def first_visit(loc_id=None):
        loc_id = loc_id or current_location
        ctx = _last_location_enter_context or {}
        if ctx.get("location") == loc_id:
            return bool(ctx.get("first_visit"))
        return location_visits.get(loc_id, 0) == 0

    def first_visit_today(loc_id=None):
        loc_id = loc_id or current_location
        ctx = _last_location_enter_context or {}
        if ctx.get("location") == loc_id:
            return bool(ctx.get("first_visit_today"))
        return location_visit_days.get(loc_id) != globals().get("day", 0)
