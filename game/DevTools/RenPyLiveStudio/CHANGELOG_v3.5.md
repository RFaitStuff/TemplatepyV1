# Ren'Py Live Studio v3.5.0 — Runtime UI Stability

## Runtime UI isolation

- Captured gameplay screens are frozen at capture time and no longer participate in later `per_interact` updates.
- Moving or editing a Scene object does not invalidate or rebuild captured HUD/UI previews.
- Source-backed UI edits are applied from the original `ScreenDisplayable` scope once per committed widget-override signature, then frozen again.
- Runtime UI does not rebuild on every mouse-motion event. Selection bounds move live; the actual source-backed screen commits on mouse-up.
- Runtime preview references are stored per captured Frame so switching frames restores the matching screen roots, widget maps, active-screen set, and exact screenshot.

## Dialogue separation

- Dialogue controllers are frame logic and are never represented as visual Scene layers.
- Active Say/Choice presentation is retained as a passive frozen canvas preview by default, but does not appear in Scene/UI Layers.
- Legacy Dialogue/Dialogue Visuals Scene records are removed during migration.

## UI capture and hierarchy

- Only active rendered gameplay screens are modeled.
- Ren'Py/common, developer/debug, Live Studio, prediction, focus/defocus, and inactive runtime screens are filtered by default.
- Loaded projects do not resurrect stale runtime-only overlays when no live preview bundle is available.
- Transparent full-screen roots such as HUD Root merge into their screen folder.
- Neutral anonymous wrappers are flattened only when they do not own layout, actions, art, or transforms.
- Captured node identity uses screen, source location, widget id, and structural path rather than a global traversal counter.
- Quick Menu is captured but locked by default.
- Container selection prioritizes descendants on the next click, and moving a container carries descendant bounds with it.

## Editing and updates

- Fixed a captured-UI resize bug where one widget's drag preview could alter unrelated selection boxes.
- Captured screen visibility follows the active Frame's runtime bundle.
- Resolved Frame states remain immutable derived snapshots rather than being mutated in-place.
- Delete, undo, redo, frame selection, and capture refresh validate selection and invalidate the correct view caches.
- Asset search updates while typing, matching the old backup editor.
- Export first commits buffered property inputs.

## Debugger

- Replaced the old Inspector-side diagnostic concept with a working copyable Debugger report.
- The report includes project/frame state, capture serial/source, cache revisions, selected-node parent chain and overrides, effective bounds, active/inactive screens, filter decisions, runtime displayable types, passive dialogue presentation, capabilities, frame changes, and recent diagnostics.
