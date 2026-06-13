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

    def world_validation_issues():
        issues = []

        for area_id, data in areas.items():
            if not data.get("name"):
                issues.append("Area '{}' has no display name.".format(area_id))

        seen_order = set()
        for loc_id in location_order:
            if loc_id in seen_order:
                issues.append("location_order contains duplicate location '{}'.".format(loc_id))
            seen_order.add(loc_id)
            if loc_id not in locations:
                issues.append("location_order references missing location '{}'.".format(loc_id))

        for loc_id, loc in locations.items():
            if loc_id not in location_order:
                issues.append("Location '{}' is registered but missing from location_order.".format(loc_id))
            if loc.get("area") and loc.get("area") not in areas:
                issues.append("Location '{}' references missing area '{}'.".format(loc_id, loc.get("area")))
            if not loc.get("bg"):
                issues.append("Location '{}' has no background id.".format(loc_id))

            for label_key in ("on_enter", "first_visit", "first_visit_today", "main_loop"):
                label = loc.get(label_key)
                if label and not renpy.has_label(label):
                    issues.append("Location '{}' {} points to missing label '{}'.".format(loc_id, label_key, label))

            for cid, spots in (loc.get("positions", {}) or {}).items():
                if cid not in (globals().get("character_stats", {}) or {}):
                    issues.append("Location '{}' has positions for missing character '{}'.".format(loc_id, cid))
                for spot in spots or []:
                    if not _world_valid_pair(spot):
                        issues.append("Location '{}' position for '{}' is not an (x, y) pair: {!r}".format(loc_id, cid, spot))

            for cid in (loc.get("variants", {}) or {}).keys():
                if cid not in (globals().get("character_stats", {}) or {}):
                    issues.append("Location '{}' has image variants for missing character '{}'.".format(loc_id, cid))

            for cid, label in (loc.get("talk", {}) or {}).items():
                if cid not in (globals().get("character_stats", {}) or {}):
                    issues.append("Location '{}' talk override references missing character '{}'.".format(loc_id, cid))
                if label and not renpy.has_label(label):
                    issues.append("Location '{}' talk override for '{}' points to missing label '{}'.".format(loc_id, cid, label))

            seen_objects = set()
            for obj in loc.get("objects", []) or []:
                oid = obj.get("id")
                if not oid:
                    issues.append("Location '{}' has object spot with no id.".format(loc_id))
                    continue
                if oid in seen_objects:
                    issues.append("Location '{}' has duplicate object spot '{}'.".format(loc_id, oid))
                seen_objects.add(oid)
                if oid not in (globals().get("interactable_defs", {}) or {}):
                    issues.append("Location '{}' object '{}' has no interactable definition.".format(loc_id, oid))
                _world_validate_requirement("Location '{}' object '{}'".format(loc_id, oid), obj.get("requires") or obj.get("show_when") or obj.get("unlock_when"), issues)
                if obj.get("pos") and not _world_valid_pair(obj.get("pos")):
                    issues.append("Location '{}' object '{}' has invalid pos {!r}.".format(loc_id, oid, obj.get("pos")))
                if obj.get("size") and not _world_valid_pair(obj.get("size")):
                    issues.append("Location '{}' object '{}' has invalid size {!r}.".format(loc_id, oid, obj.get("size")))

            for item in loc.get("items", []) or []:
                item_id = item.get("item")
                if not item_id:
                    issues.append("Location '{}' has item spot with no item id.".format(loc_id))
                    continue
                if item_id not in (globals().get("item_defs", {}) or {}):
                    issues.append("Location '{}' item spot references missing item '{}'.".format(loc_id, item_id))
                label = item.get("label")
                if label and not renpy.has_label(label):
                    issues.append("Location '{}' item '{}' points to missing label '{}'.".format(loc_id, item_id, label))
                _world_validate_requirement("Location '{}' item '{}'".format(loc_id, item_id), item.get("requires") or item.get("show_when") or item.get("unlock_when"), issues)
                if item.get("pos") and not _world_valid_pair(item.get("pos")):
                    issues.append("Location '{}' item '{}' has invalid pos {!r}.".format(loc_id, item_id, item.get("pos")))

            for ex in loc.get("exits", []) or []:
                target = ex.get("to")
                if not target:
                    issues.append("Location '{}' has exit with no target.".format(loc_id))
                    continue
                if target not in locations:
                    issues.append("Location '{}' exit points to missing location '{}'.".format(loc_id, target))
                _world_validate_requirement("Location '{}' exit '{}'".format(loc_id, target), ex.get("requires") or ex.get("show_when") or ex.get("unlock_when"), issues)
                if ex.get("pos") and not _world_valid_pair(ex.get("pos")):
                    issues.append("Location '{}' exit '{}' has invalid pos {!r}.".format(loc_id, target, ex.get("pos")))
                if ex.get("size") and not _world_valid_pair(ex.get("size")):
                    issues.append("Location '{}' exit '{}' has invalid size {!r}.".format(loc_id, target, ex.get("size")))

            for index, layer in enumerate(loc.get("layers", []) or []):
                if not layer.get("image"):
                    issues.append("Location '{}' layer #{} has no image.".format(loc_id, index + 1))
                if layer.get("slot", "overlay") not in ("back", "overlay", "front"):
                    issues.append("Location '{}' layer #{} has unknown slot '{}'.".format(loc_id, index + 1, layer.get("slot")))
                _world_validate_requirement("Location '{}' layer #{}".format(loc_id, index + 1), layer.get("requires") or layer.get("show_when"), issues)

        return issues

    def _world_valid_pair(value):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return False
        try:
            float(value[0])
            float(value[1])
            return True
        except Exception:
            return False

    def _world_validate_requirement(context, requirement, issues):
        if not requirement:
            return
        try:
            first_missing_requirement(requirement)
        except Exception:
            issues.append("{} has an invalid requirement.".format(context))


init 999 python:
    try:
        register_project_tac_validator(world_validation_issues)
    except Exception:
        pass
