# Ren'Py Live Studio - Visual Engine v3.6.0

Ren'Py Live Studio is an in-game visual authoring tool for Ren'Py. It captures the current running game, opens a modal editor over it, and lets you create inherited story frames, scene visuals, UI screens, dialogue, choices, button behavior, and flow without having to hand-write the initial Ren'Py script.

## Start it

1. Replace the previous `RenPyLiveStudio` folder with this complete folder.
2. Launch the project normally.
3. Reach the scene you want to edit.
4. Press **Shift+L**.

Disable `ENABLED` in `LiveStudio_config.rpy`, or remove the folder, before shipping a public build.

## Extension layer

Live Studio has a lightweight extension registry. The core editor stays portable for normal Ren'Py projects, while project-specific engines can add their own bottom-workspace tab, commands, validation, and generated code snippets.

The bundled Project Tac extension appears only when the current project exposes `project_save_id = "project_tac"`. It can refresh Project Tac registries, validate quest targets, generate `location_package`, `object_spot`, `create_quest`, dialogue, branch, and parallax-ready snippets, and turn the selected canvas bounds into an editable interactable starter.

This keeps the base editor useful for almost any Ren'Py project while letting Project Tac behave more like a game-design engine layered on top of the normal Ren'Py runtime.

## Project model

```text
Project
â””â”€â”€ Frame
    â”œâ”€â”€ Scenes
    â”‚   â”œâ”€â”€ Master / Exploration
    â”‚   â”œâ”€â”€ Dialogue
    â”‚   â””â”€â”€ Effects / custom scene layers
    â”œâ”€â”€ Dialogue object
    â””â”€â”€ UI screens
```

A Frame is a story state, not an animation timestamp. The normal **Next Frame** operation inherits the current frame and stores only local differences.

The Dialogue object belongs to a Scene. It stores ordered commands and the current interaction. Say and Choice screens are separate UI definitions that control appearance.

## v3.3 editor layout

The editor shell now follows the supplied modern dark mockup while retaining the original tool's working project and creation controls:

- **Top bar:** fit-aware zoom controls, workspace switcher, Save, Project, Preview, Extract Script, Settings, and Close.
- **Left:** context-sensitive Properties above a Scene Tree that still switches between complete Scene and UI hierarchies. There is intentionally no Scene Tree search field.
- **Center:** the live canvas, with a dedicated Frames strip directly below it.
- **Frames strip:** Previous, source-aware Next, inherited-frame insertion, blank-frame insertion, and frame count.
- **Right upper:** Layers, History, and Inspector. Layers keep separate Scene/UI modes, thumbnails, visibility, locking, ordering, deletion, and the Add menu.
- **Bottom center:** a Unity-style Assets browser with only **Images** and **Audio** as top-level categories. Real project folders provide character/background/UI organization without duplicate tabs. Grid and list views are available.
- **Bottom right:** Select, Move, Scale, Rotate, object editing, arrangement, locking, undo/redo, and a compact Add popup that preserves the original Scene/UI/dialogue/frame creation commands.
- **Popups:** Project, Settings, Create, and Extract Script open over the editor instead of replacing the asset workspace.

All editor scrollbars remain narrow, and the layout scales from common 1280Ã—720 projects through 1920Ã—1080 projects.

## v3.3 future-frame discovery

Live Studio now stores a JSON-safe AST node key alongside the normal source filename and line. Future-state discovery first resolves the interaction represented by the current frame, then walks from its successor. This corrects the common dialogue case where Ren'Py's runtime context already points at the next node and the old implementation accidentally skipped that first future line.

The frame bar behaves as follows:

- A stored project edge/frame is opened normally.
- One statically discoverable future interaction becomes **Import Next**.
- Multiple menu/condition branches become **Choose Future** and are listed in the right-side Inspector.
- Branch placeholder frames include their first branch interaction instead of skipping it.

This remains a conservative static preview. Dynamic Python expressions, runtime-computed jumps, and arbitrary custom statements are not executed by the editor.

## v3.2.2 interaction hotfix

- Captured labels are escaped before Ren'Py interpolation, so incomplete dynamic text cannot crash the hierarchy, layers, dialogue list, assets, or generated-code preview.
- Fixed the UI Layers button falling back to Scene mode. Scene and UI modes are synchronized across the hierarchy and Layers panel, and only the active domain can be selected or transformed on the canvas.
- Locked objects cannot be canvas-selected.
- Re-selecting the current item and clicking without moving no longer restart the editor or add no-op history.
- Frame switches enter Editable Layout and refresh immediately instead of waiting for a canvas selection.
- Selection/panel restarts keep a continuous canvas animation clock instead of replaying entrance effects.
- Normal drag keeps the current selection when objects overlap; double-click selects the highest different object under the pointer.
- Resize keeps the opposite edge anchored, and rotation uses the measured object center.
- Inspector inputs keep a local typing buffer and commit on Enter, focus change, selection/frame change, save, or close.
- **Script** is now a top-bar popup; it is no longer an Assets-area tab.
- **Preview** is intentionally a no-op notification until full-scene preview is implemented; Exact/Editable controls remain in Debug.

## v3.2 fixes

### Direct scene and UI manipulation

- **Select mode now drags objects**, matching the original editor.
- Beginning a move/resize/rotate automatically switches the static Exact Capture to Editable Layout, so the visual objectâ€”not only its selection outlineâ€”follows the pointer.
- The selection outline, actual scene image, and editable UI widget use the same transient drag state.
- Corner/edge handles resize from the selected side.
- The upper handle rotates.
- Dragging does not rewrite or deep-resolve the project on every mouse-motion event; one change is committed on mouse-up.
- Captured widgets with stable Ren'Py `id` values are moved through widget-property overrides, so the actual isolated screen preview moves rather than only its outline.
- Unnamed captured widgets remain connected to their parent but require **Convert to Managed Copy** for dependable editing/export.

### Scene/UI separation

- `screens`, `overlay`, `transient`, and `top` are no longer created as empty Scene containers.
- Active screens appear only under the UI hierarchy and UI Layers.
- Old empty `Layer: transient`, `Layer: screens`, `Layer: overlay`, and `Layer: top` records are removed during JSON loading and in-memory autoreload migration.
- Scene Layers and UI Layers are separate views.
- UI children remain nested beneath their real screen/container hierarchy.
- Explicit widget IDs become readable names such as `Time Text`; anonymous text/buttons use their source expression or visible label where recoverable.
- Anonymous runtime transforms and helper displayables are flattened instead of appearing as dozens of `Custom` entries.

### Dynamic text/value compatibility

Captured text stores both:

- its current preview value, and
- the original screen-language expression where Ren'Py exposes it.

For example, a HUD statement such as:

```renpy
text "[weekday_name()]"
```

is kept as the dynamic Ren'Py text value instead of being frozen to `Monday`. The Inspector shows **Text** versus **Value** source modes, a read-only current preview for dynamic text, and the preserved value/expression used by export.

### Properties

- Compact input boxes from the original interface are restored.
- X/Y and width/height fields are paired.
- Position, size/layout, text, appearance, and button-image groups are collapsible.
- Inherited values show a revert button.
- Property typing stays in a local field buffer and creates one field-level undo entry when committed, rather than rebuilding a large captured UI tree per character.

### Assets

- A Unity-style folder tree is built from the real source paths behind registered Ren'Py images and audio files.
- The right side shows only the current folder or search results.
- Images and Audio are the only top-level categories; character, background, GUI, and other organization comes from the actual source-folder tree.
- Search is applied on Enter or the Search button, not on every keystroke.
- Thumbnails are lazy, paged, cached, and failure-isolated.
- Ren'Py's parameterized `text` image and other non-previewable registered images remain filtered.

### Performance

- Resolved inherited frames are revision-cached.
- Inspector typing reuses the current resolved object, including frames with very large UI trees.
- Canvas objects, bounds, widget overrides, source displayables, tree rows, asset folders, and thumbnails have separate caches.
- Canvas selection does not recreate the canvas displayable.
- Captured screens are rebuilt only when their own editable widget changes.
- Thumbnail transforms are constructed once and kept out of the main `per_interact` visit tree.
- The exact capture remains the default preview; the editable layout is built only when requested or when an object is edited.
- Full grid and all-widget bounds remain opt-in Debug overlays.

## Existing handwritten screens

Existing screens are captured as runtime UI records. Live Studio shows their hierarchy and attempts to reproduce their visuals in an isolated preview.

- Widgets with stable screen-language IDs can receive visual overrides.
- Unsupported or unnamed children are limited/inspect-only.
- **Convert to Managed Copy** creates an editor-owned hierarchy with unique IDs for full export.
- Arbitrary Python-created displayables, loops, conditions, custom actions, and complex `use` behavior cannot always be perfectly reconstructed from the evaluated runtime tree.

## Export

The normal workflow remains copy-first:

1. Open **Extract Script**.
2. Review `story.rpy`, `screens.rpy`, and `live_studio_helpers.rpy` separately.
3. Copy the section you want.

Nothing is written automatically. **Export Files** explicitly writes a timestamped folder under:

```text
game/live_studio_exports/
```

Editor-owned block replacement and handwritten-source patching remain experimental and disabled by default.

## Animation

Animation is intentionally excluded from the main build. The disabled integration boundary remains under `optional/animation/`.

## Required real-project check

This build was Python-compiled, source-flow mock-tested, screen-expression checked, and compatibility-audited, but your project must still be tested in the real Ren'Py 8.5.3 nightly runtime. Run Launcher **Lint**, then test Live Studio during exploration, dialogue, and a choice menu.
