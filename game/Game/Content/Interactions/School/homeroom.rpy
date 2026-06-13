# =============================================================================
# Location: Homeroom (school)
# -----------------------------------------------------------------------------
# Per-location data ONLY. Registration (name/bg/area/variants/unlocked) lives
# in Game/World/Locations.rpy. This file fills in:
#   - where Alice stands
#   - any items that should appear here (none for now)
#   - on_enter event hook (none for now)
#   - per-location talk overrides (the dispatcher in zStory/Characters/Alice.rpy
#     handles location-aware lines, so an explicit override is rarely needed)
# =============================================================================

init python:
    location_package(
        id="homeroom",
        positions={
            "alice": [(0.50, 1.0), (0.40, 1.0), (0.60, 1.0)],
        },
        exits=[
            exit_spot("hallway", label="Hallway", pos=(0.05, 0.55), size=(180, 540)),
        ],
    )
