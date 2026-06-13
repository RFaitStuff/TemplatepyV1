# Structured diagnostics shared by the core editor and extensions.
# Loaded after LiveStudio_project.rpy so it can preserve the old call surface
# while enriching every entry with stable fields useful in copied reports.

init -979 python in live_studio:
    import time as _diagnostic_time

    DIAGNOSTIC_SEVERITIES = ("debug", "info", "warning", "error", "fatal")
    DIAGNOSTIC_CATEGORIES = (
        "compatibility_fallback",
        "user_content",
        "runtime_inspection",
        "source_write",
        "editor_defect",
        "lifecycle",
    )

    def _diagnostic_source_fields(source=None):
        source = source or {}
        if not isinstance(source, dict):
            return {"file": "", "line": 0}
        location = source.get("location") or source.get("source_location")
        filename = source.get("file") or source.get("filename") or source.get("source") or ""
        line = source.get("line") or 0
        if isinstance(location, (list, tuple)) and location:
            filename = location[0] or filename
            if len(location) > 1:
                line = location[1] or line
        try:
            line = int(line or 0)
        except Exception:
            line = 0
        return {"file": str(filename or ""), "line": line}

    def log_diagnostic(level, message, context=None, system="live_studio", operation="", object_id=None,
                       category=None, recovery="", exception=None, source=None, frame_id=None):
        level = str(level or "info").lower()
        if level not in DIAGNOSTIC_SEVERITIES:
            level = "info"
        if category is None:
            if level in ("error", "fatal"):
                category = "editor_defect"
            elif level == "warning":
                category = "runtime_inspection"
            else:
                category = "lifecycle"
        category = str(category or "lifecycle")
        source_fields = _diagnostic_source_fields(source)
        entry = {
            "id": new_id("diag") if "new_id" in globals() else "diag_{}".format(int(_diagnostic_time.time() * 1000)),
            "severity": level,
            "level": level,
            "category": category,
            "system": str(system or "live_studio"),
            "operation": str(operation or ""),
            "message": str(message or ""),
            "object_id": str(object_id or ""),
            "frame_id": str(frame_id or current_frame_id or ""),
            "source_file": source_fields["file"],
            "source_line": source_fields["line"],
            "exception": repr(exception) if exception is not None else "",
            "recovery": str(recovery or ""),
            "context": json_safe(context or {}),
            "time": int(_diagnostic_time.time()),
        }
        entries = runtime.setdefault("diagnostics", [])
        entries.append(entry)
        del entries[:-int(globals().get("DIAGNOSTIC_LIMIT", 500))]
        runtime["diagnostic_revision"] = int(runtime.get("diagnostic_revision", 0)) + 1
        try:
            renpy.log("[Live Studio][{}][{}] {}".format(entry["severity"].upper(), entry["system"], entry["message"]))
        except Exception:
            pass
        return entry

    def diagnostic_boundary(label, context=None):
        return log_diagnostic(
            "debug", "--- {} ---".format(label), context,
            system="diagnostics", operation="boundary", category="lifecycle",
        )

    def diagnostic_entries(minimum="debug", include_compatibility=None):
        order = {name: index for index, name in enumerate(DIAGNOSTIC_SEVERITIES)}
        threshold = order.get(str(minimum or "debug").lower(), 0)
        if include_compatibility is None:
            include_compatibility = bool(project_setting("diagnostics_compatibility_fallbacks", False)) if "project_setting" in globals() else False
        rows = []
        for entry in runtime.get("diagnostics", []) or []:
            severity = entry.get("severity", entry.get("level", "info"))
            if order.get(str(severity).lower(), 1) < threshold:
                continue
            if not include_compatibility and entry.get("category") == "compatibility_fallback":
                continue
            rows.append(entry)
        return rows

    def clear_diagnostics():
        runtime["diagnostics"] = []
        runtime["diagnostic_revision"] = int(runtime.get("diagnostic_revision", 0)) + 1
        runtime.pop("debug_report_preview_cache", None)
        restart()

    def diagnostic_summary_rows():
        counts = {severity: 0 for severity in DIAGNOSTIC_SEVERITIES}
        for entry in diagnostic_entries("debug", True):
            severity = str(entry.get("severity", entry.get("level", "info"))).lower()
            counts[severity if severity in counts else "info"] += 1
        return [{"label": severity.title(), "value": counts[severity]} for severity in DIAGNOSTIC_SEVERITIES if counts[severity]]

    def diagnostics_text(minimum="debug"):
        lines = []
        for entry in diagnostic_entries(minimum):
            source = ""
            if entry.get("source_file"):
                source = " {}:{}".format(entry.get("source_file"), entry.get("source_line") or "?")
            lines.append("[{severity}] {system}.{operation}{source} - {message}".format(
                severity=str(entry.get("severity", "info")).upper(),
                system=entry.get("system", "live_studio"),
                operation=entry.get("operation", "") or "event",
                source=source,
                message=entry.get("message", ""),
            ))
            if entry.get("recovery"):
                lines.append("  Recovery: {}".format(entry.get("recovery")))
            if entry.get("exception"):
                lines.append("  Exception: {}".format(entry.get("exception")))
            if entry.get("context"):
                lines.append("  Context: {}".format(entry.get("context")))
        return "\n".join(lines)
