# Scene capture, scene-node creation, and transform helpers.

init -970 python in live_studio:
    try:
        from renpy.display.core import absolute as renpy_absolute
    except Exception:
        renpy_absolute = ()

    def normalize_position(value):
        if value is None:
            return None
        try:
            if renpy_absolute and isinstance(value, renpy_absolute):
                absolute_value = float(value)
                # Keep integral absolute positions as ints so a one-pixel
                # coordinate can never be mistaken for the relative value 1.0.
                if absolute_value.is_integer():
                    return int(absolute_value)
                return {"absolute": absolute_value, "relative": 0.0}
        except Exception:
            pass
        if isinstance(value, (bool, int, float, str)):
            return value
        absolute_value = getattr(value, "absolute", None)
        relative_value = getattr(value, "relative", None)
        if absolute_value is not None or relative_value is not None:
            absolute_value = absolute_value or 0
            relative_value = relative_value or 0
            if relative_value and not absolute_value:
                return float(relative_value)
            if absolute_value and not relative_value:
                return float(absolute_value)
            return {"absolute": float(absolute_value), "relative": float(relative_value)}
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
        for _index in range(96):
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
            next_node = getattr(node, "child", None)
            if next_node is None:
                next_node = getattr(node, "raw_child", None)
            node = next_node
        return None

    def _placement_tuple(displayable):
        placement = None
        try:
            placement = renpy.get_placement(displayable)
        except Exception:
            try:
                placement = displayable.get_placement()
            except Exception:
                placement = None
        if placement is None:
            return (None, None, 0.0, 0.0, 0, 0, False)
        if isinstance(placement, (tuple, list)):
            values = list(placement) + [None] * 7
            return tuple(values[:7])
        return (
            getattr(placement, "xpos", None),
            getattr(placement, "ypos", None),
            getattr(placement, "xanchor", 0.0),
            getattr(placement, "yanchor", 0.0),
            getattr(placement, "xoffset", 0),
            getattr(placement, "yoffset", 0),
            getattr(placement, "subpixel", False),
        )

    def placement_properties(displayable):
        xpos, ypos, xanchor, yanchor, xoffset, yoffset, _subpixel = _placement_tuple(displayable)
        properties = {
            "xpos": normalize_position(xpos),
            "ypos": normalize_position(ypos),
            "xanchor": normalize_position(xanchor if xanchor is not None else 0.0),
            "yanchor": normalize_position(yanchor if yanchor is not None else 0.0),
            "xoffset": normalize_position(xoffset if xoffset is not None else 0),
            "yoffset": normalize_position(yoffset if yoffset is not None else 0),
            "xzoom": 1.0,
            "yzoom": 1.0,
            "rotate": 0.0,
            "alpha": 1.0,
        }
        state = getattr(displayable, "state", None)
        if state is not None:
            for key in ("xzoom", "yzoom", "zoom", "rotate", "alpha", "blur", "additive"):
                value = getattr(state, key, None)
                if value is not None:
                    properties[key] = normalize_position(value)
        return properties

    def position_to_pixels(value, total):
        if isinstance(value, dict):
            return float(value.get("absolute", 0) or 0) + float(value.get("relative", 0) or 0) * float(total)
        if isinstance(value, float) and -2.0 <= value <= 2.0:
            return value * float(total)
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def displayable_size(displayable):
        try:
            rendered = renpy.render(displayable, config.screen_width, config.screen_height, 0.0, 0.0)
            width, height = rendered.get_size()
            return max(1, int(width)), max(1, int(height))
        except Exception as exc:
            log_diagnostic("warning", "Could not render a captured displayable for size", {"error": str(exc), "type": displayable.__class__.__name__ if displayable else "None"})
            return 1, 1

    def calculate_bounds(properties, width, height, apply_zoom=True):
        properties = properties or {}
        width = float(width or 1)
        height = float(height or 1)
        if apply_zoom:
            xzoom = properties.get("xzoom", properties.get("zoom", 1.0))
            yzoom = properties.get("yzoom", properties.get("zoom", 1.0))
            try:
                width *= float(xzoom or 1.0)
                height *= float(yzoom or 1.0)
            except Exception:
                pass
        xpos = position_to_pixels(properties.get("xpos"), config.screen_width)
        ypos = position_to_pixels(properties.get("ypos"), config.screen_height)
        xanchor = position_to_pixels(properties.get("xanchor", 0), width)
        yanchor = position_to_pixels(properties.get("yanchor", 0), height)
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

    def runtime_layer_names(scene_list=None):
        result = []
        for collection in (getattr(config, "layers", []), getattr(config, "top_layers", [])):
            for layer in collection or []:
                if isinstance(layer, str) and layer not in result:
                    result.append(layer)
        scene_list = scene_list or scene_lists()
        layers = getattr(scene_list, "layers", None)
        if isinstance(layers, dict):
            for layer in layers.keys():
                if isinstance(layer, str) and layer not in result:
                    result.append(layer)
        return result

    def scene_group_for_layer(layer):
        for name, layers in SCENE_GROUPS.items():
            if layer in layers:
                return name
        return "Layer: {}".format(layer)

    def capture_scene_state():
        result = []
        by_name = {}
        scene_list = scene_lists()
        runtime["scene_displayables"] = {}
        if scene_list is None:
            log_diagnostic("error", "Ren'Py scene lists were unavailable during capture.")
            return result

        for layer_index, layer in enumerate(runtime_layer_names(scene_list)):
            if layer in EXCLUDED_SCENE_LAYERS:
                continue
            # Ignore Live Studio's own layers if a project retained them.
            if str(layer).startswith("live_studio"):
                continue
            group_name = scene_group_for_layer(layer)
            scene = by_name.get(group_name)
            if scene is None:
                scene_type = "dialogue" if "dialogue" in group_name.lower() else "scene"
                scene = new_scene(group_name, [], scene_type)
                by_name[group_name] = scene
                result.append(scene)
            if layer not in scene["source_layers"]:
                scene["source_layers"].append(layer)

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
                if displayable is None:
                    continue
                # UI screens are handled by LiveStudio_ui.rpy.
                try:
                    from renpy.display.screen import ScreenDisplayable
                    if isinstance(displayable, ScreenDisplayable):
                        continue
                except Exception:
                    pass
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
                    bounds=calculate_bounds(properties, width, height, apply_zoom=False),
                    source={
                        "layer": layer,
                        "tag": tag,
                        "runtime_type": displayable.__class__.__name__,
                        "captured_by": "runtime",
                    },
                    editability="editable" if image_name else "inspect",
                )
                scene["nodes"].append(node)
                runtime["scene_displayables"][node["id"]] = displayable

        return result

    def _resolve_scene_for_add(scene_id=None):
        state = resolve_frame()
        if scene_id:
            scene, _parent, kind = find_state_item(state, scene_id)
            if kind == "scene":
                return scene
        selected, _parent, kind = selected_item(state)
        if kind == "scene":
            return selected
        if kind == "scene_node":
            for scene in state.get("scenes", []):
                if find_state_item({"scenes": [scene], "ui_screens": [], "dialogue_controllers": []}, selected.get("id"))[0] is not None:
                    return scene
        return first_scene(state)


    def create_scene(name="New Scene", scene_type="scene", layers=None):
        scene = new_scene(name, layers or (["characters"] if scene_type == "dialogue" else ["master"]), scene_type)
        scene["source"] = {"created_by": "live_studio"}
        add_change(None, None, scene, root_collection="scenes", label="Add scene")
        select_item(scene.get("id"), "scene")
        return scene

    def ensure_scene(name="Master", scene_type="scene"):
        state = resolve_frame()
        for scene in state.get("scenes", []):
            if scene.get("name") == name:
                return scene
        scene = new_scene(name, ["master"] if scene_type != "dialogue" else ["characters"], scene_type)
        add_change(None, None, scene, root_collection="scenes", label="Add scene")
        return next((item for item in resolve_frame().get("scenes", []) if item.get("id") == scene.get("id")), scene)

    def add_image_to_scene(image_name, scene_id=None):
        target_scene = _resolve_scene_for_add(scene_id) or ensure_scene("Master")
        image_name = " ".join(image_name) if isinstance(image_name, (tuple, list)) else str(image_name)
        tag = image_name.split()[0] if image_name else "image"
        width = 400
        height = 400
        try:
            displayable = renpy.displayable(image_name)
            width, height = displayable_size(displayable)
        except Exception:
            pass
        node = new_scene_node(
            image_name,
            "image",
            tag=tag,
            image=image_name,
            layer=(target_scene.get("source_layers") or ["master"])[0],
            zorder=len(target_scene.get("nodes", [])),
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
            bounds=calculate_bounds({"xpos": 0.5, "ypos": 0.5, "xanchor": 0.5, "yanchor": 0.5}, width, height),
            source={"created_by": "live_studio"},
            editability="editable",
        )
        add_change(target_scene.get("id"), "nodes", node, label="Add image")
        select_item(node.get("id"), "scene_node")
        return node

    def add_scene_text(scene_id=None):
        target_scene = _resolve_scene_for_add(scene_id) or ensure_scene("Master")
        node = new_scene_node(
            "Scene Text",
            "text",
            text="New text",
            layer=(target_scene.get("source_layers") or ["master"])[0],
            zorder=len(target_scene.get("nodes", [])),
            properties={
                "text": "New text",
                "xpos": 0.5,
                "ypos": 0.5,
                "xanchor": 0.5,
                "yanchor": 0.5,
                "xsize": 500,
                "ysize": 80,
                "size": 36,
                "color": "#ffffff",
                "alpha": 1.0,
            },
            bounds={"x": config.screen_width * 0.25, "y": config.screen_height * 0.46, "width": config.screen_width * 0.5, "height": 80},
            source={"created_by": "live_studio"},
            editability="editable",
        )
        add_change(target_scene.get("id"), "nodes", node, label="Add scene text")
        select_item(node.get("id"), "scene_node")
        return node

    def add_scene_button(scene_id=None):
        target_scene = _resolve_scene_for_add(scene_id) or ensure_scene("Master")
        node = new_scene_node(
            "Scene Button",
            "hotspot",
            layer=(target_scene.get("source_layers") or ["master"])[0],
            zorder=len(target_scene.get("nodes", [])),
            properties={
                "text": "Button",
                "xpos": 0.5,
                "ypos": 0.5,
                "xanchor": 0.5,
                "yanchor": 0.5,
                "xsize": 240,
                "ysize": 70,
                "background": "#20344dcc",
                "color": "#ffffff",
                "alpha": 1.0,
            },
            bounds={"x": config.screen_width * 0.5 - 120, "y": config.screen_height * 0.5 - 35, "width": 240, "height": 70},
            actions=[new_action("jump_frame")],
            source={"created_by": "live_studio"},
            editability="editable",
        )
        add_change(target_scene.get("id"), "nodes", node, label="Add scene button")
        select_item(node.get("id"), "scene_node")
        return node

    def item_bounds(item):
        if not item:
            return None
        properties = item.get("properties") or item.get("resolved_properties") or {}
        original = item.get("bounds") or {}
        width = properties.get("xsize", original.get("width", 1))
        height = properties.get("ysize", original.get("height", 1))
        try:
            width = float(width or 1)
            height = float(height or 1)
        except Exception:
            width = float(original.get("width", 1) or 1)
            height = float(original.get("height", 1) or 1)
        # Captured runtime bounds already include the original transform. If no
        # explicit size exists, preserve the measured size and only recalculate
        # placement after editing.
        if properties.get("xpos") is None and properties.get("ypos") is None:
            return {
                "x": float(original.get("x", 0) or 0),
                "y": float(original.get("y", 0) or 0),
                "width": max(1.0, width),
                "height": max(1.0, height),
            }
        apply_zoom = properties.get("xsize") is not None or properties.get("ysize") is not None or item.get("source", {}).get("created_by") == "live_studio"
        return calculate_bounds(properties, width, height, apply_zoom=apply_zoom)
