# =============================================================================
# Location: Hallway (school)
# -----------------------------------------------------------------------------
# Demonstrates a quest-flag-gated item: the dropped pen only appears while the
# `quest_found_pen` flag is set; clicking it picks it up and clears the spot.
# =============================================================================

init python:
    location_package(
        id="hallway",
        positions={
            "alice": [(0.28, 1.0), (0.42, 1.0)],
            "bree": [(0.58, 1.0), (0.70, 1.0)],
            "cora": [(0.82, 1.0)],
        },
        items=[
            item_spot("lost_pen", pos=(0.78, 0.72), label="pickup_lost_pen", while_flag="quest_found_pen", hide_flag="got_pen"),
            item_spot("archive_key", pos=(0.36, 0.76), label="pickup_archive_key", requires="flag:bree_archive_briefed", hide_flag="got_archive_key"),
        ],
        objects=[
            object_spot(
                "archive_door",
                name="Archive Door",
                pos=(0.68, 0.54),
                size=(130, 430),
                allow_item_use=True,
                actions=[
                    action("Inspect", "archive_door_inspect", primary=True, once=True, seen_message="You already checked the door."),
                ],
            ),
        ],
        # Branching network: hallway is the school hub.
        exits=[
            exit_spot("homeroom", label="Homeroom", pos=(0.08, 0.55), size=(140, 480)),
            exit_spot("art_room", label="Art Room", pos=(0.24, 0.55), size=(140, 480)),
            exit_spot("club_room", label="Club Room", pos=(0.40, 0.55), size=(140, 480)),
            exit_spot("math_room", label="Math Room", pos=(0.56, 0.55), size=(140, 480)),
            exit_spot("archive_room", label="Records", pos=(0.66, 0.55), size=(120, 480)),
            exit_spot("roof", label="Roof", pos=(0.74, 0.55), size=(140, 480)),
            exit_spot("front", label="Outside", pos=(0.92, 0.55), size=(140, 480)),
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


label pickup_archive_key:
    "A brass key has been taped under the molding, exactly where Bree said it would be."
    $ add_item("archive_key")
    $ set_flag("got_archive_key")
    "(You picked up the archive key.)"
    jump explore


label archive_door_inspect:
    if has_flag("archive_room_unlocked"):
        "The archive door is unlocked now. The air beyond it smells like paper and dust."
    elif has_item("archive_key"):
        "The key in your pocket seems to fit the archive door."
    else:
        "The archive door is locked. Someone has scratched three tiny arrows beside the handle."
    jump explore


label archive_door_unlock:
    call use_archive_key_on_archive_door("archive_key", "archive_door")
    jump explore


label use_archive_key_on_archive_door(item_id=None, target=None):
    if has_flag("archive_room_unlocked"):
        "The archive door is already unlocked."
    elif not has_item("archive_key"):
        "The lock does not move."
    else:
        "You take the archive key from your bag and test it against the scratched lock."
        "The archive key turns with a dry click."
        $ unlock_room("archive_room")
        $ set_flag("archive_room_unlocked")
        $ set_flag("archive_keyhunt_done")
        $ reset_stamina_cost_multiplier()
        $ stop_rollback_here()
        "(The Records Archive is now accessible.)"
    jump explore
