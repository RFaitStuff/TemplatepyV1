default systems_enabled = {
    "dialogue": True,
    "interactions": True,
    "stamina": True,
    "time": True,
    "quests": True,
    "mood": True,
    "gallery": True,
    "notifications": True,
    "debug_tools": True,
}

define time_skip_sleep_hour = 2
define time_skip_wake_hour = 8

init -95 python:
    def system_enabled(name):
        return bool(systems_enabled.get(name, True))

    def set_system_enabled(name, value=True):
        systems_enabled[name] = bool(value)
        return None

    def time_sensitive_quest_lock():
        if not system_enabled("quests"):
            return None
        try:
            for quest in active_quests():
                target = getattr(quest, "target", None) or {}
                if target.get("time_sensitive") or target.get("locks_time"):
                    return quest
                for objective in getattr(quest, "objectives", []):
                    if getattr(objective, "done", False):
                        continue
                    obj_target = getattr(objective, "target", None) or {}
                    if obj_target.get("time_sensitive") or obj_target.get("locks_time"):
                        return quest
        except Exception:
            return None
        return None

    def time_sensitive_lock_message(quest=None):
        if quest is None:
            quest = time_sensitive_quest_lock()
        if quest is not None:
            target = getattr(quest, "target", None) or {}
            if target.get("lock_message"):
                return target.get("lock_message")
            for objective in getattr(quest, "objectives", []):
                if getattr(objective, "done", False):
                    continue
                obj_target = getattr(objective, "target", None) or {}
                if obj_target.get("lock_message"):
                    return obj_target.get("lock_message")
        return "I should stick to the task at hand."

    def game_action_allowed(action_type=None, iid=None):
        quest = time_sensitive_quest_lock()
        if quest is None:
            return True
        target = getattr(quest, "target", None) or {}
        if action_type == "time" and target.get("allow_time_skip"):
            return True
        if action_type == "stamina" and target.get("allow_stamina"):
            return True
        if iid:
            allowed = target.get("allowed_interactables") or target.get("allowed_targets")
            if allowed and iid in allowed:
                return True
            for objective in getattr(quest, "objectives", []):
                if getattr(objective, "done", False):
                    continue
                obj_target = getattr(objective, "target", None) or {}
                if iid in (obj_target.get("npc"), obj_target.get("item"), obj_target.get("object")):
                    return True
        return False
