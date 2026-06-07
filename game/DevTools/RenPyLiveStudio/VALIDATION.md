# Validation report

## Automated checks completed

The final build was checked with a mocked Ren'Py 8.5.3 runtime and static tooling.

Passed checks include:

- Every embedded `init python` block compiles as Python.
- All modules initialize in Ren'Py init-priority order in the mock runtime.
- 100+ screen-language references to `live_studio.*` resolve to implemented names.
- Frame inheritance and local property overrides.
- Blank, detached, inherited, and terminal branch frames.
- Same-frame add/remove behavior.
- Undo/redo project-dirty behavior.
- JSON-safe project save with deep UI trees.
- Old-controller migration to per-frame dialogue queues.
- Ordered command-plus-dialogue export.
- Command-only frames do not replay inherited dialogue.
- Empty inherited frames do not replay parent dialogue.
- Pause without duration exports as `pause`.
- Multiline Python commands and choice commands.
- Raw Ren'Py event preservation.
- Choice prompt plus options as one interaction.
- Managed Say and Choice screen generation.
- Managed child coordinates relative to their containers.
- Imagebutton preview/export.
- Structured frame/button destinations.
- Duplicate generated label and screen-name detection.
- Missing frame target, invalid Python expression/script, inheritance-cycle, duplicate widget-ID, and broken dialogue-queue validation.
- Generated helper Python block compilation.
- Source-flow import model and branch-frame creation paths.
- ZIP/file integrity and UTF-8 readability.

## Source/API cross-checks

The implementation was compared against:

- ActionEditor3's scene-list and transform-capture approach.
- Ren'Py `ScreenDisplayable` child/widget behavior.
- Ren'Py render-tree ownership and child offsets.
- `renpy.get_displayable_properties` and active screen APIs.
- `renpy.screenshot_to_bytes` screenshot capture.
- `renpy.invoke_in_new_context` layer-clearing behavior.
- Ren'Py screen-language property registrations, including padding and viewport/VPGrid behavior.
- Ren'Py AST nodes for Say, Menu, Show, Hide, Scene, Python, Jump, Call, Pause, and custom statements.

## Corrections made during validation

Major corrections include:

- Changed the shortcut from Shift+E to Shift+L.
- Removed the requirement to manually enable `config.developer`.
- Opened the editor context with `_clear_layers=False` so active UI is not cleared.
- Captured source location and exact pixels before switching context.
- Prevented runtime `ScreenDisplayable` objects from entering project JSON.
- Added recursive child traversal with cycle protection and stable widget-ID reverse mapping.
- Fixed inherited dialogue replay and added ordered per-frame event queues.
- Fixed menu captions so prompt and choices remain one interaction.
- Fixed absolute one-pixel positions and double-applied zoom.
- Fixed managed-child preview and drag coordinates to remain parent-relative.
- Fixed duplicate widget IDs during conversion.
- Fixed branch fallthrough, duplicate labels, per-frame widget overrides, and captured dialogue screen export.
- Added exact screenshot fallback and runtime-only screen-root references.

## What could not be executed here

The actual Ren'Py 8.5.3 SDK binary and Launcher Lint command were not available in this environment. Therefore, the package still requires a real SDK run against your project's custom screens.

Passing static/model tests does not guarantee that every custom displayable, screen loop, style, action, or project-specific integration will behave perfectly. Use the first-test checklist in `MIGRATION.md` and share any traceback for a targeted compatibility patch.
