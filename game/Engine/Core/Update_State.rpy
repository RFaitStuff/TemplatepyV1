# =============================================================================
# Central Update-State Pass
# -----------------------------------------------------------------------------
# Lightweight coordinator for systems that need to refresh after state changes.
# Systems can subscribe to `on("update_state", handler)` instead of manually
# poking each other after every flag/item/quest/time/stat change.
# =============================================================================

default _update_state_reason = None

init -80 python:

    _update_state_running = False

    def request_update_state(reason=None, **kwargs):
        global _update_state_running
        store._update_state_reason = reason
        if _update_state_running:
            return None
        _update_state_running = True
        try:
            emit("update_state", reason=reason, **kwargs)
        except NameError:
            pass
        finally:
            _update_state_running = False
        return None

    def _auto_request_update_state(reason):
        def _handler(*args, **kwargs):
            request_update_state(reason)
        return _handler

    on("flag_set", _auto_request_update_state("flag"))
    on("item_added", _auto_request_update_state("inventory"))
    on("item_removed", _auto_request_update_state("inventory"))
    on("quest_started", _auto_request_update_state("quest"))
    on("quest_progress", _auto_request_update_state("quest"))
    on("quest_completed", _auto_request_update_state("quest"))
    on("quest_failed", _auto_request_update_state("quest"))
    on("hour_advanced", _auto_request_update_state("time"))
    on("day_advanced", _auto_request_update_state("time"))
    on("stat_changed", _auto_request_update_state("stat"))
    on("mood_changed", _auto_request_update_state("mood"))
