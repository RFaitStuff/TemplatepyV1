# =============================================================================
# Quest runtime
# -----------------------------------------------------------------------------
# Quest definitions live in init-time `quest_defs` and save progress lives in
# `quest_states`. `quest_log` is rebuilt lazily as a compatibility view for
# existing HUD/debug screens.
#
# IMPORTANT:
# Quest definition files run during init. Ren'Py `default` variables such as
# quest_states do not exist yet at that point, so define_quest() must only
# register immutable definition data. Runtime Quest objects are created later,
# when the game actually asks for quest information.
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
            discoverable=False,
            unlock_when=None,
            start_when=None,
            show_when_inactive=False,
            track_on_start=False,
            track_next=None,
            clear_track_on_complete=True,
            guide_precision="exact",
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
            self.discoverable = bool(discoverable)
            self.unlock_when = unlock_when
            self.start_when = start_when
            self.show_when_inactive = bool(show_when_inactive)
            self.track_on_start = track_on_start
            self.track_next = track_next
            self.clear_track_on_complete = bool(clear_track_on_complete)
            self.guide_precision = guide_precision or "exact"
            self.objectives = []

            state = _quest_state(qid)
            done_ids = set(state.get("done", []))

            for o in (objectives or []):
                if isinstance(o, Objective):
                    objective = Objective(
                        o.id,
                        o.text,
                        o.flag,
                        o.optional,
                        o.target,
                        o.id in done_ids or o.done,
                        qid=qid,
                    )
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
                    objective = Objective(
                        str(o),
                        str(o),
                        done=str(o) in done_ids,
                        qid=qid,
                    )

                self.objectives.append(objective)

        @property
        def state(self):
            return _quest_state(self.id).get("state", "inactive")

        @state.setter
        def state(self, value):
            _quest_state(self.id)["state"] = value

        def _persist_done(self):
            _quest_state(self.id)["done"] = sorted(
                o.id for o in self.objectives if o.done
            )

        def start(self):
            if not system_enabled("quests"):
                return None

            if not self.is_unlocked:
                return None

            self.discover()

            if self.state == "inactive":
                self.state = "active"
                _emit_quest_event("quest_started", self.id)
                if self.track_on_start == "force" or (self.track_on_start and not tracked_quest_id):
                    set_tracked_quest(self.id)

        def complete(self):
            if not system_enabled("quests"):
                return None

            if self.state != "completed":
                self.state = "completed"
                self.discover()
                if tracked_quest_id == self.id:
                    if self.track_next:
                        next_q = quest(self.track_next)
                        if next_q and next_q.state == "inactive":
                            next_q.start()
                        set_tracked_quest(self.track_next)
                    elif self.clear_track_on_complete:
                        clear_tracked_quest()
                _emit_quest_event("quest_completed", self.id)

        def fail(self):
            if not system_enabled("quests"):
                return None

            if self.state != "failed":
                self.state = "failed"
                self.discover()
                if tracked_quest_id == self.id and self.clear_track_on_complete:
                    clear_tracked_quest()
                _emit_quest_event("quest_failed", self.id)

        def discover(self):
            if self.unlock_when is not None:
                try:
                    if not meets_requirements(self.unlock_when):
                        return None
                except Exception:
                    return None
            state = _quest_state(self.id)
            state["discovered"] = True
            return None

        @property
        def is_discovered(self):
            return bool(_quest_state(self.id).get("discovered", False))

        @property
        def visible_in_log(self):
            return self.show_when_inactive or self.is_discovered or self.state in ("active", "completed", "failed")

        @property
        def is_unlocked(self):
            if self.unlock_when is None:
                return True
            try:
                return meets_requirements(self.unlock_when)
            except Exception:
                return False

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


# Saveable runtime state. These variables are not available while init-time
# quest registration is running, which is why define_quest() never touches them.
default quest_states = {}
default tracked_quest_id = None


init python:

    def _quest_state(qid):
        """Return/create the save-state record for a quest."""
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
        """Rebuild runtime Quest wrappers from definitions + save state."""
        quest_log.clear()

        for qid in sorted(quest_defs.keys()):
            quest_object = _make_quest_from_def(qid)
            if quest_object is not None:
                quest_log[qid] = quest_object

        return quest_log

    def ensure_quest_log():
        """
        Ensure the runtime compatibility view matches the registered definitions.

        This is deliberately lazy so quest definitions can be registered during
        init without reading Ren'Py `default` variables before they exist.
        """
        if len(quest_log) != len(quest_defs):
            return rebuild_quest_log()

        for qid in quest_defs:
            if qid not in quest_log:
                return rebuild_quest_log()

        return quest_log

    if rebuild_quest_log not in config.after_load_callbacks:
        config.after_load_callbacks.append(rebuild_quest_log)

    def define_quest(qid, **kwargs):
        """
        Register immutable quest definition data.

        This function is called from init-time Game/Data quest files. It must not
        access quest_states or construct Quest objects because Ren'Py defaults do
        not exist yet during init.
        """
        quest_defs[qid] = dict(kwargs)
        return quest_defs[qid]

    def step(oid, text, flag=None, optional=False, target=None, done=False, **kwargs):
        """Writer-friendly objective builder."""
        data = {
            "oid": oid,
            "text": text,
            "flag": flag,
            "optional": optional,
            "target": target,
            "done": done,
        }
        if "guide" in kwargs and target is None:
            data["target"] = _quest_guide_target(kwargs.get("guide"), kwargs.get("precision"))
        if "needs" in kwargs:
            data.setdefault("target", {})
            data["target"]["needs"] = kwargs.get("needs")
        if "needs_item" in kwargs:
            data.setdefault("target", {})
            data["target"]["item"] = kwargs.get("needs_item")
        data.update({k: v for k, v in kwargs.items() if k not in ("guide", "precision", "needs", "needs_item")})
        return data

    def guide_target(target, icon=None, precision=None, **kwargs):
        """Short target helper for quest guide markers."""
        data = _quest_guide_target(target, precision)
        if data is None:
            data = {}
        if icon is not None:
            data["icon"] = icon
        data.update(kwargs)
        return data

    def _quest_guide_target(guide, precision=None):
        if guide is None:
            return None
        if isinstance(guide, (list, tuple)) and not isinstance(guide, str):
            targets = []
            for entry in guide:
                normalized = _quest_guide_target(entry, precision)
                if normalized:
                    targets.append(normalized)
            return {"targets": targets}
        if isinstance(guide, dict):
            target = dict(guide)
        else:
            target = {}
            for part in _req_as_list(guide):
                text = str(part)
                key, sep, value = text.partition(":")
                if sep:
                    key = key.strip()
                    value = value.strip()
                    if key in ("character", "npc"):
                        target["npc"] = value
                    elif key == "characters":
                        target["characters"] = [v.strip() for v in value.split("|") if v.strip()]
                    elif key == "item":
                        target["item"] = value
                    elif key == "object":
                        target["object"] = value
                    elif key == "location":
                        target["location"] = value
                    elif key == "area":
                        target["area"] = value
                    else:
                        target[key] = value
        if precision:
            target["guide_precision"] = precision
        return target

    def create_quest(qid, **kwargs):
        """Short authoring wrapper over define_quest()."""
        if "name" in kwargs and "title" not in kwargs:
            kwargs["title"] = kwargs.pop("name")
        if "desc" in kwargs and "description" not in kwargs:
            kwargs["description"] = kwargs.pop("desc")
        if "discover" in kwargs and "discoverable" not in kwargs:
            kwargs["discoverable"] = kwargs.pop("discover")
        if "steps" in kwargs and "objectives" not in kwargs:
            kwargs["objectives"] = kwargs.pop("steps")
        if "guide" in kwargs and "target" not in kwargs:
            kwargs["target"] = _quest_guide_target(kwargs.pop("guide"), kwargs.get("guide_precision"))
        starts_after = kwargs.pop("starts_after", None)
        if starts_after is not None and "unlock_when" not in kwargs:
            kwargs["unlock_when"] = starts_after
        return define_quest(qid, **kwargs)

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
        ensure_quest_log()
        return quest_log.get(qid)

    def discover_quest(qid, start=False, track=False):
        q = quest(qid)
        if not q:
            return None
        if not q.is_unlocked:
            return None
        q.discover()
        if start:
            q.start()
        if track:
            set_tracked_quest(qid)
        return q

    def start_quest(qid):
        q = quest(qid)
        if q:
            q.start()

    def progress_quest(qid, oid):
        q = quest(qid)
        if q:
            q.progress(oid)

    def quest_step_done(qid, oid=None):
        q = quest(qid)
        if not q:
            return None
        if oid is None:
            pending = [o for o in q.objectives if not o.done and not o.optional]
            if len(pending) != 1:
                return None
            oid = pending[0].id
        q.progress(oid)
        return q

    def refresh_quest_unlocks():
        if not system_enabled("quests"):
            return None
        ensure_quest_log()
        for q in quest_log.values():
            if q.state != "inactive":
                continue
            if q.unlock_when is not None and q.is_unlocked:
                q.discover()
            if q.start_when is not None:
                try:
                    if meets_requirements(q.start_when):
                        q.start()
                except Exception:
                    pass
        return None

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
        ensure_quest_log()
        return [q for q in quest_log.values() if q.category == category]

    def quests_for(character):
        ensure_quest_log()
        return [q for q in quest_log.values() if q.character == character]

    def active_quests():
        if not system_enabled("quests"):
            return []

        ensure_quest_log()
        return [q for q in quest_log.values() if q.is_active]

    def tracked_quest():
        ensure_quest_log()
        qid = tracked_quest_id

        if qid and qid in quest_log:
            q = quest_log[qid]
            if q.is_active:
                return q

        return None

    def set_tracked_quest(qid):
        global tracked_quest_id
        ensure_quest_log()

        if qid in quest_log and quest_log[qid].is_active:
            tracked_quest_id = qid
            store.hud_hide_objective = False

        return None

    def toggle_tracked_quest(qid):
        global tracked_quest_id
        ensure_quest_log()

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
        return None

    def completed_quests():
        ensure_quest_log()
        return [q for q in quest_log.values() if q.visible_in_log and q.is_completed]

    def visible_quests(include_completed=True):
        ensure_quest_log()
        out = [q for q in quest_log.values() if q.visible_in_log]
        if not include_completed:
            out = [q for q in out if not q.is_completed and not q.is_failed]
        order = {"main": 0, "side": 1}
        out.sort(key=lambda q: (q.is_completed, q.is_failed, order.get(q.category, 5), q.id))
        return out

    def visible_active_quests():
        return [q for q in visible_quests(include_completed=False) if q.is_active]

    def visible_completed_quests():
        return [q for q in visible_quests(include_completed=True) if q.is_completed or q.is_failed]

    def undiscovered_quests():
        ensure_quest_log()
        return [
            q for q in quest_log.values()
            if q.discoverable and q.is_unlocked and not q.visible_in_log and q.state == "inactive"
        ]

    def has_undiscovered_quests():
        return bool(undiscovered_quests())

    def quest_tree():
        ensure_quest_log()
        tree = {}

        for q in quest_log.values():
            if not q.visible_in_log:
                continue
            tree.setdefault(q.category, []).append(q)

        return tree

    def _quests_on_flag(flag):
        if not system_enabled("quests"):
            return None

        ensure_quest_log()

        refresh_quest_unlocks()

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

    def quest_validation_issues():
        issues = []
        valid_precision = set(("exact", "location", "loc", "area", "region", "characters", "none", "off", "hidden"))

        for qid, qdef in quest_defs.items():
            if not qdef.get("title"):
                issues.append("Quest '{}' has no title.".format(qid))
            if qdef.get("character") and qdef.get("character") not in (globals().get("character_stats", {}) or {}):
                issues.append("Quest '{}' references missing character '{}'.".format(qid, qdef.get("character")))
            if qdef.get("track_next") and qdef.get("track_next") not in quest_defs:
                issues.append("Quest '{}' track_next points to missing quest '{}'.".format(qid, qdef.get("track_next")))
            precision = str(qdef.get("guide_precision", "exact")).lower()
            if precision not in valid_precision:
                issues.append("Quest '{}' has unknown guide_precision '{}'.".format(qid, precision))
            for key in ("unlock_when", "start_when"):
                requirement = qdef.get(key)
                if requirement:
                    try:
                        first_missing_requirement(requirement)
                    except Exception:
                        issues.append("Quest '{}' has invalid requirement '{}'.".format(qid, key))
            _quest_validate_target(qid, "target", qdef.get("target"), issues)

            objective_ids = set()
            for objective in qdef.get("objectives", []) or []:
                if not isinstance(objective, dict):
                    continue
                oid = objective.get("oid") or objective.get("id")
                if not oid:
                    issues.append("Quest '{}' has an objective with no id.".format(qid))
                    continue
                if oid in objective_ids:
                    issues.append("Quest '{}' has duplicate objective id '{}'.".format(qid, oid))
                objective_ids.add(oid)
                if not objective.get("text"):
                    issues.append("Quest '{}.{}' has no objective text.".format(qid, oid))
                for key in ("requires", "unlock_when"):
                    requirement = objective.get(key)
                    if requirement:
                        try:
                            first_missing_requirement(requirement)
                        except Exception:
                            issues.append("Quest '{}.{}' has invalid requirement '{}'.".format(qid, oid, key))
                _quest_validate_target(qid, "objective '{}'".format(oid), objective.get("target"), issues)
        return issues

    def _quest_validate_target(qid, context, target, issues):
        if not target:
            return
        if not isinstance(target, dict):
            issues.append("Quest '{}' {} target should be a dict.".format(qid, context))
            return
        if target.get("targets"):
            for entry in target.get("targets") or []:
                merged = dict(target)
                merged.pop("targets", None)
                if isinstance(entry, dict):
                    merged.update(entry)
                _quest_validate_target(qid, context, merged, issues)
            return
        if target.get("location") and target.get("location") not in (globals().get("locations", {}) or {}):
            issues.append("Quest '{}' {} references missing location '{}'.".format(qid, context, target.get("location")))
        if target.get("area") and target.get("area") not in (globals().get("areas", {}) or {}):
            issues.append("Quest '{}' {} references missing area '{}'.".format(qid, context, target.get("area")))
        for cid in [target.get("npc")] + list(target.get("characters") or []):
            if cid and cid not in (globals().get("character_stats", {}) or {}):
                issues.append("Quest '{}' {} references missing character '{}'.".format(qid, context, cid))
        if target.get("item") and target.get("item") not in (globals().get("item_defs", {}) or {}):
            issues.append("Quest '{}' {} references missing item '{}'.".format(qid, context, target.get("item")))
        if target.get("object") and target.get("object") not in (globals().get("interactable_defs", {}) or {}):
            issues.append("Quest '{}' {} references missing object '{}'.".format(qid, context, target.get("object")))
        label = target.get("label")
        if label and not renpy.has_label(label):
            issues.append("Quest '{}' {} points to missing label '{}'.".format(qid, context, label))


init 999 python:
    try:
        register_project_tac_validator(quest_validation_issues)
    except Exception:
        pass
