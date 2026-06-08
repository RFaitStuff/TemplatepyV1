# =============================================================================
# Engine/Events.rpy - lightweight event bus
# -----------------------------------------------------------------------------
# Decouples systems. Anywhere can `emit("foo", ...)` and any other system can
# `on("foo", handler)` to react. Handlers are init-time only (functions are
# not picklable so they don't belong in `default` storage).
#
# Built-in events fired by the rest of the engine:
#   "stat_changed"    (char, stat, delta, new_value)
#   "mood_changed"    (char, mood, intensity)
#   "flag_set"        (flag)
#   "item_added"      (item_id, count)
#   "item_removed"    (item_id, count)
#   "quest_started"   (qid)
#   "quest_progress"  (qid, oid)
#   "quest_completed" (qid)
#   "quest_failed"    (qid)
#   "hour_advanced"   (hours)
#   "day_advanced"    (day)
#   "location_entered"(loc_id)
#   "location_left"   (loc_id)
#   "menu_shown"      (side)
#   "menu_hidden"     ()
#   "interactable_clicked" (iid)
#
# Feature flag: set _events_enabled = False at init time to silence the bus
# (handlers won't be called). Useful while debugging.
# =============================================================================


init -100 python:

    _events_enabled = True
    _event_handlers = {}        # event_name -> [ (priority, fn), ... ]

    def on(event_name, fn=None, priority=0):
        # Decorator OR direct call:
        #   on("foo", my_handler)
        #   @on("foo", priority=10)
        #   def my_handler(...):
        def _register(f):
            handlers = _event_handlers.setdefault(event_name, [])
            if not any(h[1] is f for h in handlers):
                handlers.append((priority, f))
                handlers.sort(key=lambda t: -t[0])
            return f
        if fn is not None:
            return _register(fn)
        return _register

    def off(event_name, fn):
        if event_name in _event_handlers:
            _event_handlers[event_name] = [
                h for h in _event_handlers[event_name] if h[1] is not fn
            ]

    def emit(event_name, *args, **kwargs):
        # Fire all handlers in priority order. Handlers can return values;
        # we ignore them by default (call emit_collect to gather them).
        if not _events_enabled:
            return
        for _, fn in list(_event_handlers.get(event_name, [])):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                renpy.log("event handler %r for %r raised: %r" % (fn, event_name, e))

    def emit_collect(event_name, *args, **kwargs):
        # Like emit() but returns the list of non-None handler return values.
        if not _events_enabled:
            return []
        out = []
        for _, fn in list(_event_handlers.get(event_name, [])):
            try:
                rv = fn(*args, **kwargs)
                if rv is not None:
                    out.append(rv)
            except Exception as e:
                renpy.log("event handler %r for %r raised: %r" % (fn, event_name, e))
        return out

    def clear_event(event_name=None):
        if event_name is None:
            _event_handlers.clear()
        else:
            _event_handlers.pop(event_name, None)
