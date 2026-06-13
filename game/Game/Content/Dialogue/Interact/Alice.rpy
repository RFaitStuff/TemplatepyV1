# Alice dialogue labels. Talk registration lives in Game/Characters/Dialogue/Alice_Talk.rpy.

# Compatibility for old direct jumps/calls.
label talk_alice:
    $ _pending_interactable_id = "alice"
    call _character_talk_dispatch
    return


label interact_alice:
    call alice_default_interact
    return


label quest_alice:
    # Quest-specific labels can be selected by quest target {"label": "..."}.
    call alice_quest_meet
    return


# -----------------------------------------------------------------------------
# Talk entries
# -----------------------------------------------------------------------------
label alice_homeroom_morning_fact:
    a "Mornings are the only time this room is bearable."
    a "Before the bell rings, it almost feels like the day has not made up its mind yet."
    return


label alice_art_room_fact:
    a "I come here when the rest of campus gets too loud."
    a "Paint is easier than people. It only lies when you water it down."
    return


label alice_evening_extra:
    a "[rline('Long day, huh.', 'You stayed late too.', 'I was hoping I would run into you.')]"
    menu (side="left"):
        "Want to head home together?":
            $ alice.happy()
            $ alice.love.d3 += 1
            a "Please."
        "Just checking in.":
            $ alice.trust.d3 += 1
            a "Go on, get some rest."
    return


label alice_club_room_group_talk:
    a "Hey. I claim the couch."
    show alex
    a2 "Move over. Half is mine."
    menu (side="middle"):
        "Sit with Alice.":
            $ alice.stats(love=1, trust=1, cd="3d")
            a "Five minutes. Then you owe me coffee."
        "Tease Alex instead.":
            a2 "Pft. Wrong choice."
            $ alex.trust.d3 += 1
            $ react("alice", "sad")
            a "...rude."
            $ react("alice")
        "Just stand there awkwardly.":
            $ set_status("alice", "tired", True)
            a "...okay."
    return


# -----------------------------------------------------------------------------
# Interactions
# -----------------------------------------------------------------------------
label alice_default_interact:
    $ start_quest("meet_alice")
    $ set_flag("met_alice")
    a "[mline('alice', default=['What did you need?', 'You have that look again.', 'Alright. I am listening.'], happy=['Hey you.'], sad=['...yeah?'], tired=['Mmgh. What is it?'])]"
    menu (side="left"):
        "Ask how she is feeling.":
            $ alice.trust.d3 += 1
            a "[rline('Tired. But better, now.', 'Hanging in there.', 'Just glad you asked.')]"
        "Compliment her focus.":
            $ react("alice", "embarrassed")
            a "...you're lucky no one else heard that."
            $ react("alice")
            $ alice.love += 1
            $ alice.lust.d3 += 1
            $ player.Lust.d3 += 1
        "Invite her to skip class.":
            $ alice.happy()
            $ alice.love.no += 2
            $ set_flag("alice_skip_offered")
            a "Tempting. Ask me again after lunch."
        "Be cold to her.":
            $ alice.sad()
            $ alice.stats(love=-1, trust=-1)
            a "...okay. Got it."

    $ set_flag("talked_alice")
    if is_quest_completed("meet_alice") and not has_flag("meet_alice_rewarded"):
        $ set_flag("meet_alice_rewarded")
        $ unlock_gallery("alice_first_meet")
        "{i}Memory saved to the gallery.{/i}"
    return


label alice_art_room_interact:
    a "Don't look. It's not done."
    menu (side="right"):
        "Let me see anyway.":
            $ react("alice", "embarrassed")
            a "...fine. Just don't say anything cruel."
            $ react("alice")
            $ alice.trust.d3 += 1
        "I'll wait.":
            $ alice.happy()
            a "Thank you."
    return


label alice_club_room_interact:
    a "If this is about the couch, I am not moving."
    menu (side="middle"):
        "Claim the other side.":
            $ alice.love.d3 += 1
            a "Acceptable."
        "Ask what she is working on.":
            $ alice.trust.d3 += 1
            a "Nothing official. Just trying to make a messy thought sit still."
    return


# -----------------------------------------------------------------------------
# Quest scenes
# -----------------------------------------------------------------------------
label alice_quest_meet:
    a "You found me."
    a "Was there something you needed, or were you just making sure I still exist?"
    $ set_flag("met_alice")
    $ set_flag("talked_alice")
    return


label alice_ch1_followup:
    a "Morning. You looked like you were a thousand miles away on the roof."
    $ react("alice", "happy")
    a "Glad you came back."
    $ react("alice")
    $ alice.trust.no += 1
    $ set_flag("ch1_followup_done")
    return


label alice_roof_signal:
    $ start_quest("alice_roof_scene")
    $ begin_dialogue("alice", pos="left")
    a "The noticeboard looked different today."
    a "I thought maybe I was the only one who noticed."
    $ menu_side("middle")
    menu:
        "Tell Alice the whole truth.":
            $ alice.trust(2, "no")
            a "Okay. Then I am in this with you."
        "Make the confident joke. {color=#ffd27a}(Coolness 10){/color}" if can("stat:Coolness>=10"):
            $ alice.love(1, "no")
            $ set_flag("alice_roof_cool_joke")
            a "That was awful. I feel better anyway."
        "Tell Alice how much she matters. {color=#ffd27a}(Alice Love 10){/color}" if can("Alice.Love>=10"):
            $ set_flag("alice_love_10_scene_seed")
            a "...you cannot just say that on a roof and expect me to stay normal."
        "Keep the strange part back.":
            $ mood("alice", "nervous", 2)
            a "I can tell when you are protecting me from a sentence."
    $ set_flag("alice_roof_signal_choice")
    $ set_flag("alice_roof_signal_done")
    $ end_dialogue()
    return


label alice_roof_aftercare:
    $ begin_dialogue("alice", pos="right")
    a "I keep replaying the roof conversation."
    a "Not the scary parts. The part where you stayed."
    $ alice.trust(1, "3d")
    $ set_flag("alice_roof_aftercare_done")
    $ end_dialogue()
    return


label alice_private_signal_scene:
    scene bg smp_roof
    show alice at left
    a "This feels less like a clue now."
    a "More like a promise."
    $ set_flag("alice_private_signal_scene_done")
    $ unlock_gallery("alice_private_signal_scene")
    return
