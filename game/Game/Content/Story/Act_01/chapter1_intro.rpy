# =============================================================================
# zStory/MainStory/Introduction/chapter1_intro.rpy
# =============================================================================
# Chapter 1 opening narrative.
#
# Single label that runs ONCE in the live game (triggered by roof_on_enter)
# and is also registered as a Gallery memory. Gallery replays use the SAME
# label - no rewriting, no parallel "_replay" copy. State changes inside the
# scene are sandboxed by Ren'Py's call_replay (see Engine/Gallery.rpy):
#   - all `default`-declared store vars are restored on return
#   - persistent unlocks and other side-effects are gated on `_in_replay`
#
# To see how the gating works, search for `_in_replay` in:
#   Engine/Gallery.rpy   (unlock_gallery)
# =============================================================================


init python:
    gallery_scene(
        "ch1_intro",
        title="Chapter 1 - Introduction",
        label="chapter1_intro",
        thumbnail="mainstory story1",
        group="Main",
        unlock="flag:ch1_intro_seen",
    )


# =============================================================================
# story_opening - first scene of the game (called from script.start).
# Sets the initial flags + objectives. Not a replayable memory.
# =============================================================================
label story_opening:
    $ phone_contact("alice", name="Alice", status="Quiet places above the school.")
    $ phone_tutorial("inventory_phone", title="Bag And Phone", body="Open your bag to check items, quests, notes, messages, contacts, badges, and gallery memories.")
    $ phone_note("first_morning", title="First Morning", body="The school is open. Alice is somewhere nearby.")
    $ phone_text("alice", "Are you already at school?", contact="alice")
    $ mark_milestone("started_story")
    "Morning sunlight pools across an empty desk."
    "You arrive early - early enough that the halls still feel like they belong to you."

    $ set_flag("quest_meet_alice")
    $ set_flag("quest_found_pen")
    "{i}New objectives: Catch up with Alice. Pick up that lost pen.{/i}"
    return


# =============================================================================
# Chapter 1 itself.
# Triggered live by roof_on_enter on the player's first roof visit.
# Replayable from Gallery -> "Chapter 1 - Introduction".
# =============================================================================
label chapter1_intro:
    scene mainstory story1 with fade
    "The town below is half-asleep, the kind of quiet that almost feels staged."
    "Streetlamps flicker out one by one as the sky bruises into pink and gold."

    scene mainstory story2 with dissolve
    "The school sits at the top of the hill - older than anyone who teaches there now."
    "You take the stairs two at a time. You used to do that with someone else."

    scene mainstory story3 with dissolve
    "Inside, the halls remember every footstep that ever crossed them."
    "Lockers tick as the metal cools. The bell tower is still wrong by a minute."

    "{i}You wonder if Alice still remembers the way you used to find each other in this exact light.{/i}"

    scene mainstory story4 with dissolve
    "Then the sun spills through the east windows and the day begins again."
    "Whatever's coming, it starts here."

    # Live-only side-effects. unlock_gallery is a no-op during replay
    # (gated on _in_replay inside Engine/Gallery.rpy).
    $ set_flag("ch1_intro_seen")
    $ unlock_gallery("ch1_intro")
    return
