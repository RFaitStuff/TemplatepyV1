# Project Tac extension for Ren'Py Live Studio.
# This file is optional project glue: it never changes Live Studio's base model.

init -845 python in live_studio:
    import renpy.store as store

    def pt_available():
        return hasattr(store, "project_save_id") and getattr(store, "project_save_id", None) == "project_tac"

    def pt_store_dict(name):
        value = getattr(store, name, {})
        return value if isinstance(value, dict) else {}

    def pt_store_list(name):
        value = getattr(store, name, [])
        return value if isinstance(value, (list, tuple, set)) else []

    def pt_refresh_index():
        index = {
            "locations": sorted(pt_store_dict("locations").keys()),
            "quests": sorted(pt_store_dict("quest_defs").keys()),
            "items": sorted(pt_store_dict("item_defs").keys()),
            "characters": sorted(pt_store_dict("character_stats").keys()),
            "branches": sorted(pt_store_dict("branch_defs").keys()),
            "systems": sorted(getattr(store, "SYSTEM_DEFAULTS", {}).keys()) if hasattr(store, "SYSTEM_DEFAULTS") else [],
            "text_tags": sorted(getattr(store.config, "custom_text_tags", {}).keys()),
            "image_aliases": dict(getattr(store, "character_image_aliases", {}) or {}),
        }
        runtime["project_tac_index"] = index
        log_diagnostic("info", "Project Tac index refreshed", {
            "locations": len(index["locations"]),
            "quests": len(index["quests"]),
            "items": len(index["items"]),
            "characters": len(index["characters"]),
        })
        restart()
        return None

    def pt_index():
        if "project_tac_index" not in runtime:
            pt_refresh_index()
        return runtime.get("project_tac_index", {})

    def pt_summary_rows():
        index = pt_index()
        rows = [
            {"label": "Locations", "value": len(index.get("locations", []))},
            {"label": "Quests", "value": len(index.get("quests", []))},
            {"label": "Items", "value": len(index.get("items", []))},
            {"label": "Characters", "value": len(index.get("characters", []))},
            {"label": "Branches", "value": len(index.get("branches", []))},
            {"label": "Systems", "value": ", ".join(index.get("systems", [])[:8])},
            {"label": "Text Tags", "value": ", ".join(index.get("text_tags", [])[:12])},
        ]
        aliases = index.get("image_aliases", {})
        if aliases:
            rows.append({"label": "Image Aliases", "value": ", ".join("{}->{}".format(k, v) for k, v in sorted(aliases.items()))})
        return rows

    def pt_selected_bounds():
        item, _parent, kind = selected_item()
        if not item:
            return None
        bounds = item.get("bounds")
        if not bounds:
            props = item.get("properties", {})
            width = props.get("xsize") or 120
            height = props.get("ysize") or 120
            bounds = calculate_bounds(props, width, height)
        return {
            "item": item,
            "kind": kind,
            "x": float(bounds.get("x", 0)),
            "y": float(bounds.get("y", 0)),
            "width": max(1, int(bounds.get("width", 1))),
            "height": max(1, int(bounds.get("height", 1))),
        }

    def pt_hotspot_from_selection():
        data = pt_selected_bounds()
        if not data:
            return "# Select an image, UI node, or captured hotspot first."
        item = data["item"]
        center_x = round((data["x"] + data["width"] / 2.0) / float(store.config.screen_width), 3)
        center_y = round((data["y"] + data["height"] / 2.0) / float(store.config.screen_height), 3)
        image_name = item.get("image") or item.get("name") or ""
        object_id = safe_identifier(image_name.split()[-1] if image_name else item.get("name", "object"), "object")
        return "\n".join([
            "object_spot(",
            "    {!r},".format(object_id),
            "    name={!r},".format(object_id.replace("_", " ").title()),
            "    pos=({}, {}),".format(center_x, center_y),
            "    size=({}, {}),".format(data["width"], data["height"]),
            "    image={!r},".format(image_name) if image_name else "    # image=\"registered image name\",",
            "    allow_item_use=True,",
            "    actions=[",
            "        action(\"Inspect\", \"{}_inspect\", primary=True, once=True),".format(object_id),
            "    ],",
            "),",
            "",
            "label {}_inspect:".format(object_id),
            "    \"Describe what the player notices.\"",
            "    jump explore",
        ])

    def pt_location_template():
        return "\n".join([
            "location_package(",
            "    id=\"new_location\",",
            "    name=\"New Location\",",
            "    area=\"school\",",
            "    bg=\"bg_image_name\",",
            "    positions={",
            "        \"alice\": [(0.35, 1.0)],",
            "    },",
            "    layers=[",
            "        explore_layer(\"bg_image_name\", slot=\"background\", zoom=1.02, drift=(8, 0), duration=18.0),",
            "    ],",
            "    objects=[",
            "        object_spot(\"desk\", name=\"Desk\", pos=(0.55, 0.62), size=(180, 120), allow_item_use=True),",
            "    ],",
            "    exits=[",
            "        exit_spot(\"hallway\", label=\"Hallway\", pos=(0.5, 0.92), size=(260, 140)),",
            "    ],",
            ")",
        ])

    def pt_quest_template():
        return "\n".join([
            "create_quest(",
            "    \"new_quest\",",
            "    title=\"New Quest\",",
            "    desc=\"Short player-facing quest description.\",",
            "    discover=True,",
            "    unlock_when=req(\"flag:intro_done\"),",
            "    guide_precision=\"area\",",
            "    target={\"location\": \"hallway\"},",
            "    steps=[",
            "        step(\"start\", \"Inspect the clue\", flag=\"new_quest_started\", target={\"object\": \"desk\", \"location\": \"new_location\"}),",
            "        step(\"finish\", \"Talk to Alice\", flag=\"new_quest_done\", target={\"npc\": \"alice\", \"location\": \"hallway\"}),",
            "    ],",
            ")",
        ])

    def pt_dialogue_template():
        return "\n".join([
            "label alice_new_scene:",
            "    $ begin_dialogue(\"alice\", pos=\"left\")",
            "    a \"Write the scene like normal.\"",
            "    $ menu_side(\"right\")",
            "    menu:",
            "        \"Confident answer. {color=#ffd27a}(Coolness 10){/color}\" if can(\"stat:Coolness>=10\"):",
            "            $ stat(\"player\", \"Coolness\", 1, \"3d\")",
            "            a \"That worked.\"",
            "        \"Kind answer. {color=#ffd27a}(Alice Love 10){/color}\" if can(\"Alice.Love>=10\"):",
            "            $ alice.trust(1, \"3d\")",
            "            a \"I knew you would say that.\"",
            "    $ end_dialogue()",
            "    return",
        ])

    def pt_branch_template():
        return "\n".join([
            "$ branch_point(\"new_branch\")",
            "$ stop_rollback_here()",
            "menu:",
            "    \"Take Alice's route.\":",
            "        $ take_branch(\"new_branch\", \"alice\")",
            "        jump alice_route",
            "    \"Take Alex's route.\":",
            "        $ take_branch(\"new_branch\", \"alex\")",
            "        jump alex_route",
        ])

    def pt_image_locator_reference():
        aliases = pt_index().get("image_aliases", {})
        alias_lines = ["character_image_aliases = {"]
        if aliases:
            for key, value in sorted(aliases.items()):
                alias_lines.append("    {!r}: {!r},".format(key, value))
        else:
            alias_lines.append("    \"temporary_character\": \"alice\",")
        alias_lines.append("}")
        return "\n".join([
            "# Auto image locator patterns",
            "# Character files: Alice.png, Alice_Happy.png, Alice_Outfit1_Sad.png",
            "# Author-facing show helpers:",
            "$ Show(\"Alice\", side=\"Left\")",
            "$ Show(\"Alice\", emotion=\"Happy\", side=\"Right\")",
            "$ Hide(\"Alice\")",
            "",
            "# Temporary image aliases for test characters:",
        ] + alias_lines)

    def pt_inventory_template():
        return "\n".join([
            "define_item(\"lockpick\", name=\"Lockpick\", desc=\"Thin enough for old doors.\", tags=[\"tool\"], quest_item=True)",
            "",
            "item_use(",
            "    \"lockpick\",",
            "    \"archive_door\",",
            "    label=\"use_lockpick_on_archive_door\",",
            "    requires=req(\"stat:Coolness>=10\"),",
            "    consume=False,",
            "    fail=\"The lockpick slips. You need a steadier hand.\",",
            ")",
            "",
            "item_use(\"*\", \"archive_door\", fail=\"I don't think {item_name} will work on this door.\", always_fail=True)",
            "recipe(\"coded_slip\", \"glass_badge\", result=\"matched_badge_clue\")",
            "",
            "label use_lockpick_on_archive_door(item_id=None, target=None):",
            "    \"You work the pick under the old latch.\"",
            "    $ unlock_room(\"archive_room\")",
            "    $ set_flag(\"archive_room_unlocked\")",
            "    jump explore",
        ])

    def pt_gallery_template():
        return "\n".join([
            "gallery_auto(",
            "    \"alice_private_signal_scene\",",
            "    character=\"alice\",",
            "    group=\"Alice\",",
            "    unlock=\"flag:alice_private_signal_scene_done\",",
            "    scene_image=\"bg smp_roof\",",
            "    autounlock=False,",
            ")",
            "",
            "label alice_private_signal_scene:",
            "    scene bg smp_roof",
            "    show alice at left",
            "    a \"This scene can unlock itself when finished.\"",
            "    $ set_flag(\"alice_private_signal_scene_done\")",
            "    return",
        ])

    def pt_minigame_template():
        return "\n".join([
            "minigame(",
            "    \"door_lockpick\",",
            "    label=\"door_lockpick_minigame\",",
            "    skip_label=\"door_lockpick_skip\",",
            "    skip_result=\"win\",",
            "    requires=req(\"item:lockpick\"),",
            "    fail_forward=True,",
            ")",
            "",
            "label door_lockpick_minigame(game_id=None):",
            "    # Replace this with a real screen or mechanic later.",
            "    \"You test the lock.\"",
            "    $ complete_minigame(game_id, \"win\")",
            "    return",
            "",
            "label door_lockpick_skip(game_id=None):",
            "    \"You bypass the lockpick challenge.\"",
            "    return",
            "",
            "$ start_minigame(\"door_lockpick\")",
        ])

    def pt_text_transform_reference():
        return "\n".join([
            "# Kinetic text tags",
            "a \"{wave}Excited text.{/wave}\"",
            "a \"{shake}Scared text.{/shake}\"",
            "a \"{fade}Slow reveal text.{/fade}\"",
            "a \"{swell}Soft emphasis.{/swell}\"",
            "a \"{rainbow}Unstable color.{/rainbow}\"",
            "a \"{glitch}Heavy glitch, accessibility-toggle aware.{/glitch}\"",
            "",
            "# Common character placement",
            "$ Show(\"Alice\", side=\"Left\")",
            "$ Show(\"Alex\", side=\"Right\")",
            "$ Show(\"Alice\", emotion=\"Happy\", side=\"Middle\")",
            "",
            "# Exploration parallax layer",
            "explore_layer(\"bg smp_noticeboard\", slot=\"overlay\", alpha=0.25, zoom=1.04, drift=(10, 0), duration=18.0)",
        ])

    def pt_validate_project():
        issues = []
        locations = pt_store_dict("locations")
        quest_defs = pt_store_dict("quest_defs")
        item_defs = pt_store_dict("item_defs")
        interactables = pt_store_dict("interactable_defs")
        for qid, q in quest_defs.items():
            targets = []
            if isinstance(q.get("target"), dict):
                targets.append(q.get("target"))
            for obj in q.get("objectives", []) or []:
                if isinstance(obj, dict) and isinstance(obj.get("target"), dict):
                    targets.append(obj.get("target"))
            for target in targets:
                loc = target.get("location")
                if loc and loc not in locations:
                    issues.append("Quest {} targets missing location {}".format(qid, loc))
                obj = target.get("object")
                if obj and obj not in interactables:
                    issues.append("Quest {} targets missing interactable {}".format(qid, obj))
                item = target.get("item")
                if item and item not in item_defs:
                    issues.append("Quest {} targets missing item {}".format(qid, item))
        if not issues:
            issues.append("No Project Tac registry issues found.")
        return "\n".join(issues)

    def pt_command_preview(title, builder):
        text = builder()
        set_extension_preview(title, text)
        return text

    register_extension(
        "project_tac",
        title="Project Tac",
        description="Authoring helpers for locations, quests, branches, dialogue, parallax layers, and engine registries.",
        summary=pt_summary_rows,
        available=pt_available,
        order=10,
        commands=[
            {"id": "refresh", "title": "Refresh Project Index", "description": "Re-scan Project Tac registries.", "action": pt_refresh_index},
            {"id": "validate", "title": "Validate Registries", "description": "Find missing quest targets and bad references.", "action": lambda: pt_command_preview("Project Tac Validation", pt_validate_project)},
            {"id": "hotspot", "title": "Selection -> Interactable", "description": "Generate object_spot code from the selected canvas bounds.", "action": lambda: pt_command_preview("Interactable From Selection", pt_hotspot_from_selection)},
            {"id": "location", "title": "Location Template", "description": "Generate a location_package starter with parallax, objects, exits, and positions.", "action": lambda: pt_command_preview("Location Template", pt_location_template)},
            {"id": "quest", "title": "Quest Template", "description": "Generate a short create_quest starter.", "action": lambda: pt_command_preview("Quest Template", pt_quest_template)},
            {"id": "dialogue", "title": "Dialogue Template", "description": "Generate Project Tac dialogue with side menu and stat requirements.", "action": lambda: pt_command_preview("Dialogue Template", pt_dialogue_template)},
            {"id": "branch", "title": "Branch Template", "description": "Generate branch point and permanent branch-save compatible script.", "action": lambda: pt_command_preview("Branch Template", pt_branch_template)},
            {"id": "images", "title": "Image Locator Reference", "description": "Show image alias and Show/Hide helper syntax.", "action": lambda: pt_command_preview("Image Locator Reference", pt_image_locator_reference)},
            {"id": "inventory", "title": "Inventory/Item Template", "description": "Generate item, item-use, wildcard fail, and crafting examples.", "action": lambda: pt_command_preview("Inventory Template", pt_inventory_template)},
            {"id": "gallery", "title": "Gallery Template", "description": "Generate gallery_auto and scene unlock example.", "action": lambda: pt_command_preview("Gallery Template", pt_gallery_template)},
            {"id": "minigame", "title": "Minigame Template", "description": "Generate universal minigame registration and skip-mode labels.", "action": lambda: pt_command_preview("Minigame Template", pt_minigame_template)},
            {"id": "text_transforms", "title": "Text/Transform Reference", "description": "Show kinetic text, character placement, and parallax snippets.", "action": lambda: pt_command_preview("Text And Transform Reference", pt_text_transform_reference)},
        ],
    )
