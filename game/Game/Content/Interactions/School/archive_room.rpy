# =============================================================================
# Location: Records Archive (school)
# =============================================================================
# Stress-test room for quest state, item visibility, interactables, stat gates,
# branches, and multi-character dialogue.
# =============================================================================

init python:
    location_package(
        id="archive_room",
        positions={
            "alice": [(0.50, 1.0)],
            "bree": [(0.28, 1.0), (0.40, 1.0)],
            "cora": [(0.62, 1.0), (0.76, 1.0)],
        },
        on_enter="archive_room_on_enter",
        items=[
            item_spot("sealed_drive", pos=(0.22, 0.70), label="pickup_sealed_drive", requires="flag:entered_archive_room", hide_flag="got_sealed_drive"),
        ],
        exits=[
            exit_spot("hallway", label="Hallway", pos=(0.06, 0.78), size=(160, 220)),
        ],
        objects=[
            object_spot(
                "archive_terminal",
                name="Archive Terminal",
                pos=(0.52, 0.48),
                size=(190, 170),
                actions=[
                    action("Decode", "archive_terminal_decode", primary=True),
                    action("Force Access", "archive_terminal_force", requires="Bree.Trust>=2"),
                ],
            ),
            object_spot(
                "glass_badge_case",
                name="Glass Badge Case",
                pos=(0.81, 0.52),
                size=(160, 210),
                actions=[
                    action("Inspect", "archive_badge_case", primary=True),
                ],
            ),
            object_spot(
                "locked_cabinet",
                name="Locked Cabinet",
                pos=(0.36, 0.50),
                size=(140, 240),
                actions=[
                    action("Inspect", "archive_locked_cabinet", primary=True),
                    action("Open", "archive_locked_cabinet_open", requires=req("flag:archive_evidence_decided", "Cora.Trust>=1")),
                ],
            ),
        ],
    )


label archive_room_on_enter:
    if not has_flag("entered_archive_room"):
        $ set_flag("entered_archive_room")
        "The archive feels abandoned in a deliberate way, as if the dust was placed here to warn people off."
    return


label pickup_sealed_drive:
    "The sealed drive is colder than the room around it."
    $ add_item("sealed_drive")
    $ set_flag("got_sealed_drive")
    "(You recovered the sealed drive.)"
    jump explore


label archive_badge_case:
    "A glass badge sits inside the case, its nameplate scraped almost clean."
    if not has_item("glass_badge"):
        $ add_item("glass_badge")
    $ set_flag("glass_badge_checked")
    if has_flag("got_sealed_drive"):
        "The badge and the drive share the same archive number."
    jump explore


label archive_locked_cabinet:
    "The cabinet is jammed shut."
    if not has_flag("archive_evidence_decided"):
        "A terminal decision probably opens the next step."
    elif char_stat("cora", "trust") < 1:
        "Cora would know the trick, if she trusted you enough to share it."
    jump explore


label archive_locked_cabinet_open:
    "Cora's hint works. The cabinet opens just far enough to reveal a handwritten map."
    $ set_flag("cabinet_map_found")
    $ cora.trust(1, "no")
    jump explore


label archive_terminal_force:
    "Bree watches while you bypass the terminal's damaged prompt."
    b "That was either clever or irresponsible."
    $ bree.trust(1, "no")
    $ set_flag("archive_terminal_forced")
    jump archive_terminal_decode


label archive_terminal_decode:
    if not has_item("sealed_drive"):
        "The terminal asks for a drive that is not attached."
        jump explore

    $ begin_dialogue("bree", pos="left")
    $ dialogue_show("cora", pos="right")
    b "The drive matches the noticeboard code."
    c "Or someone made it match after the fact."

    $ branch_point("archive_evidence_method")
    $ menu_side("middle")
    menu:
        "Cross-check the drive against the badge.":
            $ take_branch("archive_evidence_method", "crosscheck")
            $ set_route("evidence")
            $ bree.trust(1, "3d")
            b "Good. We test the story before we trust it."
        "Follow Cora's warning and isolate the drive.":
            $ take_branch("archive_evidence_method", "isolate")
            $ set_route("caution")
            $ cora.trust(1, "3d")
            c "Finally, someone here likes not being predictable."
        "Decode it directly." if char_stat("bree", "trust") >= 2:
            $ take_branch("archive_evidence_method", "direct")
            $ set_route("bold")
            b "Risky. But yes, that is faster."

    $ set_flag("archive_evidence_decided")
    $ set_flag("archive_evidence_done")
    $ end_dialogue()
    jump explore


label use_sealed_drive_on_archive_terminal(item_id=None, target=None):
    "You slide the sealed drive into the terminal's side port."
    jump archive_terminal_decode


label use_glass_badge_on_locked_cabinet(item_id=None, target=None):
    if not has_flag("archive_evidence_decided"):
        "The badge reflects the cabinet's warped glass, but you do not know what to compare yet."
    elif has_flag("cabinet_map_found"):
        "The badge has already done its job here."
    else:
        "You hold the scraped badge against the cabinet's label frame."
        "The old latch catches on the badge's edge, then gives."
        $ set_flag("cabinet_map_found")
        $ cora.trust(1, "no")
        "(The cabinet opens far enough to reveal a handwritten map.)"
    jump explore
