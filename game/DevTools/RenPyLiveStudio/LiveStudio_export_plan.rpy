# Export planning, minimal writes, hashes, manifests, and history.

init -869 python in live_studio:
    import hashlib as _export_hashlib
    import json as _export_json
    import os as _export_os
    import shutil as _export_shutil
    import time as _export_time
    import uuid as _export_uuid

    _legacy_replace_editor_owned_blocks = replace_editor_owned_blocks
    _legacy_patch_handwritten_file = patch_handwritten_file

    def export_text_hash(text):
        return _export_hashlib.sha256(str(text or "").encode("utf-8", "replace")).hexdigest()

    def build_export_plan(sections=None, force=False):
        values = generate_exports() if force or not globals().get("export_cache") else dict(export_cache)
        validation = runtime.get("export_validation") or validate_exports(values)
        selected = set(sections or [section for section, _filename in EXPORT_SECTIONS])
        sync_hashes = ensure_project().setdefault("export_sync_hashes", {})
        files = []
        for section, filename in EXPORT_SECTIONS:
            if section not in selected:
                continue
            text = values.get(section, "")
            new_hash = export_text_hash(text)
            previous_hash = sync_hashes.get(section)
            status = "unchanged" if previous_hash == new_hash else "changed"
            files.append({
                "section": section,
                "filename": filename,
                "text": text,
                "new_hash": new_hash,
                "previous_hash": previous_hash,
                "status": status,
                "bytes": len(text.encode("utf-8", "replace")),
            })
        plan = {
            "id": new_id("export_plan"),
            "created_at": int(_export_time.time()),
            "project_revision": project_revision() if "project_revision" in globals() else ensure_project().get("revision", 0),
            "files": files,
            "validation": clone(validation),
            "blocked": bool(validation.get("errors")),
        }
        runtime["export_plan"] = plan
        return plan

    def export_plan_summary(plan=None):
        plan = plan or runtime.get("export_plan")
        if not plan:
            return "No export plan generated yet. Use Regenerate to validate and compare outputs."
        changed = [row for row in plan.get("files", []) if row.get("status") == "changed"]
        unchanged = [row for row in plan.get("files", []) if row.get("status") == "unchanged"]
        errors = plan.get("validation", {}).get("errors", [])
        warnings = plan.get("validation", {}).get("warnings", [])
        rows = [
            "Export plan: {} changed, {} synchronized".format(len(changed), len(unchanged)),
            "Validation: {} errors, {} warnings".format(len(errors), len(warnings)),
        ]
        for row in plan.get("files", []):
            rows.append("{}  {}  {} bytes".format(row.get("status", "changed").upper(), row.get("filename"), row.get("bytes", 0)))
        if errors:
            rows.append("")
            rows.extend("ERROR: {}".format(message) for message in errors[:20])
        if warnings:
            rows.append("")
            rows.extend("WARNING: {}".format(message) for message in warnings[:20])
        return "\n".join(rows)

    def _export_atomic_write(path, text):
        if "_atomic_write_text" in globals():
            return _atomic_write_text(path, text)
        parent = _export_os.path.dirname(path)
        if parent and not _export_os.path.isdir(parent):
            _export_os.makedirs(parent)
        temporary = "{}.{}.tmp".format(path, _export_uuid.uuid4().hex[:8])
        try:
            with open(temporary, "w", encoding="utf-8", newline="") as output:
                output.write(str(text))
                output.flush()
                try:
                    _export_os.fsync(output.fileno())
                except Exception:
                    pass
            _export_os.replace(temporary, path)
        finally:
            if _export_os.path.exists(temporary):
                try:
                    _export_os.remove(temporary)
                except Exception:
                    pass
        return path

    def regenerate_export_plan():
        plan = build_export_plan(None, True)
        runtime["export_plan"] = plan
        restart()
        return plan

    def export_files(sections=None, include_unchanged=False):
        global last_export_directory
        flush_pending_input_edits(False)
        plan = build_export_plan(sections, True)
        if plan.get("blocked"):
            log_diagnostic("error", "Export blocked by validation errors", plan.get("validation"), system="export", operation="plan", category="user_content", recovery="Fix the reported project/export errors and regenerate the plan.")
            try:
                renpy.notify("Export blocked by validation errors")
            except Exception:
                pass
            return None
        rows = [row for row in plan.get("files", []) if include_unchanged or row.get("status") == "changed"]
        if not rows:
            record_export_history({
                "status": "synchronized", "plan_id": plan.get("id"), "files": [],
                "message": "All selected sections already match the last export hashes.",
            })
            try:
                renpy.notify("Export already synchronized")
            except Exception:
                pass
            return runtime.get("last_export_directory")
        project_id = safe_identifier(ensure_project().get("project", {}).get("id"), "project")
        timestamp = _export_time.strftime("%Y%m%d_%H%M%S")
        directory = _export_os.path.join(config.gamedir, EXPORT_DIRECTORY, "{}_{}".format(project_id, timestamp))
        written = []
        try:
            if not _export_os.path.isdir(directory):
                _export_os.makedirs(directory)
            for row in rows:
                path = _export_os.path.join(directory, row.get("filename"))
                _export_atomic_write(path, row.get("text", ""))
                written.append({
                    "section": row.get("section"), "path": path,
                    "previous_hash": row.get("previous_hash"), "new_hash": row.get("new_hash"),
                    "bytes": row.get("bytes", 0),
                })
            manifest = {
                "format": "renpy_live_studio_export",
                "release_version": RELEASE_VERSION,
                "project_id": project_id,
                "project_revision": plan.get("project_revision"),
                "created_at": plan.get("created_at"),
                "files": written,
                "validation": plan.get("validation"),
            }
            _export_atomic_write(_export_os.path.join(directory, "export_manifest.json"), _export_json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
            sync_hashes = ensure_project().setdefault("export_sync_hashes", {})
            for row in rows:
                sync_hashes[row.get("section")] = row.get("new_hash")
            last_export_directory = directory
            runtime["last_export_directory"] = directory
            record_export_history({
                "status": "applied", "plan_id": plan.get("id"), "directory": directory,
                "files": written, "validation": plan.get("validation"),
            })
            schedule_project_autosave("Export history updated") if "schedule_project_autosave" in globals() else None
            log_diagnostic("info", "Export completed", {"directory": directory, "files": len(written)}, system="export", operation="write")
            renpy.notify("Exported {} changed file(s)".format(len(written)))
            return directory
        except Exception as exc:
            record_export_history({
                "status": "failed", "plan_id": plan.get("id"), "directory": directory,
                "files": written, "error": repr(exc),
            })
            log_diagnostic("error", "Export failed", {"directory": directory, "written": written}, system="export", operation="write", category="source_write", exception=exc, recovery="The export target is a new timestamped folder; existing game source was not modified.")
            try:
                renpy.notify("Export failed")
            except Exception:
                pass
            return None

    def _safe_source_replace(path, original, updated, operation):
        if original == updated:
            log_diagnostic("info", "Source already synchronized", {"path": path}, system="export", operation=operation)
            return {"changed": False, "path": path, "backup": None}
        backup = None
        if _export_os.path.isfile(path):
            stamp = _export_time.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(int((_export_time.time() % 1.0) * 1000))
            backup = "{}.{}.live_studio_backup".format(path, stamp)
            _export_shutil.copy2(path, backup)
        _export_atomic_write(path, updated)
        record_export_history({
            "status": "applied", "operation": operation,
            "files": [{"path": path, "backup": backup, "previous_hash": export_text_hash(original), "new_hash": export_text_hash(updated)}],
        })
        return {"changed": True, "path": path, "backup": backup}

    def replace_editor_owned_blocks(path, section="story"):
        settings = ensure_project().get("settings", {})
        if not settings.get("experimental_replace_blocks", False):
            renpy.notify("Experimental block replacement is disabled")
            return False
        marker_id = safe_identifier(ensure_project().get("project", {}).get("id"), "project")
        begin = "# live-studio:begin {} {}".format(marker_id, section)
        end = "# live-studio:end {} {}".format(marker_id, section)
        replacement = begin + "\n" + export_preview(section).rstrip() + "\n" + end
        try:
            original = ""
            if _export_os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as source:
                    original = source.read()
            if begin in original and end in original:
                prefix, remainder = original.split(begin, 1)
                _old, suffix = remainder.split(end, 1)
                updated = prefix + replacement + suffix
            else:
                updated = original.rstrip() + "\n\n" + replacement + "\n"
            result = _safe_source_replace(path, original, updated, "replace_editor_block")
            renpy.notify("Editor-owned block {}".format("replaced" if result.get("changed") else "already synchronized"))
            return True
        except Exception as exc:
            log_diagnostic("error", "Block replacement failed", {"path": path, "section": section}, system="export", operation="replace_editor_block", category="source_write", exception=exc)
            return False

    def patch_handwritten_file(path, expected_text, replacement_text):
        settings = ensure_project().get("settings", {})
        if not settings.get("experimental_patch_files", False):
            renpy.notify("Experimental handwritten patching is disabled")
            return False
        try:
            with open(path, "r", encoding="utf-8") as source:
                original = source.read()
            if expected_text not in original:
                raise ValueError("The expected source block no longer matches the file")
            updated = original.replace(expected_text, replacement_text, 1)
            result = _safe_source_replace(path, original, updated, "patch_handwritten_file")
            renpy.notify("Handwritten source {}".format("patched" if result.get("changed") else "already synchronized"))
            return True
        except Exception as exc:
            log_diagnostic("error", "Handwritten patch failed", {"path": path}, system="export", operation="patch_handwritten_file", category="source_write", exception=exc, recovery="Refresh the source block and review a new diff before retrying.")
            renpy.notify("Patch failed")
            return False
