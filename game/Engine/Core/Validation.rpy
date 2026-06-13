# =============================================================================
# Project Tac Validation Facade
# -----------------------------------------------------------------------------
# Runtime-safe validation entry point for tools, startup checks, and optional
# debug UI. DevTools can provide deeper validators, but game/runtime code should
# call these helpers instead of reaching into DevTools directly.
# =============================================================================

define project_tac_startup_validation = True


init -70 python:
    project_tac_validators = []

    def register_project_tac_validator(fn):
        if fn not in project_tac_validators:
            project_tac_validators.append(fn)
        return fn

    def project_tac_validation_issues(include_devtools=True):
        issues = []

        if include_devtools:
            try:
                debug_issues = debug_validation_issues()
                if debug_issues:
                    issues.extend(debug_issues)
            except Exception:
                pass

        for validator in list(project_tac_validators):
            try:
                result = validator()
                if not result:
                    continue
                if isinstance(result, (list, tuple, set)):
                    issues.extend(str(item) for item in result if item)
                else:
                    issues.append(str(result))
            except Exception as error:
                issues.append("Validator '{}' failed: {!r}".format(
                    getattr(validator, "__name__", repr(validator)),
                    error,
                ))

        return issues

    def project_tac_validation_report(include_devtools=True):
        issues = project_tac_validation_issues(include_devtools=include_devtools)
        if not issues:
            return "PROJECT TAC VALIDATION\n======================\nNo structural issues detected."
        return "PROJECT TAC VALIDATION\n======================\n" + "\n".join(
            "{}. {}".format(index + 1, issue) for index, issue in enumerate(issues)
        )

    def project_tac_startup_validate():
        if not project_tac_startup_validation:
            return None
        try:
            if not config.developer:
                return None
        except Exception:
            return None
        issues = project_tac_validation_issues()
        if issues:
            try:
                renpy.log(project_tac_validation_report(include_devtools=False))
            except Exception:
                pass
            try:
                renpy.notify("Project Tac validation found {} issue(s).".format(len(issues)))
            except Exception:
                pass
        return None

    def _validate_project_tac_descriptor():
        issues = []
        descriptor = globals().get("PROJECT_TAC_ENGINE", {}) or {}
        paths = descriptor.get("paths", {}) or {}
        capabilities = descriptor.get("capabilities", {}) or {}

        if descriptor.get("id") != "project_tac":
            issues.append("PROJECT_TAC_ENGINE id should be 'project_tac'.")
        if not descriptor.get("engine_version"):
            issues.append("PROJECT_TAC_ENGINE has no engine_version.")
        if not paths:
            issues.append("PROJECT_TAC_ENGINE has no paths map.")
        for key in ("characters_data", "locations_data", "items_data", "quests_data", "content_root"):
            if not paths.get(key):
                issues.append("PROJECT_TAC_PATHS is missing '{}'.".format(key))
        for key in ("characters", "locations", "quests", "inventory", "validation"):
            if int(capabilities.get(key, 0) or 0) <= 0:
                issues.append("PROJECT_TAC_ENGINE capability '{}' is disabled or missing.".format(key))
        return issues

    def _validate_project_tac_core_data():
        issues = []
        for cid in sorted((globals().get("character_stats", {}) or {}).keys()):
            if cid not in (globals().get("character_speakers", {}) or {}):
                issues.append("Character '{}' has no speaker object.".format(cid))
        for loc_id in globals().get("location_order", []) or []:
            if loc_id not in (globals().get("locations", {}) or {}):
                issues.append("location_order references missing location '{}'.".format(loc_id))
        for item_id, item_data in (globals().get("item_defs", {}) or {}).items():
            show_when = item_data.get("show_when") or item_data.get("hidden_until")
            if show_when:
                try:
                    first_missing_requirement(show_when)
                except Exception:
                    issues.append("Item '{}' has an invalid visibility requirement.".format(item_id))
        for qid, qdef in (globals().get("quest_defs", {}) or {}).items():
            if not qdef.get("title"):
                issues.append("Quest '{}' has no title.".format(qid))
            for objective in qdef.get("objectives", []) or []:
                if isinstance(objective, dict) and not (objective.get("oid") or objective.get("id")):
                    issues.append("Quest '{}' has an objective with no id.".format(qid))
        return issues

    register_project_tac_validator(_validate_project_tac_descriptor)
    register_project_tac_validator(_validate_project_tac_core_data)


init 999 python:
    try:
        if project_tac_startup_validate not in config.start_callbacks:
            config.start_callbacks.append(project_tac_startup_validate)
    except Exception:
        pass
