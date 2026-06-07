default debug_all_actions_visible = False
default debug_dialogue_overlay = False

init -999 python:
    config.keymap.setdefault('debug_tools', [])
    config.keymap['debug_tools'].append('K_F10')

init python:
    def debug_open_tools_menu():
        try:
            if not system_enabled("debug_tools"):
                return
        except Exception:
            pass
        renpy.run(Show('debug_tools_menu'))

    config.underlay.append(renpy.Keymap(debug_tools=debug_open_tools_menu))
    if 'debug_dialogue_overlay' not in config.overlay_screens:
        config.overlay_screens.append('debug_dialogue_overlay')

    def _dialogue_debug_entry(cid, info):
        info = info or {}
        display_name = cid
        try:
            display_name = character_display_name(cid)
        except Exception:
            pass
        xalign = info.get('xalign', info.get('shown_xalign', 0.5))
        shown = info.get('shown_xalign', xalign)
        origin = info.get('origin_x', 0.5)
        manual = 'Y' if info.get('manual') else 'N'
        dbg = {}
        try:
            dbg = (_dialogue_debug_state or {}).get(cid, {})
        except Exception:
            dbg = {}
        dialogue_layer = 'Y' if dbg.get('dialogue_showing') else 'N'
        master_layer = 'Y' if dbg.get('master_showing') else 'N'
        show_ok = 'Y' if dbg.get('ok') else 'N'
        action = dbg.get('action', '')
        error = dbg.get('error', '')
        image = dbg.get('image', '')
        return display_name, xalign, shown, origin, manual, dialogue_layer, master_layer, show_ok, action, error, image

    def debug_add_character_stat(char_id, stat_name, amount):
        try:
            stat(char_id, stat_name, amount)
        except Exception:
            try:
                character_stats.setdefault(char_id, {})[stat_name] = character_stats.setdefault(char_id, {}).get(stat_name, 0) + amount
            except Exception:
                pass
        renpy.restart_interaction()

    def debug_add_character_mood(char_id, mood_name, amount):
        try:
            mood(char_id, mood_name, amount)
        except Exception:
            try:
                moods = character_stats.setdefault(char_id, {}).setdefault('moods', {})
                moods[mood_name] = moods.get(mood_name, 0) + amount
            except Exception:
                pass
        renpy.restart_interaction()

    def debug_set_all_actions_visible(value=True):
        global debug_all_actions_visible
        debug_all_actions_visible = bool(value)
        renpy.restart_interaction()

    def debug_toggle_dialogue_overlay(value=None):
        global debug_dialogue_overlay
        if value is None:
            debug_dialogue_overlay = not debug_dialogue_overlay
        else:
            debug_dialogue_overlay = bool(value)
        renpy.restart_interaction()

    def debug_unlock_all_gallery():
        try:
            for scene in gallery_scenes:
                unlock_gallery(scene.get('id'))
        except Exception:
            pass
        renpy.restart_interaction()

    def debug_lock_all_gallery():
        try:
            unlocked_gallery.clear()
        except Exception:
            pass
        renpy.restart_interaction()

    def debug_complete_all_quests():
        try:
            for q in quest_log.values():
                q.state = 'completed'
        except Exception:
            pass
        renpy.restart_interaction()

    def debug_unlock_all_locations():
        try:
            for loc_id in location_order:
                unlock_room(loc_id)
        except Exception:
            pass
        renpy.restart_interaction()

    def debug_lock_noninitial_locations():
        try:
            unlocked_rooms.clear()
            for loc_id in unlocked_rooms_init:
                unlock_room(loc_id)
        except Exception:
            pass
        renpy.restart_interaction()

    def debug_reset_seen_actions():
        try:
            seen_actions.clear()
        except Exception:
            pass
        renpy.restart_interaction()

    def debug_toggle_system(name):
        try:
            set_system_enabled(name, not system_enabled(name))
        except Exception:
            pass
        renpy.restart_interaction()

screen debug_tools_menu():
    modal True
    zorder 3000
    add Solid('#000000cc')
    frame:
        align (0.5, 0.5)
        xsize 720
        padding (30, 28)
        vbox:
            spacing 14
            text 'Debug Tools' size 36 color '#ffd27a' xalign 0.5
            textbutton '1 - Character Stats / Moods' action Show('debug_character_editor') text_size 24
            textbutton '2 - Action Visibility / Seen Data' action Show('debug_action_tools') text_size 24
            textbutton '3 - Unlockers / Lockers' action Show('debug_unlock_tools') text_size 24
            textbutton '4 - System Toggles' action Show('debug_system_toggles') text_size 24
            textbutton 'Layout Visualizer' action Show('layout_tool_visualizer') text_size 24
            textbutton ('Dialogue Overlay: ON' if debug_dialogue_overlay else 'Dialogue Overlay: OFF') action Function(debug_toggle_dialogue_overlay) text_size 22
            null height 12
            textbutton 'Close' action Hide('debug_tools_menu') text_size 22 xalign 0.5

screen debug_character_editor():
    modal True
    zorder 3001
    add Solid('#000000dd')
    frame:
        align (0.5, 0.5)
        xsize 980
        ysize 720
        padding (26, 24)
        vbox:
            spacing 12
            hbox:
                xfill True
                text 'Character Editor' size 30 color '#ffd27a'
                textbutton 'X' xalign 1.0 action Hide('debug_character_editor')
            viewport:
                scrollbars 'vertical'
                mousewheel True
                ysize 620
                vbox:
                    spacing 18
                    for cid in sorted(character_stats.keys()):
                        frame:
                            xfill True
                            background '#111111ee'
                            padding (16, 14)
                            vbox:
                                spacing 8
                                text '[character_display_name(cid)] ([cid])' size 24 color '#ffffff'
                                for stat_name in ('love', 'lust', 'trust', 'respect'):
                                    hbox:
                                        spacing 8
                                        text '[stat_name]: [character_stats[cid].get(stat_name, 0)]' min_width 180 color '#dddddd'
                                        textbutton '-5' action Function(debug_add_character_stat, cid, stat_name, -5)
                                        textbutton '-1' action Function(debug_add_character_stat, cid, stat_name, -1)
                                        textbutton '+1' action Function(debug_add_character_stat, cid, stat_name, 1)
                                        textbutton '+5' action Function(debug_add_character_stat, cid, stat_name, 5)
                                for mood_name in ('happy', 'sad', 'angry', 'nervous'):
                                    hbox:
                                        spacing 8
                                        text '[mood_name]: [character_stats[cid].get("moods", {}).get(mood_name, 0)]' min_width 180 color '#bbbbbb'
                                        textbutton '-1' action Function(debug_add_character_mood, cid, mood_name, -1)
                                        textbutton '+1' action Function(debug_add_character_mood, cid, mood_name, 1)
                                        textbutton '+5' action Function(debug_add_character_mood, cid, mood_name, 5)

screen debug_action_tools():
    modal True
    zorder 3001
    add Solid('#000000dd')
    frame:
        align (0.5, 0.5)
        xsize 760
        padding (26, 24)
        vbox:
            spacing 14
            hbox:
                xfill True
                text 'Action / Seen Tools' size 30 color '#ffd27a'
                textbutton 'X' xalign 1.0 action Hide('debug_action_tools')
            textbutton ('Show all character options: ON' if debug_all_actions_visible else 'Show all character options: OFF') action Function(debug_set_all_actions_visible, not debug_all_actions_visible) text_size 22
            textbutton 'Clear seen actions' action Function(debug_reset_seen_actions) text_size 22

screen debug_unlock_tools():
    modal True
    zorder 3001
    add Solid('#000000dd')
    frame:
        align (0.5, 0.5)
        xsize 760
        padding (26, 24)
        vbox:
            spacing 14
            hbox:
                xfill True
                text 'Unlock / Lock Tools' size 30 color '#ffd27a'
                textbutton 'X' xalign 1.0 action Hide('debug_unlock_tools')
            textbutton 'Unlock all gallery scenes' action Function(debug_unlock_all_gallery) text_size 22
            textbutton 'Lock all gallery scenes' action Function(debug_lock_all_gallery) text_size 22
            textbutton 'Unlock all locations' action Function(debug_unlock_all_locations) text_size 22
            textbutton 'Reset location locks' action Function(debug_lock_noninitial_locations) text_size 22
            textbutton 'Complete all quests' action Function(debug_complete_all_quests) text_size 22

screen debug_system_toggles():
    modal True
    zorder 3001
    add Solid('#000000dd')
    frame:
        align (0.5, 0.5)
        xsize 720
        padding (28, 24)
        vbox:
            spacing 10
            hbox:
                xfill True
                text 'System Toggles' size 30 color '#ffd27a'
                textbutton 'X' xalign 1.0 action Hide('debug_system_toggles')
            for _name in sorted(systems_enabled.keys()):
                hbox:
                    spacing 12
                    text _name min_width 220 color '#dddddd'
                    textbutton ('ON' if system_enabled(_name) else 'OFF') action Function(debug_toggle_system, _name)

screen debug_dialogue_overlay():
    zorder 4000
    if debug_dialogue_overlay:
        frame:
            align (0.01, 0.03)
            background '#000000dd'
            padding (18, 12)
            xmaximum 520
            vbox:
                spacing 6
                text 'Dialogue Debug Overlay' size 24 color '#ffd27a'
                $ cast_entries = list((_dialogue_cast or {}).items()) if isinstance(_dialogue_cast, dict) else []
                if cast_entries:
                    $ cast_entries.sort(key=lambda entry: entry[0])
                    for cid, info in cast_entries:
                        $ display_name, xalign, shown, origin, manual, dialogue_layer, master_layer, show_ok, action, error, image = _dialogue_debug_entry(cid, info)
                        text '[display_name] ([cid])  x:["%.2f" % xalign]  shown:["%.2f" % shown]  origin:["%.2f" % origin]  manual:[manual]  d:[dialogue_layer] m:[master_layer] ok:[show_ok] [action]' size 18 color '#ffffff'
                        if image:
                            text '  image: [image]' size 14 color '#bbbbbb'
                        if error:
                            text '  error: [error]' size 14 color '#ff8a8a'
                else:
                    text 'Dialogue cast empty' size 18 color '#bbbbbb'

                if '_menu_debug_state' in globals() and _menu_debug_state:
                    $ state = _menu_debug_state
                    $ requested = state.get('requested_side', None)
                    $ displace_flag = state.get('displace', None)
                    text 'Last menu_side: [requested if requested else "<none>"]  displace:[displace_flag]' size 18 color '#ffd27a'
                    if state.get('cast_before'):
                        text 'Cast before call: [", ".join(state.get("cast_before") or [])]' size 16 color '#dddddd'
                    if state.get('targets'):
                        text 'Targets:' size 16 color '#dddddd'
                        $ target_items = sorted(state.get('targets', {}).items(), key=lambda entry: entry[0])
                        for cid, tx in target_items:
                            text '  - [cid]: ["%.2f" % tx]' size 16 color '#bbbbbb'
                    if state.get('moved'):
                        text 'Moved: [", ".join(state.get("moved") or [])]' size 16 color '#bbbbbb'
                    if state.get('restored'):
                        text 'Restored: [", ".join(state.get("restored") or [])]' size 16 color '#bbbbbb'
                    if state.get('notes'):
                        text 'Note: [state.get("notes")]' size 16 color '#ffb37a'

init python:
    build.classify('game/DevTools/**', None)
    build.classify('game/DevTools/**/*.rpyc', None)
