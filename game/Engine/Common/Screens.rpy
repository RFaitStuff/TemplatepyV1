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
    use _popup_frame(title="Quest Log", on_close="quest_log"):
        vbox:
            spacing 12
            hbox:
                xfill True
                spacing 12
                $ _pin_enabled = bool(tracked_quest_id)
                $ _pin_on = bool(tracked_quest_id and not hud_hide_objective)
                text ("Tracked: " + quest_log[tracked_quest_id].title if tracked_quest_id in quest_log else "Tracked: None") size 16 color "#cccccc" yalign 0.5
                textbutton (u"\u2605 Hide Objective" if _pin_on else u"\u2606 Show Objective"):
                    xalign 1.0
                    text_size 16
                    text_color ("#ffd27a" if _pin_on else "#888888")
                    text_hover_color "#ffd27a"
                    sensitive _pin_enabled
                    action Function(toggle_tracked_quest_pin)

            viewport:
                scrollbars "vertical"
                mousewheel True
                ysize 530
                vbox:
                    spacing 18
                    $ _tree = quest_tree()
                    if not _tree:
                        text "No quests yet." color "#888888" italic True
                    for _cat, _qs in _tree.items():
                        text "[_cat!c]" size 22 color "#7fb3ff"
                        for _q in _qs:
                            vbox:
                                xoffset 12
                                spacing 2
                                hbox:
                                    xfill True
                                    spacing 8
                                    textbutton "[_q.title]":
                                        text_size 20
                                        text_color ("#ffd27a" if tracked_quest_id == _q.id else "#ffffff")
                                        text_hover_color "#ffd27a"
                                        action Function(toggle_tracked_quest, _q.id)
                                    if _q.is_completed:
                                        text "(done)" size 14 color "#aef0ae"
                                    elif _q.is_failed:
                                        text "(failed)" size 14 color "#ff8a8a"
                                    elif tracked_quest_id == _q.id and _q.is_active:
                                        text "(tracked)" size 14 color "#ffd27a"
                                if _q.description:
                                    text "[_q.description]" size 14 color "#cccccc"
                                for _o in _q.objectives:
                                    if _o.done:
                                        text "{s}[_o.text]{/s}" size 13 color "#aef0ae"
                                    else:
                                        text "[_o.text]" size 13 color "#cccccc"


# =============================================================================
# OPTIONAL UI - Stats Sheet (player + characters)
# =============================================================================
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
    use _popup_frame(title="Inventory", on_close="inventory_panel"):
        viewport:
            scrollbars "vertical"
            mousewheel True
            ysize 580
            vbox:
                spacing 12
                $ _inv = inventory_list()
                if not _inv:
                    text "(empty)" color "#888888" italic True
                for _id, _n in _inv:
                    hbox:
                        spacing 12
                        text "[item_name(_id)] x[_n]" size 18 color "#ffffff" min_width 320
                        text "[item_desc(_id)]" size 14 color "#cccccc"


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
                        font "assets/gui/Fonts/Blinko-Demo-Regular-BF69eaf9992b8b0.otf"
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
                font "assets/gui/Fonts/Blinko-Demo-Regular-BF69eaf9992b8b0.otf"
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
                        font "assets/gui/Fonts/Blinko-Demo-Regular-BF69eaf9992b8b0.otf"
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

