# v3.2.1 parser hotfix

- Replaced two invalid `add ... yfill True` statements in `LiveStudio_screens.rpy`.
- The hierarchy connector now sizes its `Solid` explicitly.
- The asset-browser divider now uses a one-pixel `frame` that supports `yfill`.

# v3.2 changelog — UI hierarchy, direct manipulation, and performance

## Fixed

- Select mode can drag the selected scene/UI object again.
- The editable visual now moves with its selection rectangle.
- Added edge/corner resize handles and a rotate handle.
- Captured UI widgets with stable IDs use live widget-property overrides.
- Removed empty `Layer: transient`, `Layer: screens`, `Layer: overlay`, and `Layer: top` scene entries.
- Migrates those obsolete entries from loaded and autoreload-retained projects.
- Scene and UI layer views are separated.
- UI layers show nested connected elements and thumbnails.
- Anonymous engine wrappers no longer flood the tree as `Custom`.
- Dynamic HUD text preserves its source value/expression instead of freezing the captured preview.
- Restored compact text-box Properties controls with inherited-value reversion.
- Replaced the flat asset grid with a source-folder tree plus current-folder tiles.
- All editor scrollbars are four pixels wide.

## Performance

- Property inputs no longer deep-resolve the frame on every character.
- One field-level undo entry is created after typing pauses.
- Canvas selection changes do not recreate the canvas displayable.
- Dragging uses a transient preview and commits once on mouse-up.
- Captured-screen preview invalidation is scoped to the edited screen.
- UI bounds, widget overrides, source displayables, asset rows, and thumbnails are cached independently.
- Thumbnail children are built once and excluded from the main interaction visit pass.
- Asset search waits for Enter/Search rather than restarting per keystroke.
- Empty drag clicks no longer add no-op history entries.

## Compatibility

- Project model version is now 7.
- Existing v3/v3.1 JSON projects remain migratable.
- Animation remains excluded.
- Existing-source patching remains experimental and disabled.
