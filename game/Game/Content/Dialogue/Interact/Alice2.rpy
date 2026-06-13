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


label alex_supply_start:
    $ start_quest("alex_supply_run")
    a2 "I need a pen. Not a dramatic pen. A normal one."
    a2 "If you see one in the hallway, grab it for me."
    $ set_flag("quest_found_pen")
    $ set_flag("alex_supply_asked")
    return


label alex_supply_finish:
    if not has_item("lost_pen"):
        a2 "Still penless. Tragic."
    else:
        a2 "You found one."
        menu (side="right"):
            "Hand it over.":
                $ remove_item("lost_pen")
                $ alex.trust(1, "3d")
                a2 "Reliable. Weird look on you."
            "Trade it for a favor. {color=#ffd27a}(Coolness 10){/color}" if can("stat:Coolness>=10"):
                $ remove_item("lost_pen")
                $ alex.love(1, "no")
                a2 "Smooth. Annoying, but smooth."
        $ set_flag("alex_supply_done")
    return


label alex_art_tools_scene:
    scene bg smp_classroom4
    show alex at right
    a2 "Welcome to the official department of borrowed objects."
    a2 "You brought the pen, so you get first signature."
    $ set_flag("alex_art_tools_scene_done")
    $ unlock_gallery("alex_art_tools_scene")
    return
