# =============================================================================
# Location: Roof (school)
# -----------------------------------------------------------------------------
# First-time visit triggers the Chapter 1 introduction (which itself contains
# the first BRANCH choice of the game). The on_enter label gates that with a
# flag so it only fires once.
# =============================================================================

init python:
    configure_location(
        "roof",
        positions={
            "alice":  [(0.30, 1.0), (0.45, 1.0)],
            "alex": [(0.70, 1.0), (0.85, 1.0)],
        },
        on_enter="roof_on_enter",
        exits=[
            {"to": "hallway", "label": "Stairs Down", "pos": (0.06, 0.78), "size": (180, 360)},
        ],
    )


label roof_on_enter:
    if not has_flag("ch1_intro_seen"):
        call chapter1_intro
    return
