# Project state, frame inheritance, selection, commands, and persistence.

init -980 python in live_studio:
    import json
    import os
    import time

    project_data = None
    current_frame_id = None
    selected_item_id = None
    selected_item_kind = None
    selected_tree_tab = "Scene"
    bottom_tab = "Assets"
    preview_mode = DEFAULT_PREVIEW_MODE
    tool_mode = "select"
    project_dirty = False

    history = []
    redo_stack = []
    resolved_cache = {}

    runtime = {
        "diagnostics": [],
        "snapshot": None,
        "snapshot_bytes": None,
        "scene_displayables": {},
        "ui_displayables": {},
        "screen_roots": {},
        "screen_displayables": {},
        "drag": None,
        "resize": None,
        "clipboard": None,
        "export_previews": {},
        "source_trace": [],
        "opened": False,
    }
    class EditorInputValue(renpy.store.InputValue):
        """A stable, dynamic InputValue used by the Live Studio inspector.

        Using an InputValue instead of ``input default ... changed ...`` keeps
        fields synchronized when selection or frame changes and avoids Ren'Py
        reusing an input displayable with stale text.
        """
        default = False
        editable = True
        returnable = False

        def __init__(self, kind, *arguments):
            self.kind = str(kind)
            self.arguments = tuple(arguments)

        def __eq__(self, other):
            return type(self) is type(other) and self.kind == other.kind and self.arguments == other.arguments

        def __ne__(self, other):
            return not self == other

        def get_text(self):
            try:
                if self.kind == "project_name":
                    value = project_name()
                elif self.kind == "frame_name":
                    frame = frame_by_id(self.arguments[0])
                    value = (frame or {}).get("name", "Frame")
                elif self.kind == "property":
                    item, _parent_id, _item_kind = find_state_item(resolve_frame(), self.arguments[0])
                    value = get_path_value(item or {}, self.arguments[1], "")
                elif self.kind == "action":
                    node, _parent_id, _item_kind = find_state_item(resolve_frame(), self.arguments[0])
                    value = (primary_action(node) or {}).get(self.arguments[1], "")
                else:
                    value = ""
                return str("" if value is None else value)
            except Exception:
                return ""

        def set_text(self, value):
            if self.kind == "project_name":
                set_project_name(value)
            elif self.kind == "frame_name":
                set_frame_name(self.arguments[0], value)
            elif self.kind == "property":
                property_changed(self.arguments[0], self.arguments[1])(value)
            elif self.kind == "action":
                action_field_changed(self.arguments[0], self.arguments[1])(value)

    def editor_input_value(kind, *arguments):
        return EditorInputValue(kind, *arguments)


    def restart():
        try:
            renpy.restart_interaction()
        except Exception:
            pass

    def log_diagnostic(level, message, context=None):
        entry = {
            "level": str(level or "info"),
            "message": str(message),
            "context": json_safe(context or {}),
            "time": int(time.time()),
        }
        runtime.setdefault("diagnostics", []).append(entry)
        runtime["diagnostics"] = runtime["diagnostics"][-250:]
        try:
            renpy.log("[Live Studio] {}: {}".format(entry["level"].upper(), entry["message"]))
        except Exception:
            pass

    def clear_diagnostics():
        runtime["diagnostics"] = []
        restart()

    def ensure_project(name="Untitled Live Studio Project"):
        global project_data
        if not isinstance(project_data, dict):
            project_data = new_project(name)
        return project_data

    def project_name():
        return ensure_project().get("project", {}).get("name", "Untitled Live Studio Project")

    def set_project_name(value):
        global project_dirty
        data = ensure_project()
        data.setdefault("project", {})["name"] = str(value or "Untitled Live Studio Project")
        if not data["project"].get("id"):
            data["project"]["id"] = safe_identifier(value, "project")
        project_dirty = True
        restart()

    def project_setting(name, default=False):
        return ensure_project().get("settings", {}).get(name, default)

    def set_project_setting(name, value):
        global project_dirty
        ensure_project().setdefault("settings", {})[str(name)] = clone(value)
        project_dirty = True
        restart()

    def toggle_project_setting(name):
        set_project_setting(name, not bool(project_setting(name, False)))

    def invalidate_resolved_cache():
        resolved_cache.clear()

    def frame_by_id(frame_id):
        return ensure_project().get("frames", {}).get(frame_id)

    def current_frame():
        return frame_by_id(current_frame_id)

    def frame_order():
        return list(ensure_project().get("frame_order", []))

    def frame_index(frame_id=None):
        frame_id = frame_id or current_frame_id
        try:
            return frame_order().index(frame_id)
        except Exception:
            return -1

    def _find_added_operation(frame, item_id):
        for operation in reversed(frame.get("changes", {}).get("adds", [])):
            value = operation.get("value", {})
            if value.get("id") == item_id:
                return operation
        return None

    def _apply_set_to_state(state, item_id, path, value):
        item, _parent, _kind = find_state_item(state, item_id)
        if item is not None:
            set_path_value(item, path, value)
            return True
        return False

    def apply_frame_changes(state, frame):
        state = clone(state)
        changes = frame.get("changes", {})

        # An item added and removed in the same frame should never appear.
        removed = set(changes.get("removes", []))
        for operation in changes.get("adds", []):
            value = operation.get("value", {})
            if value.get("id") in removed:
                continue
            append_to_parent(
                state,
                operation.get("parent_id"),
                operation.get("collection"),
                value,
                operation.get("root_collection"),
            )

        for item_id, paths in changes.get("sets", {}).items():
            if item_id in removed:
                continue
            for path, value in paths.items():
                _apply_set_to_state(state, item_id, path, value)

        for item_id in removed:
            remove_item_from_state(state, item_id)

        for operation in changes.get("reorders", []):
            reorder_item_in_parent(state, operation.get("item_id"), operation.get("direction", "forward"))

        source_ref = frame.get("source_ref") or {}
        if source_ref:
            state["source_ref"] = clone(source_ref)
        return state

    def resolve_frame(frame_id=None, _stack=None):
        frame_id = frame_id or current_frame_id
        if not frame_id:
            return empty_frame_state()
        if frame_id in resolved_cache:
            return clone(resolved_cache[frame_id])
        frame = frame_by_id(frame_id)
        if frame is None:
            return empty_frame_state()
        stack = set(_stack or [])
        if frame_id in stack:
            log_diagnostic("error", "Frame inheritance cycle detected", {"frame_id": frame_id})
            return empty_frame_state()
        stack.add(frame_id)
        if frame.get("root_state") is not None:
            base = clone(frame.get("root_state"))
        elif frame.get("parent_id"):
            base = resolve_frame(frame.get("parent_id"), stack)
        else:
            base = empty_frame_state()
        result = apply_frame_changes(base, frame)
        resolved_cache[frame_id] = clone(result)
        return result

    def selected_item(state=None):
        state = state or resolve_frame()
        return find_state_item(state, selected_item_id)

    def select_item(item_id, kind=None):
        global selected_item_id, selected_item_kind, bottom_tab
        selected_item_id = item_id
        if kind is None:
            _item, _parent, kind = find_state_item(resolve_frame(), item_id)
        selected_item_kind = kind
        if kind in ("dialogue_controller", "dialogue_event", "dialogue_choice"):
            bottom_tab = "Dialogue"
        restart()

    def clear_selection():
        global selected_item_id, selected_item_kind
        selected_item_id = None
        selected_item_kind = None
        restart()

    def select_frame(frame_id):
        global current_frame_id, selected_item_id, selected_item_kind
        if frame_by_id(frame_id) is None:
            return
        current_frame_id = frame_id
        selected_item_id = None
        selected_item_kind = None
        restart()

    def _history_push(entry):
        history.append(entry)
        del history[:-160]
        redo_stack[:] = []

    def _replace_frame_changes(frame_id, changes):
        global project_dirty
        frame = frame_by_id(frame_id)
        if frame is None:
            return
        frame["changes"] = clone(changes)
        invalidate_resolved_cache()
        project_dirty = True

    def _record_frame_change(label, before, after, frame_id=None):
        frame_id = frame_id or current_frame_id
        if before == after:
            return
        _history_push({
            "type": "frame_changes",
            "label": str(label),
            "frame_id": frame_id,
            "before": clone(before),
            "after": clone(after),
        })

    def undo():
        global current_frame_id, project_dirty
        if not history:
            return
        entry = history.pop()
        redo_stack.append(clone(entry))
        entry_type = entry.get("type")
        if entry_type == "frame_changes":
            _replace_frame_changes(entry.get("frame_id"), entry.get("before", {}))
            current_frame_id = entry.get("frame_id")
        elif entry_type == "add_frame":
            _remove_frame_internal(entry.get("frame", {}).get("id"))
            previous = frame_by_id(entry.get("previous_frame_id"))
            if previous is not None and "previous_stop_before" in entry:
                previous["stop_fallthrough"] = bool(entry.get("previous_stop_before"))
            current_frame_id = entry.get("previous_frame_id")
        elif entry_type == "remove_frame":
            _restore_frame_internal(entry.get("frame"), entry.get("index", -1))
            current_frame_id = entry.get("frame", {}).get("id")
        project_dirty = True
        restart()

    def redo():
        global current_frame_id, project_dirty
        if not redo_stack:
            return
        entry = redo_stack.pop()
        history.append(clone(entry))
        entry_type = entry.get("type")
        if entry_type == "frame_changes":
            _replace_frame_changes(entry.get("frame_id"), entry.get("after", {}))
            current_frame_id = entry.get("frame_id")
        elif entry_type == "add_frame":
            _restore_frame_internal(entry.get("frame"), entry.get("index", -1))
            previous = frame_by_id(entry.get("previous_frame_id"))
            if previous is not None and "previous_stop_after" in entry:
                previous["stop_fallthrough"] = bool(entry.get("previous_stop_after"))
            current_frame_id = entry.get("frame", {}).get("id")
        elif entry_type == "remove_frame":
            _remove_frame_internal(entry.get("frame", {}).get("id"))
            current_frame_id = entry.get("previous_frame_id")
        project_dirty = True
        restart()

    def set_item_value(item_id, path, value, label=None, quiet=False):
        global project_dirty
        frame = current_frame()
        if frame is None or not item_id:
            return
        before = clone(frame.get("changes", {}))
        frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(item_id, {})[str(path)] = clone(value)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        project_dirty = True
        if not quiet:
            _record_frame_change(label or "Edit {}".format(path), before, after)
            restart()

    def clear_item_override(item_id, path):
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        item_sets = frame.setdefault("changes", {}).setdefault("sets", {}).get(item_id, {})
        item_sets.pop(path, None)
        if not item_sets:
            frame["changes"]["sets"].pop(item_id, None)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        _record_frame_change("Revert {}".format(path), before, after)
        restart()

    def has_local_override(item_id, path):
        frame = current_frame()
        if frame is None:
            return False
        return path in frame.get("changes", {}).get("sets", {}).get(item_id, {})

    def parse_editor_value(text, current=None):
        raw = str(text)
        stripped = raw.strip()
        if isinstance(current, bool):
            return stripped.lower() in ("1", "true", "yes", "on")
        if stripped.lower() == "none":
            return None
        if isinstance(current, int) and not isinstance(current, bool):
            try:
                return int(float(stripped))
            except Exception:
                return current
        if isinstance(current, float):
            try:
                return float(stripped)
            except Exception:
                return current
        if stripped.lower() in ("true", "false"):
            return stripped.lower() == "true"
        try:
            if "." in stripped:
                return float(stripped)
            return int(stripped)
        except Exception:
            return raw

    def property_changed(item_id, path):
        def changed(value):
            item, _parent_id, _kind = find_state_item(resolve_frame(), item_id)
            current = get_path_value(item or {}, path, "")
            set_item_value(item_id, path, parse_editor_value(value, current), "Edit {}".format(path))
        return changed

    def toggle_item_value(item_id, path="visible"):
        item, _parent_id, _kind = find_state_item(resolve_frame(), item_id)
        if item is None:
            return
        set_item_value(item_id, path, not bool(get_path_value(item, path, True)), "Toggle {}".format(path))

    def add_change(parent_id, collection, value, root_collection=None, label="Add item"):
        global project_dirty
        frame = current_frame()
        if frame is None:
            return None
        before = clone(frame.get("changes", {}))
        operation = {
            "parent_id": parent_id,
            "collection": collection,
            "root_collection": root_collection,
            "value": clone(value),
        }
        frame.setdefault("changes", {}).setdefault("adds", []).append(operation)
        # If this id was previously removed locally, adding it restores it.
        value_id = value.get("id") if isinstance(value, dict) else None
        if value_id in frame["changes"].setdefault("removes", []):
            frame["changes"]["removes"].remove(value_id)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        project_dirty = True
        _record_frame_change(label, before, after)
        restart()
        return value

    def remove_item(item_id, label="Remove item"):
        global selected_item_id, selected_item_kind, project_dirty
        if not item_id:
            return
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        adds = frame.setdefault("changes", {}).setdefault("adds", [])
        removed_local_add = False
        for index in range(len(adds) - 1, -1, -1):
            value = adds[index].get("value", {})
            if value.get("id") == item_id:
                del adds[index]
                removed_local_add = True
                break
        if not removed_local_add:
            removes = frame["changes"].setdefault("removes", [])
            if item_id not in removes:
                removes.append(item_id)
        frame["changes"].setdefault("sets", {}).pop(item_id, None)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        project_dirty = True
        _record_frame_change(label, before, after)
        if selected_item_id == item_id:
            selected_item_id = None
            selected_item_kind = None
        restart()

    def remove_selected_item():
        remove_item(selected_item_id)

    def reorder_selected(direction):
        global project_dirty
        if not selected_item_id:
            return
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        frame.setdefault("changes", {}).setdefault("reorders", []).append({
            "item_id": selected_item_id,
            "direction": direction,
        })
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        project_dirty = True
        _record_frame_change("Reorder item", before, after)
        restart()

    def copy_selected():
        item, _parent, kind = selected_item()
        if item is None:
            return
        runtime["clipboard"] = {"kind": kind, "value": clone(item)}
        try:
            renpy.notify("Copied {}".format(item.get("name", "item")))
        except Exception:
            pass

    def _renew_ids(value):
        value = clone(value)
        id_map = {}
        def visit(item):
            if isinstance(item, dict):
                if "id" in item:
                    old_id = item.get("id")
                    prefix = str(old_id or "item").split("_", 1)[0]
                    item["id"] = new_id(prefix)
                    id_map[old_id] = item["id"]
                for child in item.values():
                    visit(child)
            elif isinstance(item, list):
                for child in item:
                    visit(child)
        visit(value)
        return value

    def paste_copied():
        copied = runtime.get("clipboard")
        if not copied:
            return
        value = _renew_ids(copied.get("value"))
        kind = copied.get("kind")
        selected, parent_id, selected_kind = selected_item()
        if kind == "scene_node":
            if selected_kind == "scene":
                parent = selected.get("id")
                collection = "nodes"
            elif selected_kind == "scene_node":
                parent = parent_id
                collection = "children" if parent_id and parent_id != selected.get("id") else "nodes"
            else:
                scene = first_scene()
                parent = scene.get("id") if scene else None
                collection = "nodes"
            add_change(parent, collection, value, label="Paste scene item")
        elif kind == "ui_node":
            if selected_kind == "ui_screen":
                parent = selected.get("id")
                collection = "nodes"
            elif selected_kind == "ui_node":
                parent = parent_id
                collection = "children" if parent_id else "nodes"
            else:
                screen = ensure_editor_ui_screen()
                parent = screen.get("id") if screen else None
                collection = "nodes"
            add_change(parent, collection, value, label="Paste UI item")

    def duplicate_selected():
        copy_selected()
        paste_copied()

    def _restore_frame_internal(frame, index=-1):
        if not frame:
            return
        data = ensure_project()
        frame_id = frame.get("id")
        data.setdefault("frames", {})[frame_id] = clone(frame)
        order = data.setdefault("frame_order", [])
        if frame_id in order:
            order.remove(frame_id)
        if index < 0 or index > len(order):
            order.append(frame_id)
        else:
            order.insert(index, frame_id)
        invalidate_resolved_cache()

    def _remove_frame_internal(frame_id):
        data = ensure_project()
        data.get("frames", {}).pop(frame_id, None)
        if frame_id in data.get("frame_order", []):
            data["frame_order"].remove(frame_id)
        invalidate_resolved_cache()

    def add_frame(mode="inherit", name=None, stop_fallthrough=False):
        global current_frame_id, project_dirty
        data = ensure_project()
        previous_id = current_frame_id
        previous = frame_by_id(previous_id)
        previous_stop_before = bool((previous or {}).get("stop_fallthrough", False))
        current_state = resolve_frame(previous_id)
        mode = mode or DEFAULT_NEW_FRAME_MODE
        if mode == "blank":
            frame = new_frame(name or "Blank Frame", parent_id=None, root_state=empty_frame_state())
        elif mode == "detach":
            frame = new_frame(name or "Detached Frame", parent_id=None, root_state=current_state)
        else:
            frame = new_frame(name or "Frame {}".format(len(data.get("frame_order", [])) + 1), parent_id=previous_id)
        frame["stop_fallthrough"] = bool(stop_fallthrough)
        # Extending a branch moves its end marker to the newly-created frame,
        # so the branch never falls through into a neighboring branch.
        if previous is not None and previous_stop_before and mode == "inherit" and not stop_fallthrough:
            previous["stop_fallthrough"] = False
            frame["stop_fallthrough"] = True
        previous_stop_after = bool((previous or {}).get("stop_fallthrough", False))
        index = frame_index(previous_id) + 1 if previous_id else len(data.get("frame_order", []))
        _restore_frame_internal(frame, index)
        _history_push({
            "type": "add_frame",
            "label": "Add frame",
            "frame": clone(frame),
            "index": index,
            "previous_frame_id": previous_id,
            "previous_stop_before": previous_stop_before,
            "previous_stop_after": previous_stop_after,
        })
        current_frame_id = frame.get("id")
        project_dirty = True
        # Dialogue controllers are inherited. Creating a new event is left to
        # the user so a visual-only frame can be made without dialogue.
        restart()
        return frame

    def duplicate_frame_detached():
        frame = current_frame()
        return add_frame("detach", "{} Copy".format(frame.get("name", "Frame") if frame else "Frame"))

    def remove_current_frame():
        global current_frame_id, selected_item_id, selected_item_kind, project_dirty
        frame = current_frame()
        order = frame_order()
        if frame is None or len(order) <= 1:
            return
        index = frame_index(current_frame_id)
        replacement = order[index - 1] if index > 0 else order[index + 1]
        entry = {
            "type": "remove_frame",
            "label": "Remove frame",
            "frame": clone(frame),
            "index": index,
            "previous_frame_id": replacement,
        }
        _remove_frame_internal(current_frame_id)
        current_frame_id = replacement
        selected_item_id = None
        selected_item_kind = None
        _history_push(entry)
        project_dirty = True
        restart()

    def set_frame_name(frame_id, value):
        global project_dirty
        frame = frame_by_id(frame_id)
        if frame is None:
            return
        frame["name"] = str(value or "Frame")
        project_dirty = True
        restart()

    def frame_name_changed(frame_id):
        return lambda value: set_frame_name(frame_id, value)

    def previous_frame():
        index = frame_index()
        order = frame_order()
        if index > 0:
            select_frame(order[index - 1])

    def next_frame():
        index = frame_index()
        order = frame_order()
        if index >= 0 and index + 1 < len(order):
            select_frame(order[index + 1])

    def set_tree_tab(value):
        global selected_tree_tab
        selected_tree_tab = str(value)
        restart()

    def set_bottom_tab(value):
        global bottom_tab
        bottom_tab = str(value)
        restart()

    def set_preview_mode(value):
        global preview_mode
        preview_mode = str(value)
        restart()

    def set_tool_mode(value):
        global tool_mode
        tool_mode = str(value)
        restart()

    def first_scene(state=None):
        state = state or resolve_frame()
        scenes = state.get("scenes", [])
        return scenes[0] if scenes else None

    def preferred_dialogue_scene(state=None):
        state = state or resolve_frame()
        for scene in state.get("scenes", []):
            name = str(scene.get("name", "")).lower()
            if scene.get("type") == "dialogue" or "dialogue" in name:
                return scene
        return first_scene(state)

    def selected_property_groups():
        item, _parent, kind = selected_item()
        if kind == "ui_node":
            groups = list(UI_PROPERTY_GROUPS)
            if item and item.get("type") in ("text", "button", "textbutton"):
                groups = list(TEXT_PROPERTY_GROUPS) + groups
            if item and item.get("type") == "imagebutton":
                groups = list(IMAGE_BUTTON_PROPERTY_GROUPS) + groups
            return groups
        if kind == "scene_node":
            groups = list(SCENE_PROPERTY_GROUPS)
            if item and item.get("type") in ("text", "hotspot"):
                groups = list(TEXT_PROPERTY_GROUPS) + groups
            return groups
        return ()

    def _project_path(filename=None):
        data = ensure_project()
        filename = filename or "{}.json".format(safe_identifier(data.get("project", {}).get("id"), "project"))
        directory = os.path.join(config.gamedir, PROJECT_DIRECTORY)
        return directory, os.path.join(directory, filename)

    def save_project(filename=None):
        global project_dirty
        data = ensure_project()
        data["project"]["updated_at"] = int(time.time())
        directory, path = _project_path(filename)
        try:
            if not os.path.isdir(directory):
                os.makedirs(directory)
            temporary = path + ".tmp"
            with open(temporary, "w", encoding="utf-8") as output:
                json.dump(json_safe(data), output, indent=2, sort_keys=True, ensure_ascii=False)
                output.write("\n")
            os.replace(temporary, path)
            project_dirty = False
            renpy.notify("Live Studio project saved")
            return path
        except Exception as exc:
            log_diagnostic("error", "Could not save project: {}".format(exc), {"path": path})
            renpy.notify("Live Studio save failed")
            return None

    def _migrate_dialogue_state(state):
        if not isinstance(state, dict):
            return
        for controller in state.get("dialogue_controllers", []) or []:
            if not isinstance(controller, dict):
                continue
            if "frame_event_ids" not in controller:
                active_id = controller.get("active_event_id")
                controller["frame_event_ids"] = [active_id] if active_id else []
            controller.setdefault("events", [])
            controller.setdefault("selected_event_id", controller.get("active_event_id"))

    def migrate_project(data):
        if not isinstance(data, dict):
            raise ValueError("Project data is not a dictionary")
        data.setdefault("settings", {})
        data["settings"].setdefault("snap_enabled", SNAP_ENABLED)
        data["settings"].setdefault("grid_enabled", GRID_ENABLED)
        data["settings"].setdefault("grid_size", GRID_SIZE)
        for frame in data.get("frames", {}).values():
            frame.setdefault("source_ref", {})
            _migrate_dialogue_state(frame.get("root_state"))
            changes = frame.setdefault("changes", {})
            changes.setdefault("sets", {})
            adds = changes.setdefault("adds", [])
            changes.setdefault("removes", [])
            changes.setdefault("reorders", [])
            for operation in adds:
                value = operation.get("value") if isinstance(operation, dict) else None
                if isinstance(value, dict) and value.get("events") is not None:
                    _migrate_dialogue_state({"dialogue_controllers": [value]})
            frame.setdefault("edges", [])
            frame.setdefault("stop_fallthrough", False)
        data["version"] = VERSION
        return data


    def saved_project_paths():
        directory, _path = _project_path()
        if not os.path.isdir(directory):
            return []
        result = []
        for filename in sorted(os.listdir(directory), reverse=True):
            if filename.lower().endswith(".json"):
                result.append((filename, os.path.join(directory, filename)))
        return result

    def load_project(path):
        global project_data, current_frame_id, selected_item_id, selected_item_kind, project_dirty
        try:
            with open(path, "r", encoding="utf-8") as source:
                loaded = migrate_project(json.load(source))
            if "frames" not in loaded:
                raise ValueError("Not a Live Studio project")
            project_data = loaded
            order = project_data.get("frame_order", [])
            current_frame_id = project_data.get("project", {}).get("entry_frame_id") or (order[0] if order else None)
            selected_item_id = None
            selected_item_kind = None
            history[:] = []
            redo_stack[:] = []
            invalidate_resolved_cache()
            project_dirty = False
            renpy.notify("Live Studio project loaded")
            restart()
            return True
        except Exception as exc:
            log_diagnostic("error", "Could not load project: {}".format(exc), {"path": path})
            renpy.notify("Live Studio load failed")
            return False
