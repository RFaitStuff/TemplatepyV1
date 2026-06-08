# =============================================================================
# Location: Club Room (school)
# -----------------------------------------------------------------------------
# A third-place hangout. Dialogue is registered in Game/Characters/Dialogue; this
# file only owns room setup.
# =============================================================================

init python:
    configure_location(
        "club_room",
        positions={
            "alice":  [(0.30, 1.0)],
            "alex": [(0.70, 1.0)],
        },
        exits=[
            {"to": "hallway", "label": "Hallway", "pos": (0.05, 0.55), "size": (160, 480)},
        ],
    )
