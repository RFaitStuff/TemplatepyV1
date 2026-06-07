# =============================================================================
# Interaction Router
# -----------------------------------------------------------------------------
# One place decides what happens when the player clicks something.
#
# Characters get Talk / Quest / Interact automatically:
#   - Talk uses mixed dialogue pools from Dialogue_Registry.
#   - Quest appears only when an active quest targets the character.
#   - Interact is available unless the active quest target locks it.
#
# Objects and items can still register custom actions.
# =============================================================================


init -90 python:
    interactable_defs = {}


default seen_actions = set()
default last_actions = {}
default _pending_interactable_id = None
default _pending_action_id = None
default force_action_menu = False


init -89 python:

    def register_interactable(iid, kind="object", title=None, icon=None, actions=None, **extra):
        d = interactable_defs.setdefault(iid, {})
        d["id"] = iid
        d["kind"] = kind
        d["title"] = title or iid.replace("_", " ").title()
        d["icon"] = icon
        d.setdefault("actions", [])
        d.update(extra)
        if actions:
            register_actions(iid, actions)
        if not d["actions"]:
            _seed_default_actions(d)
        if kind == "character":
            _ensure_default_character_actions(d)
        return d

    def register_actions(iid, actions):
        for a in actions:
            register_action(iid, **a)

    def register_action(
        iid,
        id,
        title=None,
        label=None,
        icon=None,
        available_if=None,
        primary=False,
        stamina=None,
        tooltip=None,
        **extra
    ):
        d = interactable_defs.setdefault(
            iid,
            {"id": iid, "kind": "object", "title": iid.replace("_", " ").title(), "actions": []},
        )
        for a in d["actions"]:
            if a.get("id") == id:
                a.update({
                    "title": title or a.get("title") or id.title(),
                    "label": label if label is not None else a.get("label"),
                    "icon": icon if icon is not None else a.get("icon"),
                    "available_if": available_if if available_if is not None else a.get("available_if"),
                    "primary": bool(primary or a.get("primary")),
                    "stamina": stamina if stamina is not None else a.get("stamina"),
                    "tooltip": tooltip if tooltip is not None else a.get("tooltip"),
                })
                a.update(extra)
                return a
        a = {
            "id": id,
            "title": title or id.replace("_", " ").title(),
            "label": label,
            "icon": icon,
            "available_if": available_if,
            "primary": bool(primary),
            "stamina": stamina,
            "tooltip": tooltip,
        }
        a.update(extra)
        d["actions"].append(a)
        return a

    def _seed_default_actions(d):
        kind = d.get("kind")
        iid = d.get("id")
        if kind == "character":
            _ensure_default_character_actions(d)
        elif kind == "exit":
            d["actions"].append({
                "id": "go",
                "title": "Go",
                "label": d.get("label"),
                "primary": True,
                "stamina": d.get("stamina", 10),
            })
        else:
            d["actions"].append({
                "id": "examine",
                "title": "Examine",
                "label": d.get("label") or ("examine_" + iid),
                "primary": True,
            })

    def _looks_like_character(iid):
        try:
            if iid in character_stats:
                return True
        except Exception:
            pass
        try:
            return iid in character_schedules
        except Exception:
            return False

    def _quest_target_matches_iid(t, iid):
        return (
            t.get("npc") == iid or
            t.get("item") == iid or
            t.get("object") == iid
        )

    def current_quest_target_for(iid):
        try:
            for q in active_quests():
                for o in q.objectives:
                    if o.done:
                        continue
                    t = getattr(o, "target", None) or {}
                    if _quest_target_matches_iid(t, iid):
                        return t
                t = getattr(q, "target", None) or {}
                if _quest_target_matches_iid(t, iid):
                    return t
        except Exception:
            pass
        return None

    def _character_has_active_quest(iid):
        return current_quest_target_for(iid) is not None

    def _character_quest_locks_interact(iid):
        t = current_quest_target_for(iid) or {}
        return bool(t.get("locks_interact"))

    def _ensure_default_character_actions(d):
        iid = d["id"]
        existing = set(a.get("id") for a in d.get("actions", []))
        if "talk" not in existing:
            d["actions"].append({
                "id": "talk",
                "title": "Talk",
                "label": "_character_talk_dispatch",
                "primary": True,
                "stamina": 20,
            })
        if "quest" not in existing:
            d["actions"].append({
                "id": "quest",
                "title": "Quest",
                "label": "_character_quest_dispatch",
                "available_if": (lambda iid=iid: _character_has_active_quest(iid)),
                "primary": False,
                "stamina": 20,
            })
        if "interact" not in existing:
            d["actions"].append({
                "id": "interact",
                "title": "Interact",
                "label": "_character_interact_dispatch",
                "available_if": (lambda iid=iid: not _character_quest_locks_interact(iid)),
                "primary": False,
                "stamina": 20,
            })


init python:

    def ensure_interactable(iid):
        d = interactable_defs.get(iid)
        if d:
            if d.get("kind") == "character":
                _ensure_default_character_actions(d)
            return d
        if _looks_like_character(iid):
            return register_interactable(iid, kind="character", title=character_display_name(iid))
        return None

    def get_interactable(iid):
        return ensure_interactable(iid)

    def _safe_available(fn):
        if fn is None:
            return True
        try:
            return bool(fn())
        except Exception:
            return False

    def interactable_actions(iid, only_available=True):
        d = ensure_interactable(iid)
        if not d:
            return []
        out = []
        for a in d.get("actions", []):
            if only_available and not _safe_available(a.get("available_if")):
                continue
            out.append(a)
        return out

    def primary_action(iid):
        actions = interactable_actions(iid, only_available=True)
        if not actions:
            return None
        t = current_quest_target_for(iid)
        if t and t.get("action"):
            for a in actions:
                if a.get("id") == t.get("action"):
                    return a
        for a in actions:
            if a.get("primary"):
                return a
        return actions[0]

    def _find_action(actions, action_id):
        for action in actions:
            if action.get("id") == action_id:
                return action
        return None

    def resolve_interactable_click(iid):
        try:
            if not system_enabled("interactions") or not game_action_allowed("interaction", iid):
                return ("locked", None)
        except Exception:
            pass
        debug_show_all = bool(getattr(store, "debug_all_actions_visible", False))
        actions = interactable_actions(iid, only_available=not debug_show_all)
        if not actions:
            return ("none", None)
        if debug_show_all and _looks_like_character(iid):
            return ("menu", None)
        if force_action_menu:
            return ("menu", None)
        if len(actions) == 1 and actions[0].get("id") == "interact":
            return ("direct", actions[0])
        if _looks_like_character(iid):
            non_interact = [a for a in actions if a.get("id") != "interact"]
            bright_non_interact = [a for a in non_interact if not action_is_darkened(iid, a)]
            interact_action = _find_action(actions, "interact")
            if interact_action and not non_interact:
                return ("direct", interact_action)
            if interact_action and not bright_non_interact:
                return ("direct", interact_action)
            if len(bright_non_interact) == 1:
                return ("menu", None)
        if len(actions) == 1:
            return ("direct", actions[0])
        return ("menu", None)

    # Legacy names used by HUD/older files.
    def smart_resolve(iid):
        return resolve_interactable_click(iid)

    def smart_mode_active():
        try:
            for iid in interactables_in_current_location():
                if not all_actions_seen(iid):
                    return "explore"
            return "fast"
        except Exception:
            return "explore"

    def interactables_in_current_location():
        out = []
        try:
            out.extend(npcs_here())
        except Exception:
            pass
        try:
            loc = location_data()
            for it in loc.get("items", []):
                iid = it.get("item")
                if iid:
                    out.append(iid)
            for obj in loc.get("objects", []):
                iid = obj.get("id")
                if iid:
                    out.append(iid)
        except Exception:
            pass
        return out

    def mark_action_seen(iid, action_id):
        seen_actions.add((iid, action_id))
        last_actions[iid] = action_id

    def has_seen_action(iid, action_id):
        return (iid, action_id) in seen_actions

    def all_actions_seen(iid):
        actions = interactable_actions(iid, only_available=True)
        if not actions:
            return True
        return all(has_seen_action(iid, a.get("id")) for a in actions)

    def action_is_darkened(iid, action):
        if not action:
            return False
        if action.get("id") == "interact":
            return False
        if action.get("id") == "talk" and _looks_like_character(iid):
            try:
                if not character_has_seen_basic_talk(iid):
                    return False
                return character_talk_exhausted(iid)
            except Exception:
                return has_seen_action(iid, "talk")
        return has_seen_action(iid, action.get("id"))

    def _prepare_interactable_action(iid, action):
        store._pending_interactable_id = iid
        store._pending_action_id = action.get("id") if action else None

    def _run_interactable_action(iid, action):
        if not action:
            return
        try:
            if not game_action_allowed(action.get("id"), iid):
                renpy.notify(time_sensitive_lock_message())
                return
        except Exception:
            pass
        _prepare_interactable_action(iid, action)
        mark_action_seen(iid, action.get("id"))
        try:
            emit("interactable_clicked", iid, action_id=action.get("id"))
        except Exception:
            pass
        d = get_interactable(iid)
        if d and d.get("kind") == "character":
            begin_dialogue(iid)
        stamina = action.get("stamina")
        if stamina is None:
            stamina = 20
        if stamina:
            queue_stamina_cost(stamina)
        if action.get("label"):
            renpy.jump(action["label"])

    def handle_interactable_click(iid, pos=(0.5, 0.5)):
        mode, action = resolve_interactable_click(iid)
        if mode == "direct":
            _run_interactable_action(iid, action)
        elif mode == "menu":
            renpy.show_screen("action_menu", iid, pos)
        elif mode == "locked":
            renpy.notify(time_sensitive_lock_message())

    # Backwards-compatible private name used by Engine/UI/Locations.rpy before the merge.
    _handle_interactable_click = handle_interactable_click

    def auto_register_character_interactables():
        cids = set()
        try:
            cids.update(character_stats.keys())
        except Exception:
            pass
        try:
            cids.update(character_schedules.keys())
        except Exception:
            pass
        for cid in cids:
            register_interactable(cid, kind="character", title=character_display_name(cid))


init 50 python:
    auto_register_character_interactables()


label _character_talk_dispatch:
    $ _cid = _pending_interactable_id
    $ begin_dialogue(_cid)
    $ _entry = choose_character_talk(_cid)
    if _entry:
        $ mark_character_talk_seen(_cid, _entry)
        if _entry.get("label"):
            call expression _entry["label"]
        else:
            $ say_character(_cid, _entry.get("line", "..."))
    else:
        $ say_character(_cid, "...")
    jump explore


label _character_quest_dispatch:
    $ _cid = _pending_interactable_id
    $ begin_dialogue(_cid)
    $ _label = character_quest_label(_cid)
    if _label and renpy.has_label(_label):
        call expression _label
    elif _cid and renpy.has_label("quest_" + _cid):
        call expression "quest_" + _cid
    elif _cid and renpy.has_label("talk_" + _cid):
        call expression "talk_" + _cid
    else:
        call talk_unknown
    jump explore


label _character_interact_dispatch:
    $ _cid = _pending_interactable_id
    $ begin_dialogue(_cid)
    $ _label = character_interact_label(_cid)
    if _label and renpy.has_label(_label):
        call expression _label
    elif _cid and renpy.has_label("interact_" + _cid):
        call expression "interact_" + _cid
    else:
        call talk_unknown
    jump explore
