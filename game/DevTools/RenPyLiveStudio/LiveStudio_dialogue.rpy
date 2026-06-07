# Scene-owned dialogue controllers and no-code story event editing.

init -950 python in live_studio:
    DIALOGUE_EVENT_TYPES = (
        "say", "narration", "choice", "script", "jump", "call", "return",
        "show_image", "hide_image", "show_screen", "hide_screen", "pause", "transition",
        "play_music", "play_sound", "stop_audio", "renpy",
    )

    def dialogue_scene(state=None):
        state = state or resolve_frame()
        return preferred_dialogue_scene(state)

    def controller_by_id(controller_id, state=None):
        state = state or resolve_frame()
        for controller in state.get("dialogue_controllers", []):
            if controller.get("id") == controller_id:
                return controller
        return None

    def selected_dialogue_controller(state=None):
        state = state or resolve_frame()
        item, parent_id, kind = find_state_item(state, selected_item_id)
        if kind == "dialogue_controller":
            return item
        if kind == "dialogue_event":
            return controller_by_id(parent_id, state)
        if kind == "dialogue_choice":
            event, controller_id, _event_kind = find_state_item(state, parent_id)
            return controller_by_id(controller_id, state)
        controllers = state.get("dialogue_controllers", [])
        return controllers[0] if controllers else None

    def ensure_dialogue_controller(scene_id=None):
        state = resolve_frame()
        controller = selected_dialogue_controller(state)
        if controller is not None:
            return controller
        scene = None
        if scene_id:
            scene, _parent, kind = find_state_item(state, scene_id)
            if kind != "scene":
                scene = None
        if scene is None:
            scene = dialogue_scene(state)
        if scene is None:
            scene = ensure_scene("Dialogue", "dialogue")
        controller = new_dialogue_controller("Dialogue", scene.get("id") if scene else None)
        controller["source"] = {"created_by": "live_studio"}
        add_change(None, None, controller, root_collection="dialogue_controllers", label="Add dialogue controller")
        select_item(controller.get("id"), "dialogue_controller")
        set_bottom_tab("Dialogue")
        return next((item for item in resolve_frame().get("dialogue_controllers", []) if item.get("id") == controller.get("id")), controller)

    def _captured_screen_variable(state, role, variable, fallback_screen):
        candidates = []
        preferred_layer = getattr(config, "say_layer", "screens") if role == "say" else "screens"
        candidates.append((fallback_screen, preferred_layer))
        for screen in state.get("ui_screens", []):
            if str(screen.get("role") or "").lower() == role:
                pair = (screen.get("name") or fallback_screen, screen.get("layer") or preferred_layer)
                if pair not in candidates:
                    candidates.append(pair)
        for screen_name, layer in candidates:
            try:
                value = renpy.get_screen_variable(variable, screen=screen_name, layer=layer)
                if value is not None:
                    return value
            except Exception:
                continue
        return None

    def capture_runtime_dialogue(state):
        what = _captured_screen_variable(state, "say", "what", "say")
        who = _captured_screen_variable(state, "say", "who", "say")
        if what is None:
            what = getattr(renpy.store, "_last_say_what", None)
        if who is None:
            who = getattr(renpy.store, "_last_say_who", None)

        choice_items = _captured_screen_variable(state, "choice", "items", "choice")

        if not what and not choice_items:
            return state

        scene = dialogue_scene(state)
        if scene is None:
            scene = new_scene("Dialogue", ["characters", "dialogue"], "dialogue")
            state.setdefault("scenes", []).append(scene)
        controller = new_dialogue_controller("Dialogue", scene.get("id"))
        controller["source"] = clone(state.get("source_ref", {}))

        if what and not choice_items:
            event = new_dialogue_event("say" if who else "narration")
            event["speaker"] = str(who or "")
            event["text"] = str(what)
            event["source"] = clone(state.get("source_ref", {}))
            controller["events"].append(event)
            controller["active_event_id"] = event.get("id")
            controller["selected_event_id"] = event.get("id")
            controller["frame_event_ids"].append(event.get("id"))

        if choice_items:
            event = new_dialogue_event("choice")
            # Ren'Py menus may contain a say/narration caption that is shown
            # during the same interaction as the choices.
            event["speaker"] = str(who or "") if what else ""
            event["text"] = str(what or "")
            event["choices"] = []
            try:
                iterable = list(choice_items)
            except Exception:
                iterable = []
            for item in iterable:
                caption = getattr(item, "caption", None)
                if caption is None and isinstance(item, (tuple, list)) and item:
                    caption = item[0]
                action = getattr(item, "action", None)
                option = new_choice_option(str(caption or "Choice"))
                option["runtime_action"] = serialize_action(action)
                event["choices"].append(option)
            controller["events"].append(event)
            controller["active_event_id"] = event.get("id")
            controller["selected_event_id"] = event.get("id")
            controller["frame_event_ids"].append(event.get("id"))

        state.setdefault("dialogue_controllers", []).append(controller)
        return state

    def dialogue_events(controller=None):
        controller = controller or selected_dialogue_controller()
        return controller.get("events", []) if controller else []

    def selected_dialogue_event():
        state = resolve_frame()
        item, _parent_id, kind = find_state_item(state, selected_item_id)
        if kind == "dialogue_event":
            return item
        if kind == "dialogue_choice":
            event, _controller_id, event_kind = find_state_item(state, _parent_id)
            return event if event_kind == "dialogue_event" else None
        controller = selected_dialogue_controller(state)
        if controller is None:
            return None
        selected_id = controller.get("selected_event_id") or controller.get("active_event_id")
        for event in controller.get("events", []):
            if event.get("id") == selected_id:
                return event
        events = controller.get("events", [])
        return events[0] if events else None

    def active_dialogue_event(controller=None, state=None):
        state = state or resolve_frame()
        controller = controller or selected_dialogue_controller(state)
        if controller is None:
            return None
        active_id = controller.get("active_event_id")
        for event in controller.get("events", []):
            if event.get("id") == active_id:
                return event
        return None

    def select_dialogue_event(event_id):
        controller = selected_dialogue_controller()
        if controller is not None:
            set_item_value(controller.get("id"), "selected_event_id", event_id, "Select dialogue event")
        select_item(event_id, "dialogue_event")
        set_bottom_tab("Dialogue")

    def dialogue_event_is_interaction(event):
        return bool(event and event.get("type") in ("say", "narration", "choice", "pause"))

    def frame_dialogue_events(controller=None, state=None):
        state = state or resolve_frame()
        controller = controller or selected_dialogue_controller(state)
        if controller is None:
            return []
        by_id = {event.get("id"): event for event in controller.get("events", [])}
        ids = list(controller.get("frame_event_ids", []) or [])
        # Only legacy controllers without a queue field fall back to the
        # active event. An explicit empty queue means this inherited frame has
        # no dialogue interaction of its own.
        if "frame_event_ids" not in controller and controller.get("active_event_id"):
            ids = [controller.get("active_event_id")]
        return [by_id[event_id] for event_id in ids if event_id in by_id]

    def set_active_dialogue_event(event_id):
        global project_dirty
        state = resolve_frame()
        controller = selected_dialogue_controller(state)
        if controller is None:
            return
        event, _parent_id, kind = find_state_item(state, event_id)
        if kind != "dialogue_event":
            return
        frame = current_frame()
        if frame is None:
            return
        before = clone(frame.get("changes", {}))
        controller_sets = frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(controller.get("id"), {})

        # Inherited frame queues are not replayed. The first event selected in a
        # child frame starts a fresh local queue.
        if "frame_event_ids" in controller_sets:
            event_ids = list(controller.get("frame_event_ids", []) or [])
        else:
            event_ids = []

        events_by_id = {candidate.get("id"): candidate for candidate in controller.get("events", [])}
        if dialogue_event_is_interaction(event):
            event_ids = [candidate_id for candidate_id in event_ids if not dialogue_event_is_interaction(events_by_id.get(candidate_id))]
            event_ids.append(event_id)
            controller_sets["active_event_id"] = event_id
        else:
            if event_id not in event_ids:
                # Commands execute before the frame's interaction even when the
                # command is added after the dialogue line in the editor.
                insert_at = len(event_ids)
                for index, candidate_id in enumerate(event_ids):
                    if dialogue_event_is_interaction(events_by_id.get(candidate_id)):
                        insert_at = index
                        break
                event_ids.insert(insert_at, event_id)
            # A command-only frame must not keep showing the parent's line.
            # If this local queue already has an interaction, keep that event
            # active; otherwise explicitly hide dialogue for this frame.
            local_interaction = None
            for candidate_id in event_ids:
                if dialogue_event_is_interaction(events_by_id.get(candidate_id)):
                    local_interaction = candidate_id
            controller_sets["active_event_id"] = local_interaction

        controller_sets["frame_event_ids"] = event_ids
        controller_sets["selected_event_id"] = event_id
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache()
        project_dirty = True
        _record_frame_change("Use dialogue event in frame", before, after)
        select_item(event_id, "dialogue_event")
        set_bottom_tab("Dialogue")

    def add_dialogue_event(event_type="say"):
        if event_type not in DIALOGUE_EVENT_TYPES:
            event_type = "say"
        controller = ensure_dialogue_controller()
        if controller is None:
            return None
        event = new_dialogue_event(event_type)
        add_change(controller.get("id"), "events", event, label="Add {} event".format(event_type.replace("_", " ")))
        set_active_dialogue_event(event.get("id"))
        return event

    def add_audio_event(filename, channel="music"):
        event_type = "play_music" if str(channel) == "music" else "play_sound"
        event = add_dialogue_event(event_type)
        if event is not None:
            set_item_value(event.get("id"), "audio", str(filename or ""), "Set audio file")
            set_item_value(event.get("id"), "channel", str(channel or "music"), "Set audio channel")
            set_bottom_tab("Dialogue")
        return event

    def remove_dialogue_event(event_id=None):
        event = selected_dialogue_event()
        event_id = event_id or (event or {}).get("id")
        if not event_id:
            return
        controller = selected_dialogue_controller()
        controller_id = (controller or {}).get("id")
        remove_item(event_id, "Remove dialogue event")
        updated = controller_by_id(controller_id) if controller_id else None
        if updated:
            remaining_ids = [value for value in updated.get("frame_event_ids", []) if value != event_id]
            set_item_value(controller_id, "frame_event_ids", remaining_ids, "Update frame dialogue queue")
            if updated.get("active_event_id") == event_id:
                next_active = None
                for candidate in frame_dialogue_events(updated):
                    if dialogue_event_is_interaction(candidate):
                        next_active = candidate.get("id")
                set_item_value(controller_id, "active_event_id", next_active, "Update current dialogue event")

    def move_dialogue_event(event_id, direction):
        global selected_item_id
        previous = selected_item_id
        selected_item_id = event_id
        reorder_selected("forward" if direction > 0 else "backward")
        selected_item_id = previous

    def add_choice_option(event_id=None):
        event_id = event_id or (selected_dialogue_event() or {}).get("id")
        event, _parent_id, kind = find_state_item(resolve_frame(), event_id)
        if event is None or kind != "dialogue_event" or event.get("type") != "choice":
            return None
        choice = new_choice_option()
        add_change(event_id, "choices", choice, label="Add choice")
        select_item(choice.get("id"), "dialogue_choice")
        return choice

    def remove_choice_option(choice_id):
        remove_item(choice_id, "Remove choice")

    def event_field_changed(event_id, field):
        return property_changed(event_id, field)

    def choice_field_changed(choice_id, field):
        return property_changed(choice_id, field)

    def _source_string(value):
        return repr(str(value or ""))

    def dialogue_event_source(event, indent="", say_screen=None, choice_screen=None):
        if not event:
            return []
        event_type = event.get("type")
        lines = []
        condition = str(event.get("condition", "")).strip()
        prefix = indent
        if condition and event_type != "choice":
            lines.append("{}if {}:".format(indent, condition))
            prefix += "    "

        if event_type == "say":
            speaker = safe_identifier(event.get("speaker"), "speaker")
            screen_argument = " (screen={})".format(repr(str(say_screen))) if say_screen else ""
            lines.append("{}{} {}{}".format(prefix, speaker, _source_string(event.get("text")), screen_argument))
        elif event_type == "narration":
            screen_argument = " (screen={})".format(repr(str(say_screen))) if say_screen else ""
            lines.append("{}{}{}".format(prefix, _source_string(event.get("text")), screen_argument))
        elif event_type == "script":
            script = str(event.get("script", "")).strip()
            if not script:
                lines.append("{}pass".format(prefix))
            elif "\n" in script:
                lines.append("{}python:".format(prefix))
                for script_line in script.splitlines():
                    lines.append("{}    {}".format(prefix, script_line))
            else:
                lines.append("{}$ {}".format(prefix, script))
        elif event_type == "renpy":
            statement = str(event.get("script", "")).strip()
            if statement:
                for statement_line in statement.splitlines():
                    lines.append("{}{}".format(prefix, statement_line))
            else:
                lines.append("{}pass".format(prefix))
        elif event_type == "jump":
            lines.append("{}jump {}".format(prefix, safe_identifier(event.get("target"), "target_label")))
        elif event_type == "call":
            lines.append("{}call {}".format(prefix, safe_identifier(event.get("target"), "target_label")))
        elif event_type == "return":
            lines.append("{}return".format(prefix))
        elif event_type == "show_image":
            lines.append("{}show {}".format(prefix, str(event.get("image") or "image")))
        elif event_type == "hide_image":
            lines.append("{}hide {}".format(prefix, safe_identifier(str(event.get("image") or "image").split()[0], "image")))
        elif event_type == "show_screen":
            lines.append("{}show screen {}".format(prefix, safe_identifier(event.get("screen"), "screen_name")))
        elif event_type == "hide_screen":
            lines.append("{}hide screen {}".format(prefix, safe_identifier(event.get("screen"), "screen_name")))
        elif event_type == "pause":
            duration = float(event.get("duration", 0.0) or 0.0)
            if duration > 0.0:
                lines.append("{}pause {}".format(prefix, duration))
            else:
                lines.append("{}pause".format(prefix))
        elif event_type == "transition":
            lines.append("{}with {}".format(prefix, str(event.get("transition") or "dissolve")))
        elif event_type in ("play_music", "play_sound"):
            channel = "music" if event_type == "play_music" else "sound"
            command = "{}play {} {}".format(prefix, channel, _source_string(event.get("audio")))
            fadein = float(event.get("fadein", 0.0) or 0.0)
            if fadein > 0:
                command += " fadein {}".format(fadein)
            lines.append(command)
        elif event_type == "stop_audio":
            channel = str(event.get("channel") or "music")
            command = "{}stop {}".format(prefix, safe_identifier(channel, "music"))
            fadeout = float(event.get("fadeout", 0.0) or 0.0)
            if fadeout > 0:
                command += " fadeout {}".format(fadeout)
            lines.append(command)
        elif event_type == "choice":
            if choice_screen:
                lines.append("{}menu (screen={}):".format(prefix, repr(str(choice_screen))))
            else:
                lines.append("{}menu:".format(prefix))
            prompt_text = str(event.get("text", "") or "")
            if prompt_text:
                prompt_prefix = prefix + "    "
                screen_argument = " (screen={})".format(repr(str(say_screen))) if say_screen else ""
                if str(event.get("speaker", "") or "").strip():
                    speaker = safe_identifier(event.get("speaker"), "speaker")
                    lines.append("{}{} {}{}".format(prompt_prefix, speaker, _source_string(prompt_text), screen_argument))
                else:
                    lines.append("{}{}{}".format(prompt_prefix, _source_string(prompt_text), screen_argument))
            choices = event.get("choices", [])
            if not choices:
                lines.append("{}    pass".format(prefix))
            for choice in choices:
                suffix = " if {}".format(choice.get("condition")) if str(choice.get("condition", "")).strip() else ""
                lines.append("{}    {}{}:".format(prefix, _source_string(choice.get("caption", "Choice")), suffix))
                script = str(choice.get("script", "")).strip()
                target = str(choice.get("target", "")).strip()
                target_frame_id = str(choice.get("target_frame_id", "")).strip()
                if script:
                    if "\n" in script:
                        lines.append("{}        python:".format(prefix))
                        for script_line in script.splitlines():
                            lines.append("{}            {}".format(prefix, script_line))
                    else:
                        lines.append("{}        $ {}".format(prefix, script))
                if target_frame_id:
                    target_frame = frame_by_id(target_frame_id)
                    lines.append("{}        jump {}".format(prefix, frame_label(target_frame) if target_frame else "missing_frame"))
                elif target:
                    lines.append("{}        jump {}".format(prefix, safe_identifier(target, "target_label")))
                elif not script:
                    lines.append("{}        pass".format(prefix))
        return lines

    def dialogue_source(controller=None):
        controller = controller or selected_dialogue_controller()
        if controller is None:
            return "# No dialogue controller in this frame."
        lines = ["# Scene dialogue: {}".format(controller.get("name", "Dialogue"))]
        active_id = controller.get("active_event_id")
        for index, event in enumerate(controller.get("events", [])):
            marker = "  # CURRENT FRAME" if event.get("id") == active_id else ""
            lines.append("# Event {}: {}{}".format(index + 1, event.get("type", "say"), marker))
            lines.extend(dialogue_event_source(event))
            lines.append("")
        return "\n".join(lines).rstrip()
