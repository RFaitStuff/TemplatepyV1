# =============================================================================
# zStory/MainStory/Memories/alice_first_meet.rpy
# =============================================================================
# Standalone memory unlocked once the player completes the "meet_alice" quest.
# Single label, registered as a Gallery scene. Replays use the SAME label
# inside renpy.call_replay, which sandboxes state changes (see Gallery.rpy).
# =============================================================================

init python:
    gallery_scene(
        "alice_first_meet",
        title="First Meeting",
        thumbnail="bg classroom1",
        group="Memories",
        character="alice",
        unlock="flag:alice_first_meet_seen",
    )


label alice_first_meet:
    scene bg classroom1
    $ dialog_mode("phone_message", contact="alice", side="left", body="Meet me in homeroom?")
    $ show_npc("alice", pos=(0.5, 1.0))
    a "...do I know you?"
    "(A memory. Or a re-introduction. Hard to tell, this early in the day.)"
    a "Either way - hi."
    $ set_flag("alice_first_meet_seen")
    $ clear_dialog_mode()
    return
