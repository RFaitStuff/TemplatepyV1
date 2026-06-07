# =============================================================================
# Engine/Notifications.rpy - toast-style side notifications
# -----------------------------------------------------------------------------
# Subscribes to the event bus and turns interesting events into floating
# toasts in the top-right of the screen (HUD shows them). All entry points
# are also exposed manually:
#
#   notify("Found a clue.")
#   notify_stat("alice", "trust", +1)
#   notify_player_stat("Lust", +1, source="alice")
#   notify_quest("New quest:", "Catch up with Alice")
#   notify_item("lost_pen", +1)
#
# Notifications are queued and pop one-at-a-time. Tunables:
#   notify_max_visible    - how many can stack at once
#   notify_lifetime       - seconds visible before auto-dismiss
#   notify_enabled        - kill switch (set False to disable all toasts)
#
# Set notify_enabled = False at any time (e.g. in cutscenes) to silence the
# stream. Restore True when done.
# =============================================================================


default _notify_queue   = []     # pending notifications waiting for a slot
default _notify_active  = []     # [{id, kind, text, icon, born}, ...] visible
default _notify_counter = 0


define notify_max_visible = 4
define notify_lifetime    = 4.0     # seconds (per spec)
define notify_enabled     = True


init -50 python:

    def _now_runtime():
        # Wall-clock-ish progress timer. Monotonically increasing across
        # rollback (rollback rewinds STATE but not the runtime clock), so
        # toasts saved into a rolled-back state will appear stale and
        # immediately expire on the next periodic tick. Exactly the
        # behavior the player expects.
        try:
            return renpy.get_game_runtime()
        except Exception:
            import time as _t
            return _t.time()

    def _next_notify_id():
        store._notify_counter += 1
        return store._notify_counter

    def _restart_interaction_quiet():
        try:
            renpy.restart_interaction()
        except Exception:
            pass

    def _spawn_notification(kind, text, icon=None, color=None):
        if not notify_enabled:
            return
        try:
            if not system_enabled("notifications"):
                return
        except Exception:
            pass
        n = {
            "id":    _next_notify_id(),
            "kind":  kind,
            "text":  text,
            "icon":  icon,
            "color": color,
            "born":  _now_runtime(),
        }
        if len(_notify_active) < notify_max_visible:
            _notify_active.append(n)
        else:
            _notify_queue.append(n)
        _restart_interaction_quiet()

    def _expire_notification(nid):
        for i, n in enumerate(_notify_active):
            if n["id"] == nid:
                _notify_active.pop(i)
                break
        if _notify_queue and len(_notify_active) < notify_max_visible:
            _notify_active.append(_notify_queue.pop(0))
            _notify_active[-1]["born"] = _now_runtime()
        _restart_interaction_quiet()

    def _tick_notifications():
        # Periodic callback. Sweeps for any toast whose age exceeds
        # notify_lifetime and removes it. Also re-stamps freshly-promoted
        # entries from the queue so they don't inherit a stale birth time.
        if not _notify_active and not _notify_queue:
            return
        now = _now_runtime()
        expired = []
        for n in list(_notify_active):
            born = n.get("born")
            if born is None:
                n["born"] = now
                continue
            if now - born >= notify_lifetime:
                expired.append(n["id"])
        for nid in expired:
            _expire_notification(nid)

    # Register the periodic sweeper. config.periodic_callback fires roughly
    # every 0.05-0.1s during interactions so 4s expiry is precise enough.
    if _tick_notifications not in config.periodic_callbacks:
        config.periodic_callbacks.append(_tick_notifications)

    # Also sweep right after a rollback - any saved-in-the-past toasts
    # should clear immediately rather than wait for the next tick.
    def _notify_after_rollback():
        _tick_notifications()
    if _notify_after_rollback not in config.after_load_callbacks:
        config.after_load_callbacks.append(_notify_after_rollback)

    # ------------------------------------------------------------------
    # Public helpers - call from anywhere
    # ------------------------------------------------------------------
    def notify(text, icon=None, color=None):
        _spawn_notification("info", text, icon=icon, color=color)

    def notify_stat(char, stat, delta):
        if delta == 0:
            return
        sign = "+" if delta > 0 else ""
        col  = "#aef0ae" if delta > 0 else "#ff8a8a"
        _spawn_notification(
            "stat",
            "%s %s%d %s" % (char.title(), sign, delta, stat),
            color=col,
        )

    def notify_player_stat(stat, delta, source=None):
        if delta == 0:
            return
        sign = "+" if delta > 0 else ""
        col  = "#aef0ae" if delta > 0 else "#ff8a8a"
        msg  = "%s%d %s" % (sign, delta, stat)
        if source:
            msg += "  (%s)" % source
        _spawn_notification("stat", msg, color=col)

    def notify_quest(prefix, title):
        _spawn_notification(
            "quest",
            "%s %s" % (prefix, title),
            color="#ffd27a",
        )

    def notify_item(item_id, delta):
        if delta == 0:
            return
        try:
            name = item_name(item_id)
        except NameError:
            name = item_id
        sign = "+" if delta > 0 else ""
        _spawn_notification(
            "item",
            "%s%d  %s" % (sign, delta, name),
            color=("#aef0ae" if delta > 0 else "#cccccc"),
        )

    def notify_clear():
        _notify_active[:] = []
        _notify_queue[:]  = []
        _restart_interaction_quiet()


# =============================================================================
# Auto-wiring: subscribe to the event bus so other systems don't have to call
# notify_* manually. Disable any of these by toggling the flags below.
# =============================================================================
define autonotify_stats   = True
define autonotify_moods   = True
define autonotify_quests  = True
define autonotify_items   = True


init -49 python:

    def _autonotify_stat_changed(char, stat, delta, new_value, **kwargs):
        if not autonotify_stats or delta == 0:
            return
        if stat == "moods":
            return  # mood deltas have their own event
        if char == "player":
            src = kwargs.get("source") or store._last_speaker
            notify_player_stat(stat, delta, source=src)
        else:
            notify_stat(char, stat, delta)

    def _autonotify_mood_changed(char, mood_name, delta, new_value, **kwargs):
        if not autonotify_moods or delta == 0:
            return
        sign = "+" if delta > 0 else ""
        col = "#9fd7ff" if delta > 0 else "#ffb7b7"
        _spawn_notification(
            "mood",
            "%s %s%d %s" % (char.title(), sign, delta, mood_name),
            color=col,
        )

    def _autonotify_item_added(item_id, count, **kw):
        if autonotify_items:
            notify_item(item_id, count)

    def _autonotify_item_removed(item_id, count, **kw):
        if autonotify_items:
            notify_item(item_id, -count)

    def _autonotify_quest(qid, prefix, objective_id=None):
        if not autonotify_quests:
            return
        try:
            q = quest_log.get(qid)
            if not q:
                return
            if objective_id is None:
                notify_quest(prefix, q.title)
                return
            o = q.get(objective_id)
            if o:
                notify_quest(prefix, q.title + " - " + o.text)
        except Exception:
            pass

    def _autonotify_quest_started(qid, **kw):
        _autonotify_quest(qid, "New quest:")

    def _autonotify_quest_completed(qid, **kw):
        _autonotify_quest(qid, "Quest complete:")

    def _autonotify_quest_progress(qid, oid, **kw):
        _autonotify_quest(qid, "Updated:", oid)

    on("stat_changed",     _autonotify_stat_changed)
    on("mood_changed",     _autonotify_mood_changed)
    on("item_added",       _autonotify_item_added)
    on("item_removed",     _autonotify_item_removed)
    on("quest_started",    _autonotify_quest_started)
    on("quest_completed",  _autonotify_quest_completed)
    on("quest_progress",   _autonotify_quest_progress)
