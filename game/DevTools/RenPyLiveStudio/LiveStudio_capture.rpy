# Non-destructive runtime capture. The game remains intact behind the editor.

init -890 python in live_studio:
    from renpy.store import im

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

    def capture_exact_snapshot():
        runtime["snapshot_bytes"] = None
        runtime["snapshot_displayable"] = None
        try:
            data = renpy.screenshot_to_bytes((config.screen_width, config.screen_height))
            runtime["snapshot_bytes"] = data
            runtime["snapshot_displayable"] = im.Data(data, "live_studio_capture.png")
            return True
        except Exception as exc:
            log_diagnostic("warning", "Exact screenshot capture failed: {}".format(exc))
            return False

    def capture_runtime_state():
        runtime["scene_displayables"] = {}
        runtime["screen_displayables"] = {}
        runtime["diagnostics"] = []
        runtime["capture_source"] = capture_source_reference()

        capture_exact_snapshot()
        state = empty_frame_state()
        state["source_ref"] = clone(runtime["capture_source"])
        try:
            state["scenes"] = capture_scene_state()
        except Exception as exc:
            log_diagnostic("error", "Scene capture failed: {}".format(exc))
            state["scenes"] = []
        try:
            state["ui_screens"] = capture_ui_state()
        except Exception as exc:
            log_diagnostic("error", "UI capture failed: {}".format(exc))
            state["ui_screens"] = []
        try:
            capture_runtime_dialogue(state)
        except Exception as exc:
            log_diagnostic("warning", "Dialogue capture failed: {}".format(exc))
        return state

    def begin_capture_project(name=None):
        global project_data, current_frame_id, selected_item_id, selected_item_kind, project_dirty
        state = capture_runtime_state()
        name = name or "Captured Scene"
        project_data = new_project(name)
        frame = new_frame("Captured Frame", parent_id=None, root_state=state)
        project_data["frames"][frame["id"]] = frame
        project_data["frame_order"].append(frame["id"])
        project_data["project"]["entry_frame_id"] = frame["id"]
        current_frame_id = frame["id"]
        selected_item_id = None
        selected_item_kind = None
        history[:] = []
        redo_stack[:] = []
        invalidate_resolved_cache()
        project_dirty = False
        return project_data

    def refresh_runtime_capture():
        """Replaces the current frame with a new capture after confirmation in UI."""
        global project_dirty
        frame = current_frame()
        if frame is None:
            return
        state = capture_runtime_state()
        frame["root_state"] = state
        frame["parent_id"] = None
        frame["changes"] = {"sets": {}, "adds": [], "removes": [], "reorders": []}
        invalidate_resolved_cache()
        project_dirty = True
        renpy.restart_interaction()
