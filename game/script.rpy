label start:
    call run_startup_screens

    if not player_setup_done:
        call screen player_identity_setup

    show screen hud

    $ _seed_unlocked_rooms()
    $ apply_save_migrations()
    
    call _register_all_branches
    $ auto_register_character_interactables()

    $ set_flag("quest_noticeboard")

    call story_opening

    jump explore


label explore:
    $ exit_dialogue()
    $ flush_stamina_cost()
    $ _entered_location = record_location_entry()
    $ _bg = location_bg()
    scene expression "bg " + _bg
    show screen location_visual_layers()
    $ show_all_npcs_here()

    if _entered_location:
        $ _first_visit = location_first_visit_label() if first_visit() else None
        if _first_visit:
            call expression _first_visit

        $ _first_visit_today = location_first_visit_today_label() if first_visit_today() else None
        if _first_visit_today:
            call expression _first_visit_today

        $ _on_enter = location_on_enter_label()
        if _on_enter:
            call expression _on_enter

    $ _main_loop = location_main_loop_label()
    if _main_loop:
        call expression _main_loop

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
