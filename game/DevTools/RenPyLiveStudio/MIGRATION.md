# Migration from the original SceneEditor

## 1. Back up the project

Make a copy or Git commit before replacing the old editor.

## 2. Disable the original files

Rename these files so they no longer end in `.rpy`, or move them outside `game/`:

```text
SceneEditor.rpy
SceneEditor_screens.rpy
SceneEditor_config.rpy
SceneEditor_image_browser.rpy
SceneEditor_action_core.rpy
```

Do not load the old and new editors together. They use different project models, shortcuts, state, and capture lifecycles.

## 3. Install Live Studio

Copy the final `RenPyLiveStudio` directory into:

```text
your-project/game/RenPyLiveStudio/
```

Launch the game normally from the Ren'Py SDK Launcher. Press **Shift+L** during a scene.

## 4. First tests

Test in a copy of the project:

1. Open during normal dialogue.
2. Open while a choice menu is visible.
3. Open during exploration with HUD and clickable buttons.
4. Switch between Exact and Editable previews.
5. Select nested UI children in the hierarchy.
6. Convert a captured screen to a managed copy.
7. Add a Say UI and Choice UI template.
8. Create an inherited next frame and change only one image/dialogue event.
9. Add a choice and target branch frames.
10. Review all three Export sections.
11. Save and reload the Live Studio JSON project.
12. Run **Ren'Py Launcher → Lint**.

## 5. Project data

Live Studio saves editor projects under:

```text
game/live_studio_projects/
```

It does not automatically migrate the old ActionEditor/SceneEditor persistent state. Capture the running scene again or start a blank Live Studio project.

## 6. Export safety

The default Export workspace only generates previews and copies text.

- **Export Files** is explicit and writes a new timestamped directory.
- Editor-owned block replacement is experimental and disabled.
- Handwritten-file patching is experimental and disabled.
- Both experimental paths create backup files when enabled.

## 7. Shipping

Before distributing a game, remove the Live Studio folder or set:

```python
ENABLED = False
```

in `LiveStudio_config.rpy`.
