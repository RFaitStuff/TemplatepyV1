# =============================================================================
# Location: Math Room (school)
# =============================================================================

init python:
    location_package(
        id="math_room",
        positions={
            "alice": [(0.35, 1.0), (0.65, 1.0)],
        },
        exits=[
            exit_spot("hallway", label="Hallway", pos=(0.05, 0.55), size=(160, 480)),
        ],
    )
