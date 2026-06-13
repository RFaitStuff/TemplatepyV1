# =============================================================================
# Item definitions
# =============================================================================
# Define author-created inventory data here. The inventory mechanic only owns
# runtime behavior such as add/remove/has/count.
# =============================================================================

init -1 python:
    define_item("lost_pen", name="A Lost Pen", desc="Cheap-looking pen. Someone dropped it.", tags=["misc"])
    define_item("note", name="Folded Note", desc="Handwriting you don't recognize.", tags=["paper", "clue"])
    define_item("coin", name="Coin", desc="Spare change.", tags=["misc", "gift"])
    define_item("archive_key", name="Archive Key", desc="A small brass key tagged with a room number nobody uses.", tags=["key", "school"], quest_item=True)
    define_item("coded_slip", name="Coded Slip", desc="A noticeboard scrap covered in room names and arrows.", tags=["paper", "clue"], quest_item=True)
    define_item("sealed_drive", name="Sealed Drive", desc="An old storage drive wrapped in library tape.", tags=["tech", "clue"], quest_item=True)
    define_item("glass_badge", name="Glass Badge", desc="A brittle badge with the name scratched away.", tags=["clue"], quest_item=True)
    define_item("matched_badge_clue", name="Matched Badge Clue", desc="The badge number and slip arrows line up into a room code.", tags=["clue"], quest_item=True)

    item_use(
        "archive_key",
        "archive_door",
        label="use_archive_key_on_archive_door",
        consume=False,
        fail="The key fits the lock, but something is still blocking the mechanism.",
    )

    item_use(
        "*",
        "archive_door",
        fail="I don't think {item_name} will work on this door.",
        always_fail=True,
    )

    item_use(
        "sealed_drive",
        "archive_terminal",
        label="use_sealed_drive_on_archive_terminal",
        consume=False,
        fail="The terminal has a drive slot, but this is not the right time to connect it.",
    )

    item_use(
        "glass_badge",
        "locked_cabinet",
        label="use_glass_badge_on_locked_cabinet",
        requires=req("flag:archive_evidence_decided"),
        consume=False,
        fail="The badge belongs here somehow, but the cabinet clue is not ready yet.",
    )

    recipe("coded_slip", "glass_badge", result="matched_badge_clue")
    combine_fail("archive_key", "lost_pen", "The pen is not going to make the key any more convincing.")
