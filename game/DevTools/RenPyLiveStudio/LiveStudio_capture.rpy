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
            # Runtime-only AST lookup key. It is converted to JSON-safe data
            # when stored, then restored to a tuple for script.lookup().
            "node_name": None,
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
        try:
            current_name = renpy.game.context().current
            node = renpy.game.script.lookup(current_name) if current_name is not None else None
            source["node_name"] = getattr(node, "name", current_name)
        except Exception:
            pass
        return json_safe(source)

    def source_reference_key(source=None):
        source = source or capture_source_reference()
        node_name = source.get("node_name")
        if isinstance(node_name, (list, tuple)):
            node_name = ":".join(str(part) for part in node_name)
        return "{}:{}:{}:{}:{}".format(
            source.get("filename") or "",
            source.get("line") or "",
            source.get("statement") or "",
            source.get("label") or "",
            node_name or "",
        )

    _RUNTIME_PREVIEW_MAP_KEYS = (
        "scene_displayables", "ui_displayables", "widget_displayables",
        "screen_roots", "screen_raw_roots", "screen_frozen_roots",
        "screen_displayables", "screen_index", "dialogue_presentation_roots",
    )

    def snapshot_runtime_preview_refs():
        bundle = {
            "snapshot_displayable": runtime.get("snapshot_displayable"),
            "snapshot_bytes": runtime.get("snapshot_bytes"),
            "active_screen_ids": set(runtime.get("active_screen_ids", set()) or set()),
            "active_screen_names": list(runtime.get("active_screen_names", []) or []),
            "capture_serial": runtime.get("capture_serial"),
            "capture_source": clone(runtime.get("capture_source") or {}),
        }
        for key in _RUNTIME_PREVIEW_MAP_KEYS:
            value = runtime.get(key, {})
            if isinstance(value, dict):
                bundle[key] = dict(value)
            elif isinstance(value, list):
                bundle[key] = list(value)
            else:
                bundle[key] = value
        return bundle

    def bind_runtime_preview_refs(frame_id):
        if not frame_id:
            return False
        bundle = snapshot_runtime_preview_refs()
        runtime.setdefault("frame_preview_refs", {})[frame_id] = bundle
        runtime["active_preview_frame_id"] = frame_id
        runtime["active_preview_source_frame_id"] = frame_id
        return True

    def _preview_source_frame_id(frame_id):
        visited = set()
        candidate = frame_id
        bundles = runtime.setdefault("frame_preview_refs", {})
        while candidate and candidate not in visited:
            visited.add(candidate)
            if candidate in bundles:
                return candidate
            frame = frame_by_id(candidate) if "frame_by_id" in globals() else None
            candidate = (frame or {}).get("parent_id")
        return None

    def activate_runtime_preview_refs(frame_id, clear_if_missing=True):
        source_frame_id = _preview_source_frame_id(frame_id)
        bundle = runtime.setdefault("frame_preview_refs", {}).get(source_frame_id) if source_frame_id else None
        runtime["active_preview_frame_id"] = frame_id
        runtime["active_preview_source_frame_id"] = source_frame_id
        if bundle is None:
            if clear_if_missing:
                for key in _RUNTIME_PREVIEW_MAP_KEYS:
                    runtime[key] = [] if key == "dialogue_presentation_roots" else {}
                runtime["active_screen_ids"] = set()
                runtime["active_screen_names"] = []
                runtime["snapshot_displayable"] = None
                runtime["snapshot_bytes"] = None
            return False
        for key in _RUNTIME_PREVIEW_MAP_KEYS:
            value = bundle.get(key, {})
            if isinstance(value, dict):
                runtime[key] = dict(value)
            elif isinstance(value, list):
                runtime[key] = list(value)
            else:
                runtime[key] = value
        runtime["active_screen_ids"] = set(bundle.get("active_screen_ids", set()) or set())
        runtime["active_screen_names"] = list(bundle.get("active_screen_names", []) or [])
        runtime["snapshot_displayable"] = bundle.get("snapshot_displayable")
        runtime["snapshot_bytes"] = bundle.get("snapshot_bytes")
        return True

    def inherit_runtime_preview_refs(frame_id, source_frame_id):
        source = _preview_source_frame_id(source_frame_id)
        bundle = runtime.setdefault("frame_preview_refs", {}).get(source) if source else None
        if not frame_id or bundle is None:
            return False
        # Runtime displayables are intentionally shared references. Project data
        # never serializes this bundle, and edits are represented by frame diffs.
        runtime["frame_preview_refs"][frame_id] = bundle
        return True

    def drop_runtime_preview_refs(frame_id):
        runtime.setdefault("frame_preview_refs", {}).pop(frame_id, None)
        if runtime.get("active_preview_frame_id") == frame_id:
            runtime["active_preview_frame_id"] = None
            runtime["active_preview_source_frame_id"] = None

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
        """Captures one stable runtime snapshot without erasing prior evidence."""
        runtime["scene_displayables"] = {}
        runtime["screen_displayables"] = {}
        runtime["widget_displayables"] = {}
        runtime["capture_serial"] = int(runtime.get("capture_serial", 0)) + 1
        runtime["capture_started_at"] = int(time.time())
        runtime["capture_source"] = clone(source_override or runtime.get("preopen_source") or capture_source_reference())
        log_diagnostic("info", "Runtime capture started", {
            "capture": runtime["capture_serial"],
            "source": runtime["capture_source"],
        })

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

        log_diagnostic("info", "Runtime capture completed", {
            "capture": runtime["capture_serial"],
            "scenes": len(state.get("scenes", [])),
            "ui_screens": len(state.get("ui_screens", [])),
            "dialogue_controllers": len(state.get("dialogue_controllers", [])),
        })
        return state
    def refresh_runtime_preview_references(keep_snapshot=False):
        """Refreshes runtime references and rebinds them to the current frame.

        Project nodes are not replaced, so local edits remain intact. The active
        runtime-screen set is refreshed, which hides stale developer/overlay
        screens that are no longer rendered. A Fresh Capture is still required
        to add newly-appeared screens to the editable hierarchy.
        """
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
        if current_frame_id:
            bind_runtime_preview_refs(current_frame_id)
        invalidate_view_caches(False, "runtime preview references refreshed")
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
        bind_runtime_preview_refs(frame["id"])
        return project_data


    def begin_blank_project(name="Untitled Live Studio Project"):
        global project_data, current_frame_id
        project_data = new_project(name)
        state = empty_frame_state()
        state["scenes"] = [new_scene("Master", ["master"], "scene")]
        frame = new_frame("Start", parent_id=None, root_state=state)
        project_data["frames"][frame["id"]] = frame
        project_data["frame_order"].append(frame["id"])
        project_data["project"]["entry_frame_id"] = frame["id"]
        current_frame_id = frame["id"]
        runtime["snapshot_bytes"] = None
        runtime["snapshot_displayable"] = None
        runtime["frame_preview_refs"] = {}
        runtime["active_screen_ids"] = set()
        runtime["active_screen_names"] = []
        runtime["dialogue_presentation_roots"] = []
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
        bind_runtime_preview_refs(frame["id"])
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
        bind_runtime_preview_refs(frame.get("id"))
        runtime.pop("source_candidates", None)
        runtime.pop("source_candidates_key", None)
        invalidate_resolved_cache()
        clear_selection()
        project_dirty = True
        restart()
        return True
