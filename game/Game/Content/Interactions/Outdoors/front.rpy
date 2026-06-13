# =============================================================================
# Location: School Front (outdoors)
# -----------------------------------------------------------------------------
# Demonstrates the new system end-to-end:
#   - exit hotspot (front -> hallway)
#   - clickable object hotspot (the noticeboard) routed through the action
#     menu via object_spot()
#   - quest_guide marker auto-renders over the noticeboard while the
#     "noticeboard_check" side quest is active
# =============================================================================

init python:
    location_package(
        id="front",
        positions={
            "alice":  [(0.22, 1.0), (0.34, 1.0)],
            "alex": [(0.55, 1.0), (0.66, 1.0)],
            "cora": [(0.82, 1.0)],
        },
        exits=[
            exit_spot("hallway", label="Front Doors", pos=(0.5, 0.92), size=(260, 140)),
        ],
        layers=[
            explore_layer("bg smp_noticeboard", alpha=0.12, zoom=1.04, drift=(10, 0), duration=18.0, requires="flag:read_noticeboard"),
        ],
        objects=[
            object_spot(
                "noticeboard",
                name="Noticeboard",
                pos=(0.18, 0.45),
                size=(140, 200),
                desc="A wall of flyers tugged crooked by the wind.",
                actions=[
                    action("Read flyers", "noticeboard_read", primary=True, repeat_hint="You've already read the obvious flyers."),
                    action("Search closer", "noticeboard_search", requires="flag:read_noticeboard", repeat_hint="You already checked behind the older notices."),
                    action("Report findings", "noticeboard_complex_report", requires="flag:bree_cora_side_chosen"),
                ],
            ),
        ],
    )


label noticeboard_read:
    "A wall of flyers tugged crooked by the wind."
    "{i}'Lost: one quiet afternoon. Reward: ask Alice.'{/i}"
    "Someone's underlined the bottom in red pen."
    $ set_flag("read_noticeboard")
    $ set_flag("complex_arc_available")
    "(You commit it to memory.)"
    jump explore


label noticeboard_search:
    "You shoulder past the older notices."
    if not has_item("coded_slip"):
        "A coded slip falls from behind the flyer."
        $ add_item("coded_slip")
        $ set_flag("got_coded_slip")
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


label noticeboard_complex_report:
    if not has_flag("bree_cora_side_chosen"):
        "The noticeboard has nothing new to say yet."
    else:
        "You pin a blank corner of the flyer back into place."
        if has_taken_branch("bree_cora_route", "bree"):
            "Bree's version of the truth is now the one the board remembers."
        elif has_taken_branch("bree_cora_route", "cora"):
            "Cora's warning is now folded into the route ahead."
        else:
            "The evidence has been handled, but nobody has decided what it means."
        $ set_flag("complex_arc_reported")
        "(Complex quest chain reported.)"
    jump explore
