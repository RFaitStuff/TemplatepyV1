# Ren'Py Live Studio 3.6.0 changelog

## Project lifecycle

- Advanced the project model to version 12 and centralized the release version as `3.6.0`.
- Added project metadata for engine version, source project path, authored revision, editing session, extension information, and last exported revision.
- Added periodic Studio-project autosave without rewriting game source.
- Added a crash-recovery journal with restore, inspect, and discard operations.
- Added named manual project snapshots and snapshot restoration.
- Added export history with file hashes, backup paths, validation results, and project revision.

## Commands and updates

- Added a command journal around the existing undo/redo model.
- Added a single authored-project revision counter separate from visual and selection updates.
- Fixed undo and redo paths so empty operations do not create state changes.
- Added centralized mutation touch points that schedule recovery and autosave work.
- Added structured project lifecycle data to the Debugger report.

## Diagnostics

- Added structured diagnostics with severity, category, system, operation, object, frame, source, exception, recovery action, and context.
- Added bounded diagnostic retention and summary counts.
- Kept expected compatibility fallbacks separately filterable from actionable defects.
- Expanded the copyable Debugger report with project lifecycle, command journal, asset metadata, export state, extension capabilities, and Project Tac state.

## Runtime and UI rules

- Formalized Studio-managed, source-backed, runtime-override, and preview-only object categories.
- Added explicit reasons when an object cannot be edited.
- Added coordinate modes for automatic, pixel, relative, alignment, and mixed placement.
- Preserved relative and alignment intent during canvas movement where possible.
- Added keyboard nudging and fine movement.
- Prevented free movement and resize behavior when a parent VBox, HBox, Grid, or VPGrid owns child layout.
- Kept dialogue as frame logic rather than a visual Scene layer.

## Assets

- Added an automatically derived asset metadata cache.
- Added source-signature invalidation using file paths and timestamps.
- Added inferred character, expression, background, UI, audio, and time-variant metadata.
- Added duplicate/shared-source and runtime-only asset diagnostics.
- Preserved the simple Images/Audio top-level browser while using the real folder tree for organization.

## Export safety

- Added an export plan with per-file status, generated hashes, existing hashes, and validation.
- Unchanged outputs are skipped without backups or rewrites.
- Changed outputs use temporary files, flush/fsync, and atomic replacement.
- Added export records to the Studio project history.
- Source replacement and experimental handwritten patching use the same safe replacement path.
- Pending property input is committed before export planning or writing.

## Generic extensions

- Added extension API versioning and capability negotiation.
- Added extension-level and command-level requirements.
- Added readable disabled reasons for unavailable commands.
- Added preview metadata so only explicitly safe previews can use raw Apply-to-File.
- Added structured extension failure diagnostics.

## Project Tac extension

- Added a dynamic Project Tac engine descriptor and minimum capability checks.
- Added a cached source index for files, labels, screens, transforms, styles, images, defaults, defines, functions, classes, known Project Tac definitions, generated regions, and Studio IDs.
- Added structured Project Tac validation for source-index errors, duplicate objects, capabilities, quests, locations, items, interactables, and missing labels.
- Added source signatures and time-of-check/time-of-use protection.
- Added unique timestamped backups and post-write hash verification.
- Added atomic multi-file transactions with rollback.
- Changed typed Project Tac writers to create a reviewable pending source plan rather than writing immediately.
- Added Apply Planned Changes and Discard Plan operations.
- Added unified diffs and dependency-group information to source plans.
- Restricted raw Apply-to-File to previews explicitly marked as safe.
- Tightened direct selected-widget property patching to exact source statements and source-backed UI only.
- Refused ambiguous inline-property patches rather than silently changing the wrong source.

## Documentation

- Replaced the outdated README with a UTF-8 architecture and workflow reference.
- Corrected the dialogue ownership model and removed corrupted tree characters.
- Added architecture, migration, changelog, and validation documents for 3.6.0.
