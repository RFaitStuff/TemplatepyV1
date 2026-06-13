# Ren'Py Live Studio 3.6.0

Ren'Py Live Studio is an in-game visual authoring environment for Ren'Py 8.5.3 and newer. It captures the active game without clearing the underlying runtime, then provides an editor for scene visuals, gameplay UI, dialogue logic, frames, flow, assets, source previews, and generated code.

The base editor remains portable. Project-specific behavior belongs in extensions. The bundled Project Tac extension is intentionally specialized for the Project Tac layout and can inspect, validate, plan, and apply changes to its known project structures.

## Installation

Copy the complete `RenPyLiveStudio` folder into `game/DevTools/` and launch the project normally. Open the editor with **Shift+L**.

Disable `ENABLED` in `LiveStudio_config.rpy`, or remove the entire folder, before distributing a release build. The game must not depend on Live Studio for runtime behavior.

When upgrading, replace the complete folder instead of mixing individual files from different versions. Existing Live Studio project data is migrated when loaded.

## Project model

```text
Project
└── Frame
    ├── Scene visuals
    ├── Dialogue and route logic
    └── UI screens
```

A Frame is a gameplay or story state, not an animation keyframe. Inherited frames store only their local differences.

Dialogue is frame logic. It does not appear as a visual Scene layer. Say and Choice screens are presentation UI and may be kept as passive preview context without being exposed as editable gameplay UI by default.

Scene and UI editing are separate domains:

- Scene mode edits images and other scene-owned visuals.
- UI mode edits screen and widget hierarchy data.
- Captured UI is classified as source-backed, runtime-overridable, Studio-managed, or preview-only.
- Parent-controlled layout children, such as children of a VBox, HBox, Grid, or VPGrid, are not treated like freely positioned canvas objects.

## Runtime capture rules

Live Studio captures only active rendered gameplay UI by default. It filters inactive, prediction-only, Ren'Py engine, developer, debug, focus/defocus, and Live Studio-owned screens. The filter can be changed in Settings for inspection work.

Captured runtime UI is frozen at the time of capture so ordinary Scene edits and interaction restarts do not re-evaluate the original screen tree. This prevents imagebuttons, dynamic text, scope-dependent values, and layout from unexpectedly changing while a scene object is moved.

Runtime objects use stable structural identities based on screen, source, widget ID, and hierarchy path. Transparent full-screen root wrappers may merge into their screen folder, while meaningful layout, transform, action, and clipping containers remain represented.

Quick Menu is captured but locked by default. Dialogue presentation is kept passive unless dialogue-screen capture is explicitly enabled.

## Editing behavior

The canvas supports selection, movement, resizing, rotation, duplication, deletion, hierarchy ordering, visibility, locking, snapping, guides, and keyboard nudging.

Coordinate intent is preserved when possible. Supported modes include automatic, pixels, relative, alignment, and mixed placement. A drag does not needlessly convert a relative or alignment-authored object into raw pixels.

Property fields commit before save, export, frame changes, selection changes, or editor close. Continuous typing and dragging merge into meaningful undo entries instead of producing one history record per character or mouse event.

The editor records authored revisions separately from selection and preview-only changes. Undo, redo, delete, frame switching, and runtime recapture validate the current selection and invalidate the required derived views immediately.

## Project safety

Live Studio project data is separate from game source files.

Version 3.6 adds:

- periodic project autosave;
- a crash-recovery journal;
- restore, inspect, and discard recovery actions;
- named manual Studio snapshots;
- a command journal with project revision information;
- export history with hashes and backup locations;
- structured diagnostics with severity and recovery context.

Autosaving the Studio project does not rewrite `.rpy` source files.

## Assets

The top-level Asset Browser intentionally contains only **Images** and **Audio**. Character, background, GUI, and other organization comes from the real project folder tree rather than duplicated category tabs.

Live Studio builds derived asset metadata from registered images and files. The metadata cache records source paths, timestamps, inferred kinds, character expressions, time-of-day variants, and duplicate or runtime-only conditions. It is rebuilt only when the relevant source signature changes.

## Export workflow

The normal workflow is:

```text
Generate preview
→ inspect validation and changed files
→ select an export action
→ apply atomically
```

The export planner calculates final text and hashes before writing. Unchanged files are skipped and do not receive unnecessary backups. Real changes are written through temporary files and atomic replacement. Export history records the project revision, modified files, old and new hashes, backups, and validation results.

Captured scene images emit only explicitly changed transform properties. An untouched object does not receive unnecessary output such as `rotate 0`, `alpha 1`, default zoom, or observed runtime placement.

Generic handwritten-source replacement remains experimental and disabled by default. Generated files and editor-owned regions remain the safest portable path.

## Extension system

Extensions register through `Extension/LiveStudio_extensions.rpy`. An extension may provide:

- an availability check;
- capability requirements;
- commands and command categories;
- project-file indexing and previews;
- summary information;
- generated previews;
- controlled apply behavior.

Unsupported commands remain visible when useful but are disabled with a readable capability reason. Extension failures are routed into structured Live Studio diagnostics.

## Project Tac extension

`Extension/LiveStudio_ProjectTac_Extension.rpy` contains the original Project Tac integration. `Extension/LiveStudio_ProjectTac_v36.rpy` augments it with the safer 3.6 authoring model.

The extension activates only when the running project identifies itself as Project Tac. It understands the expected `Engine`, `Mechanics`, `Game/_Data`, `Game/Content`, root UI, and DevTools layout. This specialization is deliberate; the same source-writing assumptions are not applied to arbitrary Ren'Py projects.

### Capabilities

The extension reads `PROJECT_TAC_ENGINE` when available. Otherwise it derives a conservative capability descriptor from known Project Tac symbols. Commands declare minimum capability levels and are disabled when the engine does not meet them.

### Source index

The Project Tac source index records:

- files and domains;
- labels, screens, styles, transforms, images, defaults, and defines;
- functions and classes;
- known Project Tac definitions and generated regions;
- Studio object IDs and source ranges;
- source signatures and indexing errors.

The index is cached and refreshed when relevant files change.

### Validation

Project-specific validation reports structured findings for capability mismatches, duplicate source objects, missing labels, invalid quest references, location exits and items, interactable definitions, and source-index failures. Errors can block an affected source plan without preventing unrelated valid work.

### Two-stage source changes

Project Tac writer commands create a pending source plan first. The plan contains the target files, exact resulting text, hashes, unified diffs, validation findings, and dependency group. Nothing is written during planning.

After review, **Apply Planned Changes** performs a rollback-capable transaction:

1. Verify that source hashes still match the planned versions.
2. Re-run structural validation.
3. Skip unchanged files.
4. Create uniquely timestamped backups only for real changes.
5. Write and flush temporary files.
6. Atomically replace all files in the dependency group.
7. Roll back already-replaced files if any later replacement fails.
8. Verify post-write hashes and record the result.

Raw Apply-to-File is available only for previews explicitly marked safe for that operation. Reports and structured writer plans cannot be blindly appended.

### Direct property patching

Direct source patching is limited to selected source-backed UI widgets with recoverable source metadata. It targets the exact screen-language statement rather than nearby context lines, verifies the expected original hash, and refuses ambiguous or unsafe inline-property changes.

## Debugger

The Debugger tab provides a copyable report intended for bug reports. It includes:

- Live Studio and project model versions;
- current project, frame, revision, and editing session;
- selection identity, parent chain, category, editability, coordinate modes, and bounds;
- active and filtered runtime screens;
- capture and cache revisions;
- frame-local changes and source-flow information;
- asset metadata and issues;
- export plans and recent export records;
- extension capabilities;
- Project Tac source-index, validation, and pending-plan information;
- recent structured diagnostics and command-journal entries.

Use **Copy Full Report** when reporting a problem. The visible preview may be truncated, but the copied report contains the full payload.

## File layout

```text
LiveStudio_config.rpy          Version, settings, property definitions
LiveStudio_models.rpy          JSON-safe project model and migration defaults
LiveStudio_project.rpy         Frame resolution, selection, history, core commands
LiveStudio_project_io.rpy      Save, load, autosave, recovery, snapshots, export history
LiveStudio_commands.rpy        Revision and command-journal integration
LiveStudio_diagnostics.rpy     Structured diagnostics
LiveStudio_scene.rpy           Runtime scene capture and scene editing
LiveStudio_ui.rpy              Runtime UI capture, hierarchy, overrides, managed UI
LiveStudio_runtime_rules.rpy   Object categories and coordinate/layout rules
LiveStudio_dialogue.rpy        Dialogue and route logic
LiveStudio_capture.rpy         Non-destructive runtime capture
LiveStudio_flow.rpy            Frame graph and conservative source-flow discovery
LiveStudio_assets.rpy          Asset browser
LiveStudio_asset_metadata.rpy  Derived asset metadata cache
LiveStudio_canvas.rpy          Rendering, hit testing, and direct manipulation
LiveStudio_export.rpy          Ren'Py code generation
LiveStudio_export_plan.rpy     Export planning, hashing, atomic writes, history
LiveStudio_debug_report_v36.rpy Extended copyable debugger report
LiveStudio_screens.rpy         Editor screens and styles
LiveStudio_bootstrap.rpy       Shortcut and context-safe startup
Extension/                     Generic and Project Tac-specific integrations
```

## Important limitations

Ren'Py runtime displayable trees are not guaranteed to map one-to-one to handwritten screen language. Custom displayables, dynamically generated widgets, loops, transclusion, Python closures, ATL, and repeated screen instances may only be inspectable or runtime-overridable.

Future-frame discovery is conservative. Dynamic Python conditions, computed jumps, custom statements, rollback behavior, and context changes may not have a single statically knowable next frame.

The included validation is source-level and mocked-logic validation. A complete rendered test must still be performed inside the target Ren'Py project before relying on source-writing or complex UI-editing behavior.
