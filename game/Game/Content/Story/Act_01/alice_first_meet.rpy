# =============================================================================
# zStory/MainStory/Memories/alice_first_meet.rpy
# =============================================================================
# Standalone memory unlocked once the player completes the "meet_alice" quest.
# Single label, registered as a Gallery scene. Replays use the SAME label
# inside renpy.call_replay, which sandboxes state changes (see Gallery.rpy).
# =============================================================================

init python:
    register_gallery_scene(
        gallery_id="alice_first_meet",
        title="First Meeting",
        label="alice_first_meet",
        thumbnail="bg classroom1",
        group="Memories",
    )


label alice_first_meet:
    scene bg classroom1
    $ show_npc("alice", pos=(0.5, 1.0))
    a "...do I know you?"
    "(A memory. Or a re-introduction. Hard to tell, this early in the day.)"
    a "Either way - hi."
    return
