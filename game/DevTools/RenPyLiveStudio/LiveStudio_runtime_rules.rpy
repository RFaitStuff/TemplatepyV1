# Runtime/source/editable object classification and coordinate authoring helpers.

init -976 python in live_studio:
    PARENT_LAYOUT_TYPES = set(("vbox", "hbox", "grid", "vpgrid"))

    def object_category(item=None, kind=None, state=None):
        if item is None:
            item, _parent, kind = selected_item(state)
        if not item:
            return "preview_only"
        source = item.get("source") or {}
        if item.get("managed") or source.get("created_by") == "live_studio" or source.get("provenance") in ("managed", "converted_approximation"):
            return "studio_managed"
        if source.get("screen_language") or source.get("source_location") or source.get("location") or source.get("filename"):
            if kind == "ui_node" and not item.get("widget_id"):
                return "preview_only"
            return "source_backed"
        if source.get("captured_by") == "runtime" or source.get("provenance") == "runtime_observed":
            return "runtime_override" if item.get("widget_id") else "preview_only"
        if kind in ("scene_node", "ui_node", "dialogue_controller", "dialogue_event"):
            return "studio_managed"
        return "preview_only"

    def object_category_label(item=None, kind=None):
        value = object_category(item, kind)
        return {
            "studio_managed": "Studio-managed",
            "source_backed": "Source-backed",
            "runtime_override": "Runtime override",
            "preview_only": "Preview-only",
        }.get(value, value.replace("_", " ").title())

    def object_edit_reason(item=None, kind=None, state=None):
        lookup_state = state or resolve_frame()
        if item is None:
            item, parent_id, kind = selected_item(lookup_state)
        else:
            # Properties passes the resolved item directly. Recover its parent
            # instead of losing hierarchy context, otherwise VBox/HBox/Grid
            # children incorrectly report themselves as freely editable.
            _found, parent_id, found_kind = find_state_item(lookup_state, item.get("id"))
            if kind is None:
                kind = found_kind
        if not item:
            return "No object selected."
        if item.get("locked"):
            return "The object is locked."
        category = object_category(item, kind, state)
        if category == "preview_only":
            if kind == "ui_node" and not item.get("widget_id"):
                return "This captured widget has no stable Ren'Py id. Convert its screen explicitly before editing."
            return "This object is shown for context and cannot be edited safely."
        if kind == "ui_screen":
            return "Screens are hierarchy folders. Edit their child containers and widgets instead of moving the screen root."
        if kind == "ui_node":
            parent = None
            if parent_id:
                parent, _unused, _kind = find_state_item(state or resolve_frame(), parent_id)
            if parent and str(parent.get("type", "")).lower() in PARENT_LAYOUT_TYPES:
                return "Position is controlled by the parent {} layout. Edit order, spacing, padding, or convert to a free-positioned container.".format(parent.get("type"))
        return "Editable."

    def parent_layout_controls_position(item_id, state=None):
        state = state or resolve_frame()
        item, parent_id, kind = find_state_item(state, item_id)
        if kind != "ui_node" or not parent_id:
            return False
        parent, _parent_parent, _parent_kind = find_state_item(state, parent_id)
        return bool(parent and str(parent.get("type", "")).lower() in PARENT_LAYOUT_TYPES)

    def coordinate_mode(item, axis="x"):
        if not item:
            return str(project_setting("coordinate_mode_default", "auto"))
        authoring = item.get("authoring") or {}
        coordinates = authoring.get("coordinates") or {}
        explicit = coordinates.get(str(axis).lower())
        # "auto" means infer from the current authored properties. Returning
        # the literal word auto here made aligned Scene objects lose their
        # alignment intent on the next drag.
        if explicit in COORDINATE_MODES and explicit != "auto":
            return explicit
        props = item.get("properties") or {}
        axis = str(axis).lower()
        if props.get(axis + "align") is not None:
            return "alignment" if not props.get(axis + "offset") else "mixed"
        value = props.get(axis + "pos")
        if isinstance(value, float) and -2.0 <= value <= 2.0:
            return "relative" if not props.get(axis + "offset") else "mixed"
        return "pixels"

    def set_coordinate_mode(item_id, axis, mode):
        mode = str(mode or "auto").lower()
        if mode not in COORDINATE_MODES:
            mode = "auto"
        set_item_value(item_id, "authoring.coordinates.{}".format(str(axis).lower()), mode, "Change coordinate mode")

    def cycle_coordinate_mode(item_id, axis):
        item, _parent, _kind = find_state_item(resolve_frame(), item_id)
        current = coordinate_mode(item, axis)
        order = list(COORDINATE_MODES)
        try:
            next_mode = order[(order.index(current) + 1) % len(order)]
        except Exception:
            next_mode = "auto"
        set_coordinate_mode(item_id, axis, next_mode)

    def nudge_selected(dx=0, dy=0, fine=False):
        global project_dirty, preview_mode
        item, _parent, kind = selected_item()
        if not item or kind not in ("scene_node", "ui_node"):
            return False
        if canvas_item_locked(item, kind) or object_category(item, kind) == "preview_only":
            return False
        if kind == "ui_node" and parent_layout_controls_position(item.get("id")):
            try:
                renpy.notify("Parent layout controls this widget's position")
            except Exception:
                pass
            return False
        frame = current_frame()
        if frame is None:
            return False
        before = clone(frame.get("changes", {}))
        scale = 0.25 if fine else 1.0
        props = item.get("properties") or {}
        sets = frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(item.get("id"), {})
        if dx:
            path = "properties.xoffset" if kind == "ui_node" or coordinate_mode(item, "x") in ("relative", "alignment", "mixed") else "properties.xpos"
            current = props.get(path.split(".", 1)[1], 0) or 0
            sets[path] = float(current) + float(dx) * scale
        if dy:
            path = "properties.yoffset" if kind == "ui_node" or coordinate_mode(item, "y") in ("relative", "alignment", "mixed") else "properties.ypos"
            current = props.get(path.split(".", 1)[1], 0) or 0
            sets[path] = float(current) + float(dy) * scale
        after = clone(frame.get("changes", {}))
        if before == after:
            return False
        project_dirty = True
        preview_mode = "layout"
        invalidate_resolved_cache(False, "keyboard nudge")
        _record_frame_change("Nudge item", before, after, current_frame_id)
        restart()
        return True
