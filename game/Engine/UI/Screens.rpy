# =============================================================================
# Engine/Common/Screens.rpy - shared popup screens (Quest log, Stats, Inventory, etc)
# -----------------------------------------------------------------------------
# The HUD, the in-room navigation, and the choice override now live in:
#   game/Engine/UI/HUD.rpy       (HUD bar + side notifications)
#   game/Engine/UI/Locations.rpy (location_nav with exits + interactables)
#   game/Engine/UI/Choice.rpy    (animated, side-aware choice menu)
#
# This file keeps the "open from a HUD button" popups: quest log, stats sheet,
# inventory, gallery, branch visualizer.
# =============================================================================


# =============================================================================
# OPTIONAL UI - shared popup frame style
# =============================================================================
screen _popup_frame(title="", on_close="self"):
    add "#000000c8"
    frame:
        align (0.5, 0.5)
        xsize 980
        ysize 680
        background "#1a1a1aee"
        padding (24, 24)
        vbox:
            spacing 12
            hbox:
                xfill True
                text "[title]" size 30 color "#ffd27a"
                textbutton "X" xalign 1.0 action [Function(_dev_set_open_ui, None), Hide(on_close)]
            transclude


# =============================================================================
# OPTIONAL UI - Quest Log
# =============================================================================
screen quest_log():
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "quest_log")
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("quest_log")]
    default _quest_tab = "active"
    default _selected_quest_id = None

    $ _active_quests = visible_active_quests()
    $ _completed_quests = visible_completed_quests()
    $ _quest_list = _active_quests if _quest_tab == "active" else _completed_quests
    $ _visible_ids = [q.id for q in _quest_list]
    if _selected_quest_id not in _visible_ids:
        if tracked_quest_id in _visible_ids:
            $ _selected_quest_id = tracked_quest_id
        elif _visible_ids:
            $ _selected_quest_id = _visible_ids[0]
        else:
            $ _selected_quest_id = None
    $ _selected_quest = quest(_selected_quest_id) if _selected_quest_id else None

    add "#05040bcc"

    fixed:
        align (0.5, 0.5)
        xysize (1120, 760)

        add Transform("assets/images/UI/HUD/Quest/Background.png", xysize=(1001, 729)):
            xpos 70
            ypos 10

        imagebutton:
            idle ("assets/images/UI/HUD/Quest/active_H.png" if _quest_tab == "active" else "assets/images/UI/HUD/Quest/active.png")
            hover "assets/images/UI/HUD/Quest/active_H.png"
            xpos 8
            ypos 55
            action SetScreenVariable("_quest_tab", "active")

        imagebutton:
            idle ("assets/images/UI/HUD/Quest/Completed_H.png" if _quest_tab == "completed" else "assets/images/UI/HUD/Quest/Completed.png")
            hover "assets/images/UI/HUD/Quest/Completed_H.png"
            xpos 8
            ypos 385
            action SetScreenVariable("_quest_tab", "completed")

        frame:
            background None
            xpos 150
            ypos 80
            xsize 420
            ysize 600

            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"
                vbox:
                    spacing 6

                    button:
                        xysize (390, 72)
                        background ("#301c45cc" if _selected_quest_id is None and not tracked_quest_id else "#11131f88")
                        hover_background "#3b225bcc"
                        action [SetScreenVariable("_selected_quest_id", None), Function(clear_tracked_quest)]
                        hbox:
                            spacing 18
                            yalign 0.5
                            text u"\u2298" size 34 color "#8f8f9f" yalign 0.5
                            text "Off" size 22 color "#f1edf7" yalign 0.5

                    if has_undiscovered_quests():
                        button:
                            xysize (390, 64)
                            background "#0c0f1888"
                            hover_background "#2b2140bb"
                            sensitive False
                            hbox:
                                spacing 14
                                yalign 0.5
                                text "?" size 28 color "#ff8de7" yalign 0.5
                                text "Undiscovered Quests" size 19 color "#c9c3d4" yalign 0.5

                    if not _quest_list:
                        text ("No completed quests yet." if _quest_tab == "completed" else "No active quests yet.") size 18 color "#8f8899" italic True xalign 0.5 yoffset 20

                    for _q in _quest_list:
                        $ _is_selected = (_selected_quest_id == _q.id)
                        $ _is_tracked = (tracked_quest_id == _q.id)
                        button:
                            xysize (390, 74)
                            background ("#3b1f59dd" if _is_selected else "#10131f77")
                            hover_background "#4a2670dd"
                            action ([SetScreenVariable("_selected_quest_id", _q.id), Function(set_tracked_quest, _q.id)] if _q.is_active else SetScreenVariable("_selected_quest_id", _q.id))

                            hbox:
                                spacing 14
                                yalign 0.5
                                if _q.character:
                                    frame:
                                        xysize (46, 46)
                                        background "#101722"
                                        text "[character_display_name(_q.character)[:1]]" size 22 color "#ff8de7" align (0.5, 0.5)
                                else:
                                    text (u"\u25c9" if _is_tracked else u"\u25c7") size 28 color ("#ff8de7" if _is_tracked else "#8b8396") yalign 0.5

                                vbox:
                                    yalign 0.5
                                    spacing 2
                                    text "[_q.title]" size 20 color "#f5edf7"
                                    if _q.is_completed:
                                        text "Completed" size 12 color "#9ce8b2"
                                    elif _q.is_failed:
                                        text "Failed" size 12 color "#ff8a8a"
                                    elif _is_tracked:
                                        text "Tracked" size 12 color "#ff8de7"

        add Solid("#ffffff22"):
            xpos 605
            ypos 80
            xsize 2
            ysize 600

        frame:
            background None
            xpos 640
            ypos 85
            xsize 410
            ysize 590

            if _selected_quest:
                $ _current_obj = quest_current_objective(_selected_quest)
                $ _done_objs = quest_completed_objectives(_selected_quest)
                vbox:
                    spacing 16
                    text "[_selected_quest.title]" size 34 color "#ff8de7"
                    if _selected_quest.description:
                        text "[_selected_quest.description]" size 20 color "#eeeaf2" line_spacing 8
                    else:
                        text "No description recorded." size 18 color "#8f8899" italic True

                    add Transform("assets/images/UI/HUD/Quest/separator.png", xysize=(330, 16)) xalign 0.0

                    text "Current Objective" size 21 color "#ff8de7"
                    if _current_obj:
                        hbox:
                            spacing 12
                            text u"\u25c7" size 22 color "#ff8de7" yalign 0.0
                            vbox:
                                spacing 4
                                text "[_current_obj.text]" size 18 color "#f5edf7"
                                $ _hint = quest_objective_hint(_selected_quest, _current_obj)
                                if _hint:
                                    text "[_hint]" size 14 color "#a9a0b5"
                    elif _selected_quest.is_completed:
                        text "All objectives complete." size 18 color "#9ce8b2"
                    else:
                        text "No current objective." size 18 color "#8f8899" italic True

                    if len(_selected_quest.objectives) > 1:
                        add Transform("assets/images/UI/HUD/Quest/separator.png", xysize=(330, 16)) xalign 0.0
                        text "Completed Objectives" size 21 color "#ff8de7"
                        if _done_objs:
                            for _obj in _done_objs:
                                hbox:
                                    spacing 10
                                    add Transform("assets/images/UI/HUD/Checkmark.png", xysize=(24, 24)) yalign 0.5
                                    text "{s}[_obj.text]{/s}" size 17 color "#9f98aa"
                        else:
                            text "None yet." size 16 color "#8f8899" italic True
            else:
                vbox:
                    spacing 16
                    text "No Quest Tracked" size 34 color "#ff8de7"
                    text "Select an active quest on the left to track it, or leave tracking off to explore without guidance." size 20 color "#eeeaf2" line_spacing 8
                    if has_undiscovered_quests():
                        add Transform("assets/images/UI/HUD/Quest/separator.png", xysize=(330, 16)) xalign 0.0
                        text "Undiscovered Quests" size 21 color "#ff8de7"
                        text "Some quests are hidden until you talk to the right person, inspect the right object, or trigger their story flag." size 17 color "#c9c3d4" line_spacing 6

        hbox:
            align (0.5, 0.98)
            spacing 18
            text "Esc" size 18 color "#f5edf7"
            text "Close" size 22 color "#f5edf7"


# =============================================================================
# OPTIONAL UI - Stats Sheet (player + characters)
# =============================================================================
screen player_identity_setup():
    tag menu
    modal True
    default _first = player_first_name
    default _last = player_last_name
    default _color = player_name_color

    add "#05040bf2"

    frame:
        align (0.5, 0.5)
        xysize (760, 520)
        background "#10111af2"
        padding (34, 30)

        vbox:
            spacing 22
            text "Player Setup" size 36 color "#ff8de7"

            vbox:
                spacing 8
                text "First Name" size 18 color "#f5edf7"
                input:
                    value ScreenVariableInputValue("_first")
                    length 24
                    size 28
                    color "#ffffff"
                    caret "#ff8de7"

            vbox:
                spacing 8
                text "Last Name" size 18 color "#f5edf7"
                input:
                    value ScreenVariableInputValue("_last")
                    length 24
                    size 28
                    color "#ffffff"
                    caret "#ff8de7"

            vbox:
                spacing 8
                text "Name Color" size 18 color "#f5edf7"
                hbox:
                    spacing 10
                    for _label, _value in PLAYER_NAME_COLORS:
                        button:
                            xysize (56, 42)
                            background _value
                            hover_background _value
                            selected (_color == _value)
                            action SetScreenVariable("_color", _value)
                            tooltip _label
                            if _color == _value:
                                text "✓" align (0.5, 0.5) size 24 color "#10111a"

            text "[_first or 'Taylor'] [_last]" size 24 color _color

            textbutton "Start":
                xalign 1.0
                text_size 24
                background "#623c91dd"
                hover_background "#7a4cb0dd"
                padding (22, 12)
                action [Function(set_player_identity, _first, _last, _color), Return()]


screen stats_sheet():
    tag popup
    modal True
    zorder 200
    use characters_panel()


# =============================================================================
# OPTIONAL UI - Inventory
# =============================================================================
screen inventory_panel():
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "inventory_panel")
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("inventory_panel")]
    use _inventory_phone_shell_body("inventory_panel", "inventory")


screen inventory_phone_shell(initial_app="stats"):
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "inventory_phone_shell", initial_app=initial_app)
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("inventory_phone_shell")]
    use _inventory_phone_shell_body("inventory_phone_shell", initial_app)


screen _inventory_phone_shell_body(host_screen="inventory_panel", initial_app="inventory"):
    default _selected_item = None

    $ _apps = visible_phone_apps()
    $ _app_ids = [app["id"] for app in _apps]
    $ _phone_app = phone_active_app or initial_app
    if _phone_app not in _app_ids:
        $ _phone_app = "stats" if "stats" in _app_ids else (_app_ids[0] if _app_ids else None)
    if phone_active_app != _phone_app:
        $ phone_active_app = _phone_app
    $ _inv = inventory_visible_items()
    $ _item_ids = [item_id for item_id, count in _inv]
    if _selected_item not in _item_ids:
        $ _selected_item = _item_ids[0] if _item_ids else None

    add "#05040bcc"
    button:
        xfill True
        yfill True
        background "#00000000"
        action [Function(_dev_set_open_ui, None), Hide(host_screen)]

    fixed:
        align (0.5, 0.5)
        xysize (1240, 720)

        frame:
            xpos 0
            ypos 0
            xsize 470
            ysize 720
            background "#0b0d17f2"
            padding (18, 18)

            vbox:
                spacing 14
                hbox:
                    xfill True
                    text "PHONE" size 28 color "#ff8de7"
                    textbutton "X":
                        xalign 1.0
                        text_size 22
                        action [Function(_dev_set_open_ui, None), Hide(host_screen)]

                viewport:
                    xfill True
                    ysize 54
                    mousewheel True
                    draggable True
                    hbox:
                        spacing 8
                        for _app in _apps:
                            $ _aid = _app["id"]
                            textbutton _app["label"]:
                                text_size 15
                                background ("#623c91dd" if _phone_app == _aid else "#141927cc")
                                hover_background "#7a4cb0dd"
                                padding (10, 8)
                                action SetVariable("phone_active_app", _aid)

                frame:
                    xfill True
                    yfill True
                    background "#11131fcc"
                    padding (18, 18)

                    if _phone_app == "stats":
                        use _phone_stats_app()
                    elif _phone_app == "notes":
                        use _phone_notes_app()
                    elif _phone_app == "messages":
                        use _phone_list_app("Messages", phone_visible_entries(phone_messages), "No messages yet.")
                    elif _phone_app == "contacts":
                        use _phone_contacts_app()
                    elif _phone_app == "tutorials":
                        use _phone_list_app("Tutorials", phone_visible_entries(phone_tutorials_seen), "No tutorials unlocked yet.")
                    elif _phone_app == "achievements":
                        use _phone_list_app("Achievements", phone_achievement_rows(), "No achievements unlocked yet.")
                    elif _phone_app == "gallery":
                        use _phone_gallery_app()
                    else:
                        use _phone_list_app("Phone", [], "Nothing here yet.")

        frame:
            xpos 500
            ypos 0
            xsize 740
            ysize 720
            background "#10111af2"
            padding (22, 22)

            hbox:
                spacing 22
                xfill True
                yfill True

                frame:
                    xsize 330
                    yfill True
                    background "#080a12cc"
                    padding (14, 14)

                    vbox:
                        spacing 12
                        text "BAG" size 30 color "#ffd27a"
                        if not _inv:
                            text "(empty)" size 18 color "#8f8899" italic True
                        else:
                            viewport:
                                mousewheel True
                                draggable True
                                scrollbars "vertical"
                                yfill True
                                vbox:
                                    spacing 8
                                    for _id, _count in _inv:
                                        $ _selected = (_selected_item == _id)
                                        button:
                                            xfill True
                                            background ("#3b1f59dd" if _selected else "#141927cc")
                                            hover_background "#4a2670dd"
                                            padding (10, 10)
                                            action SetScreenVariable("_selected_item", _id)
                                            hbox:
                                                spacing 10
                                                $ _icon = item_icon(_id)
                                                if _icon:
                                                    add Transform(_icon, xysize=(42, 42)) yalign 0.5
                                                else:
                                                    frame:
                                                        xysize (42, 42)
                                                        background "#232838"
                                                        text "[item_name(_id)[:1]]" size 20 color "#ffd27a" align (0.5, 0.5)
                                                vbox:
                                                    yalign 0.5
                                                    spacing 2
                                                    text "[item_name(_id)]" size 18 color "#f5edf7"
                                                    text "x[_count]" size 13 color "#a9a0b5"

                frame:
                    xfill True
                    yfill True
                    background "#0b0d17cc"
                    padding (18, 18)

                    use _bag_item_detail(_selected_item)


screen _bag_item_detail(item_id=None):
    if item_id:
        $ _tags = item_tags(item_id)
        vbox:
            spacing 16
            text "[item_name(item_id)]" size 32 color "#ff8de7"
            text "[item_desc(item_id)]" size 19 color "#eeeaf2" line_spacing 6
            if _tags:
                hbox:
                    spacing 8
                    for _tag in _tags:
                        text "[_tag]" size 13 color "#c9c3d4" outlines [(1, "#000000")]
            add Solid("#ffffff22") xsize 330 ysize 1
            hbox:
                spacing 10
                textbutton "Use":
                    text_size 18
                    background "#623c91cc"
                    hover_background "#7a4cb0dd"
                    padding (14, 8)
                    action Function(use_item, item_id)
                textbutton "Examine":
                    text_size 18
                    background "#252b3bcc"
                    hover_background "#343d55dd"
                    padding (14, 8)
                    action Function(examine_item, item_id)
                textbutton "Combine":
                    text_size 18
                    background "#252b3bcc"
                    hover_background "#343d55dd"
                    padding (14, 8)
                    sensitive (len(inventory_visible_items()) > 1 or item_count(item_id) > 1)
                    action Show("inventory_item_picker", prompt="Combine with what?", combine_with=item_id)
    else:
        vbox:
            spacing 12
            text "No Item Selected" size 32 color "#ff8de7"
            text "Pick something from the bag to inspect it or use it." size 19 color "#eeeaf2" line_spacing 6


screen inventory_item_picker(prompt="Use what?", target=None, item_filter=None, combine_with=None, allow_any_item=False):
    tag item_picker
    modal True
    zorder 240
    key "game_menu" action Hide("inventory_item_picker")

    $ _mode = "combine" if combine_with else "use"
    $ _items = inventory_items_matching(requirement=item_filter, target=target if _mode == "use" else None, combine_with=combine_with, allow_any_target=allow_any_item)

    add "#05040bcc"
    button:
        xfill True
        yfill True
        background "#00000000"
        action Hide("inventory_item_picker")

    frame:
        align (0.5, 0.5)
        xsize 520
        ysize 620
        background "#10111af2"
        padding (22, 22)

        vbox:
            spacing 14
            hbox:
                xfill True
                text prompt size 28 color "#ff8de7"
                textbutton "X":
                    xalign 1.0
                    text_size 22
                    action Hide("inventory_item_picker")

            if not _items:
                text "Nothing in your bag fits this." size 18 color "#8f8899" italic True
            else:
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    vbox:
                        spacing 8
                        for _id, _count in _items:
                            button:
                                xfill True
                                background "#141927cc"
                                hover_background "#4a2670dd"
                                padding (12, 10)
                                action ([Function(combine_items, combine_with, _id), Hide("inventory_item_picker")] if _mode == "combine" else [Function(use_item_on, _id, target), Hide("inventory_item_picker")])
                                hbox:
                                    spacing 12
                                    $ _icon = item_icon(_id)
                                    if _icon:
                                        add Transform(_icon, xysize=(44, 44)) yalign 0.5
                                    else:
                                        frame:
                                            xysize (44, 44)
                                            background "#232838"
                                            text "[item_name(_id)[:1]]" size 20 color "#ffd27a" align (0.5, 0.5)
                                    vbox:
                                        yalign 0.5
                                        spacing 2
                                        text "[item_name(_id)]" size 18 color "#f5edf7"
                                        text "x[_count]" size 13 color "#a9a0b5"


screen _phone_stats_app():
    vbox:
        spacing 14
        text "Player Stats" size 28 color "#ff8de7"
        frame:
            xfill True
            background "#141927cc"
            padding (12, 10)
            vbox:
                spacing 4
                text "[player_display_name()]" size 24 color player_name_color
                text "Protagonist" size 13 color "#a9a0b5"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 10
                for _row in player_stat_rows():
                    vbox:
                        spacing 2
                        hbox:
                            xfill True
                            text _row["label"] size 19 color _row["color"]
                            text "[_row['value_text']]" size 19 color "#ffd27a" xalign 1.0
                        if _row["perks"]:
                            text "Perks: [_row['perks_text']]" size 12 color "#a9a0b5"


screen quest_panel():
    tag popup
    modal True
    zorder 210
    on "show" action Function(_dev_set_open_ui, "quest_panel")
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("quest_panel")]

    add "#05040bcc"
    button:
        xfill True
        yfill True
        background "#00000000"
        action [Function(_dev_set_open_ui, None), Hide("quest_panel")]

    frame:
        align (0.5, 0.5)
        xsize 980
        ysize 680
        background "#10111af2"
        padding (26, 24)

        use _quest_log_app()


screen _quest_log_app():
    $ _active = visible_active_quests()
    $ _completed = visible_completed_quests()
    default _selected_quest = tracked_quest_id
    $ _all_quests = _active + _completed
    if _selected_quest and not any(q.id == _selected_quest for q in _all_quests):
        $ _selected_quest = None
    if _selected_quest is None and _active:
        $ _selected_quest = _active[0].id
    $ _quest = quest(_selected_quest) if _selected_quest else None

    hbox:
        spacing 26
        xfill True
        yfill True

        frame:
            xsize 390
            yfill True
            background "#080a12cc"
            padding (16, 16)

            vbox:
                spacing 12
                text "Quests" size 30 color "#ff8de7"
                textbutton "Tracking Off":
                    xfill True
                    text_size 18
                    background ("#3b1f59dd" if not tracked_quest_id else "#141927cc")
                    hover_background "#4a2670dd"
                    padding (12, 9)
                    action [Function(clear_tracked_quest), SetScreenVariable("_selected_quest", None)]

                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    vbox:
                        spacing 8
                        if not _active and not _completed:
                            text "No quests logged yet." size 17 color "#8f8899" italic True
                        for _q in _active:
                            button:
                                xfill True
                                background ("#3b1f59dd" if _selected_quest == _q.id else "#141927cc")
                                hover_background "#4a2670dd"
                                padding (10, 9)
                                action [SetScreenVariable("_selected_quest", _q.id), Function(set_tracked_quest, _q.id)]
                                vbox:
                                    spacing 2
                                    text "[_q.title]" size 17 color "#f5edf7"
                                    $ _obj = quest_current_objective(_q)
                                    if _obj:
                                        text "[_obj.text]" size 13 color "#a9a0b5"
                        if _completed:
                            text "Completed" size 18 color "#ffd27a" yoffset 8
                        for _q in _completed:
                            button:
                                xfill True
                                background ("#241b2fcc" if _selected_quest == _q.id else "#11131fcc")
                                hover_background "#342246cc"
                                padding (10, 9)
                                action SetScreenVariable("_selected_quest", _q.id)
                                text "[_q.title]" size 16 color "#8f8899"

        frame:
            xfill True
            yfill True
            background "#0b0d17cc"
            padding (24, 22)

            if not _quest:
                vbox:
                    spacing 12
                    text "No Quest Selected" size 32 color "#ff8de7"
                    text "Choose a quest to view its objective details." size 19 color "#eeeaf2"
            else:
                $ _current = quest_current_objective(_quest)
                $ _completed_objs = [o for o in _quest.objectives if getattr(o, "done", False)]
                vbox:
                    spacing 18
                    text "[_quest.title]" size 34 color "#ff8de7"
                    text "[_quest.description]" size 20 color "#eeeaf2" line_spacing 6
                    add Solid("#ffffff22") xfill True ysize 1
                    text "Current Objective" size 22 color "#ffd27a"
                    if _current:
                        text "[_current.text]" size 19 color "#f5edf7"
                    else:
                        text "Completed." size 19 color "#a9a0b5" italic True
                    if _completed_objs:
                        add Solid("#ffffff22") xfill True ysize 1
                        text "Completed Objectives" size 22 color "#ffd27a"
                        for _obj in _completed_objs:
                            text "[_obj.text]" size 17 color "#8f8899" strikethrough True


screen _phone_contacts_app():
    $ _contacts = visible_phone_contacts()
    vbox:
        spacing 14
        text "Contacts" size 28 color "#ff8de7"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 8
                if not _contacts:
                    text "No contacts yet." size 17 color "#8f8899" italic True
                for _contact in _contacts:
                    $ _cname = _contact.get("name", _contact.get("id", "Contact"))
                    $ _cinitial = _cname[:1] if _cname else "?"
                    hbox:
                        spacing 10
                        if _contact.get("avatar"):
                            add Transform(_contact.get("avatar"), xysize=(42, 42)) yalign 0.5
                        else:
                            frame:
                                xysize (42, 42)
                                background "#232838"
                                text "[_cinitial]" size 20 color "#ff8de7" align (0.5, 0.5)
                        vbox:
                            yalign 0.5
                            spacing 2
                            text "[_cname]" size 18 color "#f5edf7"
                            if _contact.get("status"):
                                text "[_contact.get('status')]" size 13 color "#a9a0b5"


screen phone_dialog_overlay():
    zorder 35
    if phone_dialog_state:
        $ _side = phone_dialog_state.get("side", "left")
        $ _contact = phone_dialog_state.get("contact")
        $ _mode = phone_dialog_state.get("mode", "phone_message")
        $ _title = phone_dialog_state.get("title") or (character_display_name(_contact) if _contact else "Phone")
        $ _body = phone_dialog_state.get("body")
        frame:
            xalign (0.08 if _side == "left" else 0.92 if _side == "right" else 0.5)
            yalign 0.18
            xsize 330
            background "#0b0d17ef"
            padding (16, 12)
            vbox:
                spacing 6
                text ("CALL" if "call" in _mode else "MESSAGE") size 12 color "#8f8899"
                text "[_title]" size 22 color "#ff8de7"
                if _body:
                    text "[_body]" size 16 color "#f5edf7"


screen _phone_list_app(title, entries, empty_text):
    vbox:
        spacing 14
        text title size 28 color "#ff8de7"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 10
                if not entries:
                    text empty_text size 17 color "#8f8899" italic True
                for _entry in entries:
                    $ _line = phone_entry_text(_entry)
                    text "[_line]" size 17 color "#f5edf7" line_spacing 5


screen _phone_notes_app():
    $ _notes = phone_visible_entries(phone_notes)
    vbox:
        spacing 14
        text "Notes" size 28 color "#ff8de7"
        if not _notes:
            text "No notes yet." size 17 color "#8f8899" italic True
        else:
            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"
                yfill True
                vbox:
                    spacing 12
                    for _note in _notes:
                        frame:
                            xfill True
                            background "#141927cc"
                            padding (12, 10)
                            vbox:
                                spacing 6
                                text _note.get("title", "Note") size 20 color "#ffd27a"
                                if _note.get("body"):
                                    text _note.get("body") size 16 color "#f5edf7" line_spacing 4
                                for _task in visible_phone_note_rows(_note):
                                    if isinstance(_task, dict):
                                        $ _done = phone_note_task_done(_task)
                                        $ _task_text = _task.get("text", "")
                                        $ _rendered_task = ("[x] {s}" + _task_text + "{/s}") if _done else "[ ] " + _task_text
                                        text _rendered_task:
                                            size 16
                                            color ("#8f8899" if _done else "#f5edf7")
                                            line_spacing 4
                                    else:
                                        text str(_task) size 16 color "#f5edf7" line_spacing 4


screen _phone_gallery_app():
    $ _unlocked = [s for s in gallery_scenes if is_gallery_unlocked(s["id"])]
    vbox:
        spacing 14
        text "Gallery" size 28 color "#ff8de7"
        if not _unlocked:
            text "No replayable scenes unlocked yet." size 17 color "#8f8899" italic True
        else:
            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"
                yfill True
                vbox:
                    spacing 8
                    for _s in _unlocked:
                        textbutton _s["title"]:
                            text_size 17
                            background "#141927cc"
                            hover_background "#4a2670dd"
                            padding (10, 8)
                            action Function(play_gallery, _s["id"])


# =============================================================================
# OPTIONAL UI - Gallery (replays scenes without mutating game state)
# =============================================================================
screen gallery_panel():
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "gallery_panel")
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("gallery_panel")]

    $ W = config.screen_width
    $ H = config.screen_height

    add Solid("#000000")

    $ gallery_bg_size = (int(W * 0.76), int(H * 0.72))
    fixed:
        xpos int(W * 0.12)
        ypos int(H * 0.08)
        xsize gallery_bg_size[0]
        ysize gallery_bg_size[1]
        add Transform("assets/images/UI/HUD/Characters/Facts.png", xysize=gallery_bg_size)
        frame:
            background None
            padding (34, 30)
            xfill True
            yfill True
            vbox:
                spacing 18
                hbox:
                    xfill True
                    text "GALLERY":
                        font "assets/fonts/Blinko-Demo-Regular-BF69eaf9992b8b0.otf"
                        size 72
                        color "#ffffff"
                        outlines [(2, "#00000099")]
                    textbutton "X":
                        xalign 1.0
                        yalign 0.5
                        text_size 28
                        action [Function(_dev_set_open_ui, None), Hide("gallery_panel")]
                use _gallery_scene_grid(gallery_scenes)


screen _gallery_scene_grid(scenes=[]):
    viewport:
        scrollbars "vertical"
        mousewheel True
        ysize 520
        vbox:
            spacing 18
            if not scenes:
                text "No replayable scenes unlocked yet." color "#888888" italic True
            $ _rows = [scenes[i:i+3] for i in range(0, len(scenes), 3)]
            for _row in _rows:
                hbox:
                    spacing 10
                    for _s in _row:
                        $ _unlocked = is_gallery_unlocked(_s["id"])
                        $ _title    = _s["title"] if _unlocked else "(locked)"
                        $ _thumb    = _s.get("thumbnail") if _unlocked else None
                        button:
                            xysize (260, 200)
                            background "#000000"
                            hover_background "#ffffff20"
                            sensitive _unlocked
                            action Function(play_gallery, _s["id"])
                            vbox:
                                if _thumb:
                                    add _thumb xysize (260, 150)
                                else:
                                    frame:
                                        xysize (260, 150)
                                        background "#222222"
                                        text "?" align (0.5, 0.5) size 60 color "#666666"
                                text "[_title]" size 14 color ("#ffffff" if _unlocked else "#666666") xalign 0.5


init python:

    def quest_current_objective(q):
        if not q:
            return None
        for objective in getattr(q, "objectives", []):
            if not objective.done and not objective.optional:
                return objective
        for objective in getattr(q, "objectives", []):
            if not objective.done:
                return objective
        return None

    def quest_completed_objectives(q):
        if not q:
            return []
        return [objective for objective in getattr(q, "objectives", []) if objective.done]

    def quest_objective_hint(q, objective):
        if not q or not objective:
            return None
        target = getattr(objective, "target", None) or getattr(q, "target", None) or {}
        if target.get("targets"):
            names = []
            for entry in target.get("targets", [])[:4]:
                try:
                    names.append(_target_display_name(entry))
                except Exception:
                    names.append("Target")
            suffix = "" if len(target.get("targets", [])) <= 4 else " +" + str(len(target.get("targets", [])) - 4)
            return "Guidance: multiple targets - " + ", ".join(names) + suffix
        precision = str(target.get("guide_precision", target.get("tracking", getattr(q, "guide_precision", "exact"))) or "exact").lower()
        if precision in ("none", "hidden", "off"):
            return "Tracking hint hidden. Read the quest text and explore."
        if precision in ("area", "region"):
            area = target.get("area")
            if not area and target.get("location"):
                area = location_area_id(target.get("location"))
            return "Guidance: area only" + ((" - " + area_data(area).get("name", str(area).title())) if area else "")
        if precision in ("location", "loc"):
            loc = target.get("location")
            return "Guidance: location only" + ((" - " + location_name(loc)) if loc else "")
        if precision in ("characters", "multi_character", "multi-character"):
            chars = target.get("characters") or ([target.get("npc")] if target.get("npc") else [])
            if chars:
                return "Guidance: character locations - " + ", ".join(character_display_name(cid) for cid in chars)
            return "Guidance: character location"
        return None

    CHARACTER_ORDER = ["alice", "alex"]

    def _dev_set_open_ui(screen_name, **kwargs):
        setattr(persistent, "dev_open_ui_screen", screen_name)
        setattr(persistent, "dev_open_ui_kwargs", kwargs)
        return None

    def _dev_open_ui_screen():
        return getattr(persistent, "dev_open_ui_screen", None)

    def _dev_restore_open_ui():
        screen_name = _dev_open_ui_screen()
        if not screen_name:
            return None
        try:
            if renpy.get_screen(screen_name):
                return None
            kwargs = getattr(persistent, "dev_open_ui_kwargs", {}) or {}
            renpy.show_screen(screen_name, **kwargs)
        except Exception:
            pass
        return None

    def _safe_int(v, default=0):
        try:
            return int(v)
        except Exception:
            return default

    def _char_state(cid):
        try:
            return ensure_character_state(cid)
        except Exception:
            return character_stats.get(cid, {})

    def _char_name(cid):
        try:
            return character_display_name(cid)
        except Exception:
            return cid.title()

    def _char_location_text(cid):
        try:
            loc = npc_location(cid)
            return location_name(loc) if loc else "Unknown"
        except Exception:
            return "Unknown"

    def _char_portrait(cid):
        try:
            return npc_clickable_image(cid)
        except Exception:
            return None

    def _char_facts(cid):
        try:
            return character_fact_rows(cid)
        except Exception:
            return []

    def _char_mood(cid, key):
        try:
            return _safe_int(character_stats.get(cid, {}).get("moods", {}).get(key, 0))
        except Exception:
            return 0

    def _char_stat(cid, key):
        try:
            return _safe_int(character_stats.get(cid, {}).get(key, 0))
        except Exception:
            return 0

    def _open_character_gallery(cid):
        renpy.hide_screen("characters_panel")
        _dev_set_open_ui("character_gallery_view", char_id=cid)
        renpy.show_screen("character_gallery_view", char_id=cid)

    def visible_phone_apps():
        out = []
        for app_id in globals().get("phone_app_order", []):
            app = globals().get("phone_app_defs", {}).get(app_id, {})
            requirement = app.get("requires")
            if not requirement:
                out.append(app)
                continue
            try:
                if meets_requirements(requirement):
                    out.append(app)
            except Exception:
                out.append(app)
        return out

    def phone_achievement_rows():
        try:
            return visible_achievement_rows()
        except Exception:
            rows = []
            for achievement in sorted(getattr(persistent, "achievements", set())):
                rows.append({"title": achievement, "body": "Unlocked"})
            return rows

    def player_stat_rows():
        rows = []
        defs = globals().get("PLAYER_STAT_DEFS", {}) or {}
        for key, data in defs.items():
            if data.get("hidden"):
                continue
            value = _safe_int(globals().get(key, data.get("default", 0)))
            max_value = data.get("max")
            perks = active_perks(key) if "active_perks" in globals() else []
            rows.append({
                "id": key,
                "label": data.get("label", key),
                "value": value,
                "value_text": "{}/{}".format(value, max_value) if max_value is not None else str(value),
                "color": data.get("color") or "#f5edf7",
                "icon": data.get("icon"),
                "perks": perks,
                "perks_text": ", ".join([perk.get("title", perk.get("id", "")) for perk in perks]),
            })
        return rows

    def phone_entry_text(entry):
        if isinstance(entry, dict):
            title = entry.get("title") or entry.get("label") or entry.get("name") or ""
            body = entry.get("body") or entry.get("text") or entry.get("desc") or ""
            if title and body:
                return "{} - {}".format(title, body)
            return title or body or str(entry)
        return str(entry)


screen _stat_tile(
        tile_image,
        value,
        tile_size=(180, 90),
        tile_zoom=1.0,
        value_color="#f7f7f7",
        value_size=48,
        value_xalign=0.5,
        value_yalign=0.5,
        value_xoffset=0,
        value_yoffset=0,
    ):
    $ _tile_w, _tile_h = tile_size
    fixed:
        xsize _tile_w
        ysize _tile_h
        # TAG: tweak tile_zoom/tile_size/value_offset to control background scale and number position.
        add Transform(tile_image, zoom=tile_zoom, xysize=tile_size)
        text "[value]":
            size value_size
            color value_color
            xalign value_xalign
            yalign value_yalign
            xoffset value_xoffset
            yoffset value_yoffset


screen _fact_block(label, value, unlocked=True):
    frame:
        xfill True
        background ("#0f141d88" if unlocked else "#0b0e1488")
        padding (12, 10)

        vbox:
            spacing 4
            text label size 18 color ("#ffd08c" if unlocked else "#677184")
            text value size 16 color ("#e8edf7" if unlocked else "#4d5564")


screen characters_panel(bg_image=None):
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "characters_panel")
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("characters_panel")]

    default _selected_char = "alice"
    default _hover_char = None

    $ W = config.screen_width
    $ H = config.screen_height

    $ _chars = [cid for cid in CHARACTER_ORDER if cid in character_stats]
    if not _chars:
        $ _chars = list(character_stats.keys())

    if _selected_char not in _chars and _chars:
        $ _selected_char = _chars[0]

    $ _active_char = _hover_char if _hover_char in _chars else _selected_char
    $ _data = _char_state(_active_char) if _active_char else {}
    $ _name = _char_name(_active_char) if _active_char else "Character"
    $ _loc = _char_location_text(_active_char) if _active_char else ""
    $ _portrait = _char_portrait(_active_char) if _active_char else None
    $ _facts = _char_facts(_active_char) if _active_char else []

    $ _love = _char_stat(_active_char, "love")
    $ _lust = _char_stat(_active_char, "lust")
    $ _trust = _char_stat(_active_char, "trust")
    $ _respect = _char_stat(_active_char, "respect")
    $ _love_text = "%d/100" % _love
    $ _lust_text = "%d/100" % _lust
    $ _trust_text = "%d/100" % _trust
    $ _respect_text = "%d/100" % _respect

    $ _happy = _char_mood(_active_char, "happy")
    $ _angry = _char_mood(_active_char, "angry")
    $ _nervous = _char_mood(_active_char, "nervous")
    $ _sad = _char_mood(_active_char, "sad")

    $ _max_mood = float(mood_max_intensity if mood_max_intensity else 1)

    $ _mood_len_happy   = int(120 * _happy   / _max_mood)
    $ _mood_len_angry   = int(120 * _angry   / _max_mood)
    $ _mood_len_nervous = int(120 * _nervous / _max_mood)
    $ _mood_len_sad     = int(120 * _sad     / _max_mood)

    add Solid("#000000")

    if bg_image:
        add bg_image:
            alpha 0.25

    fixed:
        xpos int(W * 0.03)
        ypos int(H * 0.03)
        xsize int(W * 0.28)
        ysize int(H * 0.78)

        # TAG: adjust name text/heart icon position & zoom here.
        hbox:
            xpos -40
            ypos -30
            spacing 20
            text _name.upper():
                font "assets/fonts/Blinko-Demo-Regular-BF69eaf9992b8b0.otf"
                size 120
                color "#ffffff"
                outlines [(2, "#00000099")]
            add Transform("assets/images/UI/HUD/Characters/Heart.png", zoom=1.13, ypos=0.28, xpos=-0.2)

        # TAG: adjust location icon/text alignment here.
        hbox:
            xpos 45
            ypos 80
            spacing 10
            add Transform("assets/images/UI/HUD/Characters/Location.png", zoom=0.7)
            text _loc:
                size 22
                color "#cfd6e8"
                yalign 0.5

        if _portrait:
            add _portrait:
                xpos -150
                ypos 130
                zoom 0.60
                alpha 0.98

        add Solid("#00000000"):
            xpos 0
            ypos 126
            xsize int(W * 0.26)
            ysize int(H * 0.63)

    $ stats_bg_size = (int(W * 0.34), int(H * 0.29))
    $ stats_bg_zoom = 1.0
    fixed:
        xpos 0.305
        ypos 0.05
        xsize stats_bg_size[0]
        ysize stats_bg_size[1]
        # TAG: adjust stats_bg_zoom/stats_bg_size to resize the Stats.png container.
        add Transform("assets/images/UI/HUD/Characters/Stats.png", zoom=stats_bg_zoom, xysize=stats_bg_size)
        frame:
            background None
            padding (24, 28)
            xfill True
            yfill True

            grid 2 2:
                xspacing 8
                yspacing 8

                use _stat_tile("assets/images/UI/HUD/Characters/Love.png", _love_text, tile_size=(300, 130), tile_zoom=1.0, value_color="#eca8c5", value_size=34, value_yoffset=24, value_xoffset=21)
                use _stat_tile("assets/images/UI/HUD/Characters/Lust.png", _lust_text, tile_size=(300, 130), tile_zoom=1.0, value_color="#d9a3e9", value_size=34, value_yoffset=24, value_xoffset=51)
                use _stat_tile("assets/images/UI/HUD/Characters/Trust.png", _trust_text, tile_size=(300, 130), tile_zoom=1.0, value_color="#7eb8e7", value_size=34, value_yoffset=24, value_xoffset=21)
                use _stat_tile("assets/images/UI/HUD/Characters/Respect.png", _respect_text, tile_size=(300, 130), tile_zoom=1.0, value_color="#d5ebca", value_size=34, value_yoffset=24, value_xoffset=31)

    $ mood_bg_size = (int(W * 0.34), int(H * 0.373))
    $ mood_bg_zoom = 1.0
    fixed:
        xpos 0.305
        ypos 0.355
        xsize mood_bg_size[0]
        ysize mood_bg_size[1]
        # TAG: adjust mood_bg_zoom/mood_bg_size to resize the mood graph art.
        add Transform("assets/images/UI/HUD/Characters/Mood.png", zoom=mood_bg_zoom, xysize=mood_bg_size)
        frame:
            background None
            padding (18, 18)
            xfill True
            yfill True

            add Solid("#ffffff55"):
                xpos 288
                ypos 175
                xysize (10, 10)



            vbox:
                xpos 280
                ypos 2
                spacing 2
                # TAG: adjust angry icon zoom here.
                add Transform("assets/images/UI/HUD/Characters/Angry.png", zoom=1.15) xalign 0.5
                
                text "[_angry]" size 24 color "#ffffff" xalign 0.5 ypos 0.2

            vbox:
                xpos 98
                ypos 125
                spacing 2
                # TAG: adjust sad icon zoom here.
                add Transform("assets/images/UI/HUD/Characters/Sad.png", zoom=1.15) xalign 0.5
                
                text "[_sad]" size 24 color "#ffffff" xalign 0.5 ypos 0.2

            vbox:
                xpos 480
                ypos 125
                spacing 2
                # TAG: adjust happy icon zoom here.
                add Transform("assets/images/UI/HUD/Characters/Happy.png", zoom=1.15) xalign 0.5
                
                text "[_happy]" size 24 color "#ffffff" xalign 0.5 ypos 0.2

            vbox:
                xpos 269
                ypos 272
                spacing 2
                # TAG: adjust nervous icon zoom here.
                add Transform("assets/images/UI/HUD/Characters/Nervous.png", zoom=1.1) xalign 0.5
                
                text "[_nervous]" size 24 color "#ffffff" xalign 0.5 ypos 0.2

    $ facts_bg_size = (int(W * 0.32), int(H * 0.677))
    $ facts_bg_zoom = 1.0
    fixed:
        xpos 0.653
        ypos 0.05
        xsize facts_bg_size[0]
        ysize facts_bg_size[1]
        # TAG: adjust facts_bg_zoom/facts_bg_size to resize the facts panel image.
        add Transform("assets/images/UI/HUD/Characters/Facts.png", zoom=facts_bg_zoom, xysize=facts_bg_size)
        frame:
            background None
            padding (18, 18)
            xfill True
            yfill True

            vbox:
                spacing 12

                add "assets/images/UI/HUD/Characters/facts_text.png"

                for _fact in _facts:
                    use _fact_block(
                        _fact.get("label", ""),
                        _fact.get("text", ""),
                        _fact.get("unlocked", True)
                    )

    frame:
        xpos 0
        ypos int(H * 0.83)
        xsize W
        ysize int(H * 0.17)
        background "#00000000"
        padding (18, 0)

        viewport:
            mousewheel True
            draggable True
            xfill True
            yfill True

            hbox:
                spacing 14

                for _cid in _chars:
                    $ _is_hover = (_hover_char == _cid)
                    $ _cname = _char_name(_cid)
                    $ _cimg = _char_portrait(_cid)

                    button:
                        xysize (182, 166)
                        background ("assets/images/UI/HUD/Characters/Card_Hovered.png" if _is_hover else "assets/images/UI/HUD/Characters/Card.png")
                        hover_background "assets/images/UI/HUD/Characters/Card_Hovered.png"
                        action [SetScreenVariable("_selected_char", _cid), Function(_open_character_gallery, _cid)]
                        hovered SetScreenVariable("_hover_char", _cid)
                        unhovered SetScreenVariable("_hover_char", None)

                        fixed:
                            xysize (182, 166)

                            if _cimg:
                                add _cimg:
                                    xpos 18
                                    ypos (-6 if _is_hover else 6)
                                    zoom (0.26 if _is_hover else 0.22)
                                    alpha (1.0 if _is_hover else 0.52)

                            add Solid("#00000088"):
                                xpos 0
                                ypos 112
                                xsize 182
                                ysize 54

                            text _cname:
                                xpos 0
                                ypos 120
                                xsize 182
                                size 16
                                color "#ffffff"
                                text_align 0.5

    $ _return_idle = Transform("assets/images/UI/HUD/Characters/Return.png", zoom=1.2)
    $ _return_hover = Transform("assets/images/UI/HUD/Characters/Return.png", zoom=1.3, matrixcolor=TintMatrix("#8c00ff7a"))
    imagebutton:
        idle _return_idle
        hover _return_hover
        xpos 0.95
        ypos 0.01
        action [Function(_dev_set_open_ui, None), Hide("characters_panel")]


screen character_gallery_view(char_id):
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "character_gallery_view", char_id=char_id)
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("character_gallery_view")]

    add Solid("#000000")

    $ W = config.screen_width
    $ H = config.screen_height
    $ gallery_bg_size = (int(W * 0.76), int(H * 0.72))

    fixed:
        xpos int(W * 0.12)
        ypos int(H * 0.08)
        xsize gallery_bg_size[0]
        ysize gallery_bg_size[1]
        add Transform("assets/images/UI/HUD/Characters/Facts.png", xysize=gallery_bg_size)
        frame:
            background None
            padding (34, 30)
            xfill True
            yfill True
            vbox:
                spacing 18
                hbox:
                    xfill True
                    text "[character_display_name(char_id).upper()] GALLERY":
                        font "assets/fonts/Blinko-Demo-Regular-BF69eaf9992b8b0.otf"
                        size 58
                        color "#ffffff"
                        outlines [(2, "#00000099")]
                    textbutton "Back":
                        xalign 1.0
                        yalign 0.5
                        text_size 24
                        action [Function(_dev_set_open_ui, "characters_panel"), Hide("character_gallery_view"), Show("characters_panel")]
                use _gallery_scene_grid(character_gallery_scenes(char_id))


# =============================================================================
# OPTIONAL UI - Branch Visualizer
# -----------------------------------------------------------------------------
# Lists every registered branch point grouped by depth (parent->child).
# - Visited branches show your chosen path in green and unchosen options in
#   grey, plus a "Replay from here" button that loads the auto-save written
#   by branch_point() so you can take the other path.
# - Unvisited branches show as locked.
# - Cross-playthrough visited tracking (persistent.branches_visited) lets the
#   player see paths they've taken in OTHER saves too.
# =============================================================================
screen branch_visualizer():
    tag popup
    modal True
    zorder 200
    on "show" action Function(_dev_set_open_ui, "branch_visualizer")
    key "game_menu" action [Function(_dev_set_open_ui, None), Hide("branch_visualizer")]
    use _popup_frame(title="Branches", on_close="branch_visualizer"):
        viewport:
            scrollbars "vertical"
            mousewheel True
            ysize 580
            vbox:
                spacing 14
                $ _tree = branch_tree()
                if not _tree:
                    text "No branches registered yet." color "#888888" italic True

                for _bid, _bdef, _depth in _tree:
                    $ _btitle = _bdef["title"]
                    $ _seen   = _bid in persistent.branches_seen
                    $ _taken  = branch_choice_taken(_bid)
                    $ _xoff   = _depth * 24

                    frame:
                        xfill True
                        xoffset _xoff
                        background "#0e0e0eaa"
                        padding (16, 12)
                        vbox:
                            spacing 6

                            # ---- header ----
                            hbox:
                                spacing 10
                                text "[_btitle]" size 20 color ("#ffd27a" if _seen else "#666666")
                                if _taken:
                                    $ _taken_title = _bdef["choices"][_taken]["title"]
                                    text "- chose:" size 14 color "#888888"
                                    text "[_taken_title]" size 14 color "#aef0ae"
                                elif _seen:
                                    text "- (not chosen yet)" size 14 color "#cccccc"
                                else:
                                    text "- (not encountered)" size 14 color "#666666"

                            # ---- choice list ----
                            for _cid, _cdef in _bdef["choices"].items():
                                $ _ctitle     = _cdef["title"]
                                $ _was        = (_bid, _cid) in persistent.branches_visited
                                $ _is_current = (_taken == _cid)
                                hbox:
                                    spacing 8
                                    xoffset 16
                                    if _is_current:
                                        text "[[*]" size 14 color "#aef0ae"
                                    elif _was:
                                        text "[[+]" size 14 color "#7fb3ff"
                                    else:
                                        text "[[ ]" size 14 color "#555555"
                                    text "[_ctitle]" size 14 color ("#ffffff" if (_was or _is_current) else "#888888")

                            # ---- rewind button ----
                            if _seen:
                                $ _slot = "branch_" + _bid
                                textbutton "Replay from here":
                                    xalign 1.0
                                    text_size 14
                                    action [Hide("branch_visualizer"), FileLoad(_slot, slot=True, confirm=False)]

