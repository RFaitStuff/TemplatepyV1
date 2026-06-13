# v3.6 debugger augmentation. Kept separate so diagnostic/report concerns do not
# further enlarge the project state module.

init -843 python in live_studio:
    import json as _debug_json

    _legacy_build_debug_report_v36 = build_debug_report

    def build_debug_report():
        base = _legacy_build_debug_report_v36()
        payload = {}
        try:
            payload = _debug_json.loads(base.split("\n", 1)[1])
        except Exception:
            payload = {"legacy_report": base}
        selected, _parent_id, selected_kind = selected_item()
        payload["project_lifecycle"] = project_lifecycle_summary() if "project_lifecycle_summary" in globals() else {}
        payload["command_journal"] = clone(command_journal_rows(100)) if "command_journal_rows" in globals() else []
        payload["diagnostic_summary"] = diagnostic_summary_rows() if "diagnostic_summary_rows" in globals() else []
        payload["object_rules"] = {
            "category": object_category(selected, selected_kind) if "object_category" in globals() else None,
            "category_label": object_category_label(selected, selected_kind) if "object_category_label" in globals() else None,
            "edit_reason": object_edit_reason(selected, selected_kind) if "object_edit_reason" in globals() else None,
            "x_coordinate_mode": coordinate_mode(selected, "x") if selected and "coordinate_mode" in globals() else None,
            "y_coordinate_mode": coordinate_mode(selected, "y") if selected and "coordinate_mode" in globals() else None,
            "parent_layout_controls_position": parent_layout_controls_position(selected.get("id")) if selected and "parent_layout_controls_position" in globals() else None,
        }
        payload["asset_metadata"] = clone(runtime.get("asset_metadata_summary", {}))
        payload["asset_metadata_issues"] = clone(asset_metadata_issues[:100]) if "asset_metadata_issues" in globals() else []
        payload["export_plan"] = clone(runtime.get("export_plan", {}))
        payload["last_export_record"] = clone(runtime.get("last_export_record", {}))
        payload["extensions"] = []
        for ext in visible_extensions() if "visible_extensions" in globals() else []:
            payload["extensions"].append({
                "id": ext.get("id"), "title": ext.get("title"),
                "api_version": ext.get("api_version"),
                "capabilities": clone(extension_capabilities(ext) if "extension_capabilities" in globals() else ext.get("capabilities", {})),
                "requirements": clone(ext.get("requirements", {})),
            })
        if "pt_available" in globals() and pt_available():
            try:
                source_index = pt_build_source_index(False)
                payload["project_tac"] = {
                    "capabilities": pt_capability_status(),
                    "source_signature": source_index.get("signature"),
                    "indexed_files": len(source_index.get("files", {})),
                    "indexed_objects": sum(len(rows) for rows in source_index.get("by_kind", {}).values()),
                    "index_errors": clone(source_index.get("errors", [])),
                    "validation": clone(runtime.get("project_tac_validation", [])),
                    "pending_change_plan": clone(runtime.get("project_tac_change_plan", {})),
                }
            except Exception as exc:
                payload["project_tac"] = {"report_error": repr(exc)}
        return "Ren'Py Live Studio Debug Report\n" + _debug_json.dumps(json_safe(payload), indent=2, sort_keys=True, ensure_ascii=False)

    def debug_report_preview(limit=12000):
        key = (
            int(runtime.get("state_revision", 0)),
            int(runtime.get("diagnostic_revision", 0)),
            project_revision() if "project_revision" in globals() else 0,
            selected_item_id, selected_item_kind,
            len(runtime.get("diagnostics", [])), right_panel_tab,
        )
        cached = runtime.get("debug_report_preview_cache")
        if not cached or cached.get("key") != key:
            report = build_debug_report()
            value = report if len(report) <= int(limit) else report[:int(limit)] + "\n... [preview truncated; Copy Full Report includes everything]"
            cached = {"key": key, "value": value}
            runtime["debug_report_preview_cache"] = cached
        return cached.get("value", "")
