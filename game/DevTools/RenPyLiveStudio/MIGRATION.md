# Migration from the original SceneEditor files

Do not load the old and new implementations together. Temporarily move or rename these old files so they no longer end in `.rpy`:

- `SceneEditor.rpy`
- `SceneEditor_screens.rpy`
- `SceneEditor_config.rpy`
- `SceneEditor_image_browser.rpy`
- `SceneEditor_action_core.rpy`

Then copy this folder into `game/RenPyLiveStudio/`.

## Responsibility changes

| Previous file | New location |
|---|---|
| `SceneEditor_config.rpy` | `LiveStudio_config.rpy` |
| Project/frame/UI/dialogue globals in `SceneEditor.rpy` | `LiveStudio_models.rpy`, `LiveStudio_project.rpy`, `LiveStudio_dialogue.rpy` |
| Destructive ActionEditor-based capture | `LiveStudio_capture.rpy`, `LiveStudio_scene.rpy`, `LiveStudio_ui.rpy` |
| Flat simulated UI records | Hierarchical UI screen/widget records in `LiveStudio_ui.rpy` |
| Monolithic editor screen | `LiveStudio_screens.rpy` |
| Image browser logic | `LiveStudio_assets.rpy` |
| Draft exporter | `LiveStudio_export.rpy` |
| ActionEditor animation/keyframes | Excluded; future adapter boundary under `optional/animation/` |

## Deliberately removed

- Clearing the game's active layers when the editor opens.
- Persisting live `ScreenDisplayable` objects in project data.
- Project-specific fake HUD reconstruction.
- Treating ActionEditor animation timestamps as story frames.
- Exporting UI as comments only.
- Automatically writing generated files as the default export action.

## Project-specific scene grouping

Override the default scene group map in a separate project file loaded at a later init priority:

```renpy
init -800 python in live_studio:
    SCENE_GROUPS = OrderedDict([
        ("Exploration", ("master",)),
        ("Dialogue", ("characters", "dialogue", "menu")),
        ("Effects", ("effects",)),
    ])
```

Keep that project-specific configuration outside the Live Studio package so updates do not overwrite it.
