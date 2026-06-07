# Ren'Py Live Studio — Visual Engine v3.2

Ren'Py Live Studio is an in-game visual authoring tool for Ren'Py. It captures the current running game, opens a modal editor over it, and lets you create inherited story frames, scene visuals, UI screens, dialogue, choices, button behavior, and flow without having to hand-write the initial Ren'Py script.

## Start it

1. Replace the previous `RenPyLiveStudio` folder with this complete folder.
2. Launch the project normally from the Ren'Py SDK Launcher.
3. Reach the scene you want to edit.
4. Press **Shift+L**.

No manual `config.developer = True` line is required. Disable `ENABLED` in `LiveStudio_config.rpy`, or remove the folder, before shipping a public build.

## Project model

```text
Project
└── Frame
    ├── Scenes
    │   ├── Master / Exploration
    │   ├── Dialogue
    │   └── Effects / custom scene layers
    ├── Dialogue object
    └── UI screens
```

A Frame is a story state, not an animation timestamp. The normal **Next Frame** operation inherits the current frame and stores only local differences.

The Dialogue object belongs to a Scene. It stores ordered commands and the current interaction. Say and Choice screens are separate UI definitions that control appearance.

## v3.2 editor layout

The shell follows the original editor's information hierarchy while supporting the newer frame/UI/dialogue model:

- **Top:** zoom, snap, save, project, preview, script, settings, and close.
- **Left upper:** context-sensitive Properties with compact editable text boxes.
- **Left lower:** current-frame hierarchy split between Scene and UI.
- **Center:** the dominant photo-editor-style canvas.
- **Below canvas:** inherited-frame navigation.
- **Right:** Scene Layers or UI Layers with hierarchy, thumbnails, visibility, and lock state; Structure, History, and Debug remain tabbed.
- **Bottom:** Unity-style project asset tree plus asset tiles, or the Dialogue/Script workspace.
- **Bottom right:** compact selection, creation, ordering, and frame tools.

All editor scrollbars use a narrow four-pixel style.

## v3.2 fixes

### Direct scene and UI manipulation

- **Select mode now drags objects**, matching the original editor.
- Beginning a move/resize/rotate automatically switches the static Exact Capture to Editable Layout, so the visual object—not only its selection outline—follows the pointer.
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
- Property typing updates the active resolved frame in place and creates one field-level undo entry after typing pauses, rather than rebuilding a large captured UI tree per character.

### Assets

- A Unity-style folder tree is built from the real source paths behind registered Ren'Py images and audio files.
- The right side shows only the current folder or search results.
- Images, audio, characters, backgrounds, and GUI categories remain available.
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

1. Open **Script**.
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

This build was compiled, model-tested, and compatibility-audited, but your project must still be tested in the real Ren'Py 8.5.3 nightly runtime. Run Launcher **Lint**, then test Live Studio during exploration, dialogue, and a choice menu.
