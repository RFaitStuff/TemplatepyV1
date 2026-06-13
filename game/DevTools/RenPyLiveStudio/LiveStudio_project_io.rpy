# Project metadata, autosave, crash recovery, snapshots, and export history.

init -977 python in live_studio:
    import hashlib as _io_hashlib
    import json as _io_json
    import os as _io_os
    import time as _io_time
    import uuid as _io_uuid

    _legacy_new_project = new_project
    _legacy_migrate_project = migrate_project
    _legacy_save_project = save_project
    _legacy_load_project = load_project

    def _enrich_project_metadata(data):
        if not isinstance(data, dict):
            return data
        now = int(_io_time.time())
        metadata = data.setdefault("project", {})
        metadata.setdefault("id", safe_identifier(metadata.get("name", "project"), "project"))
        metadata.setdefault("name", "Untitled Live Studio Project")
        metadata.setdefault("created_at", now)
        metadata.setdefault("updated_at", now)
        metadata.setdefault("entry_frame_id", None)
        metadata["live_studio_version"] = RELEASE_VERSION
        metadata["project_model_version"] = VERSION
        metadata.setdefault("engine_version", None)
        metadata.setdefault("project_path", None)
        metadata.setdefault("last_exported_revision", 0)
        metadata.setdefault("current_editing_session", None)
        metadata.setdefault("extension_information", {})
        data.setdefault("revision", 0)
        data.setdefault("command_journal", [])
        data.setdefault("export_history", [])
        data.setdefault("snapshots", [])
        settings = data.setdefault("settings", {})
        settings.setdefault("autosave_enabled", True)
        settings.setdefault("recovery_enabled", True)
        settings.setdefault("autosave_interval", AUTOSAVE_INTERVAL)
        settings.setdefault("coordinate_mode_default", "auto")
        settings.setdefault("diagnostics_compatibility_fallbacks", False)
        return data

    def new_project(name="Untitled Live Studio Project"):
        return _enrich_project_metadata(_legacy_new_project(name))

    def migrate_project(data):
        return _enrich_project_metadata(_legacy_migrate_project(data))

    def ensure_editing_session():
        data = _enrich_project_metadata(ensure_project())
        metadata = data.setdefault("project", {})
        if not metadata.get("current_editing_session"):
            metadata["current_editing_session"] = "session_{}".format(_io_uuid.uuid4().hex[:16])
            runtime["editing_session_started_at"] = int(_io_time.time())
        runtime["editing_session_id"] = metadata.get("current_editing_session")
        return metadata.get("current_editing_session")

    def _project_storage_root():
        directory, _path = _project_path()
        return directory

    def _project_aux_path(kind, filename=None):
        data = ensure_project()
        project_id = safe_identifier(data.get("project", {}).get("id"), "project")
        subdirectory = {
            "autosave": AUTOSAVE_DIRECTORY,
            "recovery": RECOVERY_DIRECTORY,
            "snapshot": SNAPSHOT_DIRECTORY,
        }.get(kind, kind)
        directory = _io_os.path.join(_project_storage_root(), subdirectory)
        if filename is None:
            suffix = {
                "autosave": ".autosave.json",
                "recovery": ".recovery.json",
                "snapshot": ".snapshot.json",
            }.get(kind, ".json")
            filename = project_id + suffix
        return directory, _io_os.path.join(directory, filename)

    def _atomic_write_text(path, text):
        parent = _io_os.path.dirname(path)
        if parent and not _io_os.path.isdir(parent):
            _io_os.makedirs(parent)
        temporary = "{}.{}.tmp".format(path, _io_uuid.uuid4().hex[:8])
        try:
            with open(temporary, "w", encoding="utf-8", newline="") as output:
                output.write(str(text))
                output.flush()
                try:
                    _io_os.fsync(output.fileno())
                except Exception:
                    pass
            _io_os.replace(temporary, path)
        finally:
            if _io_os.path.exists(temporary):
                try:
                    _io_os.remove(temporary)
                except Exception:
                    pass
        return path

    def _atomic_write_json(path, value):
        text = _io_json.dumps(json_safe(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        return _atomic_write_text(path, text)

    def _file_sha256(path):
        digest = _io_hashlib.sha256()
        with open(path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def schedule_project_autosave(reason="mutation"):
        runtime["autosave_due"] = True
        runtime["recovery_due"] = True
        runtime["autosave_reason"] = str(reason or "mutation")
        runtime["autosave_requested_at"] = float(_io_time.time())

    def _recovery_payload():
        return {
            "format": "renpy_live_studio_recovery",
            "version": VERSION,
            "release_version": RELEASE_VERSION,
            "saved_at": int(_io_time.time()),
            "session_id": ensure_editing_session(),
            "project_revision": project_revision() if "project_revision" in globals() else ensure_project().get("revision", 0),
            "project": clone(ensure_project()),
            "editor": {
                "current_frame_id": current_frame_id,
                "selected_item_id": selected_item_id,
                "selected_item_kind": selected_item_kind,
                "preview_mode": preview_mode,
                "layer_panel_mode": layer_panel_mode,
                "bottom_tab": bottom_tab,
            },
        }

    def write_recovery_journal(force=False):
        if not bool(project_setting("recovery_enabled", True)):
            return None
        if not force and not runtime.get("recovery_due"):
            return None
        directory, path = _project_aux_path("recovery")
        try:
            _atomic_write_json(path, _recovery_payload())
            runtime["recovery_due"] = False
            runtime["last_recovery_path"] = path
            runtime["last_recovery_time"] = int(_io_time.time())
            runtime.pop("recovery_info_cache", None)
            return path
        except Exception as exc:
            log_diagnostic("error", "Could not write recovery journal", {"path": path}, system="project_io", operation="recovery_write", category="source_write", exception=exc, recovery="The in-memory project is still active; use Save Project manually.")
            return None

    def autosave_project(force=False):
        if not bool(project_setting("autosave_enabled", True)):
            return None
        if not force and not runtime.get("autosave_due"):
            return None
        directory, path = _project_aux_path("autosave")
        try:
            payload = clone(_enrich_project_metadata(ensure_project()))
            payload.setdefault("project", {})["autosaved_at"] = int(_io_time.time())
            _atomic_write_json(path, payload)
            runtime["autosave_due"] = False
            runtime["last_autosave_path"] = path
            runtime["last_autosave_time"] = int(_io_time.time())
            return path
        except Exception as exc:
            log_diagnostic("error", "Could not autosave Live Studio project", {"path": path}, system="project_io", operation="autosave", category="source_write", exception=exc)
            return None

    def autosave_if_due():
        interval = float(project_setting("autosave_interval", AUTOSAVE_INTERVAL) or AUTOSAVE_INTERVAL)
        requested = float(runtime.get("autosave_requested_at", 0.0) or 0.0)
        if runtime.get("recovery_due") and (_io_time.time() - requested >= min(1.0, interval)):
            write_recovery_journal(False)
        if runtime.get("autosave_due") and (_io_time.time() - requested >= interval):
            autosave_project(False)
        return None

    def recoverable_session_path():
        _directory, path = _project_aux_path("recovery")
        return path if _io_os.path.isfile(path) else None

    def recovery_session_info():
        path = recoverable_session_path()
        if not path:
            runtime.pop("recovery_info_cache", None)
            return None
        try:
            stat = _io_os.stat(path)
            key = (path, int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1000000000))), int(stat.st_size))
            cached = runtime.get("recovery_info_cache")
            if cached and cached.get("key") == key:
                return cached.get("value")
            with open(path, "r", encoding="utf-8") as source:
                payload = _io_json.load(source)
            value = {
                "path": path,
                "saved_at": payload.get("saved_at"),
                "session_id": payload.get("session_id"),
                "project_revision": payload.get("project_revision", 0),
                "project_name": payload.get("project", {}).get("project", {}).get("name", "Recovered Project"),
            }
            runtime["recovery_info_cache"] = {"key": key, "value": value}
            return value
        except Exception as exc:
            log_diagnostic("warning", "Recovery journal could not be read", {"path": path}, system="project_io", operation="recovery_read", category="user_content", exception=exc)
            return None

    def restore_recovery_session():
        global project_data, current_frame_id, selected_item_id, selected_item_kind, preview_mode, layer_panel_mode, bottom_tab, project_dirty
        path = recoverable_session_path()
        if not path:
            return False
        try:
            with open(path, "r", encoding="utf-8") as source:
                payload = _io_json.load(source)
            project_data = migrate_project(payload.get("project") or {})
            # A restored journal starts a new editing session. Keeping the old
            # session id makes a second crash indistinguishable from the first.
            project_data.setdefault("project", {})["current_editing_session"] = "session_{}".format(_io_uuid.uuid4().hex[:16])
            runtime["editing_session_id"] = project_data["project"]["current_editing_session"]
            runtime["editing_session_started_at"] = int(_io_time.time())
            editor = payload.get("editor") or {}
            order = project_data.get("frame_order", [])
            current_frame_id = editor.get("current_frame_id") or project_data.get("project", {}).get("entry_frame_id") or (order[0] if order else None)
            selected_item_id = editor.get("selected_item_id")
            selected_item_kind = editor.get("selected_item_kind")
            preview_mode = editor.get("preview_mode") or "layout"
            layer_panel_mode = editor.get("layer_panel_mode") or "Scene"
            bottom_tab = editor.get("bottom_tab") or "Assets"
            history[:] = []
            redo_stack[:] = []
            runtime["frame_preview_refs"] = {}
            if "activate_runtime_preview_refs" in globals():
                activate_runtime_preview_refs(current_frame_id)
            project_dirty = True
            invalidate_resolved_cache(True, "recovery restored")
            validate_selection()
            schedule_project_autosave("Recovery restored")
            log_diagnostic("info", "Recovery session restored", {"path": path}, system="project_io", operation="recovery_restore")
            restart()
            return True
        except Exception as exc:
            log_diagnostic("error", "Recovery session could not be restored", {"path": path}, system="project_io", operation="recovery_restore", category="user_content", exception=exc)
            return False

    def discard_recovery_session(restart_ui=True):
        path = recoverable_session_path()
        runtime["recovery_due"] = False
        if not path:
            runtime.pop("last_recovery_path", None)
            return False
        try:
            _io_os.remove(path)
            runtime.pop("last_recovery_path", None)
            runtime.pop("recovery_info_cache", None)
            if restart_ui:
                restart()
            return True
        except Exception as exc:
            log_diagnostic("warning", "Recovery journal could not be discarded", {"path": path}, system="project_io", operation="recovery_discard", exception=exc)
            return False

    def create_project_snapshot(name=None):
        flush_pending_input_edits(False)
        data = ensure_project()
        stamp = _io_time.strftime("%Y%m%d_%H%M%S")
        label = str(name or "Snapshot {}".format(stamp))
        filename = "{}__{}.json".format(stamp, safe_identifier(label, "snapshot"))
        directory, path = _project_aux_path("snapshot", filename)
        payload = {
            "format": "renpy_live_studio_snapshot",
            "release_version": RELEASE_VERSION,
            "created_at": int(_io_time.time()),
            "label": label,
            "project_revision": project_revision() if "project_revision" in globals() else data.get("revision", 0),
            "project": clone(data),
        }
        try:
            _atomic_write_json(path, payload)
            row = {"label": label, "path": path, "created_at": payload["created_at"], "revision": payload["project_revision"]}
            data.setdefault("snapshots", []).append(row)
            del data["snapshots"][:-50]
            runtime.pop("snapshot_rows_cache", None)
            # Snapshot metadata belongs to the Studio project, but creating a
            # snapshot does not change the authored frame revision itself.
            global project_dirty
            project_dirty = True
            schedule_project_autosave("Snapshot metadata updated")
            log_diagnostic("info", "Project snapshot created", row, system="project_io", operation="snapshot")
            renpy.notify("Live Studio snapshot created")
            restart()
            return path
        except Exception as exc:
            log_diagnostic("error", "Could not create project snapshot", {"path": path}, system="project_io", operation="snapshot", category="source_write", exception=exc)
            return None

    def project_snapshot_rows():
        directory, _path = _project_aux_path("snapshot")
        if not _io_os.path.isdir(directory):
            runtime.pop("snapshot_rows_cache", None)
            return []
        file_state = []
        for filename in sorted((name for name in _io_os.listdir(directory) if name.lower().endswith(".json")), reverse=True):
            path = _io_os.path.join(directory, filename)
            try:
                stat = _io_os.stat(path)
                stamp = (int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1000000000))), int(stat.st_size))
            except Exception:
                stamp = (0, 0)
            file_state.append((filename, stamp))
        key = (directory, tuple(file_state))
        cached = runtime.get("snapshot_rows_cache")
        if cached and cached.get("key") == key:
            return cached.get("rows", [])
        rows = []
        for filename, _stamp in file_state:
            path = _io_os.path.join(directory, filename)
            row = {"label": filename, "path": path, "revision": None, "created_at": None}
            try:
                with open(path, "r", encoding="utf-8") as source:
                    payload = _io_json.load(source)
                row["label"] = str(payload.get("label") or filename)
                row["revision"] = payload.get("project_revision")
                row["created_at"] = payload.get("created_at")
            except Exception as exc:
                row["error"] = repr(exc)
            rows.append(row)
        runtime["snapshot_rows_cache"] = {"key": key, "rows": rows}
        return rows

    def restore_project_snapshot(path):
        global project_data, current_frame_id, selected_item_id, selected_item_kind, project_dirty
        try:
            with open(path, "r", encoding="utf-8") as source:
                payload = _io_json.load(source)
            project_data = migrate_project(payload.get("project") or payload)
            order = project_data.get("frame_order", [])
            current_frame_id = project_data.get("project", {}).get("entry_frame_id") or (order[0] if order else None)
            selected_item_id = None
            selected_item_kind = None
            history[:] = []
            redo_stack[:] = []
            runtime["frame_preview_refs"] = {}
            if "activate_runtime_preview_refs" in globals():
                activate_runtime_preview_refs(current_frame_id)
            project_data.setdefault("project", {})["current_editing_session"] = "session_{}".format(_io_uuid.uuid4().hex[:16])
            runtime["editing_session_id"] = project_data["project"]["current_editing_session"]
            project_dirty = True
            invalidate_resolved_cache(True, "snapshot restored")
            schedule_project_autosave("Snapshot restored")
            log_diagnostic("info", "Project snapshot restored", {"path": path}, system="project_io", operation="snapshot_restore")
            restart()
            return True
        except Exception as exc:
            log_diagnostic("error", "Could not restore project snapshot", {"path": path}, system="project_io", operation="snapshot_restore", category="user_content", exception=exc)
            return False

    def record_export_history(record):
        global project_dirty
        data = ensure_project()
        row = clone(record or {})
        row.setdefault("time", int(_io_time.time()))
        row.setdefault("project_revision", project_revision() if "project_revision" in globals() else data.get("revision", 0))
        data.setdefault("export_history", []).append(row)
        del data["export_history"][:-int(globals().get("EXPORT_HISTORY_LIMIT", 80))]
        metadata = data.setdefault("project", {})
        if row.get("status") == "applied":
            metadata["last_exported_revision"] = row.get("project_revision", 0)
        runtime["last_export_record"] = row
        project_dirty = True
        if "schedule_project_autosave" in globals():
            schedule_project_autosave("Export history updated")
        return row

    def export_history_rows(limit=30):
        rows = list(ensure_project().get("export_history", []) or [])
        rows.reverse()
        return rows[:int(limit or 30)]

    def project_lifecycle_summary():
        recovery = recovery_session_info()
        return {
            "revision": project_revision() if "project_revision" in globals() else ensure_project().get("revision", 0),
            "last_exported_revision": ensure_project().get("project", {}).get("last_exported_revision", 0),
            "session_id": ensure_editing_session(),
            "autosave_path": runtime.get("last_autosave_path", ""),
            "autosave_time": runtime.get("last_autosave_time"),
            "recovery": recovery,
            "snapshots": len(project_snapshot_rows()),
            "journal_entries": len(ensure_project().get("command_journal", []) or []),
        }

    def save_project(filename=None):
        data = _enrich_project_metadata(ensure_project())
        metadata = data.setdefault("project", {})
        metadata["updated_at"] = int(_io_time.time())
        # Persist the path inside the same atomic save rather than assigning it
        # only after the legacy writer has already serialized the project.
        _directory, intended_path = _project_path(filename)
        old_path = metadata.get("project_path")
        metadata["project_path"] = intended_path
        result = _legacy_save_project(filename)
        if result:
            metadata["project_path"] = result
            runtime["autosave_due"] = False
            runtime["recovery_due"] = False
            discard_recovery_session(False)
            log_diagnostic("info", "Project saved", {"path": result, "revision": data.get("revision", 0)}, system="project_io", operation="save")
        else:
            metadata["project_path"] = old_path
        return result

    def load_project(path):
        result = _legacy_load_project(path)
        if result:
            _enrich_project_metadata(ensure_project()).setdefault("project", {})["project_path"] = str(path)
            ensure_editing_session()
            runtime["autosave_due"] = False
            runtime["recovery_due"] = False
            log_diagnostic("info", "Project loaded", {"path": path}, system="project_io", operation="load")
        return result

init 905 python in live_studio:
    _project_io_open_editor = open_editor

    def open_editor():
        ensure_editing_session()
        diagnostic_boundary("Editor session opened", {"session": runtime.get("editing_session_id")})
        try:
            return _project_io_open_editor()
        finally:
            try:
                flush_pending_input_edits(False)
                if project_dirty:
                    write_recovery_journal(True)
                    autosave_project(True)
                else:
                    discard_recovery_session(False)
            except Exception as exc:
                log_diagnostic("warning", "Editor close autosave failed", system="project_io", operation="close", exception=exc)
