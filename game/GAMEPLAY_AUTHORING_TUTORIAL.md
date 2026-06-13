# Project Tac Gameplay Authoring Tutorial

This is the practical reference for building gameplay without digging through engine code. The core rule is:

Data describes what exists. Content describes what happens.

Writers should usually touch these folders:

```text
Game/_Data/
    Characters.rpy
    Character_Schedules.rpy
    Areas_Locations.rpy
    Items.rpy
    Quests.rpy

Game/Content/
    Dialogue/
    Interactions/
    Story/
```

The engine and mechanics folders are the reusable backbone. You only edit them when adding a new system, not when writing normal gameplay.

## Fast Workflow

1. Register the thing in `Game/_Data`: character, location, item, or quest.
2. Place it in `Game/Content`: a room package, object spot, item spot, dialogue label, or story label.
3. Connect progress with flags: `set_flag("some_checkpoint")`.
4. Gate optional content with requirements: `req("flag:intro_done", "Alice.Love>=10")`.
5. Test from LiveStudio or the in-game debug tools.

## Requirement Rules

Requirements work across locations, interactables, choices, quests, items, gallery unlocks, and UI feedback.

Use compact string requirements when writing content:

```renpy
$ can("flag:read_noticeboard")
$ can("item:archive_key")
$ can("quest_done:noticeboard_check")
$ can("Alice.Love>=10")
$ can("Coolness>=10")
```

Use `req(...)` when a field expects a reusable requirement list:

```renpy
requires=req("flag:read_noticeboard", "Alice.Love>=10")
```

Common requirement strings:

| Rule | Meaning |
| --- | --- |
| `flag:my_flag` | Requires a story flag. |
| `no_flag:my_flag` | Requires a story flag to be absent. |
| `item:key` | Requires at least one item. |
| `item:coin>=3` | Requires an item count. |
| `no_item:key` | Requires the player not to have an item. |
| `tag:tool` | Requires any carried item with that tag. |
| `quest_active:quest_id` | Requires an active quest. |
| `quest_done:quest_id` | Requires a completed quest. |
| `quest_started:quest_id` | Requires discovered, active, completed, or failed quest state. |
| `quest_discovered:quest_id` | Requires the quest to have appeared in the log. |
| `step:quest_id.objective_id` | Requires one quest objective to be done. |
| `location:hallway` | Requires the current location. |
| `area:school` | Requires the current area. |
| `time:morning\|afternoon` | Requires a time bucket. |
| `weekday:monday\|friday` | Requires a weekday. |
| `present:alice` | Requires a character in the current location. |
| `mood:alice.happy` | Requires a positive mood value. |
| `system:inventory` | Requires an enabled mechanic. |
| `Coolness>=10` | Requires a player stat. |
| `Alice.Love>=10` | Requires a character stat. |

Dictionary requirements still work, but use them only when a tool generates them or a case is clearer that way:

```renpy
requires={
    "flags": ["intro_done"],
    "stats": {"Coolness": 10},
    "character_stats": {"alice": {"love": 10}},
}
```

## Flags And Routes

Flags are the main writing glue. Quests can start, progress, or complete from flags automatically.

```renpy
$ set_flag("read_noticeboard")
$ clear_flag("read_noticeboard")

if has_flag("read_noticeboard"):
    "The noticeboard has already changed."
```

The writer shorthand is:

```renpy
flag read_noticeboard
unflag temporary_hint_seen
```

Use routes for long-term story direction:

```renpy
$ set_route("alice")

if on_route("alice"):
    a "You came back."
```

For larger projects, optionally register route ids so validation can catch typos:

```renpy
init 5 python:
    register_route("alice", title="Alice Route", requires="flag:met_alice")
    register_route("neutral", title="Neutral Route")
```

Good flag names are concrete checkpoints: `got_archive_key`, `alice_roof_signal_done`, `entered_archive_room`.

## Characters

Register character data in `Game/_Data/Characters.rpy`. Schedules live separately in `Game/_Data/Character_Schedules.rpy`.

Use the author handles for short stat and mood work:

```renpy
$ alice.love += 1
$ alice.trust.no += 1
$ alice.happy.set(4, duration=2)
$ player.Coolness += 1
```

The statement shorthand also works:

```renpy
stat alice love +1
stat alex trust -1
```

The full helper is useful when applying multiple stats or cooldowns:

```renpy
$ stat("alice", "love", 1, "trust", 1, "3d")
$ stat("player", "Coolness", 1, source="alice")
```

Mood and reaction shorthand:

```renpy
mood Alice happy
mood Alice happy +3 duration=2
mood Alice sad -1
react Alice embarrassed
react Alice
```

Cooldown tokens:

| Token | Meaning |
| --- | --- |
| `"3d"` | This stat can be rewarded once every 3 in-game days. |
| `"3da"` | All stats in this call share a 3-day cooldown. |
| `"no"` | This stat can be rewarded once ever. |
| `"noa"` | All stats in this call are rewarded once ever. |

Show characters with auto location placement:

```renpy
$ show_npc("alice")
$ show_npc("alex", pos=(0.72, 1.0), locked=True)
$ hide_npc("alice")
```

Writer shorthand:

```renpy
Show Alice
Show Alice(side=Left)
Show Alice(side=Right, emotion=happy)
Show Alice(pos=0.35 1.0, locked=True)
Show Alice(variant=1, outfit=casual, zoom=0.55)
Hide Alice
```

`locked=True` tells the menu displacement system not to move that character.

## Dialogue And Choices

Ambient talk belongs in `Game/Content/Dialogue/Talk/`. Meaningful character activities belong in `Game/Content/Dialogue/Interact/`.

```renpy
label alice_roof_signal:
    $ begin_dialogue("alice")
    $ show_npc("alice", pos=(0.36, 1.0), locked=True)
    a "You saw it too, right?"

    $ menu_side("middle")
    menu:
        "Make the confident joke." if can("Coolness>=10"):
            $ player.Coolness += 1
            $ alice.love += 1
            a "That was almost funny."

        "Tell Alice how you feel." if can("Alice.Love>=10"):
            $ alice.trust += 1
            $ set_flag("alice_confession_started")
            a "I was hoping you would say that."

        "Keep it practical.":
            a "Right. The noticeboard first."

    $ set_flag("alice_roof_signal_done")
    $ end_dialogue()
    jump explore
```

Two-character dialogue works the same way:

```renpy
label bree_cora_argument:
    $ begin_dialogue("bree", "cora")
    $ show_npc("bree", pos=(0.32, 1.0), locked=True)
    $ show_npc("cora", pos=(0.68, 1.0), locked=True)
    b "The archive proves it was staged."
    c "Or it proves someone wanted us to think that."
    $ menu_side("middle")
    menu:
        "Back Bree.":
            $ take_branch("bree_cora_route", "bree")
        "Back Cora.":
            $ take_branch("bree_cora_route", "cora")
        "Refuse both readings.":
            $ take_branch("bree_cora_route", "neutral")
    $ set_flag("bree_cora_side_chosen")
    $ end_dialogue()
    jump explore
```

## Areas And Locations

Register areas and locations in `Game/_Data/Areas_Locations.rpy`.

```renpy
init 5 python:
    register_area("school", "School", order=10)

    register_location(
        "hallway",
        name="Main Hallway",
        area="school",
        bg="school hallway day",
        unlocked=True,
    )
```

Build the room in `Game/Content/Interactions/...` with `location_package(...)`.

```renpy
init 10 python:
    location_package(
        "hallway",
        area="school",
        bg="school hallway day",
        npcs=[
            ("alice", [(0.25, 1.0)]),
            ("bree", [(0.62, 1.0)]),
        ],
        items=[
            item_spot(
                "archive_key",
                pos=(0.48, 0.78),
                requires="quest_active:archive_keyhunt",
                hide_flag="got_archive_key",
            ),
        ],
        objects=[
            object_spot(
                "archive_door",
                name="Archive Door",
                pos=(0.82, 0.48),
                size=(180, 420),
                allow_item_use=True,
                actions=[
                    action(
                        "Inspect",
                        label="archive_door_inspect",
                        primary=True,
                        once=True,
                        seen_message="The door is still locked.",
                    ),
                    action(
                        "Use Item",
                        label="archive_door_pick_item",
                        icon="item",
                    ),
                ],
            ),
        ],
        exits=[
            exit_spot("front", pos=(0.08, 0.92), label="Outside"),
            exit_spot(
                "archive_room",
                pos=(0.84, 0.92),
                requires="flag:archive_room_unlocked",
                locked_message="The archive door is locked.",
                show_when_locked=True,
            ),
        ],
        parallax=[
            explore_layer("hallway dust", slot="overlay", drift=(8, 0), alpha=0.25),
        ],
        first_visit="hallway_first_visit",
    )
```

Use `hitbox=` for custom clickable shapes:

```renpy
object_spot(
    "doorway",
    name="Doorway",
    pos=(0.5, 0.5),
    size=(360, 520),
    hitbox="poly: 0 0, 320 40, 360 520, 20 500",
    actions=[action("Enter", label="doorway_enter")],
)
```

Hitbox forms:

| Form | Use |
| --- | --- |
| `"rect:x y w h"` | Rectangular region. |
| `"poly:x1 y1 x2 y2 ..."` | Polygon region. |
| `"mask:image_name"` | Named mask image. |
| `"opaque"` | Use the visible pixels of the image. |

## Interactables

Interactables can have multiple actions. Keep common object behavior in one label file per location.

```renpy
label archive_door_inspect:
    "The lock has fresh scratches around the plate."
    $ set_flag("archive_door_checked")
    jump explore

label archive_door_pick_item:
    $ select_item("Use what on the archive door?", target="archive_door", allow_any_item=True)
    jump explore
```

Use `once=True` for one-time actions. The system can show `seen_message` afterward.

```renpy
action(
    "Inspect",
    label="archive_door_inspect",
    once=True,
    seen_message="You already checked the lock.",
)
```

Use requirements for actions that appear only sometimes:

```renpy
action(
    "Decode",
    label="archive_terminal_decode",
    requires=req("item:sealed_drive", "Coolness>=10"),
)
```

## Items And Inventory

Register items in `Game/_Data/Items.rpy`.

```renpy
init 5 python:
    define_item(
        "archive_key",
        name="Archive Key",
        desc="A brass key with a blue tape label.",
        tags=["key", "tool"],
        quest_item=True,
        show_when="quest_active:archive_keyhunt",
        use_message="Nope.",
    )
```

Add or remove items in content:

```renpy
$ add_item("archive_key")
$ remove_item("archive_key")

if has_item("archive_key"):
    "The key is still in your bag."
```

Writer shorthand:

```renpy
item archive_key +1
item coin +3
item archive_key -1
```

Item use on world targets:

```renpy
init 5 python:
    item_use(
        "archive_key",
        "archive_door",
        label="archive_door_unlock",
        consume=False,
        success="The key turns.",
    )

    item_use(
        "lockpick",
        "archive_door",
        label="archive_door_lockpick",
        requires="Coolness>=10",
        consume=False,
        fail="You need steadier hands for this.",
    )

    item_use(
        "*",
        "archive_door",
        fail="I don't think {item_name} will work on this door.",
        always_fail=True,
    )
```

The wildcard `"*"` gives object-specific failure text for every wrong item.

Use item labels like this:

```renpy
label archive_door_unlock(item_id=None, target=None):
    $ set_flag("archive_room_unlocked")
    $ set_flag("archive_door_opened")
    "The key clicks into place."
    jump explore
```

Crafting:

```renpy
init 5 python:
    define_item("cloth", tags=["material"])
    define_item("stick", tags=["material"])
    define_item("torch", tags=["tool"])

    recipe("cloth", "stick", result="torch", fail="That will not hold.")
    combine_fail("archive_key", "lost_pen", "That is not a useful combination.")
```

## Quests

Register quests in `Game/_Data/Quests.rpy`. Definitions are immutable. Per-save progress lives in `quest_states`, so updating quest text later will not trap old saves with outdated objective definitions.

Basic quest:

```renpy
init 5 python:
    side_quest(
        "noticeboard_check",
        title="Read the Noticeboard",
        description="Someone left a flyer with your name on it.",
        start_flag="quest_noticeboard",
        track_on_start="force",
        clear_track_on_complete=True,
        guide_precision="exact",
        target={"object": "noticeboard", "location": "front"},
        objectives=[
            step(
                "read",
                "Find the noticeboard out front",
                flag="read_noticeboard",
                target={"object": "noticeboard", "location": "front"},
            ),
        ],
    )
```

Quest helpers:

| Helper | Use |
| --- | --- |
| `create_quest(id, ...)` | Generic quest. |
| `main_quest(id, ...)` | Main quest category. |
| `side_quest(id, ...)` | Side quest category. |
| `char_quest(id, character, ...)` | Character quest with character icon/grouping. |
| `step(id, text, ...)` | Objective builder. |
| `guide_target(...)` | Target builder for quest guide markers. |
| `discover_quest(id, start=False, track=False)` | Reveal a hidden quest manually. |
| `start_quest(id)` | Start a quest manually. |
| `progress_quest(id, objective_id)` | Mark an objective done. |
| `complete_quest(id)` | Complete a quest manually. |
| `set_tracked_quest(id)` | Track an active quest. |
| `clear_tracked_quest()` | Track no quest. |

Writer shorthand:

```renpy
quest discover alice_roof_scene
quest start archive_keyhunt
quest track archive_keyhunt
quest progress archive_keyhunt key
quest complete archive_keyhunt
quest clear_track
```

Quest fields:

| Field | Meaning |
| --- | --- |
| `title` | Quest name in the quest UI. |
| `description` | Quest description. |
| `category` | Main, side, misc, or custom grouping. |
| `character` | Character owner for character quests. |
| `start_flag` | Calling `set_flag(...)` starts the quest. |
| `complete_flag` | Calling `set_flag(...)` completes the quest. |
| `fail_flag` | Calling `set_flag(...)` fails the quest. |
| `objectives` / `steps` | Objective list. |
| `target` | Main quest guide target. |
| `discoverable` / `discover` | Hidden until discovered or unlocked. |
| `unlock_when` / `starts_after` | Requirement before the quest can be discovered. |
| `start_when` | Requirement that auto-starts the quest. |
| `show_when_inactive` | Show in log before starting. Use rarely. |
| `track_on_start` | `True` tracks if nothing else is tracked. `"force"` replaces current tracking. |
| `track_next` | Quest to track after this one completes. |
| `clear_track_on_complete` | Clear tracking when complete. Default is true. |
| `guide_precision` | How specific the quest guide should be. |

Guide precision examples:

| Value | Use |
| --- | --- |
| `"exact"` | Point to exact object, item, NPC, or location. |
| `"location"` | Tell the player the location, not the exact object. |
| `"area"` | Tell the player the area. |
| `"characters"` | Point toward one or more characters. |
| `"none"` | No useful marker; player must read and explore. |

Hidden quest that appears after another quest:

```renpy
char_quest(
    "alice_roof_scene",
    character="alice",
    title="A Quiet Signal",
    description="Alice keeps looking toward the roof.",
    unlock_when="quest_done:noticeboard_check",
    discoverable=True,
    guide_precision="characters",
    target={"npc": "alice", "location": "roof"},
    objectives=[
        step("talk", "Talk with Alice on the roof", flag="alice_roof_signal_done"),
    ],
)
```

Discover it from dialogue:

```renpy
label alice_first_real_talk:
    a "Meet me upstairs when you can."
    $ discover_quest("alice_roof_scene", start=True, track=False)
    jump explore
```

Time-sensitive locked quest target:

```renpy
target={
    "npc": "bree",
    "location": "hallway",
    "time_sensitive": True,
    "locks_time": True,
    "locks_interact": True,
    "allowed_interactables": ["bree"],
    "lock_message": "Bree is waiting with the archive lead.",
}
```

Use this rarely. Most unlocked quests should allow free exploration.

## Branches And Save Zones

Register branch points in `Engine/Story/Branches.rpy` or a project branch registry file.

```renpy
register_branch(
    "archive_evidence_method",
    title="Archive Evidence Method",
    choices={
        "crosscheck": {"title": "Cross-check badge and drive", "label": "archive_terminal_decode"},
        "isolate": {"title": "Isolate the drive", "label": "archive_terminal_decode"},
        "direct": {"title": "Decode directly", "label": "archive_terminal_decode"},
    },
)
```

Use the branch in story:

```renpy
$ branch_point("archive_evidence_method")
$ branch_save_zone("archive_evidence_method", "Archive Evidence Method")

menu:
    "Cross-check everything.":
        $ take_branch("archive_evidence_method", "crosscheck")
        $ set_flag("archive_crosschecked")
    "Decode directly." if can("Coolness>=10"):
        $ take_branch("archive_evidence_method", "direct")
        $ set_flag("archive_decoded_directly")
```

Stop rollback at dangerous points:

```renpy
$ stop_rollback_here("The route is locked in.")
```

Branch save zones are persistent special save slots:

```renpy
$ branch_save_zone("alice_route_start", "Alice Route Start")
```

Validation checks branch parent ids, choice labels, missing replay labels, and malformed requirements. `take_branch()` also returns `False` if a story script references a branch or choice that does not exist.

## Gallery

Register gallery scenes near the content they replay or in a gallery data file.

```renpy
init 5 python:
    gallery_scene(
        "alice_roof_scene",
        title="A Quiet Signal",
        label="alice_roof_scene",
        characters=["alice"],
        unlock="flag:alice_roof_signal_done",
    )
```

Automatic unlock/replay registration:

```renpy
init 5 python:
    gallery_auto("alice_roof_scene", character="alice")
```

Use explicit metadata when a scene belongs to multiple characters:

```renpy
gallery_auto("bree_cora_argument", characters=["bree", "cora"], group="Archive")
```

Unlock from story content:

```renpy
gallery_unlock alice_roof_scene
milestone archive_witness_bree
```

## Minigames

The minigame system is a starter wrapper. It lets a future game plug in mechanics while story content keeps one simple call.

```renpy
init 5 python:
    minigame(
        "lockpick_archive",
        label="lockpick_archive_game",
        skip_label="lockpick_archive_skip",
        skip_result="win",
        requires="item:lockpick",
        fail_forward=True,
    )
```

Start it from content:

```renpy
$ result = start_minigame("lockpick_archive")
if minigame_result("lockpick_archive") == "win":
    $ set_flag("archive_room_unlocked")
```

Accessibility/story builds can skip minigames:

```renpy
$ set_minigame_skip_mode(True)
```

Validation checks minigame labels, skip labels, requirements, and `fail_forward` values.

## Systems And Toggles

Mechanics should gate themselves centrally. Content should not scatter checks everywhere.

```renpy
$ system_enabled("quests")
$ set_system_enabled("inventory", False)
$ set_system_enabled("stamina", True)
```

Use this when making a template preset or disabling mechanics for a different game style.

## Validation And Save Migrations

Use validation when a tool, startup hook, or debug screen needs to inspect the project without depending on LiveStudio.

```renpy
$ issues = project_tac_validation_issues()
$ report = project_tac_validation_report()
```

Register extra validators from project code:

```renpy
init 5 python:
    def validate_my_route_data():
        issues = []
        if "alice" not in character_stats:
            issues.append("Alice route requires character id 'alice'.")
        return issues

    register_project_tac_validator(validate_my_route_data)
```

Built-in validators currently cover the engine descriptor, character stats, moods, perks, schedules, story routes, branches, areas, locations, exits, hotspots, interactable actions, quest definitions and targets, inventory items/recipes/use rules, gallery entries, phone apps/notes/contacts, achievements, milestones, and minigames.

When you rename shipped content, add migration rules before players load old saves:

```renpy
init -5 python:
    rename_flag("old_intro_done", "intro_done")
    rename_item("rusty_key", "archive_key")
    rename_quest("old_archive_quest", "archive_keyhunt")
    rename_objective("archive_keyhunt", "old_key_step", "key")
    rename_player_stat("Charm", "Charisma")
    rename_character_stat("affection", "love")
```

Then bump `SAVE_MIGRATION_VERSION` in `Engine/State/Migrations.rpy`. The migration pass runs on start and after load.

## Player Data

Player name and color are runtime customization data. Use the player handle for player stats:

```renpy
$ player.Coolness += 1
$ stat("player", "Strength", 1)
```

When writing display text, use the project variables already wired into the name system rather than hardcoding a player name.

## LiveStudio Workflow

LiveStudio is an authoring tool, not runtime dependency.

1. Open with `Shift+L`.
2. Use Project Tac tools to inspect characters, quests, locations, items, and source-backed UI.
3. Generate a source plan.
4. Review the diff and validation messages.
5. Apply planned changes only when the preview is marked safe.

The Project Tac extension reads the runtime descriptor in `Engine/Core/Project_Tac_Descriptor.rpy`. If a data file moves, update the descriptor first so LiveStudio writes to the correct place.

## Common Labels

Exploration labels should usually end with:

```renpy
jump explore
```

Dialogue labels should usually:

```renpy
$ begin_dialogue("alice")
...
$ end_dialogue()
jump explore
```

Item-use labels can accept optional arguments:

```renpy
label use_archive_key(item_id=None, target=None):
    ...
    jump explore
```

## Small Complete Example

Data:

```renpy
init 5 python:
    define_item("strange_badge", name="Strange Badge", tags=["evidence"])

    side_quest(
        "badge_mystery",
        title="The Strange Badge",
        description="A badge is hidden near the archive door.",
        discoverable=True,
        unlock_when="quest_done:noticeboard_check",
        target={"item": "strange_badge", "location": "hallway"},
        objectives=[
            step("find", "Find the strange badge", flag="got_strange_badge"),
            step("ask", "Ask Alice about the badge", flag="asked_alice_badge"),
        ],
    )
```

Location:

```renpy
location_package(
    "hallway",
    items=[
        item_spot(
            "strange_badge",
            pos=(0.44, 0.8),
            requires="quest_discovered:badge_mystery",
            hide_flag="got_strange_badge",
        ),
    ],
)
```

Content:

```renpy
label pickup_strange_badge:
    $ add_item("strange_badge")
    $ set_flag("got_strange_badge")
    "You pocket the badge."
    jump explore

label alice_badge_question:
    $ begin_dialogue("alice")
    a "Where did you find that?"
    $ set_flag("asked_alice_badge")
    $ alice.trust += 1
    $ end_dialogue()
    jump explore
```

That is the main loop: define, place, write, flag.
