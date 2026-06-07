# Scene capture helpers and scene-node editing.

init -920 python in live_studio:
    try:
        from renpy.display.core import absolute as renpy_absolute
    except Exception:
        renpy_absolute = ()

    def normalize_position(value):
        if value is None:
            return None
        try:
            if renpy_absolute and isinstance(value, renpy_absolute):
                return float(value)
        except Exception:
            pass
        if isinstance(value, (bool, int, float, str)):
            return value
        absolute = getattr(value, "absolute", None)
        relative = getattr(value, "relative", None)
        if absolute is not None or relative is not None:
            absolute = absolute or 0
            relative = relative or 0
            if relative and not absolute:
                return float(relative)
            if absolute and not relative:
                return float(absolute)
            return {"absolute": float(absolute), "relative": float(relative)}
        return json_safe(value)

    def scene_lists():
        try:
            return renpy.game.context().scene_lists
        except Exception:
            return None

    def entry_tag(entry):
        tag = getattr(entry, "tag", None)
        if tag:
            return str(tag)
        try:
            return str(entry[0])
        except Exception:
            return None

    def entry_zorder(entry, fallback=0):
        value = getattr(entry, "zorder", None)
        if value is not None:
            try:
                return int(value)
            except Exception:
                return fallback
        try:
            return int(entry[1])
        except Exception:
            return fallback

    def displayable_image_name(displayable):
        node = displayable
        seen = set()
        for _index in range(64):
            if node is None or id(node) in seen:
                break
            seen.add(id(node))
            name = getattr(node, "name", None)
            if name:
                if isinstance(name, str):
                    return name
                try:
                    return " ".join(str(part) for part in name)
                except Exception:
                    return str(name)
            node = getattr(node, "child", None) or getattr(node, "raw_child", None)
        return None

    def placement_properties(displayable):
        properties = {
            "xpos": None,
            "ypos": None,
            "xanchor": 0.0,
            "yanchor": 0.0,
            "xoffset": 0,
            "yoffset": 0,
            "xzoom": 1.0,
            "yzoom": 1.0,
            "rotate": 0.0,
            "alpha": 1.0,
        }
        try:
            placement = renpy.get_placement(displayable)
        except Exception:
            placement = None
        if placement is not None:
            for key in ("xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset"):
                properties[key] = normalize_position(getattr(placement, key, properties.get(key)))

        state = getattr(displayable, "state", None)
        if state is not None:
            for key in ("xzoom", "yzoom", "zoom", "rotate", "alpha", "blur", "additive"):
                value = getattr(state, key, None)
                if value is not None:
                    properties[key] = normalize_position(value)
        return properties

    def position_to_pixels(value, total):
        if isinstance(value, dict):
            return float(value.get("absolute", 0)) + float(value.get("relative", 0)) * total
        if isinstance(value, float) and -2.0 <= value <= 2.0:
            return value * total
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def displayable_size(displayable):
        try:
            rendered = renpy.render(displayable, config.screen_width, config.screen_height, 0.0, 0.0)
            return int(rendered.get_size()[0]), int(rendered.get_size()[1])
        except Exception:
            return 0, 0

    def calculate_bounds(properties, width, height):
        screen_width = float(config.screen_width)
        screen_height = float(config.screen_height)
        xzoom = properties.get("xzoom", properties.get("zoom", 1.0))
        yzoom = properties.get("yzoom", properties.get("zoom", 1.0))
        try:
            width = float(width) * float(xzoom or 1.0)
            height = float(height) * float(yzoom or 1.0)
        except Exception:
            width = float(width or 0)
            height = float(height or 0)
        xpos = position_to_pixels(properties.get("xpos"), screen_width)
        ypos = position_to_pixels(properties.get("ypos"), screen_height)
        xanchor = position_to_pixels(properties.get("xanchor", 0), width)
        yanchor = position_to_pixels(properties.get("yanchor", 0), height)
        # Offsets are always absolute pixels in Ren'Py, even when represented
        # as floats. They must not be interpreted like relative positions.
        try:
            xoffset = float(properties.get("xoffset", 0) or 0)
        except Exception:
            xoffset = 0.0
        try:
            yoffset = float(properties.get("yoffset", 0) or 0)
        except Exception:
            yoffset = 0.0
        return {
            "x": xpos - xanchor + xoffset,
            "y": ypos - yanchor + yoffset,
            "width": max(1.0, width),
            "height": max(1.0, height),
        }

    def scene_group_for_layer(layer):
        for name, layers in SCENE_GROUPS.items():
            if layer in layers:
                return name
        return "Layer: {}".format(layer)

    def capture_scene_state():
        result = []
        by_name = {}
        scene_list = scene_lists()
        if scene_list is None:
            log_diagnostic("error", "Ren'Py scene lists were unavailable during capture.")
            return result

        for layer_index, layer in enumerate(config.layers):
            if layer in EXCLUDED_SCENE_LAYERS:
                continue
            group_name = scene_group_for_layer(layer)
            scene = by_name.get(group_name)
            if scene is None:
                scene = new_scene(group_name, [], "scene")
                by_name[group_name] = scene
                result.append(scene)
            if layer not in scene["source_layers"]:
                scene["source_layers"].append(layer)

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
                if displayable is None:
                    continue
                image_name = displayable_image_name(displayable)
                properties = placement_properties(displayable)
                width, height = displayable_size(displayable)
                node = new_scene_node(
                    image_name or tag,
                    "image" if image_name else "displayable",
                    tag=tag,
                    image=image_name,
                    layer=layer,
                    zorder=entry_zorder(entry, index),
                    properties=properties,
                    bounds=calculate_bounds(properties, width, height),
                    source={
                        "layer": layer,
                        "tag": tag,
                        "runtime_type": displayable.__class__.__name__,
                    },
                    editability="editable" if image_name else "inspect",
                )
                scene["nodes"].append(node)
                runtime.setdefault("scene_displayables", {})[node["id"]] = displayable

        return result

    def scene_property_groups(kind=None):
        if kind in ("ui_node", "ui_screen"):
            return UI_PROPERTY_GROUPS
        return SCENE_PROPERTY_GROUPS

    def selected_property_groups():
        return scene_property_groups(selected_item_kind)

    def selected_property_value(path, default=""):
        item, _parent_id, _kind = selected_item()
        if item is None:
            return default
        value = get_path_value(item, path, default)
        return value

    def selected_property_text(path):
        value = selected_property_value(path, "")
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        return str(value)

    def add_image_to_scene(image_name, scene_id=None):
        state = resolve_frame()
        target_scene = None
        if scene_id:
            target_scene, _parent, kind = find_state_item(state, scene_id)
            if kind != "scene":
                target_scene = None
        if target_scene is None:
            target_scene = next((scene for scene in state.get("scenes", []) if scene.get("name") == "Exploration"), None)
        if target_scene is None and state.get("scenes"):
            target_scene = state["scenes"][0]
        if target_scene is None:
            target_scene = new_scene("Exploration", ["master"])
            add_change(None, None, target_scene, root_collection="scenes", label="Add scene")
            state = resolve_frame()
            target_scene = next((scene for scene in state.get("scenes", []) if scene.get("name") == "Exploration"), state.get("scenes", [None])[0])
        if target_scene is None:
            return
        image_name = " ".join(image_name) if isinstance(image_name, (tuple, list)) else str(image_name)
        tag = image_name.split()[0] if image_name else "image"
        node = new_scene_node(
            image_name,
            "image",
            tag=tag,
            image=image_name,
            layer=(target_scene.get("source_layers") or ["master"])[0],
            zorder=0,
            properties={
                "xpos": 0.5,
                "ypos": 0.5,
                "xanchor": 0.5,
                "yanchor": 0.5,
                "xoffset": 0,
                "yoffset": 0,
                "xzoom": 1.0,
                "yzoom": 1.0,
                "rotate": 0.0,
                "alpha": 1.0,
            },
            bounds={
                "x": config.screen_width * 0.25,
                "y": config.screen_height * 0.25,
                "width": config.screen_width * 0.5,
                "height": config.screen_height * 0.5,
            },
            source={"created_by": "live_studio"},
            editability="editable",
        )
        add_change(target_scene.get("id"), "nodes", node, label="Add image")
        select_item(node.get("id"), "scene_node")

    def update_item_bounds_from_properties(item):
        if item is None:
            return None
        bounds = item.get("bounds") or {"x": 0, "y": 0, "width": 100, "height": 100}
        properties = item.get("properties", {})
        width = bounds.get("width", 100)
        height = bounds.get("height", 100)
        return calculate_bounds(properties, width, height)
