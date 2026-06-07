# Ren'Py Live Studio — first refactor build

This folder is a clean, non-destructive foundation for an in-game Ren'Py scene/UI editor.

## Install

1. Back up the project.
2. Copy the `RenPyLiveStudio` folder into the game's `game/` directory.
3. Do **not** copy the old `SceneEditor_action_core.rpy` into this build.
4. Start the game with `config.developer = True`.
5. Press **Shift+L** while the game is displaying the state you want to capture.

The editor captures the current scene, active screens, dialogue/choice data, and an exact screenshot. It does not clear or replace the running game's layers.

## Model

```text
Project
└── Frame
    ├── Scenes
    │   └── Nodes (images, hotspots, Dialogue attachment)
    ├── UI Screens
    │   └── Widget tree
    └── Dialogue Controllers
        └── Events (say, narration, choice, script, navigation)
```

A new frame inherits its parent and stores only local changes. `Blank Frame` and `Duplicate and Detach` are explicit alternatives.

Dialogue content is owned by a Dialogue Controller attached to a scene. The `say` and `choice` screens remain separate UI screens.

## Export behavior

Export is preview-first:

- `story.rpy`
- `screens.rpy`
- `ui_overrides.rpy`

Each section can be copied independently. No file is written until **Export All Files** is pressed. Exports are written into `game/live_studio_exports/`.

The following remain experimental and disabled by default:

- Replacing marked editor-owned blocks.
- Patching existing handwritten files.

## Current first-build limitations

- The viewport uses an exact captured screenshot plus editable hierarchy bounds. This guarantees that existing UI visuals are visible even when a custom runtime screen cannot be reconstructed safely.
- Moving an object updates its editable bounds and exported properties, but the screenshot pixels do not repaint in real time yet.
- Runtime UI children without explicit `id` values are inspect-only and use generated names.
- Existing arbitrary Python actions are inspected, but only recognized/editor-created actions are safely editable.
- Source flow analysis beyond frame edges and ordinary next-frame order is not implemented yet.
- Generated source receives structural smoke checks, but final Ren'Py Launcher **Lint** validation is still required in the target project. Automatic reload is not yet included.
- Animation is intentionally excluded.

## Recommended screen IDs

Important widgets should have explicit IDs:

```renpy
screen hud():
    frame:
        id "time_panel"

        text current_time:
            id "time_text"
```

Explicit IDs let Live Studio retrieve widget properties and generate stable `_widget_properties` overrides.

## Files

The main build contains 13 `.rpy` files:

1. `LiveStudio_config.rpy`
2. `LiveStudio_models.rpy`
3. `LiveStudio_project.rpy`
4. `LiveStudio_scene.rpy`
5. `LiveStudio_ui.rpy`
6. `LiveStudio_dialogue.rpy`
7. `LiveStudio_capture.rpy`
8. `LiveStudio_flow.rpy`
9. `LiveStudio_export.rpy`
10. `LiveStudio_assets.rpy`
11. `LiveStudio_canvas.rpy`
12. `LiveStudio_screens.rpy`
13. `LiveStudio_bootstrap.rpy`
