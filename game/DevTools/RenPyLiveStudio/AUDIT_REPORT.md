# Architecture and compatibility audit

## Final architecture

The main build contains 13 `.rpy` files. Responsibilities are grouped without splitting every small class into its own file:

```text
LiveStudio_config.rpy       configuration and compatibility boundary
LiveStudio_models.rpy       JSON-safe Project/Frame/Scene/UI/Dialogue models
LiveStudio_project.rpy      inheritance resolver, operations, history, save/load
LiveStudio_scene.rpy        scene-list capture and scene object editing
LiveStudio_ui.rpy           screen/widget capture, managed UI, button actions
LiveStudio_dialogue.rpy     scene-owned dialogue and menu logic
LiveStudio_capture.rpy      non-destructive runtime capture lifecycle
LiveStudio_flow.rpy         frame graph and conservative source-AST preview
LiveStudio_export.rpy       generated code, validators, copy/export, experiments
LiveStudio_assets.rpy       image/audio browser index
LiveStudio_canvas.rpy       preview, hierarchy bounds, hit testing, transforms
LiveStudio_screens.rpy      editor shell and panels
LiveStudio_bootstrap.rpy    shortcut and context-safe startup
```

Animation is isolated under `optional/animation/` and disabled.

## ActionEditor3 boundary

ActionEditor3 is an animation/transform editor whose scene number and timeline are built around keyframes. Live Studio uses only the proven architectural idea of reading Ren'Py scene lists and opening a tool in a separate context.

Live Studio Frames are story-state nodes. Animation code is not included in the main build and does not control the project model.

## Runtime capture lifecycle

1. Shift+L records the original game source reference and exact screenshot.
2. A new Python context is created with `_clear_layers=False`.
3. The copied scene lists are inspected without calling `renpy.scene()` on the game.
4. Images and loose displayables become Scene nodes.
5. Active `ScreenDisplayable` instances become runtime-only Screen records.
6. Their root children are recursively traversed into a widget hierarchy.
7. Live displayable references remain in the temporary runtime cache only.
8. The modal editor covers the game.
9. Closing the editor discards the tool context and returns to the untouched game context.

## UI editability levels

- **Editable:** stable widget ID and supported managed type.
- **Limited:** some properties/actions can be recovered, but not the full source meaning.
- **Inspect:** visible hierarchy/bounds only.

Captured screens can be converted into managed copies. The converter creates unique widget IDs and preserves supported hierarchy, properties, and structured actions.

## Frame inheritance

An inherited Frame stores operations rather than duplicating the complete visual state:

- `sets` — local property changes.
- `adds` — new scenes, nodes, screens, controllers, or events.
- `removes` — hidden/removed inherited objects.
- `reorders` — local ordering changes.

Resolution recursively combines the parent state with the local operations. Blank and Detached frames are explicit alternatives.

## Dialogue separation

The Dialogue object belongs to a Scene and contains reusable events. Each Frame stores an ordered event queue with multiple commands and at most one interaction.

Say and Choice screens remain UI definitions. A Choice interaction may include an optional speaker/narration prompt and choices in the same Ren'Py menu interaction.

## Export policy

Default behavior is preview/copy only. File output requires an explicit button and creates new timestamped files. Existing-source modifications remain experimental.

The validator checks the editor model before output, but raw Ren'Py statements and arbitrary custom displayables still require SDK lint/runtime testing.
