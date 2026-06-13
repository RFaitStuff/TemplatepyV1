# Ren'Py Live Studio - generic extension registry.
# Extensions are optional and data-driven so the editor remains portable.

init -855 python in live_studio:
    from collections import OrderedDict

    extension_defs = OrderedDict()

    def register_extension(ext_id, title=None, description="", commands=None, summary=None, available=None, order=100):
        ext_id = safe_identifier(ext_id, "extension")
        data = extension_defs.setdefault(ext_id, {})
        data.update({
            "id": ext_id,
            "title": title or ext_id.replace("_", " ").title(),
            "description": description or "",
            "commands": list(commands or []),
            "summary": summary,
            "available": available,
            "order": int(order or 100),
        })
        return data

    def extension_available(ext):
        if not ext:
            return False
        fn = ext.get("available")
        if fn is None:
            return True
        try:
            return bool(fn())
        except Exception as exc:
            log_diagnostic("warning", "Extension availability check failed", {"extension": ext.get("id"), "error": str(exc)})
            return False

    def visible_extensions():
        rows = [ext for ext in extension_defs.values() if extension_available(ext)]
        rows.sort(key=lambda ext: (ext.get("order", 100), ext.get("title", ext.get("id", ""))))
        return rows

    def extension_tab_id(ext_id):
        return "Extension:" + safe_identifier(ext_id, "extension")

    def is_extension_bottom_tab(value=None):
        value = str(bottom_tab if value is None else value)
        return value.startswith("Extension:")

    def active_extension_id():
        if not is_extension_bottom_tab():
            return None
        return str(bottom_tab).split(":", 1)[1]

    def active_extension():
        return extension_defs.get(active_extension_id())

    def extension_summary_rows(ext):
        fn = (ext or {}).get("summary")
        if fn is None:
            return []
        try:
            rows = fn()
            return list(rows or [])
        except Exception as exc:
            log_diagnostic("warning", "Extension summary failed", {"extension": (ext or {}).get("id"), "error": str(exc)})
            return [{"label": "Summary error", "value": str(exc)}]

    def set_extension_preview(title, text):
        runtime["extension_preview_title"] = str(title or "Preview")
        runtime["extension_preview_text"] = str(text or "")
        restart()

    def extension_preview_title():
        return runtime.get("extension_preview_title", "Preview")

    def extension_preview_text():
        return runtime.get("extension_preview_text", "")

    def copy_extension_preview():
        text = extension_preview_text()
        if text and "copy_text_to_clipboard" in globals():
            if copy_text_to_clipboard(text):
                log_diagnostic("info", "Extension preview copied to clipboard.")
        return None

    def extension_commands(ext):
        out = []
        for command in (ext or {}).get("commands", []):
            if not isinstance(command, dict):
                continue
            available = command.get("available")
            if available is not None:
                try:
                    if not available():
                        continue
                except Exception:
                    continue
            out.append(command)
        return out

    def run_extension_command(ext_id, command_id):
        ext = extension_defs.get(safe_identifier(ext_id, "extension"))
        if not ext:
            return None
        for command in extension_commands(ext):
            if command.get("id") != command_id:
                continue
            fn = command.get("action")
            if fn is None:
                return None
            try:
                result = fn()
                if isinstance(result, str):
                    set_extension_preview(command.get("title", "Preview"), result)
                return result
            except Exception as exc:
                log_diagnostic("error", "Extension command failed", {"extension": ext_id, "command": command_id, "error": str(exc)})
                set_extension_preview("Extension Error", str(exc))
                return None
        return None
