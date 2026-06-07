# Third-party boundary

Ren'Py Live Studio was inspired by the workflow of ActionEditor3:

- https://github.com/kyouryuukunn/renpy-ActionEditor3

The main Live Studio build does not include ActionEditor3's animation/keyframe implementation. Animation is intentionally disabled and isolated behind a future adapter boundary under `optional/animation/`.

Ren'Py itself is licensed separately by its authors. This package is intended to run inside a Ren'Py project and uses Ren'Py's public and runtime APIs.
