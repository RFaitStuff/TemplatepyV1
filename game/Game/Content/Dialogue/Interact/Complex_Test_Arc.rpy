# =============================================================================
# Complex test arc dialogue
# =============================================================================
# Exercises quest labels, left/middle/right menus, multi-character dialogue,
# character branches, stat gates, mood changes, route flags, and interact APIs.
# =============================================================================

init python:
    gallery_auto(
        "bree_private_archive_scene",
        character="bree",
        group="Bree",
        unlock="flag:bree_private_archive_scene_done",
        scene_image="bg smp_classroom4",
    )
    gallery_auto(
        "cora_private_archive_scene",
        character="cora",
        group="Cora",
        unlock="flag:cora_private_archive_scene_done",
        scene_image="bg smp_classroom4",
    )

    register_character_talk(
        "bree",
        "archive_hint_basic",
        kind="basic",
        line="If the noticeboard starts making sense, that means someone made a mistake.",
    )
    register_character_talk(
        "bree",
        "archive_room_fact",
        kind="fact",
        label="bree_archive_room_fact",
        locations=["archive_room"],
        requires="flag:entered_archive_room",
    )
    register_character_interact(
        "bree",
        "review_evidence",
        label="bree_review_evidence",
        locations=["archive_room"],
        requires="flag:archive_evidence_decided",
        group="bree_archive",
        once=True,
        completion_flag="bree_review_evidence_done",
        priority=20,
    )
    register_character_interact(
        "bree",
        "hallway_followup",
        label="bree_hallway_followup",
        locations=["hallway"],
        requires="flag:archive_room_unlocked",
        group="bree_archive",
        once=True,
        completion_flag="bree_hallway_followup_done",
        priority=15,
    )
    register_character_interact(
        "bree",
        "roof_pressure",
        label="bree_roof_pressure",
        locations=["roof"],
        requires="flag:archive_evidence_decided",
        group="bree_archive",
        once=True,
        completion_flag="bree_roof_pressure_done",
        priority=15,
    )
    register_character_interact(
        "bree",
        "private_archive_scene",
        label="bree_private_archive_scene",
        locations=["archive_room"],
        group="bree_archive",
        special=True,
        completion_flag="bree_private_archive_scene_done",
        priority=100,
    )

    register_character_talk(
        "cora",
        "cora_basic",
        kind="basic",
        line="Do not confuse a clue with permission.",
    )
    register_character_talk(
        "cora",
        "cora_badge_fact",
        kind="fact",
        label="cora_badge_fact",
        locations=["archive_room"],
        requires="flag:glass_badge_checked",
    )
    register_character_interact(
        "cora",
        "cabinet_hint",
        label="cora_cabinet_hint",
        locations=["archive_room"],
        requires="flag:archive_evidence_decided",
        group="cora_archive",
        once=True,
        completion_flag="cora_cabinet_hint_done",
        priority=20,
    )
    register_character_interact(
        "cora",
        "front_warning",
        label="cora_front_warning",
        locations=["front"],
        requires="flag:complex_arc_available",
        group="cora_archive",
        once=True,
        completion_flag="cora_front_warning_done",
        priority=15,
    )
    register_character_interact(
        "cora",
        "archive_afterthought",
        label="cora_archive_afterthought",
        locations=["archive_room"],
        requires="flag:glass_badge_checked",
        group="cora_archive",
        once=True,
        completion_flag="cora_archive_afterthought_done",
        priority=15,
    )
    register_character_interact(
        "cora",
        "private_archive_scene",
        label="cora_private_archive_scene",
        locations=["archive_room"],
        group="cora_archive",
        special=True,
        completion_flag="cora_private_archive_scene_done",
        priority=100,
    )


label quest_bree_archive_briefing:
    $ begin_dialogue("bree", pos="left")
    b "You read the noticeboard."
    b "Good. That flyer is less a message and more a lockpick."

    $ menu_side("left")
    menu:
        "Ask why she was watching the board.":
            $ bree.trust(1, "3d")
            b "Because it changed after you arrived."
            b "Most people miss edits to the world when the sentence still sounds normal."
        "Ask who else knows.":
            $ cora.trust(1, "3d")
            b "Cora. She notices absences better than evidence."
        "Demand the short version.":
            $ bree.respect(1, "3d")
            b "Find the key in the hallway. Open the archive. Bring Cora if she tries to stop you."

    b "The key is taped under the hallway molding. If it is gone, this test is already more interesting."
    $ set_stamina_cost_multiplier(0.5)
    $ set_flag("bree_archive_briefed")
    $ end_dialogue()
    return


label bree_archive_room_fact:
    b "This room used to be indexed by hand. That means every missing file has a human shape."
    return


label cora_badge_fact:
    c "The badge case is staged. Real keepsakes collect dust unevenly."
    return


label bree_review_evidence:
    $ begin_dialogue("bree", pos="left")
    b "Evidence has weight. People pretend it has a voice."

    $ menu_side("right")
    menu:
        "Tell Bree the drive is enough." if has_item("sealed_drive"):
            $ bree.trust(1, "3d")
            b "Enough to begin. Never enough to finish."
        "Keep the room calm with pure confidence. {color=#ffd27a}(Coolness 10){/color}" if can("stat:Coolness>=10"):
            $ bree.love(2, "no")
            $ set_flag("bree_coolness_10_seen")
            b "That was obnoxiously composed."
            b "Do it again if anything starts falling apart."
        "Ask Bree to trust Cora." if can("Cora.Trust>=1"):
            $ bree.respect(1, "3d")
            b "That is a difficult ask. Which makes it useful."
        "Tell Bree you trust her completely. {color=#ffd27a}(Bree Love 10){/color}" if can("Bree.Love>=10"):
            $ set_flag("bree_love_10_confession")
            b "Careful. Complete trust can make people lazy."
            b "But... thank you."
        "Admit you are not sure.":
            $ mood("bree", "nervous", 2)
            b "Uncertainty is not failure. It is the part before lying."
    $ set_flag("bree_review_evidence_done")
    $ end_dialogue()
    return


label bree_hallway_followup:
    $ begin_dialogue("bree", pos="left")
    b "The hallway is the archive's waiting room."
    b "People decide whether they are brave here, then pretend the door made the decision."
    $ menu_side("left")
    menu:
        "Ask if she is brave.":
            $ bree.trust(1, "3d")
            b "No. I am prepared. People confuse those."
        "Say you are ready. {color=#ffd27a}(Coolness 10){/color}" if can("stat:Coolness>=10"):
            $ bree.respect(2, "no")
            b "You actually sound like it."
    $ set_flag("bree_hallway_followup_done")
    $ end_dialogue()
    return


label bree_roof_pressure:
    $ begin_dialogue("bree", pos="right")
    b "Up here, every story sounds smaller."
    b "That helps when the archive starts acting important."
    $ menu_side("right")
    menu:
        "Ask what she wants after this.":
            $ bree.love(1, "3d")
            b "A version of the school that does not need hidden rooms."
        "Promise to stay with her route. {color=#ffd27a}(Bree Love 10){/color}" if can("Bree.Love>=10"):
            $ set_flag("bree_love_10_roof_promise")
            b "Do not promise routes. Promise choices."
    $ set_flag("bree_roof_pressure_done")
    $ end_dialogue()
    return


label bree_private_archive_scene:
    $ begin_dialogue("bree", pos="middle")
    b "You finished the little circuit I left for you."
    b "Hallway. Archive. Roof. The three places where people decide what kind of witness they are."
    scene expression "bg smp_classroom4"
    show bree happy
    b "This is not a normal interaction anymore."
    b "This is the kind of scene that should feel earned: private framing, different pacing, and a consequence that can echo later."
    $ unlock_character_fact("bree", "secret")
    $ bree.love(1, "no")
    $ set_flag("bree_private_archive_scene_done")
    $ mark_milestone("archive_witness_bree")
    $ end_dialogue()
    jump explore


label cora_cabinet_hint:
    $ begin_dialogue("cora", pos="right")
    c "The cabinet latch catches on the left. Lift before you pull."
    $ cora.trust(1, "no")
    $ set_flag("cora_cabinet_hint_done")
    $ end_dialogue()
    return


label cora_front_warning:
    $ begin_dialogue("cora", pos="right")
    c "The noticeboard makes people look forward. I prefer looking at who stands behind them."
    $ menu_side("right")
    menu:
        "Ask who is behind you.":
            $ cora.trust(1, "3d")
            c "Today? Bree. Tomorrow depends on what you touch."
        "Tell Cora you already noticed. {color=#ffd27a}(Coolness 10){/color}" if can("stat:Coolness>=10"):
            $ cora.respect(2, "no")
            c "Good. Then I can stop speaking gently."
    $ set_flag("cora_front_warning_done")
    $ end_dialogue()
    return


label cora_archive_afterthought:
    $ begin_dialogue("cora", pos="left")
    c "The badge case is a confession wearing museum glass."
    $ menu_side("middle")
    menu:
        "Ask Cora why she cares.":
            $ cora.trust(1, "3d")
            c "Because people call old harm history when they want to stop apologizing."
        "Tell her you care about her version. {color=#ffd27a}(Cora Love 10){/color}" if can("Cora.Love>=10"):
            $ set_flag("cora_love_10_archive_vow")
            c "Then do not make my version smaller so it fits yours."
    $ set_flag("cora_archive_afterthought_done")
    $ end_dialogue()
    return


label cora_private_archive_scene:
    $ begin_dialogue("cora", pos="middle")
    c "You followed every warning instead of treating them like locked doors."
    scene expression "bg smp_classroom4"
    show cora worried
    c "So here is the real scene: not the clue, not the cabinet, not the drive."
    c "The archive was built to make someone doubt their own memory."
    $ unlock_character_fact("cora", "secret")
    $ cora.love(1, "no")
    $ set_flag("cora_private_archive_scene_done")
    $ mark_milestone("archive_witness_cora")
    $ end_dialogue()
    jump explore


label quest_cora_confrontation:
    $ begin_dialogue("cora", pos="right")
    $ dialogue_show("bree", pos="left")
    c "Bree brought you here fast."
    b "Cora would rather wait until the evidence gets embarrassed and leaves."
    c "I would rather not hand the story a knife."

    $ menu_side("middle")
    menu:
        "Let them argue while you listen.":
            $ set_flag("bree_cora_met_archive")
            $ bree.trust(1, "3d")
            $ cora.trust(1, "3d")
            b "Fine. Timeline first."
            c "Motive first. Timelines can be forged."
        "Ask Bree to summarize.":
            $ set_flag("bree_cora_met_archive")
            $ bree.respect(1, "3d")
            b "Someone moved a record, then planted three signs pointing at the move."
        "Ask Cora what scares her.":
            $ set_flag("bree_cora_met_archive")
            $ cora.trust(1, "3d")
            c "That the signs are for you, not from them."

    $ end_dialogue()
    return


label quest_bree_cora_choice:
    $ begin_dialogue("bree", pos="left")
    $ dialogue_show("cora", pos="right")
    b "We choose a working theory."
    c "No. We choose what damage we are willing to cause."

    $ branch_point("bree_cora_route")
    $ menu_side("right")
    menu:
        "Back Bree's reconstruction." if can("Bree.Trust>=1"):
            $ take_branch("bree_cora_route", "bree")
            $ set_route("bree")
            $ bree.love(1, "no")
            b "Then we follow the edits."
            c "And hope whoever edited them wanted to be followed."
        "Back Cora's warning." if can("Cora.Trust>=1"):
            $ take_branch("bree_cora_route", "cora")
            $ set_route("cora")
            $ cora.love(1, "no")
            c "Then we protect the people the archive points at."
            b "Protection can become obstruction."
        "Refuse both readings.":
            $ take_branch("bree_cora_route", "neutral")
            $ set_route("neutral")
            $ mood("bree", "angry", 2)
            $ mood("cora", "nervous", 2)
            b "That is not a theory."
            c "No. But it might be a conscience."
        "Name both of them as witnesses. {color=#ffd27a}(Coolness 10, Bree Love 10, Cora Love 10){/color}" if can("stat:Coolness>=10", "Bree.Love>=10", "Cora.Love>=10"):
            $ take_branch("bree_cora_route", "both")
            $ set_route("both")
            b "That is not a side."
            c "No. It is harder."
            b "Then it might be the first honest answer."

    $ set_flag("bree_cora_side_chosen")
    $ end_dialogue()
    return
