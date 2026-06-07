# Ren'Py Live Studio — Visual Engine Build v3

Ren'Py Live Studio is an in-game visual authoring tool for Ren'Py. It captures the current running game, opens a modal editor over it, and lets you build story frames, scene visuals, UI screens, dialogue, choices, button behavior, and flow without manually writing the initial Ren'Py code.

## Start it

1. Copy the `RenPyLiveStudio` folder into your project's `game/` directory.
2. Launch the project normally from the Ren'Py SDK Launcher.
3. Reach the scene you want to edit.
4. Press **Shift+L**.

No manual `config.developer = True` setting is required. Live Studio is enabled by its own `ENABLED` setting in `LiveStudio_config.rpy`.

Disable `ENABLED` or remove the folder before shipping a public build.

## Project model

```text
Project
└── Frame
    ├── Scenes
    │   ├── Master / Exploration
    │   ├── Dialogue
    │   └── Effects / custom layer scenes
    ├── Dialogue object
    └── UI screens
```

A Frame is a story/game state, not an animation timestamp. New frames inherit the previous frame and store only local changes unless Blank or Detached is selected.

The Dialogue object belongs to a Scene. It stores ordered commands plus one main interaction for the frame. Say and Choice screens are separate UI templates that control appearance.

## Editor layout

- **Top:** project, frame navigation, undo/redo, preview, save, and export tools.
- **Left upper:** context-sensitive Inspector.
- **Left lower:** frame hierarchy split into Scene and UI.
- **Center:** visual canvas with selection, move, resize, rotate, snapping, and exact/editable preview modes.
- **Bottom:** Assets, Dialogue, Next Source, Export, and Diagnostics workspaces.
- **Right:** creation, selection, and frame tools.

## Main features

- Non-destructive capture of the active scene lists and screens.
- Exact pre-editor screenshot fallback.
- Scene image capture by Ren'Py layer.
- Active screen and recursive widget-tree inspection.
- Widget IDs and properties where Ren'Py exposes them.
- Inspect-only fallback for unnamed or unsupported runtime children.
- Conversion of captured screens into managed editor-owned copies.
- Ready-made managed Say UI and Choice UI templates.
- Managed text, images, buttons, image buttons, frames, and containers.
- Structured button actions and visual frame destinations.
- Inherited frames, branches, blank frames, and detached snapshots.
- Scene-owned dialogue with say, narration, menu prompts, choices, Python commands, raw Ren'Py statements, images, screens, transitions, audio, pause, jump, call, and return events.
- Conservative inspection of likely next Ren'Py dialogue/menu/pause states from the current AST.
- Choice imports create inherited branch-frame placeholders.
- Separate generated previews for `story.rpy`, `screens.rpy`, and `live_studio_helpers.rpy`.
- Copy-first export. Nothing is written until **Export Files** is pressed.
- Project JSON save/load.
- Experimental editor-owned block replacement and handwritten-file patching remain disabled by default.

## UI compatibility model

Existing handwritten screens are captured as runtime screens. Live Studio attempts to show their real visuals and hierarchy while keeping their runtime objects temporary.

- Widgets with stable screen-language `id` values can expose editable properties.
- Unnamed children remain inspect-only or limited.
- **Convert to Managed Copy** creates an editor-owned screen that can be exported.
- Arbitrary loops, conditions, `use` statements, Python-created displayables, and custom actions cannot always be reconstructed from the evaluated runtime tree. Live Studio does not pretend those are perfectly editable.

## Export behavior

The default workflow does not modify project files:

1. Open the **Export** workspace.
2. Review each generated section.
3. Use **Copy Current** to paste it where you want.

**Export Files** explicitly writes a timestamped folder under:

```text
game/live_studio_exports/
```

The generated sections are:

- `story.rpy` — inherited frame differences, dialogue, choices, flow, and active screens.
- `screens.rpy` — editor-owned UI and scene overlays.
- `live_studio_helpers.rpy` — inferred Character definitions, widget overrides, and helper actions.

## Animation

Animation is intentionally excluded from the main build. The disabled boundary is under `optional/animation/`. Project Frames remain story states. A later animation module should attach timelines to individual scene nodes.

## Important limitation

This package has been statically audited and model-tested, but must still be run through the Ren'Py Launcher **Lint** command and tested with your project's custom screens. Runtime screen structures can vary greatly between projects.

See `VALIDATION.md`, `AUDIT_REPORT.md`, and `MIGRATION.md` before replacing the old editor.
