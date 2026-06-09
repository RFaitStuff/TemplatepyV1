# =============================================================================
# Location: School Front (outdoors)
# -----------------------------------------------------------------------------
# Demonstrates the new system end-to-end:
#   - exit hotspot (front -> hallway)
#   - clickable object hotspot (the noticeboard) routed through the action
#     menu via register_interactable()
#   - quest_guide marker auto-renders over the noticeboard while the
#     "noticeboard_check" side quest is active
# =============================================================================

init python:
    configure_location(
        "front",
        positions={
            "alice":  [(0.25, 1.0), (0.40, 1.0)],
            "alex": [(0.60, 1.0), (0.78, 1.0)],
        },
        exits=[
            {"to": "hallway", "label": "Front Doors", "pos": (0.5, 0.92), "size": (260, 140)},
        ],
        objects=[
            {"id": "noticeboard", "label": "Noticeboard", "pos": (0.18, 0.45), "size": (140, 200)},
        ],
    )

    register_interactable(
        "noticeboard",
        kind="object",
        title="Noticeboard",
        actions=[
            {"id": "read",   "title": "Read flyers",   "label": "noticeboard_read", "primary": True},
            {"id": "search", "title": "Search closer", "label": "noticeboard_search", "available_if": (lambda: has_flag("read_noticeboard"))},
        ],
    )


label noticeboard_read:
    "A wall of flyers tugged crooked by the wind."
    "{i}'Lost: one quiet afternoon. Reward: ask Alice.'{/i}"
    "Someone's underlined the bottom in red pen."
    $ set_flag("read_noticeboard")
    "(You commit it to memory.)"
    jump explore


label noticeboard_search:
    "You shoulder past the older notices."
    a "Found something?"
    menu:
        "Just an old flyer.":
            $ alice.trust(1, "3d")
            a "Mm. Whatever it was, it's gone now."
        "I think it was meant for me.":
            $ react("alice", "embarrassed")
            a "...maybe. Maybe not."
            $ react("alice")
    jump explore
