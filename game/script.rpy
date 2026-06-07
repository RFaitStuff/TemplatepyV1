label start:
    show screen hud

    $ _seed_unlocked_rooms()
    call _register_all_quests
    call _register_all_branches
    $ auto_register_character_interactables()

    $ set_flag("quest_noticeboard")

    call story_opening

    jump explore


label explore:
    $ exit_dialogue()
    $ flush_stamina_cost()
    $ _bg = location_bg()
    scene expression "bg " + _bg
    $ show_all_npcs_here()

    $ _on_enter = location_on_enter_label()
    if _on_enter:
        call expression _on_enter

    call screen location_nav(npcs_here=npcs_here())

    jump explore


label nav_left:
    $ go_prev_location()
    jump explore

label nav_right:
    $ go_next_location()
    jump explore


label talk_unknown:
    "(Oh well something weird happened in the game...)"
    jump explore
