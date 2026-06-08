# =============================================================================
# Quest runtime
# -----------------------------------------------------------------------------
# Quest definitions live in init-time `quest_defs` and save progress lives in
# `quest_states`. `quest_log` is rebuilt as a compatibility view for existing
# HUD/debug screens.
# =============================================================================

init -5 python:

    quest_defs = {}
    quest_log = {}

    def _emit_quest_event(event_name, *args):
        try:
            emit(event_name, *args)
        except NameError:
            pass

    class Objective(object):
        def __init__(self, oid, text, flag=None, optional=False, target=None, done=False, qid=None):
            self.qid = qid
            self.id = oid
            self.text = text
            self.flag = flag
            self.optional = optional
            self.target = target or None
            self._done = bool(done)
            if done and qid:
                done_ids = set(_quest_state(qid).get("done", []))
                done_ids.add(oid)
                _quest_state(qid)["done"] = sorted(done_ids)

        @property
        def done(self):
            if self.qid:
                return self.id in set(_quest_state(self.qid).get("done", []))
            return self._done

        @done.setter
        def done(self, value):
            self._done = bool(value)
            if not self.qid:
                return
            state = _quest_state(self.qid)
            done_ids = set(state.get("done", []))
            if value:
                done_ids.add(self.id)
            else:
                done_ids.discard(self.id)
            state["done"] = sorted(done_ids)

    class Quest(object):
        def __init__(
            self,
            qid,
            title,
            description="",
            category="misc",
            character=None,
            start_flag=None,
            complete_flag=None,
            fail_flag=None,
            objectives=None,
            target=None,
        ):
            self.id = qid
            self.title = title
            self.description = description
            self.category = category
            self.character = character
            self.start_flag = start_flag
            self.complete_flag = complete_flag
            self.fail_flag = fail_flag
            self.target = target
            self.objectives = []

            state = _quest_state(qid)
            done_ids = set(state.get("done", []))
            for o in (objectives or []):
                if isinstance(o, Objective):
                    objective = Objective(o.id, o.text, o.flag, o.optional, o.target, o.id in done_ids or o.done, qid=qid)
                elif isinstance(o, dict):
                    data = dict(o)
                    oid = data.get("oid") or data.get("id")
                    data["oid"] = oid
                    data.pop("id", None)
                    data["qid"] = qid
                    objective = Objective(**data)
                    objective.done = objective.id in done_ids
                elif isinstance(o, tuple):
                    objective = Objective(*o, qid=qid)
                    objective.done = objective.id in done_ids
                else:
                    objective = Objective(str(o), str(o), done=str(o) in done_ids, qid=qid)
                self.objectives.append(objective)

        @property
        def state(self):
            return _quest_state(self.id).get("state", "inactive")

        @state.setter
        def state(self, value):
            _quest_state(self.id)["state"] = value

        def _persist_done(self):
            _quest_state(self.id)["done"] = sorted(o.id for o in self.objectives if o.done)

        def start(self):
            if not system_enabled("quests"):
                return None
            if self.state == "inactive":
                self.state = "active"
                _emit_quest_event("quest_started", self.id)

        def complete(self):
            if not system_enabled("quests"):
                return None
            if self.state != "completed":
                self.state = "completed"
                _emit_quest_event("quest_completed", self.id)

        def fail(self):
            if not system_enabled("quests"):
                return None
            if self.state != "failed":
                self.state = "failed"
                _emit_quest_event("quest_failed", self.id)

        def get(self, oid):
            for o in self.objectives:
                if o.id == oid:
                    return o
            return None

        def progress(self, oid):
            if not system_enabled("quests"):
                return None
            o = self.get(oid)
            if o and not o.done:
                o.done = True
                self._persist_done()
                _emit_quest_event("quest_progress", self.id, oid)
            if self.state == "active" and self.all_required_done():
                self.complete()

        def all_required_done(self):
            return all(o.done for o in self.objectives if not o.optional)

        @property
        def is_active(self):
            return self.state == "active"

        @property
        def is_completed(self):
            return self.state == "completed"

        @property
        def is_failed(self):
            return self.state == "failed"


default quest_states = {}
default tracked_quest_id = None


init python:

    def _quest_state(qid):
        state = quest_states.setdefault(qid, {})
        state.setdefault("state", "inactive")
        state.setdefault("done", [])
        return state

    def _make_quest_from_def(qid):
        data = dict(quest_defs.get(qid, {}))
        if not data:
            return None
        return Quest(qid, **data)

    def rebuild_quest_log():
        quest_log.clear()
        for qid in sorted(quest_defs.keys()):
            quest_log[qid] = _make_quest_from_def(qid)
        return quest_log

    if rebuild_quest_log not in config.after_load_callbacks:
        config.after_load_callbacks.append(rebuild_quest_log)

    def define_quest(qid, **kwargs):
        """Register immutable quest data and rebuild the runtime compatibility view."""
        quest_defs[qid] = dict(kwargs)
        _quest_state(qid)
        quest_log[qid] = _make_quest_from_def(qid)
        return quest_log[qid]

    def main_quest(qid, **kwargs):
        kwargs.setdefault("category", "main")
        return define_quest(qid, **kwargs)

    def side_quest(qid, **kwargs):
        kwargs.setdefault("category", "side")
        return define_quest(qid, **kwargs)

    def char_quest(qid, character, **kwargs):
        kwargs.setdefault("category", "character_" + character)
        kwargs.setdefault("character", character)
        return define_quest(qid, **kwargs)

    def quest(qid):
        return quest_log.get(qid) or _make_quest_from_def(qid)

    def start_quest(qid):
        q = quest(qid)
        if q:
            q.start()

    def progress_quest(qid, oid):
        q = quest(qid)
        if q:
            q.progress(oid)

    def complete_quest(qid):
        q = quest(qid)
        if q:
            q.complete()

    def fail_quest(qid):
        q = quest(qid)
        if q:
            q.fail()

    def is_quest_active(qid):
        q = quest(qid)
        return bool(q and q.is_active)

    def is_quest_completed(qid):
        q = quest(qid)
        return bool(q and q.is_completed)

    def quests_in(category):
        return [q for q in quest_log.values() if q.category == category]

    def quests_for(character):
        return [q for q in quest_log.values() if q.character == character]

    def active_quests():
        if not system_enabled("quests"):
            return []
        return [q for q in quest_log.values() if q.is_active]

    def tracked_quest():
        qid = tracked_quest_id
        if qid and qid in quest_log:
            q = quest_log[qid]
            if q.is_active:
                return q
        active = active_quests()
        if active:
            order = {"main": 0, "side": 1}
            active.sort(key=lambda q: (order.get(q.category, 5), q.id))
            return active[0]
        return None

    def set_tracked_quest(qid):
        global tracked_quest_id
        if qid in quest_log and quest_log[qid].is_active:
            tracked_quest_id = qid
        return None

    def toggle_tracked_quest(qid):
        global tracked_quest_id
        if tracked_quest_id == qid:
            tracked_quest_id = None
        elif qid in quest_log and quest_log[qid].is_active:
            tracked_quest_id = qid
        return None

    def toggle_tracked_quest_pin():
        global tracked_quest_id
        if not tracked_quest_id:
            return None
        try:
            store.hud_hide_objective = not bool(store.hud_hide_objective)
        except Exception:
            pass
        return None

    def clear_tracked_quest():
        global tracked_quest_id
        tracked_quest_id = None

    def completed_quests():
        return [q for q in quest_log.values() if q.is_completed]

    def quest_tree():
        tree = {}
        for q in quest_log.values():
            tree.setdefault(q.category, []).append(q)
        return tree

    def _quests_on_flag(flag):
        if not system_enabled("quests"):
            return None
        for q in quest_log.values():
            if q.start_flag == flag:
                q.start()
            if q.fail_flag == flag:
                q.fail()
            for o in q.objectives:
                if o.flag == flag and not o.done:
                    q.progress(o.id)
            if q.is_active and q.all_required_done():
                q.complete()
            if q.complete_flag == flag:
                q.complete()
