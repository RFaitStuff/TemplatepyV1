# UI screen/widget inspection, managed UI creation, and structured actions.

init -960 python in live_studio:
    try:
        from renpy.display.screen import ScreenDisplayable
    except Exception:
        ScreenDisplayable = ()

    KNOWN_RENPY_ACTIONS = {
        "Jump", "Call", "Return", "Show", "Hide", "ToggleScreen", "ShowMenu",
        "SetVariable", "SetField", "ToggleVariable", "ToggleField", "Play",
        "Stop", "Queue", "If", "Confirm", "NullAction", "Function",
    }

    def screen_name_from_displayable(displayable, fallback="screen"):
        value = getattr(displayable, "screen_name", None)
        if value:
            if isinstance(value, (tuple, list)):
                return " ".join(str(part) for part in value)
            return str(value)
        value = getattr(displayable, "name", None)
        return str(value or fallback)

    def _action_data(action):
        result = {}
        try:
            for key, value in vars(action).items():
                if key.startswith("_"):
                    continue
                result[key] = json_safe(value)
        except Exception:
            pass
        return result

    def serialize_action(action):
        if action is None:
            return None
        if isinstance(action, (list, tuple)):
            return {
                "id": new_id("action"),
                "type": "multiple",
                "editable": True,
                "actions": [item for item in (serialize_action(child) for child in action) if item],
                "source": {"captured_by": "runtime"},
            }
        action_type = action.__class__.__name__
        data = _action_data(action)
        internal = {
            "id": new_id("action"),
            "type": action_type,
            "editable": action_type in KNOWN_RENPY_ACTIONS,
            "data": data,
            "repr": repr(action),
            "source": {"captured_by": "runtime", "runtime_type": action_type},
        }
        # Normalize common Ren'Py actions into Live Studio action types when
        # their fields can be recovered safely.
        if action_type == "Jump":
            internal.update({"type": "jump_label", "target": data.get("label") or data.get("target") or "", "editable": True})
        elif action_type == "Call":
            internal.update({"type": "call_label", "target": data.get("label") or data.get("target") or "", "editable": True})
        elif action_type == "Return":
            internal.update({"type": "return", "editable": True})
        elif action_type == "Show":
            internal.update({"type": "show_screen", "screen": data.get("screen") or data.get("name") or "", "editable": True})
        elif action_type == "Hide":
            internal.update({"type": "hide_screen", "screen": data.get("screen") or data.get("name") or "", "editable": True})
        elif action_type == "SetVariable":
            internal.update({"type": "set_variable", "variable": data.get("variable") or data.get("name") or "", "value": data.get("value", ""), "editable": True})
        return internal

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


    def collect_render_bounds(displayable):
        """Maps runtime displayables to absolute bounds from Ren'Py's render tree.

        Placement properties alone are relative to each layout container and
        cannot locate VBox/HBox children. The Render tree records the actual
        blit offsets after layout, so this provides the visual bounds used by
        the hierarchy and hit-testing overlay.
        """
        result = {}
        try:
            root_render = renpy.render(displayable, config.screen_width, config.screen_height, 0.0, 0.0)
        except Exception as exc:
            log_diagnostic("warning", "Could not inspect screen render tree", repr(exc))
            return result

        def add_bounds(runtime_displayable, x, y, width, height):
            key = id(runtime_displayable)
            value = {"x": float(x), "y": float(y), "width": max(1.0, float(width)), "height": max(1.0, float(height))}
            old = result.get(key)
            if old is None:
                result[key] = value
            else:
                left = min(old["x"], value["x"])
                top = min(old["y"], value["y"])
                right = max(old["x"] + old["width"], value["x"] + value["width"])
                bottom = max(old["y"] + old["height"], value["y"] + value["height"])
                result[key] = {"x": left, "y": top, "width": right - left, "height": bottom - top}

        def walk(render, offset_x, offset_y, ancestors):
            identity = id(render)
            # Render trees may be DAGs: the same cached render can be blitted at
            # multiple positions. Only reject a true cycle in the current path.
            if identity in ancestors:
                return
            next_ancestors = set(ancestors)
            next_ancestors.add(identity)
            try:
                width, height = render.get_size()
            except Exception:
                width, height = (1, 1)
            for runtime_displayable in getattr(render, "render_of", []) or []:
                add_bounds(runtime_displayable, offset_x, offset_y, width, height)
            for child_entry in getattr(render, "children", []) or []:
                try:
                    child, child_x, child_y = child_entry[0], child_entry[1], child_entry[2]
                except Exception:
                    continue
                if hasattr(child, "children") and hasattr(child, "render_of"):
                    walk(child, offset_x + float(child_x), offset_y + float(child_y), next_ancestors)
        walk(root_render, 0.0, 0.0, set())
        return result

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
        if "imagebutton" in lowered:
            return "imagebutton"
        if "button" in lowered:
            return "button"
        if lowered == "text" or lowered.endswith("text"):
            return "text"
        if "window" in lowered or "frame" in lowered:
            return "frame"
        if "viewport" in lowered:
            return "viewport"
        if "vpgrid" in lowered:
            return "vpgrid"
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
        return "custom"

    def safe_widget_properties(widget_id, screen_name, layer):
        if not widget_id:
            return {}
        try:
            values = renpy.get_displayable_properties(widget_id, screen=screen_name, layer=layer)
            return json_safe(values or {})
        except Exception:
            return {}

    def _displayable_content_properties(displayable, node_type):
        result = {}
        if node_type == "text":
            text_value = getattr(displayable, "text", None)
            if text_value is None:
                text_value = getattr(displayable, "text_parameter", None)
            if text_value is not None:
                result["text"] = json_safe(text_value)
        elif node_type == "button":
            result.setdefault("text", "Button")
        elif node_type == "imagebutton":
            for state_name in ("idle", "hover", "insensitive", "selected_idle", "selected_hover"):
                value = getattr(displayable, state_name, None)
                if value is None:
                    continue
                image_name = displayable_image_name(value)
                if image_name:
                    result[state_name] = image_name
        image_name = displayable_image_name(displayable)
        if image_name and node_type == "image":
            result["image"] = image_name
        return result

    def capture_ui_node(displayable, reverse_map, render_bounds, screen_name, layer, depth, counter, ancestors):
        if displayable is None or id(displayable) in ancestors:
            return None
        if depth > UI_CAPTURE_MAX_DEPTH or counter[0] >= UI_CAPTURE_MAX_NODES:
            return None
        next_ancestors = set(ancestors)
        next_ancestors.add(id(displayable))
        counter[0] += 1

        widget_id = reverse_map.get(id(displayable))
        node_type = ui_node_type(displayable)
        name = widget_id or "{} {}".format(node_type.title(), counter[0])
        node = new_ui_node(name, node_type, widget_id)
        node["source"] = {
            "screen": screen_name,
            "layer": layer,
            "runtime_type": displayable.__class__.__name__,
            "captured_by": "runtime",
        }
        widget_properties = safe_widget_properties(widget_id, screen_name, layer)
        placement = placement_properties(displayable)
        properties = clone(widget_properties)
        for key, value in placement.items():
            properties.setdefault(key, value)
        properties.update({key: value for key, value in _displayable_content_properties(displayable, node_type).items() if key not in properties})
        node["properties"] = properties
        node["resolved_properties"] = clone(placement)
        measured = render_bounds.get(id(displayable))
        if measured is not None:
            node["bounds"] = clone(measured)
            width, height = measured.get("width", 1), measured.get("height", 1)
        else:
            width, height = displayable_size(displayable)
            # Fallback for displayables absent from the render tree.
            node["bounds"] = calculate_bounds(placement, width, height, apply_zoom=False)
        node["actions"] = displayable_actions(displayable)
        if not widget_id:
            node["editability"] = "inspect"
        elif node["actions"] and not all(action.get("editable") for action in node["actions"]):
            node["editability"] = "limited"
        else:
            node["editability"] = "editable"
        runtime.setdefault("ui_displayables", {})[node["id"]] = displayable
        runtime.setdefault("widget_displayables", {})[node["id"]] = displayable

        for child in displayable_children(displayable):
            child_node = capture_ui_node(child, reverse_map, render_bounds, screen_name, layer, depth + 1, counter, next_ancestors)
            if child_node is not None:
                node["children"].append(child_node)
        return node

    def _screen_role(name):
        lowered = str(name or "").lower()
        if lowered == "say" or "dialogue" in lowered:
            return "say"
        if lowered == "choice" or "choice" in lowered:
            return "choice"
        if "quick" in lowered:
            return "quick_menu"
        if "hud" in lowered:
            return "hud"
        return "screen"


    def screen_runtime_key(screen_or_name, tag=None, layer=None):
        if isinstance(screen_or_name, dict):
            screen = screen_or_name
            name = screen.get("name") or screen.get("tag") or "screen"
            tag = screen.get("tag") or name
            layer = screen.get("layer") or "screens"
        else:
            name = screen_or_name or tag or "screen"
            tag = tag or name
            layer = layer or "screens"
        return (str(name), str(tag), str(layer))

    def runtime_screen_root(screen):
        if not screen:
            return None
        direct = runtime.get("screen_roots", {}).get(screen.get("id"))
        if direct is not None:
            return direct
        entry = runtime.get("screen_index", {}).get(screen_runtime_key(screen))
        if entry is not None:
            return entry.get("root")
        # Tags can be altered by transient/say screens. A same-name/layer
        # fallback keeps saved projects previewable in a later SDK run.
        for key, value in runtime.get("screen_index", {}).items():
            if key[0] == str(screen.get("name")) and key[2] == str(screen.get("layer") or "screens"):
                return value.get("root")
        return None

    def capture_ui_state():
        result = []
        scene_list = scene_lists()
        runtime["ui_displayables"] = {}
        runtime["screen_roots"] = {}
        runtime["screen_displayables"] = {}
        runtime["screen_index"] = {}
        if scene_list is None or not ScreenDisplayable:
            log_diagnostic("warning", "ScreenDisplayable was unavailable; UI capture was skipped.")
            return result

        ordered_layers = list(UI_LAYERS)
        for layer in runtime_layer_names(scene_list):
            if layer not in ordered_layers:
                ordered_layers.append(layer)
        for layer in ordered_layers:
            try:
                entries = list(scene_list.layers.get(layer, [])) if isinstance(scene_list.layers, dict) else list(scene_list.layers[layer])
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
                screen["role"] = _screen_role(screen_name)
                location = getattr(getattr(displayable, "screen", None), "location", None)
                screen["source"] = {
                    "screen": screen_name,
                    "layer": layer,
                    "tag": tag,
                    "captured_by": "runtime",
                    "location": json_safe(location),
                }
                reverse_map = ui_widget_reverse_map(displayable)
                render_bounds = collect_render_bounds(displayable)
                root = getattr(displayable, "child", None)
                counter = [0]
                root_node = capture_ui_node(root, reverse_map, render_bounds, screen_name, layer, 0, counter, set())
                if root_node is not None:
                    screen["nodes"].append(root_node)
                screen["editability"] = "limited" if reverse_map else "inspect"
                result.append(screen)
                runtime["screen_displayables"][screen["id"]] = displayable
                runtime["screen_roots"][screen["id"]] = root
                runtime["screen_index"][screen_runtime_key(screen)] = {
                    "root": root,
                    "displayable": displayable,
                    "screen_id": screen.get("id"),
                }
        return result

    def ui_screen_by_name(state, name):
        for screen in state.get("ui_screens", []):
            if screen.get("name") == name or screen.get("tag") == name:
                return screen
        return None


    def create_editor_ui_screen(name=None):
        state = resolve_frame()
        base = safe_identifier(name or "live_studio_ui", "live_studio_ui")
        existing = set(screen.get("name") for screen in state.get("ui_screens", []))
        final_name = base
        index = 2
        while final_name in existing:
            final_name = "{}_{}".format(base, index)
            index += 1
        created = new_ui_screen(final_name, "screens", final_name, 50)
        created["managed"] = True
        created["editability"] = "editable"
        created["source"] = {"created_by": "live_studio"}
        root = new_ui_node("Root", "fixed", "root")
        root["properties"] = {"xfill": True, "yfill": True}
        root["source"] = {"created_by": "live_studio", "screen": final_name}
        created["nodes"].append(root)
        add_change(None, None, created, root_collection="ui_screens", label="Add UI screen")
        select_item(created.get("id"), "ui_screen")
        set_tree_tab("UI")
        return created

    def _unique_managed_screen_name(base_name):
        base = safe_identifier(base_name, "live_studio_screen")
        existing = set()
        for screen in resolve_frame().get("ui_screens", []):
            existing.add(str(screen.get("name") or ""))
            existing.add(str(screen.get("tag") or ""))
        candidate = base
        index = 2
        while candidate in existing:
            candidate = "{}_{}".format(base, index)
            index += 1
        return candidate

    def _managed_screen_base(name, role="screen", zorder=50):
        screen = new_ui_screen(name, "screens", name, zorder)
        screen["managed"] = True
        screen["editability"] = "editable"
        screen["role"] = role
        screen["source"] = {"created_by": "live_studio"}
        return screen

    def create_say_ui_template(name=None):
        """Creates an editor-owned say screen wired to the Dialogue object."""
        name = _unique_managed_screen_name(name or "live_studio_say")
        screen = _managed_screen_base(name, "say", 80)

        root = new_ui_node("Say Root", "fixed", "say_root")
        root["properties"] = {"xfill": True, "yfill": True}

        window = new_ui_node("Dialogue Window", "window", "window")
        window["properties"] = {
            "xalign": 0.5, "yalign": 1.0, "xsize": int(config.screen_width * 0.92),
            "ysize": int(config.screen_height * 0.25), "background": "#101522e8",
            "padding": 28, "alpha": 1.0,
        }

        content = new_ui_node("Dialogue Content", "vbox", "say_content")
        content["properties"] = {"xfill": True, "yfill": True, "spacing": 10}

        who = new_ui_node("Speaker", "text", "who")
        who["binding"] = "who"
        who["properties"] = {
            "text": "Character", "xalign": 0.0, "size": 30,
            "color": "#8ecbff", "bold": True, "alpha": 1.0,
        }

        what = new_ui_node("Dialogue Text", "text", "what")
        what["binding"] = "what"
        what["properties"] = {
            "text": "Dialogue appears here.", "xalign": 0.0, "size": 28,
            "color": "#ffffff", "alpha": 1.0,
        }

        content["children"] = [who, what]
        window["children"] = [content]
        root["children"] = [window]
        for node, _parent, _depth in walk_nodes([root]):
            node["editability"] = "editable"
            node["source"] = {"created_by": "live_studio", "screen": name}
        screen["nodes"] = [root]

        add_change(None, None, screen, root_collection="ui_screens", label="Add Say UI template")
        controller = ensure_dialogue_controller()
        if controller is not None:
            set_item_value(controller.get("id"), "say_screen", screen.get("id"), "Use Say UI template")
        select_item(screen.get("id"), "ui_screen")
        set_tree_tab("UI")
        return screen

    def create_choice_ui_template(name=None):
        """Creates an editor-owned choice screen wired to the Dialogue object."""
        name = _unique_managed_screen_name(name or "live_studio_choice")
        screen = _managed_screen_base(name, "choice", 90)

        root = new_ui_node("Choice Root", "fixed", "choice_root")
        root["properties"] = {"xfill": True, "yfill": True}

        choices = new_ui_node("Choice List", "vbox", "choice_list")
        choices["properties"] = {
            "xalign": 0.5, "yalign": 0.5, "xsize": min(760, int(config.screen_width * 0.72)),
            "spacing": 16, "alpha": 1.0,
        }

        button = new_ui_node("Choice Button", "button", "choice_button")
        button["properties"] = {
            "text": "Choice", "xfill": True, "ysize": 76,
            "background": "#17253ee8", "hover_background": "#2d5484f2",
            "color": "#ffffff", "size": 28, "text_align": 0.5,
            "padding": 18, "alpha": 1.0,
        }
        choices["children"] = [button]
        root["children"] = [choices]
        for node, _parent, _depth in walk_nodes([root]):
            node["editability"] = "editable"
            node["source"] = {"created_by": "live_studio", "screen": name}
        screen["nodes"] = [root]

        add_change(None, None, screen, root_collection="ui_screens", label="Add Choice UI template")
        controller = ensure_dialogue_controller()
        if controller is not None:
            set_item_value(controller.get("id"), "choice_screen", screen.get("id"), "Use Choice UI template")
        select_item(screen.get("id"), "ui_screen")
        set_tree_tab("UI")
        return screen

    def ensure_editor_ui_screen(screen_id=None, name="live_studio_ui"):
        state = resolve_frame()
        screen = None
        if screen_id:
            screen, _parent, kind = find_state_item(state, screen_id)
            if kind != "ui_screen":
                screen = None
        if screen is None:
            selected, _parent, kind = selected_item(state)
            if kind == "ui_screen" and selected.get("managed"):
                screen = selected
        if screen is None:
            screen = ui_screen_by_name(state, name)
        if screen is None or not screen.get("managed"):
            created = new_ui_screen(name, "screens", name, 50)
            created["managed"] = True
            created["editability"] = "editable"
            created["source"] = {"created_by": "live_studio"}
            root = new_ui_node("Root", "fixed", "root")
            root["properties"] = {"xfill": True, "yfill": True}
            root["source"] = {"created_by": "live_studio", "screen": name}
            created["nodes"].append(root)
            add_change(None, None, created, root_collection="ui_screens", label="Add UI screen")
            screen = next((item for item in resolve_frame().get("ui_screens", []) if item.get("id") == created.get("id")), created)
        return screen

    def _managed_parent(screen_id=None, parent_id=None):
        screen = ensure_editor_ui_screen(screen_id)
        if screen is None:
            return None, None
        if parent_id:
            parent, _grandparent, kind = find_state_item(resolve_frame(), parent_id)
            if kind == "ui_node":
                return screen, parent
        selected, _parent, kind = selected_item()
        if kind == "ui_node" and selected.get("source", {}).get("screen") == screen.get("name"):
            return screen, selected
        root = screen.get("nodes", [None])[0] if screen.get("nodes") else None
        return screen, root

    def _add_managed_node(node, screen_id=None, parent_id=None, label="Add UI item"):
        screen, parent = _managed_parent(screen_id, parent_id)
        if screen is None:
            return None
        node["source"] = {"created_by": "live_studio", "screen": screen.get("name")}
        node["editability"] = "editable"
        if parent is not None:
            parent_type = str(parent.get("type") or "fixed").lower()
            props = node.setdefault("properties", {})
            if parent_type == "vbox":
                alignment = props.get("xalign", props.get("xpos", 0.5))
                props.pop("xpos", None)
                props.pop("xanchor", None)
                props.pop("ypos", None)
                props.pop("yanchor", None)
                props["xalign"] = alignment
            elif parent_type == "hbox":
                alignment = props.get("yalign", props.get("ypos", 0.5))
                props.pop("xpos", None)
                props.pop("xanchor", None)
                props.pop("ypos", None)
                props.pop("yanchor", None)
                props["yalign"] = alignment
            elif parent_type in ("grid", "vpgrid"):
                for key in ("xpos", "ypos", "xanchor", "yanchor"):
                    props.pop(key, None)
        if parent is not None and parent.get("type") in ("fixed", "frame", "vbox", "hbox", "grid", "viewport", "vpgrid"):
            add_change(parent.get("id"), "children", node, label=label)
        else:
            add_change(screen.get("id"), "nodes", node, label=label)
        select_item(node.get("id"), "ui_node")
        return node

    def add_ui_text(screen_id=None, parent_id=None):
        node = new_ui_node("Text", "text", safe_identifier(new_id("text"), "text"))
        node["properties"] = {
            "text": "New text", "xpos": 0.5, "ypos": 0.5,
            "xanchor": 0.5, "yanchor": 0.5, "xsize": 400, "ysize": 60,
            "size": 30, "color": "#ffffff", "text_align": 0.5, "alpha": 1.0,
        }
        node["bounds"] = {"x": config.screen_width * 0.5 - 200, "y": config.screen_height * 0.5 - 30, "width": 400, "height": 60}
        return _add_managed_node(node, screen_id, parent_id, "Add UI text")

    def add_ui_button(screen_id=None, parent_id=None):
        node = new_ui_node("Button", "button", safe_identifier(new_id("button"), "button"))
        node["properties"] = {
            "text": "Button", "xpos": 0.5, "ypos": 0.5,
            "xanchor": 0.5, "yanchor": 0.5, "xsize": 260, "ysize": 70,
            "background": "#20344dcc", "hover_background": "#31537add",
            "color": "#ffffff", "alpha": 1.0,
        }
        node["actions"] = [new_action("jump_frame")]
        node["bounds"] = {"x": config.screen_width * 0.5 - 130, "y": config.screen_height * 0.5 - 35, "width": 260, "height": 70}
        return _add_managed_node(node, screen_id, parent_id, "Add UI button")

    def add_ui_image_button(image_name=None, screen_id=None, parent_id=None):
        image_name = str(image_name or "")
        node = new_ui_node("Image Button", "imagebutton", safe_identifier(new_id("imagebutton"), "imagebutton"))
        node["properties"] = {
            "idle": image_name, "hover": image_name,
            "xpos": 0.5, "ypos": 0.5, "xanchor": 0.5, "yanchor": 0.5,
            "xsize": 260, "ysize": 90, "alpha": 1.0,
        }
        node["actions"] = [new_action("jump_frame")]
        node["bounds"] = {"x": config.screen_width * 0.5 - 130, "y": config.screen_height * 0.5 - 45, "width": 260, "height": 90}
        return _add_managed_node(node, screen_id, parent_id, "Add UI image button")

    def add_ui_image(image_name=None, screen_id=None, parent_id=None):
        image_name = str(image_name or "")
        node = new_ui_node(image_name or "Image", "image", safe_identifier(new_id("image"), "image"))
        node["properties"] = {
            "image": image_name, "xpos": 0.5, "ypos": 0.5,
            "xanchor": 0.5, "yanchor": 0.5, "xsize": 300, "ysize": 300,
            "alpha": 1.0,
        }
        node["bounds"] = {"x": config.screen_width * 0.5 - 150, "y": config.screen_height * 0.5 - 150, "width": 300, "height": 300}
        return _add_managed_node(node, screen_id, parent_id, "Add UI image")

    def add_ui_container(container_type="fixed", screen_id=None, parent_id=None):
        container_type = container_type if container_type in ("fixed", "frame", "vbox", "hbox", "grid", "viewport") else "fixed"
        node = new_ui_node(container_type.title(), container_type, safe_identifier(new_id(container_type), container_type))
        node["properties"] = {
            "xpos": 0.5, "ypos": 0.5, "xanchor": 0.5, "yanchor": 0.5,
            "xsize": 500, "ysize": 300, "spacing": 10,
            "background": "#152033aa" if container_type == "frame" else None,
            "alpha": 1.0,
        }
        node["bounds"] = {"x": config.screen_width * 0.5 - 250, "y": config.screen_height * 0.5 - 150, "width": 500, "height": 300}
        return _add_managed_node(node, screen_id, parent_id, "Add UI container")

    def _convert_node_to_managed(node, screen_name, counter, used_widget_ids=None):
        used_widget_ids = used_widget_ids if used_widget_ids is not None else set()
        converted = clone(node)
        converted["id"] = new_id("ui")
        raw_widget_id = converted.get("widget_id") or converted.get("type") or "widget"
        base_widget_id = safe_identifier(raw_widget_id, "widget")
        widget_id = base_widget_id
        suffix = 2
        while widget_id in used_widget_ids:
            widget_id = "{}_{}".format(base_widget_id, suffix)
            suffix += 1
        used_widget_ids.add(widget_id)
        counter[0] += 1
        converted["widget_id"] = widget_id
        supported_types = {"fixed", "frame", "window", "vbox", "hbox", "grid", "viewport", "vpgrid", "text", "button", "textbutton", "image", "add", "imagebutton"}
        converted["editability"] = "editable" if str(converted.get("type") or "").lower() in supported_types else "limited"
        converted["source"] = {"created_by": "live_studio", "converted_from": node.get("source", {}), "screen": screen_name}
        converted["actions"] = [clone(action) for action in converted.get("actions", []) if action.get("editable")]
        converted["children"] = [_convert_node_to_managed(child, screen_name, counter, used_widget_ids) for child in converted.get("children", [])]
        return converted

    def convert_screen_to_managed(screen_id):
        screen, _parent, kind = find_state_item(resolve_frame(), screen_id)
        if kind != "ui_screen" or screen.get("managed"):
            return screen
        name = safe_identifier("{}_managed".format(screen.get("name", "screen")), "managed_screen")
        converted = new_ui_screen(name, "screens", name, screen.get("zorder", 0))
        converted["managed"] = True
        converted["editability"] = "editable"
        converted["role"] = screen.get("role", "screen")
        converted["source"] = {"created_by": "live_studio", "converted_from": clone(screen.get("source", {}))}
        counter = [0]
        used_widget_ids = set()
        converted["nodes"] = [_convert_node_to_managed(node, name, counter, used_widget_ids) for node in screen.get("nodes", [])]
        add_change(None, None, converted, root_collection="ui_screens", label="Convert screen to managed")
        select_item(converted.get("id"), "ui_screen")
        return converted

    def primary_action(node):
        actions = node.get("actions", []) if node else []
        return actions[0] if actions else None

    def set_node_action_type(node_id, action_type):
        node, _parent, kind = find_state_item(resolve_frame(), node_id)
        if kind not in ("ui_node", "scene_node"):
            return
        actions = clone(node.get("actions", []))
        if actions:
            action = actions[0]
            replacement = new_action(action_type)
            replacement["id"] = action.get("id", replacement["id"])
            actions[0] = replacement
        else:
            actions = [new_action(action_type)]
        set_item_value(node_id, "actions", actions, "Change button action")

    def action_field_changed(node_id, field):
        def changed(value):
            node, _parent, kind = find_state_item(resolve_frame(), node_id)
            if kind not in ("ui_node", "scene_node"):
                return
            actions = clone(node.get("actions", []))
            if not actions:
                actions = [new_action("none")]
            actions[0][field] = parse_editor_value(value, actions[0].get(field, ""))
            set_item_value(node_id, "actions", actions, "Edit button action")
        return changed

    def action_type_changed(node_id):
        return lambda value: set_node_action_type(node_id, value)

    def action_summary(action):
        if not action:
            return "No action"
        action_type = action.get("type", "none")
        if action_type == "jump_frame":
            return "Go to frame: {}".format((frame_by_id(action.get("target_frame_id")) or {}).get("name", "Not set"))
        if action_type in ("jump_label", "call_label"):
            return "{}: {}".format(action_type.replace("_", " ").title(), action.get("target") or "Not set")
        if action_type in ("show_screen", "hide_screen"):
            return "{}: {}".format(action_type.replace("_", " ").title(), action.get("screen") or "Not set")
        if action_type == "multiple":
            return "Multiple actions ({})".format(len(action.get("actions", [])))
        return action_type.replace("_", " ").title()
