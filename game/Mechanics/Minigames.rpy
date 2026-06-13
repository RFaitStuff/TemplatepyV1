# =============================================================================
# Universal Minigame Starter
# =============================================================================
# Register any future minigame here, then call:
#   $ start_minigame("lockpick")
# Skip mode lets story builds and accessibility settings bypass mechanics.
# =============================================================================

default minigame_skip_mode = False
default minigame_results = {}


init -2 python:
    minigame_defs = {}

    def minigame(game_id, label=None, skip_label=None, skip_result="skipped", requires=None, fail_forward=True, **extra):
        data = minigame_defs.setdefault(game_id, {})
        data.update({
            "id": game_id,
            "label": label,
            "skip_label": skip_label,
            "skip_result": skip_result,
            "requires": requires,
            "fail_forward": fail_forward,
        })
        data.update(extra)
        return data


init python:

    def set_minigame_skip_mode(value=True):
        global minigame_skip_mode
        minigame_skip_mode = bool(value)
        return None

    def complete_minigame(game_id, result="win", **extra):
        data = {"result": result}
        data.update(extra)
        minigame_results[game_id] = data
        try:
            emit("minigame_completed", game_id, result=result)
        except Exception:
            pass
        return result

    def minigame_result(game_id, default=None):
        return minigame_results.get(game_id, {}).get("result", default)

    def start_minigame(game_id, **kwargs):
        if not system_enabled("minigames"):
            return complete_minigame(game_id, "disabled")
        data = minigame_defs.get(game_id)
        if not data:
            renpy.notify("Minigame not registered: %s" % game_id)
            return complete_minigame(game_id, "missing")
        req = data.get("requires")
        if req:
            try:
                if not meets_requirements(req):
                    renpy.notify(data.get("locked_message", "You can't do that right now."))
                    return complete_minigame(game_id, "locked")
            except Exception:
                return complete_minigame(game_id, "locked")
        if minigame_skip_mode:
            skip_label = data.get("skip_label")
            if skip_label and renpy.has_label(skip_label):
                renpy.call_in_new_context(skip_label, game_id)
            return complete_minigame(game_id, data.get("skip_result", "skipped"))
        label = data.get("label")
        if label and renpy.has_label(label):
            renpy.call_in_new_context(label, game_id)
            return minigame_result(game_id, "played")
        if data.get("fail_forward", True):
            return complete_minigame(game_id, data.get("skip_result", "skipped"))
        return complete_minigame(game_id, "missing")

    def minigame_validation_issues():
        issues = []
        for game_id, data in (globals().get("minigame_defs", {}) or {}).items():
            if not isinstance(data, dict):
                issues.append("Minigame '{}' should be a dictionary definition.".format(game_id))
                continue
            if data.get("id") and data.get("id") != game_id:
                issues.append("Minigame '{}' has mismatched id '{}'.".format(game_id, data.get("id")))
            for label_key in ("label", "skip_label"):
                label = data.get(label_key)
                if label:
                    try:
                        if not renpy.has_label(label):
                            issues.append("Minigame '{}' {} points to missing label '{}'.".format(game_id, label_key, label))
                    except Exception:
                        pass
            reqs = data.get("requires")
            if reqs:
                try:
                    first_missing_requirement(reqs)
                except Exception:
                    issues.append("Minigame '{}' has invalid requirements '{}'.".format(game_id, reqs))
            if "fail_forward" in data and not isinstance(data.get("fail_forward"), bool):
                issues.append("Minigame '{}' fail_forward should be true/false.".format(game_id))
        return issues


init 5 python:
    minigame(
        "sample_lockpick",
        skip_result="win",
        fail_forward=True,
    )


init 999 python:
    try:
        register_project_tac_validator(minigame_validation_issues)
    except Exception:
        pass
