# =============================================================================
# Quest Manager
# -----------------------------------------------------------------------------
# Quests are organized in a tree:
#     main / side / character_<id> / misc
# Each quest's objectives can be flag-driven: when you call `set_flag("X")`,
# any objective listening for "X" auto-completes; when all required objectives
# are done, the quest auto-completes.
#
# So your story code just sets flags - the manager handles the rest.
# =============================================================================

init -5 python:

    def _emit_quest_event(event_name, *args):
        try:
            emit(event_name, *args)
        except NameError:
            pass

    class Objective(object):
        def __init__(self, oid, text, flag=None, optional=False, target=None):
            self.id = oid
            self.text = text
            self.flag = flag        # if set, completes when this story flag is set
            self.optional = optional
            self.done = False
            # Optional spatial target hint - e.g. {"npc": "alice", "location": "art_room"}.
            # Read by Engine/Quest_Guide.rpy to draw automatic markers.
            self.target = target or None

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
            self.category = category          # "main" | "side" | "misc" | "character_<id>"
            self.character = character        # optional character id
            self.start_flag = start_flag      # auto-start when this flag is set
            self.complete_flag = complete_flag  # auto-complete when set
            self.fail_flag = fail_flag        # auto-fail when set
            self.target = target              # quest-level guide hint
            self.state = "inactive"
            self.objectives = []
            for o in (objectives or []):
                if isinstance(o, Objective):
                    self.objectives.append(o)
                elif isinstance(o, dict):
                    self.objectives.append(Objective(**o))
                elif isinstance(o, tuple):
                    self.objectives.append(Objective(*o))
                else:
                    self.objectives.append(Objective(str(o), str(o)))

        def start(self):
            if self.state == "inactive":
                self.state = "active"
                _emit_quest_event("quest_started", self.id)

        def complete(self):
            if self.state != "completed":
                self.state = "completed"
                _emit_quest_event("quest_completed", self.id)

        def fail(self):
            if self.state != "failed":
                self.state = "failed"
                _emit_quest_event("quest_failed", self.id)

        def get(self, oid):
            for o in self.objectives:
                if o.id == oid:
                    return o
            return None

        def progress(self, oid):
            o = self.get(oid)
            if o and not o.done:
                o.done = True
                _emit_quest_event("quest_progress", self.id, oid)
            if self.state == "active" and self.all_required_done():
                self.complete()

        def all_required_done(self):
            return all(o.done for o in self.objectives if not o.optional)

        @property
        def is_active(self):    return self.state == "active"
        @property
        def is_completed(self): return self.state == "completed"
        @property
        def is_failed(self):    return self.state == "failed"


# Master quest registry: qid -> Quest
default quest_log = {}
default tracked_quest_id = None


init python:

    def define_quest(qid, **kwargs):
        """Register a quest. Safe to call multiple times - won't overwrite state."""
        if qid not in quest_log:
            quest_log[qid] = Quest(qid, **kwargs)
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

    def start_quest(qid):
        if qid in quest_log:
            quest_log[qid].start()

    def progress_quest(qid, oid):
        if qid in quest_log:
            quest_log[qid].progress(oid)

    def complete_quest(qid):
        if qid in quest_log:
            quest_log[qid].complete()

    def fail_quest(qid):
        if qid in quest_log:
            quest_log[qid].fail()

    def is_quest_active(qid):
        return qid in quest_log and quest_log[qid].is_active

    def is_quest_completed(qid):
        return qid in quest_log and quest_log[qid].is_completed

    def quests_in(category):
        return [q for q in quest_log.values() if q.category == category]

    def quests_for(character):
        return [q for q in quest_log.values() if q.character == character]

    def active_quests():
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
        # NOTE: returns None on purpose. Returning True/False would close any
        # `call screen ...` running underneath (action results propagate to
        # the current interaction), which used to teleport the player by
        # falling through to nav_left when the quest log was opened on top of
        # the explore loop.
        global tracked_quest_id
        if qid in quest_log and quest_log[qid].is_active:
            tracked_quest_id = qid
        return None

    def toggle_tracked_quest(qid):
        # Click-to-track helper: if already tracked, untrack; else track.
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
        """Return {category: [quest, ...]} for UI display."""
        tree = {}
        for q in quest_log.values():
            tree.setdefault(q.category, []).append(q)
        return tree

    def _quests_on_flag(flag):
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


