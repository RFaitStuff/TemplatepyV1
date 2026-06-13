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

    def apply_save_migrations():
        global save_migration_version
        if save_migration_version >= SAVE_MIGRATION_VERSION:
            return None

        _migrate_story_flags()
        _migrate_inventory_items()
        _migrate_quest_ids()
        _migrate_objective_ids()

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
            if old in quest_log and new not in quest_log:
                quest_log[new] = quest_log.pop(old)
                quest_log[new].id = new
            elif old in quest_log:
                quest_log.pop(old, None)

    def _migrate_objective_ids():
        for (quest_id, old), new in save_migration_rules.get("objectives", {}).items():
            q = quest_log.get(quest_id)
            if not q:
                continue
            for objective in getattr(q, "objectives", []) or []:
                if getattr(objective, "id", None) == old:
                    objective.id = new


init 999 python:
    try:
        if apply_save_migrations not in config.after_load_callbacks:
            config.after_load_callbacks.append(apply_save_migrations)
    except Exception:
        pass
