# UI screen/widget inspection and structured action capture.

init -910 python in live_studio:
    try:
        from renpy.display.screen import ScreenDisplayable
    except Exception:
        ScreenDisplayable = ()

    KNOWN_ACTION_TYPES = {
        "Jump", "Call", "Return", "Show", "Hide", "ToggleScreen", "ShowMenu",
        "SetVariable", "SetField", "ToggleVariable", "ToggleField", "Play",
        "Stop", "Queue", "If", "Confirm", "NullAction", "Function",
    }

    def screen_name_from_displayable(displayable, fallback="screen"):
        for attribute in ("screen_name", "name", "tag"):
            try:
                value = getattr(displayable, attribute, None)
                if value:
                    if isinstance(value, (tuple, list)):
                        return str(value[0])
                    return str(value)
            except Exception:
                pass
        return str(fallback)

    def serialize_action(action):
        if action is None:
            return None
        if isinstance(action, (list, tuple)):
            return {
                "type": "multiple",
                "editable": True,
                "actions": [item for item in (serialize_action(child) for child in action) if item],
            }
        action_type = action.__class__.__name__
        data = {}
        try:
            for key, value in vars(action).items():
                if key.startswith("_"):
                    continue
                data[key] = json_safe(value)
        except Exception:
            pass
        return {
            "type": action_type,
            "editable": action_type in KNOWN_ACTION_TYPES,
            "data": data,
            "repr": repr(action),
        }

    def displayable_actions(displayable):
        result = []
        for attribute in ("action", "clicked", "alternate", "hovered", "unhovered"):
            try:
                value = getattr(displayable, attribute, None)
            except Exception:
                value = None
            serialized = serialize_action(value)
            if serialized:
                serialized["slot"] = attribute
                result.append(serialized)
        return result

    def displayable_children(displayable):
        result = []
        visit = getattr(displayable, "visit", None)
        if callable(visit):
            try:
                result = list(visit() or [])
            except Exception:
                result = []
        if not result:
            child = getattr(displayable, "child", None)
            if child is not None:
                result = [child]
        unique = []
        seen = set()
        for child in result:
            if child is None or id(child) in seen:
                continue
            seen.add(id(child))
            unique.append(child)
        return unique

    def ui_widget_reverse_map(screen_displayable):
        result = {}
        for attribute in ("widgets", "base_widgets"):
            values = getattr(screen_displayable, attribute, None)
            if not isinstance(values, dict):
                continue
            for widget_id, displayable in values.items():
                if displayable is not None:
                    result[id(displayable)] = str(widget_id)
        return result

    def ui_node_type(displayable):
        class_name = displayable.__class__.__name__
        lowered = class_name.lower()
        if "textbutton" in lowered:
            return "textbutton"
        if "imagebutton" in lowered:
            return "imagebutton"
        if "button" in lowered:
            return "button"
        if lowered == "text" or "text" in lowered:
            return "text"
        if "window" in lowered or "frame" in lowered:
            return "frame"
        if "viewport" in lowered:
            return "viewport"
        if "grid" in lowered:
            return "grid"
        if "vbox" in lowered:
            return "vbox"
        if "hbox" in lowered:
            return "hbox"
        if "fixed" in lowered or "multibox" in lowered:
            return "fixed"
        if "bar" in lowered:
            return "bar"
        if "input" in lowered:
            return "input"
        if "drag" in lowered:
            return "drag"
        if "transform" in lowered:
            return "transform"
        if "image" in lowered:
            return "image"
        return class_name

    def safe_widget_properties(widget_id, screen_name, layer):
        if not widget_id:
            return {}
        try:
            values = renpy.get_displayable_properties(widget_id, screen=screen_name, layer=layer)
            return json_safe(values or {})
        except Exception:
            return {}

    def capture_ui_node(displayable, reverse_map, screen_name, layer, depth, counter, visited):
        if displayable is None or id(displayable) in visited:
            return None
        if depth > UI_CAPTURE_MAX_DEPTH or counter[0] >= UI_CAPTURE_MAX_NODES:
            return None
        visited.add(id(displayable))
        counter[0] += 1

        widget_id = reverse_map.get(id(displayable))
        node_type = ui_node_type(displayable)
        name = widget_id or "{} {}".format(node_type, counter[0])
        node = new_ui_node(name, node_type, widget_id)
        node["source"] = {
            "screen": screen_name,
            "layer": layer,
            "runtime_type": displayable.__class__.__name__,
        }
        node["properties"] = safe_widget_properties(widget_id, screen_name, layer)
        placement = placement_properties(displayable)
        node["resolved_properties"] = placement
        width, height = displayable_size(displayable)
        node["bounds"] = calculate_bounds(placement, width, height)
        node["actions"] = displayable_actions(displayable)
        if not widget_id:
            node["editability"] = "inspect"
        elif node["actions"] and not all(action.get("editable") for action in node["actions"]):
            node["editability"] = "limited"
        else:
            node["editability"] = "editable"

        for child in displayable_children(displayable):
            child_node = capture_ui_node(child, reverse_map, screen_name, layer, depth + 1, counter, visited)
            if child_node is not None:
                node["children"].append(child_node)
        return node

    def capture_ui_state():
        result = []
        scene_list = scene_lists()
        if scene_list is None or not ScreenDisplayable:
            return result

        for layer in UI_LAYERS:
            if layer not in config.layers:
                continue
            try:
                entries = list(scene_list.layers[layer])
            except Exception:
                entries = []
            for index, entry in enumerate(entries):
                tag = entry_tag(entry)
                if not tag:
                    continue
                try:
                    displayable = scene_list.get_displayable_by_tag(layer, tag)
                except Exception:
                    displayable = None
                if not isinstance(displayable, ScreenDisplayable):
                    continue

                screen_name = screen_name_from_displayable(displayable, tag)
                screen = new_ui_screen(screen_name, layer, tag, entry_zorder(entry, index))
                screen["managed"] = False
                screen["source"] = {
                    "screen": screen_name,
                    "layer": layer,
                    "tag": tag,
                    "captured_by": "runtime",
                }
                reverse_map = ui_widget_reverse_map(displayable)
                root = getattr(displayable, "child", None)
                counter = [0]
                root_node = capture_ui_node(root, reverse_map, screen_name, layer, 0, counter, set())
                if root_node is not None:
                    screen["nodes"].append(root_node)
                screen["editability"] = "editable" if reverse_map else "inspect"
                result.append(screen)
                runtime.setdefault("screen_displayables", {})[screen["id"]] = displayable

        return result

    def ui_screen_by_name(state, name):
        for screen in state.get("ui_screens", []):
            if screen.get("name") == name or screen.get("tag") == name:
                return screen
        return None

    def ensure_editor_ui_screen(screen_id=None):
        state = resolve_frame()
        screen = None
        if screen_id:
            screen, _parent, kind = find_state_item(state, screen_id)
            if kind != "ui_screen":
                screen = None
        if screen is None:
            screen = ui_screen_by_name(state, "live_studio_ui")
        if screen is None:
            created = new_ui_screen("live_studio_ui", "screens", "live_studio_ui", 50)
            created["managed"] = True
            created["editability"] = "editable"
            created["source"] = {"created_by": "live_studio"}
            add_change(None, None, created, root_collection="ui_screens", label="Add UI screen")
            state = resolve_frame()
            screen = next((item for item in state.get("ui_screens", []) if item.get("id") == created.get("id")), None)
        return screen

    def add_ui_text(screen_id=None):
        screen = ensure_editor_ui_screen(screen_id)
        if screen is None:
            return
        node = new_ui_node("Text", "text", safe_identifier(new_id("text"), "text"))
        node["source"] = {"created_by": "live_studio", "screen": screen.get("name")}
        node["properties"] = {
            "text": "New text",
            "xpos": 0.5,
            "ypos": 0.5,
            "xanchor": 0.5,
            "yanchor": 0.5,
            "xsize": 400,
            "ysize": 60,
            "size": 30,
            "color": "#ffffff",
            "alpha": 1.0,
        }
        node["resolved_properties"] = clone(node["properties"])
        node["bounds"] = {"x": config.screen_width * 0.4, "y": config.screen_height * 0.47, "width": 400, "height": 60}
        add_change(screen.get("id"), "nodes", node, label="Add UI text")
        select_item(node.get("id"), "ui_node")

    def add_ui_button(screen_id=None):
        screen = ensure_editor_ui_screen(screen_id)
        if screen is None:
            return
        node = new_ui_node("Button", "textbutton", safe_identifier(new_id("button"), "button"))
        node["source"] = {"created_by": "live_studio", "screen": screen.get("name")}
        node["properties"] = {
            "text": "Button",
            "xpos": 0.5,
            "ypos": 0.5,
            "xanchor": 0.5,
            "yanchor": 0.5,
            "xsize": 260,
            "ysize": 70,
            "alpha": 1.0,
        }
        node["actions"] = [{
            "slot": "action",
            "type": "jump_frame",
            "editable": True,
            "data": {"target_frame_id": ""},
            "repr": "",
        }]
        node["resolved_properties"] = clone(node["properties"])
        node["bounds"] = {"x": config.screen_width * 0.43, "y": config.screen_height * 0.46, "width": 260, "height": 70}
        add_change(screen.get("id"), "nodes", node, label="Add UI button")
        select_item(node.get("id"), "ui_node")

    def action_summary(action):
        if not action:
            return "No action"
        action_type = action.get("type", "Action")
        data = action.get("data", {})
        if action_type == "jump_frame":
            return "Jump to frame: {}".format(data.get("target_frame_id") or "Not set")
        if action_type == "multiple":
            return "Multiple actions ({})".format(len(action.get("actions", [])))
        return action_type
