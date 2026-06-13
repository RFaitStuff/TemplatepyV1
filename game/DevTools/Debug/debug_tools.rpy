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
            loc = locations_data.get(loc_id, {}) or {}
            for label_key in ("first_visit", "first_visit_today", "on_enter", "main_loop"):
                label = loc.get(label_key)
                if label and not renpy.has_label(label):
                    issues.append("Location '{}' {} label '{}' is missing.".format(loc_id, label_key, label))
            seen_objects = set()
            for ex in loc.get("exits", []) or []:
                debug_validate_requirements("Location '{}' exit '{}'".format(loc_id, ex.get("to")), ex.get("requires") or ex.get("show_when") or ex.get("unlock_when"), issues)
                target = ex.get("to")
                if target and target not in locations_data:
                    issues.append("Location '{}' exit points to missing location '{}'.".format(loc_id, target))
            for item in loc.get("items", []) or []:
                debug_validate_requirements("Location '{}' item '{}'".format(loc_id, item.get("item")), item.get("requires") or item.get("show_when") or item.get("unlock_when"), issues)
                item_id = item.get("item")
                if item_id and item_id not in globals().get("item_defs", {}):
                    issues.append("Location '{}' item spot references missing item '{}'.".format(loc_id, item_id))
                label = item.get("label")
                if label and not renpy.has_label(label):
                    issues.append("Location '{}' item '{}' points to missing label '{}'.".format(loc_id, item_id, label))
            for obj in loc.get("objects", []) or []:
                oid = obj.get("id")
                if not oid:
                    issues.append("Location '{}' has object spot with no id.".format(loc_id))
                    continue
                if oid in seen_objects:
                    issues.append("Location '{}' has duplicate object spot '{}'.".format(loc_id, oid))
                seen_objects.add(oid)
                if oid not in globals().get("interactable_defs", {}):
                    issues.append("Location '{}' object '{}' has no interactable registration.".format(loc_id, oid))
                hitbox = obj.get("hitbox")
                if hitbox and hitbox.get("type") in ("poly", "mask"):
                    if not obj.get("image") and not hitbox.get("size"):
                        issues.append("Location '{}' object '{}' has a {} hitbox without image or fallback size.".format(loc_id, oid, hitbox.get("type")))
                debug_validate_requirements("Location '{}' object '{}'".format(loc_id, oid), obj.get("requires") or obj.get("show_when") or obj.get("unlock_when"), issues)
            for index, layer in enumerate(loc.get("layers", []) or []):
                if not layer.get("image"):
                    issues.append("Location '{}' layer #{} has no image.".format(loc_id, index + 1))
                slot = layer.get("slot", "overlay")
                if slot not in ("overlay", "front", "back"):
                    issues.append("Location '{}' layer #{} uses unknown slot '{}'.".format(loc_id, index + 1, slot))
                debug_validate_requirements("Location '{}' layer #{}".format(loc_id, index + 1), layer.get("requires") or layer.get("show_when"), issues)

        for iid, data in (globals().get("interactable_defs", {}) or {}).items():
            seen_action_ids = set()
            for action in data.get("actions", []) or []:
                action_id = action.get("id")
                if not action_id:
                    issues.append("Interactable '{}' has an action with no id.".format(iid))
                    continue
                if action_id in seen_action_ids:
                    issues.append("Interactable '{}' has duplicate action id '{}'.".format(iid, action_id))
                seen_action_ids.add(action_id)
                label = action.get("label")
                if label and not label.startswith("_") and not renpy.has_label(label):
                    issues.append("Interactable '{}' action '{}' points to missing label '{}'.".format(iid, action_id, label))
                debug_validate_requirements("Interactable '{}' action '{}'".format(iid, action_id), action.get("requires"), issues)

        for key, use_data in (globals().get("item_use_defs", {}) or {}).items():
            item_id, target = key
            if item_id != "*" and item_id not in globals().get("item_defs", {}):
                issues.append("Item use references missing item '{}'.".format(item_id))
            label = use_data.get("label")
            if label and not renpy.has_label(label):
                issues.append("Item use '{} -> {}' points to missing label '{}'.".format(item_id, target, label))
            debug_validate_requirements("Item use '{} -> {}'".format(item_id, target), use_data.get("requires"), issues)

        for item_id, item_data in (globals().get("item_defs", {}) or {}).items():
            debug_validate_requirements("Item '{}' visibility".format(item_id), item_data.get("show_when") or item_data.get("hidden_until"), issues)
            debug_validate_requirements("Item '{}' use".format(item_id), item_data.get("use_when"), issues)
            label = item_data.get("use_label")
            if label and not renpy.has_label(label):
                issues.append("Item '{}' use_label points to missing label '{}'.".format(item_id, label))
            label = item_data.get("examine_label")
            if label and not renpy.has_label(label):
                issues.append("Item '{}' examine_label points to missing label '{}'.".format(item_id, label))

        for key, recipe_data in (globals().get("item_recipe_defs", {}) or {}).items():
            result = recipe_data.get("result")
            if result and result not in globals().get("item_defs", {}):
                issues.append("Recipe '{}' points to missing result item '{}'.".format(key, result))
            label = recipe_data.get("label")
            if label and not renpy.has_label(label):
                issues.append("Recipe '{}' points to missing label '{}'.".format(key, label))
            debug_validate_requirements("Recipe '{}'".format(key), recipe_data.get("requires"), issues)

        for cid, entries in (globals().get("character_interact_entries", {}) or {}).items():
            seen_interaction_ids = set()
            groups = {}
            specials = []
            for entry in entries or []:
                entry_id = entry.get("id")
                if not entry_id:
                    issues.append("Character '{}' has an interact entry with no id.".format(cid))
                    continue
                if entry_id in seen_interaction_ids:
                    issues.append("Character '{}' has duplicate interact id '{}'.".format(cid, entry_id))
                seen_interaction_ids.add(entry_id)
                label = entry.get("label")
                if label and not renpy.has_label(label):
                    issues.append("Character '{}' interact '{}' points to missing label '{}'.".format(cid, entry_id, label))
                debug_validate_requirements("Character '{}' interact '{}'".format(cid, entry_id), entry.get("requires") or entry.get("unlocks_after"), issues)
                group = entry.get("group")
                if group:
                    groups.setdefault(group, []).append(entry)
                if entry.get("special"):
                    specials.append(entry)
                    if not group and not entry.get("unlocks_after"):
                        issues.append("Character '{}' special interact '{}' has no group or unlocks_after requirement.".format(cid, entry_id))
            for special in specials:
                group = special.get("group")
                if not group:
                    continue
                required = [e for e in groups.get(group, []) if not e.get("special") and e.get("required_for_group", True)]
                if not required:
                    issues.append("Character '{}' special interact '{}' uses group '{}' with no required normal interactions.".format(cid, special.get("id"), group))

        for cid, entries in (globals().get("character_talk_entries", {}) or {}).items():
            seen_talk_ids = set()
            for entry in entries or []:
                entry_id = entry.get("id")
                if not entry_id:
                    issues.append("Character '{}' has a talk entry with no id.".format(cid))
                    continue
                if entry_id in seen_talk_ids:
                    issues.append("Character '{}' has duplicate talk id '{}'.".format(cid, entry_id))
                seen_talk_ids.add(entry_id)
                label = entry.get("label")
                if label and not renpy.has_label(label):
                    issues.append("Character '{}' talk '{}' points to missing label '{}'.".format(cid, entry_id, label))
                debug_validate_requirements("Character '{}' talk '{}'".format(cid, entry_id), entry.get("requires"), issues)

        seen_phone_apps = set()
        for app_id in globals().get("phone_app_order", []) or []:
            if app_id in seen_phone_apps:
                issues.append("Duplicate phone app id '{}'.".format(app_id))
            seen_phone_apps.add(app_id)
            app = (globals().get("phone_app_defs", {}) or {}).get(app_id)
            if not app:
                issues.append("phone_app_order references missing app '{}'.".format(app_id))
                continue
            if not app.get("label"):
                issues.append("Phone app '{}' has no label.".format(app_id))
            debug_validate_requirements("Phone app '{}'".format(app_id), app.get("requires"), issues)

        seen_note_ids = set()
        for note in globals().get("phone_notes", []) or []:
            if not isinstance(note, dict):
                continue
            note_id = note.get("id")
            if not note_id:
                issues.append("Phone note has no id.")
                continue
            if note_id in seen_note_ids:
                issues.append("Duplicate phone note id '{}'.".format(note_id))
            seen_note_ids.add(note_id)
            debug_validate_requirements("Phone note '{}'".format(note_id), note.get("requires"), issues)
            for index, row in enumerate(note.get("rows", []) or []):
                if isinstance(row, dict):
                    if not row.get("text"):
                        issues.append("Phone note '{}' row #{} has no text.".format(note_id, index + 1))
                    debug_validate_requirements("Phone note '{}' row #{} visibility".format(note_id, index + 1), row.get("requires"), issues)
                    debug_validate_requirements("Phone note '{}' row #{} done".format(note_id, index + 1), row.get("done"), issues)

        seen_startup_ids = set()
        for entry in globals().get("startup_screen_defs", []) or []:
            sid = entry.get("id")
            if not sid:
                issues.append("Startup notice has no id.")
                continue
            if sid in seen_startup_ids:
                issues.append("Duplicate startup notice id '{}'.".format(sid))
            seen_startup_ids.add(sid)
            if not entry.get("title"):
                issues.append("Startup notice '{}' has no title.".format(sid))
            debug_validate_requirements("Startup notice '{}'".format(sid), entry.get("requires"), issues)

        achievement_defs_data = globals().get("achievement_defs", {}) or {}
        for aid, achievement_data in achievement_defs_data.items():
            if not achievement_data.get("title"):
                issues.append("Achievement '{}' has no title.".format(aid))
            debug_validate_requirements("Achievement '{}'".format(aid), achievement_data.get("requires"), issues)
        for mid, milestone_data in (globals().get("milestone_defs", {}) or {}).items():
            aid = milestone_data.get("achievement")
            if aid and aid not in achievement_defs_data:
                issues.append("Milestone '{}' references missing achievement '{}'.".format(mid, aid))
            gid = milestone_data.get("gallery")
            if gid and not gallery_scene(gid):
                issues.append("Milestone '{}' references missing gallery scene '{}'.".format(mid, gid))
            debug_validate_requirements("Milestone '{}'".format(mid), milestone_data.get("requires"), issues)

        player_stat_defs_data = globals().get("PLAYER_STAT_DEFS", {}) or {}
        for stat_id, stat_data in player_stat_defs_data.items():
            if stat_data.get("max") is not None and stat_data.get("min") is not None:
                if int(stat_data.get("max")) < int(stat_data.get("min")):
                    issues.append("Player stat '{}' has max below min.".format(stat_id))
        for perk_id, perk_data in (globals().get("perk_defs", {}) or {}).items():
            stat_id = perk_data.get("stat")
            if stat_id and stat_id not in player_stat_defs_data:
                issues.append("Perk '{}' references missing player stat '{}'.".format(perk_id, stat_id))
            debug_validate_requirements("Perk '{}'".format(perk_id), perk_data.get("requires"), issues)

        for preset_id in globals().get("quick_start_order", []) or []:
            preset = (globals().get("quick_start_defs", {}) or {}).get(preset_id)
            if not preset:
                issues.append("quick_start_order references missing preset '{}'.".format(preset_id))
                continue
            location = preset.get("location")
            if location and location not in locations_data:
                issues.append("Quick start '{}' points to missing location '{}'.".format(preset_id, location))
            setup = preset.get("setup")
            if isinstance(setup, str) and not renpy.has_label(setup):
                issues.append("Quick start '{}' points to missing setup label '{}'.".format(preset_id, setup))

        for sound_id, sound_data in (globals().get("sound_presets", {}) or {}).items():
            if not sound_data.get("channel"):
                issues.append("Sound preset '{}' has no channel.".format(sound_id))
            if sound_data.get("file"):
                try:
                    if not renpy.loadable(sound_data.get("file")):
                        issues.append("Sound preset '{}' points to missing file '{}'.".format(sound_id, sound_data.get("file")))
                except Exception:
                    pass

        for index, layer in enumerate(globals().get("main_menu_layers", []) or []):
            image = layer.get("image")
            if not image:
                issues.append("Main menu layer #{} has no image.".format(index + 1))
            elif isinstance(image, str):
                try:
                    if "/" in image and not renpy.loadable(image):
                        issues.append("Main menu layer #{} points to missing file '{}'.".format(index + 1, image))
                except Exception:
                    pass

        migration_rules = globals().get("save_migration_rules", {}) or {}
        for old, new in migration_rules.get("items", {}).items():
            if new not in globals().get("item_defs", {}):
                issues.append("Item migration '{}' -> '{}' points to missing new item.".format(old, new))
        for old, new in migration_rules.get("quests", {}).items():
            if new not in globals().get("quest_defs", {}):
                issues.append("Quest migration '{}' -> '{}' points to missing new quest.".format(old, new))
        for (quest_id, old), new in migration_rules.get("objectives", {}).items():
            qdef = (globals().get("quest_defs", {}) or {}).get(quest_id)
            if not qdef:
                issues.append("Objective migration '{}.{}' -> '{}' points to missing quest.".format(quest_id, old, new))
                continue
            objective_ids = []
            for objective in qdef.get("objectives", []) or []:
                if isinstance(objective, dict):
                    objective_ids.append(objective.get("oid") or objective.get("id"))
            if new not in objective_ids:
                issues.append("Objective migration '{}.{}' -> '{}' points to missing new objective.".format(quest_id, old, new))

        for qid, qdef in (globals().get("quest_defs", {}) or {}).items():
            debug_validate_requirements("Quest '{}' unlock".format(qid), qdef.get("unlock_when"), issues)
            debug_validate_requirements("Quest '{}' start".format(qid), qdef.get("start_when"), issues)
            debug_validate_quest_target(qid, "quest target", qdef.get("target"), issues)
            for objective in qdef.get("objectives", []) or []:
                oid = objective.get("oid") or objective.get("id") if isinstance(objective, dict) else "<objective>"
                target = objective.get("target") if isinstance(objective, dict) else None
                debug_validate_quest_target(qid, "objective '{}'".format(oid), target, issues)
                if isinstance(objective, dict):
                    debug_validate_requirements("Quest '{}' objective '{}'".format(qid, oid), objective.get("requires") or objective.get("unlock_when"), issues)

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


    def debug_validate_quest_target(qid, context, target, issues):
        if not target:
            return
        if target.get("targets"):
            for entry in target.get("targets") or []:
                merged = dict(target)
                merged.pop("targets", None)
                merged.update(entry)
                debug_validate_quest_target(qid, context, merged, issues)
            return
        if target.get("location") and target.get("location") not in (globals().get("locations", {}) or {}):
            issues.append("Quest '{}' {} references missing location '{}'.".format(qid, context, target.get("location")))
        if target.get("area") and target.get("area") not in (globals().get("areas", {}) or {}):
            issues.append("Quest '{}' {} references missing area '{}'.".format(qid, context, target.get("area")))
        for cid in [target.get("npc")] + list(target.get("characters") or []):
            if cid and cid not in (globals().get("character_stats", {}) or {}):
                issues.append("Quest '{}' {} references missing character '{}'.".format(qid, context, cid))
        if target.get("item") and target.get("item") not in (globals().get("item_defs", {}) or {}):
            issues.append("Quest '{}' {} references missing item '{}'.".format(qid, context, target.get("item")))
        if target.get("object") and target.get("object") not in (globals().get("interactable_defs", {}) or {}):
            issues.append("Quest '{}' {} references missing object/interactable '{}'.".format(qid, context, target.get("object")))
        label = target.get("label")
        if label and not renpy.has_label(label):
            issues.append("Quest '{}' {} points to missing label '{}'.".format(qid, context, label))


    def debug_validate_requirements(context, requirements, issues):
        if not requirements or callable(requirements):
            return
        if isinstance(requirements, dict):
            debug_validate_requirement_dict(context, requirements, issues)
            return
        if isinstance(requirements, (list, tuple, set)):
            for rule in requirements:
                debug_validate_requirements(context, rule, issues)
            return
        if isinstance(requirements, str):
            debug_validate_requirement_string(context, requirements, issues)


    def debug_validate_requirement_dict(context, requirements, issues):
        known = {
            "flags", "blocked_by_flags", "unless", "stats", "character_stats",
            "items", "quests_completed", "quests_active", "quest_objectives",
            "time", "locations", "areas",
        }
        for key in requirements.keys():
            if key not in known:
                issues.append("{} has unknown requirement key '{}'.".format(context, key))
        for stat_name in (requirements.get("stats") or {}).keys():
            if not debug_known_player_stat(stat_name):
                issues.append("{} requires missing player stat '{}'.".format(context, stat_name))
        for char_name, stats in (requirements.get("character_stats") or {}).items():
            cid = debug_character_id(char_name)
            if cid not in (globals().get("character_stats", {}) or {}):
                issues.append("{} requires missing character '{}'.".format(context, char_name))
            for stat_name in (stats or {}).keys():
                if not debug_known_character_stat(stat_name):
                    issues.append("{} requires missing character stat '{}'.".format(context, stat_name))
        for item_id in (requirements.get("items") or {}).keys():
            if item_id not in (globals().get("item_defs", {}) or {}):
                issues.append("{} requires missing item '{}'.".format(context, item_id))
        for qid in _debug_as_list(requirements.get("quests_completed")) + _debug_as_list(requirements.get("quests_active")):
            if qid not in (globals().get("quest_defs", {}) or {}):
                issues.append("{} requires missing quest '{}'.".format(context, qid))
        for qid, oids in (requirements.get("quest_objectives") or {}).items():
            if qid not in (globals().get("quest_defs", {}) or {}):
                issues.append("{} requires missing quest '{}'.".format(context, qid))
                continue
            known_oids = debug_quest_objective_ids(qid)
            for oid in _debug_as_list(oids):
                if oid not in known_oids:
                    issues.append("{} requires missing quest objective '{}.{}'.".format(context, qid, oid))
        for loc_id in _debug_as_list(requirements.get("locations")):
            if loc_id not in (globals().get("locations", {}) or {}):
                issues.append("{} requires missing location '{}'.".format(context, loc_id))
        for area_id in _debug_as_list(requirements.get("areas")):
            if area_id not in (globals().get("areas", {}) or {}):
                issues.append("{} requires missing area '{}'.".format(context, area_id))


    def debug_validate_requirement_string(context, rule, issues):
        raw = str(rule).strip()
        if not raw:
            return
        compare = _debug_parse_compare_requirement(raw)
        if compare:
            left, op, right = compare
            left = left.replace("stat:", "").strip()
            if "." in left:
                char_name, stat_name = left.split(".", 1)
                if debug_character_id(char_name) not in (globals().get("character_stats", {}) or {}):
                    issues.append("{} requires missing character '{}'.".format(context, char_name))
                if not debug_known_character_stat(stat_name):
                    issues.append("{} requires missing character stat '{}'.".format(context, stat_name))
            elif not debug_known_player_stat(left):
                issues.append("{} requires missing player stat '{}'.".format(context, left))
            return

        key, sep, value = raw.partition(":")
        if not sep:
            return
        key = key.strip().lower()
        value = value.strip()
        if key in ("item", "has_item", "no_item"):
            item_id = value.split(">=", 1)[0].strip()
            if item_id and item_id not in (globals().get("item_defs", {}) or {}):
                issues.append("{} requires missing item '{}'.".format(context, item_id))
        elif key == "tag":
            known_tags = set()
            for item in (globals().get("item_defs", {}) or {}).values():
                known_tags.update(item.get("tags", []) or [])
            if value and value not in known_tags:
                issues.append("{} requires missing item tag '{}'.".format(context, value))
        elif key in ("quest_done", "quest_completed", "quest_active", "quest_started", "quest_unlocked", "quest_discovered", "discover"):
            if value and value not in (globals().get("quest_defs", {}) or {}):
                issues.append("{} requires missing quest '{}'.".format(context, value))
        elif key in ("quest_step", "step"):
            qid, _, oid = value.partition(".")
            if qid not in (globals().get("quest_defs", {}) or {}):
                issues.append("{} requires missing quest '{}'.".format(context, qid))
            elif oid and oid not in debug_quest_objective_ids(qid):
                issues.append("{} requires missing quest objective '{}.{}'.".format(context, qid, oid))
        elif key in ("loc", "location"):
            if value and value not in (globals().get("locations", {}) or {}):
                issues.append("{} requires missing location '{}'.".format(context, value))
        elif key == "area":
            if value and value not in (globals().get("areas", {}) or {}):
                issues.append("{} requires missing area '{}'.".format(context, value))
        elif key in ("present", "character_present", "npc"):
            if debug_character_id(value) not in (globals().get("character_stats", {}) or {}):
                issues.append("{} requires missing character '{}'.".format(context, value))
        elif key in ("mood", "char_mood"):
            char_name, _, mood_name = value.partition(".")
            if mood_name:
                if debug_character_id(char_name) not in (globals().get("character_stats", {}) or {}):
                    issues.append("{} requires missing character '{}'.".format(context, char_name))
            else:
                mood_name = value
            if mood_name and mood_name.lower() not in [str(m).lower() for m in (globals().get("MOOD_DEFS", {}) or {}).keys()]:
                issues.append("{} requires missing mood '{}'.".format(context, mood_name))
        elif key == "system":
            if value and value not in (globals().get("SYSTEM_DEFAULTS", {}) or {}):
                issues.append("{} requires missing system '{}'.".format(context, value))
        elif key not in ("flag", "has_flag", "blocked_by_flag", "blocked_by_flags", "unless", "no_flag", "time", "weekday"):
            issues.append("{} has unknown requirement prefix '{}'.".format(context, key))


    def _debug_as_list(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]


    def _debug_parse_compare_requirement(rule):
        for op in (">=", "<=", "==", "!=", ">", "<"):
            if op in rule:
                left, right = rule.split(op, 1)
                return left.strip(), op, right.strip()
        return None


    def debug_known_player_stat(stat_name):
        target = str(stat_name).lower()
        for key, data in (globals().get("PLAYER_STAT_DEFS", {}) or {}).items():
            if key.lower() == target:
                return True
            for alias in data.get("aliases", []) or []:
                if str(alias).lower() == target:
                    return True
        return False


    def debug_known_character_stat(stat_name):
        target = str(stat_name).lower()
        return any(str(key).lower() == target for key in (globals().get("CHARACTER_STAT_DEFS", {}) or {}).keys())


    def debug_character_id(name):
        raw = str(name or "").strip()
        norm = raw.lower().replace(" ", "_")
        if norm in (globals().get("character_stats", {}) or {}):
            return norm
        for cid in (globals().get("character_stats", {}) or {}).keys():
            try:
                if character_display_name(cid).lower() == raw.lower():
                    return cid
            except Exception:
                pass
        return norm


    def debug_quest_objective_ids(qid):
        qdef = (globals().get("quest_defs", {}) or {}).get(qid, {}) or {}
        out = []
        for objective in qdef.get("objectives", []) or []:
            if isinstance(objective, dict):
                oid = objective.get("oid") or objective.get("id")
                if oid:
                    out.append(oid)
            else:
                oid = getattr(objective, "id", None)
                if oid:
                    out.append(oid)
        return out


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
            last_actions.clear()
            action_memory.clear()
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
            spacing 8
            text "Progress snapshot" style "debug_tool_heading"
            text "[label_progress_summary()]" style "debug_tool_body"
            hbox:
                spacing 12
                for _row in label_progress_rows():
                    text "[_row['label']]: [_row['value']]" style "debug_tool_muted"
            hbox:
                spacing 12
                for _row in completion_progress_rows():
                    text "[_row['label']]: [_row['done']]/[_row['total']]" style "debug_tool_muted"

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
                textbutton ("Screenshot: ON" if screenshot_mode else "Screenshot: OFF") action Function(toggle_screenshot_mode) style "debug_tool_small_button" text_style "debug_tool_small_button_text"
                null

    frame:
        style "debug_tool_card"
        xfill True
        vbox:
            spacing 10
            text "Quick starts" style "debug_tool_heading"
            $ _quick_starts = visible_quick_starts()
            if not _quick_starts:
                text "No quick starts registered." style "debug_tool_muted"
            else:
                for _preset in _quick_starts:
                    button:
                        xfill True
                        background "#141927cc"
                        hover_background "#263a5add"
                        padding (10, 8)
                        action Function(apply_quick_start, _preset.get("id"))
                        vbox:
                            spacing 2
                            text "[_preset.get('title')]" size 17 color "#e8f1ff"
                            if _preset.get("desc"):
                                text "[_preset.get('desc')]" size 13 color "#9fb1c7"


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
