# Migration / update instructions — v3.2

## Replace, do not merge

Delete the previous `RenPyLiveStudio` directory and replace it with this complete folder. Do not merge individual files from v3.1 and v3.2.

After replacement, fully close and relaunch the project from the Ren'Py SDK. Autoreload can retain old displayable classes, keymap actions, and runtime caches.

## Recommended location

```text
your-project/game/DevTools/RenPyLiveStudio/
```

The folder may also be directly under `game/`, but use one location only.

## Disable the original editor

Rename or move these old files so they no longer end in `.rpy`:

```text
SceneEditor.rpy
SceneEditor_screens.rpy
SceneEditor_config.rpy
SceneEditor_image_browser.rpy
SceneEditor_action_core.rpy
```

Do not load the old and new editors together.

## Existing Live Studio projects

v3/v3.1 JSON projects remain loadable. Migration now:

- upgrades the project model to version 7;
- removes empty `Layer: transient`, `Layer: screens`, `Layer: overlay`, and `Layer: top` scenes;
- marks anonymous runtime custom/transform wrappers as internal;
- adds dynamic text binding/source fields;
- preserves inherited frames, dialogue queues, and managed screens.

The same migration is applied to an in-memory project retained by autoreload.

## First test checklist

1. Launch normally from the SDK and press **Shift+L**.
2. Confirm the Scene tree contains actual scene groups only.
3. Switch to UI and expand the HUD screen; verify frames/text/buttons are nested.
4. Confirm anonymous `Custom` rows are absent or limited to genuinely named custom widgets.
5. With **Select**, drag a scene image and verify the image—not only its outline—moves.
6. Drag a captured UI widget that has an ID and verify the isolated screen preview moves.
7. Convert an unnamed/limited screen to a managed copy and drag its children.
8. Test edge resize and rotate handles.
9. Select dynamic HUD text and verify the Inspector shows the current preview plus its saved value/expression.
10. Browse assets using the folder tree and search.
11. Create an inherited next frame and confirm unchanged content remains inherited.
12. Save/reload the Live Studio project.
13. Review all three Script outputs.
14. Run **Ren'Py Launcher → Lint**.

## Export safety

The default Script workspace only generates previews and clipboard content. **Export Files** is explicit. Handwritten-file patching and editor-owned block replacement are still experimental and disabled.

## Shipping

Remove the tool folder or set `ENABLED = False` in `LiveStudio_config.rpy` before distribution.
