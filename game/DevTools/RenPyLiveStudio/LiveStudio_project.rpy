# Project, frame inheritance, selection, and lightweight undo/redo.

init -930 python in live_studio:
    import copy
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
    project_dirty = False

    runtime = {
        "snapshot_bytes": None,
        "snapshot_displayable": None,
        "scene_displayables": {},
        "screen_displayables": {},
        "diagnostics": [],
        "capture_source": {},
        "drag": None,
    }

    history = []
    redo_stack = []
    resolved_frame_cache = {}

    def log_diagnostic(level, message, context=None):
        entry = {
            "level": str(level or "info"),
            "message": str(message),
            "context": json_safe(context or {}),
        }
        runtime.setdefault("diagnostics", []).append(entry)
        try:
            renpy.log("[Live Studio:{}] {}".format(entry["level"], entry["message"]))
        except Exception:
            pass

    def clear_diagnostics():
        runtime["diagnostics"] = []
        renpy.restart_interaction()

    def ensure_project(name="Untitled Live Studio Project"):
        global project_data
        if not isinstance(project_data, dict):
            project_data = new_project(name)
        return project_data

    def project_name():
        data = ensure_project()
        return data.get("project", {}).get("name", "Untitled Live Studio Project")

    def set_project_name(value):
        global project_dirty
        data = ensure_project()
        before = data.get("project", {}).get("name", "")
        after = str(value or "Untitled Live Studio Project")
        if before == after:
            return
        data["project"]["name"] = after
        data["project"]["id"] = safe_identifier(after.lower(), "project")
        data["project"]["updated_at"] = int(time.time())
        project_dirty = True
        renpy.restart_interaction()

    def invalidate_resolved_cache():
        resolved_frame_cache.clear()

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
        except ValueError:
            return -1

    def apply_frame_changes(state, frame):
        changes = frame.get("changes", {})

        # Additions are applied before removals so an item created and then
        # deleted in the same frame does not reappear when the frame resolves.
        for add in changes.get("adds", []):
            parent_id = add.get("parent_id")
            collection = add.get("collection")
            value = add.get("value")
            if parent_id and collection and isinstance(value, dict):
                append_to_parent(state, parent_id, collection, value)
            elif add.get("root_collection") in ("scenes", "ui_screens", "dialogue_controllers"):
                state.setdefault(add["root_collection"], []).append(clone(value))

        for item_id in changes.get("removes", []):
            remove_item_from_state(state, item_id)

        for item_id, values in changes.get("sets", {}).items():
            target, _parent_id, _kind = find_state_item(state, item_id)
            if target is None:
                continue
            for path, value in values.items():
                set_path_value(target, path, clone(value))

        return state

    def resolve_frame(frame_id=None, _stack=None):
        frame_id = frame_id or current_frame_id
        if not frame_id:
            return empty_frame_state()
        if frame_id in resolved_frame_cache:
            return clone(resolved_frame_cache[frame_id])

        frame = frame_by_id(frame_id)
        if frame is None:
            return empty_frame_state()

        _stack = list(_stack or [])
        if frame_id in _stack:
            log_diagnostic("error", "Frame inheritance cycle detected.", {"frame_id": frame_id})
            return empty_frame_state()
        _stack.append(frame_id)

        if frame.get("root_state") is not None:
            state = clone(frame.get("root_state"))
        elif frame.get("parent_id"):
            state = resolve_frame(frame.get("parent_id"), _stack)
        else:
            state = empty_frame_state()

        apply_frame_changes(state, frame)
        resolved_frame_cache[frame_id] = clone(state)
        return state

    def select_frame(frame_id):
        global current_frame_id, selected_item_id, selected_item_kind
        if frame_by_id(frame_id) is None:
            return
        current_frame_id = frame_id
        selected_item_id = None
        selected_item_kind = None
        renpy.restart_interaction()

    def selected_item():
        state = resolve_frame()
        return find_state_item(state, selected_item_id)

    def select_item(item_id, kind=None):
        global selected_item_id, selected_item_kind
        item, _parent_id, found_kind = find_state_item(resolve_frame(), item_id)
        if item is None:
            selected_item_id = None
            selected_item_kind = None
        else:
            selected_item_id = item_id
            selected_item_kind = kind or found_kind
            if found_kind in ("dialogue_controller", "dialogue_event", "dialogue_choice"):
                set_bottom_tab("Dialogue")
        renpy.restart_interaction()

    def clear_selection():
        global selected_item_id, selected_item_kind
        selected_item_id = None
        selected_item_kind = None
        renpy.restart_interaction()

    def _history_push(entry):
        history.append(entry)
        if len(history) > 150:
            del history[0]
        redo_stack[:] = []

    def _replace_frame_changes(frame_id, changes):
        frame = frame_by_id(frame_id)
        if frame is None:
            return
        frame["changes"] = clone(changes)
        invalidate_resolved_cache()

    def _record_frame_change(label, before, after, frame_id=None):
        global project_dirty
        frame_id = frame_id or current_frame_id
        if before == after:
            return
        _history_push({
            "type": "frame_changes",
            "label": label,
            "frame_id": frame_id,
            "before": clone(before),
            "after": clone(after),
        })
        project_dirty = True

    def undo():
        global project_dirty
        if not history:
            return
        entry = history.pop()
        if entry.get("type") == "frame_changes":
            _replace_frame_changes(entry.get("frame_id"), entry.get("before", {}))
        elif entry.get("type") == "add_frame":
            _remove_frame_internal(entry.get("frame", {}).get("id"))
            select_frame(entry.get("previous_frame_id"))
        elif entry.get("type") == "remove_frame":
            _restore_frame_internal(entry.get("frame"), entry.get("index", -1))
            select_frame(entry.get("frame", {}).get("id"))
        redo_stack.append(entry)
        project_dirty = True
        renpy.restart_interaction()

    def redo():
        global project_dirty
        if not redo_stack:
            return
        entry = redo_stack.pop()
        if entry.get("type") == "frame_changes":
            _replace_frame_changes(entry.get("frame_id"), entry.get("after", {}))
        elif entry.get("type") == "add_frame":
            _restore_frame_internal(entry.get("frame"), entry.get("index", -1))
            select_frame(entry.get("frame", {}).get("id"))
        elif entry.get("type") == "remove_frame":
            _remove_frame_internal(entry.get("frame", {}).get("id"))
            select_frame(entry.get("previous_frame_id"))
        history.append(entry)
        project_dirty = True
        renpy.restart_interaction()

    def set_item_value(item_id, path, value, label=None):
        frame = current_frame()
        if frame is None or not item_id or not path:
            return
        before = clone(frame.get("changes", {}))
        sets = frame.setdefault("changes", {}).setdefault("sets", {})
        sets.setdefault(item_id, {})[path] = clone(value)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        _record_frame_change(label or "Set {}".format(path), before, after)
        renpy.restart_interaction()

    def clear_item_override(item_id, path):
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        sets = frame.setdefault("changes", {}).setdefault("sets", {})
        item_sets = sets.get(item_id, {})
        if path in item_sets:
            del item_sets[path]
        if not item_sets and item_id in sets:
            del sets[item_id]
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        _record_frame_change("Revert {}".format(path), before, after)
        renpy.restart_interaction()

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
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        frame.setdefault("changes", {}).setdefault("adds", []).append({
            "parent_id": parent_id,
            "collection": collection,
            "root_collection": root_collection,
            "value": clone(value),
        })
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        _record_frame_change(label, before, after)
        renpy.restart_interaction()

    def remove_selected_item():
        global selected_item_id, selected_item_kind
        if not selected_item_id:
            return
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        removes = frame.setdefault("changes", {}).setdefault("removes", [])
        if selected_item_id not in removes:
            removes.append(selected_item_id)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        _record_frame_change("Remove item", before, after)
        selected_item_id = None
        selected_item_kind = None
        renpy.restart_interaction()

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

    def add_frame(mode="inherit", name=None):
        global current_frame_id, project_dirty
        data = ensure_project()
        previous_id = current_frame_id
        current_state = resolve_frame(previous_id)
        mode = mode or DEFAULT_NEW_FRAME_MODE
        if mode == "blank":
            frame = new_frame(name or "Blank Frame", parent_id=None, root_state=empty_frame_state())
        elif mode == "detach":
            frame = new_frame(name or "Detached Frame", parent_id=None, root_state=current_state)
        else:
            frame = new_frame(name or "Frame {}".format(len(data.get("frame_order", [])) + 1), parent_id=previous_id, root_state=None)
        index = frame_index(previous_id) + 1 if previous_id else len(data.get("frame_order", []))
        _restore_frame_internal(frame, index)
        _history_push({
            "type": "add_frame",
            "label": "Add frame",
            "frame": clone(frame),
            "index": index,
            "previous_frame_id": previous_id,
        })
        current_frame_id = frame.get("id")
        project_dirty = True
        renpy.restart_interaction()
        return frame

    def duplicate_frame_detached():
        return add_frame("detach", "{} Copy".format(current_frame().get("name", "Frame") if current_frame() else "Frame"))

    def remove_current_frame():
        global current_frame_id, selected_item_id, selected_item_kind, project_dirty
        frame = current_frame()
        if frame is None or len(frame_order()) <= 1:
            return
        order = frame_order()
        index = frame_index(current_frame_id)
        previous_id = order[index - 1] if index > 0 else order[index + 1]
        entry = {
            "type": "remove_frame",
            "label": "Remove frame",
            "frame": clone(frame),
            "index": index,
            "previous_frame_id": previous_id,
        }
        _remove_frame_internal(current_frame_id)
        current_frame_id = previous_id
        selected_item_id = None
        selected_item_kind = None
        _history_push(entry)
        project_dirty = True
        renpy.restart_interaction()

    def set_frame_name(frame_id, value):
        global project_dirty
        frame = frame_by_id(frame_id)
        if frame is None:
            return
        frame["name"] = str(value or "Frame")
        project_dirty = True
        renpy.restart_interaction()

    def frame_name_changed(frame_id):
        def changed(value):
            set_frame_name(frame_id, value)
        return changed

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
        renpy.restart_interaction()

    def set_bottom_tab(value):
        global bottom_tab
        bottom_tab = str(value)
        renpy.restart_interaction()

    def set_preview_mode(value):
        global preview_mode
        preview_mode = str(value)
        renpy.restart_interaction()

    def project_setting(name, default=False):
        return ensure_project().get("settings", {}).get(name, default)

    def toggle_project_setting(name):
        global project_dirty
        settings = ensure_project().setdefault("settings", {})
        settings[name] = not bool(settings.get(name, False))
        project_dirty = True
        renpy.restart_interaction()

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
            log_diagnostic("error", "Could not save project: {}".format(exc))
            renpy.notify("Live Studio save failed")
            return None

    def load_project(path):
        global project_data, current_frame_id, selected_item_id, selected_item_kind, project_dirty
        try:
            with open(path, "r", encoding="utf-8") as source:
                loaded = json.load(source)
            if not isinstance(loaded, dict) or "frames" not in loaded:
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
            renpy.restart_interaction()
            return True
        except Exception as exc:
            log_diagnostic("error", "Could not load project: {}".format(exc), {"path": path})
            renpy.notify("Live Studio load failed")
            return False
