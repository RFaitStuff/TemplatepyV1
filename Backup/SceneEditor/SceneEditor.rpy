init 999 python:
    config.underlay.append(renpy.Keymap(
        scene_editor = renpy.curry(renpy.invoke_in_new_context)(_viewers.open_scene_editor),
        ))

init 999 python:
    config.locked = False
    check_version = getattr(_viewers, "check_version", None)
    if callable(check_version) and check_version(23060707):
        config.keymap["scene_editor"] = ['shift_K_e']
    else:
        config.keymap["scene_editor"] = ['E']

init -898 python in _viewers:
    from copy import deepcopy
    from collections import defaultdict
    from math import atan2, degrees, sin
    from renpy.store import config, persistent, Text, Fixed, Solid, Transform, InputValue as SceneEditorInputValue
    try:
        from renpy.display.image import images as scene_editor_renpy_images
    except Exception:
        scene_editor_renpy_images = {}
    try:
        from renpy.display.core import absolute as scene_editor_absolute
    except Exception:
        scene_editor_absolute = None
    try:
        from renpy.display.core import display_time as scene_editor_display_time
    except Exception:
        scene_editor_display_time = lambda: 0.0
    try:
        from renpy.display.screen import ScreenDisplayable as scene_editor_screen_displayable
    except Exception:
        scene_editor_screen_displayable = ()
    try:
        from renpy.display.layout import Position as scene_editor_position_type
    except Exception:
        scene_editor_position_type = ()

    scene_editor_selected_layer = "master"
    scene_editor_selected_tag = None
    scene_editor_canvas_zoom = scene_editor_canvas_zoom_default if "scene_editor_canvas_zoom_default" in globals() else 1.0
    scene_editor_history = []
    scene_editor_redo_stack = []
    scene_editor_restore_not_included_layer = None
    scene_editor_default_props = scene_editor_primary_props
    scene_editor_sound_inputs = defaultdict(str)
    scene_editor_active_sounds = {}
    scene_editor_property_groups_state = {name: (name == "Core") for name, _props in scene_editor_property_groups}
    scene_editor_property_input_cache = {}
    scene_editor_clipboard = None
    scene_editor_hover_image_name = None
    scene_editor_captured_displayables = [{}]
    scene_editor_locked_items = set()
    scene_editor_hidden_items = set()
    scene_editor_group_members = {}
    scene_editor_thumbnail_cache = {}
    scene_editor_child_size_cache = {}
    scene_editor_transform_apply_error_cache = set()
    scene_editor_image_current_path = ()
    scene_editor_tool_mode = "select"
    scene_editor_axis_constraint = None
    scene_editor_active_drag_mode = None
    scene_editor_snap_enabled = False
    scene_editor_snap_increment = scene_editor_default_snap_increment if "scene_editor_default_snap_increment" in globals() else 16
    scene_editor_asset_search_active = False
    scene_editor_active_value_input = None
    scene_editor_highlight_until = 0.0
    scene_editor_transform_preview_props = (
        "xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset",
        "zoom", "xzoom", "yzoom", "rotate", "alpha",
        "zpos", "xrotate", "yrotate", "zrotate", "xaround", "yaround",
        "radius", "angle", "blur", "additive", "blend",
        "xpan", "ypan", "xtile", "ytile", "subpixel",
    )

    if "not_included_layer" not in globals():
        not_included_layer = ()
    if "default_transition" not in globals():
        default_transition = None
    if "default_warper" not in globals():
        default_warper = "linear"
    if "time_range" not in globals():
        time_range = 8.0
    if "default_channel_list" not in globals():
        default_channel_list = []
    if "at_clauses_flag" not in globals():
        at_clauses_flag = False
    if "scene_editor_snap_increment_values" not in globals():
        scene_editor_snap_increment_values = (8, 16, 32, 64)

    _scene_editor_all_props = tuple(prop for _group, props in scene_editor_property_groups for _label, prop in props)

    if "camera_props" not in globals():
        camera_props = tuple(prop for prop in _scene_editor_all_props if prop not in ("child", "function"))
    if "transform_props" not in globals():
        transform_props = ("child",) + tuple(prop for prop in _scene_editor_all_props if prop != "function")
    if "property_default_value" not in globals():
        property_default_value = {
            "child": (None, None),
            "xpos": 0,
            "ypos": 0,
            "zpos": 0.0,
            "xaround": 0.0,
            "yaround": 0.0,
            "around": (0.0, 0.0),
            "radius": 0,
            "angle": 0,
            "xanchor": 0,
            "yanchor": 0,
            "matrixanchorX": 0.5,
            "matrixanchorY": 0.5,
            "matrixanchor": (0.5, 0.5),
            "xoffset": 0,
            "yoffset": 0,
            "rotate": 0.0,
            "xzoom": 1.0,
            "yzoom": 1.0,
            "zoom": 1.0,
            "cropX": 0.0,
            "cropY": 0.0,
            "cropW": 1.0,
            "cropH": 1.0,
            "crop": (0.0, 0.0, 1.0, 1.0),
            "xrotate": 0.0,
            "yrotate": 0.0,
            "zrotate": 0.0,
            "xorientation": 0.0,
            "yorientation": 0.0,
            "zorientation": 0.0,
            "orientation": (0.0, 0.0, 0.0),
            "point_to": None,
            "offsetX": 0.0,
            "offsetY": 0.0,
            "offsetZ": 0.0,
            "rotateX": 0.0,
            "rotateY": 0.0,
            "rotateZ": 0.0,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "scaleZ": 1.0,
            "dof": 400,
            "focusing": round(renpy.config.perspective[1], 2),
            "alpha": 1.0,
            "additive": 0.0,
            "blur": 0.0,
            "hue": 0.0,
            "bright": 0.0,
            "saturate": 1.0,
            "contrast": 1.0,
            "invert": 0.0,
            "zzoom": False,
            "xpan": 0.0,
            "ypan": 0.0,
            "xtile": 1,
            "ytile": 1,
            "function": (None, None),
            "perspective": None,
            "blend": "normal",
        }
    if "load_matrix" not in globals():
        def load_matrix(prop, value):
            return []
    if "menu_props" not in globals():
        menu_props = {}
    if "boolean_props" not in globals():
        boolean_props = set()
    if "check_new_position_type" not in globals():
        def check_new_position_type(value):
            if scene_editor_position_type and isinstance(value, scene_editor_position_type):
                return True
            return hasattr(value, "absolute") and hasattr(value, "relative")
    if "get_image_state" not in globals():
        def get_image_state(layer, scene_num=None):
            if scene_num is None:
                scene_num = current_scene
            try:
                base_org = image_state_org[scene_num].get(layer, {})
                overrides = image_state[scene_num].get(layer, {})
            except Exception:
                base_org = {}
                overrides = {}
            result = dict(base_org)
            result.update(overrides)
            return result
    if "get_image_name_candidates" not in globals():
        def get_image_name_candidates():
            try:
                names = renpy.list_images()
            except Exception:
                names = []
            normalized = []
            for name in names:
                if isinstance(name, str):
                    normalized.append(tuple(name.split()))
                elif isinstance(name, tuple):
                    normalized.append(name)
                else:
                    normalized.append((str(name),))
            return normalized
    if "get_value" not in globals():
        def get_value(key, time=None, default=False, scene_num=None):
            tag, layer, prop = key
            if scene_num is None:
                scene_num = current_scene
            state = {}
            if tag is None:
                state = camera_state_org[scene_num].get(layer, {})
            else:
                layer_state = get_image_state(layer, scene_num)
                state = layer_state.get(tag, {}) if isinstance(layer_state, dict) else {}
            if prop in state:
                return state[prop]
            if default:
                return property_default_value.get(prop)
            return None
    if "set_keyframe" not in globals():
        def set_keyframe(key, value, recursion=False, time=None):
            tag, layer, prop = key
            scene_index = current_scene
            if time is None:
                time = current_time
            if tag is None:
                layer_state = camera_state_org[scene_index].setdefault(layer, {})
            else:
                layer_dict = image_state[scene_index].setdefault(layer, {})
                layer_state = layer_dict.setdefault(tag, {})
            previous_value = layer_state.get(prop, property_default_value.get(prop))
            layer_state[prop] = value
            frames = all_keyframes[scene_index].setdefault(key, [])
            warper = getattr(persistent, "_viewer_warper", default_warper)
            scene_start = scene_keyframes[scene_index][1]
            if not frames and time != scene_start:
                frames.append((previous_value, scene_start, warper))
            inserted = False
            for idx, (_, existing_time, _) in enumerate(frames):
                if time == existing_time:
                    frames[idx] = (value, time, warper)
                    inserted = True
                    break
                if time < existing_time:
                    frames.insert(idx, (value, time, warper))
                    inserted = True
                    break
            if not inserted:
                frames.append((value, time, warper))
    if "play" not in globals():
        def play(loop=True):
            return
    if "change_time" not in globals():
        def change_time(value):
            global current_time
            current_time = round(value, 2)
            for channel in getattr(persistent, "_viewer_channel_list", []) or []:
                try:
                    renpy.music.stop(channel, False)
                except Exception:
                    pass
            play_func = globals().get("play", None)
            if callable(play_func):
                play_func(False)
            renpy.restart_interaction()

    if "reset" not in globals():
        def reset(key_list, time=None):
            if time is None:
                time = current_time
            if not isinstance(key_list, list):
                key_list = [key_list]
            for key in key_list:
                tag, layer, prop = key
                if tag is None:
                    state = camera_state_org[current_scene].get(layer, {})
                else:
                    state = get_image_state(layer).get(tag, {})
                value = state.get(prop, property_default_value.get(prop))
                set_keyframe(key, value, time=time)
            change_time(time)
    def scene_editor_remove_image(layer, tag):
        try:
            key = scene_editor_item_key(layer, tag)
            if key in scene_editor_locked_items:
                scene_editor_locked_items.remove(key)
            if key in scene_editor_group_members:
                del scene_editor_group_members[key]
            if tag in image_state[current_scene].get(layer, {}):
                del image_state[current_scene][layer][tag]
            if tag in image_state_org[current_scene].get(layer, {}):
                del image_state_org[current_scene][layer][tag]
            if tag in scene_editor_captured_displayables[current_scene].get(layer, {}):
                del scene_editor_captured_displayables[current_scene][layer][tag]
            zorder_list[current_scene][layer] = [(t, z) for t, z in zorder_list[current_scene].get(layer, []) if t != tag]
            for key in list(all_keyframes[current_scene].keys()):
                if key[0] == tag and key[1] == layer:
                    del all_keyframes[current_scene][key]
        except Exception:
            pass

    if "put_clipboard" not in globals():
        def put_clipboard():
            renpy.notify(_("Clipboard export requires ActionEditor"))
    if "put_image_clipboard" not in globals():
        def put_image_clipboard(tag, layer):
            renpy.notify(_("Image clipboard requires ActionEditor"))
    if "put_camera_clipboard" not in globals():
        def put_camera_clipboard(layer="master"):
            renpy.notify(_("Camera clipboard requires ActionEditor"))

    def scene_editor_default_false():
        return False

    def scene_editor_current_layers():
        rv = []
        for layer in config.layers:
            if not isinstance(layer, str):
                continue
            state = get_image_state(layer)
            if state:
                rv.append(layer)
        return rv

    def scene_editor_sound_channels():
        channels = list(persistent._viewer_channel_list or default_channel_list)
        rv = [channel for channel in channels if isinstance(channel, str)]
        if not rv:
            rv = ["sound"]
        return rv

    def scene_editor_sound_input_changed(channel):
        def changed(text):
            scene_editor_sound_inputs[channel] = text.strip()
        return changed

    def scene_editor_sound_input_value(channel):
        return scene_editor_sound_inputs[channel]

    def scene_editor_sound_status(channel):
        filename = scene_editor_active_sounds.get(channel)
        if filename:
            return _("Playing {}".format(filename))
        return _("Stopped")

    def scene_editor_start_sound(channel):
        filename = scene_editor_sound_inputs[channel]
        if not filename:
            renpy.notify(_("Enter a sound filename for {}".format(channel)))
            return
        try:
            renpy.music.play(filename, channel=channel, loop=False)
            scene_editor_active_sounds[channel] = filename
            renpy.notify(_("Playing {}".format(channel)))
        except Exception as exc:
            renpy.notify(_("Could not play sound: {}".format(exc)))

    def scene_editor_stop_sound(channel):
        if channel in scene_editor_active_sounds:
            try:
                renpy.music.stop(channel)
                del scene_editor_active_sounds[channel]
            except Exception:
                pass
        renpy.notify(_("Stopped {}".format(channel)))

    def scene_editor_property_group_expanded(name):
        if name == "Core":
            return True
        return scene_editor_property_groups_state.get(name, False)

    def scene_editor_toggle_property_group(name):
        if name == "Core":
            return
        scene_editor_property_groups_state[name] = not scene_editor_property_group_expanded(name)
        renpy.restart_interaction()

    def scene_editor_canvas_bounds():
        right_sidebar = globals().get("scene_editor_right_sidebar_width", 0)
        available_x = scene_editor_sidebar_width
        available_y = scene_editor_top_height
        available_width = max(1.0, config.screen_width - scene_editor_sidebar_width - right_sidebar)
        available_height = max(1.0, config.screen_height - scene_editor_top_height - scene_editor_bottom_height)
        target_ratio = 16.0 / 9.0
        width = available_width
        height = width / target_ratio
        if height > available_height:
            height = available_height
            width = height * target_ratio
        x = available_x + max(0.0, (available_width - width) / 2.0)
        y = available_y
        return x, y, width, height

    def scene_editor_canvas_scale_value():
        _x, _y, width, height = scene_editor_canvas_bounds()
        if config.screen_width <= 0 or config.screen_height <= 0:
            return 1.0
        base_scale = min(width / float(config.screen_width), height / float(config.screen_height))
        return max(0.05, base_scale * scene_editor_canvas_zoom)

    def scene_editor_canvas_offsets():
        x, y, width, height = scene_editor_canvas_bounds()
        scale = scene_editor_canvas_scale_value()
        content_width = config.screen_width * scale
        content_height = config.screen_height * scale
        offset_x = x + max(0.0, (width - content_width) / 2.0)
        offset_y = y + max(0.0, (height - content_height) / 2.0)
        return offset_x, offset_y, scale

    def scene_editor_preview_transform_values():
        if getattr(persistent, "_viewer_legacy_gui", False):
            return 0.0, 0.0, 1.0
        preview_zoom = globals().get("preview_size", 1.0) * globals().get("scene_editor_preview_scale", 1.0)
        leftover = 1.0 - preview_zoom
        preview_offset_x = leftover * min(1.0, max(0.0, globals().get("scene_editor_preview_offset_x", 0.5)))
        preview_offset_y = leftover * min(1.0, max(0.0, globals().get("scene_editor_preview_offset_y", 0.5)))
        return preview_offset_x * config.screen_width, preview_offset_y * config.screen_height, preview_zoom

    def scene_editor_point_in_canvas(x, y):
        canvas_x, canvas_y, width, height = scene_editor_canvas_bounds()
        return (canvas_x <= x <= canvas_x + width) and (canvas_y <= y <= canvas_y + height)

    def scene_editor_screen_to_stage(x, y):
        offset_x, offset_y, scale = scene_editor_canvas_offsets()
        preview_x, preview_y, preview_zoom = scene_editor_preview_transform_values()
        if scale == 0:
            return (x - offset_x, y - offset_y)
        if preview_zoom == 0:
            preview_zoom = 1.0
        return (((x - offset_x) / scale - preview_x) / preview_zoom, ((y - offset_y) / scale - preview_y) / preview_zoom)

    def scene_editor_get_layers():
        rv = []
        excluded = globals().get("not_included_layer", ())
        for layer in config.layers:
            if isinstance(layer, str) and layer not in excluded:
                rv.append(layer)
        return rv

    class SceneEditorFixedTimeDisplayable(renpy.Displayable):
        def __init__(self, child, fixed_st=0, fixed_at=0, **properties):
            super(SceneEditorFixedTimeDisplayable, self).__init__(**properties)
            self.child = child
            self.fixed_st = fixed_st
            self.fixed_at = fixed_at

        def render(self, width, height, st, at):
            try:
                renpy.render(self.child, width, height, 0, 0)
            except Exception:
                pass
            return renpy.render(self.child, width, height, self.fixed_st, self.fixed_at)

    def scene_editor_init_state():
        global image_state, image_state_org, camera_state_org, movie_cache, third_view_child, scene_editor_captured_displayables
        action_editor_init()
        scene_editor_captured_displayables = [{}]
        for layer in scene_editor_get_layers():
            scene_editor_captured_displayables[current_scene][layer] = {}

    def scene_editor_scene_lists():
        try:
            return renpy.game.context().scene_lists
        except Exception:
            return None

    def scene_editor_normalize_position(value):
        if value is None:
            return None
        if check_new_position_type(value):
            abs_part = getattr(value, "absolute", 0)
            rel_part = getattr(value, "relative", 0)
            if abs_part and not rel_part:
                return int(abs_part)
            if rel_part and not abs_part:
                return float(rel_part)
            return value
        if scene_editor_absolute and isinstance(value, scene_editor_absolute):
            try:
                return round(float(value))
            except Exception:
                return float(value)
        return value

    def scene_editor_fill_placement(target, placement):
        if placement is None:
            return
        for prop in ("xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset"):
            target[prop] = scene_editor_normalize_position(getattr(placement, prop, None))

    def scene_editor_image_name_string(value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        try:
            return " ".join([str(part) for part in value])
        except Exception:
            return str(value)

    def scene_editor_find_image_name(displayable):
        node = displayable
        guard = 0
        while node is not None and guard < 64:
            name = getattr(node, "name", None)
            if name:
                return scene_editor_image_name_string(name)
            node = getattr(node, "child", None) or getattr(node, "raw_child", None)
            guard += 1
        return None

    def scene_editor_get_transform_name(obj):
        getter = globals().get("get_transform_name", None)
        if callable(getter):
            return getter(obj)
        atl = getattr(obj, "atl", None)
        if atl is None:
            return None
        try:
            for name, _file, _line in renpy.dump.transforms:
                transform = getattr(renpy.store, name, None)
                transform_atl = getattr(transform, "atl", None)
                if transform is not None and getattr(transform_atl, "loc", None) == getattr(atl, "loc", None):
                    return (name, obj.context.context)
        except Exception:
            return None
        return None

    def scene_editor_extract_camera_state(displayable):
        data = {}
        if displayable is None:
            return data
        try:
            placement = renpy.get_placement(displayable)
        except Exception:
            placement = None
        scene_editor_fill_placement(data, placement)
        state = getattr(displayable, "state", None)
        if state is not None:
            for prop in camera_props:
                if prop in data:
                    continue
                data[prop] = scene_editor_normalize_position(getattr(state, prop, None))
            for group_name, group_props in globals().get("props_groups", {}).items():
                group_values = getattr(state, group_name, None)
                if group_values is None:
                    continue
                for prop, value in zip(group_props, group_values):
                    if prop in camera_props:
                        data[prop] = scene_editor_normalize_position(value)
        data.setdefault("at_list", [])
        return data

    def scene_editor_extract_image_state(displayable):
        if displayable is None:
            return None
        if scene_editor_screen_displayable and isinstance(displayable, scene_editor_screen_displayable):
            return None
        try:
            placement = renpy.get_placement(displayable)
        except Exception:
            placement = None
        entry = {"at_list": []}
        scene_editor_fill_placement(entry, placement)
        image_name = scene_editor_find_image_name(displayable)
        if image_name:
            entry["child"] = (image_name, None)
        else:
            return None
        display_state = getattr(displayable, "state", None)
        for prop in transform_props:
            if prop in entry or prop == "child":
                continue
            value = None
            if display_state is not None:
                value = getattr(display_state, prop, None)
            entry[prop] = scene_editor_normalize_position(value)
        if display_state is not None:
            for group_name, group_props in globals().get("props_groups", {}).items():
                group_values = getattr(display_state, group_name, None)
                if group_values is None:
                    continue
                for prop, value in zip(group_props, group_values):
                    if prop in transform_props:
                        entry[prop] = scene_editor_normalize_position(value)
        return entry

    def scene_editor_entry_tag(entry):
        tag = getattr(entry, "tag", None)
        if tag:
            return tag
        try:
            return entry[0]
        except Exception:
            return None

    def scene_editor_entry_zorder(entry, fallback):
        zorder = getattr(entry, "zorder", None)
        if zorder is not None:
            return zorder
        try:
            return entry[1]
        except Exception:
            return fallback

    def scene_editor_capture_live_scene():
        sle = scene_editor_scene_lists()
        if sle is None:
            return
        for layer in scene_editor_get_layers():
            try:
                camera_displayable = sle.camera_transform[layer]
            except Exception:
                camera_displayable = None
            camera_state_org[current_scene][layer] = {}
            child = getattr(camera_displayable, "child", None)
            at_list = []
            while child is not None and type(child) is not renpy.display.layout.MultiBox:
                trans = scene_editor_get_transform_name(child)
                if trans is not None:
                    at_list.append(trans)
                child = getattr(child, "child", None)
            at_list.reverse()
            camera_state_org[current_scene][layer]["at_list"] = at_list
            camera_state_org[current_scene][layer].update(scene_editor_extract_camera_state(camera_displayable))
            image_state[current_scene][layer] = {}
            image_state_org[current_scene][layer] = {}
            scene_editor_captured_displayables[current_scene][layer] = {}
            z_entries = []
            try:
                layer_entries = list(sle.layers[layer])
            except Exception:
                layer_entries = []
            for idx, entry in enumerate(layer_entries):
                tag = scene_editor_entry_tag(entry)
                if not tag:
                    continue
                displayable = sle.get_displayable_by_tag(layer, tag)
                image_props = scene_editor_extract_image_state(displayable)
                if not image_props:
                    image_props = {"at_list": [], "_captured_raw": True}
                    try:
                        scene_editor_fill_placement(image_props, renpy.get_placement(displayable))
                    except Exception:
                        pass
                image_state_org[current_scene][layer][tag] = deepcopy(image_props)
                scene_editor_captured_displayables[current_scene][layer][tag] = displayable
                child = getattr(displayable, "child", None)
                at_list = []
                while child is not None:
                    trans = scene_editor_get_transform_name(child)
                    if trans is not None:
                        at_list.append(trans)
                    child = getattr(child, "child", None)
                at_list.reverse()
                image_state_org[current_scene][layer][tag]["at_list"] = at_list
                z_entries.append((tag, scene_editor_entry_zorder(entry, idx)))
            zorder_list[current_scene][layer] = z_entries

    def scene_editor_copy_captured_displayables():
        copied = []
        for scene_data in scene_editor_captured_displayables:
            copied_scene = {}
            for layer, tags in scene_data.items():
                copied_scene[layer] = dict(tags)
            copied.append(copied_scene)
        return copied

    def scene_editor_clear_runtime_caches(assets=False):
        scene_editor_property_input_cache.clear()
        scene_editor_child_size_cache.clear()
        scene_editor_transform_apply_error_cache.clear()
        if assets and "scene_editor_clear_asset_browser_cache" in globals():
            scene_editor_clear_asset_browser_cache()

    def scene_editor_shortcuts_enabled():
        return not scene_editor_asset_search_active and scene_editor_active_value_input is None

    def scene_editor_set_asset_search_active(active):
        global scene_editor_asset_search_active
        scene_editor_asset_search_active = bool(active)
        renpy.restart_interaction()

    def scene_editor_flash_selected(duration=0.75):
        global scene_editor_highlight_until
        if not scene_editor_has_selected():
            return
        now = scene_editor_display_time()
        scene_editor_highlight_until = max(scene_editor_highlight_until, now + max(0.1, duration))
        renpy.restart_interaction()

    def scene_editor_active_transform_mode():
        if scene_editor_active_drag_mode == "resize":
            return "scale"
        if scene_editor_active_drag_mode in ("move", "scale", "rotate"):
            return scene_editor_active_drag_mode
        return scene_editor_tool_mode

    def scene_editor_clear_axis_constraint(restart=False):
        global scene_editor_axis_constraint
        scene_editor_axis_constraint = None
        if restart:
            renpy.restart_interaction()

    def scene_editor_can_constrain_axis():
        return scene_editor_active_transform_mode() in ("move", "scale")

    def scene_editor_toggle_axis_constraint(axis):
        global scene_editor_axis_constraint
        if axis not in ("x", "y"):
            return
        if not scene_editor_can_constrain_axis():
            return
        scene_editor_axis_constraint = None if scene_editor_axis_constraint == axis else axis
        renpy.restart_interaction()

    def scene_editor_toggle_snap():
        global scene_editor_snap_enabled
        scene_editor_snap_enabled = not scene_editor_snap_enabled
        renpy.restart_interaction()

    def scene_editor_set_snap_increment(value):
        global scene_editor_snap_increment
        try:
            scene_editor_snap_increment = max(1, int(value))
        except Exception:
            return
        renpy.restart_interaction()

    def scene_editor_cycle_snap_increment():
        global scene_editor_snap_increment
        values = tuple(scene_editor_snap_increment_values)
        if not values:
            return
        try:
            index = values.index(scene_editor_snap_increment)
        except ValueError:
            index = -1
        scene_editor_snap_increment = values[(index + 1) % len(values)]
        renpy.restart_interaction()

    def scene_editor_snap_value(value):
        if not scene_editor_snap_enabled:
            return value
        increment = max(1, int(scene_editor_snap_increment))
        return round(float(value) / increment) * increment

    def scene_editor_raise_ignore_event():
        ignore = getattr(renpy, "IgnoreEvent", None)
        if ignore is None:
            ignore = renpy.display.core.IgnoreEvent
        raise ignore()

    def scene_editor_snapshot():
        return {
            "current_scene": current_scene,
            "current_time": current_time,
            "scene_keyframes": deepcopy(scene_keyframes),
            "image_state": deepcopy(image_state),
            "image_state_org": deepcopy(image_state_org),
            "captured_displayables": scene_editor_copy_captured_displayables(),
            "camera_state_org": deepcopy(camera_state_org),
            "zorder_list": deepcopy(zorder_list),
            "all_keyframes": deepcopy(all_keyframes),
            "loops": deepcopy(loops),
            "splines": deepcopy(splines),
            "selected_layer": scene_editor_selected_layer,
            "selected_tag": scene_editor_selected_tag,
            "locked_items": deepcopy(scene_editor_locked_items),
            "hidden_items": deepcopy(scene_editor_hidden_items),
            "group_members": deepcopy(scene_editor_group_members),
        }

    def scene_editor_snapshots_equivalent(a, b):
        for key in a:
            if key == "captured_displayables":
                continue
            if a.get(key) != b.get(key):
                return False
        return True

    def scene_editor_restore(snapshot):
        global current_scene, current_time, scene_keyframes, image_state, image_state_org, scene_editor_captured_displayables, camera_state_org, zorder_list, all_keyframes, loops, splines
        global scene_editor_selected_layer, scene_editor_selected_tag, scene_editor_locked_items, scene_editor_hidden_items, scene_editor_group_members
        current_scene = snapshot["current_scene"]
        current_time = snapshot["current_time"]
        scene_keyframes = deepcopy(snapshot["scene_keyframes"])
        image_state = deepcopy(snapshot["image_state"])
        image_state_org = deepcopy(snapshot["image_state_org"])
        scene_editor_captured_displayables = snapshot.get("captured_displayables", scene_editor_copy_captured_displayables())
        camera_state_org = deepcopy(snapshot["camera_state_org"])
        zorder_list = deepcopy(snapshot["zorder_list"])
        all_keyframes = deepcopy(snapshot["all_keyframes"])
        loops = deepcopy(snapshot["loops"])
        splines = deepcopy(snapshot["splines"])
        scene_editor_selected_layer = snapshot["selected_layer"]
        scene_editor_selected_tag = snapshot["selected_tag"]
        scene_editor_locked_items = deepcopy(snapshot.get("locked_items", set()))
        scene_editor_hidden_items = deepcopy(snapshot.get("hidden_items", set()))
        scene_editor_group_members = deepcopy(snapshot.get("group_members", {}))
        scene_editor_clear_runtime_caches()
        change_time(current_time)

    def scene_editor_push_history():
        snapshot = scene_editor_snapshot()
        if scene_editor_history and scene_editor_snapshots_equivalent(scene_editor_history[-1], snapshot):
            return
        scene_editor_history.append(snapshot)
        if len(scene_editor_history) > scene_editor_history_limit:
            del scene_editor_history[0]
        del scene_editor_redo_stack[:]

    def scene_editor_undo():
        if not scene_editor_history:
            renpy.notify(_("Nothing to undo"))
            return
        scene_editor_redo_stack.append(scene_editor_snapshot())
        scene_editor_restore(scene_editor_history.pop())

    def scene_editor_redo():
        if not scene_editor_redo_stack:
            renpy.notify(_("Nothing to redo"))
            return
        scene_editor_history.append(scene_editor_snapshot())
        if len(scene_editor_history) > scene_editor_history_limit:
            del scene_editor_history[0]
        scene_editor_restore(scene_editor_redo_stack.pop())

    def scene_editor_select(layer, tag):
        global scene_editor_selected_layer, scene_editor_selected_tag
        if tag is not None and (scene_editor_item_hidden(layer, tag) or scene_editor_item_locked(layer, tag)):
            return
        scene_editor_selected_layer = layer
        scene_editor_selected_tag = tag
        scene_editor_clear_runtime_caches()
        renpy.restart_interaction()

    def scene_editor_item_key(layer=None, tag=None):
        if layer is None:
            layer = scene_editor_selected_layer
        if tag is None:
            tag = scene_editor_selected_tag
        return (layer, tag)

    def scene_editor_item_locked(layer=None, tag=None):
        if tag is None:
            tag = scene_editor_selected_tag
        if tag is None:
            return False
        return scene_editor_item_key(layer, tag) in scene_editor_locked_items

    def scene_editor_item_hidden(layer=None, tag=None):
        if tag is None:
            tag = scene_editor_selected_tag
        if tag is None:
            return False
        return scene_editor_item_key(layer, tag) in scene_editor_hidden_items

    def scene_editor_toggle_hidden(layer=None, tag=None):
        if layer is None:
            layer = scene_editor_selected_layer
        if tag is None:
            tag = scene_editor_selected_tag
        if tag is None:
            return
        scene_editor_push_history()
        key = scene_editor_item_key(layer, tag)
        hiding = key not in scene_editor_hidden_items
        if hiding:
            scene_editor_hidden_items.add(key)
        else:
            scene_editor_hidden_items.remove(key)
        change_time(current_time)
        if hiding and scene_editor_selected_layer == layer and scene_editor_selected_tag == tag:
            scene_editor_select(layer, None)
            return
        renpy.restart_interaction()

    def scene_editor_toggle_lock(layer=None, tag=None):
        if layer is None:
            layer = scene_editor_selected_layer
        if tag is None:
            tag = scene_editor_selected_tag
        if tag is None:
            return
        scene_editor_push_history()
        key = scene_editor_item_key(layer, tag)
        if key in scene_editor_locked_items:
            scene_editor_locked_items.remove(key)
        else:
            scene_editor_locked_items.add(key)
        change_time(current_time)
        if scene_editor_selected_layer == layer and scene_editor_selected_tag == tag and key in scene_editor_locked_items:
            scene_editor_select(layer, None)
            return
        renpy.restart_interaction()

    def scene_editor_layer_tags(layer):
        state = get_image_state(layer)
        ordered = scene_editor_ordered_tags(layer)
        return [tag for tag, _z in ordered if tag in state]

    def scene_editor_layer_panel_tags(layer):
        tags = scene_editor_layer_tags(layer)
        tags.reverse()
        return tags

    def scene_editor_rewrite_zorder(layer, tags):
        zorder_list[current_scene][layer] = [(tag, index) for index, tag in enumerate(tags)]

    def scene_editor_append_zorder(layer, tag):
        entries = zorder_list[current_scene].setdefault(layer, [])
        entries.append((tag, len(entries)))

    def scene_editor_layer_render_tags(layer):
        state = get_image_state(layer)
        return [tag for tag in scene_editor_layer_tags(layer) if tag in state and not scene_editor_item_hidden(layer, tag)]

    def scene_editor_reorder_selected(mode):
        layer = scene_editor_selected_layer
        tag = scene_editor_selected_tag
        if tag is None or scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        panel_tags = list(scene_editor_layer_panel_tags(layer))
        if tag not in panel_tags:
            return
        index = panel_tags.index(tag)
        if mode == "front":
            new_index = 0
        elif mode == "back":
            new_index = len(panel_tags) - 1
        elif mode == "forward":
            new_index = max(0, index - 1)
        elif mode == "backward":
            new_index = min(len(panel_tags) - 1, index + 1)
        else:
            return
        if new_index == index:
            return
        scene_editor_push_history()
        panel_tags.pop(index)
        panel_tags.insert(new_index, tag)
        reordered = list(reversed(panel_tags))
        scene_editor_rewrite_zorder(layer, reordered)
        change_time(current_time)
        renpy.restart_interaction()

    def scene_editor_item_group(layer=None, tag=None):
        key = scene_editor_item_key(layer, tag)
        return scene_editor_group_members.get(key)

    def scene_editor_toggle_group(layer=None, tag=None):
        if layer is None:
            layer = scene_editor_selected_layer
        if tag is None:
            tag = scene_editor_selected_tag
        if tag is None:
            return
        key = scene_editor_item_key(layer, tag)
        scene_editor_push_history()
        if key in scene_editor_group_members:
            del scene_editor_group_members[key]
        else:
            scene_editor_group_members[key] = "{}:{}".format(layer, tag)
        renpy.restart_interaction()

    def scene_editor_set_tool_mode(mode):
        global scene_editor_tool_mode
        if mode == "resize":
            mode = "scale"
        if mode not in ("select", "move", "scale", "rotate"):
            return
        if scene_editor_tool_mode == mode:
            return
        scene_editor_tool_mode = mode
        scene_editor_clear_axis_constraint()
        renpy.restart_interaction()

    def scene_editor_toggle_lock_selected():
        if scene_editor_selected_tag is None:
            return
        scene_editor_toggle_lock()

    def scene_editor_handle_shortcut(name):
        if not scene_editor_shortcuts_enabled():
            return
        actions = {
            "undo": scene_editor_undo,
            "redo": scene_editor_redo,
            "copy": scene_editor_copy_selected,
            "paste": scene_editor_paste_copied,
            "duplicate": scene_editor_duplicate_selected,
            "delete": scene_editor_remove_selected,
            "forward": renpy.curry(scene_editor_reorder_selected)("forward"),
            "backward": renpy.curry(scene_editor_reorder_selected)("backward"),
            "front": renpy.curry(scene_editor_reorder_selected)("front"),
            "back": renpy.curry(scene_editor_reorder_selected)("back"),
            "group": scene_editor_group_selected,
            "ungroup": scene_editor_ungroup_selected,
            "lock_toggle": scene_editor_toggle_lock_selected,
            "move_tool": renpy.curry(scene_editor_set_tool_mode)("move"),
            "resize_tool": renpy.curry(scene_editor_set_tool_mode)("scale"),
            "rotate_tool": renpy.curry(scene_editor_set_tool_mode)("rotate"),
            "select_tool": renpy.curry(scene_editor_set_tool_mode)("select"),
            "axis_x": renpy.curry(scene_editor_toggle_axis_constraint)("x"),
            "axis_y": renpy.curry(scene_editor_toggle_axis_constraint)("y"),
            "snap_toggle": scene_editor_toggle_snap,
            "snap_cycle": scene_editor_cycle_snap_increment,
        }
        action = actions.get(name)
        if action is not None:
            action()

    def scene_editor_escape():
        if scene_editor_asset_search_active:
            scene_editor_set_asset_search_active(False)
            return
        scene_editor_set_tool_mode("select")

    def scene_editor_group_selected():
        if scene_editor_selected_tag is None:
            return
        if scene_editor_item_group() is not None:
            return
        scene_editor_toggle_group()

    def scene_editor_ungroup_selected():
        if scene_editor_selected_tag is None:
            return
        if scene_editor_item_group() is None:
            return
        scene_editor_toggle_group()

    def scene_editor_lock_selected():
        if scene_editor_selected_tag is None:
            return
        if scene_editor_item_locked():
            return
        scene_editor_toggle_lock()

    def scene_editor_unlock_selected():
        if scene_editor_selected_tag is None:
            return
        if not scene_editor_item_locked():
            return
        scene_editor_toggle_lock()

    def scene_editor_selected_key(prop):
        if scene_editor_selected_tag is None:
            return (None, scene_editor_selected_layer, prop)
        return (scene_editor_selected_tag, scene_editor_selected_layer, prop)

    def scene_editor_selected_state():
        if not scene_editor_has_selected():
            return None
        if scene_editor_selected_tag is None:
            return camera_state_org[current_scene][scene_editor_selected_layer]
        return get_image_state(scene_editor_selected_layer)[scene_editor_selected_tag]

    def scene_editor_property_available(prop):
        state = scene_editor_selected_state()
        if state is None:
            return False
        if scene_editor_selected_tag is None and prop == "child":
            return False
        return prop in state

    def scene_editor_has_selected():
        layer = scene_editor_selected_layer
        tag = scene_editor_selected_tag
        if tag is None:
            return layer in camera_state_org[current_scene]
        if scene_editor_item_hidden(layer, tag):
            return False
        return layer in image_state[current_scene] and tag in get_image_state(layer)

    def scene_editor_value_to_string(key):
        try:
            value = get_value(key, default=True)
        except Exception:
            return ""
        if key[2] == "child" and isinstance(value, tuple):
            return str(value[0])
        if key[2] == "function" and isinstance(value, tuple):
            return str(value[0])
        if check_new_position_type(value):
            if value.absolute and value.relative:
                return "{}+{}".format(value.absolute, value.relative)
            if value.absolute:
                return str(value.absolute)
            return str(value.relative)
        return str(value)

    class SceneEditorPropertyInputValue(SceneEditorInputValue):
        def __init__(self, key):
            super(SceneEditorPropertyInputValue, self).__init__()
            self.key = key
            self.buffer = None

        def get_text(self):
            if self.buffer is not None:
                return self.buffer
            return scene_editor_value_to_string(self.key)

        def set_text(self, text):
            self.buffer = text

        def enter(self):
            self.commit()
            scene_editor_finish_value_input(self.key)

        def lose_focus(self):
            self.commit()
            scene_editor_finish_value_input(self.key)

        def commit(self):
            if self.buffer is None:
                return
            old_value = get_value(self.key, default=True)
            try:
                value = scene_editor_parse_value(self.buffer, old_value)
            except Exception:
                value = None
            if value is not None and value != old_value:
                scene_editor_set_value(self.key, value, push=True)
            self.buffer = None

    def scene_editor_property_input_value(key):
        cached = scene_editor_property_input_cache.get(key)
        if cached is None or cached.key != key:
            cached = SceneEditorPropertyInputValue(key)
            scene_editor_property_input_cache[key] = cached
        return cached

    def scene_editor_is_editing_value(key):
        return scene_editor_active_value_input == key

    def scene_editor_begin_value_input(key):
        global scene_editor_active_value_input, scene_editor_asset_search_active
        scene_editor_asset_search_active = False
        scene_editor_active_value_input = key
        value = scene_editor_property_input_value(key)
        value.buffer = scene_editor_value_to_string(key)
        renpy.restart_interaction()

    def scene_editor_finish_value_input(key=None):
        global scene_editor_active_value_input
        if key is not None and scene_editor_active_value_input not in (None, key):
            return
        scene_editor_active_value_input = None
        renpy.restart_interaction()

    class SceneEditorSearchInputValue(SceneEditorInputValue):
        def __init__(self):
            super(SceneEditorSearchInputValue, self).__init__()

        def get_text(self):
            return globals().get("scene_editor_image_filter", "")

        def set_text(self, text):
            setter = globals().get("scene_editor_set_image_filter")
            if setter is not None:
                setter(text)

        def enter(self):
            scene_editor_set_asset_search_active(False)

        def lose_focus(self):
            scene_editor_set_asset_search_active(False)

    scene_editor_search_input = SceneEditorSearchInputValue()

    def scene_editor_search_input_value():
        return scene_editor_search_input

    class SceneEditorDraggableValue(renpy.Displayable):
        def __init__(self, key, **properties):
            from pygame import MOUSEMOTION
            self.key = key
            self.field_width = int(properties.pop("xsize", scene_editor_sidebar_width - 56))
            self.field_height = int(properties.pop("ysize", 28))
            super(SceneEditorDraggableValue, self).__init__(**properties)
            self.dragging = False
            self.drag_origin = 0
            self.start_value = None
            self.last_value = None
            self.drag_threshold = 4
            self.MOUSEMOTION = MOUSEMOTION

        def render(self, width, height, st, at):
            default_w = globals().get("scene_editor_property_field_width", 160)
            default_h = globals().get("scene_editor_property_field_height", 28)
            w = self.field_width or width or default_w
            h = self.field_height or height or default_h
            field = Fixed(xsize=w, ysize=h)
            text = Text(scene_editor_value_to_string(self.key), style="scene_editor_property_value_text")
            field.add(Transform(text, xalign=0.0, yalign=0.5))
            render = renpy.render(field, w, h, st, at)
            self.width, self.height = w, h
            return render

        def value_step(self, value):
            if isinstance(value, bool) or value is None:
                return None
            if isinstance(value, int):
                return 1
            if isinstance(value, float):
                magnitude = abs(value)
                if magnitude < 2:
                    return 0.01
                if magnitude < 20:
                    return 0.1
                return 1.0
            return None

        def apply_delta(self, base, delta):
            if isinstance(base, int):
                return int(round(base + delta))
            if isinstance(base, float):
                return round(base + delta, 4)
            return None

        def begin_drag(self, x):
            self.dragging = True
            self.drag_origin = x
            self.start_value = get_value(self.key, default=True)
            self.last_value = self.start_value
            scene_editor_push_history()

        def update_drag(self, x):
            if not self.dragging or self.start_value is None:
                return
            step = self.value_step(self.start_value)
            if step is None:
                return
            delta_pixels = x - self.drag_origin
            if abs(delta_pixels) < 1:
                return
            new_value = self.apply_delta(self.start_value, delta_pixels * step)
            if new_value is None or new_value == self.last_value:
                return
            self.last_value = new_value
            scene_editor_set_value(self.key, new_value, push=False, refresh=False)

        def end_drag(self, x):
            click_like = abs(x - self.drag_origin) <= self.drag_threshold
            self.dragging = False
            self.drag_origin = 0
            self.start_value = None
            self.last_value = None
            change_time(current_time)
            if click_like:
                self.prompt_edit()

        def prompt_edit(self):
            scene_editor_begin_value_input(self.key)

        def event(self, ev, x, y, st):
            if ev.type == self.MOUSEMOTION and self.dragging:
                self.update_drag(x)
                scene_editor_raise_ignore_event()
            if renpy.map_event(ev, "mousedown_1") and 0 <= x <= getattr(self, "width", 0) and 0 <= y <= getattr(self, "height", 0):
                self.begin_drag(x)
                scene_editor_raise_ignore_event()
            if renpy.map_event(ev, "mouseup_1") and self.dragging:
                self.end_drag(x)
                scene_editor_raise_ignore_event()
            if renpy.map_event(ev, "button_alternate") and 0 <= x <= getattr(self, "width", 0) and 0 <= y <= getattr(self, "height", 0):
                scene_editor_reset_value(self.key)
                scene_editor_raise_ignore_event()

        def per_interact(self):
            if self.dragging:
                renpy.redraw(self, 0)

    def scene_editor_parse_value(text, old_value):
        import ast
        text = text.strip()
        if text == "":
            return None
        if isinstance(old_value, int) and not isinstance(old_value, bool):
            return int(float(text))
        if isinstance(old_value, float):
            return round(float(text), 3)
        if isinstance(old_value, bool):
            return text.lower() in ("true", "1", "yes", "on")
        if check_new_position_type(old_value):
            return renpy.atl.position.from_any(float(text))
        if text == "None":
            return None
        try:
            return ast.literal_eval(text)
        except Exception:
            return renpy.python.py_eval(text)

    def scene_editor_set_value(key, value, push=True, refresh=True):
        if not scene_editor_has_selected():
            return
        if key[0] is not None and scene_editor_item_locked(key[1], key[0]):
            renpy.notify(_("Locked items cannot be edited"))
            return
        if push:
            scene_editor_push_history()
        set_keyframe(key, value, time=current_time)
        if key[2] == "child":
            scene_editor_child_size_cache.clear()
        if refresh:
            change_time(current_time)

    def scene_editor_toggle_value(key):
        scene_editor_push_history()
        scene_editor_set_value(key, not bool(get_value(key, default=True)), push=False)

    def scene_editor_cycle_menu_value(key):
        values = menu_props.get(key[2], [])
        if not values:
            return
        current = get_value(key, default=True)
        try:
            index = values.index(current)
        except ValueError:
            index = -1
        scene_editor_set_value(key, values[(index + 1) % len(values)], push=True)

    def scene_editor_reset_value(key):
        scene_editor_push_history()
        reset(key)
        change_time(current_time)

    def scene_editor_inline_changed(key):
        def changed(text):
            try:
                if key[2] == "child":
                    return
                old_value = get_value(key, default=True)
                if isinstance(old_value, tuple) and key[2] == "function":
                    return
                value = scene_editor_parse_value(text, old_value)
                if value is None:
                    return
                scene_editor_set_value(key, value, push=True)
            except Exception as exc:
                renpy.notify(_("Invalid value: {message}").format(message=exc))
                return
        return changed

    def scene_editor_change_layer(layer):
        if layer not in image_state[current_scene]:
            return
        scene_editor_select(layer, None)

    def scene_editor_change_scene(scene_num):
        global current_scene
        if scene_num < 0 or scene_num >= len(scene_keyframes):
            return
        current_scene = scene_num
        scene_editor_clear_runtime_caches()
        change_time(scene_keyframes[scene_num][1])

    def scene_editor_scene_time(before):
        if before:
            if current_scene == 0:
                return 0.0
            return round((scene_keyframes[current_scene - 1][1] + scene_keyframes[current_scene][1]) / 2.0, 2)
        if current_scene + 1 < len(scene_keyframes):
            return round((scene_keyframes[current_scene][1] + scene_keyframes[current_scene + 1][1]) / 2.0, 2)
        return round(scene_keyframes[current_scene][1] + 1.0, 2)

    def scene_editor_add_scene(before=False, empty=False):
        global current_scene
        insert_at = current_scene if before else current_scene + 1
        new_time = scene_editor_scene_time(before)
        source_scene = current_scene
        layers = scene_editor_current_layers()
        source_image_state = deepcopy(image_state[source_scene])
        source_image_state_org = deepcopy(image_state_org[source_scene])
        source_camera_state_org = deepcopy(camera_state_org[source_scene])
        source_zorder_list = deepcopy(zorder_list[source_scene])
        source_values = {}
        source_camera_values = {}
        if not empty:
            for layer in layers:
                source_values[layer] = {}
                source_camera_values[layer] = {}
                for prop in scene_editor_clone_props:
                    if prop in camera_state_org[source_scene][layer]:
                        source_camera_values[layer][prop] = deepcopy(get_value((None, layer, prop), scene_keyframes[source_scene][1], True, source_scene))
                for tag in get_image_state(layer, source_scene):
                    source_values[layer][tag] = {}
                    for prop in scene_editor_clone_props:
                        if prop in get_image_state(layer, source_scene)[tag]:
                            source_values[layer][tag][prop] = deepcopy(get_value((tag, layer, prop), scene_keyframes[source_scene][1], True, source_scene))
        if before and insert_at == 0:
            renpy.notify(_("Can't add a scene before Scene 0"))
            return
        scene_editor_push_history()
        scene_keyframes.insert(insert_at, (persistent._viewer_transition, new_time, None))
        image_state.insert(insert_at, {})
        image_state_org.insert(insert_at, {})
        scene_editor_captured_displayables.insert(insert_at, {})
        camera_state_org.insert(insert_at, source_camera_state_org)
        zorder_list.insert(insert_at, {})
        all_keyframes.insert(insert_at, {})
        loops.insert(insert_at, defaultdict(scene_editor_default_false))
        splines.insert(insert_at, defaultdict(dict))
        for layer in layers:
            if empty:
                image_state[insert_at][layer] = {}
                image_state_org[insert_at][layer] = {}
                scene_editor_captured_displayables[insert_at][layer] = {}
                zorder_list[insert_at][layer] = []
            else:
                image_state[insert_at][layer] = deepcopy(source_image_state[layer])
                image_state_org[insert_at][layer] = deepcopy(source_image_state_org[layer])
                scene_editor_captured_displayables[insert_at][layer] = {}
                zorder_list[insert_at][layer] = deepcopy(source_zorder_list[layer])
                for prop, value in source_camera_values[layer].items():
                    all_keyframes[insert_at][(None, layer, prop)] = [(value, new_time, persistent._viewer_warper)]
                for tag, values in source_values[layer].items():
                    for prop, value in values.items():
                        all_keyframes[insert_at][(tag, layer, prop)] = [(value, new_time, persistent._viewer_warper)]
        current_scene = insert_at
        change_time(new_time)

    def scene_editor_add_image(layer):
        filtered = scene_editor_filter_images(path=scene_editor_image_current_path)
        if filtered:
            scene_editor_apply_image_name(filtered[0][1], layer, None)
        else:
            renpy.notify(_("Select an image from the browser"))

    def scene_editor_remove_selected():
        if scene_editor_selected_tag is None:
            return
        if scene_editor_item_locked(scene_editor_selected_layer, scene_editor_selected_tag):
            renpy.notify(_("Locked items cannot be deleted"))
            return
        scene_editor_push_history()
        scene_editor_remove_image(scene_editor_selected_layer, scene_editor_selected_tag)
        scene_editor_select(scene_editor_selected_layer, None)
        scene_editor_child_size_cache.clear()
        change_time(current_time)

    def scene_editor_copy_selected():
        global scene_editor_clipboard
        if scene_editor_selected_tag is None:
            renpy.notify(_("Select an image to copy"))
            return
        state = get_image_state(scene_editor_selected_layer).get(scene_editor_selected_tag, {})
        zorder = scene_editor_default_added_zorder
        for tag, z in zorder_list[current_scene].get(scene_editor_selected_layer, []):
            if tag == scene_editor_selected_tag:
                zorder = z
                break
        scene_editor_clipboard = {
            "layer": scene_editor_selected_layer,
            "tag": scene_editor_selected_tag,
            "state": deepcopy(state),
            "zorder": zorder,
        }
        renpy.notify(_("Copied {}".format(scene_editor_selected_tag)))

    def scene_editor_paste_copied(layer=None):
        global scene_editor_selected_layer, scene_editor_selected_tag
        if scene_editor_clipboard is None:
            renpy.notify(_("Nothing copied"))
            return
        if layer is None:
            layer = scene_editor_selected_layer
        base_tag = scene_editor_clipboard.get("tag") or "image"
        new_tag = scene_editor_unique_tag(base_tag, layer)
        if new_tag is None:
            renpy.notify(_("too many same tag images is used"))
            return
        scene_editor_push_history()
        image_state[current_scene].setdefault(layer, {})[new_tag] = deepcopy(scene_editor_clipboard["state"])
        scene_editor_captured_displayables[current_scene].setdefault(layer, {})[new_tag] = None
        scene_editor_append_zorder(layer, new_tag)
        for prop, value in image_state[current_scene][layer][new_tag].items():
            if prop != "at_list":
                set_keyframe((new_tag, layer, prop), deepcopy(value), time=current_time)
        scene_editor_selected_layer = layer
        scene_editor_selected_tag = new_tag
        scene_editor_clear_runtime_caches()
        change_time(current_time)

    def scene_editor_duplicate_selected():
        if scene_editor_selected_tag is None:
            return
        scene_editor_copy_selected()
        scene_editor_paste_copied(scene_editor_selected_layer)

    def scene_editor_child_name(layer, tag):
        try:
            child = get_value((tag, layer, "child"), default=True)
            if isinstance(child, tuple):
                return child[0]
            return child
        except Exception:
            return None

    def scene_editor_checkpoint_value(key, state, prop):
        if key in all_keyframes[current_scene]:
            return all_keyframes[current_scene][key], False
        value = state.get(prop)
        if value is not None or prop == "child":
            try:
                value = get_value(key, default=False, scene_num=current_scene)
            except Exception:
                pass
            return [(value, scene_keyframes[current_scene][1], None)], False
        if prop in globals().get("not_used_by_default", ()):
            return None, False
        try:
            value = get_value(key, default=True, scene_num=current_scene)
        except Exception:
            value = property_default_value.get(prop)
        return [(value, scene_keyframes[current_scene][1], None)], True

    def scene_editor_matrix_value(args, matrix, props):
        pieces = []
        if matrix == "matrixtransform":
            offset_matrix = globals().get("OffsetMatrix", None)
            rotate_matrix = globals().get("RotateMatrix", None)
            scale_matrix = globals().get("ScaleMatrix", None)
            if offset_matrix is None or rotate_matrix is None or scale_matrix is None:
                return None
            for i in range(0, len(props), 3):
                prop = props[i].split("_")[-1]
                values = args[i:i + 3]
                if prop.startswith("offset"):
                    pieces.append(offset_matrix(*values))
                elif prop.startswith("rotate"):
                    pieces.append(rotate_matrix(*values))
                elif prop.startswith("scale"):
                    pieces.append(scale_matrix(*values))
        else:
            matrix_types = {
                "invert": globals().get("InvertMatrix", None),
                "contrast": globals().get("ContrastMatrix", None),
                "saturate": globals().get("SaturationMatrix", None),
                "bright": globals().get("BrightnessMatrix", None),
                "hue": globals().get("HueMatrix", None),
            }
            for prop, value in zip(props, args):
                matrix_type = matrix_types.get(prop.split("_")[-1])
                if matrix_type is not None:
                    pieces.append(matrix_type(value))
        if not pieces:
            return None
        value = pieces[0]
        for piece in pieces[1:]:
            value = value * piece
        return value

    def scene_editor_transform_checkpoints(layer, tag, state):
        t = scene_keyframes[current_scene][1]
        checkpoints = {"at_list": [(state.get("at_list", []), t, None)]}
        props_use_default = []
        for prop in state:
            if prop in ("at_list", "props_use_default", "_captured_raw"):
                continue
            if tag is None and prop == "child":
                continue
            if prop in ("xpos", "ypos"):
                for grouped_prop in ("xaround", "yaround", "radius", "angle"):
                    if (tag, layer, grouped_prop) in all_keyframes[current_scene]:
                        break
                else:
                    grouped_prop = None
                if grouped_prop is not None:
                    continue
            if prop in ("xaround", "yaround", "radius", "angle"):
                for grouped_prop in ("xpos", "ypos"):
                    if (tag, layer, grouped_prop) in all_keyframes[current_scene]:
                        break
                else:
                    for grouped_prop in ("xaround", "yaround", "radius", "angle"):
                        if (tag, layer, grouped_prop) in all_keyframes[current_scene]:
                            break
                    else:
                        grouped_prop = None
                if grouped_prop is None:
                    continue
            key = (tag, layer, prop)
            prop_checkpoints, used_default = scene_editor_checkpoint_value(key, state, prop)
            if prop_checkpoints is None:
                continue
            checkpoints[prop] = prop_checkpoints
            if used_default:
                props_use_default.append(prop)
        checkpoints["props_use_default"] = [(props_use_default, t, None)]
        included_groups = {}
        for prop in list(checkpoints.keys()):
            check_result = check_props_group((tag, layer, prop), current_scene)
            if check_result is None:
                continue
            group_name, group_props = check_result
            if group_name == "focusing" or group_name in included_groups:
                continue
            if any(group_prop not in checkpoints for group_prop in group_props):
                continue
            args = [checkpoints[group_prop] for group_prop in group_props]
            group_checkpoints = []
            for cs in zip(*args):
                value = tuple(c[0] for c in cs)
                if group_name in ("matrixtransform", "matrixcolor"):
                    matrix_args = value
                    value = scene_editor_matrix_value(matrix_args, group_name, group_props)
                    if value is None:
                        value = renpy.python.py_eval(generate_matrix_strings(matrix_args, group_name, group_props))
                group_checkpoints.append((value, cs[0][1], cs[0][2]))
            included_groups[group_name] = (group_props, group_checkpoints)
        for group_name, (group_props, group_checkpoints) in included_groups.items():
            for group_prop in group_props:
                if group_prop in checkpoints:
                    del checkpoints[group_prop]
            checkpoints[group_name] = group_checkpoints
        if any(prop in checkpoints for prop in ("radius", "angle")):
            props_use_default_entry = checkpoints.get("props_use_default", [(None, None, None)])[0][0]
            for around_prop in ("xaround", "yaround"):
                if around_prop in checkpoints:
                    continue
                default_value = state.get(around_prop)
                if default_value is None:
                    default_value = property_default_value.get(around_prop, 0)
                    if props_use_default_entry is not None:
                        props_use_default_entry.append(around_prop)
                checkpoints[around_prop] = [(default_value, t, None)]
        if "around" in checkpoints:
            if (tag, layer, "radius") not in all_keyframes[current_scene] and (tag, layer, "angle") not in all_keyframes[current_scene]:
                checkpoints["around"] = [((state.get("xaround", 0), state.get("yaround", 0)), t, None)]
        if tag is not None:
            if persistent._viewer_focusing and perspective_enabled(layer, current_scene, time=t):
                if "blur" in checkpoints:
                    del checkpoints["blur"]
            else:
                for prop in ("focusing", "dof"):
                    if prop in checkpoints:
                        del checkpoints[prop]
        return checkpoints

    def scene_editor_build_child_displayable(name, at_list=None):
        if not name:
            return None
        child = None
        getter = globals().get("get_widget", None)
        if callable(getter):
            try:
                child = getter(name, current_time, 0, at_list or [])
            except Exception:
                child = None
        if child is None:
            try:
                if hasattr(renpy, "displayable"):
                    child = renpy.displayable(name)
                else:
                    child = renpy.easy.displayable(name)
                child = scene_editor_apply_at_list(child, at_list or [])
                child = SceneEditorFixedTimeDisplayable(child, current_time, 0)
            except Exception:
                child = None
        return child

    def scene_editor_at_list_cache_key(at_list):
        if not at_list:
            return ()
        key = []
        for entry in at_list:
            try:
                name, kwargs = entry
                key.append((name, tuple(sorted((kwargs or {}).items()))))
            except Exception:
                key.append(repr(entry))
        return tuple(key)

    def scene_editor_asset_thumbnail(name, width=128, height=88):
        cache_key = (name, width, height)
        if cache_key in scene_editor_thumbnail_cache:
            return scene_editor_thumbnail_cache[cache_key]
        try:
            child = scene_editor_build_child_displayable(name, None)
        except Exception:
            child = None
        if child is None:
            thumb = Solid("#0F1628", xsize=width, ysize=height)
            scene_editor_thumbnail_cache[cache_key] = thumb
            return thumb
        thumb = Transform(child, fit="contain", xsize=width, ysize=height)
        try:
            renpy.render(thumb, width, height, 0, 0)
        except Exception:
            thumb = Solid("#0F1628", xsize=width, ysize=height)
        scene_editor_thumbnail_cache[cache_key] = thumb
        return thumb

    def scene_editor_apply_at_list(child, at_list):
        if not at_list:
            return child
        for entry in at_list:
            try:
                name, kwargs = entry
                transform = getattr(renpy.store, name)
                child = transform(child=child, **(kwargs or {}))
            except (AttributeError, TypeError, ValueError) as exc:
                err_key = (repr(entry), type(exc).__name__, str(exc))
                if err_key not in scene_editor_transform_apply_error_cache:
                    scene_editor_transform_apply_error_cache.add(err_key)
                    renpy.notify(_("Could not apply transform {name}: {message}").format(name=entry, message=exc))
        return child

    def scene_editor_number(value, fallback=0):
        if value is None:
            return fallback
        if check_new_position_type(value):
            return value
        try:
            return float(value)
        except Exception:
            return fallback

    def scene_editor_transform_kwargs(layer, tag):
        rv = {}
        for prop in scene_editor_transform_preview_props:
            try:
                value = get_value((tag, layer, prop), default=True)
            except Exception:
                value = None
            if value is not None:
                rv[prop] = value
        return rv

    def scene_editor_camera_kwargs(layer):
        return scene_editor_transform_kwargs(layer, None)

    def scene_editor_ordered_tags(layer):
        state = get_image_state(layer)
        seen = set()
        ordered = []
        for tag, z in zorder_list[current_scene].get(layer, []):
            if tag in state and tag not in seen:
                ordered.append((tag, z))
                seen.add(tag)
        for tag in state:
            if tag not in seen:
                ordered.append((tag, scene_editor_default_added_zorder))
        return ordered

    def scene_editor_render_item(layer, tag, st=0, at=0):
        state = get_image_state(layer).get(tag, {})
        if state.get("_captured_raw"):
            try:
                return scene_editor_captured_displayables[current_scene].get(layer, {}).get(tag)
            except Exception:
                return None
        child_name = scene_editor_child_name(layer, tag)
        child = scene_editor_build_child_displayable(child_name, state.get("at_list"))
        if child is None:
            try:
                child = scene_editor_captured_displayables[current_scene].get(layer, {}).get(tag)
            except Exception:
                child = None
        if child is None:
            return None
        return Transform(child, **scene_editor_transform_kwargs(layer, tag))

    def scene_editor_preview_displayable(st=0, at=0):
        scene = Fixed(xsize=config.screen_width, ysize=config.screen_height)
        count = 0
        scene_checkpoints = tuple(scene_keyframes)
        preview_x, preview_y, preview_zoom = scene_editor_preview_transform_values()
        preview_zorder = [{} for _scene in zorder_list]
        for layer in scene_editor_current_layers():
            state = get_image_state(layer)
            if not state:
                continue
            layer_image_points = {}
            render_tags = scene_editor_layer_render_tags(layer)
            for tag in render_tags:
                layer_image_points[tag] = scene_editor_transform_checkpoints(layer, tag, state[tag])
                count += 1
            camera_state = camera_state_org[current_scene].get(layer, {})
            camera_checkpoints = scene_editor_transform_checkpoints(layer, None, camera_state)
            loop = defaultdict(scene_editor_default_false)
            spline = defaultdict(dict)
            preview_zorder[current_scene][layer] = [(tag, index) for index, tag in enumerate(render_tags)]
            scene.add(Transform(
                Transform(function=renpy.curry(camera_transform)(
                camera_check_points=camera_checkpoints,
                image_check_points=layer_image_points,
                scene_checkpoints=scene_checkpoints,
                viewer_check_points=camera_checkpoints,
                zorder_list=preview_zorder,
                loop=loop,
                spline=spline,
                time=current_time,
                scene_num=current_scene,
                layer=layer)),
                zoom=preview_zoom,
                xpos=preview_x,
                ypos=preview_y))
        if not count:
            scene.add(Transform(Text("SceneEditor captured no drawable images", color="#FFFFFF", size=30), xpos=40, ypos=40))
        return scene, count

    def scene_editor_to_pixel(value, size):
        if check_new_position_type(value):
            return value.absolute + value.relative * size
        if isinstance(value, float):
            if -1.0 <= value <= 1.0:
                return value * size
            return value
        if value is None:
            return 0
        return value

    def scene_editor_stage_item_rect(layer, tag, st=0, at=0):
        xpos = scene_editor_to_pixel(get_value((tag, layer, "xpos"), default=True), config.screen_width)
        ypos = scene_editor_to_pixel(get_value((tag, layer, "ypos"), default=True), config.screen_height)
        xanchor = scene_editor_to_pixel(get_value((tag, layer, "xanchor"), default=True), 1.0)
        yanchor = scene_editor_to_pixel(get_value((tag, layer, "yanchor"), default=True), 1.0)
        xoffset = get_value((tag, layer, "xoffset"), default=True)
        yoffset = get_value((tag, layer, "yoffset"), default=True)
        zoom = get_value((tag, layer, "zoom"), default=True)
        xzoom = get_value((tag, layer, "xzoom"), default=True)
        yzoom = get_value((tag, layer, "yzoom"), default=True)
        if zoom is None:
            zoom = 1.0
        if xzoom is None:
            xzoom = 1.0
        if yzoom is None:
            yzoom = 1.0
        if xoffset is None:
            xoffset = 0
        if yoffset is None:
            yoffset = 0
        width = 160
        height = 160
        name = scene_editor_child_name(layer, tag)
        if name:
            state = get_image_state(layer).get(tag, {})
            size_key = (name, scene_editor_at_list_cache_key(state.get("at_list")), config.screen_width, config.screen_height)
            cached_size = scene_editor_child_size_cache.get(size_key)
            if cached_size is not None:
                width, height = cached_size
            else:
                try:
                    child = scene_editor_build_child_displayable(name, state.get("at_list"))
                    cr = renpy.render(child, config.screen_width, config.screen_height, st, at)
                    width, height = cr.get_size()
                    scene_editor_child_size_cache[size_key] = (width, height)
                except Exception:
                    pass
        width = max(24, abs(width * zoom * xzoom))
        height = max(24, abs(height * zoom * yzoom))
        x = xpos + xoffset - width * xanchor
        y = ypos + yoffset - height * yanchor
        return x, y, width, height

    def scene_editor_item_rect(layer, tag, st=0, at=0):
        sx, sy, sw, sh = scene_editor_stage_item_rect(layer, tag, st, at)
        offset_x, offset_y, scale = scene_editor_canvas_offsets()
        preview_x, preview_y, preview_zoom = scene_editor_preview_transform_values()
        return (
            offset_x + (preview_x + sx * preview_zoom) * scale,
            offset_y + (preview_y + sy * preview_zoom) * scale,
            sw * preview_zoom * scale,
            sh * preview_zoom * scale,
        )

    def scene_editor_selected_screen_rect(st=0, at=0):
        if scene_editor_selected_tag is None:
            return None
        if not scene_editor_has_selected():
            return None
        return scene_editor_item_rect(scene_editor_selected_layer, scene_editor_selected_tag, st, at)

    def scene_editor_item_hit_opaque(layer, tag, stage_x, stage_y, st=0, at=0):
        if not hasattr(renpy, "is_pixel_opaque"):
            return True
        displayable = scene_editor_render_item(layer, tag, st, at)
        if displayable is None:
            return False
        try:
            return renpy.is_pixel_opaque(
                displayable,
                config.screen_width,
                config.screen_height,
                st,
                at,
                int(stage_x),
                int(stage_y),
            )
        except Exception:
            return True

    def scene_editor_hit_test(x, y, st=0, at=0):
        stage_x, stage_y = scene_editor_screen_to_stage(x, y)
        fallback_layer = None
        fallback_tag = None
        for layer in reversed(scene_editor_current_layers()):
            state = get_image_state(layer)
            for tag in scene_editor_layer_panel_tags(layer):
                if tag not in state:
                    continue
                if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
                    continue
                rx, ry, rw, rh = scene_editor_item_rect(layer, tag, st, at)
                if x >= rx and x <= rx + rw and y >= ry and y <= ry + rh:
                    if fallback_tag is None:
                        fallback_layer = layer
                        fallback_tag = tag
                    if scene_editor_item_hit_opaque(layer, tag, stage_x, stage_y, st, at):
                        return layer, tag
        return fallback_layer, fallback_tag

    def scene_editor_set_position(layer, tag, x, y, refresh=True):
        if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        x = scene_editor_snap_value(x)
        y = scene_editor_snap_value(y)
        set_keyframe((tag, layer, "xpos"), int(round(x)), time=current_time)
        set_keyframe((tag, layer, "ypos"), int(round(y)), time=current_time)
        if refresh:
            change_time(current_time)

    def scene_editor_set_scale(layer, tag, xzoom, yzoom, refresh=True):
        if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        set_keyframe((tag, layer, "xzoom"), max(0.01, round(float(xzoom), 3)), time=current_time)
        set_keyframe((tag, layer, "yzoom"), max(0.01, round(float(yzoom), 3)), time=current_time)
        if refresh:
            change_time(current_time)

    def scene_editor_set_rotate(layer, tag, rotate, refresh=True):
        if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        set_keyframe((tag, layer, "rotate"), round(float(rotate), 2), time=current_time)
        if refresh:
            change_time(current_time)

    def open_scene_editor():
        global current_time, current_scene, scene_keyframes, zorder_list, sound_keyframes, all_keyframes, playing, in_editor, loops, splines
        global scene_editor_selected_layer, scene_editor_selected_tag, scene_editor_restore_not_included_layer
        global not_included_layer
        if not config.developer:
            return
        playing = False
        scene_editor_clear_runtime_caches(assets=True)
        current_time = 0.0
        current_scene = 0
        loops = [defaultdict(scene_editor_default_false)]
        splines = [defaultdict(dict)]
        sound_keyframes = {}
        all_keyframes = [{}]
        zorder_list = [{}]
        scene_editor_restore_not_included_layer = not_included_layer
        not_included_layer = ()
        for layer in scene_editor_get_layers():
            zorder_list[current_scene][layer] = renpy.get_zorder_list(layer)
        scene_keyframes = [(None, 0, None)]
        if persistent._viewer_transition is None:
            persistent._viewer_transition = default_transition
        if persistent._viewer_warper is None:
            persistent._viewer_warper = default_warper
        if persistent._viewer_rot is None:
            persistent._viewer_rot = False
        if persistent._viewer_focusing is None:
            persistent._viewer_focusing = False
        persistent._viewer_sideview = False
        if persistent._time_range is None:
            persistent._time_range = time_range
        if persistent._viewer_channel_list is None:
            persistent._viewer_channel_list = default_channel_list
        for channel in persistent._viewer_channel_list:
            sound_keyframes[channel] = {}
        renpy.store._viewers.at_clauses_flag = False
        scene_editor_init_state()
        scene_editor_history[:] = []
        scene_editor_redo_stack[:] = []
        layers = scene_editor_current_layers()
        if not layers:
            not_included_layer = scene_editor_restore_not_included_layer
            renpy.notify(_("No editable layers found"))
            return
        scene_editor_selected_layer = "master" if "master" in image_state[current_scene] else layers[0]
        scene_editor_selected_tag = None
        in_editor = True
        window_org = renpy.store._window
        skipping_org = renpy.store._skipping
        quick_menu_org = renpy.store.quick_menu
        renpy.store._window = False
        renpy.store._skipping = False
        renpy.store.quick_menu = False
        try:
            change_time(0)
            renpy.call_screen("_scene_photo_editor")
        finally:
            renpy.store._skipping = skipping_org
            renpy.store._window = window_org
            renpy.store.quick_menu = quick_menu_org
            not_included_layer = scene_editor_restore_not_included_layer
            in_editor = False
