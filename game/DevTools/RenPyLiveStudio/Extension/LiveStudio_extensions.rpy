# Ren'Py Live Studio - generic extension registry.
# Extensions are optional and data-driven so the editor remains portable.

init -855 python in live_studio:
    from collections import OrderedDict

    extension_defs = OrderedDict()

    extension_selected_files = {}
    extension_selected_categories = {}
    extension_selected_file_domains = {}
    extension_command_queries = {}
    extension_file_queries = {}

    class ExtensionFilterInputValue(renpy.store.InputValue):
        def __init__(self, ext_id, kind):
            self.ext_id = safe_identifier(ext_id, "extension")
            self.kind = str(kind or "command")
            super(ExtensionFilterInputValue, self).__init__()

        def get_text(self):
            source = extension_file_queries if self.kind == "file" else extension_command_queries
            return source.get(self.ext_id, "")

        def set_text(self, value):
            source = extension_file_queries if self.kind == "file" else extension_command_queries
            source[self.ext_id] = str(value or "")
            restart()

        def enter(self):
            return None

    def register_extension(ext_id, title=None, description="", commands=None, summary=None, files=None, file_preview=None, apply_preview=None, available=None, order=100):
        ext_id = safe_identifier(ext_id, "extension")
        data = extension_defs.setdefault(ext_id, {})
        data.update({
            "id": ext_id,
            "title": title or ext_id.replace("_", " ").title(),
            "description": description or "",
            "commands": list(commands or []),
            "summary": summary,
            "files": files,
            "file_preview": file_preview,
            "apply_preview": apply_preview,
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

    def selected_extension_file(ext=None):
        if ext is None:
            ext = active_extension()
        ext_id = (ext or {}).get("id")
        return extension_selected_files.get(ext_id)

    def set_selected_extension_file(ext_id, file_id):
        extension_selected_files[safe_identifier(ext_id, "extension")] = str(file_id or "")
        restart()

    def selected_extension_category(ext=None):
        if ext is None:
            ext = active_extension()
        ext_id = (ext or {}).get("id")
        return extension_selected_categories.get(ext_id, "All")

    def set_selected_extension_category(ext_id, category):
        extension_selected_categories[safe_identifier(ext_id, "extension")] = str(category or "All")
        restart()

    def selected_extension_file_domain(ext=None):
        if ext is None:
            ext = active_extension()
        ext_id = (ext or {}).get("id")
        return extension_selected_file_domains.get(ext_id, "All")

    def set_selected_extension_file_domain(ext_id, domain):
        extension_selected_file_domains[safe_identifier(ext_id, "extension")] = str(domain or "All")
        restart()

    def extension_filter_input(ext_id, kind):
        return ExtensionFilterInputValue(ext_id, kind)

    def extension_command_query(ext=None):
        if ext is None:
            ext = active_extension()
        ext_id = (ext or {}).get("id")
        return extension_command_queries.get(ext_id, "")

    def extension_file_query(ext=None):
        if ext is None:
            ext = active_extension()
        ext_id = (ext or {}).get("id")
        return extension_file_queries.get(ext_id, "")

    def _extension_query_parts(value):
        value = str(value or "").strip().lower()
        if not value:
            return []
        return [part for part in value.split() if part]

    def _extension_text_matches(parts, *values):
        if not parts:
            return True
        haystack = " ".join(str(value or "").lower() for value in values)
        return all(part in haystack for part in parts)

    def extension_file_rows(ext):
        fn = (ext or {}).get("files")
        if fn is None:
            return []
        try:
            return list(fn() or [])
        except Exception as exc:
            log_diagnostic("warning", "Extension file index failed", {"extension": (ext or {}).get("id"), "error": str(exc)})
            return [{"id": "", "label": "File index error", "path": str(exc), "domain": "error", "editable": False}]

    def extension_file_domains(ext):
        domains = []
        for row in extension_file_rows(ext):
            domain = str(row.get("domain", "Other") or "Other")
            if domain not in domains:
                domains.append(domain)
        return ["All"] + domains

    def filtered_extension_file_rows(ext):
        selected = selected_extension_file_domain(ext)
        rows = extension_file_rows(ext)
        if not selected or selected == "All":
            filtered = rows
        else:
            filtered = [row for row in rows if str(row.get("domain", "Other") or "Other") == selected]
        parts = _extension_query_parts(extension_file_query(ext))
        if parts:
            filtered = [
                row for row in filtered
                if _extension_text_matches(parts, row.get("id"), row.get("label"), row.get("path"), row.get("domain"))
            ]
        return filtered

    def extension_file_preview(ext):
        fn = (ext or {}).get("file_preview")
        file_id = selected_extension_file(ext)
        if fn is None or not file_id:
            return ""
        try:
            return str(fn(file_id) or "")
        except Exception as exc:
            log_diagnostic("warning", "Extension file preview failed", {"extension": (ext or {}).get("id"), "file": file_id, "error": str(exc)})
            return "Preview error: {}".format(exc)

    def preview_selected_extension_file():
        ext = active_extension()
        file_id = selected_extension_file(ext)
        if not ext or not file_id:
            return None
        set_extension_preview("File: " + str(file_id), extension_file_preview(ext))
        return None

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

    def apply_extension_preview():
        ext = active_extension()
        text = extension_preview_text()
        fn = (ext or {}).get("apply_preview")
        if not ext or not text or fn is None:
            return None
        try:
            result = fn(selected_extension_file(ext), text)
            if isinstance(result, str):
                set_extension_preview("Apply Result", result)
            return result
        except Exception as exc:
            log_diagnostic("error", "Extension apply failed", {"extension": ext.get("id"), "error": str(exc)})
            set_extension_preview("Apply Error", str(exc))
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

    def extension_command_categories(ext):
        cats = []
        for command in extension_commands(ext):
            cat = str(command.get("category", "General") or "General")
            if cat not in cats:
                cats.append(cat)
        return ["All"] + cats

    def filtered_extension_commands(ext):
        selected = selected_extension_category(ext)
        commands = extension_commands(ext)
        if not selected or selected == "All":
            filtered = commands
        else:
            filtered = [command for command in commands if str(command.get("category", "General") or "General") == selected]
        parts = _extension_query_parts(extension_command_query(ext))
        if parts:
            filtered = [
                command for command in filtered
                if _extension_text_matches(parts, command.get("id"), command.get("title"), command.get("description"), command.get("category"))
            ]
        return filtered

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
