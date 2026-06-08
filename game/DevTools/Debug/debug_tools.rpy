# =============================================================================
# Developer Debug Tools
# =============================================================================
# F10 opens one clean diagnostics workspace. The old Layout Visualizer entry has
# been removed. Diagnostics can be copied per section or as one complete report.
# =============================================================================


default debug_all_actions_visible = False
default debug_dialogue_overlay = False
default debug_world_overlay = False
default debug_quest_overlay = False
default debug_tools_tab = "Overview"


init -999 python:
    config.keymap.setdefault("debug_tools", [])
    if "K_F10" not in config.keymap["debug_tools"]:
        config.keymap["debug_tools"].append("K_F10")


init python:

    DEBUG_TOOL_TABS = ("Overview", "Dialogue", "World", "Quests", "Characters", "Systems")


    def _debug_system_available():
        try:
            return bool(system_enabled("debug_tools"))
        except Exception:
            return True


    def debug_open_tools_menu():
        if not _debug_system_available():
            return None
        renpy.show_screen("debug_tools_menu")
        renpy.restart_interaction()
        return None


    def debug_close_tools_menu():
        renpy.hide_screen("debug_tools_menu")
        renpy.restart_interaction()
        return None


    def debug_set_tab(tab):
        global debug_tools_tab
        if tab in DEBUG_TOOL_TABS:
            debug_tools_tab = tab
        renpy.restart_interaction()
        return None


    def debug_copy_text(text, label="Debug report"):
        try:
            import pygame.scrap
            try:
                pygame.scrap.init()
            except Exception:
                pass
            pygame.scrap.put(pygame.SCRAP_TEXT, str(text).encode("utf-8"))
            renpy.notify("{} copied to clipboard.".format(label))
        except Exception as error:
            try:
                renpy.log("Clipboard copy failed: {!r}".format(error))
            except Exception:
                pass
            renpy.notify("Clipboard copy failed. See log.txt.")
        return None


    def _debug_safe(value, fallback="<unavailable>"):
        try:
            return str(value)
        except Exception:
            return fallback


    def _debug_bool(value):
        return "Y" if value else "N"


    def _debug_float(value, fallback="--"):
        try:
            return "{:.3f}".format(float(value))
        except Exception:
            return fallback


    def _dialogue_debug_entry(cid, info):
        info = info or {}
        try:
            display_name = character_display_name(cid)
        except Exception:
            display_name = cid

        try:
            debug_state = (_dialogue_debug_state or {}).get(cid, {})
        except Exception:
            debug_state = {}
        try:
            render_state = (_dialogue_render_debug or {}).get(cid, {})
        except Exception:
            render_state = {}

        model_x = info.get("xalign", 0.5)
        requested_x = info.get("requested_xalign", info.get("shown_xalign", model_x))
        render_x = render_state.get("x", debug_state.get("render_x"))
        render_target = render_state.get("target", debug_state.get("render_target", requested_x))
        complete = render_state.get("complete", debug_state.get("render_complete"))

        if render_x is None:
            sync_status = "NO SAMPLE"
        elif not complete and abs(float(render_x) - float(render_target)) >= 0.002:
            sync_status = "MOVING"
        elif abs(float(render_x) - float(requested_x)) <= 0.01:
            sync_status = "SYNC"
        else:
            sync_status = "DESYNC"

        try:
            attributes = list(renpy.get_attributes(cid, layer="dialogue") or ())
        except Exception:
            attributes = []
        try:
            at_count = len(renpy.get_at_list(cid, layer="dialogue") or [])
        except Exception:
            at_count = 0

        return {
            "id": cid,
            "name": display_name,
            "model_x": model_x,
            "requested_x": requested_x,
            "render_x": render_x,
            "render_target": render_target,
            "origin_x": info.get("origin_x", 0.5),
            "manual": bool(info.get("manual")),
            "pinned": bool(info.get("menu_locked")),
            "dialogue_showing": bool(debug_state.get("dialogue_showing")),
            "master_showing": bool(debug_state.get("master_showing")),
            "ok": bool(debug_state.get("ok")),
            "action": debug_state.get("action", ""),
            "error": debug_state.get("error", ""),
            "image": debug_state.get("image", ""),
            "source_attrs": list(info.get("source_attrs", [])),
            "renpy_attrs": attributes,
            "at_count": at_count,
            "render_mode": render_state.get("mode", debug_state.get("render_mode", "")),
            "render_complete": complete,
            "sync_status": sync_status,
        }


    def debug_dialogue_report():
        lines = [
            "PROJECT TAC - DIALOGUE DEBUG",
            "=" * 72,
            "in_dialogue: {}".format(_debug_safe(getattr(store, "_in_dialogue", None))),
            "dialogue layer tags: {}".format(
                ", ".join(sorted(renpy.get_showing_tags(layer="dialogue")))
                if "dialogue" in config.layers else "<dialogue layer missing>"
            ),
            "master layer tags: {}".format(", ".join(sorted(renpy.get_showing_tags(layer="master")))),
            "",
            "CAST",
            "----",
        ]

        cast = getattr(store, "_dialogue_cast", {})
        if not isinstance(cast, dict) or not cast:
            lines.append("<empty>")
        else:
            for cid in sorted(cast.keys()):
                entry = _dialogue_debug_entry(cid, cast[cid])
                lines.extend([
                    "{} ({}) [{}]".format(entry["name"], cid, entry["sync_status"]),
                    "  model={} requested={} render={} target={} origin={}".format(
                        _debug_float(entry["model_x"]),
                        _debug_float(entry["requested_x"]),
                        _debug_float(entry["render_x"]),
                        _debug_float(entry["render_target"]),
                        _debug_float(entry["origin_x"]),
                    ),
                    "  manual={} pinned={} dialogue={} master={} show_ok={} action={}".format(
                        _debug_bool(entry["manual"]),
                        _debug_bool(entry["pinned"]),
                        _debug_bool(entry["dialogue_showing"]),
                        _debug_bool(entry["master_showing"]),
                        _debug_bool(entry["ok"]),
                        entry["action"],
                    ),
                    "  image: {}".format(entry["image"] or "<none>"),
                    "  source attrs: {}".format(entry["source_attrs"]),
                    "  Ren'Py attrs: {} | at-list count: {}".format(entry["renpy_attrs"], entry["at_count"]),
                    "  render mode: {} complete: {}".format(entry["render_mode"] or "<none>", entry["render_complete"]),
                ])
                if entry["error"]:
                    lines.append("  ERROR: {}".format(entry["error"]))

        state = getattr(store, "_menu_debug_state", {}) or {}
        lines.extend(["", "LAST CHOICE MENU", "----------------"])
        if not state:
            lines.append("<no menu diagnostics>")
        else:
            lines.extend([
                "phase: {}".format(state.get("phase", "")),
                "side: {} | displace: {}".format(state.get("requested_side"), state.get("displace")),
                "cast before: {}".format(state.get("cast_before", [])),
                "positions before: {}".format(state.get("positions_before", {})),
                "targets: {}".format(state.get("targets", {})),
                "moved: {}".format(state.get("moved", [])),
                "skipped: {}".format(state.get("skipped", [])),
                "restored: {}".format(state.get("restored", [])),
                "notes: {}".format(state.get("notes", "")),
            ])
        return "\n".join(lines)


    def debug_world_report():
        lines = [
            "PROJECT TAC - WORLD DEBUG",
            "=" * 72,
            "location: {} ({})".format(
                _debug_safe(globals().get("current_location")),
                _debug_safe(location_name() if "location_name" in globals() else ""),
            ),
            "area: {}".format(_debug_safe(current_area_id() if "current_area_id" in globals() else None)),
            "background: {}".format(_debug_safe(location_bg() if "location_bg" in globals() else None)),
            "day/time: {} / {}".format(_debug_safe(globals().get("day")), _debug_safe(globals().get("time"))),
            "weekday: {}".format(_debug_safe(weekday_name() if "weekday_name" in globals() else None)),
            "stamina: {} / {}".format(
                _debug_safe(globals().get("stamina")),
                _debug_safe(get_max_stamina() if "get_max_stamina" in globals() else None),
            ),
            "pending stamina: {}".format(_debug_safe(globals().get("_pending_stamina_cost"))),
            "route: {}".format(_debug_safe(globals().get("current_route"))),
            "",
            "VISIBLE EXPLORATION NPCS",
            "------------------------",
        ]

        visible = globals().get("_visible_npcs", {}) or {}
        if visible:
            for cid in sorted(visible.keys()):
                lines.append("{}: {}".format(cid, visible[cid]))
        else:
            lines.append("<none>")

        lines.extend(["", "ROOMS", "-----"])
        lines.append("unlocked: {}".format(sorted(globals().get("unlocked_rooms", set()) or set())))
        lines.append("order: {}".format(list(globals().get("location_order", []) or [])))

        lines.extend(["", "ACTIVE ITEMS", "------------"])
        try:
            active_items = location_active_items()
        except Exception:
            active_items = []
        lines.append(_debug_safe(active_items))

        lines.extend(["", "STORY FLAGS", "-----------"])
        lines.append(_debug_safe(sorted(globals().get("story_flags", set()) or set())))
        return "\n".join(lines)


    def debug_quest_report():
        lines = [
            "PROJECT TAC - QUEST DEBUG",
            "=" * 72,
            "tracked quest id: {}".format(_debug_safe(globals().get("tracked_quest_id"))),
            "",
        ]

        quests = globals().get("quest_log", {}) or {}
        if not quests:
            lines.append("<quest log empty>")
            return "\n".join(lines)

        for qid in sorted(quests.keys()):
            quest = quests[qid]
            lines.append("{} [{}] {}".format(qid, getattr(quest, "state", "?"), getattr(quest, "title", "")))
            lines.append("  category={} character={} target={}".format(
                getattr(quest, "category", None),
                getattr(quest, "character", None),
                getattr(quest, "target", None),
            ))
            lines.append("  flags: start={} complete={} fail={}".format(
                getattr(quest, "start_flag", None),
                getattr(quest, "complete_flag", None),
                getattr(quest, "fail_flag", None),
            ))
            for objective in getattr(quest, "objectives", []):
                lines.append("    [{}] {}: {} | flag={} optional={} target={}".format(
                    "x" if getattr(objective, "done", False) else " ",
                    getattr(objective, "id", "?"),
                    getattr(objective, "text", ""),
                    getattr(objective, "flag", None),
                    getattr(objective, "optional", False),
                    getattr(objective, "target", None),
                ))
            lines.append("")
        return "\n".join(lines)


    def debug_character_report():
        lines = ["PROJECT TAC - CHARACTER DEBUG", "=" * 72]
        stats = globals().get("character_stats", {}) or {}
        for cid in sorted(stats.keys()):
            data = stats[cid]
            try:
                image_data = character_image_debug(cid)
            except Exception:
                image_data = {}
            stat_text = " ".join(
                "{}={}".format(stat_name, data.get(stat_name, 0))
                for stat_name in RELATIONSHIP_STATS
            )
            lines.extend([
                "{} ({})".format(character_display_name(cid), cid),
                "  stats: {}".format(stat_text),
                "  moods: {}".format(data.get("moods", {})),
                "  reactions: {}".format(data.get("reactions", {})),
                "  statuses: {}".format(data.get("statuses", {})),
                "  schedule: {}".format((globals().get("character_schedules", {}) or {}).get(cid, {})),
                "  image locator: {}".format(image_data),
                "",
            ])
        return "\n".join(lines)


    def debug_system_report():
        lines = ["PROJECT TAC - SYSTEM DEBUG", "=" * 72]
        systems = globals().get("systems_enabled", {}) or {}
        for name in sorted(systems.keys()):
            lines.append("{}: {}".format(name, "ON" if system_enabled(name) else "OFF"))
        lines.extend([
            "",
            "config layers: {}".format(list(config.layers)),
            "overlay screens: {}".format(list(config.overlay_screens)),
            "start interaction callbacks: {}".format([
                getattr(callback, "__name__", repr(callback))
                for callback in config.start_interact_callbacks
            ]),
        ])
        return "\n".join(lines)


    def debug_validation_issues():
        issues = []
        characters = set((globals().get("character_stats", {}) or {}).keys())
        speakers = globals().get("character_speakers", {}) or {}
        schedules = globals().get("character_schedules", {}) or {}

        if "dialogue" not in config.layers:
            issues.append("Dialogue layer is missing from config.layers.")

        for cid in sorted(characters):
            if cid not in speakers:
                issues.append("Character '{}' has state but no character_speakers entry.".format(cid))
            if cid not in schedules:
                issues.append("Character '{}' has no schedule entry.".format(cid))
            try:
                if not renpy.has_image((cid,), exact=True):
                    issues.append("Character '{}' has no short base image (`show {}`).".format(cid, cid))
            except Exception:
                pass
            if config.tag_layer.get(cid) != "dialogue":
                issues.append("Character '{}' is not routed to the dialogue layer.".format(cid))

        locations_data = globals().get("locations", {}) or {}
        for loc_id in globals().get("location_order", []) or []:
            if loc_id not in locations_data:
                issues.append("location_order contains unregistered location '{}'.".format(loc_id))

        gallery_ids = set()
        for scene in globals().get("gallery_scenes", []) or []:
            gid = scene.get("id")
            if gid in gallery_ids:
                issues.append("Duplicate gallery id '{}'.".format(gid))
            gallery_ids.add(gid)
            label = scene.get("label")
            if label and not renpy.has_label(label):
                issues.append("Gallery '{}' points to missing label '{}'.".format(gid, label))

        return issues


    def debug_validation_report():
        issues = debug_validation_issues()
        if not issues:
            return "ENGINE VALIDATION\n=================\nNo structural issues detected."
        return "ENGINE VALIDATION\n=================\n" + "\n".join(
            "{}. {}".format(index + 1, issue) for index, issue in enumerate(issues)
        )


    def debug_full_report():
        return "\n\n".join([
            debug_validation_report(),
            debug_dialogue_report(),
            debug_world_report(),
            debug_quest_report(),
            debug_character_report(),
            debug_system_report(),
        ])


    def debug_add_character_stat(char_id, stat_name, amount):
        try:
            stat(char_id, stat_name, amount)
        except Exception as error:
            renpy.log("Debug stat edit failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_add_character_mood(char_id, mood_name, amount):
        try:
            mood(char_id, mood_name, amount)
        except Exception as error:
            renpy.log("Debug mood edit failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_set_all_actions_visible(value=True):
        global debug_all_actions_visible
        debug_all_actions_visible = bool(value)
        renpy.restart_interaction()
        return None


    def debug_toggle_overlay(name, value=None):
        variable_name = "debug_{}_overlay".format(name)
        current = bool(getattr(store, variable_name, False))
        setattr(store, variable_name, (not current) if value is None else bool(value))
        renpy.restart_interaction()
        return None


    def debug_toggle_dialogue_overlay(value=None):
        return debug_toggle_overlay("dialogue", value)


    def debug_unlock_all_gallery():
        try:
            for scene in gallery_scenes:
                unlock_gallery(scene.get("id"))
        except Exception as error:
            renpy.log("Debug gallery unlock failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_lock_all_gallery():
        try:
            unlocked_gallery.clear()
        except Exception as error:
            renpy.log("Debug gallery lock failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_complete_all_quests():
        try:
            for quest in quest_log.values():
                quest.state = "completed"
        except Exception as error:
            renpy.log("Debug quest completion failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_unlock_all_locations():
        try:
            for loc_id in location_order:
                unlock_room(loc_id)
        except Exception as error:
            renpy.log("Debug location unlock failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_lock_noninitial_locations():
        try:
            unlocked_rooms.clear()
            for loc_id in unlocked_rooms_init:
                unlock_room(loc_id)
        except Exception as error:
            renpy.log("Debug location reset failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_reset_seen_actions():
        try:
            seen_actions.clear()
        except Exception as error:
            renpy.log("Debug seen-action reset failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    def debug_toggle_system(name):
        try:
            set_system_enabled(name, not system_enabled(name))
        except Exception as error:
            renpy.log("Debug system toggle failed: {!r}".format(error))
        renpy.restart_interaction()
        return None


    config.underlay.append(renpy.Keymap(debug_tools=debug_open_tools_menu))

    for _debug_overlay_name in ("debug_dialogue_overlay", "debug_world_overlay", "debug_quest_overlay"):
        if _debug_overlay_name not in config.overlay_screens:
            config.overlay_screens.append(_debug_overlay_name)


# =============================================================================
# Styles
# =============================================================================

style debug_tool_root_frame is empty:
    background "#0b1018f5"
    padding (0, 0)

style debug_tool_sidebar_frame is empty:
    background "#111927"
    padding (16, 18)

style debug_tool_content_frame is empty:
    background "#0b1018"
    padding (24, 20)

style debug_tool_button is button:
    background "#172235"
    hover_background "#223653"
    selected_background "#31547f"
    insensitive_background "#111722"
    padding (14, 9)

style debug_tool_button_text is button_text:
    color "#cbd8e8"
    hover_color "#ffffff"
    selected_color "#ffffff"
    size 18
    xalign 0.0

style debug_tool_small_button is debug_tool_button:
    padding (10, 6)

style debug_tool_small_button_text is debug_tool_button_text:
    size 15
    xalign 0.5

style debug_tool_card is empty:
    background "#111a28"
    padding (16, 14)

style debug_tool_title is text:
    color "#f5c66d"
    size 31

style debug_tool_heading is text:
    color "#dbe8f7"
    size 22

style debug_tool_body is text:
    color "#b7c5d6"
    size 16

style debug_tool_muted is text:
    color "#7f91a8"
    size 14

style debug_tool_vscrollbar is vscrollbar:
    xsize 6
    base_bar "#111927"
    thumb "#45688f"
    unscrollable "hide"


# =============================================================================
# Main workspace
# =============================================================================

screen debug_tools_menu():
    modal True
    zorder 5000

    key "K_ESCAPE" action Function(debug_close_tools_menu)
    add Solid("#000000b8")

    frame:
        style "debug_tool_root_frame"
        align (0.5, 0.5)
        xsize 1560
        ysize 880

        hbox:
            xfill True
            yfill True

            frame:
                style "debug_tool_sidebar_frame"
                xsize 250
                yfill True

                vbox:
                    spacing 8
                    text "DEBUG TOOLS" style "debug_tool_title" size 24
                    text "F10" style "debug_tool_muted"
                    null height 10

                    for _tab in DEBUG_TOOL_TABS:
                        textbutton _tab:
                            style "debug_tool_button"
                            text_style "debug_tool_button_text"
                            xfill True
                            selected (debug_tools_tab == _tab)
                            action Function(debug_set_tab, _tab)

                    null yfill True
                    textbutton "Copy full report":
                        style "debug_tool_button"
                        text_style "debug_tool_button_text"
                        xfill True
                        action Function(debug_copy_text, debug_full_report(), "Full debug report")
                    textbutton "Close":
                        style "debug_tool_button"
                        text_style "debug_tool_button_text"
                        xfill True
                        action Function(debug_close_tools_menu)

            frame:
                style "debug_tool_content_frame"
                xfill True
                yfill True

                vbox:
                    xfill True
                    yfill True
                    spacing 14

                    hbox:
                        xfill True
                        text "[debug_tools_tab]" style "debug_tool_title"
                        null xfill True
                        if debug_tools_tab == "Dialogue":
                            textbutton "Copy dialogue":
                                style "debug_tool_small_button"
                                text_style "debug_tool_small_button_text"
                                action Function(debug_copy_text, debug_dialogue_report(), "Dialogue report")
                        elif debug_tools_tab == "World":
                            textbutton "Copy world":
                                style "debug_tool_small_button"
                                text_style "debug_tool_small_button_text"
                                action Function(debug_copy_text, debug_world_report(), "World report")
                        elif debug_tools_tab == "Quests":
                            textbutton "Copy quests":
                                style "debug_tool_small_button"
                                text_style "debug_tool_small_button_text"
                                action Function(debug_copy_text, debug_quest_report(), "Quest report")
                        elif debug_tools_tab == "Characters":
                            textbutton "Copy characters":
                                style "debug_tool_small_button"
                                text_style "debug_tool_small_button_text"
                                action Function(debug_copy_text, debug_character_report(), "Character report")
                        elif debug_tools_tab == "Systems":
                            textbutton "Copy systems":
                                style "debug_tool_small_button"
                                text_style "debug_tool_small_button_text"
                                action Function(debug_copy_text, debug_system_report(), "System report")
                        else:
                            textbutton "Copy validation":
                                style "debug_tool_small_button"
                                text_style "debug_tool_small_button_text"
                                action Function(debug_copy_text, debug_validation_report(), "Validation report")

                    viewport:
                        mousewheel True
                        draggable True
                        scrollbars "vertical"
                        vscrollbar_xsize 6
                        vscrollbar_base_bar "#111927"
                        vscrollbar_thumb "#45688f"
                        vscrollbar_unscrollable "hide"
                        yfill True

                        vbox:
                            xfill True
                            spacing 14

                            if debug_tools_tab == "Overview":
                                use debug_tools_overview
                            elif debug_tools_tab == "Dialogue":
                                use debug_tools_dialogue
                            elif debug_tools_tab == "World":
                                use debug_tools_world
                            elif debug_tools_tab == "Quests":
                                use debug_tools_quests
                            elif debug_tools_tab == "Characters":
                                use debug_tools_characters
                            elif debug_tools_tab == "Systems":
                                use debug_tools_systems


screen debug_tools_overview():
    $ _issues = debug_validation_issues()

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 8
            text "Live overlays" style "debug_tool_heading"
            hbox:
                spacing 8
                textbutton ("Dialogue: ON" if debug_dialogue_overlay else "Dialogue: OFF") action Function(debug_toggle_overlay, "dialogue") style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton ("World: ON" if debug_world_overlay else "World: OFF") action Function(debug_toggle_overlay, "world") style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton ("Quests: ON" if debug_quest_overlay else "Quests: OFF") action Function(debug_toggle_overlay, "quest") style "debug_tool_small_button" text_style "debug_tool_small_button_text"

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 8
            text "Engine validation" style "debug_tool_heading"
            if _issues:
                text "[len(_issues)] issue(s) detected" color "#ff9a8e" size 16
                for _issue in _issues:
                    text "• [_issue]" style "debug_tool_body"
            else:
                text "No structural issues detected." color "#86d39b" size 17

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 10
            text "Quick controls" style "debug_tool_heading"
            grid 3 3:
                spacing 8
                textbutton ("All actions: ON" if debug_all_actions_visible else "All actions: OFF") action Function(debug_set_all_actions_visible, not debug_all_actions_visible) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton "Clear seen actions" action Function(debug_reset_seen_actions) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton "Complete quests" action Function(debug_complete_all_quests) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton "Unlock locations" action Function(debug_unlock_all_locations) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton "Reset location locks" action Function(debug_lock_noninitial_locations) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton "Unlock gallery" action Function(debug_unlock_all_gallery) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                textbutton "Lock gallery" action Function(debug_lock_all_gallery) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                null
                null


screen debug_tools_dialogue():
    $ _cast = _dialogue_cast or {}
    $ _menu_state = _menu_debug_state or {}

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 7
            text "Dialogue state" style "debug_tool_heading"
            text "Active: [_in_dialogue] | Cast: [len(_cast)]" style "debug_tool_body"
            text "Dialogue tags: [sorted(renpy.get_showing_tags(layer='dialogue')) if 'dialogue' in config.layers else []]" style "debug_tool_muted"

    if _cast:
        for _cid in sorted(_cast.keys()):
            $ _entry = _dialogue_debug_entry(_cid, _cast[_cid])
            frame:
                style "debug_tool_card"
                xfill True
                vbox:
                    spacing 5
                    hbox:
                        xfill True
                        text "[_entry['name']] ([_cid])" style "debug_tool_heading"
                        null xfill True
                        text "[_entry['sync_status']]" color ("#86d39b" if _entry["sync_status"] == "SYNC" else "#f5c66d" if _entry["sync_status"] == "MOVING" else "#ff9a8e") size 17
                    text "Model [_debug_float(_entry['model_x'])]   Requested [_debug_float(_entry['requested_x'])]   Render [_debug_float(_entry['render_x'])]   Origin [_debug_float(_entry['origin_x'])]" style "debug_tool_body"
                    text "manual:[_debug_bool(_entry['manual'])] pinned:[_debug_bool(_entry['pinned'])] dialogue:[_debug_bool(_entry['dialogue_showing'])] master:[_debug_bool(_entry['master_showing'])] show-ok:[_debug_bool(_entry['ok'])]" style "debug_tool_muted"
                    text "Image: [_entry['image'] or '<none>']" style "debug_tool_body"
                    text "Source attrs: [_entry['source_attrs']] | Ren'Py attrs: [_entry['renpy_attrs']]" style "debug_tool_muted"
                    text "Render: [_entry['render_mode'] or '<none>'] complete:[_entry['render_complete']] at-list:[_entry['at_count']]" style "debug_tool_muted"
                    if _entry["error"]:
                        text "ERROR: [_entry['error']]" color "#ff8d8d" size 15
    else:
        frame:
            style "debug_tool_card"
            xfill True
            text "Dialogue cast is empty." style "debug_tool_body"

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 5
            text "Last choice menu" style "debug_tool_heading"
            if _menu_state:
                text "Phase: [_menu_state.get('phase')] | Side: [_menu_state.get('requested_side')] | Displace: [_menu_state.get('displace')]" style "debug_tool_body"
                text "Before: [_menu_state.get('positions_before', {})]" style "debug_tool_muted"
                text "Targets: [_menu_state.get('targets', {})]" style "debug_tool_muted"
                text "Moved: [_menu_state.get('moved', [])] | Skipped: [_menu_state.get('skipped', [])]" style "debug_tool_muted"
                text "Restored: [_menu_state.get('restored', [])]" style "debug_tool_muted"
                text "Note: [_menu_state.get('notes', '')]" style "debug_tool_body"
            else:
                text "No choice-menu diagnostics yet." style "debug_tool_body"


screen debug_tools_world():
    $ _world_lines = debug_world_report().split("\n")
    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 4
            for _line in _world_lines:
                text "[_line]" style "debug_tool_body"


screen debug_tools_quests():
    $ _quests = globals().get("quest_log", {}) or {}
    if not _quests:
        frame:
            style "debug_tool_card"
            xfill True
            text "Quest log is empty." style "debug_tool_body"
    for _qid in sorted(_quests.keys()):
        $ _quest = _quests[_qid]
        frame:
            style "debug_tool_card"
            xfill True
            vbox:
                spacing 5
                text "[_quest.title] ([_qid])" style "debug_tool_heading"
                text "State: [_quest.state] | Category: [_quest.category] | Character: [_quest.character]" style "debug_tool_body"
                text "Target: [_quest.target]" style "debug_tool_muted"
                text "Flags: start=[_quest.start_flag] complete=[_quest.complete_flag] fail=[_quest.fail_flag]" style "debug_tool_muted"
                for _objective in _quest.objectives:
                    $ _objective_mark = "✓" if _objective.done else "○"
                    text "[_objective_mark] [_objective.id] — [_objective.text] | flag=[_objective.flag] optional=[_objective.optional]" style "debug_tool_body"


screen debug_tools_characters():
    for _cid in sorted(character_stats.keys()):
        frame:
            style "debug_tool_card"
            xfill True
            vbox:
                spacing 8
                text "[character_display_name(_cid)] ([_cid])" style "debug_tool_heading"
                for _stat_name in RELATIONSHIP_STATS:
                    hbox:
                        spacing 7
                        text "[_stat_name]: [character_stats[_cid].get(_stat_name, 0)]" min_width 190 style "debug_tool_body"
                        textbutton "-5" action Function(debug_add_character_stat, _cid, _stat_name, -5) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                        textbutton "-1" action Function(debug_add_character_stat, _cid, _stat_name, -1) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                        textbutton "+1" action Function(debug_add_character_stat, _cid, _stat_name, 1) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                        textbutton "+5" action Function(debug_add_character_stat, _cid, _stat_name, 5) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                null height 3
                for _mood_name in MOOD_AXES:
                    hbox:
                        spacing 7
                        text "[_mood_name]: [character_stats[_cid].get('moods', {}).get(_mood_name, 0)]" min_width 190 style "debug_tool_body"
                        textbutton "-5" action Function(debug_add_character_mood, _cid, _mood_name, -5) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                        textbutton "-1" action Function(debug_add_character_mood, _cid, _mood_name, -1) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                        textbutton "+1" action Function(debug_add_character_mood, _cid, _mood_name, 1) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                        textbutton "+5" action Function(debug_add_character_mood, _cid, _mood_name, 5) style "debug_tool_small_button" text_style "debug_tool_small_button_text"


screen debug_tools_systems():
    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 8
            text "Runtime systems" style "debug_tool_heading"
            for _name in sorted(systems_enabled.keys()):
                hbox:
                    xfill True
                    text "[_name]" min_width 260 style "debug_tool_body"
                    textbutton ("ON" if system_enabled(_name) else "OFF") action Function(debug_toggle_system, _name) style "debug_tool_small_button" text_style "debug_tool_small_button_text"

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 6
            text "Registered layers" style "debug_tool_heading"
            text "[list(config.layers)]" style "debug_tool_body"
            text "Overlay screens" style "debug_tool_heading"
            text "[list(config.overlay_screens)]" style "debug_tool_body"


# Compatibility screen names now open the corresponding workspace tab.
screen debug_character_editor():
    on "show" action [Function(debug_set_tab, "Characters"), Show("debug_tools_menu")]
    timer 0.01 action Hide("debug_character_editor")

screen debug_action_tools():
    on "show" action [Function(debug_set_tab, "Overview"), Show("debug_tools_menu")]
    timer 0.01 action Hide("debug_action_tools")

screen debug_unlock_tools():
    on "show" action [Function(debug_set_tab, "Overview"), Show("debug_tools_menu")]
    timer 0.01 action Hide("debug_unlock_tools")

screen debug_system_toggles():
    on "show" action [Function(debug_set_tab, "Systems"), Show("debug_tools_menu")]
    timer 0.01 action Hide("debug_system_toggles")


# =============================================================================
# Live overlays
# =============================================================================

screen debug_dialogue_overlay():
    zorder 4900
    if debug_dialogue_overlay:
        frame:
            align (0.01, 0.025)
            xmaximum 680
            background "#09111aee"
            padding (14, 11)

            vbox:
                spacing 5
                hbox:
                    xfill True
                    text "DIALOGUE" color "#f5c66d" size 19
                    null xfill True
                    textbutton "Copy" action Function(debug_copy_text, debug_dialogue_report(), "Dialogue report") style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                    textbutton "×" action Function(debug_toggle_overlay, "dialogue", False) style "debug_tool_small_button" text_style "debug_tool_small_button_text"

                $ _overlay_cast = _dialogue_cast or {}
                if _overlay_cast:
                    for _cid in sorted(_overlay_cast.keys()):
                        $ _entry = _dialogue_debug_entry(_cid, _overlay_cast[_cid])
                        text "[_entry['name']]  model:[_debug_float(_entry['model_x'])] req:[_debug_float(_entry['requested_x'])] render:[_debug_float(_entry['render_x'])]  [_entry['sync_status']]" color "#e5edf6" size 15
                        text "  image:[_entry['image']] attrs:[_entry['renpy_attrs']] manual:[_debug_bool(_entry['manual'])] pinned:[_debug_bool(_entry['pinned'])]" color "#8fa2b8" size 12
                        if _entry["error"]:
                            text "  error: [_entry['error']]" color "#ff8d8d" size 12
                else:
                    text "Cast empty" color "#8fa2b8" size 14

                $ _overlay_menu = _menu_debug_state or {}
                if _overlay_menu:
                    text "Menu [_overlay_menu.get('requested_side')] phase:[_overlay_menu.get('phase')] targets:[_overlay_menu.get('targets', {})]" color "#f5c66d" size 13
                    text "Moved:[_overlay_menu.get('moved', [])] restored:[_overlay_menu.get('restored', [])]" color "#8fa2b8" size 12


screen debug_world_overlay():
    zorder 4890
    if debug_world_overlay:
        frame:
            align (0.99, 0.025)
            xmaximum 470
            background "#09111aee"
            padding (14, 11)
            vbox:
                spacing 4
                hbox:
                    xfill True
                    text "WORLD" color "#f5c66d" size 19
                    null xfill True
                    textbutton "Copy" action Function(debug_copy_text, debug_world_report(), "World report") style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                    textbutton "×" action Function(debug_toggle_overlay, "world", False) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                text "Location: [current_location] ([location_name()])" color "#e5edf6" size 15
                text "Day [day] — [weekday_name()] — [time]" color "#c5d1df" size 14
                text "Stamina [stamina]/[get_max_stamina()] pending:[_pending_stamina_cost]" color "#c5d1df" size 14
                text "Explore NPCs: [sorted((_visible_npcs or {}).keys())]" color "#8fa2b8" size 13
                text "Dialogue: [_in_dialogue]" color "#8fa2b8" size 13


screen debug_quest_overlay():
    zorder 4880
    if debug_quest_overlay:
        frame:
            align (0.01, 0.98)
            xmaximum 620
            background "#09111aee"
            padding (14, 11)
            vbox:
                spacing 4
                hbox:
                    xfill True
                    text "QUESTS" color "#f5c66d" size 19
                    null xfill True
                    textbutton "Copy" action Function(debug_copy_text, debug_quest_report(), "Quest report") style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                    textbutton "×" action Function(debug_toggle_overlay, "quest", False) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                $ _active_debug_quests = active_quests() if "active_quests" in globals() else []
                if _active_debug_quests:
                    for _quest in _active_debug_quests[:5]:
                        text "[_quest.id] — [_quest.title]" color "#e5edf6" size 14
                        for _objective in [obj for obj in _quest.objectives if not obj.done][:3]:
                            text "  ○ [_objective.text]" color "#8fa2b8" size 12
                else:
                    text "No active quests" color "#8fa2b8" size 14


init python:
    build.classify("game/DevTools/**", None)
    build.classify("game/DevTools/**/*.rpyc", None)
