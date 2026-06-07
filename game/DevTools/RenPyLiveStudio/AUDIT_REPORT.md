# Ren'Py Live Studio v2 audit report

This package was re-audited against:

- The five original SceneEditor files supplied with the project.
- The current ActionEditor3 `ActionEditor.rpy` architecture and scene-list capture pattern.
- Ren'Py's current documentation for screens, screen Python APIs, screenshots, displayables, image statements, developer tools, and custom displayables.
- Ren'Py's current `ScreenDisplayable` implementation, including `child`, `widgets`, `base_widgets`, `visit()`, and non-save fields.

## Safe architectural conclusions

- Runtime layers are not cleared when Live Studio opens.
- The exact visual capture is produced before the editor screen replaces the view.
- Runtime displayables are held only in the temporary runtime dictionary and are not serialized into project JSON.
- Active screens are represented as hierarchical widget trees rather than one flat full-screen record.
- Dialogue content is stored in scene-owned Dialogue Controllers while Say/Choice visuals remain UI screens.
- Child frames inherit their parent and store local operations rather than complete copied states.
- Animation code is excluded from the main package.
- Writing files is an explicit operation; preview and clipboard copy remain the default workflow.
- Source block replacement and handwritten patching remain disabled unless explicitly enabled per project.

## Important corrections made

See `VALIDATION.md` for the full list. The most significant corrections were shortcut collision avoidance, captured-screen export filtering, unique labels, per-frame UI overrides, correct bounds/offset math, deep JSON preservation, and safe generated string literals.

## What still requires the target project

A true Ren'Py test must still cover:

1. Launcher parsing and Lint under the exact Ren'Py 8.5.3 build used by the project.
2. Opening Live Studio during exploration, ordinary dialogue, a menu, and a custom screen.
3. Capturing project-specific custom displayables and screens with `use`, loops, viewport content, and Python-created children.
4. Checking whether custom layers are included in `config.layers` and mapped in `SCENE_GROUPS`.
5. Copying generated source into a disposable test file and running Lint again.

The package is suitable for that first integration test, but it should still be installed into a project copy rather than the only working project folder.
