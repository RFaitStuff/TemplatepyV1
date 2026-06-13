# Migration to Ren'Py Live Studio 3.6.0

## Upgrade procedure

1. Close Ren'Py and make a copy of the existing `RenPyLiveStudio` folder.
2. Replace the complete folder with the 3.6.0 folder. Do not merge individual `.rpy` files from different releases.
3. Delete stale `.rpyc` files for the old Live Studio folder if Ren'Py does not rebuild them automatically.
4. Launch the project and open Live Studio with **Shift+L**.
5. Open or import the existing Studio project. The model migrates to version 12.
6. Review Settings, Project recovery information, extension capability status, and the Debugger report.
7. Run a fresh runtime capture before editing UI created by a previous runtime session.
8. Review every Project Tac source plan before applying it.

## Existing Studio projects

Migration adds default metadata for project revision, engine compatibility, editing session, export history, extension information, and lifecycle state. Existing frames and authored changes remain intact.

Runtime preview displayables are session-local and are not restored as if they were permanent authored objects. A fresh capture is required to inspect the current game runtime accurately.

## Project Tac extension

The existing Project Tac extension remains in place. The additional `LiveStudio_ProjectTac_v36.rpy` module augments it rather than replacing its domain commands and generators.

Typed writer commands now plan changes first. A command that previously wrote immediately will create a pending plan and unified diff. Use **Apply Planned Changes** after review, or **Discard Plan**.

Existing backups are not removed. New backups use unique timestamped names and are created only when final content differs.

## Runtime and UI behavior

Dialogue no longer belongs to a visual Scene layer. Legacy dialogue visual Scene records are removed or ignored by migration, while dialogue logic stays attached to the Frame.

Captured UI should be refreshed from the live game after upgrading. Engine, developer, focus/defocus, inactive, and prediction-only screens remain filtered by default.

Parent-layout-controlled UI children may no longer move freely on the canvas. Edit the parent layout or use supported layout properties instead.

## Rollback

To roll back the Studio itself, restore the complete previous `RenPyLiveStudio` folder. Do not mix old core files with the 3.6 extension modules.

To roll back a Project Tac source transaction, use the backup paths recorded in the source-plan result or export history. Source transactions also attempt automatic rollback if a multi-file apply fails midway.
