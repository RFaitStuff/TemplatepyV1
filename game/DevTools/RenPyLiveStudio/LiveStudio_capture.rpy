# Non-destructive runtime capture. The running game is covered by the editor,
# never cleared or rebuilt in-place.

init -890 python in live_studio:
    from renpy.store import config, im

    def capture_source_reference():
        source = {
            "filename": None,
            "line": None,
            "statement": None,
            "label": None,
        }
        try:
            filename, line = renpy.get_filename_line()
            source["filename"] = filename
            source["line"] = line
        except Exception:
            pass
        try:
            source["statement"] = renpy.get_statement_name()
        except Exception:
            pass
        try:
            source["label"] = renpy.get_label()
        except Exception:
            pass
        return json_safe(source)

    def source_reference_key(source=None):
        source = source or capture_source_reference()
        return "{}:{}:{}".format(
            source.get("filename") or "",
            source.get("line") or "",
            source.get("statement") or "",
        )

    def capture_exact_snapshot():
        runtime["snapshot_bytes"] = None
        runtime["snapshot_displayable"] = None
        try:
            data = renpy.screenshot_to_bytes((config.screen_width, config.screen_height))
            runtime["snapshot_bytes"] = data
            runtime["snapshot_displayable"] = im.Data(data, "live_studio_capture.png")
            return True
        except Exception as exc:
            log_diagnostic("warning", "Exact screenshot capture failed", repr(exc))

        # Older or unusual renderers may not support screenshot_to_bytes at
        # this point. Keep a Surface fallback in runtime-only state.
        try:
            runtime["snapshot_displayable"] = renpy.screenshot()
            return True
        except Exception as exc:
            log_diagnostic("warning", "Screenshot fallback failed", repr(exc))
            return False

    def capture_runtime_state(source_override=None, keep_snapshot=False):
        runtime["scene_displayables"] = {}
        runtime["screen_displayables"] = {}
        runtime["widget_displayables"] = {}
        runtime["diagnostics"] = []
        runtime["capture_source"] = clone(source_override or runtime.get("preopen_source") or capture_source_reference())

        if not keep_snapshot or runtime.get("snapshot_displayable") is None:
            capture_exact_snapshot()
        state = empty_frame_state()
        state["source_ref"] = clone(runtime["capture_source"])

        try:
            state["scenes"] = capture_scene_state()
        except Exception as exc:
            log_diagnostic("error", "Scene capture failed", repr(exc))
            state["scenes"] = []

        try:
            state["ui_screens"] = capture_ui_state()
        except Exception as exc:
            log_diagnostic("error", "UI capture failed", repr(exc))
            state["ui_screens"] = []

        try:
            capture_runtime_dialogue(state)
        except Exception as exc:
            log_diagnostic("warning", "Dialogue capture failed", repr(exc))

        return state


    def refresh_runtime_preview_references(keep_snapshot=False):
        """Refreshes temporary visual references without changing project data."""
        if not keep_snapshot or runtime.get("snapshot_displayable") is None:
            capture_exact_snapshot()
        try:
            capture_scene_state()
        except Exception as exc:
            log_diagnostic("warning", "Scene preview references could not be refreshed", repr(exc))
        try:
            capture_ui_state()
        except Exception as exc:
            log_diagnostic("warning", "UI preview references could not be refreshed", repr(exc))
        return True

    def _reset_editor_state_after_project_change():
        global selected_item_id, selected_item_kind, project_dirty
        selected_item_id = None
        selected_item_kind = None
        history[:] = []
        redo_stack[:] = []
        invalidate_resolved_cache()
        project_dirty = False

    def begin_capture_project(name=None, source_override=None, keep_snapshot=False):
        global project_data, current_frame_id
        state = capture_runtime_state(source_override, keep_snapshot)
        name = name or "Captured Scene"
        project_data = new_project(name)
        source = state.get("source_ref", {})
        frame_name = source.get("label") or "Captured Frame"
        frame = new_frame(frame_name, parent_id=None, root_state=state)
        frame["source_ref"] = clone(source)
        project_data["frames"][frame["id"]] = frame
        project_data["frame_order"].append(frame["id"])
        project_data["project"]["entry_frame_id"] = frame["id"]
        current_frame_id = frame["id"]
        runtime.setdefault("runtime_trace", []).append({
            "frame_id": frame["id"],
            "source_ref": clone(source),
            "key": source_reference_key(source),
        })
        _reset_editor_state_after_project_change()
        return project_data


    def begin_blank_project(name="Untitled Live Studio Project"):
        global project_data, current_frame_id
        project_data = new_project(name)
        state = empty_frame_state()
        master = new_scene("Master", ["master"], "scene")
        dialogue = new_scene("Dialogue", ["characters", "dialogue"], "dialogue")
        state["scenes"] = [master, dialogue]
        frame = new_frame("Start", parent_id=None, root_state=state)
        project_data["frames"][frame["id"]] = frame
        project_data["frame_order"].append(frame["id"])
        project_data["project"]["entry_frame_id"] = frame["id"]
        current_frame_id = frame["id"]
        runtime["snapshot_bytes"] = None
        runtime["snapshot_displayable"] = None
        _reset_editor_state_after_project_change()
        restart()
        return project_data

    def append_runtime_capture_as_frame(name=None, connect=True, source_override=None, keep_snapshot=False):
        """Adds the current game state as a detached runtime snapshot frame.

        This is used when Live Studio is opened again later in the game. It is
        deliberately explicit: advancing arbitrary Ren'Py code from inside a
        modal editor is unsafe, but capturing the state reached by normal play
        is reliable.
        """
        global current_frame_id, project_dirty
        ensure_project()
        source_id = current_frame_id
        state = capture_runtime_state(source_override, keep_snapshot)
        source = state.get("source_ref", {})
        frame = new_frame(name or source.get("label") or "Runtime Capture", None, state)
        frame["source_ref"] = clone(source)
        project_data["frames"][frame["id"]] = frame
        project_data["frame_order"].append(frame["id"])
        if connect and source_id and source_id != frame["id"]:
            _add_frame_edge_no_restart(source_id, frame["id"], "runtime", "Runtime next")
        current_frame_id = frame["id"]
        runtime.setdefault("runtime_trace", []).append({
            "frame_id": frame["id"],
            "source_ref": clone(source),
            "key": source_reference_key(source),
        })
        invalidate_resolved_cache()
        project_dirty = True
        restart()
        return frame

    def refresh_runtime_capture():
        """Replaces the current frame with a fresh root capture.

        The UI asks for confirmation before calling this because local changes
        on the selected frame are discarded.
        """
        global project_dirty
        frame = current_frame()
        if frame is None:
            return False
        state = capture_runtime_state()
        frame["root_state"] = state
        frame["parent_id"] = None
        frame["source_ref"] = clone(state.get("source_ref", {}))
        frame["changes"] = {"sets": {}, "adds": [], "removes": [], "reorders": []}
        invalidate_resolved_cache()
        clear_selection()
        project_dirty = True
        restart()
        return True
