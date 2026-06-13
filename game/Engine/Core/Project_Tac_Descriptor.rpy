# Project Tac engine contract for tools and optional authoring extensions.
# Keep this runtime-safe: the game must not depend on DevTools being present.

init -1000 python:
    PROJECT_TAC_VERSION = "1.0.0"
    PROJECT_TAC_DATA_SCHEMA = 1

    PROJECT_TAC_PATHS = {
        "characters_data": "Game/_Data/Characters.rpy",
        "character_schedules_data": "Game/_Data/Character_Schedules.rpy",
        "locations_data": "Game/_Data/Areas_Locations.rpy",
        "items_data": "Game/_Data/Items.rpy",
        "quests_data": "Game/_Data/Quests.rpy",
        "content_root": "Game/Content",
        "dialogue_interact_default": "Game/Content/Dialogue/Interact/Alice.rpy",
        "story_default": "Game/Content/Story/Act_01/chapter1_intro.rpy",
        "interaction_default": "Game/Content/Interactions/School/hallway.rpy",
        "gallery_content_default": "Game/Content/Dialogue/Interact/Complex_Test_Arc.rpy",
        "engine_ui": "Engine/UI/Screens.rpy",
        "engine_validation": "Engine/Core/Validation.rpy",
        "save_migrations": "Engine/State/Migrations.rpy",
        "root_screens": "screens.rpy",
        "root_gui": "gui.rpy",
        "generated_root": "Game/_Generated",
    }

    PROJECT_TAC_ENGINE = {
        "id": "project_tac",
        "engine_version": PROJECT_TAC_VERSION,
        "data_schema": PROJECT_TAC_DATA_SCHEMA,
        "paths": PROJECT_TAC_PATHS,
        "capabilities": {
            "characters": 1,
            "relationships": 1,
            "locations": 2,
            "quests": 2,
            "inventory": 2,
            "gallery": 1,
            "minigames": 1,
            "source_authoring": 2,
            "live_studio_sync": 2,
            "validation": 2,
        },
    }

    def project_tac_path(key, default=None):
        return PROJECT_TAC_PATHS.get(key, default)

    def project_tac_supports(capability, minimum=1):
        try:
            actual = int(PROJECT_TAC_ENGINE.get("capabilities", {}).get(capability, 0) or 0)
            minimum = int(minimum or 0)
        except Exception:
            return False
        return actual >= minimum
