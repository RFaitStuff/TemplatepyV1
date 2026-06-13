# Project Tac â€“ Author Cheat Sheet

Use this when writing content. Sections are ordered by the things you touch most often.

For the full gameplay authoring reference, including locations, quests, items,
interactables, branches, requirements, gallery, minigames, and LiveStudio flow,
see `GAMEPLAY_AUTHORING_TUTORIAL.md`.

---

## 1. Dialogue & Scene Quickstart

### 1.1 Minimal flow
```renpy
label alice_chat:
    $ begin_dialogue("alice")
    $ show_npc("alice")                # auto pose/spot/zoom
    a "Hey. You needed me?"

    $ menu_side("left")                # or menu("middle"):
    menu:
        "Ask about practice.":
            $ stat("alice", "trust", 1, "3d")
            $ mood("alice", "happy", 4)
            a "It went better than last time."
        "Push her too far.":
            $ set_status("alice", "tired", True)
            $ set_reaction("alice", "embarrassed")
            $ react("alice", "embarrassed")
            a "Can we not do this here?"
            $ react("alice")
    $ end_dialogue()
    jump explore
```

### 1.2 Stats, moods, statuses, reactions
- Relationship stats: `stat(char, stat_name, amount, cooldown_tokens...)`. Cooldowns = `"3d"`, `"3da"`, `"no"`, `"noa"`.
- Shorthand (no cooldowns):
  ```renpy
  stat alice love +1
  stat Alice, Love +1
  stat alex trust -1
  ```
- Mood axes (0â€“15): `happy`, `sad`, `angry`, `nervous`.
  ```renpy
  $ mood("alice", "happy", 3)
  $ set_mood("alice", "sad", 8)
  $ add_mood("alice", "angry", -2)
  $ mood("alice", "neutral")         # clear all
  mood Alice happy +3 duration=2
  react Alice embarrassed
  react Alice
  ```
- Statuses (`tired`, `sick`, `hurt`) + reactions (`embarrassed`, `jealous`, `shy`, `confused`, `confident`):
  ```renpy
  $ set_status("alice", "tired", True)
  $ clear_status("alice", "tired")
  $ set_reaction("alice", "confident")
  $ clear_reaction("alice")            # clear all
  ```
- Portrait overrides for a single line:
  ```renpy
  $ react("alice", "embarrassed")
  a "..."
  $ react("alice")                     # revert to mood-driven art
  ```

### 1.3 Facts, quests, and rewards directly from dialogue
```renpy
$ register_character_fact("alice", "favorite_place", "Favorite Place", "She loves the art room roof.")
...
$ unlock_character_fact("alice", "favorite_place")
$ set_flag("alice_picnic_offered")      # quest flag helper from Story_Flags
$ set_status("alice", "tired", False)  # reward cleanup
$ add_item("lunch_bento")               # Inventory helper
```
- Common helpers: `set_flag`, `clear_flag`, `has_flag`, `set_tracked_quest`, `toggle_tracked_character`.
- Writer shorthand:
  ```renpy
  flag alice_picnic_offered
  unflag temporary_hint_seen
  item lunch_bento +1
  quest start alice_picnic
  quest progress alice_picnic meet
  quest clear_track
  gallery_unlock alice_first_meet
  milestone started_story
  ```
- Use facts to populate the Characters screen; locked entries auto render as `???`.

### 1.4 Menus, placement, and polish
- Engine-aware character placement:
  ```renpy
  Show Alice
  Show Alice(side=Left)
  Show Alice(side=Right, emotion=happy)
  Hide Alice
  ```
- `menu_side("left" | "right" | "middle")` slides the dialogue cast smoothly via `_xalign_anim`.
- `menu("middle"):` syntax works as shorthand on supported Ren'Py versions.
- Dialogue defocus overlay keeps the room visible but softened. Toggle via:
  ```renpy
  define dialogue_defocus_enabled = True
  define dialogue_defocus_overlay = "#05070a70"
  ```

### 1.5 Time-based dialogue
```renpy
if weekday_name() == "Friday" and time >= 18:
    a "Finally the weekend."
else:
    a "Try me when the sun's down."
    return
```
- Global vars: `time` (0â€“23), `day` (starting at 1 = Monday).
- Helpers from `Mechanics/Time_Stamina.rpy`:
  - `advance_hour(hours)` (also triggers mood decay, NPC schedules).
  - `on_hour_advance(fn)` for background systems.
  - `convert_to_12hr_format(time)`, `weekday_name(day=None)`.
- Queue stamina costs during dialogue with `queue_stamina_cost(amount)` and `flush_stamina_cost()` afterward.

---

## 2. Quests + Items (they travel together)

### 2.1 Register quests
```python
init python:
    char_quest(
        "alice_picnic",
        character="alice",
        title="Lunch with Alice",
        description="She wants to meet on the roof.",
        start_flag="alice_picnic_offered",
        objectives=[
            ("buy_food",   "Pick up lunch",      "got_lunch"),
            ("meet",       "Meet on the roof",   "lunch_with_alice"),
            ("dessert",    "Optional dessert",   "alice_dessert", True),
        ],
    )
```
- Trigger progress with `set_flag("got_lunch")` etc.
- Use `set_tracked_quest(qid)` or `toggle_tracked_quest(qid)` so the HUD objective updates.

### 2.2 Items that feed quests
```python
init python:
    define_item("lunch_bento", name="Lunch Bento", desc="Enough for two.", quest="alice_picnic")
```
- Add/remove/check inventory:
  ```renpy
  $ add_item("lunch_bento")
  if has_item("lunch_bento"):
      ...
  $ remove_item("lunch_bento")
  ```
- Location hotspots can drop items automatically while a quest flag is active (see section 3).

---

## 3. Locations
```renpy
init python:
    register_location(
        "roof",
        name="Rooftop",
        bg="bg_roof_day",
        area="school",
        order_after="club_room",
        unlocked=True,
        variants={"alice": ["", "1"]},
        positions={"alice": [(0.25, 1.0), (0.65, 1.0)]},
        on_enter="roof_first_visit",
        items=[
            {"item": "lunch_bento", "while_flag": "alice_picnic_offered", "label": "pickup_roof_lunch", "pos": (0.82, 0.68)},
        ],
    )
```
- `label roof_first_visit:` is optional onboarding and should end with `return`.
- Use `jump explore` after handling a clickable hotspot so the navigation loop continues.
- Exploration helpers:
  - `show_all_npcs_here()`, `npcs_here()`, `is_npc_here("alice")`.
  - `set_explore_npc_highlight(char_id, True/False)` for HUD pings.

---

## 4. Characters
- Every character entry lives in `Game/_Data/Characters.rpy`. `ensure_character_state(char)` fills in:
  - Relationship stats (`love`, `lust`, `trust`, `respect`).
  - Mood dict with the four axes (0-15).
  - Reaction tags + status tags (default False/0).
  - Fact registry + unlocked set.
- Schedule example:
  ```python
  character_schedules["alice"] = {
      "day": "homeroom",
      "afternoon": "art_room",
      "evening": "club_room",
      "night": "roof",
  }
  ```
- Handy accessors: `character_display_name`, `npc_location`, `set_tracked_character`, `clear_tracked_character`.
- `mline(char, default=..., happy=[...], tired=[...])` now checks mood, then reactions, then statuses.

---

## 5. Misc Add-ons (nice to have, not required)
- **Gallery scenes** (`Engine/Gallery.rpy`):
  ```python
  register_gallery_scene(
      gallery_id="ch2_rooftop",
      title="Chapter 2 - Rooftop",
      label="ch2_rooftop_replay",
      thumbnail="mainstory story2",
      character="alice",
      group="Main",
  )
  ```
- **Characters screen** pulls data automatically:
  - Relationship stats + mood graph + active statuses/reactions.
  - Facts column shows `???` until each fact is unlocked.
- **HUD tweaks** (`Engine/UI/HUD.rpy`): tune button sizes, objective visibility, tracked character markers.
- **Syntax sugar** (`Engine/Common/Syntax_Sugar.rpy`): `stat alice love +1` statements for simple bumps.

---

## 6. Advanced / Systems Map
Use these files when you need to push beyond author scripting.

| Area | File(s) | Notes |
| ---- | ------- | ----- |
| User-authored characters | `Game/_Data/Characters.rpy`, `Game/_Data/Character_Schedules.rpy`, `Game/Content/Dialogue/Talk/*.rpy`, `Game/Content/Dialogue/Interact/*.rpy` | Character data, schedules, talk labels, and meaningful interaction labels are split so new content is easy to add. |
| Character engine | `Engine/Characters/Character_System.rpy`, `Engine/Dialogue/Dialogue_Registry.rpy` | Reusable character state helpers, stat rewards, facts, dialogue selection, and interaction routing. |
| User-authored world | `Game/_Data/Areas_Locations.rpy`, `Game/Content/Interactions/<Area>/*.rpy` | Location registration stays separate from per-location items, NPC positions, exits, and hooks. |
| Location engine | `Engine/World/Location_System.rpy`, `Engine/World/Location_Package.rpy`, `Engine/UI/Locations.rpy` | Registry helpers, room packages, navigation state, background lookup, and exploration screen UI. |
| Dialogue layer & blur | `Engine/Dialogue/Dialogue_Handler.rpy`, `Engine/UI/Choice.rpy`, `Engine/UI/Say.rpy` | Dialogue-only sprite layer, menu displacement animation, dialogue box styling. |
| Mood engine & reacts | `Mechanics/Mood.rpy` | Four-axis model, incompatibility matrix, auto decay, `react()` overrides. |
| HUD & overlays | `Engine/UI/HUD.rpy`, `Engine/UI/Screens.rpy` | HUD icons, objective pin toggle, fullscreen Characters UI, quest log. |
| Exploration UI | `Engine/UI/Locations.rpy`, `Engine/Images/Show_NPC.rpy` | Hotspots, reveal mode, NPC highlight syncing. |
| Time & stamina | `Mechanics/Time_Stamina.rpy` | Hour advance, stamina drain, skip-hour button, forced sleep from 2 AM until morning. |
| System gates | `Engine/Core/System_Toggles.rpy` | Toggle systems on/off and define time-sensitive quest locks that block time skip, stamina, and unrelated interactions. |
| Validation & migrations | `Engine/Core/Validation.rpy`, `Engine/State/Migrations.rpy` | Runtime-safe validation facade plus save-compatible renames for flags, items, quests, objectives, and stats. |
| Quests | `Mechanics/Quest/Quest_Runtime.rpy`, `Mechanics/Quest/Quest_Guide.rpy`, `Game/_Data/Quests.rpy` | Quest engine is separate from quest definitions. Quest targets can use `time_sensitive`, `locks_time`, `allowed_interactables`, and `lock_message`. |
| Inventory & items | `Mechanics/Inventory/Inventory.rpy`, `Game/_Data/Items.rpy` | Item registry, add/remove hooks, use-on-target rules, crafting, and quest tagging. |
| Flags & story state | `Engine/State/Story_Flags.rpy` | `set_flag`, `clear_flag`, `has_flag`, story routing helpers. |
| Folder map | `Engine/`, `Mechanics/`, `Game/`, `assets/` | Keep feature code near its domain. |

Use Ren'Py Lint after editing to validate creator-defined statements and screen syntax.
