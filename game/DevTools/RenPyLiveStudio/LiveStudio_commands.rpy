# Central command journal and mutation revisions.
# Existing editor functions continue to use their established undo entries;
# this adapter makes every committed command observable, recoverable, and
# consistently revisioned without forcing a risky all-at-once rewrite.

init -978 python in live_studio:
    import time as _command_time

    _legacy_history_push = _history_push
    _legacy_undo = undo
    _legacy_redo = redo
    _legacy_set_project_setting = set_project_setting
    _legacy_set_project_name_live = set_project_name_live
    _legacy_set_frame_name_live = set_frame_name_live

    def project_revision():
        try:
            return int(ensure_project().get("revision", 0) or 0)
        except Exception:
            return 0

    def _command_descriptor(entry, action="apply"):
        entry = entry or {}
        return {
            "id": new_id("command"),
            "action": str(action or "apply"),
            "type": str(entry.get("type") or "mutation"),
            "label": str(entry.get("label") or "Project mutation"),
            "frame_id": str(entry.get("frame_id") or current_frame_id or ""),
            "item_id": str(entry.get("item_id") or selected_item_id or ""),
            "time": int(_command_time.time()),
            "revision": project_revision(),
        }

    def _append_command_journal(entry, action="apply"):
        data = ensure_project()
        journal = data.setdefault("command_journal", [])
        descriptor = _command_descriptor(entry, action)
        journal.append(descriptor)
        del journal[:-int(globals().get("COMMAND_JOURNAL_LIMIT", 500))]
        runtime["last_command"] = descriptor
        runtime["recovery_due"] = True
        runtime["autosave_due"] = True
        return descriptor

    def touch_project(reason="Project mutation", entry=None):
        global project_dirty
        data = ensure_project()
        data["revision"] = int(data.get("revision", 0) or 0) + 1
        metadata = data.setdefault("project", {})
        metadata["updated_at"] = int(_command_time.time())
        metadata["live_studio_version"] = RELEASE_VERSION
        metadata["project_model_version"] = VERSION
        runtime["project_revision"] = data["revision"]
        runtime["last_mutation_reason"] = str(reason or "Project mutation")
        project_dirty = True
        descriptor = _append_command_journal(entry or {"label": reason}, "apply")
        try:
            schedule_project_autosave(reason)
        except Exception:
            pass
        return descriptor

    def _history_push(entry):
        _legacy_history_push(entry)
        touch_project(entry.get("label", "Project command") if isinstance(entry, dict) else "Project command", entry if isinstance(entry, dict) else None)

    def undo():
        if not history:
            return None
        before = project_revision()
        result = _legacy_undo()
        if project_revision() == before:
            data = ensure_project()
            data["revision"] = before + 1
        _append_command_journal({"label": "Undo", "type": "undo", "frame_id": current_frame_id}, "revert")
        try:
            schedule_project_autosave("Undo")
        except Exception:
            pass
        return result

    def redo():
        if not redo_stack:
            return None
        before = project_revision()
        result = _legacy_redo()
        if project_revision() == before:
            data = ensure_project()
            data["revision"] = before + 1
        _append_command_journal({"label": "Redo", "type": "redo", "frame_id": current_frame_id}, "reapply")
        try:
            schedule_project_autosave("Redo")
        except Exception:
            pass
        return result

    def set_project_setting(name, value):
        old = clone(project_setting(name, None))
        result = _legacy_set_project_setting(name, value)
        if old != value:
            touch_project("Setting changed: {}".format(name), {
                "type": "set_setting", "label": "Change {}".format(name), "item_id": name,
            })
        return result

    def set_project_name_live(value):
        old = project_name()
        result = _legacy_set_project_name_live(value)
        if old != str(value or "Untitled Live Studio Project"):
            touch_project("Rename project", {"type": "rename_project", "label": "Rename project"})
        return result

    def set_frame_name_live(frame_id, value):
        frame = frame_by_id(frame_id)
        old = (frame or {}).get("name")
        result = _legacy_set_frame_name_live(frame_id, value)
        if frame is not None and old != frame.get("name"):
            touch_project("Rename frame", {"type": "rename_frame", "label": "Rename frame", "frame_id": frame_id})
        return result

    def command_journal_rows(limit=80):
        rows = list(ensure_project().get("command_journal", []) or [])
        rows.reverse()
        return rows[:int(limit or 80)]

    def command_journal_text(limit=200):
        lines = ["Ren'Py Live Studio Command Journal"]
        for row in command_journal_rows(limit):
            lines.append("r{revision} {action} {label} [{type}] frame={frame_id} item={item_id}".format(
                revision=row.get("revision", 0), action=row.get("action", "apply"),
                label=row.get("label", "Command"), type=row.get("type", "mutation"),
                frame_id=row.get("frame_id", "") or "-", item_id=row.get("item_id", "") or "-",
            ))
        return "\n".join(lines)
