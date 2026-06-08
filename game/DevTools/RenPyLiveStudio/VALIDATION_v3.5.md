# Validation v3.5.0

Validation performed outside a complete Ren'Py game runtime:

- All embedded `init python` blocks compile as Python.
- Screen definitions are unique.
- Screen expressions reference available Live Studio symbols under source-level analysis.
- Scene groups do not contain Dialogue and UI/dialogue layers are excluded from Scene capture.
- Captured UI uses frozen runtime displayables and per-frame runtime preview bundles.
- Captured screen cache keys depend on UI override signatures, not unrelated Scene revisions.
- Active runtime screens are filtered from the UI hierarchy when their Frame capture bundle is inactive.
- Say/Choice presentation is retained as passive frozen canvas content while remaining outside Layers.
- HUD/root structural merge, neutral-wrapper filtering, stable structural IDs, default Quick Menu locking, and debugger report hooks are present.
- Asset search updates its committed query from `InputValue.set_text`.
- Export commits pending Inspector/Properties edits before generation.
- ZIP integrity and manifest hashes are checked after packaging.

Required in-project checks:

1. Open Live Studio during dialogue, move a Scene image, and verify HUD plus the current say screen remain visually unchanged.
2. Enter UI Layers and move an authored-id HUD widget. Its selection follows while dragging and the actual widget updates on mouse-up.
3. Resize and rotate that widget, then move a parent container and verify all descendant selection bounds move together.
4. Confirm HUD appears once as a folder, without HUD Root, dialogue defocus, inactive debugger, or prediction/helper nodes.
5. Confirm Quick Menu is visible but locked until unlocked in Layers.
6. Trigger a notification in normal gameplay, open Live Studio, and confirm it is captured only while active.
7. Delete a selected Scene/UI node and verify it disappears and selection clears immediately.
8. Type in Properties and Assets search, then save/export without clicking elsewhere; verify the typed values are used.
9. Open Debugger and use Copy Full Report; paste it into a text editor and verify the JSON section is complete.
10. Run Ren'Py Launcher Lint on the complete Project Tac project.

A rendered runtime test was not possible in this container because the full Ren'Py SDK/project executable is unavailable.
