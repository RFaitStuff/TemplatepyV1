# Ren'Py Live Studio 3.6 architecture

## Boundaries

Live Studio core is a removable development tool. It must never become a runtime dependency of the game.

Project-specific knowledge is implemented through extensions. The base editor may inspect a normal Ren'Py project conservatively, while the Project Tac extension may use the known Project Tac layout, registries, capabilities, and source conventions.

## State layers

The editor distinguishes four different kinds of state:

1. **Runtime observation** — what Ren'Py rendered when the editor opened or refreshed capture.
2. **Resolved project state** — the inherited Frame result derived from Studio project data.
3. **Transient editing overlay** — drag and typing previews that have not yet committed.
4. **Export/source plan** — proposed source output and exact file changes.

Runtime observation is not treated as authored source. Resolved state is derived and should not become an uncontrolled mutable cache. Source-writing occurs only from an explicit plan.

## Object categories

- **Studio-managed:** created and fully owned by Live Studio.
- **Source-backed:** tied to recoverable Ren'Py or Project Tac source metadata.
- **Runtime override:** captured from the active runtime and editable only through supported properties.
- **Preview-only:** visible for context but unsafe to edit or export.

The category controls property availability, direct manipulation, and export behavior.

## Project and frame relationships

A frame has an inheritance relationship for visual/editor state and separate route edges for story flow. Editor order, visual parentage, runtime predecessor, and route destination are not assumed to be identical.

Dialogue is frame logic. Scene visual groups contain visual objects only. UI screens retain real parent-child hierarchy.

## Revision and cache model

Authored project changes advance the project revision and append a command-journal entry. Selection, hover, and passive preview changes do not mark the project dirty.

Derived caches use runtime state revisions and their own scoped invalidation paths. Project mutation schedules autosave and recovery persistence without forcing source export.

## Source-writing model

Generic Live Studio generates source previews and files. Handwritten-source patching is experimental.

Project Tac source authoring uses:

1. source indexing;
2. object/source identity;
3. expected old hashes;
4. final text generation in memory;
5. unified diff review;
6. structural validation;
7. backup creation only for real changes;
8. temporary-file writing and atomic replacement;
9. transaction rollback;
10. post-write hash verification and export history.

## Compatibility model

The generic extension registry exposes an API version and capability requirements. Project Tac supplies a capability descriptor when available, while the extension can conservatively infer limited support for older project versions.

Unsupported commands are disabled rather than executed optimistically.

## Error model

Diagnostics are structured and retained. Expected Ren'Py compatibility fallbacks may be hidden by default; user/content errors, runtime inspection failures, source-write failures, and editor defects remain available in the Debugger and full report.
