# Validation report — v3.2

## Automated checks completed

- Compiled all 15 embedded Python init blocks.
- Executed all 14 `live_studio` init blocks in priority order against a mocked Ren'Py 8.5.3 runtime.
- Resolved all 151 `live_studio.*` screen/style references to implemented names.
- Re-tested project creation, frame inheritance, local overrides, and migration.
- Verified a large 900-child UI model reuses the same resolved frame during repeated property-input updates.
- Verified repeated typing creates one field-level undo entry.
- Verified Select-mode drag data, snapping, edge resize, and mouse-up commit.
- Verified captured UI movement produces a widget override for the actual widget ID.
- Verified scene capture excludes UI-only layers and does not create empty layer scenes.
- Verified old empty layer scenes are removed during model migration.
- Verified anonymous custom wrappers are flattened and explicit widget IDs become readable names.
- Verified dynamic Ren'Py text such as `"[weekday_name()]"` preserves the original source expression.
- Verified managed screen export uses that source expression rather than the captured preview text.
- Verified Unity-style asset folder-tree generation.
- Re-tested parameterized-image filtering and safe lazy thumbnails.
- Re-tested generated story/screen/helper model paths from the previous build.
- Verified ZIP contents and SHA-256 manifest after packaging.

## Static/API review

The implementation was cross-checked against the Ren'Py 8.5.3-era source behavior used by this project, including screen widget IDs/properties, screen AST positional expressions, render-tree offsets, input values, viewports/scrollbars, scene lists, and separate-context layer preservation.

## Not executable in this environment

The actual Ren'Py SDK binary and your full Project Tac runtime are not installed here. The package therefore still requires:

1. A clean project relaunch after replacement.
2. Ren'Py Launcher **Lint**.
3. Exploration/HUD capture.
4. Dialogue and choice capture.
5. Scene image drag, captured widget-ID drag, and managed UI drag.
6. Save/reload and generated-code review.

A runtime traceback or screenshot from those tests should be treated as a targeted compatibility bug, not ignored.
