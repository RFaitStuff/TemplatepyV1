# =============================================================================
# Save Migration Helpers
# =============================================================================
# Register compatibility moves here before public releases with real saves.
# =============================================================================


default save_migration_version = 0


init -10 python:
    SAVE_MIGRATION_VERSION = 1
    save_migration_rules = {
        "flags": {},
        "items": {},
        "quests": {},
        "objectives": {},
        "player_stats": {},
        "character_stats": {},
    }


init python:

    def rename_flag(old, new):
        save_migration_rules["flags"][old] = new
        return None

    def rename_item(old, new):
        save_migration_rules["items"][old] = new
        return None

    def rename_quest(old, new):
        save_migration_rules["quests"][old] = new
        return None

    def rename_objective(quest_id, old, new):
        save_migration_rules["objectives"][(quest_id, old)] = new
        return None

    def rename_player_stat(old, new):
        save_migration_rules["player_stats"][old] = new
        return None

    def rename_character_stat(old, new):
        save_migration_rules["character_stats"][old] = new
        return None

    def apply_save_migrations():
        global save_migration_version
        if save_migration_version >= SAVE_MIGRATION_VERSION:
            return None

        _migrate_story_flags()
        _migrate_inventory_items()
        _migrate_quest_ids()
        _migrate_objective_ids()
        _migrate_player_stats()
        _migrate_character_stats()

        save_migration_version = SAVE_MIGRATION_VERSION
        try:
            request_update_state("save_migration", version=save_migration_version)
        except Exception:
            pass
        return None

    def _migrate_story_flags():
        for old, new in save_migration_rules.get("flags", {}).items():
            if old in story_flags:
                story_flags.discard(old)
                story_flags.add(new)

    def _migrate_inventory_items():
        for old, new in save_migration_rules.get("items", {}).items():
            count = player_inventory.pop(old, 0)
            if count:
                player_inventory[new] = player_inventory.get(new, 0) + count

    def _migrate_quest_ids():
        for old, new in save_migration_rules.get("quests", {}).items():
            old_state = quest_states.pop(old, None)
            if old_state:
                if new in quest_states:
                    _merge_quest_state(new, old_state)
                else:
                    quest_states[new] = old_state

            if old in quest_log and new not in quest_log:
                quest_log[new] = quest_log.pop(old)
                quest_log[new].id = new
            elif old in quest_log:
                quest_log.pop(old, None)

            if tracked_quest_id == old:
                globals()["tracked_quest_id"] = new

    def _migrate_objective_ids():
        for (quest_id, old), new in save_migration_rules.get("objectives", {}).items():
            state = quest_states.get(quest_id, {})
            done = set(state.get("done", []) or [])
            if old in done:
                done.discard(old)
                done.add(new)
                state["done"] = sorted(done)

            q = quest_log.get(quest_id)
            if q:
                for objective in getattr(q, "objectives", []) or []:
                    if getattr(objective, "id", None) == old:
                        objective.id = new

    def _merge_quest_state(qid, old_state):
        state = quest_states.setdefault(qid, {})
        old_done = set(old_state.get("done", []) or [])
        new_done = set(state.get("done", []) or [])
        state["done"] = sorted(old_done | new_done)
        old_rank = {"inactive": 0, "active": 1, "failed": 2, "completed": 3}
        old_value = old_state.get("state", "inactive")
        new_value = state.get("state", "inactive")
        if old_rank.get(old_value, 0) > old_rank.get(new_value, 0):
            state["state"] = old_value
        state["discovered"] = bool(state.get("discovered")) or bool(old_state.get("discovered"))

    def _migrate_player_stats():
        for old, new in save_migration_rules.get("player_stats", {}).items():
            if hasattr(store, old):
                old_value = getattr(store, old)
                if not hasattr(store, new):
                    setattr(store, new, old_value)

    def _migrate_character_stats():
        for old, new in save_migration_rules.get("character_stats", {}).items():
            for char_id, data in (character_stats or {}).items():
                if old in data and new not in data:
                    data[new] = data.get(old)


init 999 python:
    try:
        if apply_save_migrations not in config.after_load_callbacks:
            config.after_load_callbacks.append(apply_save_migrations)
    except Exception:
        pass
