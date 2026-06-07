# Optional animation module

Animation is intentionally not part of the first Live Studio release.

The current editor treats a **Frame** as a story/game state. Animation timelines and keyframes would be attached to individual scene nodes later, rather than turning project frames into animation timestamps.

A future animation module should expose a small adapter interface:

- `capture_animation(node_id)`
- `evaluate_animation(node_id, time)`
- `open_animation_workspace(node_id)`
- `export_animation(node_id)`

ActionEditor3-derived code should remain outside the main editor until it has been rewritten around that interface and its licensing/attribution has been reviewed.
