# Validation performed in audited build v2

## Executed checks

- Parsed every embedded `init python` block with Python's AST parser.
- Executed all 13 Python modules in init-priority order against a Ren'Py API compatibility stub.
- Exercised frame inheritance, local overrides, additions/removals, duplicate frame names, dialogue active-event export, managed UI export, captured-screen exclusion, per-frame widget overrides, and JSON saving.
- Tested quoted and multiline dialogue/UI text generation.
- Checked the screen source against Ren'Py 8.5 screen-language documentation and removed unsupported `vpgrid allow_underfull` usage.
- Cross-checked scene-list capture patterns with ActionEditor3's current `ActionEditor.rpy` implementation.
- Confirmed runtime `ScreenDisplayable` objects and screenshot bytes remain outside the JSON project model.
- Confirmed animation/ATL editor implementation is absent from the main build.

## Corrections made during the audit

- Changed the default shortcut from Shift+E to Shift+L to avoid Ren'Py's built-in editor shortcut.
- Prevented captured `say`, `choice`, and other runtime screens from exporting as ordinary `show screen` statements.
- Made exported frame labels unique with stable ID suffixes.
- Changed UI overrides to be stored per frame instead of allowing later frames to overwrite earlier values.
- Fixed first-button creation adding an unwanted text element.
- Fixed same-frame add/remove resolution order.
- Fixed float offsets being interpreted as relative screen positions.
- Fixed captured bounds applying zoom twice.
- Increased JSON-safe nesting depth so deep UI trees are not converted into strings.
- Made generated strings safe for quotes, slashes, tabs, and newlines.
- Added deterministic layer clearing to root-frame story exports.

## Remaining required target-project check

This environment does not include a runnable Ren'Py 8.5.3 launcher, so the package has not been passed through the actual Ren'Py Launcher **Lint** command or launched against your project's custom screens, layers, and store variables. Run the first test in a project copy with the old SceneEditor files disabled. Lint is still necessary because Ren'Py itself notes that lint is not a substitute for runtime testing, and the reverse is also true.
