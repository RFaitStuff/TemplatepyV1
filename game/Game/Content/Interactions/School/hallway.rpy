# =============================================================================
# Location: Hallway (school)
# -----------------------------------------------------------------------------
# Demonstrates a quest-flag-gated item: the dropped pen only appears while the
# `quest_found_pen` flag is set; clicking it picks it up and clears the spot.
# =============================================================================

init python:
    configure_location(
        "hallway",
        positions={
            "alice": [(0.40, 1.0), (0.60, 1.0)],
        },
        items=[
            {
                "item":       "lost_pen",
                "while_flag": "quest_found_pen",
                "hide_flag":  "got_pen",
                "label":      "pickup_lost_pen",
                "pos":        (0.78, 0.72),
            },
        ],
        # Branching network: hallway is the school hub.
        exits=[
            {"to": "homeroom",  "label": "Homeroom",  "pos": (0.08, 0.55), "size": (140, 480)},
            {"to": "art_room",  "label": "Art Room",  "pos": (0.24, 0.55), "size": (140, 480)},
            {"to": "club_room", "label": "Club Room", "pos": (0.40, 0.55), "size": (140, 480)},
            {"to": "math_room", "label": "Math Room", "pos": (0.56, 0.55), "size": (140, 480)},
            {"to": "roof",      "label": "Roof",      "pos": (0.74, 0.55), "size": (140, 480)},
            {"to": "front",     "label": "Outside",   "pos": (0.92, 0.55), "size": (140, 480)},
        ],
    )


# -----------------------------------------------------------------------------
# Item pickup label - MUST end with `jump explore` (call screen is terminated
# by Jump, not Call).
# -----------------------------------------------------------------------------
label pickup_lost_pen:
    
    "There's a pen on the floor. Cheap, but someone might miss it."
    $ add_item("lost_pen")
    $ set_flag("got_pen")
    "(You picked up a pen.)"
    jump explore
