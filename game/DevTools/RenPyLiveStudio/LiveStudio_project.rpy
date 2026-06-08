# Project state, frame inheritance, selection, commands, and persistence.

init -980 python in live_studio:
    import ast as _literal_ast
    import json
    import os
    import time

    project_data = None
    current_frame_id = None
    selected_item_id = None
    selected_item_kind = None
    selected_tree_tab = "Scene"
    bottom_tab = "Assets"
    script_popup_open = False
    project_popup_open = False
    settings_popup_open = False
    create_popup_open = False
    future_popup_open = False
    script_export_section = "story"
    workspace_mode = "Default"
    asset_view_mode = "grid"
    preview_mode = DEFAULT_PREVIEW_MODE
    tool_mode = "select"
    right_panel_tab = "Layers"
    layer_panel_mode = "Scene"
    canvas_zoom = 1.0
    expanded_property_groups = set(("Position", "Size & Transform", "Size & Layout", "Text"))
    expanded_tree_items = set()
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
        "screen_raw_roots": {},
        "screen_frozen_roots": {},
        "screen_displayables": {},
        "screen_index": {},
        "active_screen_ids": set(),
        "active_screen_names": [],
        "dialogue_presentation_roots": [],
        "frame_preview_refs": {},
        "active_preview_frame_id": None,
        "active_preview_source_frame_id": None,
        "drag": None,
        "resize": None,
        "clipboard": None,
        "export_previews": {},
        "source_trace": [],
        "opened": False,
        "state_revision": 0,
        "canvas_cache": {},
        "canvas_item_cache": {},
        "captured_screen_preview_cache": {},
        "item_thumbnail_cache": {},
        "bounds_cache": {},
        "widget_override_cache": {},
        "preview_source_cache": {},
        "canvas_instance": None,
        "pending_input_edits": {},
        "editor_input_values": {},
        "input_last_edit_time": 0.0,
        "drag_revision": 0,
        "last_drag_render_time": 0.0,
        "canvas_animation_epoch": time.time(),
        "last_canvas_click": None,
        "source_flow_status": "",
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
            try:
                super(EditorInputValue, self).__init__()
            except Exception:
                pass
            self.kind = str(kind)
            self.arguments = tuple(arguments)
            self.buffer = None

        def __eq__(self, other):
            return type(self) is type(other) and self.kind == other.kind and self.arguments == other.arguments

        def __ne__(self, other):
            return not self == other

        def current_text(self):
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

        def get_text(self):
            if self.buffer is not None:
                return self.buffer
            return self.current_text()

        def set_text(self, value):
            # Keep an editable buffer while the field has focus. Parsing and
            # mutating numeric properties on every keystroke made values such as
            # "-24" or "0.5" impossible to enter because the temporary "-" and
            # "0." states were immediately rejected and replaced.
            self.buffer = str(value)

        def commit(self):
            if self.buffer is None:
                return False
            value = self.buffer
            self.buffer = None
            old_text = self.current_text()
            if value == old_text:
                return False
            if self.kind == "project_name":
                set_project_name_live(value)
            elif self.kind == "frame_name":
                set_frame_name_live(self.arguments[0], value)
            elif self.kind == "property":
                set_property_value_live(self.arguments[0], self.arguments[1], value)
                _flush_pending_key(_pending_edit_key("property", current_frame_id, self.arguments[0], self.arguments[1]))
            elif self.kind == "action":
                set_action_value_live(self.arguments[0], self.arguments[1], value)
                _flush_pending_key(_pending_edit_key("action", current_frame_id, self.arguments[0], self.arguments[1]))
            return True

        def enter(self):
            if self.commit():
                restart()
            return None

        def lose_focus(self):
            if self.commit():
                restart()

    def editor_input_value(kind, *arguments):
        frame_key = current_frame_id if str(kind) in ("property", "action") else None
        key = (frame_key, str(kind), tuple(arguments))
        cache = runtime.setdefault("editor_input_values", {})
        value = cache.get(key)
        if value is None:
            value = EditorInputValue(kind, *arguments)
            cache[key] = value
        if len(cache) > 320:
            for old_key in list(cache.keys())[:-240]:
                old_value = cache.get(old_key)
                if old_value is not None and old_value.buffer is not None:
                    continue
                cache.pop(old_key, None)
        return value

    def commit_buffered_editor_inputs():
        changed = False
        for value in list(runtime.setdefault("editor_input_values", {}).values()):
            try:
                changed = value.commit() or changed
            except Exception as exc:
                log_diagnostic("warning", "Inspector value could not be committed", repr(exc))
        return changed


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

    def set_project_name_live(value):
        global project_dirty
        data = ensure_project()
        data.setdefault("project", {})["name"] = str(value or "Untitled Live Studio Project")
        if not data["project"].get("id"):
            data["project"]["id"] = safe_identifier(value, "project")
        project_dirty = True

    def set_frame_name_live(frame_id, value):
        global project_dirty
        frame = frame_by_id(frame_id)
        if frame is None:
            return
        frame["name"] = str(value or "Frame")
        project_dirty = True

    def _pending_edit_key(kind, frame_id, item_id, path):
        return "{}|{}|{}|{}".format(kind, frame_id or "", item_id or "", path or "")

    def _begin_pending_frame_edit(kind, item_id, path, label):
        pending = runtime.setdefault("pending_input_edits", {})
        key = _pending_edit_key(kind, current_frame_id, item_id, path)
        # A new field commits the previous field as one undo entry. This keeps
        # typing responsive while preserving useful field-level undo behavior.
        for old_key in list(pending.keys()):
            if old_key != key:
                _flush_pending_key(old_key)
        if key not in pending:
            frame = current_frame()
            pending[key] = {
                "frame_id": current_frame_id,
                "item_id": item_id,
                "path": path,
                "label": label,
                "before": clone((frame or {}).get("changes", {})),
            }
        runtime["input_last_edit_time"] = time.time()
        return key

    def _flush_pending_key(key):
        pending = runtime.setdefault("pending_input_edits", {})
        session = pending.pop(key, None)
        if not session:
            return False
        frame = frame_by_id(session.get("frame_id"))
        if frame is None:
            return False
        after = clone(frame.get("changes", {}))
        _record_frame_change(session.get("label", "Edit property"), session.get("before", {}), after, session.get("frame_id"))
        _preserve_edited_current_state(session.get("frame_id"))
        return True

    def flush_pending_input_edits(restart_ui=False):
        buffered_changed = commit_buffered_editor_inputs()
        pending = runtime.setdefault("pending_input_edits", {})
        changed = buffered_changed
        for key in list(pending.keys()):
            changed = _flush_pending_key(key) or changed
        if restart_ui and changed:
            restart()
        return changed

    def invalidate_view_caches(clear_runtime_previews=False, reason="view change"):
        """Refresh editor-derived views without discarding captured roots."""
        runtime["last_invalidation_reason"] = str(reason)
        runtime["state_revision"] = int(runtime.get("state_revision", 0)) + 1
        runtime["canvas_cache"] = {}
        runtime["canvas_item_cache"] = {}
        runtime["bounds_cache"] = {}
        runtime["widget_override_cache"] = {}
        runtime["preview_source_cache"] = {}
        runtime["item_thumbnail_cache"] = {}
        if clear_runtime_previews:
            runtime["captured_screen_preview_cache"] = {}
        request_canvas_redraw()

    def flush_pending_input_edits_if_idle(delay=0.65):
        if not runtime.get("pending_input_edits"):
            return
        if time.time() - float(runtime.get("input_last_edit_time", 0.0) or 0.0) >= float(delay):
            flush_pending_input_edits(restart_ui=True)

    def _drop_item_thumbnail(item_id):
        cache = runtime.setdefault("item_thumbnail_cache", {})
        for key in list(cache.keys()):
            if key and key[0] == item_id:
                cache.pop(key, None)

    def _mark_live_item_edit(item_id, clear_screen_preview=True):
        """Invalidates render/layout caches for one item edit.

        Resolved frame states are immutable derived snapshots. Runtime preview
        roots are retained unless the edited item belongs to that captured
        screen, preventing unrelated Scene edits from rebuilding gameplay UI.
        """
        runtime["state_revision"] = int(runtime.get("state_revision", 0)) + 1
        runtime["canvas_cache"] = {}
        runtime["canvas_item_cache"] = {}
        runtime["bounds_cache"] = {}
        runtime["widget_override_cache"] = {}
        runtime["preview_source_cache"] = {}
        _drop_item_thumbnail(item_id)
        if clear_screen_preview:
            state = resolved_cache.get(current_frame_id)
            screen = screen_for_node(state, item_id) if state is not None and "screen_for_node" in globals() else None
            if screen is not None:
                cache = runtime.setdefault("captured_screen_preview_cache", {})
                for key in list(cache.keys()):
                    if key and key[0] == screen.get("id"):
                        cache.pop(key, None)
        request_canvas_redraw()

    def _preserve_edited_current_state(frame_id):
        state = resolved_cache.get(frame_id)
        resolved_cache.clear()
        if state is not None:
            resolved_cache[frame_id] = state

    def set_property_value_live(item_id, path, text):
        global project_dirty, preview_mode
        frame = current_frame()
        if frame is None or not item_id:
            return False
        state = resolve_frame()
        item, _parent_id, item_kind = find_state_item(state, item_id)
        if item is None:
            log_diagnostic("warning", "Property edit targeted a missing item", {"item_id": item_id, "path": path})
            return False
        if item_kind == "ui_node":
            screen = screen_for_node(state, item_id) if "screen_for_node" in globals() else None
            if screen is not None and not screen.get("managed") and not item.get("widget_id"):
                log_diagnostic("warning", "Runtime UI node has no authored widget id and is inspect-only", {
                    "screen": screen.get("name"), "item": item.get("name"), "path": path,
                })
                try:
                    renpy.notify("This runtime UI item has no Ren'Py id. Convert the screen explicitly before editing it.")
                except Exception:
                    pass
                return False
        current = get_path_value(item, path, "")
        value = parse_editor_value(text, current)
        _begin_pending_frame_edit("property", item_id, path, "Edit {}".format(path))
        frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(item_id, {})[str(path)] = clone(value)
        # Resolved frame states remain derived snapshots. Earlier builds mutated
        # the cached item in place, which could leave a value visible after undo
        # or carry a partial edit into descendants. Input is buffered, so a clean
        # resolve at commit time is both correct and fast enough.
        if str(path).startswith(("properties.", "binding.")) and item_kind in ("scene_node", "ui_node"):
            preview_mode = "layout"
        project_dirty = True
        invalidate_resolved_cache(False, "property committed: {}".format(path))
        return True

    def set_action_value_live(node_id, field, text):
        state = resolve_frame()
        node, _parent_id, kind = find_state_item(state, node_id)
        if kind not in ("ui_node", "scene_node"):
            return
        actions = clone(node.get("actions", []))
        if not actions:
            actions = [new_action("none")]
        actions[0][field] = parse_editor_value(text, actions[0].get(field, ""))
        _begin_pending_frame_edit("action", node_id, field, "Edit button action")
        frame = current_frame()
        frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(node_id, {})["actions"] = actions
        global project_dirty
        project_dirty = True
        invalidate_resolved_cache(False, "action committed")

    def project_setting(name, default=False):
        return ensure_project().get("settings", {}).get(name, default)

    def set_project_setting(name, value):
        global project_dirty
        ensure_project().setdefault("settings", {})[str(name)] = clone(value)
        project_dirty = True
        # Editor/capture preferences do not alter the resolved frame model.
        # Clearing it caused unrelated screen roots to rebuild after toggles.
        invalidate_view_caches(False, "setting changed: {}".format(name))
        restart()

    def toggle_project_setting(name):
        set_project_setting(name, not bool(project_setting(name, False)))

    def toggle_ui_capture_engine_filter():
        """Toggle whether Ren'Py/common/developer chrome is filtered from UI capture.

        The setting applies to future captures and fresh captures. It does not
        silently recapture the current frame, because that could discard local
        editor changes.
        """
        new_value = not bool(project_setting("ui_capture_filter_engine_screens", UI_CAPTURE_FILTER_ENGINE_SCREENS))
        set_project_setting("ui_capture_filter_engine_screens", new_value)
        log_diagnostic("info", "UI capture engine-screen filter {}".format("enabled" if new_value else "disabled"), "Use Fresh Capture to rebuild this frame with the new capture filter.")

    def request_canvas_redraw():
        canvas = runtime.get("canvas_instance")
        if canvas is not None:
            try:
                renpy.redraw(canvas, 0)
            except Exception:
                pass

    def invalidate_resolved_cache(clear_runtime_previews=False, reason="project mutation"):
        runtime["last_invalidation_reason"] = str(reason)
        resolved_cache.clear()
        runtime["state_revision"] = int(runtime.get("state_revision", 0)) + 1
        runtime["canvas_cache"] = {}
        runtime["canvas_item_cache"] = {}
        runtime["bounds_cache"] = {}
        runtime["widget_override_cache"] = {}
        runtime["preview_source_cache"] = {}
        if clear_runtime_previews:
            runtime["captured_screen_preview_cache"] = {}
            runtime["item_thumbnail_cache"] = {}
        request_canvas_redraw()

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
            # Resolved states are treated as read-only snapshots. Returning the
            # cached object avoids deep-copying a potentially 1,000+ widget UI
            # tree every time a screen expression asks for the current frame.
            return resolved_cache[frame_id]
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
        resolved_cache[frame_id] = result
        return result

    def selected_item(state=None):
        state = state or resolve_frame()
        return find_state_item(state, selected_item_id)

    def validate_selection(state=None):
        global selected_item_id, selected_item_kind
        if not selected_item_id:
            return False
        state = state or resolve_frame()
        item, _parent, kind = find_state_item(state, selected_item_id)
        if item is not None:
            if selected_item_kind != kind:
                selected_item_kind = kind
            return False
        selected_item_id = None
        selected_item_kind = None
        runtime["drag"] = None
        return True

    def select_item_live(item_id, kind=None):
        """Changes selection without rebuilding the whole editor screen.

        Canvas selection and drag begin in the same mouse event. Scheduling a
        full restart between those two operations made direct manipulation feel
        detached and could cancel the first drag frame on large captured UIs.
        """
        global selected_item_id, selected_item_kind, bottom_tab
        flush_pending_input_edits()
        if kind is None:
            _item, _parent, kind = find_state_item(resolve_frame(), item_id)
        if item_id == selected_item_id and kind == selected_item_kind:
            return False
        selected_item_id = item_id
        selected_item_kind = kind
        if kind in ("dialogue_controller", "dialogue_event", "dialogue_choice"):
            bottom_tab = "Dialogue"
        request_canvas_redraw()
        return True

    def select_item(item_id, kind=None):
        if select_item_live(item_id, kind):
            restart()

    def clear_selection_live():
        global selected_item_id, selected_item_kind
        flush_pending_input_edits()
        if selected_item_id is None and selected_item_kind is None:
            return False
        selected_item_id = None
        selected_item_kind = None
        request_canvas_redraw()
        return True

    def clear_selection():
        if clear_selection_live():
            restart()

    def select_frame(frame_id):
        global current_frame_id, selected_item_id, selected_item_kind, preview_mode
        flush_pending_input_edits()
        if frame_by_id(frame_id) is None:
            return
        if frame_id == current_frame_id:
            return
        current_frame_id = frame_id
        if "activate_runtime_preview_refs" in globals():
            activate_runtime_preview_refs(frame_id)
        selected_item_id = None
        selected_item_kind = None
        preview_mode = "layout"
        runtime["drag"] = None
        runtime.pop("source_candidates", None)
        runtime.pop("source_candidates_key", None)
        invalidate_view_caches(clear_runtime_previews=False)
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
        global current_frame_id, project_dirty, preview_mode
        flush_pending_input_edits()
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
        if "activate_runtime_preview_refs" in globals():
            activate_runtime_preview_refs(current_frame_id)
        project_dirty = True
        preview_mode = "layout"
        validate_selection()
        restart()

    def redo():
        global current_frame_id, project_dirty, preview_mode
        flush_pending_input_edits()
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
        if "activate_runtime_preview_refs" in globals():
            activate_runtime_preview_refs(current_frame_id)
        project_dirty = True
        preview_mode = "layout"
        validate_selection()
        restart()

    def set_item_value(item_id, path, value, label=None, quiet=False):
        global project_dirty, preview_mode
        frame = current_frame()
        if frame is None or not item_id:
            return
        before = clone(frame.get("changes", {}))
        frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(item_id, {})[str(path)] = clone(value)
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        # Any visual property edit should immediately show the rebuilt scene,
        # not the immutable exact-capture screenshot.
        if str(path).startswith(("properties.", "binding.")):
            _item, _parent_id, item_kind = find_state_item(resolve_frame(), item_id)
            if item_kind in ("scene_node", "ui_node"):
                preview_mode = "layout"
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
        """Parse inspector text without evaluating arbitrary Python.

        Numeric values keep their numeric type, and tuple/list/dict properties
        such as padding, outlines, and crop use ``ast.literal_eval``. Dynamic
        text expressions are stored separately under ``binding.expression`` and
        are intentionally left as source strings.
        """
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
        looks_literal = bool(stripped) and stripped.startswith(("(", "[", "{", "'", '"')) and stripped.endswith((")", "]", "}", "'", '"'))
        if isinstance(current, (tuple, list, dict, set)) or looks_literal:
            try:
                value = _literal_ast.literal_eval(stripped)
                if isinstance(current, tuple) and isinstance(value, list):
                    value = tuple(value)
                return value
            except Exception:
                if isinstance(current, (tuple, list, dict, set)):
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

    def _item_contains_id(item, target_id):
        if not item or not target_id:
            return False
        if item.get("id") == target_id:
            return True
        for child, _parent, _depth in walk_nodes(item.get("children", item.get("nodes", []))):
            if child.get("id") == target_id:
                return True
        for event in item.get("events", []):
            if event.get("id") == target_id:
                return True
            if any(choice.get("id") == target_id for choice in event.get("choices", [])):
                return True
        return False

    def remove_item(item_id, label="Remove item"):
        global selected_item_id, selected_item_kind, project_dirty
        if not item_id:
            return
        frame = current_frame()
        if frame is None:
            return
        state_before = resolve_frame()
        removed_object, _removed_parent, _removed_kind = find_state_item(state_before, item_id)
        if removed_object is None:
            return
        selection_is_removed = _item_contains_id(removed_object, selected_item_id)
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
        if selection_is_removed:
            selected_item_id = None
            selected_item_kind = None
        runtime["drag"] = None
        request_canvas_redraw()
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
        if "drop_runtime_preview_refs" in globals():
            drop_runtime_preview_refs(frame_id)
        invalidate_resolved_cache()

    def add_frame(mode="inherit", name=None, stop_fallthrough=False):
        global current_frame_id, project_dirty, preview_mode
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
        if mode == "detach" and "inherit_runtime_preview_refs" in globals():
            inherit_runtime_preview_refs(frame.get("id"), previous_id)
        if "activate_runtime_preview_refs" in globals():
            activate_runtime_preview_refs(frame.get("id"))
        preview_mode = "layout"
        project_dirty = True
        runtime.pop("source_candidates", None)
        runtime.pop("source_candidates_key", None)
        # Dialogue controllers are inherited. Creating a new event is left to
        # the user so a visual-only frame can be made without dialogue.
        restart()
        return frame

    def duplicate_frame_detached():
        frame = current_frame()
        return add_frame("detach", "{} Copy".format(frame.get("name", "Frame") if frame else "Frame"))

    def remove_current_frame():
        global current_frame_id, selected_item_id, selected_item_kind, project_dirty, preview_mode
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
        if "activate_runtime_preview_refs" in globals():
            activate_runtime_preview_refs(replacement)
        selected_item_id = None
        selected_item_kind = None
        preview_mode = "layout"
        _history_push(entry)
        project_dirty = True
        restart()

    def set_frame_name(frame_id, value):
        set_frame_name_live(frame_id, value)
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


    def toggle_future_popup(force=None):
        global future_popup_open, script_popup_open, project_popup_open, settings_popup_open, create_popup_open
        opening = (not future_popup_open) if force is None else bool(force)
        script_popup_open = False
        project_popup_open = False
        settings_popup_open = False
        create_popup_open = False
        future_popup_open = opening
        restart()

    def set_tree_tab(value):
        global selected_tree_tab, layer_panel_mode
        value = "UI" if str(value).lower() == "ui" else "Scene"
        if selected_tree_tab == value and layer_panel_mode == value:
            return
        selected_tree_tab = value
        layer_panel_mode = value
        request_canvas_redraw()
        restart()

    def set_bottom_tab(value):
        global bottom_tab
        value = str(value)
        if value == "Export":
            open_script_popup()
            return
        bottom_tab = value if value in ("Assets", "Dialogue") else "Assets"
        restart()

    def close_all_popups(restart_ui=True):
        global script_popup_open, project_popup_open, settings_popup_open, create_popup_open, future_popup_open
        changed = bool(script_popup_open or project_popup_open or settings_popup_open or create_popup_open or future_popup_open)
        script_popup_open = False
        project_popup_open = False
        settings_popup_open = False
        create_popup_open = False
        future_popup_open = False
        if changed and restart_ui:
            restart()
        return changed

    def popup_is_open():
        return bool(script_popup_open or project_popup_open or settings_popup_open or create_popup_open or future_popup_open)

    def open_script_popup():
        global script_popup_open, project_popup_open, settings_popup_open, create_popup_open, future_popup_open
        flush_pending_input_edits()
        try:
            generate_exports()
        except Exception as exc:
            log_diagnostic("error", "Code preview generation failed", repr(exc))
        project_popup_open = False
        settings_popup_open = False
        create_popup_open = False
        future_popup_open = False
        if script_popup_open:
            return
        script_popup_open = True
        restart()

    def close_script_popup():
        global script_popup_open
        if not script_popup_open:
            return
        script_popup_open = False
        restart()

    def toggle_project_popup():
        global project_popup_open, script_popup_open, settings_popup_open, create_popup_open, future_popup_open
        opening = not project_popup_open
        script_popup_open = False
        settings_popup_open = False
        create_popup_open = False
        future_popup_open = False
        project_popup_open = opening
        restart()

    def toggle_settings_popup():
        global settings_popup_open, script_popup_open, project_popup_open, create_popup_open, future_popup_open
        opening = not settings_popup_open
        script_popup_open = False
        project_popup_open = False
        create_popup_open = False
        future_popup_open = False
        settings_popup_open = opening
        restart()

    def toggle_create_popup():
        global create_popup_open, script_popup_open, project_popup_open, settings_popup_open, future_popup_open
        opening = not create_popup_open
        script_popup_open = False
        project_popup_open = False
        settings_popup_open = False
        future_popup_open = False
        create_popup_open = opening
        restart()

    def new_blank_project_from_ui():
        close_all_popups(restart_ui=False)
        begin_blank_project("Untitled Live Studio Project")

    def new_capture_project_from_ui():
        close_all_popups(restart_ui=False)
        source = clone(runtime.get("capture_source") or capture_source_reference())
        begin_capture_project("Captured Ren'Py Project", source, keep_snapshot=True)
        restart()

    def save_project_from_ui():
        save_project()
        close_all_popups()

    def load_project_from_ui(path):
        if isinstance(path, (tuple, list)) and len(path) > 1:
            path = path[1]
        if load_project(path):
            close_all_popups()

    def set_script_export_section(value):
        global script_export_section
        value = str(value or "story")
        if value not in ("story", "screens", "helpers"):
            value = "story"
        if script_export_section == value:
            return
        script_export_section = value
        restart()

    def request_full_preview():
        # The dedicated whole-scene preview runner is intentionally not wired
        # yet. Most importantly, this button must not toggle the editor between
        # exact capture and editable layout modes.
        try:
            renpy.notify("Full scene preview is not implemented yet")
        except Exception:
            pass

    def consume_event():
        # Used by modal overlays to prevent otherwise-unhandled clicks from
        # falling through into controls underneath the overlay.
        raise renpy.IgnoreEvent()

    def set_preview_mode(value):
        global preview_mode
        preview_mode = str(value)
        restart()

    def set_tool_mode(value):
        global tool_mode
        tool_mode = str(value)
        restart()

    def set_workspace_mode(value):
        global workspace_mode, bottom_tab
        value = str(value or "Default")
        if value not in ("Default", "Scene", "UI", "Dialogue"):
            value = "Default"
        if workspace_mode == value:
            return
        workspace_mode = value
        if value == "Scene":
            set_tree_tab("Scene")
            return
        if value == "UI":
            set_tree_tab("UI")
            return
        if value == "Dialogue":
            bottom_tab = "Dialogue"
        restart()

    def cycle_workspace_mode():
        values = ("Default", "Scene", "UI", "Dialogue")
        try:
            index = values.index(workspace_mode)
        except ValueError:
            index = 0
        set_workspace_mode(values[(index + 1) % len(values)])

    def set_asset_view_mode(value):
        global asset_view_mode
        value = "list" if str(value).lower() == "list" else "grid"
        if asset_view_mode == value:
            return
        asset_view_mode = value
        restart()

    def set_right_panel_tab(value):
        global right_panel_tab
        value = str(value or "Layers")
        if value in ("Structure", "Inspector", "Debug"):
            value = "Debugger"
        if value not in ("Layers", "History", "Debugger"):
            value = "Layers"
        if right_panel_tab == value:
            return
        right_panel_tab = value
        restart()

    def set_layer_panel_mode(value):
        global layer_panel_mode, selected_tree_tab
        # str.title() turns "UI" into "Ui", which made the UI layer button
        # immediately fall back to Scene mode. Normalize the domain explicitly.
        value = "UI" if str(value or "Scene").lower() == "ui" else "Scene"
        if layer_panel_mode == value and selected_tree_tab == value:
            return
        layer_panel_mode = value
        selected_tree_tab = value
        request_canvas_redraw()
        restart()

    def select_layer_item(item_id, kind):
        global selected_tree_tab, layer_panel_mode
        is_ui = str(kind).startswith("ui")
        wanted = "UI" if is_ui else "Scene"
        tab_changed = selected_tree_tab != wanted or layer_panel_mode != wanted
        selected_tree_tab = wanted
        layer_panel_mode = wanted
        selection_changed = select_item_live(item_id, kind)
        if tab_changed or selection_changed:
            restart()

    def set_canvas_zoom(value):
        global canvas_zoom
        try:
            value = float(value)
        except Exception:
            value = 1.0
        canvas_zoom = max(CANVAS_ZOOM_MIN, min(CANVAS_ZOOM_MAX, value))
        runtime["canvas_cache"] = {}
        request_canvas_redraw()
        restart()

    def zoom_canvas(delta):
        set_canvas_zoom(canvas_zoom + float(delta or 0.0))

    def reset_canvas_zoom():
        set_canvas_zoom(1.0)

    _PROPERTY_PAIR_LABELS = {
        ("X", "Y"): "Position",
        ("X Offset", "Y Offset"): "Offset",
        ("X Anchor", "Y Anchor"): "Anchor",
        ("X Align", "Y Align"): "Align",
        ("Width", "Height"): "Size",
        ("X Zoom", "Y Zoom"): "Zoom",
        ("X Fill", "Y Fill"): "Fill",
    }

    def property_editor_rows(properties):
        values = list(properties or [])
        result = []
        index = 0
        while index < len(values):
            first = values[index]
            second = values[index + 1] if index + 1 < len(values) else None
            key = (first[0], second[0]) if second else None
            if key in _PROPERTY_PAIR_LABELS:
                result.append({"type": "pair", "label": _PROPERTY_PAIR_LABELS[key], "x": first, "y": second})
                index += 2
            else:
                result.append({"type": "single", "label": first[0], "path": first[1]})
                index += 1
        return result

    def property_group_expanded(group_name):
        return str(group_name) in expanded_property_groups

    def toggle_property_group(group_name):
        name = str(group_name)
        if name in expanded_property_groups:
            expanded_property_groups.discard(name)
        else:
            expanded_property_groups.add(name)
        restart()

    def tree_item_expanded(item_id, default=False):
        if item_id in expanded_tree_items:
            return True
        return bool(default)

    def toggle_tree_item(item_id, default=False):
        item_id = str(item_id)
        if tree_item_is_open(item_id, default):
            expanded_tree_items.discard(item_id)
            expanded_tree_items.add("closed:" + item_id)
        else:
            expanded_tree_items.add(item_id)
            expanded_tree_items.discard("closed:" + item_id)
        restart()

    def tree_item_is_open(item_id, default=False):
        item_id = str(item_id)
        if "closed:" + item_id in expanded_tree_items:
            return False
        if item_id in expanded_tree_items:
            return True
        return bool(default)

    def _append_visible_node_rows(rows, nodes, parent_id, depth, kind):
        for node in nodes or []:
            children = node.get("children", []) or []
            # Runtime transforms and anonymous helper displayables are useful for
            # capture, but presenting dozens of them as "Custom" makes both the
            # tree and layers unusable. Flatten internal wrappers while keeping
            # their meaningful descendants attached to the nearest real parent.
            if node.get("internal"):
                _append_visible_node_rows(rows, children, parent_id, depth, kind)
                continue
            open_value = tree_item_is_open(node.get("id"), False)
            rows.append({
                "item": node,
                "parent_id": parent_id,
                "depth": depth,
                "kind": kind,
                "has_children": bool(children),
                "open": open_value,
            })
            if children and open_value:
                _append_visible_node_rows(rows, children, node.get("id"), depth + 1, kind)


    def _debug_node_count(nodes):
        return sum(1 for _node, _parent, _depth in walk_nodes(nodes or []))

    def _debug_parent_chain(state, item_id):
        chain = []
        visited = set()
        current = item_id
        while current and current not in visited:
            visited.add(current)
            item, parent_id, kind = find_state_item(state, current)
            if item is None:
                break
            chain.append({"id": item.get("id"), "name": item.get("name"), "kind": kind, "parent_id": parent_id})
            current = parent_id
        return chain

    def _debug_selected_payload(state):
        item, parent_id, kind = selected_item(state)
        if item is None:
            return {"id": selected_item_id, "kind": selected_item_kind, "status": "none"}
        screen = screen_for_node(state, item.get("id")) if kind == "ui_node" and "screen_for_node" in globals() else None
        frame = current_frame() or {}
        local_sets = frame.get("changes", {}).get("sets", {}).get(item.get("id"), {})
        runtime_displayable = None
        if kind == "ui_node":
            runtime_displayable = runtime.get("widget_displayables", {}).get(item.get("id"))
        elif kind == "scene_node":
            runtime_displayable = runtime.get("scene_displayables", {}).get(item.get("id"))
        try:
            effective_bounds = item_stage_bounds(item, canvas_bounds_map(state)) if kind in ("ui_node", "scene_node") and "canvas_bounds_map" in globals() else item.get("bounds")
        except Exception:
            effective_bounds = item.get("bounds")
        return {
            "id": item.get("id"), "kind": kind, "name": item.get("name"),
            "parent_id": parent_id, "parent_chain": _debug_parent_chain(state, item.get("id")),
            "type": item.get("type"), "widget_id": item.get("widget_id"),
            "editability": item.get("editability"), "selectable": item.get("selectable"),
            "locked": item.get("locked"), "screen_locked": (screen or {}).get("locked"),
            "screen": (screen or {}).get("name"), "screen_id": (screen or {}).get("id"),
            "screen_managed": (screen or {}).get("managed"),
            "screen_runtime_active": runtime_screen_is_active(screen) if screen and "runtime_screen_is_active" in globals() else None,
            "bounds": item.get("bounds"), "effective_bounds": effective_bounds,
            "properties": item.get("properties"), "captured_properties": item.get("captured_properties"),
            "resolved_properties": item.get("resolved_properties"), "local_overrides": local_sets,
            "source": item.get("source"),
            "runtime_displayable_type": runtime_displayable.__class__.__name__ if runtime_displayable is not None else None,
        }

    def build_debug_report():
        """Returns a clipboard-safe diagnostic snapshot for bug reports."""
        try:
            state = resolve_frame()
        except Exception as exc:
            state = empty_frame_state()
            log_diagnostic("error", "Debugger could not resolve current frame", repr(exc))
        frame = current_frame() or {}
        filter_info = clone(runtime.get("last_ui_capture_filter", {}))
        event = None
        try:
            event = _active_preview_event(state) if "_active_preview_event" in globals() else None
        except Exception:
            event = None
        screens = []
        for screen in state.get("ui_screens", []):
            try:
                active = screen_visible_in_canvas(screen, state, event) if "screen_visible_in_canvas" in globals() else bool(screen.get("visible", True))
            except Exception:
                active = False
            screen_id = screen.get("id")
            screen_entry = runtime.get("screen_index", {}).get(screen_runtime_key(screen)) if "screen_runtime_key" in globals() else None
            screens.append({
                "id": screen_id, "name": screen.get("name"), "tag": screen.get("tag"),
                "layer": screen.get("layer"), "role": screen.get("role"), "active_in_canvas": active,
                "runtime_active": runtime_screen_is_active(screen) if "runtime_screen_is_active" in globals() else None,
                "visible": screen.get("visible"), "locked": screen.get("locked"), "managed": screen.get("managed"),
                "editability": screen.get("editability"), "nodes": _debug_node_count(screen.get("nodes", [])),
                "root_flattened": (screen.get("source") or {}).get("root_flattened", False),
                "has_runtime_screen": screen_id in runtime.get("screen_displayables", {}),
                "has_frozen_root": screen_id in runtime.get("screen_frozen_roots", {}),
                "runtime_entry_frozen": (screen_entry or {}).get("frozen"),
                "source": screen.get("source"),
            })
        payload = {
            "tool": {"name": TOOL_NAME, "release": globals().get("RELEASE_VERSION", str(VERSION)), "model_version": VERSION},
            "renpy": {"version": getattr(renpy, "version_string", None), "screen": [config.screen_width, config.screen_height]},
            "project": {"name": project_name(), "dirty": project_dirty, "frame_count": len(ensure_project().get("frames", {}))},
            "editor": {
                "current_frame_id": current_frame_id, "frame_name": frame.get("name"),
                "source_ref": frame.get("source_ref") or state.get("source_ref"),
                "tree_tab": selected_tree_tab, "layer_mode": layer_panel_mode,
                "right_tab": right_panel_tab, "preview_mode": preview_mode, "tool_mode": tool_mode,
                "state_revision": runtime.get("state_revision"), "drag_revision": runtime.get("drag_revision"),
                "last_invalidation_reason": runtime.get("last_invalidation_reason"),
                "pending_inputs": len(runtime.get("pending_input_edits", {})),
                "active_preview_frame_id": runtime.get("active_preview_frame_id"),
                "active_preview_source_frame_id": runtime.get("active_preview_source_frame_id"),
                "drag": runtime.get("drag"),
            },
            "selection": _debug_selected_payload(state),
            "counts": {
                "scenes": len(state.get("scenes", [])),
                "scene_nodes": sum(_debug_node_count(scene.get("nodes", [])) for scene in state.get("scenes", [])),
                "ui_screens": len(state.get("ui_screens", [])),
                "ui_nodes": sum(_debug_node_count(screen.get("nodes", [])) for screen in state.get("ui_screens", [])),
                "dialogue_controllers": len(state.get("dialogue_controllers", [])),
                "resolved_cache": len(resolved_cache),
                "canvas_cache": len(runtime.get("canvas_cache", {})),
                "bounds_cache": len(runtime.get("bounds_cache", {})),
                "screen_preview_cache": len(runtime.get("captured_screen_preview_cache", {})),
                "frame_preview_bundles": len(runtime.get("frame_preview_refs", {})),
            },
            "capabilities": {
                "screen_displayable": bool(globals().get("ScreenDisplayable")),
                "get_displayable_properties": hasattr(renpy, "get_displayable_properties"),
                "screenshot_to_bytes": hasattr(renpy, "screenshot_to_bytes"),
                # Report the adapter's presence without calling it while the
                # debugger screen is evaluating. A failed internal API lookup
                # must not make the Debugger itself disappear.
                "scene_lists_adapter": callable(globals().get("scene_lists")),
                "script_lookup": bool(getattr(getattr(renpy, "game", None), "script", None)),
            },
            "capture": {
                "serial": runtime.get("capture_serial"), "started_at": runtime.get("capture_started_at"),
                "source": runtime.get("capture_source"), "filter": filter_info,
                "active_screen_ids": sorted(str(value) for value in runtime.get("active_screen_ids", set())),
                "active_screen_names": list(runtime.get("active_screen_names", [])),
                "runtime_screen_keys": [list(key) for key in runtime.get("screen_index", {}).keys()],
                "modeled_runtime_screen_ids": [screen.get("id") for screen in state.get("ui_screens", []) if not screen.get("managed")],
                "modeled_but_inactive_ids": [screen.get("id") for screen in state.get("ui_screens", []) if not screen.get("managed") and screen.get("id") not in set(runtime.get("active_screen_ids", set()) or set())],
                "runtime_ids_missing_from_model": [screen_id for screen_id in runtime.get("active_screen_ids", set()) if not any(screen.get("id") == screen_id for screen in state.get("ui_screens", []))],
                "passive_dialogue_presentations": [
                    {"name": item.get("name"), "tag": item.get("tag"), "layer": item.get("layer"), "zorder": item.get("zorder")}
                    for item in runtime.get("dialogue_presentation_roots", [])
                ],
            },
            "ui_screens": screens,
            "frame_changes": frame.get("changes", {}),
            "active_dialogue_event": event,
            "diagnostics": clone(runtime.get("diagnostics", [])[-100:]),
        }
        return "Ren'Py Live Studio Debug Report\n" + json.dumps(json_safe(payload), indent=2, sort_keys=True, ensure_ascii=False)

    def debug_report_preview(limit=12000):
        key = (
            int(runtime.get("state_revision", 0)), selected_item_id, selected_item_kind,
            len(runtime.get("diagnostics", [])), right_panel_tab,
        )
        cached = runtime.get("debug_report_preview_cache")
        if not cached or cached.get("key") != key:
            report = build_debug_report()
            value = report if len(report) <= int(limit) else report[:int(limit)] + "\n... [preview truncated; Copy Full Report includes everything]"
            cached = {"key": key, "value": value}
            runtime["debug_report_preview_cache"] = cached
        return cached.get("value", "")

    def copy_debug_report():
        flush_pending_input_edits(False)
        report = build_debug_report()
        copied = copy_text_to_clipboard(report) if "copy_text_to_clipboard" in globals() else False
        if copied:
            renpy.notify("Live Studio debug report copied.")
            log_diagnostic("info", "Debug report copied", {"characters": len(report)})
        else:
            renpy.notify("Could not copy the debug report. See renpy.log.")
            try:
                renpy.log(report)
            except Exception:
                pass
        restart()
        return copied

    def visible_scene_tree_rows(state=None):
        """Visual Scene hierarchy only. Dialogue controllers live in Dialogue."""
        state = state or resolve_frame()
        rows = []
        for scene in state.get("scenes", []):
            scene_open = tree_item_is_open(scene.get("id"), True)
            rows.append({
                "item": scene,
                "parent_id": None,
                "depth": 0,
                "kind": "scene",
                "has_children": bool(scene.get("nodes")),
                "open": scene_open,
            })
            if scene_open:
                _append_visible_node_rows(rows, scene.get("nodes", []), scene.get("id"), 1, "scene_node")
        return rows

    def _ui_container_has_selected(screen):
        if not screen or not selected_item_id:
            return False
        if screen.get("id") == selected_item_id:
            return True
        return any(node.get("id") == selected_item_id for node, _parent, _depth in walk_nodes(screen.get("nodes", [])))

    def _runtime_screen_listed(screen):
        if "runtime_screen_is_active" not in globals():
            return True
        try:
            return runtime_screen_is_active(screen)
        except Exception:
            return True

    def visible_ui_tree_rows(state=None):
        state = state or resolve_frame()
        rows = []
        for screen in state.get("ui_screens", []):
            if not _runtime_screen_listed(screen):
                continue
            screen_open = tree_item_is_open(screen.get("id"), _ui_container_has_selected(screen))
            rows.append({
                "item": screen,
                "parent_id": None,
                "depth": 0,
                "kind": "ui_screen",
                "has_children": bool(screen.get("nodes")),
                "open": screen_open,
            })
            if screen_open:
                _append_visible_node_rows(rows, screen.get("nodes", []), screen.get("id"), 1, "ui_node")
        return rows

    def _layer_node_rows(rows, nodes, parent_id, depth, kind, screen_id=None):
        for node in reversed(nodes or []):
            children = node.get("children", []) or []
            if node.get("internal"):
                _layer_node_rows(rows, children, parent_id, depth, kind, screen_id)
                continue
            open_key = "layer:" + str(node.get("id"))
            open_value = tree_item_is_open(open_key, False)
            rows.append({
                "kind": kind,
                "item": node,
                "parent_id": parent_id,
                "screen_id": screen_id,
                "depth": depth,
                "group": False,
                "has_children": bool(children),
                "open": open_value,
                "open_key": open_key,
            })
            if children and open_value:
                _layer_node_rows(rows, children, node.get("id"), depth + 1, kind, screen_id)

    def scene_layer_rows(state=None):
        """Scene displayables only; dialogue is behavior, not a layer."""
        state = state or resolve_frame()
        rows = []
        for scene in reversed(state.get("scenes", [])):
            if not scene.get("nodes"):
                continue
            open_key = "layer:" + str(scene.get("id"))
            open_value = tree_item_is_open(open_key, True)
            rows.append({"kind": "scene", "item": scene, "depth": 0, "group": True, "has_children": True, "open": open_value, "open_key": open_key})
            if open_value:
                _layer_node_rows(rows, scene.get("nodes", []), scene.get("id"), 1, "scene_node")
        return rows

    def ui_layer_rows(state=None):
        state = state or resolve_frame()
        rows = []
        for screen in reversed(state.get("ui_screens", [])):
            if not _runtime_screen_listed(screen):
                continue
            open_key = "layer:" + str(screen.get("id"))
            open_value = tree_item_is_open(open_key, _ui_container_has_selected(screen))
            rows.append({"kind": "ui_screen", "item": screen, "depth": 0, "group": True, "has_children": bool(screen.get("nodes")), "screen_id": screen.get("id"), "open": open_value, "open_key": open_key})
            if open_value:
                _layer_node_rows(rows, screen.get("nodes", []), screen.get("id"), 1, "ui_node", screen.get("id"))
        return rows

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
        flush_pending_input_edits()
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
            # Dialogue is frame logic and is no longer parented to a visual Scene.
            controller["scene_id"] = None
            if "frame_event_ids" not in controller:
                active_id = controller.get("active_event_id")
                controller["frame_event_ids"] = [active_id] if active_id else []
            controller.setdefault("events", [])
            controller.setdefault("selected_event_id", controller.get("active_event_id"))

    def _migrate_ui_nodes(nodes):
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            node.setdefault("captured_properties", clone(node.get("properties", {})))
            node.setdefault("binding", {"mode": "literal", "expression": "", "source_expression": "", "preview": str(node.get("properties", {}).get("text", "") or "")})
            binding = node.get("binding")
            if not isinstance(binding, dict):
                node["binding"] = {"mode": "literal", "expression": "", "source_expression": "", "preview": str(node.get("properties", {}).get("text", "") or "")}
            else:
                binding.setdefault("mode", "literal")
                binding.setdefault("expression", "")
                binding.setdefault("source_expression", binding.get("expression", ""))
                binding.setdefault("preview", str(node.get("properties", {}).get("text", "") or ""))
            runtime_type = str(node.get("source", {}).get("runtime_type") or node.get("runtime_type") or node.get("type") or "").lower()
            if node.get("widget_id") is None and (str(node.get("type") or "").lower() in ("custom", "transform") or runtime_type in ("custom", "transform", "showif", "dynamicdisplayable")):
                node.setdefault("internal", True)
            _migrate_ui_nodes(node.get("children", []))

    def migrate_project(data):
        if not isinstance(data, dict):
            raise ValueError("Project data is not a dictionary")
        try:
            old_version = int(data.get("version", 0) or 0)
        except Exception:
            old_version = 0
        data.setdefault("settings", {})
        data["settings"].setdefault("snap_enabled", SNAP_ENABLED)
        data["settings"].setdefault("grid_enabled", GRID_ENABLED)
        data["settings"].setdefault("grid_size", GRID_SIZE)
        data["settings"].setdefault("guides_enabled", GUIDES_ENABLED)
        data["settings"].setdefault("show_all_bounds", SHOW_ALL_BOUNDS)
        data["settings"].setdefault("ui_capture_filter_engine_screens", UI_CAPTURE_FILTER_ENGINE_SCREENS)
        data["settings"].setdefault("ui_capture_include_dialogue_screens", UI_CAPTURE_DIALOGUE_SCREENS)
        data["settings"].setdefault("asset_browser_mode", "tree")
        data["settings"].setdefault("layer_panel_mode", "Scene")
        # Version 3 stored the noisy grid/all-widget overlay as the normal
        # editing view. Reset those defaults once when migrating to the cleaner
        # interface; users can re-enable them from Debug.
        if old_version < 4:
            data["settings"]["grid_enabled"] = False
            data["settings"]["guides_enabled"] = True
            data["settings"]["show_all_bounds"] = False
        for frame in data.get("frames", {}).values():
            frame.setdefault("source_ref", {})
            root_state = frame.get("root_state")
            _migrate_dialogue_state(root_state)
            if isinstance(root_state, dict):
                migrated_scenes = []
                for scene in root_state.get("scenes", []) or []:
                    if not scene.get("nodes") and str(scene.get("name", "")) in ("Layer: transient", "Layer: screens", "Layer: overlay", "Layer: top", "Dialogue"):
                        continue
                    if str(scene.get("type") or "").lower() == "dialogue" or str(scene.get("name") or "").lower() in ("dialogue", "dialogue visuals"):
                        # Dialogue is frame behavior, never a visual Scene layer.
                        # Older builds accidentally captured say/dialogue widgets
                        # here; the dedicated dialogue controller retains logic.
                        continue
                    migrated_scenes.append(scene)
                root_state["scenes"] = migrated_scenes
                migrated_screens = []
                for screen in root_state.get("ui_screens", []) or []:
                    _migrate_ui_nodes(screen.get("nodes", []))
                    nodes = screen.get("nodes", []) or []
                    if len(nodes) == 1 and "_captured_root_is_structural" in globals() and _captured_root_is_structural(nodes[0], screen.get("name")):
                        screen["nodes"] = nodes[0].get("children", [])
                        screen.setdefault("source", {})["root_flattened"] = True
                    name = str(screen.get("name") or "").lower()
                    runtime_observed = screen.get("source", {}).get("captured_by") == "runtime"
                    if runtime_observed and (name.startswith("live_studio") or name in UI_CAPTURE_EXCLUDED_SCREEN_NAMES or any(pattern in name for pattern in globals().get("UI_CAPTURE_EXCLUDED_SCREEN_PATTERNS", ()) if pattern)):
                        continue
                    if runtime_observed and str(screen.get("role") or "").lower() in ("say", "choice") and not bool(data.get("settings", {}).get("ui_capture_include_dialogue_screens", UI_CAPTURE_DIALOGUE_SCREENS)):
                        continue
                    if screen.get("nodes"):
                        migrated_screens.append(screen)
                root_state["ui_screens"] = migrated_screens
            changes = frame.setdefault("changes", {})
            changes.setdefault("sets", {})
            adds = changes.setdefault("adds", [])
            changes.setdefault("removes", [])
            changes.setdefault("reorders", [])
            filtered_adds = []
            for operation in adds:
                value = operation.get("value") if isinstance(operation, dict) else None
                if isinstance(value, dict) and operation.get("root_collection") == "scenes":
                    scene_name = str(value.get("name", "")).lower()
                    scene_type = str(value.get("type", "")).lower()
                    if scene_type == "dialogue" or scene_name in ("dialogue", "dialogue visuals"):
                        continue
                    if not value.get("nodes") and str(value.get("name", "")) in ("Layer: transient", "Layer: screens", "Layer: overlay", "Layer: top"):
                        continue
                if isinstance(value, dict) and value.get("events") is not None:
                    _migrate_dialogue_state({"dialogue_controllers": [value]})
                if isinstance(value, dict) and (value.get("type") or value.get("children") is not None):
                    _migrate_ui_nodes([value])
                filtered_adds.append(operation)
            changes["adds"] = filtered_adds
            frame.setdefault("edges", [])
            frame.setdefault("stop_fallthrough", False)
        data["version"] = VERSION
        return data


    def project_file_label(path):
        try:
            if isinstance(path, (tuple, list)) and path:
                return str(path[0])
            return os.path.basename(str(path or "")) or "Project"
        except Exception:
            return "Project"

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
            runtime["frame_preview_refs"] = {}
            if "activate_runtime_preview_refs" in globals():
                activate_runtime_preview_refs(current_frame_id)
            invalidate_resolved_cache()
            project_dirty = False
            renpy.notify("Live Studio project loaded")
            restart()
            return True
        except Exception as exc:
            log_diagnostic("error", "Could not load project: {}".format(exc), {"path": path})
            renpy.notify("Live Studio load failed")
            return False
