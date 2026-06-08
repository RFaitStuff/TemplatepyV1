# =============================================================================
# Alice Dialogue
# -----------------------------------------------------------------------------
# Repeatable Talk is registered as data. Longer choice scenes stay as labels.
# =============================================================================


init 10 python:
    # Facts: once every 5 days.
    register_character_talk(
        "alice",
        "homeroom_morning_fact",
        kind="fact",
        label="alice_homeroom_morning_fact",
        locations="homeroom",
        times="day",
    )
    register_character_talk(
        "alice",
        "art_room_fact",
        kind="fact",
        label="alice_art_room_fact",
        locations="art_room",
        times="afternoon",
    )

    # Extras: once every 3 days, can contain choices/stat changes.
    register_character_talk(
        "alice",
        "ch1_followup",
        kind="extra",
        label="alice_ch1_followup",
        available_if=(lambda: has_flag("ch1_intro_seen") and not has_flag("ch1_followup_done")),
        cooldown_days=0,
    )
    register_character_talk(
        "alice",
        "evening_extra",
        kind="extra",
        label="alice_evening_extra",
        times="evening",
    )
    register_character_talk(
        "alice",
        "club_group_extra",
        kind="extra",
        label="alice_club_room_group_talk",
        locations="club_room",
        times="evening",
    )

    # Basics: always available fallback when richer talk is exhausted.
    register_character_talk("alice", "basic_period", kind="basic", line="I can't wait for this period to be over.")
    register_character_talk("alice", "basic_hi", kind="basic", line="Oh - hey.")
    register_character_talk("alice", "basic_mood", kind="basic", line="I'm here. That's something, right?")

    # Interact routes can also be filtered by location/time/mood.
    register_character_interact("alice", "default", "alice_default_interact")
    register_character_interact("alice", "art_room", "alice_art_room_interact", locations="art_room", priority=5)
    register_character_interact("alice", "club_room", "alice_club_room_interact", locations="club_room", priority=5)

