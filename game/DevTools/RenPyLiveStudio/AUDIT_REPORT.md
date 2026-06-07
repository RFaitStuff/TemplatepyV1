# Architecture and compatibility audit — v3.2

## Main architecture

The build remains at 13 primary `.rpy` files. Animation is isolated and disabled.

```text
LiveStudio_config.rpy       configuration and property definitions
LiveStudio_models.rpy       JSON-safe project data
LiveStudio_project.rpy      inheritance, commands, caches, history, save/load
LiveStudio_scene.rpy        scene-list capture and scene editing
LiveStudio_ui.rpy           screen/widget hierarchy, values, managed UI/actions
LiveStudio_dialogue.rpy     scene-owned dialogue and choices
LiveStudio_capture.rpy      non-destructive runtime capture
LiveStudio_flow.rpy         frame graph and conservative source preview
LiveStudio_export.rpy       generated code, validator, copy/export
LiveStudio_assets.rpy       source-folder asset tree and thumbnails
LiveStudio_canvas.rpy       visual preview, hit testing, direct manipulation
LiveStudio_screens.rpy      original-inspired editor shell
LiveStudio_bootstrap.rpy    shortcut and context-safe startup
```

## Scene and UI boundary

Scene capture ignores UI-only Ren'Py layers and skips `ScreenDisplayable` objects. UI capture separately finds active screens and recursively records their screen/container/widget hierarchy. This prevents fake empty Scene containers while keeping the UI available under its own tree and layer mode.

## Connected UI model

A UI Screen owns root nodes. Containers own children. Anonymous engine wrappers are flattened only when they do not carry an ID, action, or meaningful standalone content. Meaningful frames, text, buttons, images, and containers remain connected.

Naming priority is:

1. explicit screen-language widget ID;
2. text source expression or visible text;
3. image name;
4. child label for frames/buttons;
5. runtime type as a final diagnostic fallback.

## Dynamic text model

Text nodes carry a binding record:

```text
mode
expression
source_expression
preview
```

`preview` is what was visible during capture. `source_expression` is the original screen-language expression where available. Export uses the expression for dynamic text and the literal preview only for literal text.

## Direct manipulation

The canvas uses one persistent displayable. During drag, a transient property overlay is applied to the selected resolved node. It does not mutate project data until mouse-up.

- Scene images are rebuilt in the editable layout using the transient transform.
- Managed UI is laid out from its parent hierarchy.
- Captured UI widgets with IDs are rebuilt through screen widget-property overrides.
- Selection, bounds, and the actual editable visual consume the same transient values.

## Performance changes

The expensive path in earlier builds was repeated deep copying and screen reconstruction from ordinary screen expressions and input callbacks. v3.2 separates caches for resolved frame state, flattened canvas items, measured bounds, widget overrides, screen previews, semantic displayables, layer thumbnails, asset rows, and asset thumbnails.

Property fields update the current cached resolved state during typing. Descendant frame caches are discarded when the field edit is committed. This keeps inherited correctness while avoiding a complete 900-node tree clone for every character.

## Limitations retained deliberately

- A captured widget without a stable ID cannot reliably receive a Ren'Py widget override.
- Runtime evaluation does not preserve every original loop, `if`, `use`, Python closure, or custom displayable constructor.
- Converting to a managed copy is the dependable no-code path for full editing/export.
- Handwritten-source patching and editor-block replacement remain experimental.
