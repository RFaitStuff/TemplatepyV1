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
    scene_editor_fast_drag_preview = True
    scene_editor_precise_hit_testing = False
    scene_editor_preview_mode = False
    scene_editor_ui_scene_visible = True
    scene_editor_tree_tab = "Scene"
    scene_editor_bottom_panel_tab = "Assets"
    scene_editor_layers_view = "Scenes"
    scene_editor_tree_expanded = set()
    scene_editor_drag_redraw_interval = 0.016
    scene_editor_snap_enabled = False
    scene_editor_snap_increment = scene_editor_default_snap_increment if "scene_editor_default_snap_increment" in globals() else 16
    scene_editor_asset_search_active = False
    scene_editor_active_value_input = None
    scene_editor_highlight_until = 0.0
    scene_editor_ui_layer = "__ui_scene__"
    scene_editor_ui_groups = ("dialogue_box", "choices", "stats", "time", "indicators", "overlays")
    scene_editor_ui_group_labels = {
        "dialogue_box": "Dialogue Box",
        "choices": "Choices",
        "stats": "Stats",
        "time": "Time / Day",
        "indicators": "Indicators",
        "overlays": "Overlays",
    }
    scene_editor_ui_elements = [{}]
    scene_editor_ui_group_visibility = dict((group, True) for group in scene_editor_ui_groups)
    scene_editor_ui_group_locks = set()
    scene_editor_ui_counter = 0
    scene_editor_ui_captured_displayables = [{}]
    scene_editor_image_fallback_paths = {
        "ui_hud_characters": "assets/images/UI/HUD/Characters.png",
        "ui_hud_characters_love": "assets/images/UI/HUD/Characters_Love.png",
        "ui_hud_characters_lust": "assets/images/UI/HUD/Characters_Lust.png",
        "ui_hud_location": "assets/images/UI/HUD/Location.png",
    }
    scene_editor_project_name = "live_studio_project"
    scene_editor_current_route_id = "route_main"
    scene_editor_route_counter = 1
    scene_editor_frame_counter = 0
    scene_editor_frame_records = []
    scene_editor_dialogue_scenes = [{}]
    scene_editor_dialogue_entry_counter = 0
    scene_editor_selected_dialogue_entry_id = None
    scene_editor_project_slot = "autosave"
    scene_editor_export_cache = ""
    scene_editor_last_written_file = ""
    scene_editor_dialogue_entry_types = ("line", "narration", "choice", "script", "stat", "reaction", "jump", "label", "condition")
    scene_editor_frame_insert_step = 1.0
    scene_editor_export_visuals = True
    scene_editor_export_ui = True
    scene_editor_export_dialogue = True
    scene_editor_export_scene_clears = True
    scene_editor_export_hidden_ui = False
    scene_editor_preview_dialogue = True
    scene_editor_text_props = ("text", "bound_variable", "color", "background")
    scene_editor_ui_property_defaults = {
        "kind": "text",
        "group": "overlays",
        "text": "New Text",
        "bound_variable": "",
        "background": "#00000000",
        "image": "",
        "visible": True,
        "xpos": 0.5,
        "ypos": 0.5,
        "xanchor": 0.5,
        "yanchor": 0.5,
        "xoffset": 0,
        "yoffset": 0,
        "zoom": 1.0,
        "xzoom": 1.0,
        "yzoom": 1.0,
        "rotate": 0.0,
        "alpha": 1.0,
        "size": 32,
        "color": "#FFFFFF",
        "xsize": 220,
        "ysize": 48,
        "zorder": 0,
    }
    scene_editor_ui_property_groups = (
        ("Core", (
            ("Kind", "kind"),
            ("Group", "group"),
            ("Visible", "visible"),
            ("Text", "text"),
            ("Value", "bound_variable"),
            ("Background", "background"),
            ("Image", "image"),
            ("Xpos", "xpos"),
            ("Ypos", "ypos"),
            ("Width", "xsize"),
            ("Height", "ysize"),
            ("Zoom", "zoom"),
            ("SizeX", "xzoom"),
            ("SizeY", "yzoom"),
            ("Rotate", "rotate"),
            ("Alpha", "alpha"),
        )),
        ("Appearance", (
            ("Font Size", "size"),
            ("Color", "color"),
            ("XAnchor", "xanchor"),
            ("YAnchor", "yanchor"),
            ("XOffset", "xoffset"),
            ("YOffset", "yoffset"),
        )),
    )
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

    def scene_editor_set_tree_tab(tab):
        global scene_editor_tree_tab
        if tab == "Frames":
            tab = "Frame"
        if tab not in ("Scene", "Frame"):
            return
        scene_editor_tree_tab = tab
        renpy.restart_interaction()

    def scene_editor_set_bottom_panel_tab(tab):
        global scene_editor_bottom_panel_tab
        if tab not in ("Assets", "Dialogue"):
            tab = "Assets"
        scene_editor_bottom_panel_tab = tab
        renpy.restart_interaction()

    def scene_editor_set_preview_mode(value=True):
        global scene_editor_preview_mode
        scene_editor_preview_mode = bool(value)
        renpy.restart_interaction()

    def scene_editor_toggle_preview_mode():
        scene_editor_set_preview_mode(not scene_editor_preview_mode)

    def scene_editor_set_layers_view(view):
        global scene_editor_layers_view, scene_editor_selected_layer, scene_editor_selected_tag
        if view not in ("Scenes", "UI"):
            return
        scene_editor_layers_view = view
        if view == "UI":
            scene_editor_selected_layer = scene_editor_ui_layer
            scene_editor_selected_tag = None
        elif scene_editor_selected_layer == scene_editor_ui_layer:
            layers = scene_editor_current_layers()
            scene_editor_selected_layer = layers[0] if layers else "master"
            scene_editor_selected_tag = None
        renpy.restart_interaction()

    def scene_editor_toggle_ui_scene_visible():
        global scene_editor_ui_scene_visible
        scene_editor_ui_scene_visible = not scene_editor_ui_scene_visible
        renpy.restart_interaction()

    def scene_editor_tree_key(kind, value=None, scene_num=None):
        if scene_num is None:
            scene_num = current_scene
        return (kind, value, scene_num)

    def scene_editor_tree_is_expanded(kind, value=None, scene_num=None):
        key = scene_editor_tree_key(kind, value, scene_num)
        return key in scene_editor_tree_expanded

    def scene_editor_toggle_tree_expanded(kind, value=None, scene_num=None):
        if scene_num is None:
            scene_num = current_scene
        key = scene_editor_tree_key(kind, value, scene_num)
        if key in scene_editor_tree_expanded:
            scene_editor_tree_expanded.remove(key)
        else:
            scene_editor_tree_expanded.add(key)
        renpy.restart_interaction()

    def scene_editor_frame_label(scene_num):
        scene_editor_ensure_frame_records()
        if scene_num < 0 or scene_num >= len(scene_editor_frame_records):
            return "Frame {}".format(scene_num)
        return scene_editor_frame_records[scene_num].get("name", "Frame {}".format(scene_num))

    def scene_editor_frame_has_dialogue(scene_num):
        scene = scene_editor_ensure_dialogue_scene(scene_num)
        return bool(scene.get("entries", []))

    def scene_editor_current_layers(scene_num=None):
        if scene_num is None:
            scene_num = current_scene
        rv = []
        for layer in config.layers:
            if not isinstance(layer, str):
                continue
            state = get_image_state(layer, scene_num)
            if state:
                rv.append(layer)
        return rv

    def scene_editor_is_ui_layer(layer=None):
        if layer is None:
            layer = scene_editor_selected_layer
        return layer == scene_editor_ui_layer

    def scene_editor_ensure_ui_scene(scene_num=None):
        if scene_num is None:
            scene_num = current_scene
        while len(scene_editor_ui_elements) <= scene_num:
            scene_editor_ui_elements.append({})
        scene_editor_ui_elements[scene_num] = scene_editor_normalize_ui_scene(scene_editor_ui_elements[scene_num])
        return scene_editor_ui_elements[scene_num]

    def scene_editor_ui_scene():
        return scene_editor_ensure_ui_scene(current_scene)

    def scene_editor_ui_group_label(group):
        return scene_editor_ui_group_labels.get(group, str(group).replace("_", " ").title())

    def scene_editor_ui_group_visible(group):
        return bool(scene_editor_ui_group_visibility.get(group, True))

    def scene_editor_toggle_ui_group(group):
        if group not in scene_editor_ui_groups:
            return
        scene_editor_ui_group_visibility[group] = not scene_editor_ui_group_visible(group)
        renpy.restart_interaction()

    def scene_editor_ui_group_locked(group):
        return group in scene_editor_ui_group_locks

    def scene_editor_toggle_ui_group_lock(group):
        if group not in scene_editor_ui_groups:
            return
        scene_editor_push_history()
        tags = [tag for tag in scene_editor_ui_layer_panel_tags() if (scene_editor_ui_element(tag) or {}).get("group") == group]
        if scene_editor_ui_group_locked(group):
            scene_editor_ui_group_locks.discard(group)
            for tag in tags:
                scene_editor_locked_items.discard(scene_editor_item_key(scene_editor_ui_layer, tag))
        else:
            scene_editor_ui_group_locks.add(group)
            for tag in tags:
                scene_editor_locked_items.add(scene_editor_item_key(scene_editor_ui_layer, tag))
        renpy.restart_interaction()

    def scene_editor_ui_choice_values(prop):
        if prop == "kind":
            return ("text", "value", "panel")
        if prop == "group":
            return scene_editor_ui_groups
        return ()

    def scene_editor_cycle_ui_choice(key):
        values = scene_editor_ui_choice_values(key[2])
        if not values:
            return
        current = scene_editor_get_property_value(key, default=True)
        try:
            index = values.index(current)
        except ValueError:
            index = -1
        scene_editor_set_value(key, values[(index + 1) % len(values)], push=True)

    def scene_editor_ui_element(tag=None):
        if tag is None:
            tag = scene_editor_selected_tag
        if tag is None:
            return None
        return scene_editor_ui_scene().get(tag)

    def scene_editor_ui_tags(include_hidden=True):
        items = []
        for tag, element in scene_editor_ui_scene().items():
            if not include_hidden:
                if not element.get("visible", True) or not scene_editor_ui_group_visible(element.get("group", "overlays")):
                    continue
            items.append((tag, element.get("zorder", 0)))
        items.sort(key=lambda item: (item[1], item[0]))
        return [tag for tag, _z in items]

    def scene_editor_ui_layer_panel_tags():
        tags = scene_editor_ui_tags(include_hidden=True)
        tags.reverse()
        return tags

    def scene_editor_ui_unique_tag(base="ui"):
        global scene_editor_ui_counter
        scene_editor_ui_counter += 1
        candidate = "{}_{}".format(base, scene_editor_ui_counter)
        while candidate in scene_editor_ui_scene():
            scene_editor_ui_counter += 1
            candidate = "{}_{}".format(base, scene_editor_ui_counter)
        return candidate

    def scene_editor_ui_default_element(kind="text", group="overlays"):
        element = deepcopy(scene_editor_ui_property_defaults)
        element["kind"] = kind
        element["group"] = group if group in scene_editor_ui_groups else "overlays"
        if kind == "value":
            element["text"] = "Value"
            element["bound_variable"] = "variable.name"
        elif kind == "panel":
            element["text"] = ""
            element["background"] = "#00000080"
        elif kind == "screen":
            element["text"] = ""
            element["background"] = "#00000000"
            element["selectable"] = False
        return element

    def scene_editor_normalize_ui_element(element):
        if not isinstance(element, dict):
            element = {}
        kind = element.get("kind", "text")
        group = element.get("group", "overlays")
        defaults = scene_editor_ui_default_element(kind, group)
        defaults.update(element)
        if defaults.get("kind") not in ("text", "value", "panel", "screen"):
            defaults["kind"] = "text"
        if defaults.get("group") not in scene_editor_ui_groups:
            defaults["group"] = "overlays"
        return defaults

    def scene_editor_normalize_ui_scene(ui_scene):
        if not isinstance(ui_scene, dict):
            return {}
        for tag in list(ui_scene.keys()):
            ui_scene[tag] = scene_editor_normalize_ui_element(ui_scene[tag])
        return ui_scene

    def scene_editor_add_ui_element(kind="text", group="overlays"):
        global scene_editor_selected_layer, scene_editor_selected_tag
        if kind not in ("text", "value", "panel"):
            kind = "text"
        scene_editor_push_history()
        tag = scene_editor_ui_unique_tag(kind)
        scene_editor_ui_scene()[tag] = scene_editor_ui_default_element(kind, group)
        scene_editor_selected_layer = scene_editor_ui_layer
        scene_editor_selected_tag = tag
        scene_editor_clear_runtime_caches()
        change_time(current_time)

    def scene_editor_remove_ui_element(tag):
        if tag in scene_editor_ui_scene():
            del scene_editor_ui_scene()[tag]
        try:
            scene_editor_ui_captured_displayables[current_scene].pop(tag, None)
        except Exception:
            pass
        key = scene_editor_item_key(scene_editor_ui_layer, tag)
        scene_editor_locked_items.discard(key)
        scene_editor_hidden_items.discard(key)
        if key in scene_editor_group_members:
            del scene_editor_group_members[key]

    def scene_editor_get_property_value(key, default=False):
        tag, layer, prop = key
        if scene_editor_is_ui_layer(layer):
            element = scene_editor_ui_scene().get(tag, {})
            if prop in element:
                return element[prop]
            if default:
                return scene_editor_ui_property_defaults.get(prop)
            return None
        return get_value(key, default=default)

    def scene_editor_set_property_value(key, value):
        tag, layer, prop = key
        if scene_editor_is_ui_layer(layer):
            element = scene_editor_ui_scene().setdefault(tag, scene_editor_ui_default_element())
            element[prop] = value
            return
        set_keyframe(key, value, time=current_time)

    def scene_editor_direct_number(value, fallback=0):
        if value is None:
            return fallback
        try:
            return float(value)
        except Exception:
            return fallback

    def scene_editor_reset_property_value(key):
        tag, layer, prop = key
        if scene_editor_is_ui_layer(layer):
            default = scene_editor_ui_property_defaults.get(prop)
            if default is not None:
                scene_editor_ui_scene().setdefault(tag, scene_editor_ui_default_element())[prop] = deepcopy(default)
            return
        reset(key)

    def scene_editor_ui_display_text(element):
        if element.get("kind") == "value":
            binding = element.get("bound_variable", "")
            if binding:
                try:
                    return str(renpy.python.py_eval(binding))
                except Exception:
                    return "[" + binding + "]"
        return element.get("text", "")

    def scene_editor_hud_screen_displayable():
        hud = Fixed(xsize=config.screen_width, ysize=config.screen_height)
        time_panel = Fixed(xsize=250, ysize=118)
        time_panel.add(Solid("#000000a0", xsize=250, ysize=118))
        time_panel.add(Transform(Text(scene_editor_ui_display_text({"kind": "value", "bound_variable": '"{} - Day {}".format(weekday_name(), day)'}), size=22, color="#ffffff"), xpos=16, ypos=12))
        time_panel.add(Transform(Text(scene_editor_ui_display_text({"kind": "value", "bound_variable": 'convert_to_12hr_format(time)'}), size=22, color="#ffd27a"), xpos=16, ypos=44))
        time_panel.add(Transform(Text(scene_editor_ui_display_text({"kind": "value", "bound_variable": '"Stamina: {}/{}".format(stamina, get_max_stamina())'}), size=20, color="#aef0ae"), xpos=16, ypos=74))
        hud.add(Transform(time_panel, xpos=20, ypos=20))

        location_bar = scene_editor_build_child_displayable("ui_hud_location", None)
        if location_bar is not None:
            hud.add(Transform(location_bar, fit="contain", xsize=760, ysize=98, xpos=0.5, ypos=-6, xanchor=0.5, yanchor=0.0))
        hud.add(Transform(Text(scene_editor_ui_display_text({"kind": "value", "bound_variable": "location_name()"}), size=28, color="#ffffff", outlines=[(2, "#000000", 0, 0)], xsize=700, text_align=0.5), xpos=0.5, ypos=22, xanchor=0.5))
        objective = scene_editor_ui_display_text({"kind": "value", "bound_variable": 'quest_target_for_current_location() or ""'})
        if objective:
            hud.add(Transform(Text(objective, size=16, color="#ffd27a", xsize=720, text_align=0.5), xpos=0.5, ypos=96, xanchor=0.5))

        hud.add(Transform(Text("Quests", size=16, color="#ffffff"), xpos=config.screen_width - 300, ypos=29))
        hud.add(Transform(Text("Inventory", size=16, color="#ffffff"), xpos=config.screen_width - 220, ypos=29))
        chars = scene_editor_build_child_displayable("ui_hud_characters", None)
        if chars is not None:
            hud.add(Transform(chars, fit="contain", xsize=110, ysize=110, xpos=config.screen_width - 130, ypos=7))
        return hud

    def scene_editor_screen_fallback_displayable(screen_name):
        if screen_name == "hud":
            return scene_editor_hud_screen_displayable()
        return None

    def scene_editor_ui_displayable(tag):
        element = scene_editor_ui_element(tag)
        if not element:
            return None
        if element.get("group") in ("dialogue_box", "choices") and (not scene_editor_preview_dialogue or not scene_editor_current_dialogue_visible()):
            return None
        if scene_editor_item_hidden(scene_editor_ui_layer, tag):
            return None
        if not element.get("visible", True):
            return None
        if not scene_editor_ui_group_visible(element.get("group", "overlays")):
            return None
        if element.get("kind") == "screen":
            try:
                child = scene_editor_ui_captured_displayables[current_scene].get(tag)
            except Exception:
                child = None
            if child is not None:
                return SceneEditorFixedTimeDisplayable(child, current_time, 0)
            screen_name = element.get("source_screen")
            if screen_name:
                try:
                    screen = renpy.get_screen(screen_name)
                    if screen is not None:
                        return SceneEditorFixedTimeDisplayable(screen, current_time, 0)
                except Exception:
                    pass
                fallback = scene_editor_screen_fallback_displayable(screen_name)
                if fallback is not None:
                    return fallback
            return None
        image_name = element.get("image", "")
        if image_name:
            try:
                child = scene_editor_build_child_displayable(image_name, None)
            except Exception:
                child = None
            if child is None:
                child = Solid(element.get("background", "#00000000"), xsize=int(element.get("xsize", 220)), ysize=int(element.get("ysize", 48)))
            else:
                child = Transform(child, fit="contain", xsize=int(element.get("xsize", 220)), ysize=int(element.get("ysize", 48)))
        elif element.get("kind") == "panel":
            child = Solid(element.get("background", "#00000080"), xsize=int(element.get("xsize", 220)), ysize=int(element.get("ysize", 48)))
        else:
            child = Text(scene_editor_ui_display_text(element), size=int(element.get("size", 32)), color=element.get("color", "#FFFFFF"), xsize=element.get("xsize", None))
        kwargs = {}
        for prop in ("xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset", "zoom", "xzoom", "yzoom", "rotate", "alpha"):
            if prop in element:
                kwargs[prop] = element[prop]
        return Transform(child, **kwargs)

    def scene_editor_dialogue_preview_displayable():
        if not scene_editor_preview_dialogue or not scene_editor_current_dialogue_visible():
            return None
        entries = scene_editor_dialogue_entries()
        if not entries:
            return None
        entry = scene_editor_dialogue_entry() or entries[0]
        if entry.get("type") not in ("line", "choice", "reaction"):
            return None
        speaker = scene_editor_character_label(entry.get("speaker", ""))
        text = entry.get("text", "")
        if entry.get("type") == "choice":
            text = " / ".join(choice.get("caption", "") for choice in entry.get("choices", []) if choice.get("caption")) or text
        if not text:
            return None
        label = "{}: {}".format(speaker, text) if speaker else text
        return Transform(Text(label, size=28, color="#FFFFFF"), xpos=0.5, ypos=0.88, xanchor=0.5, yanchor=0.5)

    def scene_editor_render_ui_scene(target):
        if not scene_editor_ui_scene_visible:
            return 0
        count = 0
        for tag in scene_editor_ui_tags(include_hidden=False):
            displayable = scene_editor_ui_displayable(tag)
            if displayable is not None:
                target.add(displayable)
                count += 1
        dialogue_preview = scene_editor_dialogue_preview_displayable()
        if dialogue_preview is not None:
            target.add(dialogue_preview)
            count += 1
        return count

    def scene_editor_drag_name(kind, *parts):
        return tuple([kind] + list(parts))

    def scene_editor_drag_payload(drag):
        try:
            return drag.drag_name
        except Exception:
            return None

    def scene_editor_dragged_noop(drags, drop=None):
        return

    def scene_editor_drop_scene_tree(drags, drop=None):
        if not drags:
            return
        payload = scene_editor_drag_payload(drags[0])
        target = scene_editor_drag_payload(drop)
        if not payload or not target:
            return
        if payload[0] == "image" and target[0] == "frame":
            scene_editor_move_image_to_scene(payload[1], payload[2], payload[3], target[1])
            return
        if payload[0] == "asset":
            scene_editor_drop_asset_on_target(payload[1], target)

    def scene_editor_drop_asset_on_stage(drags, drop=None):
        if not drags:
            return
        payload = scene_editor_drag_payload(drags[0])
        if payload and payload[0] == "asset":
            scene_editor_drop_asset_on_target(payload[1], ("stage", current_scene))

    def scene_editor_drop_asset_on_target(image_name, target):
        layer = scene_editor_selected_layer
        if scene_editor_is_ui_layer(layer):
            layer = "master"
        if target and target[0] == "layer":
            layer = target[2]
            if target[1] != current_scene:
                scene_editor_change_scene(target[1])
        elif target and target[0] == "frame" and target[1] != current_scene:
            scene_editor_change_scene(target[1])
        scene_editor_apply_image_name(image_name, layer, None)

    def scene_editor_move_image_to_scene(source_scene, layer, tag, target_scene):
        global current_scene, scene_editor_selected_layer, scene_editor_selected_tag
        if source_scene == target_scene:
            return
        if source_scene < 0 or source_scene >= len(scene_keyframes):
            return
        if target_scene < 0 or target_scene >= len(scene_keyframes):
            return
        state = get_image_state(layer, source_scene)
        if tag not in state:
            return
        scene_editor_push_history()
        moved_state = deepcopy(state[tag])
        moved_displayable = scene_editor_captured_displayables[source_scene].get(layer, {}).get(tag)
        target_tag = scene_editor_unique_tag(tag, layer)
        old_scene = current_scene
        current_scene = target_scene
        target_tag = scene_editor_unique_tag(tag, layer)
        if target_tag is None:
            current_scene = old_scene
            renpy.notify(_("too many same tag images is used"))
            return
        image_state[target_scene].setdefault(layer, {})[target_tag] = deepcopy(moved_state)
        image_state_org[target_scene].setdefault(layer, {})[target_tag] = deepcopy(moved_state)
        scene_editor_captured_displayables[target_scene].setdefault(layer, {})[target_tag] = moved_displayable
        zorder_list[target_scene].setdefault(layer, []).append((target_tag, len(zorder_list[target_scene].setdefault(layer, []))))
        for prop, value in moved_state.items():
            if prop not in ("at_list", "_captured_raw"):
                all_keyframes[target_scene][(target_tag, layer, prop)] = [(deepcopy(value), scene_keyframes[target_scene][1], persistent._viewer_warper)]
        current_scene = source_scene
        scene_editor_remove_image(layer, tag)
        current_scene = target_scene
        scene_editor_selected_layer = layer
        scene_editor_selected_tag = target_tag
        scene_editor_tree_expanded.add(scene_editor_tree_key("frame", target_scene, target_scene))
        scene_editor_clear_runtime_caches()
        change_time(scene_keyframes[target_scene][1])

    def scene_editor_ui_upsert(tag, kind, group, **values):
        scene = scene_editor_ui_scene()
        element = scene.setdefault(tag, scene_editor_ui_default_element(kind, group))
        element["kind"] = kind
        element["group"] = group if group in scene_editor_ui_groups else "overlays"
        for key, value in values.items():
            element[key] = deepcopy(value)
        return element

    def scene_editor_ui_capture_displayable(tag, displayable):
        while len(scene_editor_ui_captured_displayables) <= current_scene:
            scene_editor_ui_captured_displayables.append({})
        scene_editor_ui_captured_displayables[current_scene][tag] = displayable

    def scene_editor_ui_screen_is_captured(screen_name):
        if not screen_name:
            return False
        try:
            for tag, displayable in scene_editor_ui_captured_displayables[current_scene].items():
                element = scene_editor_ui_scene().get(tag, {})
                if element.get("source_screen") == screen_name and displayable is not None:
                    return True
        except Exception:
            pass
        return False

    def scene_editor_screen_showing(name, layer="screens"):
        try:
            return renpy.get_screen(name, layer=layer) is not None
        except Exception:
            try:
                return renpy.get_screen(name) is not None
            except Exception:
                return False

    def scene_editor_screen_variable(screen_name, variable, fallback=None, layer="screens"):
        getter = getattr(renpy, "get_screen_variable", None)
        if not callable(getter):
            return fallback
        try:
            value = getter(variable, screen=screen_name, layer=layer)
        except Exception:
            try:
                value = getter(variable, screen_name, layer)
            except Exception:
                return fallback
        return fallback if value is None else value

    def scene_editor_screen_displayable_name(displayable, fallback):
        for attr in ("screen_name", "screen", "name", "tag"):
            try:
                value = getattr(displayable, attr, None)
                if value:
                    return str(value)
            except Exception:
                pass
        return str(fallback or "screen")

    def scene_editor_capture_active_screen_layers():
        if not scene_editor_screen_displayable:
            return
        sle = scene_editor_scene_lists()
        if sle is None:
            return
        screen_layers = [layer for layer in ("screens", "overlay", "transient") if layer in getattr(config, "layers", ())]
        for layer in screen_layers:
            try:
                layer_entries = list(sle.layers[layer])
            except Exception:
                layer_entries = []
            for index, entry in enumerate(layer_entries):
                tag = scene_editor_entry_tag(entry)
                try:
                    displayable = sle.get_displayable_by_tag(layer, tag)
                except Exception:
                    displayable = None
                if not isinstance(displayable, scene_editor_screen_displayable):
                    continue
                screen_name = scene_editor_screen_displayable_name(displayable, tag)
                safe_tag = scene_editor_safe_identifier("screen_{}_{}".format(layer, screen_name), "screen_ui")
                try:
                    zorder = scene_editor_entry_zorder(entry, index)
                except Exception:
                    zorder = 200 + index
                group = "dialogue_box" if screen_name == "say" else ("choices" if screen_name == "choice" else "overlays")
                scene_editor_ui_upsert(safe_tag, "screen", group, text=screen_name, xpos=0, ypos=0, xanchor=0.0, yanchor=0.0, xsize=config.screen_width, ysize=config.screen_height, zorder=zorder, selectable=False, source_screen=screen_name, source_layer=layer, source_role="active_screen")
                scene_editor_ui_capture_displayable(safe_tag, displayable)

    def scene_editor_seed_say_ui(who=None, what=None):
        scene_editor_ui_upsert("say_window", "panel", "dialogue_box", text="", background="#0000000d", xpos=0.5, ypos=1.0, xanchor=0.5, yanchor=1.0, xsize=config.screen_width, ysize=240, zorder=160, source_screen="say", source_role="window")
        scene_editor_ui_upsert("say_name_plate", "panel", "dialogue_box", text="", background="#ffffff77", xpos=60, ypos=config.screen_height - 170, xanchor=0.0, yanchor=0.0, xsize=220, ysize=52, zorder=161, source_screen="say", source_role="who_plate")
        scene_editor_ui_upsert("say_who", "text", "dialogue_box", text=str(who or "Speaker"), xpos=150, ypos=config.screen_height - 154, xanchor=0.5, yanchor=0.0, size=28, color="#ffffff", xsize=220, zorder=162, source_screen="say", source_role="who")
        scene_editor_ui_upsert("say_what", "text", "dialogue_box", text=str(what or "Dialogue text"), xpos=270, ypos=config.screen_height - 150, xanchor=0.0, yanchor=0.0, size=30, color="#ffffff", xsize=max(200, config.screen_width - 360), zorder=162, source_screen="say", source_role="what")
        scene_editor_ui_upsert("say_hide_button", "text", "dialogue_box", text="◉", xpos=config.screen_width - 58, ypos=config.screen_height - 58, xanchor=0.5, yanchor=0.5, size=32, color="#ffffffcc", zorder=163, source_screen="say", source_role="hide_interface")

    def scene_editor_choice_captions():
        items = scene_editor_screen_variable("choice", "items", None)
        captions = []
        if items:
            for item in items:
                caption = getattr(item, "caption", None)
                if caption:
                    captions.append(str(caption))
        return captions

    def scene_editor_seed_choice_ui(captions=None):
        captions = captions or ["Choice"]
        count = max(1, len(captions))
        panel_height = max(80, count * 58 + 32)
        scene_editor_ui_upsert("choice_panel", "panel", "choices", text="", background="#00000099", xpos=0.5, ypos=0.5, xanchor=0.5, yanchor=0.5, xsize=720, ysize=panel_height, zorder=170, source_screen="choice", source_role="panel")
        for index, caption in enumerate(captions[:8]):
            scene_editor_ui_upsert("choice_option_{:02d}".format(index + 1), "text", "choices", text=str(caption), xpos=0.5, ypos=0.5, xanchor=0.5, yanchor=0.5, yoffset=(index - (count - 1) / 2.0) * 58, size=26, color="#ffffff", xsize=660, zorder=171 + index, source_screen="choice", source_role="option")

    def scene_editor_seed_hud_ui():
        if getattr(renpy.store, "hud_visible", True) is False:
            return
        scene_editor_ui_upsert("hud_time_panel", "panel", "time", text="", background="#000000a0", xpos=20, ypos=20, xanchor=0.0, yanchor=0.0, xsize=250, ysize=118, zorder=100, source_screen="hud", source_role="time_panel")
        scene_editor_ui_upsert("hud_day", "value", "time", text="Day", bound_variable='"{} - Day {}".format(weekday_name(), day)', xpos=36, ypos=34, xanchor=0.0, yanchor=0.0, size=22, color="#ffffff", xsize=220, zorder=101, source_screen="hud", source_role="day")
        scene_editor_ui_upsert("hud_time", "value", "time", text="Time", bound_variable='convert_to_12hr_format(time)', xpos=36, ypos=62, xanchor=0.0, yanchor=0.0, size=22, color="#ffd27a", xsize=220, zorder=101, source_screen="hud", source_role="time")
        scene_editor_ui_upsert("hud_stamina", "value", "stats", text="Stamina", bound_variable='"Stamina: {}/{}".format(stamina, get_max_stamina())', xpos=36, ypos=90, xanchor=0.0, yanchor=0.0, size=20, color="#aef0ae", xsize=240, zorder=101, source_screen="hud", source_role="stamina")
        scene_editor_ui_upsert("hud_location_bar", "panel", "indicators", text="", background="#00000000", image="ui_hud_location", xpos=0.5, ypos=0.0, xanchor=0.5, yanchor=0.0, yoffset=-6, xsize=760, ysize=98, zorder=102, source_screen="hud", source_role="location_bar")
        scene_editor_ui_upsert("hud_location_name", "value", "indicators", text="Location", bound_variable="location_name()", xpos=0.5, ypos=24, xanchor=0.5, yanchor=0.0, size=28, color="#ffffff", xsize=700, zorder=103, source_screen="hud", source_role="location_name")
        scene_editor_ui_upsert("hud_objective", "value", "indicators", text="Objective", bound_variable='quest_target_for_current_location() or ""', xpos=0.5, ypos=96, xanchor=0.5, yanchor=0.0, size=16, color="#ffd27a", xsize=720, zorder=103, source_screen="hud", source_role="objective")
        scene_editor_ui_upsert("hud_quests_button", "text", "overlays", text="Quests", xpos=config.screen_width - 265, ypos=28, xanchor=0.5, yanchor=0.0, size=16, color="#ffffff", zorder=104, source_screen="hud", source_role="quests_button")
        scene_editor_ui_upsert("hud_inventory_button", "text", "overlays", text="Inventory", xpos=config.screen_width - 180, ypos=28, xanchor=0.5, yanchor=0.0, size=16, color="#ffffff", zorder=104, source_screen="hud", source_role="inventory_button")
        scene_editor_ui_upsert("hud_characters_button", "panel", "overlays", text="", background="#00000000", image="ui_hud_characters", xpos=config.screen_width - 75, ypos=7, xanchor=0.5, yanchor=0.0, xsize=110, ysize=110, zorder=104, source_screen="hud", source_role="characters_button")

    def scene_editor_speaker_id_from_who(who):
        last_speaker = getattr(renpy.store, "_last_speaker", None)
        if last_speaker:
            return str(last_speaker)
        who = str(who or "").strip()
        if not who:
            return ""
        for char_id, label in scene_editor_known_characters():
            if who == label or who.lower() == str(label).lower() or who == char_id:
                return char_id
        return who

    def scene_editor_capture_runtime_dialogue(who=None, what=None):
        global scene_editor_selected_dialogue_entry_id
        dialogue_scene = scene_editor_dialogue_scene()
        try:
            cast = getattr(renpy.store, "_dialogue_cast", None)
            if isinstance(cast, dict):
                dialogue_scene["cast"] = deepcopy(cast)
        except Exception:
            pass
        dialogue_scene["active"] = bool(getattr(renpy.store, "_in_dialogue", None))
        if what is None:
            what = scene_editor_screen_variable("say", "what", None)
        if who is None:
            who = scene_editor_screen_variable("say", "who", None)
        if what:
            entries = dialogue_scene.setdefault("entries", [])
            if not entries:
                entry = scene_editor_new_dialogue_entry("line" if who else "narration")
                entry["speaker"] = scene_editor_speaker_id_from_who(who)
                entry["text"] = str(what)
                entry["frame_id"] = scene_editor_current_frame_id()
                entries.append(entry)
                scene_editor_selected_dialogue_entry_id = entry["id"]

    def scene_editor_capture_live_studio_context():
        who = scene_editor_screen_variable("say", "who", None)
        what = scene_editor_screen_variable("say", "what", None)
        if scene_editor_screen_showing("say") or what or who:
            scene_editor_seed_say_ui(who, what)
        else:
            scene_editor_seed_say_ui()
        captions = scene_editor_choice_captions()
        if scene_editor_screen_showing("choice") or captions:
            scene_editor_seed_choice_ui(captions)
        else:
            scene_editor_seed_choice_ui(["Choice 1", "Choice 2"])
        if scene_editor_screen_showing("hud") or hasattr(renpy.store, "hud_visible"):
            scene_editor_seed_hud_ui()
        scene_editor_capture_active_screen_layers()
        scene_editor_capture_runtime_dialogue(who, what)

    def scene_editor_screen_to_ui_stage(x, y):
        offset_x, offset_y, scale = scene_editor_canvas_offsets()
        if scale == 0:
            return (x - offset_x, y - offset_y)
        return ((x - offset_x) / scale, (y - offset_y) / scale)

    def scene_editor_ensure_frame_records():
        global scene_editor_frame_counter
        while len(scene_editor_frame_records) < len(scene_keyframes):
            scene_index = len(scene_editor_frame_records)
            scene_editor_frame_counter += 1
            new_id = "frame_{:03d}".format(scene_editor_frame_counter)
            parent_id = scene_editor_frame_records[-1]["id"] if scene_editor_frame_records else None
            scene_editor_frame_records.append({
                "id": new_id,
                "route_id": scene_editor_current_route_id,
                "name": "Frame {}".format(scene_index),
                "scene_index": scene_index,
                "parent_id": parent_id,
                "time": scene_keyframes[scene_index][1] if scene_index < len(scene_keyframes) else 0,
                "inherits": parent_id is not None,
            })
        while len(scene_editor_frame_records) > len(scene_keyframes):
            scene_editor_frame_records.pop()
        for index, record in enumerate(scene_editor_frame_records):
            if not record.get("id"):
                scene_editor_frame_counter += 1
                record["id"] = "frame_{:03d}".format(scene_editor_frame_counter)
            record.setdefault("route_id", scene_editor_current_route_id)
            record.setdefault("name", "Frame {}".format(index))
            record.setdefault("dialogue_visible", True)
            record.setdefault("notes", "")
            record["scene_index"] = index
            if index < len(scene_keyframes):
                record["time"] = scene_keyframes[index][1]
            if index == 0:
                record["parent_id"] = None
                record["inherits"] = False
            elif record.get("inherits", True) and not record.get("parent_id"):
                record["parent_id"] = scene_editor_frame_records[index - 1]["id"]
            elif not record.get("inherits", True):
                record["parent_id"] = None
        return scene_editor_frame_records

    def scene_editor_current_frame_record():
        scene_editor_ensure_frame_records()
        if current_scene < 0 or current_scene >= len(scene_editor_frame_records):
            return None
        return scene_editor_frame_records[current_scene]

    def scene_editor_current_frame_id():
        record = scene_editor_current_frame_record()
        return record.get("id") if record else None

    def scene_editor_current_frame_label():
        record = scene_editor_current_frame_record()
        if not record:
            return "No Frame"
        parent = record.get("parent_id") or "root"
        return "{} · {}".format(record.get("id", "frame"), parent)

    def scene_editor_frame_children(scene_num=None):
        scene_editor_ensure_frame_records()
        if scene_num is None:
            scene_num = current_scene
        if scene_num < 0 or scene_num >= len(scene_editor_frame_records):
            return []
        parent_id = scene_editor_frame_records[scene_num].get("id")
        return [index for index, record in enumerate(scene_editor_frame_records) if record.get("parent_id") == parent_id]

    def scene_editor_frame_depth(scene_num):
        scene_editor_ensure_frame_records()
        if scene_num < 0 or scene_num >= len(scene_editor_frame_records):
            return 0
        depth = 0
        seen = set()
        parent_id = scene_editor_frame_records[scene_num].get("parent_id")
        while parent_id and parent_id not in seen:
            seen.add(parent_id)
            parent_index = None
            for index, record in enumerate(scene_editor_frame_records):
                if record.get("id") == parent_id:
                    parent_index = index
                    break
            if parent_index is None:
                break
            depth += 1
            parent_id = scene_editor_frame_records[parent_index].get("parent_id")
        return min(depth, 12)

    def scene_editor_frame_tree_rows():
        scene_editor_ensure_frame_records()
        return [(index, scene_editor_frame_depth(index), record) for index, record in enumerate(scene_editor_frame_records)]

    def scene_editor_next_frame_index():
        if current_scene + 1 < len(scene_keyframes):
            return current_scene + 1
        return current_scene

    def scene_editor_previous_frame_index():
        return max(0, current_scene - 1)

    def scene_editor_parent_frame_index():
        record = scene_editor_current_frame_record()
        if not record:
            return current_scene
        parent_id = record.get("parent_id")
        if not parent_id:
            return current_scene
        for index, frame in enumerate(scene_editor_frame_records):
            if frame.get("id") == parent_id:
                return index
        return current_scene

    def scene_editor_first_child_frame_index():
        children = scene_editor_frame_children(current_scene)
        if children:
            return children[0]
        return current_scene

    def scene_editor_go_previous_frame():
        scene_editor_change_scene(scene_editor_previous_frame_index())

    def scene_editor_go_next_frame():
        scene_editor_change_scene(scene_editor_next_frame_index())

    def scene_editor_go_parent_frame():
        scene_editor_change_scene(scene_editor_parent_frame_index())

    def scene_editor_go_child_frame():
        scene_editor_change_scene(scene_editor_first_child_frame_index())

    def scene_editor_ensure_dialogue_scene(scene_num=None):
        if scene_num is None:
            scene_num = current_scene
        while len(scene_editor_dialogue_scenes) <= scene_num:
            scene_editor_dialogue_scenes.append({"entries": []})
        scene_data = scene_editor_dialogue_scenes[scene_num]
        scene_data.setdefault("entries", [])
        scene_editor_dialogue_scenes[scene_num] = scene_editor_normalize_dialogue_scene(scene_data)
        return scene_editor_dialogue_scenes[scene_num]

    def scene_editor_dialogue_scene():
        return scene_editor_ensure_dialogue_scene(current_scene)

    def scene_editor_dialogue_entries():
        return scene_editor_dialogue_scene().get("entries", [])

    def scene_editor_choice_default(caption="Choice", target=""):
        return {"caption": caption, "target": target, "condition": "", "script": "", "merge_target": ""}

    def scene_editor_normalize_dialogue_entry(entry):
        if not isinstance(entry, dict):
            entry = scene_editor_new_dialogue_entry("line")
        if not entry.get("id"):
            entry["id"] = scene_editor_new_dialogue_entry(entry.get("type", "line")).get("id")
        entry.setdefault("type", "line")
        if entry.get("type") not in scene_editor_dialogue_entry_types:
            entry["type"] = "line"
        entry.setdefault("speaker", "")
        entry.setdefault("text", "")
        entry.setdefault("target", "")
        entry.setdefault("condition", "")
        entry.setdefault("payload", "")
        entry.setdefault("on_show", "")
        entry.setdefault("on_advance", "")
        entry.setdefault("on_select", "")
        if entry.get("type") == "choice":
            choices = entry.setdefault("choices", [])
            if not choices:
                choices.append(scene_editor_choice_default(entry.get("text", "Choice"), entry.get("target", "")))
            for index, choice in enumerate(list(choices)):
                if not isinstance(choice, dict):
                    choice = scene_editor_choice_default(str(choice), "")
                    choices[index] = choice
                choice.setdefault("caption", entry.get("text", "Choice"))
                choice.setdefault("target", "")
                choice.setdefault("condition", "")
                choice.setdefault("script", "")
                choice.setdefault("merge_target", "")
            entry["text"] = choices[0].get("caption", entry.get("text", ""))
            entry["target"] = choices[0].get("target", entry.get("target", ""))
        return entry

    def scene_editor_normalize_dialogue_scene(dialogue_scene):
        if not isinstance(dialogue_scene, dict):
            dialogue_scene = {"entries": []}
        entries = dialogue_scene.setdefault("entries", [])
        for index in range(len(entries)):
            entries[index] = scene_editor_normalize_dialogue_entry(entries[index])
        return dialogue_scene

    def scene_editor_current_dialogue_visible():
        record = scene_editor_current_frame_record()
        if not record:
            return True
        return bool(record.get("dialogue_visible", True))

    def scene_editor_toggle_current_dialogue_visible():
        record = scene_editor_current_frame_record()
        if not record:
            return
        scene_editor_push_history()
        record["dialogue_visible"] = not bool(record.get("dialogue_visible", True))
        renpy.restart_interaction()

    def scene_editor_known_characters():
        characters = []
        seen = set()
        def add_character(char_id, label=None):
            if not char_id:
                return
            char_id = str(char_id)
            if char_id in seen:
                return
            seen.add(char_id)
            characters.append((char_id, label or scene_editor_character_label(char_id)))
        try:
            speakers = getattr(renpy.store, "character_speakers", None)
            if isinstance(speakers, dict):
                for char_id, character in sorted(speakers.items()):
                    label = char_id
                    for attr in ("name", "_name"):
                        try:
                            value = getattr(character, attr)
                            if value:
                                label = str(value)
                                break
                        except Exception:
                            pass
                    add_character(char_id, label)
        except Exception:
            pass
        try:
            stats = getattr(renpy.store, "character_stats", None)
            if isinstance(stats, dict):
                for char_id in sorted(stats.keys()):
                    add_character(char_id)
        except Exception:
            pass
        try:
            known = getattr(renpy.store, "_dialogue_known_characters", None)
            if callable(known):
                for char_id in known():
                    add_character(char_id)
        except Exception:
            pass
        return characters

    def scene_editor_character_label(char_id):
        char_id = str(char_id or "").strip()
        if not char_id:
            return ""
        try:
            speakers = getattr(renpy.store, "character_speakers", None)
            if isinstance(speakers, dict) and char_id in speakers:
                character = speakers[char_id]
                for attr in ("name", "_name", "who_prefix"):
                    try:
                        value = getattr(character, attr)
                        if isinstance(value, str) and value.strip():
                            return value
                    except Exception:
                        pass
        except Exception:
            pass
        return char_id[:1].upper() + char_id[1:]

    def scene_editor_set_dialogue_speaker(entry_id, speaker):
        scene_editor_set_dialogue_field(entry_id, "speaker", speaker)

    def scene_editor_add_choice_option(entry_id=None):
        entry = scene_editor_dialogue_entry(entry_id)
        if not entry or entry.get("type") != "choice":
            return
        scene_editor_push_history()
        choices = entry.setdefault("choices", [])
        choices.append(scene_editor_choice_default("Choice {}".format(len(choices) + 1), ""))
        renpy.restart_interaction()

    def scene_editor_remove_choice_option(entry_id, index):
        entry = scene_editor_dialogue_entry(entry_id)
        if not entry or entry.get("type") != "choice":
            return
        choices = entry.setdefault("choices", [])
        if index < 0 or index >= len(choices):
            return
        scene_editor_push_history()
        del choices[index]
        if not choices:
            choices.append(scene_editor_choice_default())
        renpy.restart_interaction()

    def scene_editor_set_choice_field(entry_id, index, field, value):
        entry = scene_editor_dialogue_entry(entry_id)
        if not entry or entry.get("type") != "choice":
            return
        choices = entry.setdefault("choices", [])
        if index < 0 or index >= len(choices):
            return
        old_value = choices[index].get(field)
        if old_value != value:
            scene_editor_push_history()
        choices[index][field] = value
        if index == 0:
            if field == "caption":
                entry["text"] = value
            elif field == "target":
                entry["target"] = value
        renpy.restart_interaction()

    def scene_editor_choice_field_changed(entry_id, index, field):
        def changed(value):
            scene_editor_set_choice_field(entry_id, index, field, value)
        return changed

    def scene_editor_new_dialogue_entry(entry_type="line"):
        global scene_editor_dialogue_entry_counter
        if entry_type not in scene_editor_dialogue_entry_types:
            entry_type = "line"
        scene_editor_dialogue_entry_counter += 1
        entry = {
            "id": "dlg_{:03d}".format(scene_editor_dialogue_entry_counter),
            "type": entry_type,
            "speaker": "",
            "text": "New {}".format(entry_type),
            "target": "",
            "condition": "",
            "payload": "",
            "on_show": "",
            "on_advance": "",
            "on_select": "",
        }
        if entry_type == "choice":
            entry["choices"] = [scene_editor_choice_default()]
        return entry

    def scene_editor_add_dialogue_entry(entry_type="line"):
        global scene_editor_selected_dialogue_entry_id
        scene_editor_push_history()
        entry = scene_editor_new_dialogue_entry(entry_type)
        scene_editor_dialogue_entries().append(entry)
        scene_editor_selected_dialogue_entry_id = entry["id"]
        renpy.restart_interaction()

    def scene_editor_dialogue_entry(entry_id=None):
        if entry_id is None:
            entry_id = scene_editor_selected_dialogue_entry_id
        for entry in scene_editor_dialogue_entries():
            if entry.get("id") == entry_id:
                return entry
        return None

    def scene_editor_select_dialogue_entry(entry_id):
        global scene_editor_selected_dialogue_entry_id
        scene_editor_selected_dialogue_entry_id = entry_id
        renpy.restart_interaction()

    def scene_editor_remove_dialogue_entry(entry_id=None):
        global scene_editor_selected_dialogue_entry_id
        if entry_id is None:
            entry_id = scene_editor_selected_dialogue_entry_id
        if entry_id is None:
            return
        entries = scene_editor_dialogue_entries()
        for index, entry in enumerate(list(entries)):
            if entry.get("id") == entry_id:
                scene_editor_push_history()
                del entries[index]
                scene_editor_selected_dialogue_entry_id = None
                renpy.restart_interaction()
                return

    def scene_editor_move_dialogue_entry(entry_id, direction):
        entries = scene_editor_dialogue_entries()
        for index, entry in enumerate(entries):
            if entry.get("id") == entry_id:
                new_index = index + direction
                if new_index < 0 or new_index >= len(entries):
                    return
                scene_editor_push_history()
                entries[index], entries[new_index] = entries[new_index], entries[index]
                renpy.restart_interaction()
                return

    def scene_editor_set_dialogue_field(entry_id, field, value):
        entry = scene_editor_dialogue_entry(entry_id)
        if entry is None:
            return
        if entry.get(field) != value:
            scene_editor_push_history()
        entry[field] = value
        if entry.get("type") == "choice" and field in ("text", "target"):
            choices = entry.setdefault("choices", [scene_editor_choice_default(entry.get("text", "Choice"), entry.get("target", ""))])
            if not choices:
                choices.append(scene_editor_choice_default(entry.get("text", "Choice"), entry.get("target", "")))
            if field == "text":
                choices[0]["caption"] = value
            elif field == "target":
                choices[0]["target"] = value
        renpy.restart_interaction()

    def scene_editor_dialogue_field_changed(entry_id, field):
        def changed(value):
            scene_editor_set_dialogue_field(entry_id, field, value)
        return changed

    def scene_editor_set_project_name(value):
        global scene_editor_project_name
        new_value = value.strip() or "live_studio_project"
        if scene_editor_project_name != new_value:
            scene_editor_push_history()
        scene_editor_project_name = new_value
        renpy.restart_interaction()

    def scene_editor_set_route_id(value):
        global scene_editor_current_route_id
        new_value = scene_editor_safe_identifier(value, "route_main")
        if scene_editor_current_route_id != new_value:
            scene_editor_push_history()
        scene_editor_current_route_id = new_value
        for record in scene_editor_frame_records:
            record["route_id"] = scene_editor_current_route_id
        renpy.restart_interaction()

    def scene_editor_set_project_slot(value):
        global scene_editor_project_slot
        new_value = value.strip() or "autosave"
        if scene_editor_project_slot != new_value:
            scene_editor_push_history()
        scene_editor_project_slot = new_value
        renpy.restart_interaction()

    def scene_editor_set_frame_insert_step(value):
        global scene_editor_frame_insert_step
        old_value = scene_editor_frame_insert_step
        try:
            new_value = max(0.1, float(value))
        except Exception:
            new_value = 1.0
        if old_value != new_value:
            scene_editor_push_history()
        scene_editor_frame_insert_step = new_value
        renpy.restart_interaction()

    def scene_editor_toggle_setting(name):
        global scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue
        old_values = (scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue)
        if name == "export_visuals":
            scene_editor_export_visuals = not scene_editor_export_visuals
        elif name == "export_ui":
            scene_editor_export_ui = not scene_editor_export_ui
        elif name == "export_dialogue":
            scene_editor_export_dialogue = not scene_editor_export_dialogue
        elif name == "export_scene_clears":
            scene_editor_export_scene_clears = not scene_editor_export_scene_clears
        elif name == "export_hidden_ui":
            scene_editor_export_hidden_ui = not scene_editor_export_hidden_ui
        elif name == "preview_dialogue":
            scene_editor_preview_dialogue = not scene_editor_preview_dialogue
        new_values = (scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue)
        if old_values != new_values:
            scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue = old_values
            scene_editor_push_history()
            scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue = new_values
        renpy.restart_interaction()

    def scene_editor_set_frame_notes(scene_num, value):
        scene_editor_ensure_frame_records()
        if 0 <= scene_num < len(scene_editor_frame_records):
            if scene_editor_frame_records[scene_num].get("notes", "") != value:
                scene_editor_push_history()
            scene_editor_frame_records[scene_num]["notes"] = value
            renpy.restart_interaction()

    def scene_editor_frame_notes_changed(scene_num):
        def changed(value):
            scene_editor_set_frame_notes(scene_num, value)
        return changed

    def scene_editor_set_frame_name(scene_num, value):
        scene_editor_ensure_frame_records()
        if 0 <= scene_num < len(scene_editor_frame_records):
            new_value = value.strip() or "Frame {}".format(scene_num)
            if scene_editor_frame_records[scene_num].get("name") != new_value:
                scene_editor_push_history()
            scene_editor_frame_records[scene_num]["name"] = new_value
            renpy.restart_interaction()

    def scene_editor_frame_name_changed(scene_num):
        def changed(value):
            scene_editor_set_frame_name(scene_num, value)
        return changed

    def scene_editor_set_frame_inherits(scene_num, value):
        scene_editor_ensure_frame_records()
        if scene_num <= 0 or scene_num >= len(scene_editor_frame_records):
            return
        scene_editor_push_history()
        scene_editor_frame_records[scene_num]["inherits"] = bool(value)
        scene_editor_frame_records[scene_num]["parent_id"] = scene_editor_frame_records[scene_num - 1]["id"] if value else None
        renpy.restart_interaction()

    def scene_editor_frame_to_dict(scene_num):
        scene_editor_ensure_frame_records()
        frame = deepcopy(scene_editor_frame_records[scene_num])
        frame["ui"] = deepcopy(scene_editor_ensure_ui_scene(scene_num))
        frame["dialogue"] = deepcopy(scene_editor_ensure_dialogue_scene(scene_num))
        frame["scene_keyframe"] = deepcopy(scene_keyframes[scene_num])
        return frame

    def scene_editor_project_snapshot():
        snapshot = scene_editor_snapshot()
        snapshot["captured_displayables"] = [{} for _scene in scene_keyframes]
        return snapshot

    def scene_editor_project_data():
        scene_editor_ensure_frame_records()
        return {
            "version": 1,
            "name": scene_editor_project_name,
            "route_id": scene_editor_current_route_id,
            "route_counter": scene_editor_route_counter,
            "frame_counter": scene_editor_frame_counter,
            "dialogue_entry_counter": scene_editor_dialogue_entry_counter,
            "ui_group_visibility": deepcopy(scene_editor_ui_group_visibility),
            "ui_group_locks": sorted(scene_editor_ui_group_locks),
            "settings": {
                "export_visuals": scene_editor_export_visuals,
                "export_ui": scene_editor_export_ui,
                "export_dialogue": scene_editor_export_dialogue,
                "export_scene_clears": scene_editor_export_scene_clears,
                "export_hidden_ui": scene_editor_export_hidden_ui,
                "preview_dialogue": scene_editor_preview_dialogue,
                "frame_insert_step": scene_editor_frame_insert_step,
            },
            "frames": [scene_editor_frame_to_dict(i) for i in range(len(scene_keyframes))],
            "snapshot": scene_editor_project_snapshot(),
        }

    def scene_editor_save_project(slot=None):
        if slot is None:
            slot = scene_editor_project_slot
        if not hasattr(persistent, "_scene_editor_projects") or persistent._scene_editor_projects is None:
            persistent._scene_editor_projects = {}
        persistent._scene_editor_projects[slot] = deepcopy(scene_editor_project_data())
        renpy.save_persistent()
        renpy.notify(_("Saved Live Studio project: {}".format(slot)))

    def scene_editor_load_project(slot=None):
        global scene_editor_project_name, scene_editor_current_route_id, scene_editor_route_counter, scene_editor_frame_counter, scene_editor_frame_records, scene_editor_ui_elements, scene_editor_dialogue_scenes, scene_editor_dialogue_entry_counter, scene_editor_selected_dialogue_entry_id
        global scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue, scene_editor_frame_insert_step
        if slot is None:
            slot = scene_editor_project_slot
        projects = getattr(persistent, "_scene_editor_projects", {}) or {}
        data = projects.get(slot)
        if not data:
            renpy.notify(_("No Live Studio project in slot: {}".format(slot)))
            return
        snapshot = data.get("snapshot")
        if snapshot:
            scene_editor_restore(snapshot)
        scene_editor_project_name = data.get("name", scene_editor_project_name)
        scene_editor_current_route_id = data.get("route_id", scene_editor_current_route_id)
        scene_editor_route_counter = data.get("route_counter", scene_editor_route_counter)
        scene_editor_frame_counter = data.get("frame_counter", scene_editor_frame_counter)
        scene_editor_dialogue_entry_counter = data.get("dialogue_entry_counter", scene_editor_dialogue_entry_counter)
        scene_editor_selected_dialogue_entry_id = None
        frames = data.get("frames", [])
        if frames:
            scene_editor_frame_records = []
            for index, frame in enumerate(frames):
                record = {}
                for key in ("id", "route_id", "name", "scene_index", "parent_id", "time", "inherits", "dialogue_visible", "notes"):
                    if key in frame:
                        record[key] = deepcopy(frame[key])
                record.setdefault("name", "Frame {}".format(index))
                record.setdefault("route_id", scene_editor_current_route_id)
                record.setdefault("dialogue_visible", True)
                record.setdefault("notes", "")
                scene_editor_frame_records.append(record)
        if frames:
            scene_editor_ui_elements = [scene_editor_normalize_ui_scene(deepcopy(frame.get("ui", {}))) for frame in frames]
        scene_editor_dialogue_scenes = [scene_editor_normalize_dialogue_scene(deepcopy(frame.get("dialogue", {"entries": []}))) for frame in frames] or [{}]
        settings = data.get("settings", {})
        scene_editor_export_visuals = settings.get("export_visuals", scene_editor_export_visuals)
        scene_editor_export_ui = settings.get("export_ui", scene_editor_export_ui)
        scene_editor_export_dialogue = settings.get("export_dialogue", scene_editor_export_dialogue)
        scene_editor_export_scene_clears = settings.get("export_scene_clears", scene_editor_export_scene_clears)
        scene_editor_export_hidden_ui = settings.get("export_hidden_ui", scene_editor_export_hidden_ui)
        scene_editor_preview_dialogue = settings.get("preview_dialogue", scene_editor_preview_dialogue)
        scene_editor_frame_insert_step = settings.get("frame_insert_step", scene_editor_frame_insert_step)
        scene_editor_ensure_frame_records()
        renpy.notify(_("Loaded Live Studio project: {}".format(slot)))
        renpy.restart_interaction()

    def scene_editor_dialogue_export_lines(entries):
        lines = []
        for entry in entries:
            entry_type = entry.get("type", "line")
            text = entry.get("text", "")
            speaker = entry.get("speaker", "").strip()
            on_show = entry.get("on_show", "").strip()
            if on_show:
                lines.append("    $ {}".format(on_show))
            if entry_type == "line":
                if speaker:
                    lines.append('    {} "{}"'.format(scene_editor_dialogue_speaker_export_name(speaker), text.replace('"', '\\"')))
                else:
                    lines.append('    "{}"'.format(text.replace('"', '\\"')))
            elif entry_type == "narration":
                lines.append('    "{}"'.format(text.replace('"', '\\"')))
            elif entry_type == "choice":
                lines.append("    menu:")
                on_select = entry.get("on_select", "").strip()
                for choice in entry.get("choices", []) or [{"caption": text, "target": entry.get("target", "")}]:
                    caption = choice.get("caption", text).replace('"', '\\"')
                    target = choice.get("target", "") or choice.get("merge_target", "")
                    condition = choice.get("condition", "").strip()
                    if condition:
                        lines.append('        "{}" if {}:'.format(caption, condition))
                    else:
                        lines.append('        "{}":'.format(caption))
                    if on_select:
                        lines.append("            $ {}".format(on_select))
                    script = choice.get("script", "").strip()
                    if script:
                        lines.append("            $ {}".format(script))
                    if target:
                        lines.append("            jump {}".format(scene_editor_safe_identifier(target, "TODO_choice_target")))
                    else:
                        lines.append("            pass")
            elif entry_type == "script":
                lines.append("    $ {}".format(entry.get("payload") or text or "pass"))
            elif entry_type == "stat":
                lines.append("    $ {}".format(entry.get("payload") or "# TODO stat change"))
            elif entry_type == "reaction":
                lines.append("    # reaction: {}".format(text))
            elif entry_type == "jump":
                lines.append("    jump {}".format(scene_editor_safe_identifier(entry.get("target") or text, "TODO_jump_target")))
            elif entry_type == "label":
                lines.append("    # label marker: {}".format(scene_editor_safe_identifier(entry.get("target") or text, "TODO_label")))
            elif entry_type == "condition":
                condition = entry.get("condition", "").strip() or "True"
                lines.append("    if {}:".format(condition))
                payload = entry.get("payload", "").strip()
                if payload:
                    lines.append("        $ {}".format(payload))
                else:
                    lines.append("        pass")
            on_advance = entry.get("on_advance", "").strip()
            if on_advance:
                lines.append("    $ {}".format(on_advance))
        return lines

    def scene_editor_dialogue_speaker_export_name(speaker):
        speaker = str(speaker or "").strip()
        if not speaker:
            return "speaker"
        safe_speaker = scene_editor_safe_identifier(speaker, "speaker")
        try:
            existing = getattr(renpy.store, safe_speaker, None)
            if existing is not None:
                return safe_speaker
        except Exception:
            pass
        try:
            speakers = getattr(renpy.store, "character_speakers", None)
            if isinstance(speakers, dict) and speaker in speakers:
                character = speakers[speaker]
                for name, value in vars(renpy.store).items():
                    if name.startswith("_"):
                        continue
                    if value is character and scene_editor_safe_identifier(name, "") == name:
                        return name
        except Exception:
            pass
        return safe_speaker

    def scene_editor_ui_export_lines(scene_num):
        lines = []
        ui_scene = scene_editor_ensure_ui_scene(scene_num)
        if ui_scene:
            lines.append("    # UI scene")
        for tag in sorted(ui_scene, key=lambda item: ui_scene[item].get("zorder", 0)):
            element = ui_scene[tag]
            if not scene_editor_export_hidden_ui and not element.get("visible", True):
                continue
            group = element.get("group", "overlays")
            text = element.get("text", "")
            if element.get("kind") == "value":
                text = "[" + element.get("bound_variable", "") + "]"
            lines.append('    # ui {tag} group={group} text="{text}"'.format(tag=tag, group=group, text=text.replace('"', '\\"')))
        return lines

    def scene_editor_safe_identifier(value, fallback):
        text = str(value or "").strip()
        if not text:
            return fallback
        cleaned = []
        for index, char in enumerate(text):
            if char.isalnum() or char == "_":
                cleaned.append(char)
            elif char in (" ", "-", "."):
                cleaned.append("_")
        text = "".join(cleaned).strip("_")
        if not text:
            return fallback
        if text[0].isdigit():
            text = "_" + text
        return text

    def scene_editor_visual_export_lines(scene_num):
        lines = []
        scene_layers = []
        for layer in scene_editor_get_layers():
            if layer in image_state_org[scene_num] or layer in image_state[scene_num]:
                scene_layers.append(layer)
        for layer in scene_layers:
            state = get_image_state(layer, scene_num)
            if not state:
                continue
            for tag, _z in zorder_list[scene_num].get(layer, []):
                if tag not in state:
                    continue
                child = state[tag].get("child")
                image_name = child[0] if isinstance(child, tuple) else child
                if not image_name:
                    continue
                if isinstance(image_name, tuple):
                    image_name = " ".join(str(part) for part in image_name)
                else:
                    image_name = str(image_name)
                command = "    show {}".format(image_name)
                if image_name.split()[0] != tag:
                    command += " as {}".format(tag)
                if layer != "master":
                    command += " onlayer {}".format(layer)
                lines.append(command)
        return lines

    def scene_editor_build_live_studio_script():
        scene_editor_ensure_frame_records()
        label_name = scene_editor_safe_identifier(scene_editor_project_name, "live_studio_project")
        lines = [
            "label {}:".format(label_name),
            "    # Generated by Ren'Py Live Studio draft exporter.",
        ]
        for scene_num, frame in enumerate(scene_editor_frame_records):
            lines.append("")
            lines.append("    # {} ({})".format(frame.get("name", "Frame"), frame.get("id", "frame")))
            if frame.get("parent_id"):
                lines.append("    # inherits {}".format(frame.get("parent_id")))
            if scene_editor_export_scene_clears and scene_num > 0:
                lines.append("    scene")
            if scene_editor_export_visuals:
                lines.extend(scene_editor_visual_export_lines(scene_num))
            if scene_editor_export_ui:
                lines.extend(scene_editor_ui_export_lines(scene_num))
            if scene_editor_export_dialogue and frame.get("dialogue_visible", True):
                lines.extend(scene_editor_dialogue_export_lines(scene_editor_ensure_dialogue_scene(scene_num).get("entries", [])))
        lines.append("    return")
        return "\n".join(lines)

    def scene_editor_copy_text_to_clipboard(text):
        try:
            from pygame import scrap, locals
            scrap.put(locals.SCRAP_TEXT, text.encode("utf-8"))
            return True
        except Exception:
            try:
                renpy.set_clipboard(text)
                return True
            except Exception:
                return False

    def scene_editor_export_live_studio_script():
        global scene_editor_export_cache
        scene_editor_export_cache = scene_editor_build_live_studio_script()
        if scene_editor_copy_text_to_clipboard(scene_editor_export_cache):
            renpy.notify(_("Live Studio draft script copied to clipboard"))
        else:
            renpy.notify(_("Live Studio draft script generated, but clipboard failed"))
        renpy.restart_interaction()

    def scene_editor_write_live_studio_file():
        global scene_editor_export_cache, scene_editor_last_written_file
        scene_editor_export_cache = scene_editor_build_live_studio_script()
        filename = scene_editor_safe_identifier(scene_editor_project_name, "live_studio_project") + ".rpy.draft"
        relative_dir = "DevTools/Debug/SceneEditor/gamefiles"
        relative_path = relative_dir + "/" + filename
        try:
            import os
            target_dir = renpy.config.gamedir + "/" + relative_dir
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            target_path = target_dir + "/" + filename
            with open(target_path, "w", encoding="utf-8") as export_file:
                export_file.write(scene_editor_export_cache)
                export_file.write("\n")
            scene_editor_last_written_file = relative_path
            renpy.notify(_("Wrote Live Studio draft: {}".format(relative_path)))
        except Exception as exc:
            scene_editor_last_written_file = ""
            renpy.notify(_("Live Studio file write failed: {}".format(exc)))
        renpy.restart_interaction()

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
                return renpy.render(self.child, width, height, self.fixed_st, self.fixed_at)
            except Exception:
                return renpy.Render(1, 1)

        def visit(self):
            return [self.child]

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

    def scene_editor_copy_ui_captured_displayables():
        copied = []
        for scene_data in scene_editor_ui_captured_displayables:
            copied.append(dict(scene_data))
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
            "ui_elements": deepcopy(scene_editor_ui_elements),
            "ui_captured_displayables": scene_editor_copy_ui_captured_displayables(),
            "ui_group_visibility": deepcopy(scene_editor_ui_group_visibility),
            "ui_counter": scene_editor_ui_counter,
            "ui_scene_visible": scene_editor_ui_scene_visible,
            "tree_tab": scene_editor_tree_tab,
            "bottom_panel_tab": scene_editor_bottom_panel_tab,
            "layers_view": scene_editor_layers_view,
            "tree_expanded": deepcopy(scene_editor_tree_expanded),
            "project_name": scene_editor_project_name,
            "current_route_id": scene_editor_current_route_id,
            "route_counter": scene_editor_route_counter,
            "frame_counter": scene_editor_frame_counter,
            "frame_records": deepcopy(scene_editor_frame_records),
            "dialogue_scenes": deepcopy(scene_editor_dialogue_scenes),
            "dialogue_entry_counter": scene_editor_dialogue_entry_counter,
            "selected_dialogue_entry_id": scene_editor_selected_dialogue_entry_id,
            "project_slot": scene_editor_project_slot,
            "export_cache": scene_editor_export_cache,
            "export_visuals": scene_editor_export_visuals,
            "export_ui": scene_editor_export_ui,
            "export_dialogue": scene_editor_export_dialogue,
            "export_scene_clears": scene_editor_export_scene_clears,
            "export_hidden_ui": scene_editor_export_hidden_ui,
            "preview_dialogue": scene_editor_preview_dialogue,
            "frame_insert_step": scene_editor_frame_insert_step,
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
        global scene_editor_selected_layer, scene_editor_selected_tag, scene_editor_locked_items, scene_editor_hidden_items, scene_editor_group_members, scene_editor_ui_elements, scene_editor_ui_captured_displayables, scene_editor_ui_group_visibility, scene_editor_ui_group_locks, scene_editor_ui_counter, scene_editor_ui_scene_visible, scene_editor_tree_tab, scene_editor_bottom_panel_tab, scene_editor_layers_view, scene_editor_tree_expanded
        global scene_editor_project_name, scene_editor_current_route_id, scene_editor_route_counter, scene_editor_frame_counter, scene_editor_frame_records, scene_editor_dialogue_scenes, scene_editor_dialogue_entry_counter, scene_editor_selected_dialogue_entry_id, scene_editor_project_slot, scene_editor_export_cache
        global scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue, scene_editor_frame_insert_step
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
        scene_editor_ui_elements = [scene_editor_normalize_ui_scene(deepcopy(scene)) for scene in snapshot.get("ui_elements", [{}])]
        scene_editor_ui_captured_displayables = snapshot.get("ui_captured_displayables", scene_editor_copy_ui_captured_displayables())
        scene_editor_ui_group_visibility = deepcopy(snapshot.get("ui_group_visibility", dict((group, True) for group in scene_editor_ui_groups)))
        scene_editor_ui_group_locks = set(snapshot.get("ui_group_locks", []))
        scene_editor_ui_counter = snapshot.get("ui_counter", scene_editor_ui_counter)
        scene_editor_ui_scene_visible = snapshot.get("ui_scene_visible", scene_editor_ui_scene_visible)
        scene_editor_tree_tab = snapshot.get("tree_tab", scene_editor_tree_tab)
        scene_editor_bottom_panel_tab = snapshot.get("bottom_panel_tab", scene_editor_bottom_panel_tab)
        if scene_editor_tree_tab == "Frames":
            scene_editor_tree_tab = "Frame"
        if scene_editor_tree_tab == "Dialogue":
            scene_editor_tree_tab = "Scene"
            scene_editor_bottom_panel_tab = "Dialogue"
        scene_editor_layers_view = snapshot.get("layers_view", scene_editor_layers_view)
        scene_editor_tree_expanded = deepcopy(snapshot.get("tree_expanded", set()))
        scene_editor_project_name = snapshot.get("project_name", scene_editor_project_name)
        scene_editor_current_route_id = snapshot.get("current_route_id", scene_editor_current_route_id)
        scene_editor_route_counter = snapshot.get("route_counter", scene_editor_route_counter)
        scene_editor_frame_counter = snapshot.get("frame_counter", scene_editor_frame_counter)
        scene_editor_frame_records = deepcopy(snapshot.get("frame_records", []))
        scene_editor_dialogue_scenes = [scene_editor_normalize_dialogue_scene(deepcopy(scene)) for scene in snapshot.get("dialogue_scenes", [{}])]
        scene_editor_dialogue_entry_counter = snapshot.get("dialogue_entry_counter", scene_editor_dialogue_entry_counter)
        scene_editor_selected_dialogue_entry_id = snapshot.get("selected_dialogue_entry_id", None)
        scene_editor_project_slot = snapshot.get("project_slot", scene_editor_project_slot)
        scene_editor_export_cache = snapshot.get("export_cache", "")
        scene_editor_export_visuals = snapshot.get("export_visuals", scene_editor_export_visuals)
        scene_editor_export_ui = snapshot.get("export_ui", scene_editor_export_ui)
        scene_editor_export_dialogue = snapshot.get("export_dialogue", scene_editor_export_dialogue)
        scene_editor_export_scene_clears = snapshot.get("export_scene_clears", scene_editor_export_scene_clears)
        scene_editor_export_hidden_ui = snapshot.get("export_hidden_ui", scene_editor_export_hidden_ui)
        scene_editor_preview_dialogue = snapshot.get("preview_dialogue", scene_editor_preview_dialogue)
        scene_editor_frame_insert_step = snapshot.get("frame_insert_step", scene_editor_frame_insert_step)
        scene_editor_ensure_frame_records()
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
        global scene_editor_selected_layer, scene_editor_selected_tag, scene_editor_layers_view
        if tag is not None and scene_editor_item_hidden(layer, tag):
            return
        if layer == scene_editor_ui_layer and tag is not None and tag not in scene_editor_ui_scene():
            return
        scene_editor_selected_layer = layer
        scene_editor_selected_tag = tag
        scene_editor_layers_view = "UI" if layer == scene_editor_ui_layer else "Scenes"
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
        renpy.restart_interaction()

    def scene_editor_layer_tags(layer):
        state = get_image_state(layer)
        ordered = scene_editor_ordered_tags(layer)
        return [tag for tag, _z in ordered if tag in state]

    def scene_editor_layer_panel_tags(layer):
        if scene_editor_is_ui_layer(layer):
            return scene_editor_ui_layer_panel_tags()
        tags = scene_editor_layer_tags(layer)
        tags.reverse()
        return tags

    def scene_editor_rewrite_zorder(layer, tags):
        if scene_editor_is_ui_layer(layer):
            for index, tag in enumerate(tags):
                if tag in scene_editor_ui_scene():
                    scene_editor_ui_scene()[tag]["zorder"] = index
            return
        zorder_list[current_scene][layer] = [(tag, index) for index, tag in enumerate(tags)]

    def scene_editor_append_zorder(layer, tag):
        entries = zorder_list[current_scene].setdefault(layer, [])
        entries.append((tag, len(entries)))

    def scene_editor_layer_render_tags(layer):
        if scene_editor_is_ui_layer(layer):
            return scene_editor_ui_tags(include_hidden=False)
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
            "prev_frame": scene_editor_go_previous_frame,
            "next_frame": scene_editor_go_next_frame,
            "parent_frame": scene_editor_go_parent_frame,
            "child_frame": scene_editor_go_child_frame,
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
        if scene_editor_is_ui_layer():
            return scene_editor_ui_element()
        if scene_editor_selected_tag is None:
            return camera_state_org[current_scene][scene_editor_selected_layer]
        return get_image_state(scene_editor_selected_layer)[scene_editor_selected_tag]

    def scene_editor_property_available(prop):
        state = scene_editor_selected_state()
        if state is None:
            return False
        if scene_editor_is_ui_layer():
            return prop in scene_editor_ui_property_defaults
        if scene_editor_selected_tag is None and prop == "child":
            return False
        return prop in state

    def scene_editor_has_selected():
        layer = scene_editor_selected_layer
        tag = scene_editor_selected_tag
        if scene_editor_is_ui_layer(layer):
            return tag is None or tag in scene_editor_ui_scene()
        if tag is None:
            return layer in camera_state_org[current_scene]
        if scene_editor_item_hidden(layer, tag):
            return False
        return layer in image_state[current_scene] and tag in get_image_state(layer)

    def scene_editor_value_to_string(key):
        try:
            value = scene_editor_get_property_value(key, default=True)
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
            old_value = scene_editor_get_property_value(self.key, default=True)
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
            self.start_value = scene_editor_get_property_value(self.key, default=True)
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
        if isinstance(old_value, str):
            return text
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
        scene_editor_set_property_value(key, value)
        if key[2] == "child":
            scene_editor_child_size_cache.clear()
        if refresh:
            change_time(current_time)

    def scene_editor_toggle_value(key):
        scene_editor_push_history()
        scene_editor_set_value(key, not bool(scene_editor_get_property_value(key, default=True)), push=False)

    def scene_editor_cycle_menu_value(key):
        values = menu_props.get(key[2], [])
        if not values:
            return
        current = scene_editor_get_property_value(key, default=True)
        try:
            index = values.index(current)
        except ValueError:
            index = -1
        scene_editor_set_value(key, values[(index + 1) % len(values)], push=True)

    def scene_editor_reset_value(key):
        scene_editor_push_history()
        scene_editor_reset_property_value(key)
        change_time(current_time)

    def scene_editor_inline_changed(key):
        def changed(text):
            try:
                if key[2] == "child":
                    return
                old_value = scene_editor_get_property_value(key, default=True)
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
        if layer == scene_editor_ui_layer:
            scene_editor_select(scene_editor_ui_layer, None)
            return
        if layer not in image_state[current_scene]:
            return
        scene_editor_select(layer, None)

    def scene_editor_change_scene(scene_num):
        global current_scene
        if scene_num < 0 or scene_num >= len(scene_keyframes):
            return
        current_scene = scene_num
        scene_editor_ensure_frame_records()
        scene_editor_ensure_dialogue_scene(scene_num)
        scene_editor_tree_expanded.add(scene_editor_tree_key("frame", scene_num, scene_num))
        scene_editor_clear_runtime_caches()
        change_time(scene_keyframes[scene_num][1])

    def scene_editor_scene_time(before, scene_num=None):
        if scene_num is None:
            scene_num = current_scene
        if before:
            if scene_num == 0:
                return 0.0
            return round((scene_keyframes[scene_num - 1][1] + scene_keyframes[scene_num][1]) / 2.0, 2)
        if scene_num + 1 < len(scene_keyframes):
            return round((scene_keyframes[scene_num][1] + scene_keyframes[scene_num + 1][1]) / 2.0, 2)
        return round(scene_keyframes[scene_num][1] + scene_editor_frame_insert_step, 2)

    def scene_editor_add_scene(before=False, empty=False, source_scene=None):
        global current_scene
        if source_scene is None:
            source_scene = current_scene
        if source_scene < 0 or source_scene >= len(scene_keyframes):
            return
        insert_at = source_scene if before else source_scene + 1
        new_time = scene_editor_scene_time(before, source_scene)
        scene_editor_ensure_frame_records()
        source_frame_id = scene_editor_frame_records[source_scene].get("id")
        source_parent_id = scene_editor_frame_records[source_scene].get("parent_id")
        new_parent_id = None
        if not empty:
            new_parent_id = source_parent_id if before else source_frame_id
        layers = scene_editor_current_layers(source_scene)
        source_image_state = deepcopy(image_state[source_scene])
        source_image_state_org = deepcopy(image_state_org[source_scene])
        source_camera_state_org = deepcopy(camera_state_org[source_scene])
        source_zorder_list = deepcopy(zorder_list[source_scene])
        source_ui_elements = deepcopy(scene_editor_ensure_ui_scene(source_scene))
        try:
            source_ui_captured_displayables = dict(scene_editor_ui_captured_displayables[source_scene])
        except Exception:
            source_ui_captured_displayables = {}
        source_dialogue_scene = {"entries": []} if empty else deepcopy(scene_editor_ensure_dialogue_scene(source_scene))
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
        scene_editor_ui_elements.insert(insert_at, deepcopy(source_ui_elements))
        scene_editor_ui_captured_displayables.insert(insert_at, {} if empty else dict(source_ui_captured_displayables))
        scene_editor_dialogue_scenes.insert(insert_at, deepcopy(source_dialogue_scene))
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
        scene_editor_frame_records.insert(insert_at, {
            "id": None,
            "route_id": scene_editor_current_route_id,
            "name": "Frame {}".format(insert_at),
            "scene_index": insert_at,
            "parent_id": new_parent_id,
            "time": new_time,
            "inherits": not empty,
            "dialogue_visible": True,
            "notes": "",
        })
        scene_editor_ensure_frame_records()
        new_frame_id = scene_editor_frame_records[insert_at].get("id")
        next_index = insert_at + 1
        if not empty and new_frame_id and next_index < len(scene_editor_frame_records):
            next_record = scene_editor_frame_records[next_index]
            if next_record.get("inherits", True) and next_record.get("parent_id") == new_parent_id:
                next_record["parent_id"] = new_frame_id
        change_time(new_time)

    def scene_editor_add_scene_end(empty=False):
        scene_editor_add_scene(False, empty, len(scene_keyframes) - 1)

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
        if scene_editor_is_ui_layer():
            scene_editor_remove_ui_element(scene_editor_selected_tag)
        else:
            scene_editor_remove_image(scene_editor_selected_layer, scene_editor_selected_tag)
        scene_editor_select(scene_editor_selected_layer, None)
        scene_editor_child_size_cache.clear()
        change_time(current_time)

    def scene_editor_copy_selected():
        global scene_editor_clipboard
        if scene_editor_selected_tag is None:
            renpy.notify(_("Select an object to copy"))
            return
        if scene_editor_is_ui_layer():
            state = scene_editor_ui_element(scene_editor_selected_tag) or {}
            zorder = state.get("zorder", 0)
        else:
            state = get_image_state(scene_editor_selected_layer).get(scene_editor_selected_tag, {})
            zorder = scene_editor_default_added_zorder
            for tag, z in zorder_list[current_scene].get(scene_editor_selected_layer, []):
                if tag == scene_editor_selected_tag:
                    zorder = z
                    break
        clipboard_kind = "ui" if scene_editor_is_ui_layer() else "image"
        scene_editor_clipboard = {
            "kind": clipboard_kind,
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
        if scene_editor_clipboard.get("kind") == "ui":
            scene_editor_push_history()
            state = deepcopy(scene_editor_clipboard["state"])
            base_tag = scene_editor_clipboard.get("tag") or "ui"
            new_tag = scene_editor_ui_unique_tag(base_tag)
            state["zorder"] = max([element.get("zorder", 0) for element in scene_editor_ui_scene().values()] + [-1]) + 1
            scene_editor_ui_scene()[new_tag] = state
            scene_editor_selected_layer = scene_editor_ui_layer
            scene_editor_selected_tag = new_tag
            scene_editor_clear_runtime_caches()
            change_time(current_time)
            return
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
        if child is None:
            fallback_name = scene_editor_image_fallback_paths.get(name)
            if fallback_name:
                try:
                    if hasattr(renpy, "displayable"):
                        child = renpy.displayable(fallback_name)
                    else:
                        child = renpy.easy.displayable(fallback_name)
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
        preview_x, preview_y, preview_zoom = scene_editor_preview_transform_values()
        drag_layer = scene_editor_selected_layer if scene_editor_fast_drag_preview and scene_editor_active_drag_mode and scene_editor_selected_tag else None
        drag_tag = scene_editor_selected_tag if drag_layer else None
        for layer in scene_editor_current_layers():
            if drag_layer and drag_layer != scene_editor_ui_layer and layer != drag_layer:
                continue
            state = get_image_state(layer)
            if not state:
                continue
            layer_scene = Fixed(xsize=config.screen_width, ysize=config.screen_height)
            render_tags = [drag_tag] if drag_layer == layer and drag_tag in state else scene_editor_layer_render_tags(layer)
            for tag in render_tags:
                displayable = scene_editor_render_item(layer, tag, st, at)
                if displayable is not None:
                    layer_scene.add(displayable)
                    count += 1
            if render_tags:
                scene.add(Transform(Transform(layer_scene, **scene_editor_camera_kwargs(layer)), zoom=preview_zoom, xpos=preview_x, ypos=preview_y))
        count += scene_editor_render_ui_scene(scene)
        if not count:
            scene.add(Transform(Text("SceneEditor captured no drawable images", color="#FFFFFF", size=30), xpos=40, ypos=40))
        return scene, count

    def scene_editor_game_preview_displayable(st=0, at=0):
        scene = Fixed(xsize=config.screen_width, ysize=config.screen_height)
        count = 0
        for layer in scene_editor_current_layers():
            state = get_image_state(layer)
            if not state:
                continue
            layer_scene = Fixed(xsize=config.screen_width, ysize=config.screen_height)
            render_tags = scene_editor_layer_render_tags(layer)
            for tag in render_tags:
                displayable = scene_editor_render_item(layer, tag, st, at)
                if displayable is not None:
                    layer_scene.add(displayable)
                    count += 1
            if render_tags:
                scene.add(Transform(layer_scene, **scene_editor_camera_kwargs(layer)))
        count += scene_editor_render_ui_scene(scene)
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
        state = scene_editor_ui_element(tag) if scene_editor_is_ui_layer(layer) else get_image_state(layer).get(tag, {})
        at_list = (state or {}).get("at_list", [])

        def placement_value(prop, size, default_size=None):
            value = scene_editor_get_property_value((tag, layer, prop), default=True)
            default_value = scene_editor_ui_property_defaults.get(prop) if scene_editor_is_ui_layer(layer) else property_default_value.get(prop)
            if at_list and (value is None or value == default_value):
                getter = globals().get("get_at_list_props", None)
                if callable(getter):
                    try:
                        at_value = getter(at_list, prop, current_time, at)
                        if at_value is not None:
                            value = at_value
                    except Exception:
                        pass
            return scene_editor_to_pixel(value, size if default_size is None else default_size)

        xpos = placement_value("xpos", config.screen_width)
        ypos = placement_value("ypos", config.screen_height)
        xanchor = placement_value("xanchor", 1.0)
        yanchor = placement_value("yanchor", 1.0)
        xoffset = scene_editor_direct_number(scene_editor_get_property_value((tag, layer, "xoffset"), default=True), 0)
        yoffset = scene_editor_direct_number(scene_editor_get_property_value((tag, layer, "yoffset"), default=True), 0)
        zoom = scene_editor_get_property_value((tag, layer, "zoom"), default=True)
        xzoom = scene_editor_get_property_value((tag, layer, "xzoom"), default=True)
        yzoom = scene_editor_get_property_value((tag, layer, "yzoom"), default=True)
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
        if scene_editor_is_ui_layer(layer):
            element = scene_editor_ui_element(tag) or {}
            if element.get("kind") in ("panel", "screen"):
                width = int(element.get("xsize", 220))
                height = int(element.get("ysize", 48))
                if element.get("kind") == "screen":
                    try:
                        displayable = scene_editor_ui_captured_displayables[current_scene].get(tag)
                        if displayable is not None:
                            cr = renpy.render(displayable, config.screen_width, config.screen_height, st, at)
                            width, height = cr.get_size()
                    except Exception:
                        pass
            else:
                try:
                    if element.get("image"):
                        text_child = scene_editor_ui_displayable(tag)
                    else:
                        text_child = Text(scene_editor_ui_display_text(element), size=int(element.get("size", 32)), color=element.get("color", "#FFFFFF"), xsize=element.get("xsize", None))
                    cr = renpy.render(text_child, config.screen_width, config.screen_height, st, at)
                    width, height = cr.get_size()
                except Exception:
                    width, height = int(element.get("xsize", 220)), int(element.get("ysize", 48))
        else:
            if state.get("_captured_raw"):
                try:
                    captured = scene_editor_captured_displayables[current_scene].get(layer, {}).get(tag)
                    if captured is not None:
                        cr = renpy.render(captured, config.screen_width, config.screen_height, st, at)
                        width, height = cr.get_size()
                except Exception:
                    pass
            name = scene_editor_child_name(layer, tag)
            if name:
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
        rotate = scene_editor_direct_number(scene_editor_get_property_value((tag, layer, "rotate"), default=True), 0)
        if rotate:
            try:
                from math import radians, cos
                angle = radians(rotate)
                c = abs(cos(angle))
                s = abs(sin(angle))
                rotated_w = width * c + height * s
                rotated_h = width * s + height * c
                cx = x + width / 2.0
                cy = y + height / 2.0
                x = cx - rotated_w / 2.0
                y = cy - rotated_h / 2.0
                width = rotated_w
                height = rotated_h
            except Exception:
                pass
        return x, y, width, height

    def scene_editor_item_rect(layer, tag, st=0, at=0):
        sx, sy, sw, sh = scene_editor_stage_item_rect(layer, tag, st, at)
        offset_x, offset_y, scale = scene_editor_canvas_offsets()
        if scene_editor_is_ui_layer(layer):
            return (
                offset_x + sx * scale,
                offset_y + sy * scale,
                sw * scale,
                sh * scale,
            )
        preview_x, preview_y, preview_zoom = scene_editor_preview_transform_values()
        camera = camera_state_org[current_scene].get(layer, {})
        camera_zoom = scene_editor_direct_number(camera.get("zoom", 1.0), 1.0)
        camera_xzoom = scene_editor_direct_number(camera.get("xzoom", 1.0), 1.0)
        camera_yzoom = scene_editor_direct_number(camera.get("yzoom", 1.0), 1.0)
        camera_x = scene_editor_to_pixel(camera.get("xpos", 0), config.screen_width)
        camera_y = scene_editor_to_pixel(camera.get("ypos", 0), config.screen_height)
        camera_xoffset = scene_editor_direct_number(camera.get("xoffset", 0), 0)
        camera_yoffset = scene_editor_direct_number(camera.get("yoffset", 0), 0)
        sx = camera_x + camera_xoffset + sx * camera_zoom * camera_xzoom
        sy = camera_y + camera_yoffset + sy * camera_zoom * camera_yzoom
        sw = abs(sw * camera_zoom * camera_xzoom)
        sh = abs(sh * camera_zoom * camera_yzoom)
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
        if scene_editor_layers_view == "UI" and scene_editor_selected_layer != scene_editor_ui_layer:
            return None
        if scene_editor_layers_view == "Scenes" and scene_editor_selected_layer == scene_editor_ui_layer:
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
        if scene_editor_layers_view == "UI":
            if not scene_editor_ui_scene_visible:
                return None, None
            for tag in reversed(scene_editor_ui_tags(include_hidden=False)):
                element = scene_editor_ui_element(tag) or {}
                if not element.get("selectable", True):
                    continue
                if scene_editor_item_locked(scene_editor_ui_layer, tag) or scene_editor_item_hidden(scene_editor_ui_layer, tag):
                    continue
                rx, ry, rw, rh = scene_editor_item_rect(scene_editor_ui_layer, tag, st, at)
                if x >= rx and x <= rx + rw and y >= ry and y <= ry + rh:
                    return scene_editor_ui_layer, tag
            return None, None
        if scene_editor_layers_view != "Scenes":
            return None, None
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
                    if not scene_editor_precise_hit_testing or scene_editor_item_hit_opaque(layer, tag, stage_x, stage_y, st, at):
                        return layer, tag
        return fallback_layer, fallback_tag

    def scene_editor_set_position(layer, tag, x, y, refresh=True):
        if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        x = scene_editor_snap_value(x)
        y = scene_editor_snap_value(y)
        scene_editor_set_property_value((tag, layer, "xpos"), int(round(x)))
        scene_editor_set_property_value((tag, layer, "ypos"), int(round(y)))
        if refresh:
            change_time(current_time)

    def scene_editor_set_scale(layer, tag, xzoom, yzoom, refresh=True):
        if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        scene_editor_set_property_value((tag, layer, "xzoom"), max(0.01, round(float(xzoom), 3)))
        scene_editor_set_property_value((tag, layer, "yzoom"), max(0.01, round(float(yzoom), 3)))
        if refresh:
            change_time(current_time)

    def scene_editor_set_rotate(layer, tag, rotate, refresh=True):
        if scene_editor_item_locked(layer, tag) or scene_editor_item_hidden(layer, tag):
            return
        scene_editor_set_property_value((tag, layer, "rotate"), round(float(rotate), 2))
        if refresh:
            change_time(current_time)

    def open_scene_editor():
        global current_time, current_scene, scene_keyframes, zorder_list, sound_keyframes, all_keyframes, playing, in_editor, loops, splines
        global scene_editor_selected_layer, scene_editor_selected_tag, scene_editor_restore_not_included_layer
        global scene_editor_ui_elements, scene_editor_ui_captured_displayables, scene_editor_ui_group_visibility, scene_editor_ui_group_locks, scene_editor_ui_counter, scene_editor_ui_scene_visible, scene_editor_preview_mode, scene_editor_tree_tab, scene_editor_bottom_panel_tab, scene_editor_layers_view, scene_editor_tree_expanded
        global scene_editor_frame_records, scene_editor_frame_counter, scene_editor_dialogue_scenes, scene_editor_dialogue_entry_counter, scene_editor_selected_dialogue_entry_id, scene_editor_export_cache
        global scene_editor_export_visuals, scene_editor_export_ui, scene_editor_export_dialogue, scene_editor_export_scene_clears, scene_editor_export_hidden_ui, scene_editor_preview_dialogue, scene_editor_frame_insert_step
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
        scene_editor_ui_elements = [{}]
        scene_editor_ui_captured_displayables = [{}]
        scene_editor_ui_group_visibility = dict((group, True) for group in scene_editor_ui_groups)
        scene_editor_ui_group_locks = set()
        scene_editor_ui_counter = 0
        scene_editor_ui_scene_visible = True
        scene_editor_preview_mode = False
        scene_editor_tree_tab = "Scene"
        scene_editor_bottom_panel_tab = "Assets"
        scene_editor_layers_view = "Scenes"
        scene_editor_tree_expanded = set([scene_editor_tree_key("frame", 0, 0)])
        scene_editor_frame_records = []
        scene_editor_frame_counter = 0
        scene_editor_dialogue_scenes = [{}]
        scene_editor_dialogue_entry_counter = 0
        scene_editor_selected_dialogue_entry_id = None
        scene_editor_export_cache = ""
        scene_editor_export_visuals = True
        scene_editor_export_ui = True
        scene_editor_export_dialogue = True
        scene_editor_export_scene_clears = True
        scene_editor_export_hidden_ui = False
        scene_editor_preview_dialogue = True
        scene_editor_frame_insert_step = 1.0
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
        scene_editor_capture_live_studio_context()
        scene_editor_init_state()
        scene_editor_ensure_frame_records()
        scene_editor_ensure_dialogue_scene(0)
        scene_editor_history[:] = []
        scene_editor_redo_stack[:] = []
        layers = scene_editor_current_layers()
        has_ui_scene = bool(scene_editor_ui_scene())
        if not layers and not has_ui_scene:
            not_included_layer = scene_editor_restore_not_included_layer
            renpy.notify(_("No editable layers found"))
            return
        if "master" in image_state[current_scene]:
            scene_editor_selected_layer = "master"
        elif layers:
            scene_editor_selected_layer = layers[0]
        else:
            scene_editor_selected_layer = scene_editor_ui_layer
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
