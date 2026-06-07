# Scene-owned dialogue controllers and event editing.

init -900 python in live_studio:
    DIALOGUE_EVENT_TYPES = ("say", "narration", "choice", "script", "jump", "call", "return", "condition")

    def dialogue_scene(state=None):
        state = state or resolve_frame()
        for scene in state.get("scenes", []):
            if scene.get("name") == "Dialogue":
                return scene
        return state.get("scenes", [None])[0] if state.get("scenes") else None

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
        for controller in state.get("dialogue_controllers", []):
            return controller
        return None

    def dialogue_controller_node(scene, controller):
        return new_scene_node(
            controller.get("name", "Dialogue"),
            "dialogue",
            controller_id=controller.get("id"),
            selectable=True,
            editability="editable",
            source={"created_by": "live_studio"},
            properties={},
            bounds=None,
        )

    def ensure_dialogue_controller():
        state = resolve_frame()
        controller = selected_dialogue_controller(state)
        if controller is not None:
            return controller

        controller = new_dialogue_controller("Dialogue")
        add_change(None, None, controller, root_collection="dialogue_controllers", label="Add dialogue controller")
        state = resolve_frame()
        controller = next((item for item in state.get("dialogue_controllers", []) if item.get("id") == controller.get("id")), None)
        scene = dialogue_scene(state)
        if scene is None:
            scene = new_scene("Dialogue", ["characters", "dialogue"])
            add_change(None, None, scene, root_collection="scenes", label="Add dialogue scene")
            state = resolve_frame()
            scene = dialogue_scene(state)
        if scene is not None and controller is not None:
            node = dialogue_controller_node(scene, controller)
            add_change(scene.get("id"), "nodes", node, label="Attach dialogue to scene")
            select_item(controller.get("id"), "dialogue_controller")
        return controller

    def capture_runtime_dialogue(state):
        who = None
        what = None
        try:
            what = renpy.get_screen_variable("what", screen="say", layer="screens")
        except Exception:
            pass
        try:
            who = renpy.get_screen_variable("who", screen="say", layer="screens")
        except Exception:
            pass

        choice_items = None
        try:
            choice_items = renpy.get_screen_variable("items", screen="choice", layer="screens")
        except Exception:
            choice_items = None

        if not what and not choice_items:
            return state

        controller = new_dialogue_controller("Dialogue")
        controller["source"] = clone(state.get("source_ref", {}))
        if what:
            event = new_dialogue_event("say" if who else "narration")
            event["speaker"] = str(who or "")
            event["text"] = str(what)
            controller["events"].append(event)
            controller["active_event_id"] = event.get("id")
            controller["selected_event_id"] = event.get("id")
        if choice_items:
            event = new_dialogue_event("choice")
            event["choices"] = []
            for item in choice_items:
                caption = getattr(item, "caption", None)
                action = getattr(item, "action", None)
                event["choices"].append({
                    "id": new_id("choice"),
                    "caption": str(caption or "Choice"),
                    "condition": "",
                    "target": "",
                    "script": "",
                    "runtime_action": serialize_action(action),
                })
            controller["events"].append(event)
            if not controller.get("active_event_id"):
                controller["active_event_id"] = event.get("id")
            if not controller.get("selected_event_id"):
                controller["selected_event_id"] = event.get("id")

        state.setdefault("dialogue_controllers", []).append(controller)
        scene = dialogue_scene(state)
        if scene is None:
            scene = new_scene("Dialogue", ["characters", "dialogue"])
            state.setdefault("scenes", []).append(scene)
        scene.setdefault("nodes", []).append(dialogue_controller_node(scene, controller))
        return state

    def dialogue_events():
        controller = selected_dialogue_controller()
        return controller.get("events", []) if controller else []

    def selected_dialogue_event():
        state = resolve_frame()
        item, _parent_id, kind = find_state_item(state, selected_item_id)
        if kind == "dialogue_event":
            return item
        controller = selected_dialogue_controller(state)
        if controller is None:
            return None
        selected_id = controller.get("selected_event_id") or controller.get("active_event_id")
        for event in controller.get("events", []):
            if event.get("id") == selected_id:
                return event
        return controller.get("events", [None])[0] if controller.get("events") else None

    def select_dialogue_event(event_id):
        controller = selected_dialogue_controller()
        if controller is not None:
            set_item_value(controller.get("id"), "selected_event_id", event_id, "Select dialogue event")
        select_item(event_id, "dialogue_event")

    def set_active_dialogue_event(event_id):
        controller = selected_dialogue_controller()
        if controller is None:
            return
        set_item_value(controller.get("id"), "active_event_id", event_id, "Set current dialogue event")
        set_item_value(controller.get("id"), "selected_event_id", event_id, "Select dialogue event")
        select_item(event_id, "dialogue_event")

    def add_dialogue_event(event_type="say"):
        if event_type not in DIALOGUE_EVENT_TYPES:
            event_type = "say"
        controller = ensure_dialogue_controller()
        if controller is None:
            return
        event = new_dialogue_event(event_type)
        add_change(controller.get("id"), "events", event, label="Add {} event".format(event_type))
        set_item_value(controller.get("id"), "selected_event_id", event.get("id"), "Select dialogue event")
        set_item_value(controller.get("id"), "active_event_id", event.get("id"), "Set current dialogue event")
        select_item(event.get("id"), "dialogue_event")

    def add_choice_option(event_id=None):
        event_id = event_id or (selected_dialogue_event() or {}).get("id")
        event, _parent_id, kind = find_state_item(resolve_frame(), event_id)
        if event is None or kind != "dialogue_event" or event.get("type") != "choice":
            return
        choice = {
            "id": new_id("choice"),
            "caption": "Choice",
            "condition": "",
            "target": "",
            "script": "",
        }
        add_change(event_id, "choices", choice, label="Add choice")
        select_item(choice.get("id"), "dialogue_choice")

    def dialogue_source(controller=None):
        controller = controller or selected_dialogue_controller()
        if controller is None:
            return "# No dialogue controller in this frame."
        lines = []
        for event in controller.get("events", []):
            event_type = event.get("type")
            if event_type == "say":
                speaker = safe_identifier(event.get("speaker"), "speaker")
                lines.append("{} {}".format(speaker, repr(str(event.get("text", "")))))
            elif event_type == "narration":
                lines.append(repr(str(event.get("text", ""))))
            elif event_type == "script":
                script = str(event.get("script", "")).strip()
                lines.append("$ {}".format(script or "pass"))
            elif event_type == "jump":
                lines.append("jump {}".format(safe_identifier(event.get("target"), "target_label")))
            elif event_type == "call":
                lines.append("call {}".format(safe_identifier(event.get("target"), "target_label")))
            elif event_type == "return":
                lines.append("return")
            elif event_type == "condition":
                lines.append("if {}:".format(event.get("condition") or "True"))
                lines.append("    pass")
            elif event_type == "choice":
                lines.append("menu:")
                for choice in event.get("choices", []):
                    caption = repr(str(choice.get("caption", "Choice")))
                    condition = str(choice.get("condition", "")).strip()
                    suffix = " if {}".format(condition) if condition else ""
                    lines.append('    {}{}:'.format(caption, suffix))
                    script = str(choice.get("script", "")).strip()
                    target = str(choice.get("target", "")).strip()
                    if script:
                        lines.append("        $ {}".format(script))
                    if target:
                        lines.append("        jump {}".format(safe_identifier(target, "target_label")))
                    if not script and not target:
                        lines.append("        pass")
        return "\n".join(lines)
