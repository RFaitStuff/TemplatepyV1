init python:
    def _scene_editor_value_box_dims(key, viewers, field_min_width, value_border, value_padding_x, value_char_width):
        box_width = field_min_width
        inner_width = max(12, box_width - 2 * (value_border + value_padding_x))
        return box_width, inner_width


screen scene_editor_button():
    if config.developer:
        textbutton _("Scene Editor") action Function(renpy.invoke_in_new_context, _viewers.open_scene_editor)

screen scene_editor_bottom_dialogue_panel():
    viewport:
        mousewheel True
        scrollbars "vertical"
        yfill True
        has vbox
        spacing _viewers.scene_editor_right_panel_section_spacing
        hbox:
            spacing 8
            xfill True
            text "Dialogue" yalign .5 style "scene_editor_assets_title"
            null xfill True
            textbutton ("Preview On" if _viewers.scene_editor_preview_dialogue else "Preview Off") action Function(_viewers.scene_editor_toggle_setting, "preview_dialogue") selected _viewers.scene_editor_preview_dialogue style "scene_editor_asset_mode_tab_button"
            textbutton ("Frame On" if _viewers.scene_editor_current_dialogue_visible() else "Frame Off") action Function(_viewers.scene_editor_toggle_current_dialogue_visible) selected _viewers.scene_editor_current_dialogue_visible() style "scene_editor_asset_mode_tab_button"
        hbox:
            spacing 6
            style_prefix "scene_editor_tool"
            for entry_type in _viewers.scene_editor_dialogue_entry_types:
                textbutton "+ {}".format(entry_type.title()) action Function(_viewers.scene_editor_add_dialogue_entry, entry_type)
        $ dialogue_entries = _viewers.scene_editor_dialogue_entries()
        if not dialogue_entries:
            text "No dialogue entries for this frame." italic True
        for entry in dialogue_entries:
            $ entry_id = entry.get("id")
            $ entry_selected = entry_id == _viewers.scene_editor_selected_dialogue_entry_id
            button:
                style "scene_editor_layer_row_button"
                action [SelectedIf(entry_selected), Function(_viewers.scene_editor_select_dialogue_entry, entry_id)]
                selected entry_selected
                xfill True
                has vbox
                spacing 3
                text "{} [{}] {}".format(">" if entry_selected else " ", entry.get("type", "line"), entry.get("text", "")) size 13 color ("#FFFFFF" if entry_selected else "#C8D8FF")
                text entry.get("speaker", "") size 11 color "#94A3B8"
            if entry_selected:
                hbox:
                    spacing 4
                    textbutton "Up" action Function(_viewers.scene_editor_move_dialogue_entry, entry_id, -1) style "scene_editor_layer_icon_button"
                    textbutton "Down" action Function(_viewers.scene_editor_move_dialogue_entry, entry_id, 1) style "scene_editor_layer_icon_button"
                    textbutton "Delete" action Function(_viewers.scene_editor_remove_dialogue_entry, entry_id) style "scene_editor_layer_icon_button"
                if entry.get("type") in ("line", "narration", "reaction"):
                    text "Speaker" style "scene_editor_property_label"
                    input default entry.get("speaker", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "speaker") copypaste True xfill True style "scene_editor_property_input"
                if entry.get("type") in ("line", "narration", "reaction", "choice", "jump", "label"):
                    text ("Text" if entry.get("type") not in ("jump", "label") else "Label / Target Text") style "scene_editor_property_label"
                    input default entry.get("text", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "text") copypaste True xfill True style "scene_editor_property_input"
                if entry.get("type") in ("choice", "jump", "label"):
                    text "Target" style "scene_editor_property_label"
                    input default entry.get("target", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "target") copypaste True xfill True style "scene_editor_property_input"
                if entry.get("type") in ("condition", "choice"):
                    text "Condition" style "scene_editor_property_label"
                    input default entry.get("condition", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "condition") copypaste True xfill True style "scene_editor_property_input"
                if entry.get("type") in ("script", "stat", "condition"):
                    text "Payload / Script" style "scene_editor_property_label"
                    input default entry.get("payload", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "payload") copypaste True xfill True style "scene_editor_property_input"
                if entry.get("type") == "choice":
                    text "Choice Options" style "scene_editor_property_label"
                    textbutton "+ Option" action Function(_viewers.scene_editor_add_choice_option, entry_id) style "scene_editor_layer_icon_button"
                    for choice_index in range(len(entry.get("choices", []))):
                        $ choice = entry.get("choices", [])[choice_index]
                        text "Option {} Caption".format(choice_index + 1) size 11 color "#94A3B8"
                        input default choice.get("caption", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "caption") copypaste True xfill True style "scene_editor_property_input"
                        text "Option {} Target".format(choice_index + 1) size 11 color "#94A3B8"
                        input default choice.get("target", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "target") copypaste True xfill True style "scene_editor_property_input"
                        text "Option {} Script".format(choice_index + 1) size 11 color "#94A3B8"
                        input default choice.get("script", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "script") copypaste True xfill True style "scene_editor_property_input"


screen _scene_photo_editor():
    default confirm_exit = False

    key "game_menu" action SetScreenVariable("confirm_exit", True)
    key "scene_editor" action NullAction()
    key "K_ESCAPE" action If(confirm_exit, SetScreenVariable("confirm_exit", False), SetScreenVariable("confirm_exit", True))
    key "ctrl_K_z" action Function(_viewers.scene_editor_handle_shortcut, "undo")
    key "ctrl_K_y" action Function(_viewers.scene_editor_handle_shortcut, "redo")
    key "ctrl_K_c" action Function(_viewers.scene_editor_handle_shortcut, "copy")
    key "ctrl_K_v" action Function(_viewers.scene_editor_handle_shortcut, "paste")
    key "ctrl_K_d" action Function(_viewers.scene_editor_handle_shortcut, "duplicate")
    key "K_DELETE" action Function(_viewers.scene_editor_handle_shortcut, "delete")
    key "K_g" action Function(_viewers.scene_editor_handle_shortcut, "move_tool")
    key "K_s" action Function(_viewers.scene_editor_handle_shortcut, "resize_tool")
    key "K_r" action Function(_viewers.scene_editor_handle_shortcut, "rotate_tool")
    key "K_q" action Function(_viewers.scene_editor_handle_shortcut, "select_tool")
    key "K_x" action Function(_viewers.scene_editor_handle_shortcut, "axis_x")
    key "K_y" action Function(_viewers.scene_editor_handle_shortcut, "axis_y")
    key "ctrl_K_w" action Function(_viewers.scene_editor_handle_shortcut, "forward")
    key "ctrl_K_s" action Function(_viewers.scene_editor_handle_shortcut, "backward")
    key "ctrl_alt_K_w" action Function(_viewers.scene_editor_handle_shortcut, "front")
    key "ctrl_alt_K_s" action Function(_viewers.scene_editor_handle_shortcut, "back")
    key "ctrl_K_1" action Function(_viewers.scene_editor_handle_shortcut, "group")
    key "ctrl_K_2" action Function(_viewers.scene_editor_handle_shortcut, "ungroup")
    key "ctrl_K_3" action Function(_viewers.scene_editor_handle_shortcut, "lock_toggle")
    key "K_PAGEUP" action Function(_viewers.scene_editor_change_scene, max(0, _viewers.current_scene - 1))
    key "K_PAGEDOWN" action Function(_viewers.scene_editor_change_scene, min(len(_viewers.scene_keyframes) - 1, _viewers.current_scene + 1))

    add _viewers.SceneEditorOverlay()

    $ _scene_editor_selected_rect = _viewers.scene_editor_selected_screen_rect()
    if False and _scene_editor_selected_rect is not None and _viewers.scene_editor_tool_mode in ("select", "scale"):
        $ _scene_editor_box_x, _scene_editor_box_y, _scene_editor_box_w, _scene_editor_box_h = _scene_editor_selected_rect
        $ _scene_editor_box_t = _viewers.scene_editor_selection_outline_thickness
        $ _scene_editor_box_color = _viewers.scene_editor_selection_color
        add Solid(_scene_editor_box_color, xsize=max(1, int(_scene_editor_box_w)), ysize=_scene_editor_box_t) xpos int(_scene_editor_box_x) ypos int(_scene_editor_box_y)
        add Solid(_scene_editor_box_color, xsize=max(1, int(_scene_editor_box_w)), ysize=_scene_editor_box_t) xpos int(_scene_editor_box_x) ypos int(_scene_editor_box_y + _scene_editor_box_h - _scene_editor_box_t)
        add Solid(_scene_editor_box_color, xsize=_scene_editor_box_t, ysize=max(1, int(_scene_editor_box_h))) xpos int(_scene_editor_box_x) ypos int(_scene_editor_box_y)
        add Solid(_scene_editor_box_color, xsize=_scene_editor_box_t, ysize=max(1, int(_scene_editor_box_h))) xpos int(_scene_editor_box_x + _scene_editor_box_w - _scene_editor_box_t) ypos int(_scene_editor_box_y)

    frame:
        style_group "scene_photo_toolbar"
        xpos 0
        ypos 0
        xsize config.screen_width
        ysize _viewers.scene_editor_top_height
        has hbox
        spacing 0
        xfill True
        text "Ren'Py live studio" yalign .5 style "scene_editor_logo_text"
        null xfill True
        hbox:
            spacing 6
            yalign .5
            text "Zoom" yalign .5 style "scene_editor_toolbar_zoom_label"
            $ zoom_label = "{:.0f}%".format(_viewers.scene_editor_canvas_zoom * 100)
            frame:
                style "scene_editor_zoom_display_frame"
                has hbox
                spacing 8
                yalign .5
                text zoom_label yalign .5 style "scene_editor_zoom_value_text"
                text "▾" yalign .5 style "scene_editor_zoom_chevron"
            textbutton "−" action SetField(_viewers, "scene_editor_canvas_zoom", max(_viewers.scene_editor_canvas_zoom_min, _viewers.scene_editor_canvas_zoom - _viewers.scene_editor_canvas_zoom_step)) style "scene_editor_zoom_step_button"
            textbutton "+" action SetField(_viewers, "scene_editor_canvas_zoom", min(_viewers.scene_editor_canvas_zoom_max, _viewers.scene_editor_canvas_zoom + _viewers.scene_editor_canvas_zoom_step)) style "scene_editor_zoom_step_button"
        null width 16
        hbox:
            spacing 6
            yalign .5
            text "Snap" yalign .5 style "scene_editor_toolbar_zoom_label"
            textbutton ("On" if _viewers.scene_editor_snap_enabled else "Off") action Function(_viewers.scene_editor_toggle_snap) selected _viewers.scene_editor_snap_enabled style "scene_editor_snap_toggle_button"
            textbutton "{}px".format(_viewers.scene_editor_snap_increment) action Function(_viewers.scene_editor_cycle_snap_increment) style "scene_editor_zoom_step_button"
        null xfill True
        hbox:
            spacing 8
            yalign .5
            if _viewers.scene_editor_axis_constraint is not None:
                text "Axis: {}".format(_viewers.scene_editor_axis_constraint.upper()) yalign .5 color "#8BC6FF" size 14
            textbutton "Preview" action Function(_viewers.scene_editor_set_preview_mode, True) style "scene_editor_toolbar_action_button"
            textbutton "Settings" action Function(_viewers.scene_editor_set_right_panel_tab, "Project") style "scene_editor_toolbar_action_button"
            textbutton "</>  Export Draft" action Function(_viewers.scene_editor_export_live_studio_script) style "scene_editor_toolbar_action_button"
            textbutton "Write Draft" action Function(_viewers.scene_editor_write_live_studio_file) style "scene_editor_toolbar_action_button"
            textbutton "💾  Save" action Function(_viewers.scene_editor_save_project) style "scene_editor_toolbar_action_button"
            textbutton "↺  Load" action Function(_viewers.scene_editor_load_project) style "scene_editor_toolbar_action_button"

    frame:
        style_group "scene_photo_editor"
        xpos 0
        ypos _viewers.scene_editor_top_height
        xsize _viewers.scene_editor_sidebar_width
        ysize config.screen_height - _viewers.scene_editor_top_height
        has vbox
        spacing _viewers.scene_editor_left_panel_spacing
        frame:
            style "scene_editor_panel_header"
            has hbox
            xfill True
            spacing 6
            text "Properties" style "scene_editor_panel_header_text"
            null xfill True
            text "∧" style "scene_editor_panel_header_chevron"
        viewport:
            style_prefix "scene_editor_property_scroll"
            mousewheel True
            scrollbars "vertical"
            ymaximum int((config.screen_height - _viewers.scene_editor_top_height) * 0.52)
            has vbox
            spacing _viewers.scene_editor_property_viewport_spacing
            if _viewers.scene_editor_has_selected():
                if _viewers.scene_editor_selected_tag is None and _viewers.scene_editor_is_ui_layer():
                    text "UI Scene · Persistent UI" style "scene_editor_selection_label"
                elif _viewers.scene_editor_selected_tag is None:
                    text "[_viewers.scene_editor_selected_layer] · Camera" style "scene_editor_selection_label"
                else:
                    text "[_viewers.scene_editor_selected_layer] · [_viewers.scene_editor_selected_tag]" style "scene_editor_selection_label"
                null height 4
                for group_name, props in (_viewers.scene_editor_ui_property_groups if _viewers.scene_editor_is_ui_layer() else _viewers.scene_editor_property_groups):
                    $ group_entries = [(_prop_label, _prop_name) for _prop_label, _prop_name in props if _viewers.scene_editor_property_available(_prop_name)]
                    if group_entries:
                        $ display_group = {"Core": "Transform", "Position": "Appearance", "Anchor / Offset": "Filters & Effects", "3D / Orientation": "Animation", "Crop": "Interaction", "Effects": "Physics", "Pan / Tile": "Custom Properties"}.get(group_name, group_name)
                        if group_name == "Core":
                            $ group_expanded = True
                            text display_group style "scene_editor_property_group_label"
                        else:
                            $ group_expanded = _viewers.scene_editor_property_group_expanded(group_name)
                            button:
                                style "scene_editor_property_group_button"
                                action Function(_viewers.scene_editor_toggle_property_group, group_name)
                                has hbox
                                xfill True
                                text display_group style "scene_editor_property_group_label"
                                null xfill True
                                text ("⌄" if group_expanded else "›") style "scene_editor_property_group_chevron"
                        if group_expanded:
                            frame:
                                style "scene_editor_property_group_frame"
                                has vbox
                                spacing _viewers.scene_editor_property_group_spacing
                                python:
                                    pair_label_overrides = {
                                        "pos": "Position",
                                        "position": "Position",
                                        "size": "Size",
                                        "anchor": "Anchor",
                                        "offset": "Offset",
                                    }
                                    grouped_rows = []
                                    i = 0
                                    while i < len(group_entries):
                                        label, name = group_entries[i]
                                        next_entry = group_entries[i + 1] if i + 1 < len(group_entries) else None
                                        pairable_prefix = next_entry and label.startswith("X") and next_entry[0].startswith("Y")
                                        pairable_suffix = next_entry and label.endswith("X") and next_entry[0].endswith("Y")
                                        if pairable_prefix or pairable_suffix:
                                            grouped_rows.append({"type": "pair", "x": (label, name), "y": next_entry})
                                            i += 2
                                        else:
                                            grouped_rows.append({"type": "single", "label": label, "name": name})
                                            i += 1
                                $ field_min_width = _viewers.scene_editor_property_field_width
                                $ field_height = _viewers.scene_editor_property_field_height
                                $ value_border = 1
                                $ value_padding_x = 4
                                $ value_padding_y = 2
                                $ value_border_color = "#23314D"
                                $ value_fill_color = "#0E1628"
                                $ value_input_allow = "0123456789.-"
                                $ value_char_width = 9
                                $ field_inner_height = max(12, field_height - 2 * (value_border + value_padding_y))
                                for row in grouped_rows:
                                    if row["type"] == "pair":
                                        $ x_label, x_name = row["x"]
                                        $ y_label, y_name = row["y"]
                                        $ base_label = x_label.strip("XY") or x_label
                                        $ base_label = pair_label_overrides.get(base_label.lower(), base_label.capitalize())
                                        $ x_key = _viewers.scene_editor_selected_key(x_name)
                                        $ y_key = _viewers.scene_editor_selected_key(y_name)
                                        frame:
                                            style "scene_editor_property_row_frame"
                                            xfill True
                                            has vbox
                                            spacing 4
                                            hbox:
                                                spacing 6
                                                xfill True
                                                text base_label style "scene_editor_property_pair_label"
                                                null xfill True
                                                for axis_label, axis_key in (("X", x_key), ("Y", y_key)):
                                                    hbox:
                                                        spacing 4
                                                        yalign 0.0
                                                        text axis_label style "scene_editor_axis_label"
                                                        $ box_width, inner_width = _scene_editor_value_box_dims(axis_key, _viewers, field_min_width, value_border, value_padding_x, value_char_width)
                                                        fixed:
                                                            xsize box_width
                                                            ysize field_height
                                                            add Transform(Solid(value_border_color), xsize=box_width, ysize=field_height)
                                                            add Transform(Solid(value_fill_color), xpos=value_border, ypos=value_border, xsize=box_width - value_border * 2, ysize=field_height - value_border * 2)
                                                            if _viewers.scene_editor_is_editing_value(axis_key):
                                                                input value _viewers.scene_editor_property_input_value(axis_key) copypaste True allow value_input_allow xsize inner_width ysize field_inner_height style "scene_editor_property_input" xpos value_border + value_padding_x ypos value_border + value_padding_y
                                                            else:
                                                                add _viewers.SceneEditorDraggableValue(axis_key, xsize=inner_width, ysize=field_inner_height) xpos value_border + value_padding_x ypos value_border + value_padding_y
                                    else:
                                        $ label = row["label"]
                                        $ name = row["name"]
                                        $ prop_key = _viewers.scene_editor_selected_key(name)
                                        frame:
                                            style "scene_editor_property_row_frame"
                                            xfill True
                                            has hbox
                                            spacing 8
                                            text label style "scene_editor_property_label"
                                            null width 4
                                            null xfill True
                                            if name == "child":
                                                textbutton _viewers.scene_editor_value_to_string(prop_key) action Function(_viewers.scene_editor_flash_selected) style "scene_editor_child_name_button"
                                            elif name == "function":
                                                input default _viewers.scene_editor_value_to_string(prop_key) changed _viewers.scene_editor_inline_changed(prop_key) copypaste True xfill True style "scene_editor_property_input"
                                            elif _viewers.scene_editor_is_ui_layer() and name in ("text", "bound_variable", "color", "background", "image"):
                                                input default _viewers.scene_editor_value_to_string(prop_key) changed _viewers.scene_editor_inline_changed(prop_key) copypaste True xfill True style "scene_editor_property_input"
                                            elif _viewers.scene_editor_is_ui_layer() and name == "visible":
                                                textbutton _viewers.scene_editor_value_to_string(prop_key) action Function(_viewers.scene_editor_toggle_value, prop_key) style "scene_editor_property_value_button"
                                            elif _viewers.scene_editor_is_ui_layer() and name in ("kind", "group"):
                                                textbutton _viewers.scene_editor_value_to_string(prop_key) action Function(_viewers.scene_editor_cycle_ui_choice, prop_key) style "scene_editor_property_value_button"
                                            elif name in _viewers.boolean_props:
                                                textbutton _viewers.scene_editor_value_to_string(prop_key) action Function(_viewers.scene_editor_toggle_value, prop_key) style "scene_editor_property_value_button"
                                            elif name in _viewers.menu_props:
                                                textbutton _viewers.scene_editor_value_to_string(prop_key) action Function(_viewers.scene_editor_cycle_menu_value, prop_key) style "scene_editor_property_value_button"
                                            else:
                                                $ box_width, inner_width = _scene_editor_value_box_dims(prop_key, _viewers, field_min_width, value_border, value_padding_x, value_char_width)
                                                fixed:
                                                    xsize box_width
                                                    ysize field_height
                                                    add Transform(Solid(value_border_color), xsize=box_width, ysize=field_height)
                                                    add Transform(Solid(value_fill_color), xpos=value_border, ypos=value_border, xsize=box_width - value_border * 2, ysize=field_height - value_border * 2)
                                                    if _viewers.scene_editor_is_editing_value(prop_key):
                                                        input value _viewers.scene_editor_property_input_value(prop_key) copypaste True allow value_input_allow xsize inner_width ysize field_inner_height style "scene_editor_property_input" xpos value_border + value_padding_x ypos value_border + value_padding_y
                                                    else:
                                                        add _viewers.SceneEditorDraggableValue(prop_key, xsize=inner_width, ysize=field_inner_height) xpos value_border + value_padding_x ypos value_border + value_padding_y
            else:
                text _("Select an image, UI element, or camera from the scene tree.") style "scene_editor_selection_label"
        null height 2
        frame:
            style "scene_editor_panel_header"
            has hbox
            xfill True
            null xfill True
            hbox:
                spacing 4
                xalign 0.5
                style_prefix "scene_editor_tab"
                textbutton "Scene" action Function(_viewers.scene_editor_set_tree_tab, "Scene") selected _viewers.scene_editor_tree_tab == "Scene"
                textbutton "Frame" action Function(_viewers.scene_editor_set_tree_tab, "Frame") selected _viewers.scene_editor_tree_tab == "Frame"
            null xfill True
        viewport:
            mousewheel True
            scrollbars "vertical"
            yfill True
            has vbox
            spacing _viewers.scene_editor_scene_tree_spacing
            if _viewers.scene_editor_tree_tab == "Scene":
                hbox:
                    spacing 4
                    xalign 0.5
                    textbutton "+ Frame" action Function(_viewers.scene_editor_add_scene, False, False) style "scene_editor_layer_icon_button"
                    textbutton "+ Dialogue" action [Function(_viewers.scene_editor_set_bottom_panel_tab, "Dialogue"), Function(_viewers.scene_editor_add_dialogue_entry, "line")] style "scene_editor_layer_icon_button"
                for i, scene_data in enumerate(_viewers.scene_keyframes):
                    $ scene_open = _viewers.scene_editor_tree_is_expanded("frame", i, i)
                    $ scene_selected = i == _viewers.current_scene
                    $ can_move_selected_here = (not scene_selected) and _viewers.scene_editor_selected_tag is not None and not _viewers.scene_editor_is_ui_layer()
                    if can_move_selected_here:
                        textbutton "    Move selected here" action Function(_viewers.scene_editor_move_image_to_scene, _viewers.current_scene, _viewers.scene_editor_selected_layer, _viewers.scene_editor_selected_tag, i) style "scene_editor_tree_button"
                    textbutton "{} {}{}".format("⌄" if scene_open else "›", _viewers.scene_editor_frame_label(i), " · current" if scene_selected else "") action [SelectedIf(scene_selected), Function(_viewers.scene_editor_change_scene, i), Function(_viewers.scene_editor_toggle_tree_expanded, "frame", i, i)] style "scene_editor_tree_button"
                    if scene_open:
                        $ current_layers = _viewers.scene_editor_current_layers(i)
                        for l in current_layers:
                            $ layer_open = _viewers.scene_editor_tree_is_expanded("layer", l, i)
                            $ layer_selected = i == _viewers.current_scene and l == _viewers.scene_editor_selected_layer and _viewers.scene_editor_selected_tag is None
                            textbutton "  {} {}".format("⌄" if layer_open else "›", l) action [SelectedIf(layer_selected), Function(_viewers.scene_editor_change_scene, i), Function(_viewers.scene_editor_change_layer, l), Function(_viewers.scene_editor_toggle_tree_expanded, "layer", l, i)] style "scene_editor_tree_button"
                            if layer_open and i == _viewers.current_scene:
                                $ _scene_layer_state = _viewers.get_image_state(l) if hasattr(_viewers, "get_image_state") else (_viewers.image_state[_viewers.current_scene].get(l, {}) if hasattr(_viewers, "image_state") else {})
                                for tag in _scene_layer_state:
                                    $ tag_selected = l == _viewers.scene_editor_selected_layer and tag == _viewers.scene_editor_selected_tag
                                    textbutton "      {}".format(tag) action [SelectedIf(tag_selected), Function(_viewers.scene_editor_select, l, tag)] style "scene_editor_tree_button"
                        if i == _viewers.current_scene:
                            $ ui_open = _viewers.scene_editor_tree_is_expanded("ui", "scene", i)
                            $ ui_layer_selected = _viewers.scene_editor_selected_layer == _viewers.scene_editor_ui_layer and _viewers.scene_editor_selected_tag is None
                            textbutton "  {} UI".format("⌄" if ui_open else "›") action [SelectedIf(ui_layer_selected), Function(_viewers.scene_editor_change_layer, _viewers.scene_editor_ui_layer), Function(_viewers.scene_editor_toggle_tree_expanded, "ui", "scene", i)] style "scene_editor_tree_button"
                            if ui_open:
                                hbox:
                                    spacing 4
                                    textbutton "+ Text" action Function(_viewers.scene_editor_add_ui_element, "text", "overlays") style "scene_editor_layer_icon_button"
                                    textbutton "+ Value" action Function(_viewers.scene_editor_add_ui_element, "value", "stats") style "scene_editor_layer_icon_button"
                                    textbutton "+ Panel" action Function(_viewers.scene_editor_add_ui_element, "panel", "overlays") style "scene_editor_layer_icon_button"
                                for group in _viewers.scene_editor_ui_groups:
                                    $ group_open = _viewers.scene_editor_tree_is_expanded("ui_group", group, i)
                                    $ group_visible = _viewers.scene_editor_ui_group_visible(group)
                                    textbutton "      {} {} {}".format("⌄" if group_open else "›", "👁" if group_visible else "🙈", _viewers.scene_editor_ui_group_label(group)) action Function(_viewers.scene_editor_toggle_tree_expanded, "ui_group", group, i) style "scene_editor_tree_button"
                                    if group_open:
                                        for tag in [tag for tag in _viewers.scene_editor_ui_layer_panel_tags() if (_viewers.scene_editor_ui_element(tag) or {}).get("group") == group]:
                                            $ tag_selected = _viewers.scene_editor_selected_layer == _viewers.scene_editor_ui_layer and tag == _viewers.scene_editor_selected_tag
                                            textbutton "          {}".format(tag) action [SelectedIf(tag_selected), Function(_viewers.scene_editor_select, _viewers.scene_editor_ui_layer, tag)] style "scene_editor_tree_button"
            elif _viewers.scene_editor_tree_tab == "Frame":
                text "Current: {}".format(_viewers.scene_editor_current_frame_label()) style "scene_editor_selection_label"
                hbox:
                    spacing 4
                    textbutton "+ Before" action Function(_viewers.scene_editor_add_scene, True, False) style "scene_editor_layer_icon_button"
                    textbutton "+ After" action Function(_viewers.scene_editor_add_scene, False, False) style "scene_editor_layer_icon_button"
                    textbutton "+ End" action Function(_viewers.scene_editor_add_scene_end, False) style "scene_editor_layer_icon_button"
                hbox:
                    spacing 4
                    textbutton "Prev" action Function(_viewers.scene_editor_go_previous_frame) style "scene_editor_layer_icon_button"
                    textbutton "Next" action Function(_viewers.scene_editor_go_next_frame) style "scene_editor_layer_icon_button"
                    textbutton "Parent" action Function(_viewers.scene_editor_go_parent_frame) style "scene_editor_layer_icon_button"
                    textbutton "Child" action Function(_viewers.scene_editor_go_child_frame) style "scene_editor_layer_icon_button"
                for frame_row in _viewers.scene_editor_frame_tree_rows():
                    $ i = frame_row[0]
                    $ depth = frame_row[1]
                    $ frame_record = frame_row[2]
                    $ frame_selected = i == _viewers.current_scene
                    $ frame_indent = depth * 12
                    textbutton "{}{} {}{}".format(" " * int(depth * 2), "▶" if frame_selected else " ", frame_record.get("name", "Frame"), "" if frame_record.get("dialogue_visible", True) else " · no dialogue") action [SelectedIf(frame_selected), Function(_viewers.scene_editor_change_scene, i)] style "scene_editor_tree_button"
                    if frame_selected:
                        input default frame_record.get("name", "") changed _viewers.scene_editor_frame_name_changed(i) copypaste True xfill True style "scene_editor_property_input"
                        text "Notes" style "scene_editor_property_label"
                        input default frame_record.get("notes", "") changed _viewers.scene_editor_frame_notes_changed(i) copypaste True xfill True style "scene_editor_property_input"
                        textbutton ("Dialogue Visible" if _viewers.scene_editor_current_dialogue_visible() else "Dialogue Hidden") action Function(_viewers.scene_editor_toggle_current_dialogue_visible) selected _viewers.scene_editor_current_dialogue_visible() style "scene_editor_property_value_button"
                        if i > 0:
                            textbutton ("Inherits: On" if frame_record.get("inherits") else "Inherits: Off") action Function(_viewers.scene_editor_set_frame_inherits, i, not frame_record.get("inherits")) style "scene_editor_property_value_button"
            else:
                text "Dialogue · {}".format(_viewers.scene_editor_current_frame_id() or "frame") style "scene_editor_selection_label"
                textbutton ("Preview On" if _viewers.scene_editor_preview_dialogue else "Preview Off") action Function(_viewers.scene_editor_toggle_setting, "preview_dialogue") selected _viewers.scene_editor_preview_dialogue style "scene_editor_property_value_button"
                textbutton ("Frame Visible" if _viewers.scene_editor_current_dialogue_visible() else "Frame Hidden") action Function(_viewers.scene_editor_toggle_current_dialogue_visible) selected _viewers.scene_editor_current_dialogue_visible() style "scene_editor_property_value_button"
                hbox:
                    spacing 4
                    style_prefix "scene_editor_tool"
                    for entry_type in _viewers.scene_editor_dialogue_entry_types:
                        textbutton "+ {}".format(entry_type.title()) action Function(_viewers.scene_editor_add_dialogue_entry, entry_type)
                $ dialogue_entries = _viewers.scene_editor_dialogue_entries()
                if not dialogue_entries:
                    text "No dialogue entries for this frame." italic True
                for entry in dialogue_entries:
                    $ entry_id = entry.get("id")
                    $ entry_selected = entry_id == _viewers.scene_editor_selected_dialogue_entry_id
                    button:
                        style "scene_editor_layer_row_button"
                        action [SelectedIf(entry_selected), Function(_viewers.scene_editor_select_dialogue_entry, entry_id)]
                        selected entry_selected
                        xfill True
                        has vbox
                        spacing 3
                        text "{} [{}] {}".format("▶" if entry_selected else " ", entry.get("type", "line"), entry.get("text", "")) size 13 color ("#FFFFFF" if entry_selected else "#C8D8FF")
                        text entry.get("speaker", "") size 11 color "#94A3B8"
                    if entry_selected:
                        hbox:
                            spacing 4
                            textbutton "↑" action Function(_viewers.scene_editor_move_dialogue_entry, entry_id, -1) style "scene_editor_layer_icon_button"
                            textbutton "↓" action Function(_viewers.scene_editor_move_dialogue_entry, entry_id, 1) style "scene_editor_layer_icon_button"
                            textbutton "Delete" action Function(_viewers.scene_editor_remove_dialogue_entry, entry_id) style "scene_editor_layer_icon_button"
                        if entry.get("type") in ("line", "narration", "reaction"):
                            text "Speaker" style "scene_editor_property_label"
                            input default entry.get("speaker", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "speaker") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("line", "narration", "reaction", "choice", "jump", "label"):
                            text ("Text" if entry.get("type") not in ("jump", "label") else "Label / Target Text") style "scene_editor_property_label"
                            input default entry.get("text", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "text") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("choice", "jump", "label"):
                            text "Target" style "scene_editor_property_label"
                            input default entry.get("target", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "target") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("condition", "choice"):
                            text "Condition" style "scene_editor_property_label"
                            input default entry.get("condition", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "condition") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("script", "stat", "condition"):
                            text "Payload / Script" style "scene_editor_property_label"
                            input default entry.get("payload", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "payload") copypaste True xfill True style "scene_editor_property_input"
                        text "On Show Script" style "scene_editor_property_label"
                        input default entry.get("on_show", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "on_show") copypaste True xfill True style "scene_editor_property_input"
                        text "On Advance Script" style "scene_editor_property_label"
                        input default entry.get("on_advance", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "on_advance") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") == "choice":
                            text "On Select Script" style "scene_editor_property_label"
                            input default entry.get("on_select", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "on_select") copypaste True xfill True style "scene_editor_property_input"
                            text "Choice Options" style "scene_editor_property_label"
                            textbutton "+ Option" action Function(_viewers.scene_editor_add_choice_option, entry_id) style "scene_editor_layer_icon_button"
                            for choice_index in range(len(entry.get("choices", []))):
                                $ choice = entry.get("choices", [])[choice_index]
                                text "Option {} Caption".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("caption", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "caption") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Target".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("target", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "target") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Condition".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("condition", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "condition") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Script".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("script", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "script") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Merge Target".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("merge_target", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "merge_target") copypaste True xfill True style "scene_editor_property_input"
                                textbutton "Remove Option" action Function(_viewers.scene_editor_remove_choice_option, entry_id, choice_index) style "scene_editor_layer_icon_button"

    frame:
        style_group "scene_photo_properties"
        xpos config.screen_width - _viewers.scene_editor_right_sidebar_width
        ypos _viewers.scene_editor_top_height
        xsize _viewers.scene_editor_right_sidebar_width
        ysize config.screen_height - _viewers.scene_editor_top_height - _viewers.scene_editor_bottom_height
        has vbox
        spacing _viewers.scene_editor_right_panel_spacing
        frame:
            style "scene_editor_panel_tab_bar"
            hbox:
                style_prefix "scene_editor_tab"
                spacing _viewers.scene_editor_right_panel_tab_spacing
                textbutton "Layers" action Function(_viewers.scene_editor_set_right_panel_tab, "Layers") selected _viewers.scene_editor_right_panel_tab == "Layers"
                textbutton "Project" action Function(_viewers.scene_editor_set_right_panel_tab, "Project") selected _viewers.scene_editor_right_panel_tab == "Project"
                textbutton "History" action Function(_viewers.scene_editor_set_right_panel_tab, "History") selected _viewers.scene_editor_right_panel_tab == "History"
        if _viewers.scene_editor_right_panel_tab == "Layers":
            frame:
                style "scene_editor_blend_mode_bar"
                has hbox
                xfill True
                spacing 6
                style_prefix "scene_editor_tab"
                textbutton "Scenes" action Function(_viewers.scene_editor_set_layers_view, "Scenes") selected _viewers.scene_editor_layers_view == "Scenes"
                textbutton "UI" action Function(_viewers.scene_editor_set_layers_view, "UI") selected _viewers.scene_editor_layers_view == "UI"
                null xfill True
                if _viewers.scene_editor_layers_view == "UI":
                    textbutton ("UI Visible" if _viewers.scene_editor_ui_scene_visible else "UI Hidden") action Function(_viewers.scene_editor_toggle_ui_scene_visible) selected _viewers.scene_editor_ui_scene_visible style "scene_editor_layer_icon_button"
            viewport:
                mousewheel True
                scrollbars "vertical"
                yfill True
                has vbox
                spacing 0
                if _viewers.scene_editor_layers_view == "Scenes":
                    for layer in _viewers.scene_editor_current_layers():
                        if layer in _viewers.zorder_list[_viewers.current_scene]:
                            $ _scene_layer_state = _viewers.get_image_state(layer) if hasattr(_viewers, "get_image_state") else (_viewers.image_state[_viewers.current_scene].get(layer, {}) if hasattr(_viewers, "image_state") else {})
                            for tag in _viewers.scene_editor_layer_panel_tags(layer):
                                if tag in _scene_layer_state:
                                    $ tag_selected = layer == _viewers.scene_editor_selected_layer and tag == _viewers.scene_editor_selected_tag
                                    $ tag_locked = _viewers.scene_editor_item_locked(layer, tag)
                                    $ tag_hidden = _viewers.scene_editor_item_hidden(layer, tag)
                                    $ tag_grouped = _viewers.scene_editor_item_group(layer, tag) is not None
                                    $ child_name = _viewers.scene_editor_child_name(layer, tag)
                                    hbox:
                                        style "scene_editor_layer_row_container"
                                        spacing 8
                                        xfill True
                                        button:
                                            style "scene_editor_layer_row_button"
                                            action [SelectedIf(tag_selected), Function(_viewers.scene_editor_select, layer, tag)]
                                            selected tag_selected
                                            xfill True
                                            has hbox
                                            spacing 10
                                            frame:
                                                style "scene_editor_layer_thumb_frame"
                                                xsize _viewers.scene_editor_layer_thumb_size
                                                ysize _viewers.scene_editor_layer_thumb_size
                                                xalign 0.5
                                                yalign 0.5
                                                if child_name:
                                                    add Transform(_viewers.scene_editor_asset_thumbnail(child_name, _viewers.scene_editor_layer_thumb_size - 8, _viewers.scene_editor_layer_thumb_size - 8), xalign=0.5, yalign=0.5)
                                            vbox:
                                                xfill True
                                                yalign 0.5
                                                spacing 3
                                                text "{}{}".format("▣ " if tag_grouped else "", tag) size 14 color ("#7B88A8" if tag_hidden else "#FFFFFF")
                                                text child_name size 11 color "#94A3B8"
                                        hbox:
                                            style "scene_editor_layer_row_actions"
                                            spacing 4
                                            yalign 0.5
                                            textbutton ("🔒" if tag_locked else "🔓") action Function(_viewers.scene_editor_toggle_lock, layer, tag) style "scene_editor_layer_icon_button"
                                            textbutton ("🙈" if tag_hidden else "👁") action Function(_viewers.scene_editor_toggle_hidden, layer, tag) style "scene_editor_layer_icon_button"
                else:
                    for group in _viewers.scene_editor_ui_groups:
                        $ group_visible = _viewers.scene_editor_ui_group_visible(group)
                        $ group_locked = _viewers.scene_editor_ui_group_locked(group)
                        hbox:
                            style "scene_editor_layer_row_container"
                            spacing 8
                            xfill True
                            textbutton _viewers.scene_editor_ui_group_label(group) action Function(_viewers.scene_editor_toggle_ui_group, group) style "scene_editor_tree_button" xfill True
                            hbox:
                                style "scene_editor_layer_row_actions"
                                spacing 4
                                yalign 0.5
                                textbutton ("🔒" if group_locked else "🔓") action Function(_viewers.scene_editor_toggle_ui_group_lock, group) style "scene_editor_layer_icon_button"
                                textbutton ("👁" if group_visible else "🙈") action Function(_viewers.scene_editor_toggle_ui_group, group) style "scene_editor_layer_icon_button"
                        for tag in [tag for tag in _viewers.scene_editor_ui_layer_panel_tags() if (_viewers.scene_editor_ui_element(tag) or {}).get("group") == group]:
                            $ _ui_element = _viewers.scene_editor_ui_element(tag) or {}
                            $ tag_selected = _viewers.scene_editor_selected_layer == _viewers.scene_editor_ui_layer and tag == _viewers.scene_editor_selected_tag
                            $ tag_locked = _viewers.scene_editor_item_locked(_viewers.scene_editor_ui_layer, tag)
                            $ tag_hidden = _viewers.scene_editor_item_hidden(_viewers.scene_editor_ui_layer, tag) or not _ui_element.get("visible", True) or not _viewers.scene_editor_ui_group_visible(_ui_element.get("group", "overlays")) or not _viewers.scene_editor_ui_scene_visible
                            hbox:
                                style "scene_editor_layer_row_container"
                                spacing 8
                                xfill True
                                button:
                                    style "scene_editor_layer_row_button"
                                    action [SelectedIf(tag_selected), Function(_viewers.scene_editor_select, _viewers.scene_editor_ui_layer, tag)]
                                    selected tag_selected
                                    xfill True
                                    has hbox
                                    spacing 10
                                    frame:
                                        style "scene_editor_layer_thumb_frame"
                                        xsize _viewers.scene_editor_layer_thumb_size
                                        ysize _viewers.scene_editor_layer_thumb_size
                                        xalign 0.5
                                        yalign 0.5
                                        text ("▭" if _ui_element.get("kind") == "panel" else ("ƒ" if _ui_element.get("kind") == "value" else "T")) size 20 xalign .5 yalign .5
                                    vbox:
                                        xfill True
                                        yalign 0.5
                                        spacing 3
                                        text tag size 14 color ("#7B88A8" if tag_hidden else "#FFFFFF")
                                        text _viewers.scene_editor_ui_group_label(_ui_element.get("group", "overlays")) size 11 color "#94A3B8"
                                hbox:
                                    style "scene_editor_layer_row_actions"
                                    spacing 4
                                    yalign 0.5
                                    textbutton ("🔒" if tag_locked else "🔓") action Function(_viewers.scene_editor_toggle_lock, _viewers.scene_editor_ui_layer, tag) style "scene_editor_layer_icon_button"
                                    textbutton ("🙈" if tag_hidden else "👁") action Function(_viewers.scene_editor_toggle_hidden, _viewers.scene_editor_ui_layer, tag) style "scene_editor_layer_icon_button"
        elif _viewers.scene_editor_right_panel_tab == "Frames":
            viewport:
                mousewheel True
                scrollbars "vertical"
                yfill True
                has vbox
                spacing _viewers.scene_editor_right_panel_section_spacing
                text "Current: {}".format(_viewers.scene_editor_current_frame_label()) style "scene_editor_selection_label"
                hbox:
                    spacing 6
                    textbutton "Prev" action Function(_viewers.scene_editor_go_previous_frame) style "scene_editor_layer_icon_button"
                    textbutton "Next" action Function(_viewers.scene_editor_go_next_frame) style "scene_editor_layer_icon_button"
                    textbutton "Parent" action Function(_viewers.scene_editor_go_parent_frame) style "scene_editor_layer_icon_button"
                    textbutton "Child" action Function(_viewers.scene_editor_go_child_frame) style "scene_editor_layer_icon_button"
                hbox:
                    spacing 6
                    textbutton "+ Before" action Function(_viewers.scene_editor_add_scene, True, False) style "scene_editor_tool_button"
                    textbutton "+ After" action Function(_viewers.scene_editor_add_scene, False, False) style "scene_editor_tool_button"
                    textbutton "+ End" action Function(_viewers.scene_editor_add_scene_end, False) style "scene_editor_tool_button"
                hbox:
                    spacing 6
                    textbutton "+ Empty After" action Function(_viewers.scene_editor_add_scene, False, True) style "scene_editor_tool_button"
                    textbutton "+ Empty End" action Function(_viewers.scene_editor_add_scene_end, True) style "scene_editor_tool_button"
                textbutton ("Dialogue Visible" if _viewers.scene_editor_current_dialogue_visible() else "Dialogue Hidden") action Function(_viewers.scene_editor_toggle_current_dialogue_visible) selected _viewers.scene_editor_current_dialogue_visible() style "scene_editor_property_value_button"
                for frame_row in _viewers.scene_editor_frame_tree_rows():
                    $ i = frame_row[0]
                    $ depth = frame_row[1]
                    $ frame_record = frame_row[2]
                    $ frame_selected = i == _viewers.current_scene
                    $ frame_indent = depth * 12
                    button:
                        style "scene_editor_layer_row_button"
                        action [SelectedIf(frame_selected), Function(_viewers.scene_editor_change_scene, i)]
                        selected frame_selected
                        xfill True
                        has hbox
                        spacing 4
                        null width frame_indent
                        vbox:
                            spacing 4
                            text "{} {}{}".format("▶" if frame_selected else " ", frame_record.get("name", "Frame"), "" if frame_record.get("dialogue_visible", True) else " · no dialogue") size 14 color ("#FFFFFF" if frame_selected else "#C8D8FF")
                            text "{} · parent {}".format(frame_record.get("id", ""), frame_record.get("parent_id") or "root") size 11 color "#94A3B8"
                    if frame_selected:
                        input default frame_record.get("name", "") changed _viewers.scene_editor_frame_name_changed(i) copypaste True xfill True style "scene_editor_property_input"
                        text "Notes" style "scene_editor_property_label"
                        input default frame_record.get("notes", "") changed _viewers.scene_editor_frame_notes_changed(i) copypaste True xfill True style "scene_editor_property_input"
                        if i > 0:
                            textbutton ("Inherits: On" if frame_record.get("inherits") else "Inherits: Off") action Function(_viewers.scene_editor_set_frame_inherits, i, not frame_record.get("inherits")) style "scene_editor_property_value_button"
        elif _viewers.scene_editor_right_panel_tab == "Dialogue":
            viewport:
                mousewheel True
                scrollbars "vertical"
                yfill True
                has vbox
                spacing _viewers.scene_editor_right_panel_section_spacing
                text "Dialogue · {}".format(_viewers.scene_editor_current_frame_id() or "frame") style "scene_editor_selection_label"
                textbutton ("Preview Dialogue On" if _viewers.scene_editor_preview_dialogue else "Preview Dialogue Off") action Function(_viewers.scene_editor_toggle_setting, "preview_dialogue") selected _viewers.scene_editor_preview_dialogue style "scene_editor_property_value_button"
                textbutton ("Frame Dialogue Visible" if _viewers.scene_editor_current_dialogue_visible() else "Frame Dialogue Hidden") action Function(_viewers.scene_editor_toggle_current_dialogue_visible) selected _viewers.scene_editor_current_dialogue_visible() style "scene_editor_property_value_button"
                hbox:
                    spacing 4
                    style_prefix "scene_editor_tool"
                    for entry_type in _viewers.scene_editor_dialogue_entry_types:
                        textbutton "+ {}".format(entry_type.title()) action Function(_viewers.scene_editor_add_dialogue_entry, entry_type)
                $ dialogue_entries = _viewers.scene_editor_dialogue_entries()
                if not dialogue_entries:
                    text "No dialogue entries for this frame." italic True
                for entry in dialogue_entries:
                    $ entry_id = entry.get("id")
                    $ entry_selected = entry_id == _viewers.scene_editor_selected_dialogue_entry_id
                    button:
                        style "scene_editor_layer_row_button"
                        action [SelectedIf(entry_selected), Function(_viewers.scene_editor_select_dialogue_entry, entry_id)]
                        selected entry_selected
                        xfill True
                        has vbox
                        spacing 3
                        text "{} [{}] {}".format("▶" if entry_selected else " ", entry.get("type", "line"), entry.get("text", "")) size 13 color ("#FFFFFF" if entry_selected else "#C8D8FF")
                        text entry.get("speaker", "") size 11 color "#94A3B8"
                    if entry_selected:
                        hbox:
                            spacing 4
                            textbutton "↑" action Function(_viewers.scene_editor_move_dialogue_entry, entry_id, -1) style "scene_editor_layer_icon_button"
                            textbutton "↓" action Function(_viewers.scene_editor_move_dialogue_entry, entry_id, 1) style "scene_editor_layer_icon_button"
                            textbutton "Delete" action Function(_viewers.scene_editor_remove_dialogue_entry, entry_id) style "scene_editor_layer_icon_button"
                        if entry.get("type") in ("line", "narration", "reaction"):
                            text "Speaker" style "scene_editor_property_label"
                            hbox:
                                spacing 4
                                for char_pair in _viewers.scene_editor_known_characters():
                                    $ char_id = char_pair[0]
                                    $ char_label = char_pair[1]
                                    textbutton char_label action Function(_viewers.scene_editor_set_dialogue_speaker, entry_id, char_id) selected entry.get("speaker", "") == char_id style "scene_editor_layer_icon_button"
                            input default entry.get("speaker", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "speaker") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("line", "narration", "reaction", "choice", "jump", "label"):
                            text ("Text" if entry.get("type") not in ("jump", "label") else "Label / Target Text") style "scene_editor_property_label"
                            input default entry.get("text", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "text") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("choice", "jump", "label"):
                            text "Target" style "scene_editor_property_label"
                            input default entry.get("target", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "target") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("condition", "choice"):
                            text "Condition" style "scene_editor_property_label"
                            input default entry.get("condition", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "condition") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") in ("script", "stat", "condition"):
                            text "Payload / Script" style "scene_editor_property_label"
                            input default entry.get("payload", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "payload") copypaste True xfill True style "scene_editor_property_input"
                        text "On Show Script" style "scene_editor_property_label"
                        input default entry.get("on_show", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "on_show") copypaste True xfill True style "scene_editor_property_input"
                        text "On Advance Script" style "scene_editor_property_label"
                        input default entry.get("on_advance", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "on_advance") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") == "choice":
                            text "On Select Script" style "scene_editor_property_label"
                            input default entry.get("on_select", "") changed _viewers.scene_editor_dialogue_field_changed(entry_id, "on_select") copypaste True xfill True style "scene_editor_property_input"
                        if entry.get("type") == "choice":
                            text "Choice Options" style "scene_editor_property_label"
                            textbutton "+ Option" action Function(_viewers.scene_editor_add_choice_option, entry_id) style "scene_editor_layer_icon_button"
                            for choice_index in range(len(entry.get("choices", []))):
                                $ choice = entry.get("choices", [])[choice_index]
                                text "Option {} Caption".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("caption", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "caption") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Target".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("target", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "target") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Condition".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("condition", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "condition") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Script".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("script", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "script") copypaste True xfill True style "scene_editor_property_input"
                                text "Option {} Merge Target".format(choice_index + 1) size 11 color "#94A3B8"
                                input default choice.get("merge_target", "") changed _viewers.scene_editor_choice_field_changed(entry_id, choice_index, "merge_target") copypaste True xfill True style "scene_editor_property_input"
                                textbutton "Remove Option" action Function(_viewers.scene_editor_remove_choice_option, entry_id, choice_index) style "scene_editor_layer_icon_button"
        elif _viewers.scene_editor_right_panel_tab == "Project":
            viewport:
                mousewheel True
                scrollbars "vertical"
                yfill True
                has vbox
                spacing _viewers.scene_editor_right_panel_section_spacing
                text "Project" style "scene_editor_selection_label"
                text "Name" style "scene_editor_property_label"
                input default _viewers.scene_editor_project_name changed _viewers.scene_editor_set_project_name copypaste True xfill True style "scene_editor_property_input"
                text "Route ID" style "scene_editor_property_label"
                input default _viewers.scene_editor_current_route_id changed _viewers.scene_editor_set_route_id copypaste True xfill True style "scene_editor_property_input"
                text "Slot" style "scene_editor_property_label"
                input default _viewers.scene_editor_project_slot changed _viewers.scene_editor_set_project_slot copypaste True xfill True style "scene_editor_property_input"
                hbox:
                    spacing 6
                    textbutton "Save Project" action Function(_viewers.scene_editor_save_project) style "scene_editor_tool_button"
                    textbutton "Load Project" action Function(_viewers.scene_editor_load_project) style "scene_editor_tool_button"
                text "Settings" style "scene_editor_selection_label"
                textbutton ("Preview Dialogue: On" if _viewers.scene_editor_preview_dialogue else "Preview Dialogue: Off") action Function(_viewers.scene_editor_toggle_setting, "preview_dialogue") selected _viewers.scene_editor_preview_dialogue style "scene_editor_property_value_button"
                textbutton ("Export Visuals: On" if _viewers.scene_editor_export_visuals else "Export Visuals: Off") action Function(_viewers.scene_editor_toggle_setting, "export_visuals") selected _viewers.scene_editor_export_visuals style "scene_editor_property_value_button"
                textbutton ("Export UI: On" if _viewers.scene_editor_export_ui else "Export UI: Off") action Function(_viewers.scene_editor_toggle_setting, "export_ui") selected _viewers.scene_editor_export_ui style "scene_editor_property_value_button"
                textbutton ("Export Dialogue: On" if _viewers.scene_editor_export_dialogue else "Export Dialogue: Off") action Function(_viewers.scene_editor_toggle_setting, "export_dialogue") selected _viewers.scene_editor_export_dialogue style "scene_editor_property_value_button"
                textbutton ("Scene Clears: On" if _viewers.scene_editor_export_scene_clears else "Scene Clears: Off") action Function(_viewers.scene_editor_toggle_setting, "export_scene_clears") selected _viewers.scene_editor_export_scene_clears style "scene_editor_property_value_button"
                textbutton ("Hidden UI Export: On" if _viewers.scene_editor_export_hidden_ui else "Hidden UI Export: Off") action Function(_viewers.scene_editor_toggle_setting, "export_hidden_ui") selected _viewers.scene_editor_export_hidden_ui style "scene_editor_property_value_button"
                text "End Insert Step" style "scene_editor_property_label"
                input default str(_viewers.scene_editor_frame_insert_step) changed _viewers.scene_editor_set_frame_insert_step copypaste True xfill True style "scene_editor_property_input"
                text "Export" style "scene_editor_selection_label"
                textbutton "Copy Draft Script" action Function(_viewers.scene_editor_export_live_studio_script) style "scene_editor_tool_button"
                textbutton "Write Experimental Draft File" action Function(_viewers.scene_editor_write_live_studio_file) style "scene_editor_tool_button"
                if _viewers.scene_editor_export_cache:
                    text "Last export generated: {} chars".format(len(_viewers.scene_editor_export_cache)) size 12 color "#94A3B8"
                if _viewers.scene_editor_last_written_file:
                    text "Last file: {}".format(_viewers.scene_editor_last_written_file) size 12 color "#94A3B8"
                text "Frames: {}".format(len(_viewers.scene_editor_ensure_frame_records())) size 12 color "#94A3B8"
                text "Route: {}".format(_viewers.scene_editor_current_route_id) size 12 color "#94A3B8"
        else:
            viewport:
                mousewheel True
                scrollbars "vertical"
                yfill True
                has vbox
                spacing _viewers.scene_editor_right_panel_section_spacing
                text _("Undo stack: {count}").format(count=len(_viewers.scene_editor_history))
                text _("Redo stack: {count}").format(count=len(_viewers.scene_editor_redo_stack))
                null height 8
                $ history_preview = list(reversed(_viewers.scene_editor_history[-12:]))
                for idx, item in enumerate(history_preview):
                    text _("Snapshot {index}").format(index=idx + 1)

    hbox:
        xpos _viewers.scene_editor_sidebar_width
        ypos config.screen_height - _viewers.scene_editor_bottom_height
        xsize config.screen_width - _viewers.scene_editor_sidebar_width - _viewers.scene_editor_right_sidebar_width
        ysize _viewers.scene_editor_bottom_height
        spacing 0
        frame:
            style_group "scene_photo_properties"
            background _viewers.scene_editor_asset_panel_background
            xsize _viewers.scene_editor_asset_panel_width
            yfill True
            has vbox
            spacing _viewers.scene_editor_asset_panel_spacing
            hbox:
                spacing 6
                yalign .5
                xfill True
                text "Assets" yalign .5 style "scene_editor_assets_title"
                null width 12
                textbutton "Assets" action Function(_viewers.scene_editor_set_bottom_panel_tab, "Assets") selected (_viewers.scene_editor_bottom_panel_tab == "Assets") style "scene_editor_asset_mode_tab_button"
                textbutton "Dialogue" action Function(_viewers.scene_editor_set_bottom_panel_tab, "Dialogue") selected (_viewers.scene_editor_bottom_panel_tab == "Dialogue") style "scene_editor_asset_mode_tab_button"
                null width 12
                for _tab_name in ("Images", "Audio"):
                    textbutton _tab_name action Function(_viewers.scene_editor_set_asset_tab, _tab_name) selected (_viewers.scene_editor_asset_tab == _tab_name) style "scene_editor_asset_mode_tab_button"
                null xfill True
                for _sort_name in ("Recent", "Oldest", "Name A-Z", "Name Z-A"):
                    textbutton _sort_name action Function(_viewers.scene_editor_set_asset_sort_mode, _sort_name) selected (_viewers.scene_editor_asset_sort_mode == _sort_name) style "scene_editor_sort_button"
                null width 8
                button:
                    style "scene_editor_search_frame"
                    action Function(_viewers.scene_editor_activate_asset_search)
                    xsize _viewers.scene_editor_asset_search_width
                    has hbox
                    spacing 8
                    yalign 0.5
                    text "🔍" yalign .5 color "#AFC3FF" size 16
                    if _viewers.scene_editor_asset_search_active:
                        input value _viewers.scene_editor_search_input_value() copypaste True xfill True style "scene_editor_search_input"
                    else:
                        $ search_label = _viewers.scene_editor_image_filter or "Click to search assets"
                        text search_label style "scene_editor_search_placeholder"
            if _viewers.scene_editor_asset_mode == "Images":
                $ folder_entries, file_entries = _viewers.scene_editor_current_folder_entries()
                $ current_folder_label = _viewers.scene_editor_current_folder_label()
                vbox:
                    spacing _viewers.scene_editor_asset_panel_spacing
                    hbox:
                        spacing _viewers.scene_editor_asset_path_spacing
                        text "Path: {}".format(current_folder_label) yalign .5
                        if _viewers.scene_editor_can_go_up_asset_folder():
                            textbutton "⬆ Up" action Function(_viewers.scene_editor_go_up_asset_folder)
                        textbutton "⌂ Root" action Function(_viewers.scene_editor_reset_asset_folder)
                        textbutton "Refresh" action Function(_viewers.scene_editor_refresh_asset_browser)
                    viewport:
                        style_prefix "scene_editor_asset_scroll"
                        mousewheel True
                        scrollbars "vertical"
                        yfill True
                        $ entries = folder_entries + [{"name": name, "path": None, "file": True} for name in file_entries]
                        vpgrid:
                            cols _viewers.scene_editor_asset_grid_cols
                            spacing _viewers.scene_editor_asset_grid_spacing
                            xfill True
                            xalign 0.5
                            for entry in entries:
                                $ is_folder = entry.get("path") is not None
                                $ button_action = Function(_viewers.scene_editor_open_asset_folder, entry["path"]) if is_folder else Function(_viewers.scene_editor_apply_image_name, entry["name"], _viewers.scene_editor_selected_layer, None)
                                $ alternate_action = NullAction()
                                $ hover_action = NullAction()
                                $ unhover_action = NullAction()
                                if not is_folder:
                                    $ alternate_action = [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_apply_image_name, entry["name"], _viewers.scene_editor_selected_layer, _viewers.scene_editor_selected_tag)]
                                    $ hover_action = Function(_viewers.scene_editor_preview_image, entry["name"])
                                    $ unhover_action = Function(_viewers.scene_editor_hide_preview)
                                $ entry_label = entry["name"].split()[-1] if (not is_folder and entry.get("name")) else entry.get("name", "")
                                button:
                                    style "scene_editor_asset_tile_button"
                                    action button_action
                                    alternate alternate_action
                                    hovered hover_action
                                    unhovered unhover_action
                                    xsize _viewers.scene_editor_asset_tile_width
                                    ysize _viewers.scene_editor_asset_tile_height
                                    xalign 0.5
                                    has vbox
                                    spacing _viewers.scene_editor_asset_tile_inner_spacing
                                    frame:
                                        style "scene_editor_asset_tile_border_frame"
                                        xsize _viewers.scene_editor_asset_thumb_box_size + 2
                                        ysize _viewers.scene_editor_asset_thumb_box_size + 2
                                        xalign 0.5
                                        yalign 0.5
                                        frame:
                                            style "scene_editor_asset_tile_thumb_frame"
                                            xsize _viewers.scene_editor_asset_thumb_box_size
                                            ysize _viewers.scene_editor_asset_thumb_box_size
                                            xalign 0.5
                                            yalign 0.5
                                            if is_folder:
                                                text "📁" size 32 xalign .5 yalign .5
                                            else:
                                                add Transform(_viewers.scene_editor_asset_thumbnail(entry["name"]), xalign=0.5, yalign=0.5)
                                    frame:
                                        style "scene_editor_asset_label_frame"
                                        xalign 0.5
                                        text entry_label size 11 xalign .5 yalign .5
                    if not folder_entries and not file_entries:
                        text "No assets in this folder." italic True
            else:
                $ audio_entries = _viewers.scene_editor_list_audio_assets()
                viewport:
                    style_prefix "scene_editor_asset_scroll"
                    mousewheel True
                    scrollbars "vertical"
                    yfill True
                    vpgrid:
                        cols _viewers.scene_editor_audio_grid_cols
                        spacing _viewers.scene_editor_audio_grid_spacing
                        xfill True
                        xalign 0.5
                        for audio_name in audio_entries:
                            button:
                                style "scene_editor_asset_tile_button"
                                action NullAction()
                                xsize _viewers.scene_editor_audio_tile_width
                                ysize _viewers.scene_editor_audio_tile_height
                                xalign 0.5
                                has vbox
                                spacing _viewers.scene_editor_asset_tile_inner_spacing
                                frame:
                                    style "scene_editor_asset_tile_border_frame"
                                    xsize _viewers.scene_editor_asset_thumb_box_size + 2
                                    ysize _viewers.scene_editor_asset_thumb_box_size + 2
                                    xalign 0.5
                                    frame:
                                        style "scene_editor_asset_tile_thumb_frame"
                                        xsize _viewers.scene_editor_asset_thumb_box_size
                                        ysize _viewers.scene_editor_asset_thumb_box_size
                                        xalign 0.5
                                        text "♪" size 24 xalign .5 yalign .5
                                frame:
                                    style "scene_editor_asset_label_frame"
                                    xalign 0.5
                                    text audio_name size 12 xalign .5 yalign .5
        frame:
            style_group "scene_photo_properties"
            background _viewers.scene_editor_tools_panel_background
            xsize _viewers.scene_editor_tools_panel_width
            yfill True
            has vbox
            spacing _viewers.scene_editor_tools_section_spacing
            text "Tools" style "scene_editor_tools_title"
            vbox:
                spacing _viewers.scene_editor_tools_section_spacing
                vbox:
                    spacing 4
                    text "Edit" style "scene_editor_tool_category_label"
                    hbox:
                        spacing _viewers.scene_editor_tool_button_spacing
                        style_prefix "scene_editor_tool"
                        for tool_label, tool_mode in (("⌖  Select", "select"), ("✣  Move", "move"), ("⛶  Scale", "resize"), ("⟳  Rotate", "rotate")):
                            $ selected_tool_mode = "scale" if tool_mode == "resize" else tool_mode
                            textbutton tool_label action Function(_viewers.scene_editor_set_tool_mode, tool_mode) selected _viewers.scene_editor_tool_mode == selected_tool_mode
                vbox:
                    spacing 4
                    text "Edit Objects" style "scene_editor_tool_category_label"
                    hbox:
                        spacing _viewers.scene_editor_tool_button_spacing
                        style_prefix "scene_editor_tool"
                        textbutton "⧉  Copy" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_copy_selected)]
                        textbutton "▣  Paste" action Function(_viewers.scene_editor_paste_copied)
                        textbutton "⧉  Duplicate" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_duplicate_selected)]
                        textbutton "⌫  Delete" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_remove_selected)]
                vbox:
                    spacing 4
                    text "Arrange" style "scene_editor_tool_category_label"
                    hbox:
                        spacing _viewers.scene_editor_tool_button_spacing
                        style_prefix "scene_editor_tool"
                        textbutton "▣  Bring Front" action Function(_viewers.scene_editor_reorder_selected, "front") sensitive (_viewers.scene_editor_selected_tag is not None)
                        textbutton "▤  Send Back" action Function(_viewers.scene_editor_reorder_selected, "back") sensitive (_viewers.scene_editor_selected_tag is not None)
                        textbutton "▥  Bring Forward" action Function(_viewers.scene_editor_reorder_selected, "forward") sensitive (_viewers.scene_editor_selected_tag is not None)
                        textbutton "▦  Send Backward" action Function(_viewers.scene_editor_reorder_selected, "backward") sensitive (_viewers.scene_editor_selected_tag is not None)
                vbox:
                    spacing 4
                    text "Other" style "scene_editor_tool_category_label"
                    hbox:
                        spacing _viewers.scene_editor_tool_button_spacing
                        style_prefix "scene_editor_tool"
                        textbutton "☷  Group" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_group_selected)]
                        textbutton "☰  Ungroup" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_ungroup_selected)]
                        textbutton "Lock" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_lock_selected)]
                        textbutton "Unlock" action [SensitiveIf(_viewers.scene_editor_selected_tag is not None), Function(_viewers.scene_editor_unlock_selected)]
            vbox:
                spacing _viewers.scene_editor_bottom_section_spacing
                vbox:
                    spacing _viewers.scene_editor_secondary_controls_row_spacing
                    hbox:
                        spacing _viewers.scene_editor_secondary_controls_spacing
                        textbutton "Undo" action [SensitiveIf(len(_viewers.scene_editor_history) > 0), Function(_viewers.scene_editor_undo)] style "scene_editor_tool_button"
                        textbutton "Redo" action [SensitiveIf(len(_viewers.scene_editor_redo_stack) > 0), Function(_viewers.scene_editor_redo)] style "scene_editor_tool_button"

    if _viewers.scene_editor_bottom_panel_tab == "Dialogue":
        frame:
            style_group "scene_photo_properties"
            background _viewers.scene_editor_asset_panel_background
            xpos _viewers.scene_editor_sidebar_width
            ypos config.screen_height - _viewers.scene_editor_bottom_height
            xsize _viewers.scene_editor_asset_panel_width
            ysize _viewers.scene_editor_bottom_height
            has vbox
            spacing _viewers.scene_editor_asset_panel_spacing
            hbox:
                spacing 6
                yalign .5
                xfill True
                text "Dialogue" yalign .5 style "scene_editor_assets_title"
                null width 12
                textbutton "Assets" action Function(_viewers.scene_editor_set_bottom_panel_tab, "Assets") selected False style "scene_editor_asset_mode_tab_button"
                textbutton "Dialogue" action Function(_viewers.scene_editor_set_bottom_panel_tab, "Dialogue") selected True style "scene_editor_asset_mode_tab_button"
            use scene_editor_bottom_dialogue_panel

    if _viewers.scene_editor_preview_mode:
        add _viewers.SceneEditorFullscreenPreview()
        frame:
            modal True
            xpos 0
            ypos _viewers.scene_editor_top_height
            xsize config.screen_width
            ysize config.screen_height - _viewers.scene_editor_top_height
            background None
        frame:
            style_group "scene_photo_toolbar"
            xpos 0
            ypos 0
            xsize config.screen_width
            ysize _viewers.scene_editor_top_height
            has hbox
            spacing 8
            text "Preview" yalign .5 style "scene_editor_logo_text"
            null xfill True
            textbutton "Leave Preview" action Function(_viewers.scene_editor_set_preview_mode, False) style "scene_editor_toolbar_action_button"

    if confirm_exit:
        frame:
            modal True
            xpos 0
            ypos 0
            xsize config.screen_width
            ysize config.screen_height
            background "#00000099"

        frame:
            style_group "scene_photo_properties"
            xalign 0.5
            yalign 0.5
            xsize 520
            has vbox
            spacing 16
            text "Exit Scene Editor?" xalign 0.5 size 28 color "#FFFFFF"
            text "Any unsaved editor changes may be lost. Are you sure you want to close the Scene Editor?" xalign 0.5 text_align 0.5 color "#DDE6FF"
            hbox:
                xalign 0.5
                spacing 16
                textbutton "Cancel" action SetScreenVariable("confirm_exit", False) xsize 160
                textbutton "Exit" action Return() xsize 160
init -897 python in _viewers:
    from renpy.store import Fixed, Solid, Text, Transform

    class SceneEditorOverlay(renpy.Displayable):
        def __init__(self, **properties):
            super(SceneEditorOverlay, self).__init__(**properties)
            from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
            self.MOUSEBUTTONDOWN = MOUSEBUTTONDOWN
            self.MOUSEBUTTONUP = MOUSEBUTTONUP
            self.MOUSEMOTION = MOUSEMOTION
            self.mode = None
            self.layer = None
            self.tag = None
            self.start_mouse = (0, 0)
            self.start_pos = (0, 0)
            self.start_scale = (1.0, 1.0)
            self.start_rotate = 0.0
            self.start_stage_mouse = (0, 0)
            self.start_rect = None
            self.resize_handle = None
            self.start_rotate_angle = 0.0
            self.last_applied_value = None
            self.last_redraw_st = 0.0

        def __eq__(self, other):
            return isinstance(other, SceneEditorOverlay)

        def selected_rect(self, st=0, at=0):
            if scene_editor_selected_tag is None:
                return None
            if not scene_editor_has_selected():
                return None
            return scene_editor_item_rect(scene_editor_selected_layer, scene_editor_selected_tag, st, at)

        def render(self, width, height, st, at):
            box = Fixed()
            canvas_x, canvas_y, canvas_w, canvas_h = scene_editor_canvas_bounds()
            offset_x, offset_y, scale = scene_editor_canvas_offsets()
            box.add(Transform(Solid("#111827", xsize=max(1, int(canvas_w)), ysize=max(1, int(canvas_h))), xpos=canvas_x, ypos=canvas_y))
            if scene_editor_snap_enabled:
                grid = max(1, int(scene_editor_snap_increment * scale))
                gx = canvas_x
                while gx <= canvas_x + canvas_w:
                    box.add(Transform(Solid("#46FF8855", xsize=1, ysize=max(1, int(canvas_h))), xpos=gx, ypos=canvas_y))
                    gx += grid
                gy = canvas_y
                while gy <= canvas_y + canvas_h:
                    box.add(Transform(Solid("#46FF8855", xsize=max(1, int(canvas_w)), ysize=1), xpos=canvas_x, ypos=gy))
                    gy += grid
            preview = self.preview_scene(st, at)
            box.add(Transform(preview, xpos=offset_x, ypos=offset_y, zoom=scale))
            rect = self.selected_rect(st, at)
            if rect is not None:
                x, y, w, h = [float(v) if hasattr(v, "absolute") or hasattr(v, "relative") else v for v in rect]
                x = float(x)
                y = float(y)
                w = float(w)
                h = float(h)
                color = scene_editor_selection_color
                thickness = scene_editor_selection_outline_thickness
                highlight_time = max(0.0, scene_editor_highlight_until - scene_editor_display_time())
                if highlight_time > 0:
                    pulse = 0.5 + 0.5 * sin(scene_editor_display_time() * 10.0)
                    glow_alpha = int(80 + pulse * 80)
                    glow_color = "#8BC6FF{:02X}".format(glow_alpha)
                    thickness = 4
                    box.add(Transform(Solid(glow_color, xsize=max(1, int(w) + thickness * 2), ysize=thickness), xpos=x - thickness, ypos=y - thickness))
                    box.add(Transform(Solid(glow_color, xsize=max(1, int(w) + thickness * 2), ysize=thickness), xpos=x - thickness, ypos=y + h))
                    box.add(Transform(Solid(glow_color, xsize=thickness, ysize=max(1, int(h) + thickness * 2)), xpos=x - thickness, ypos=y - thickness))
                    box.add(Transform(Solid(glow_color, xsize=thickness, ysize=max(1, int(h) + thickness * 2)), xpos=x + w, ypos=y - thickness))
                box.add(Transform(Solid(color, xsize=max(1, int(w)), ysize=thickness), xpos=x, ypos=y))
                box.add(Transform(Solid(color, xsize=max(1, int(w)), ysize=thickness), xpos=x, ypos=y + h - thickness))
                box.add(Transform(Solid(color, xsize=thickness, ysize=max(1, int(h))), xpos=x, ypos=y))
                box.add(Transform(Solid(color, xsize=thickness, ysize=max(1, int(h))), xpos=x + w - thickness, ypos=y))
                handle_size = scene_editor_selection_handle_size
                handle_inner = max(2, handle_size - 4)
                handle_fill = scene_editor_selection_handle_fill if scene_editor_tool_mode in ("select", "scale") else scene_editor_selection_handle_idle_fill
                for _name, hx, hy, _dx, _dy in self.resize_handles((x, y, w, h)):
                    box.add(Transform(Solid(color, xsize=handle_size, ysize=handle_size), xpos=hx - handle_size / 2, ypos=hy - handle_size / 2))
                    box.add(Transform(Solid(handle_fill, xsize=handle_inner, ysize=handle_inner), xpos=hx - handle_inner / 2, ypos=hy - handle_inner / 2))
                rx, ry, rw, rh = self.rotate_handle_rect((x, y, w, h))
                box.add(Transform(Solid(color, xsize=2, ysize=max(1, int(y - (ry + rh)))), xpos=x + w / 2, ypos=ry + rh))
                box.add(Transform(Solid(color, xsize=int(rw), ysize=int(rh)), xpos=rx, ypos=ry))
                box.add(Transform(Solid("#0B1020FF", xsize=max(1, int(rw - 6)), ysize=max(1, int(rh - 6))), xpos=rx + 3, ypos=ry + 3))
                box.add(Transform(Solid(scene_editor_selection_rotate_handle_fill, xsize=max(1, int(rw - 12)), ysize=max(1, int(rh - 12))), xpos=rx + 6, ypos=ry + 6))
            return renpy.render(box, width, height, st, at)

        def resize_handles(self, rect):
            x, y, w, h = rect
            cx = x + w / 2.0
            cy = y + h / 2.0
            return (
                ("nw", x, y, -1, -1),
                ("n", cx, y, 0, -1),
                ("ne", x + w, y, 1, -1),
                ("e", x + w, cy, 1, 0),
                ("se", x + w, y + h, 1, 1),
                ("s", cx, y + h, 0, 1),
                ("sw", x, y + h, -1, 1),
                ("w", x, cy, -1, 0),
            )

        def rotate_handle_rect(self, rect):
            x, y, w, _h = rect
            size = scene_editor_selection_rotate_handle_size
            return (x + w / 2.0 - size / 2.0, y - scene_editor_selection_rotate_handle_offset, size, size)

        def resize_handle_at(self, x, y, rect):
            half_hit = scene_editor_selection_handle_hit_size / 2.0
            for name, hx, hy, _dx, _dy in self.resize_handles(rect):
                if x >= hx - half_hit and x <= hx + half_hit and y >= hy - half_hit and y <= hy + half_hit:
                    return name
            return None

        def in_rect(self, x, y, rect):
            rx, ry, rw, rh = rect
            return x >= rx and x <= rx + rw and y >= ry and y <= ry + rh

        def preview_scene(self, st, at):
            scene, _count = scene_editor_preview_displayable(st, at)
            return scene

        def in_editor_canvas(self, x, y):
            return scene_editor_point_in_canvas(x, y)

        def event(self, ev, x, y, st):
            global scene_editor_active_drag_mode
            if ev.type == self.MOUSEBUTTONDOWN and getattr(ev, "button", None) == 1:
                if not self.in_editor_canvas(x, y):
                    return
                scene_editor_set_asset_search_active(False)
                rect = self.selected_rect(st, st)
                if rect is not None:
                    if scene_editor_tool_mode in ("select", "scale"):
                        handle = self.resize_handle_at(x, y, rect)
                        if handle is not None:
                            self.begin_drag("resize", x, y, handle)
                            scene_editor_raise_ignore_event()
                    if scene_editor_tool_mode in ("select", "rotate") and self.in_rect(x, y, self.rotate_handle_rect(rect)):
                        self.begin_drag("rotate", x, y)
                        scene_editor_raise_ignore_event()
                    if scene_editor_tool_mode in ("select", "move") and self.in_rect(x, y, rect):
                        self.begin_drag("move", x, y)
                        scene_editor_raise_ignore_event()
                layer, tag = scene_editor_hit_test(x, y, st, st)
                if tag is not None:
                    scene_editor_select(layer, tag)
                    if scene_editor_tool_mode == "scale":
                        self.begin_drag("resize", x, y, "se")
                        scene_editor_raise_ignore_event()
                    if scene_editor_tool_mode == "rotate":
                        self.begin_drag("rotate", x, y)
                        scene_editor_raise_ignore_event()
                    if scene_editor_tool_mode in ("select", "move"):
                        self.begin_drag("move", x, y)
                        scene_editor_raise_ignore_event()
                    scene_editor_raise_ignore_event()
            elif ev.type == self.MOUSEMOTION and self.mode is not None:
                self.update_drag(x, y, st)
                scene_editor_raise_ignore_event()
            elif ev.type == self.MOUSEBUTTONUP and getattr(ev, "button", None) == 1 and self.mode is not None:
                self.mode = None
                scene_editor_active_drag_mode = None
                self.layer = None
                self.tag = None
                self.resize_handle = None
                scene_editor_clear_axis_constraint()
                change_time(current_time)
                scene_editor_raise_ignore_event()
            if self.mode is None:
                renpy.redraw(self, 0)

        def begin_drag(self, mode, x, y, handle=None):
            global scene_editor_active_drag_mode
            self.mode = mode
            scene_editor_active_drag_mode = mode
            self.layer = scene_editor_selected_layer
            self.tag = scene_editor_selected_tag
            self.resize_handle = handle
            self.last_applied_value = None
            self.last_redraw_st = 0.0
            self.start_mouse = (x, y)
            if scene_editor_is_ui_layer(self.layer):
                self.start_stage_mouse = scene_editor_screen_to_ui_stage(x, y)
            else:
                self.start_stage_mouse = scene_editor_screen_to_stage(x, y)
            self.drag_scale = max(0.001, scene_editor_canvas_scale_value())
            self.start_pos = (
                scene_editor_to_pixel(scene_editor_get_property_value((self.tag, self.layer, "xpos"), default=True), config.screen_width),
                scene_editor_to_pixel(scene_editor_get_property_value((self.tag, self.layer, "ypos"), default=True), config.screen_height),
            )
            self.start_rect = scene_editor_stage_item_rect(self.layer, self.tag)
            self.start_scale = (
                scene_editor_get_property_value((self.tag, self.layer, "xzoom"), default=True),
                scene_editor_get_property_value((self.tag, self.layer, "yzoom"), default=True),
            )
            if self.start_scale[0] is None or self.start_scale[1] is None:
                self.start_scale = (
                    1.0 if self.start_scale[0] is None else self.start_scale[0],
                    1.0 if self.start_scale[1] is None else self.start_scale[1],
                )
            self.start_rotate = scene_editor_get_property_value((self.tag, self.layer, "rotate"), default=True)
            if self.start_rotate is None:
                self.start_rotate = 0.0
            if self.start_rect is not None:
                rx, ry, rw, rh = self.start_rect
                cx = rx + rw / 2.0
                cy = ry + rh / 2.0
                sx_stage, sy_stage = self.start_stage_mouse
                self.start_rotate_angle = degrees(atan2(sy_stage - cy, sx_stage - cx))
            else:
                self.start_rotate_angle = 0.0
            scene_editor_push_history()

        def update_drag(self, x, y, st=0):
            if self.tag is None or self.layer is None:
                return
            sx, sy = self.start_mouse
            scale = getattr(self, "drag_scale", scene_editor_canvas_scale_value())
            if scale <= 0:
                scale = 1.0
            if self.mode == "move":
                px, py = self.start_pos
                if scene_editor_is_ui_layer(self.layer):
                    stage_x, stage_y = scene_editor_screen_to_ui_stage(x, y)
                else:
                    stage_x, stage_y = scene_editor_screen_to_stage(x, y)
                start_stage_x, start_stage_y = self.start_stage_mouse
                stage_dx = stage_x - start_stage_x
                stage_dy = stage_y - start_stage_y
                if scene_editor_axis_constraint == "x":
                    stage_dy = 0
                elif scene_editor_axis_constraint == "y":
                    stage_dx = 0
                target = (int(round(scene_editor_snap_value(px + stage_dx))), int(round(scene_editor_snap_value(py + stage_dy))))
                if target != self.last_applied_value:
                    self.last_applied_value = target
                    scene_editor_set_position(self.layer, self.tag, target[0], target[1], refresh=False)
            elif self.mode == "resize":
                rect = self.start_rect or scene_editor_stage_item_rect(self.layer, self.tag)
                _rx, _ry, rw, rh = rect
                handle_dirs = {
                    "nw": (-1, -1),
                    "n": (0, -1),
                    "ne": (1, -1),
                    "e": (1, 0),
                    "se": (1, 1),
                    "s": (0, 1),
                    "sw": (-1, 1),
                    "w": (-1, 0),
                }
                dir_x, dir_y = handle_dirs.get(self.resize_handle or "se", (1, 1))
                stage_dx = (x - sx) / scale
                stage_dy = (y - sy) / scale
                if scene_editor_axis_constraint == "x":
                    dir_y = 0
                    stage_dy = 0
                elif scene_editor_axis_constraint == "y":
                    dir_x = 0
                    stage_dx = 0
                target_w = rw if dir_x == 0 else max(24.0, rw + (stage_dx * dir_x))
                target_h = rh if dir_y == 0 else max(24.0, rh + (stage_dy * dir_y))
                if scene_editor_snap_enabled:
                    if dir_x != 0:
                        target_w = max(24.0, scene_editor_snap_value(target_w))
                    if dir_y != 0:
                        target_h = max(24.0, scene_editor_snap_value(target_h))
                x_factor = 1.0 if dir_x == 0 else target_w / max(24.0, rw)
                y_factor = 1.0 if dir_y == 0 else target_h / max(24.0, rh)
                target = (round(self.start_scale[0] * x_factor, 3), round(self.start_scale[1] * y_factor, 3))
                if target != self.last_applied_value:
                    self.last_applied_value = target
                    scene_editor_set_scale(self.layer, self.tag, target[0], target[1], refresh=False)
            elif self.mode == "rotate":
                rect = scene_editor_stage_item_rect(self.layer, self.tag)
                rx, ry, rw, rh = rect
                cx = rx + rw / 2.0
                cy = ry + rh / 2.0
                if scene_editor_is_ui_layer(self.layer):
                    sx_stage, sy_stage = scene_editor_screen_to_ui_stage(x, y)
                else:
                    sx_stage, sy_stage = scene_editor_screen_to_stage(x, y)
                angle = degrees(atan2(sy_stage - cy, sx_stage - cx))
                target = round(self.start_rotate + angle - self.start_rotate_angle, 2)
                if target != self.last_applied_value:
                    self.last_applied_value = target
                    scene_editor_set_rotate(self.layer, self.tag, target, refresh=False)
            if st - self.last_redraw_st >= scene_editor_drag_redraw_interval:
                self.last_redraw_st = st
                renpy.redraw(self, 0)
            else:
                renpy.redraw(self, scene_editor_drag_redraw_interval)

        def per_interact(self):
            if self.mode is not None or scene_editor_highlight_until > scene_editor_display_time():
                renpy.redraw(self, scene_editor_drag_redraw_interval if self.mode is not None else 0)

    class SceneEditorFullscreenPreview(renpy.Displayable):
        def __init__(self, **properties):
            super(SceneEditorFullscreenPreview, self).__init__(**properties)

        def __eq__(self, other):
            return isinstance(other, SceneEditorFullscreenPreview)

        def render(self, width, height, st, at):
            scene, _count = scene_editor_game_preview_displayable(st, at)
            preview = Fixed(xsize=config.screen_width, ysize=config.screen_height)
            preview.add(Transform(Solid("#000000", xsize=config.screen_width, ysize=config.screen_height)))
            preview.add(scene)
            renpy.redraw(self, 0)
            return renpy.render(preview, width, height, st, at)


init -896:
    style scene_photo_editor_frame background "#0B1020" padding (0, 0)
    style scene_photo_editor_text color "#DDE6FF" size 14
    style scene_photo_editor_label_text color "#FFFFFF" size 15
    style scene_photo_editor_button background "#1E2B47" hover_background "#2A3860" selected_background "#5B3EF7" padding (10, 6)
    style scene_photo_editor_button_text color "#C8D8FF" selected_color "#FFFFFF" size 14
    style scene_photo_toolbar_frame background "#0C1121" padding (12, 0)
    style scene_photo_toolbar_frame yfill True
    style scene_photo_toolbar_text color "#F1F4FF" size 16
    style scene_photo_toolbar_button is scene_photo_editor_button
    style scene_photo_toolbar_button_text is scene_photo_editor_button_text
    style scene_photo_properties_frame background "#0D1528" padding (12, 10)
    style scene_photo_properties_text color "#C8D8FF" size 14
    style scene_photo_properties_button is scene_photo_editor_button
    style scene_photo_properties_button_text is scene_photo_editor_button_text
    style scene_photo_properties_input background "#0A0F1C" color "#FFFFFF" size 14
    style scene_photo_properties_group_button is scene_photo_properties_button
    style scene_photo_properties_group_button_text is scene_photo_properties_button_text

    style scene_editor_logo_text is scene_photo_toolbar_text
    style scene_editor_logo_text color "#FFFFFF" size 18
    style scene_editor_logo_text yalign 0.5

    style scene_editor_toolbar_zoom_label is scene_photo_toolbar_text
    style scene_editor_toolbar_zoom_label color "#8E9DC4" size 14
    style scene_editor_toolbar_zoom_label yalign 0.5

    style scene_editor_zoom_display_frame is frame
    style scene_editor_zoom_display_frame background "#1A2440"
    style scene_editor_zoom_display_frame hover_background "#243055"
    style scene_editor_zoom_display_frame padding (10, 5)
    style scene_editor_zoom_display_frame yalign 0.5

    style scene_editor_zoom_value_text is scene_photo_toolbar_text
    style scene_editor_zoom_value_text color "#FFFFFF" size 14

    style scene_editor_zoom_chevron is scene_photo_toolbar_text
    style scene_editor_zoom_chevron color "#7080A8" size 12

    style scene_editor_zoom_step_button is button
    style scene_editor_zoom_step_button background "#1A2440"
    style scene_editor_zoom_step_button hover_background "#283560"
    style scene_editor_zoom_step_button padding (10, 5)
    style scene_editor_zoom_step_button yalign 0.5
    style scene_editor_zoom_step_button_text color "#FFFFFF" size 16

    style scene_editor_snap_toggle_button is button
    style scene_editor_snap_toggle_button background "#1A2440"
    style scene_editor_snap_toggle_button hover_background "#283560"
    style scene_editor_snap_toggle_button selected_background "#3B2DB0"
    style scene_editor_snap_toggle_button padding (10, 5)
    style scene_editor_snap_toggle_button yalign 0.5
    style scene_editor_snap_toggle_button_text color "#8897C4" size 14
    style scene_editor_snap_toggle_button_text selected_color "#FFFFFF"

    style scene_editor_toolbar_action_button is button
    style scene_editor_toolbar_action_button background "#1A2440"
    style scene_editor_toolbar_action_button hover_background "#283560"
    style scene_editor_toolbar_action_button selected_background "#5B3EF7"
    style scene_editor_toolbar_action_button padding (14, 7)
    style scene_editor_toolbar_action_button yalign 0.5
    style scene_editor_toolbar_action_button_text color "#C8D8FF" size 14

    style scene_editor_section_button is scene_photo_editor_button padding (8, 4)
    style scene_editor_section_button_text is scene_photo_editor_button_text size 14
    style scene_editor_card_button is scene_photo_editor_button padding (8, 8)
    style scene_editor_card_button_text is scene_photo_editor_button_text size 13

    style scene_editor_tab_button is scene_photo_editor_button
    style scene_editor_tab_button background None
    style scene_editor_tab_button hover_background "#FFFFFF14"
    style scene_editor_tab_button selected_background "#A8C5FF24"
    style scene_editor_tab_button padding (6, 4)
    style scene_editor_tab_button_text is scene_photo_editor_button_text
    style scene_editor_tab_button_text color "#FFFFFF"
    style scene_editor_tab_button_text selected_color "#8BC6FF"
    style scene_editor_tab_button_text underline False
    style scene_editor_tab_button_text selected_underline True

    style scene_editor_tool_button is scene_photo_editor_button
    style scene_editor_tool_button background "#1d273d"
    style scene_editor_tool_button hover_background "#273453"
    style scene_editor_tool_button selected_background "#4D35B8"
    style scene_editor_tool_button left_padding 13
    style scene_editor_tool_button right_padding 13
    style scene_editor_tool_button top_padding 5
    style scene_editor_tool_button bottom_padding 5
    style scene_editor_tool_button_text is scene_photo_editor_button_text
    style scene_editor_tool_button_text color "#D7E0FF" size 12
    style scene_editor_tool_button_text selected_color "#FFFFFF"
    style scene_editor_tool_button_text underline False
    style scene_editor_tool_button_text selected_underline False

    style scene_editor_tool_category_label is scene_photo_properties_text
    style scene_editor_tool_category_label size 11
    style scene_editor_tool_category_label color "#93A0C4"

    style scene_editor_tools_title is scene_photo_editor_label_text
    style scene_editor_tools_title color "#8C5CFF"
    style scene_editor_tools_title size 16
    style scene_editor_tools_title xalign 0.0

    style scene_editor_panel_header is frame
    style scene_editor_panel_header background "#111827"
    style scene_editor_panel_header padding (12, 8)

    style scene_editor_panel_header_text is scene_photo_editor_label_text
    style scene_editor_panel_header_text size 14
    style scene_editor_panel_header_text color "#7C9EFF"

    style scene_editor_panel_header_chevron is scene_photo_editor_text
    style scene_editor_panel_header_chevron size 12
    style scene_editor_panel_header_chevron color "#5B6D9A"
    style scene_editor_panel_header_chevron yalign 0.5

    style scene_editor_selection_label is scene_photo_properties_text
    style scene_editor_selection_label color "#8BA0D0"
    style scene_editor_selection_label size 12

    style scene_editor_property_group_button is button
    style scene_editor_property_group_button background None
    style scene_editor_property_group_button hover_background "#FFFFFF0D"
    style scene_editor_property_group_button padding (8, 5)
    style scene_editor_property_group_button xfill True

    style scene_editor_property_group_label is scene_photo_properties_text
    style scene_editor_property_group_label size 12
    style scene_editor_property_group_label color "#D9E3FF"

    style scene_editor_property_group_chevron is scene_photo_properties_text
    style scene_editor_property_group_chevron size 13
    style scene_editor_property_group_chevron color "#94A3B8"

    style scene_editor_property_group_frame is frame
    style scene_editor_property_group_frame background None
    style scene_editor_property_group_frame padding (8, 4)

    style scene_editor_property_row_frame is frame
    style scene_editor_property_row_frame background None
    style scene_editor_property_row_frame padding (0, 3)

    style scene_editor_property_label is scene_photo_properties_text
    style scene_editor_property_label size 12
    style scene_editor_property_label color "#AAB8D6"

    style scene_editor_property_pair_label is scene_photo_properties_text
    style scene_editor_property_pair_label size 12
    style scene_editor_property_pair_label color "#9AACCF"

    style scene_editor_axis_label is scene_photo_properties_text
    style scene_editor_axis_label size 11
    style scene_editor_axis_label color "#7888A8"

    style scene_editor_property_value_button is scene_photo_properties_button
    style scene_editor_property_value_button padding (8, 3)

    style scene_editor_property_input is scene_photo_properties_input
    style scene_editor_property_input xalign 0.0
    style scene_editor_property_input text_align 0.0
    style scene_editor_property_input background None
    style scene_editor_property_input padding (0, 0)
    style scene_editor_property_input left_padding 6
    style scene_editor_property_input right_padding 6
    style scene_editor_property_input top_padding 2
    style scene_editor_property_input bottom_padding 2
    style scene_editor_property_input size 12
    style scene_editor_property_input color "#F2F6FF"

    style scene_editor_value_frame is frame
    style scene_editor_value_frame background "#0A101F"
    style scene_editor_value_frame padding (0, 0)
    style scene_editor_value_frame left_padding 4
    style scene_editor_value_frame right_padding 4
    style scene_editor_value_frame top_padding 2
    style scene_editor_value_frame bottom_padding 2
    style scene_editor_value_frame xalign 0.0
    style scene_editor_value_frame yalign 0.5
    style scene_editor_value_frame yoffset -3
    style scene_editor_value_frame outlines [(1, "#3A5280", 0, 0)]

    style scene_editor_child_name_button is scene_editor_property_value_button
    style scene_editor_child_name_button background None
    style scene_editor_child_name_button hover_background "#FFFFFF12"
    style scene_editor_child_name_button padding (6, 2)
    style scene_editor_child_name_button_text color "#8AAED4"
    style scene_editor_child_name_button_text size 12

    style scene_editor_editable_value_button is button
    style scene_editor_editable_value_button background None
    style scene_editor_editable_value_button hover_background "#FFFFFF12"
    style scene_editor_editable_value_button padding (6, 2)

    style scene_editor_property_value_text is scene_photo_properties_text
    style scene_editor_property_value_text size 12
    style scene_editor_property_value_text color "#DDE6FF"
    style scene_editor_property_value_text text_align 0.5
    style scene_editor_property_value_text xalign 0.5

    style scene_editor_reset_button is scene_photo_properties_button
    style scene_editor_reset_button background None
    style scene_editor_reset_button hover_background None
    style scene_editor_reset_button padding (4, 0)
    style scene_editor_reset_button_text color "#5B7AB8"
    style scene_editor_reset_button_text size 10

    style scene_editor_panel_tab_bar is frame
    style scene_editor_panel_tab_bar background "#0D1424"
    style scene_editor_panel_tab_bar padding (12, 8)

    style scene_editor_blend_mode_bar is frame
    style scene_editor_blend_mode_bar background "#0C1322"
    style scene_editor_blend_mode_bar padding (12, 6)

    style scene_editor_blend_mode_dropdown is frame
    style scene_editor_blend_mode_dropdown background "#151E31"
    style scene_editor_blend_mode_dropdown hover_background "#243055"
    style scene_editor_blend_mode_dropdown padding (10, 6)
    style scene_editor_blend_mode_dropdown xfill True

    style scene_editor_blend_mode_text is scene_photo_properties_text
    style scene_editor_blend_mode_text color "#D6E1FF" size 12

    style scene_editor_layer_header_button is button
    style scene_editor_layer_header_button idle_background "#0D1426"
    style scene_editor_layer_header_button hover_background "#14203C"
    style scene_editor_layer_header_button selected_background "#5B3EF733"
    style scene_editor_layer_header_button padding (10, 6)

    style scene_editor_layer_name_text is scene_photo_properties_text
    style scene_editor_layer_name_text color "#C8D8FF" size 13

    style scene_editor_search_placeholder is scene_photo_properties_text
    style scene_editor_search_placeholder color "#4E5E84"
    style scene_editor_search_placeholder size 13

    style scene_editor_layer_row_button is button
    style scene_editor_layer_row_button idle_background None
    style scene_editor_layer_row_button hover_background "#17223A"
    style scene_editor_layer_row_button selected_background "#33236F"
    style scene_editor_layer_row_button padding (14, 8)

    style scene_editor_layer_row_container is hbox
    style scene_editor_layer_row_container xfill True
    style scene_editor_layer_row_container yalign 0.5

    style scene_editor_layer_thumb_frame is frame
    style scene_editor_layer_thumb_frame background "#111827"
    style scene_editor_layer_thumb_frame padding (1, 1)

    style scene_editor_layer_icon_button is button
    style scene_editor_layer_icon_button background None
    style scene_editor_layer_icon_button hover_background "#FFFFFF12"
    style scene_editor_layer_icon_button selected_background None
    style scene_editor_layer_icon_button padding (4, 6)
    style scene_editor_layer_icon_button yalign 0.5
    style scene_editor_layer_icon_button_text color "#DCE8FF" size 14
    style scene_editor_layer_icon_button_text hover_color "#FFFFFF"

    style scene_editor_layer_row_actions is hbox
    style scene_editor_layer_row_actions xalign 1.0

    style scene_editor_tree_button is button
    style scene_editor_tree_button background None
    style scene_editor_tree_button hover_background "#FFFFFF0D"
    style scene_editor_tree_button selected_background "#4B34A766"
    style scene_editor_tree_button padding (8, 3)
    style scene_editor_tree_button_text color "#A9B8D8" selected_color "#FFFFFF" size 12

    style scene_editor_assets_title is scene_photo_editor_text
    style scene_editor_assets_title color "#FFFFFF" size 16

    style scene_editor_asset_mode_tab_button is button
    style scene_editor_asset_mode_tab_button idle_background "#161F34"
    style scene_editor_asset_mode_tab_button hover_background "#1E2B47"
    style scene_editor_asset_mode_tab_button selected_background "#5B3EF7"
    style scene_editor_asset_mode_tab_button padding (12, 6)
    style scene_editor_asset_mode_tab_button_text color "#8897C4" size 13
    style scene_editor_asset_mode_tab_button_text selected_color "#FFFFFF"

    style scene_editor_sort_button is button
    style scene_editor_sort_button idle_background None
    style scene_editor_sort_button hover_background "#FFFFFF14"
    style scene_editor_sort_button selected_background "#A8C5FF22"
    style scene_editor_sort_button padding (8, 5)
    style scene_editor_sort_button_text color "#6B7DA8" size 12
    style scene_editor_sort_button_text selected_color "#8BC6FF"

    style scene_editor_search_frame is button
    style scene_editor_search_frame background "#131C30"
    style scene_editor_search_frame hover_background "#1A2440"
    style scene_editor_search_frame padding (8, 6)
    style scene_editor_search_frame xfill False
    style scene_editor_search_frame yfill False

    style scene_editor_search_input is scene_photo_properties_input
    style scene_editor_search_input background None
    style scene_editor_search_input color "#E7EEFF"
    style scene_editor_asset_tile_button is button
    style scene_editor_asset_tile_button idle_background None
    style scene_editor_asset_tile_button hover_background _viewers.scene_editor_asset_tile_hover_background
    style scene_editor_asset_tile_button insensitive_background None
    style scene_editor_asset_tile_button padding (4, 4)
    style scene_editor_asset_tile_button xpadding 4
    style scene_editor_asset_tile_button ypadding 4
    style scene_editor_asset_tile_border_frame is frame
    style scene_editor_asset_tile_border_frame background Solid(_viewers.scene_editor_asset_tile_border_color)
    style scene_editor_asset_tile_border_frame hover_background Solid(_viewers.scene_editor_asset_tile_border_highlight)
    style scene_editor_asset_tile_border_frame padding (1, 1)
    style scene_editor_asset_tile_border_frame xpadding 1
    style scene_editor_asset_tile_border_frame ypadding 1
    style scene_editor_asset_tile_thumb_frame is frame
    style scene_editor_asset_tile_thumb_frame background _viewers.scene_editor_asset_tile_background
    style scene_editor_asset_tile_thumb_frame top_padding 6
    style scene_editor_asset_tile_thumb_frame bottom_padding 6
    style scene_editor_asset_tile_thumb_frame left_padding 6
    style scene_editor_asset_tile_thumb_frame right_padding 6
    style scene_editor_asset_label_frame is frame
    style scene_editor_asset_label_frame background None
    style scene_editor_asset_label_frame ysize _viewers.scene_editor_asset_label_height
    style scene_editor_asset_label_frame xalign 0.5
    style scene_editor_asset_label_frame xpadding 4
    style scene_editor_asset_scroll_vscrollbar is vscrollbar
    style scene_editor_asset_scroll_vscrollbar xsize _viewers.scene_editor_asset_scrollbar_width
    style scene_editor_asset_scroll_vscrollbar bar_resizing False
    style scene_editor_asset_scroll_vbar is vbar
    style scene_editor_asset_scroll_vbar xsize _viewers.scene_editor_asset_scrollbar_width
    style scene_editor_asset_scroll_vthumb is vthumb
    style scene_editor_asset_scroll_vthumb xsize _viewers.scene_editor_asset_scrollbar_width
    style scene_editor_asset_scroll_vthumb background "#5C6D9322"
    style scene_editor_property_scroll_vscrollbar is vscrollbar
    style scene_editor_property_scroll_vscrollbar xsize _viewers.scene_editor_property_scrollbar_width
    style scene_editor_property_scroll_vscrollbar bar_resizing False
    style scene_editor_property_scroll_vbar is vbar
    style scene_editor_property_scroll_vbar xsize _viewers.scene_editor_property_scrollbar_width
    style scene_editor_property_scroll_vthumb is vthumb
    style scene_editor_property_scroll_vthumb xsize _viewers.scene_editor_property_scrollbar_width
    style scene_editor_property_scroll_vthumb background "#4C5D8A44"
