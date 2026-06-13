# =============================================================================
# Location: Club Room (school)
# -----------------------------------------------------------------------------
# A third-place hangout. Dialogue is registered in Game/Characters/Dialogue; this
# file only owns room setup.
# =============================================================================

init python:
    location_package(
        id="club_room",
        positions={
            "alice":  [(0.30, 1.0)],
            "alex": [(0.70, 1.0)],
        },
        exits=[
            exit_spot("hallway", label="Hallway", pos=(0.05, 0.55), size=(160, 480)),
        ],
    )
