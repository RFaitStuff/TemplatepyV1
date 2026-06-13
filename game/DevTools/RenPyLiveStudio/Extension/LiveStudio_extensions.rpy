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

    def register_extension(ext_id, title=None, description="", commands=None, summary=None, files=None, file_preview=None, apply_preview=None, available=None, order=100, api_version=1, capabilities=None, requirements=None, capability_provider=None):
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
            "api_version": int(api_version or 1),
            "capabilities": dict(capabilities or {}),
            "requirements": dict(requirements or {}),
            "capability_provider": capability_provider,
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
        set_extension_preview("File: " + str(file_id), extension_file_preview(ext), kind="file", applyable=False)
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

    def set_extension_preview(title, text, kind="text", applyable=False, metadata=None):
        runtime["extension_preview_title"] = str(title or "Preview")
        runtime["extension_preview_text"] = str(text or "")
        runtime["extension_preview_kind"] = str(kind or "text")
        runtime["extension_preview_applyable"] = bool(applyable)
        runtime["extension_preview_metadata"] = json_safe(metadata or {})
        runtime["extension_preview_generation"] = int(runtime.get("extension_preview_generation", 0)) + 1
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


    def extension_preview_apply_status(ext=None):
        ext = ext or active_extension()
        if not ext:
            return False, "No extension is active."
        if not runtime.get("extension_preview_applyable", False):
            return False, "This preview is reference/report content. Use a typed Write command for source changes."
        if not selected_extension_file(ext):
            return False, "Select a writable project file first."
        if (ext or {}).get("apply_preview") is None:
            return False, "This extension does not support raw preview application."
        return True, ""

    def apply_extension_preview():
        ext = active_extension()
        text = extension_preview_text()
        fn = (ext or {}).get("apply_preview")
        enabled, reason = extension_preview_apply_status(ext)
        if not ext or not text or fn is None or not enabled:
            if reason:
                set_extension_preview("Apply Unavailable", reason, kind="status", applyable=False)
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

    def extension_capabilities(ext):
        ext = ext or {}
        provider = ext.get("capability_provider")
        if provider is not None:
            try:
                values = provider()
                if isinstance(values, dict):
                    return values
            except Exception as exc:
                log_diagnostic("warning", "Extension capability provider failed", {"extension": ext.get("id")}, system="extensions", operation="capabilities", exception=exc)
        capabilities = ext.get("capabilities", {}) or {}
        return capabilities if isinstance(capabilities, dict) else {}

    def _extension_capability_value(ext, name):
        capabilities = extension_capabilities(ext)
        value = capabilities.get(name, 0)
        try:
            return int(value or 0)
        except Exception:
            return 0

    def extension_command_status(ext, command):
        if not isinstance(command, dict):
            return False, "Invalid command definition."
        minimum_api = int(command.get("extension_api", 1) or 1)
        if int(globals().get("EXTENSION_API_VERSION", 1)) < minimum_api:
            return False, "Requires Live Studio extension API {}.".format(minimum_api)
        requirements = command.get("requires", {}) or {}
        for capability, minimum in requirements.items():
            try:
                minimum = int(minimum or 0)
            except Exception:
                minimum = 0
            actual = _extension_capability_value(ext, capability)
            if actual < minimum:
                return False, "Requires {} capability {} (available {}).".format(capability, minimum, actual)
        available = command.get("available")
        if available is not None:
            try:
                result = available()
                if isinstance(result, tuple):
                    if not bool(result[0]):
                        return False, str(result[1] if len(result) > 1 else "Unavailable")
                elif not bool(result):
                    return False, str(command.get("unavailable_reason") or "Unavailable in this project.")
            except Exception as exc:
                log_diagnostic("warning", "Extension command availability failed", {"extension": (ext or {}).get("id"), "command": command.get("id")}, system="extensions", operation="command_status", exception=exc)
                return False, "Availability check failed: {}".format(exc)
        return True, ""

    def extension_commands(ext):
        out = []
        for command in (ext or {}).get("commands", []):
            if not isinstance(command, dict):
                continue
            row = dict(command)
            enabled, reason = extension_command_status(ext, row)
            row["_enabled"] = enabled
            row["_disabled_reason"] = reason
            out.append(row)
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
            enabled, reason = extension_command_status(ext, command)
            if not enabled:
                set_extension_preview("Command Unavailable", reason)
                return None
            fn = command.get("action")
            if fn is None:
                return None
            try:
                preview_generation = int(runtime.get("extension_preview_generation", 0))
                result = fn()
                # Builders such as Project Tac's typed preview helper may have
                # already supplied richer preview metadata. Do not overwrite it.
                if isinstance(result, str) and int(runtime.get("extension_preview_generation", 0)) == preview_generation:
                    set_extension_preview(command.get("title", "Preview"), result, kind=command.get("preview_kind", "text"), applyable=bool(command.get("preview_applyable", False)), metadata={"command": command_id})
                return result
            except Exception as exc:
                log_diagnostic("error", "Extension command failed", {"extension": ext_id, "command": command_id, "error": str(exc)})
                set_extension_preview("Extension Error", str(exc))
                return None
        return None
