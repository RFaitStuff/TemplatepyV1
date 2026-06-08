# Alex dialogue labels. Talk registration lives in Game/Characters/Dialogue/Alex_Talk.rpy.

label talk_alex:
    $ _pending_interactable_id = "alex"
    call _character_talk_dispatch
    return


label interact_alex:
    call alex_default_interact
    return


label quest_alex:
    call alex_default_interact
    return


label alex_art_room_extra:
    a2 "Alice gets the dramatic corner. I get the paint water."
    show alice
    a "You chose the paint water."
    a2 "And I stand by my art."
    return


label alex_default_interact:
    a2 "Yo. What are we doing?"
    menu (side="left"):
        "Make her happy.":
            $ alex.happy()
            a2 "Ha. Whatever you say."
        "Make her sad.":
            $ alex.sad()
            a2 "...why."
        "Flirt.":
            $ react("alex", "blush")
            $ player.Lust.d3 += 1
            a2 "Pfft. Try harder."
            $ react("alex")
        "Show my Lust breakdown.":
            $ _bd = player_stat_breakdown("Lust")
            $ _bd_str = ", ".join("%s=%s" % (k, v) for k, v in _bd.items())
            "Lust contributions: [_bd_str]"
    return
