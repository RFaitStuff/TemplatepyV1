# Ren'Py Live Studio interface.
# Modern editor layout: properties/tree left, live canvas center, layers/tools
# right, and a Unity-style asset browser along the bottom.

style live_studio_text is default:
    color "#e9edf4"
    size 15

style live_studio_muted_text is live_studio_text:
    color "#8e9aab"
    size 13

style live_studio_heading is live_studio_text:
    color "#f5f7fb"
    size 17
    bold True

style live_studio_small is live_studio_text:
    size 12

style live_studio_panel is frame:
    background Solid("#0d141d")
    padding (10, 8)

style live_studio_panel_alt is frame:
    background Solid("#101923")
    padding (8, 7)

style live_studio_panel_header is frame:
    background Solid("#0c131b")
    padding (12, 8)

style live_studio_panel_header_text is live_studio_text:
    color "#a66cff"
    size 15
    bold True

style live_studio_button is button:
    background Solid("#17212d")
    hover_background Solid("#222f3e")
    selected_background Solid("#4b278f")
    insensitive_background Solid("#111821")
    padding (12, 7)

style live_studio_button_text is live_studio_text:
    color "#d9e0ea"
    hover_color "#ffffff"
    selected_color "#ffffff"
    insensitive_color "#566171"
    size 13

style live_studio_compact_button is live_studio_button:
    padding (9, 5)

style live_studio_compact_button_text is live_studio_button_text:
    size 12

style live_studio_icon_button is live_studio_button:
    padding (8, 5)
    xminimum 30

style live_studio_icon_button_text is live_studio_button_text:
    size 13
    text_align 0.5

style live_studio_tab is button:
    background None
    hover_background Solid("#ffffff0c")
    selected_background Solid("#4d298f")
    padding (12, 7)

style live_studio_tab_text is live_studio_button_text:
    color "#8d98a8"
    hover_color "#dce3ec"
    selected_color "#ffffff"
    size 13

style live_studio_tree_button is button:
    background None
    hover_background Solid("#ffffff0a")
    selected_background Solid("#4b278f")
    padding (7, 5)
    xfill True

style live_studio_tree_button_text is live_studio_text:
    color "#b6c0ce"
    selected_color "#ffffff"
    size 12
    text_align 0.0

style live_studio_input is input:
    color "#f6f8fb"
    size 13

style live_studio_input_frame is frame:
    background Solid("#091017")
    padding (8, 5)
    xfill True

style live_studio_property_group is button:
    background Solid("#111a24")
    hover_background Solid("#17232f")
    padding (8, 6)
    xfill True

style live_studio_property_group_text is live_studio_text:
    color "#d5dbe4"
    size 12

style live_studio_asset_tile is button:
    background Solid("#18212c")
    hover_background Solid("#263342")
    selected_background Solid("#3c236f")
    padding (5, 5)

style live_studio_asset_tile_text is live_studio_small:
    color "#d7dde6"

style live_studio_asset_thumb is frame:
    background Solid("#0f151d")
    padding (4, 4)

style live_studio_accent_text is live_studio_text:
    color "#a66cff"
    bold True

style live_studio_section_label is live_studio_muted_text:
    color "#aeb7c4"
    size 12

style live_studio_viewport is viewport:
    xfill True
    yfill True

style live_studio_vscrollbar is vscrollbar:
    xsize live_studio.SCROLLBAR_WIDTH
    base_bar Solid("#101720")
    thumb Solid("#7650c9")
    bar_resizing False

style live_studio_scrollbar is scrollbar:
    ysize live_studio.SCROLLBAR_WIDTH
    base_bar Solid("#101720")
    thumb Solid("#7650c9")
    bar_resizing False

style live_studio_layer_group is button:
    background Solid("#111a24")
    hover_background Solid("#1a2633")
    selected_background Solid("#352064")
    padding (6, 5)
    xfill True

style live_studio_layer_group_text is live_studio_text:
    size 12
    bold True
    color "#e4e8ee"

style live_studio_layer_row is button:
    background None
    hover_background Solid("#ffffff0a")
    selected_background Solid("#43257e")
    padding (5, 4)
    xfill True

style live_studio_layer_row_text is live_studio_text:
    size 12
    color "#bec7d2"
    selected_color "#ffffff"

style live_studio_folder_row is button:
    background None
    hover_background Solid("#ffffff0a")
    selected_background Solid("#3c236f")
    padding (5, 4)
    xfill True

style live_studio_folder_row_text is live_studio_text:
    size 12
    color "#aeb8c5"
    selected_color "#ffffff"

style live_studio_property_label is live_studio_muted_text:
    size 12
    yalign 0.5

style live_studio_property_input_frame is frame:
    background Solid("#091017")
    padding (6, 3)
    xfill True
    yminimum 30

style live_studio_property_input is live_studio_input:
    size 12

style live_studio_tool_button is live_studio_button:
    padding (11, 8)
    xfill True

style live_studio_tool_button_text is live_studio_button_text:
    size 12
    text_align 0.5

style live_studio_popup is frame:
    background Solid("#101923")
    padding (14, 12)

screen live_studio_editor():
    modal True
    style_prefix "live_studio"
    zorder 9999

    if live_studio.popup_is_open():
        key "game_menu" action Function(live_studio.close_all_popups)
        key "K_ESCAPE" action Function(live_studio.close_all_popups)
    else:
        key "game_menu" action [Function(live_studio.flush_pending_input_edits), Return()]
        key "K_ESCAPE" action [Function(live_studio.flush_pending_input_edits), Return()]
        key "K_DELETE" action Function(live_studio.remove_selected_item)
        key "ctrl_K_z" action Function(live_studio.undo)
        key "ctrl_K_y" action Function(live_studio.redo)
        key "ctrl_K_c" action Function(live_studio.copy_selected)
        key "ctrl_K_v" action Function(live_studio.paste_copied)
        key "ctrl_K_s" action Function(live_studio.save_project)
        key "K_q" action Function(live_studio.set_tool_mode, "select")
        key "K_g" action Function(live_studio.set_tool_mode, "move")
        key "K_s" action Function(live_studio.set_tool_mode, "resize")
        key "K_r" action Function(live_studio.set_tool_mode, "rotate")

    $ sw = config.screen_width
    $ sh = config.screen_height
    $ left_width = int(min(live_studio.LEFT_PANEL_MAX, max(live_studio.LEFT_PANEL_MIN, sw * live_studio.LEFT_PANEL_RATIO)))
    $ right_width = int(min(live_studio.RIGHT_PANEL_MAX, max(live_studio.RIGHT_PANEL_MIN, sw * live_studio.RIGHT_PANEL_RATIO)))
    $ top_height = live_studio.TOP_BAR_HEIGHT
    $ bottom_height = int(min(live_studio.BOTTOM_PANEL_MAX, max(live_studio.BOTTOM_PANEL_MIN, sh * live_studio.BOTTOM_PANEL_RATIO)))
    $ nav_height = live_studio.FRAME_NAV_HEIGHT
    $ upper_height = sh - top_height - bottom_height
    $ canvas_height = max(180, upper_height - nav_height)
    $ canvas_width = max(420, sw - left_width - right_width)
    $ inspector_height = int((sh - top_height) * 0.53)

    add Solid("#070b10")

    use live_studio_top_bar(top_height)

    # Left column: context properties above the full Scene/UI hierarchy.
    frame:
        background Solid("#0d141d")
        padding (0, 0)
        xpos 0
        ypos top_height
        xsize left_width
        ysize sh - top_height
        vbox:
            spacing 1
            xfill True
            yfill True
            frame:
                style "live_studio_panel_alt"
                padding (0, 0)
                xfill True
                ysize inspector_height
                use live_studio_inspector
            frame:
                style "live_studio_panel_alt"
                padding (0, 0)
                xfill True
                yfill True
                use live_studio_hierarchy

    # Center canvas and frame navigation.
    frame:
        background Solid(live_studio.CANVAS_BACKGROUND)
        padding (7, 7)
        xpos left_width
        ypos top_height
        xsize canvas_width
        ysize canvas_height
        add live_studio.canvas_displayable()

    frame:
        background Solid("#0d141d")
        padding (10, 6)
        xpos left_width
        ypos top_height + canvas_height
        xsize canvas_width
        ysize nav_height
        use live_studio_frame_nav

    # Right layers/history/flow inspector.
    frame:
        background Solid("#0d141d")
        padding (0, 0)
        xpos sw - right_width
        ypos top_height
        xsize right_width
        ysize upper_height
        use live_studio_right_panel

    # Bottom asset/dialogue workspace aligns exactly with the canvas.
    frame:
        background Solid("#0d141d")
        padding (10, 8)
        xpos left_width
        ypos sh - bottom_height
        xsize canvas_width
        ysize bottom_height
        use live_studio_bottom_workspace

    # Bottom-right tool palette aligns with Layers.
    frame:
        background Solid("#0d141d")
        padding (10, 8)
        xpos sw - right_width
        ypos sh - bottom_height
        xsize right_width
        ysize bottom_height
        use live_studio_tools_panel

    if live_studio.script_popup_open:
        use live_studio_script_popup
    elif live_studio.project_popup_open:
        use live_studio_project_popup
    elif live_studio.settings_popup_open:
        use live_studio_settings_popup
    elif live_studio.create_popup_open:
        use live_studio_create_popup
    elif live_studio.future_popup_open:
        use live_studio_future_popup

screen live_studio_top_bar(top_height):
    frame:
        background Solid("#0a1017")
        padding (14, 6)
        xpos 0
        ypos 0
        xfill True
        ysize top_height
        hbox:
            spacing 8
            yalign 0.5
            xfill True

            text "Ren'Py Live Studio" style "live_studio_heading" yalign 0.5
            null width 24

            text "Zoom" style "live_studio_muted_text" yalign 0.5
            textbutton "−" action Function(live_studio.zoom_canvas, -live_studio.CANVAS_ZOOM_STEP) sensitive live_studio.canvas_zoom > live_studio.CANVAS_ZOOM_MIN style "live_studio_icon_button"
            textbutton "{:.0f}%".format(live_studio.canvas_zoom * 100) action Function(live_studio.reset_canvas_zoom) tooltip "Reset to fit" style "live_studio_compact_button"
            textbutton "+" action Function(live_studio.zoom_canvas, live_studio.CANVAS_ZOOM_STEP) sensitive live_studio.canvas_zoom < live_studio.CANVAS_ZOOM_MAX style "live_studio_icon_button"
            textbutton "Fit" action Function(live_studio.reset_canvas_zoom) style "live_studio_compact_button"

            null width 16
            text "Workspace" style "live_studio_muted_text" yalign 0.5
            textbutton "{}  ▾".format(live_studio.workspace_mode) action Function(live_studio.cycle_workspace_mode) style "live_studio_button"

            null width 1 xfill True

            textbutton ("Save *" if live_studio.project_dirty else "Save") action Function(live_studio.save_project) style "live_studio_button"
            textbutton "Project  ▾" action Function(live_studio.toggle_project_popup) selected live_studio.project_popup_open style "live_studio_button"
            textbutton "Preview" action Function(live_studio.request_full_preview) style "live_studio_button"
            textbutton "</> Extract Script" action Function(live_studio.open_script_popup) selected live_studio.script_popup_open style "live_studio_button"
            textbutton "Settings  ▾" action Function(live_studio.toggle_settings_popup) selected live_studio.settings_popup_open style "live_studio_button"
            textbutton "Close" action [Function(live_studio.flush_pending_input_edits), Return()] style "live_studio_button"

screen live_studio_frame_nav():
    $ next_label = live_studio.next_frame_action_label()
    $ next_count = live_studio.future_source_count() if not live_studio.has_stored_next_frame() else 0
    hbox:
        spacing 8
        xfill True
        yalign 0.5
        text "Frames" style "live_studio_accent_text" yalign 0.5
        null width 8
        textbutton "←  Previous Frame" action Function(live_studio.previous_frame) sensitive live_studio.frame_index() > 0 style "live_studio_compact_button"
        textbutton "{}  →".format(next_label) action Function(live_studio.advance_or_import_next) sensitive live_studio.has_stored_next_frame() or next_count > 0 style "live_studio_compact_button"
        textbutton "+  Insert New Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_compact_button"
        textbutton "+  Insert Blank Frame" action Function(live_studio.add_frame, "blank", "Blank Frame") style "live_studio_compact_button"
        null width 1 xfill True
        if next_count > 1:
            text "{} future branches".format(next_count) style "live_studio_muted_text" yalign 0.5
        text "{}/{}".format(live_studio.frame_index() + 1, max(1, len(live_studio.frame_order()))) style "live_studio_muted_text" yalign 0.5

screen live_studio_text_field(label, item_id, path, value, label_width=102):
    hbox:
        spacing 6
        xfill True
        yminimum 29
        text label style "live_studio_property_label" xsize label_width
        frame:
            style "live_studio_property_input_frame"
            xfill True
            input value live_studio.editor_input_value("property", item_id, path) copypaste True style "live_studio_property_input"
        if live_studio.has_local_override(item_id, path):
            textbutton "↶" action Function(live_studio.clear_item_override, item_id, path) tooltip "Revert to inherited value" style "live_studio_icon_button"

screen live_studio_axis_field(axis, item_id, path, value, field_width=112):
    hbox:
        spacing 3
        xsize field_width
        text axis style "live_studio_muted_text" xsize 12 yalign 0.5
        frame:
            style "live_studio_property_input_frame"
            xsize max(56, field_width - (44 if live_studio.has_local_override(item_id, path) else 19))
            input value live_studio.editor_input_value("property", item_id, path) copypaste True style "live_studio_property_input"
        if live_studio.has_local_override(item_id, path):
            textbutton "↶" action Function(live_studio.clear_item_override, item_id, path) style "live_studio_icon_button"

screen live_studio_action_editor(node):
    $ action = live_studio.primary_action(node)
    $ action_type = (action or {}).get("type", "none")
    vbox:
        spacing 5
        xfill True
        text "Button Logic" style "live_studio_small"
        viewport:
            mousewheel "horizontal"
            draggable True
            xfill True
            ysize 34
            hbox:
                spacing 4
                for action_value, action_label in live_studio.ACTION_TYPES:
                    textbutton action_label action Function(live_studio.set_node_action_type, node.get("id"), action_value) selected action_type == action_value style "live_studio_compact_button"

        if action_type == "jump_frame":
            text "Destination Frame" style "live_studio_muted_text"
            viewport:
                mousewheel True
                draggable True
                ymaximum 105
                vbox:
                    spacing 2
                    xfill True
                    for frame_id, frame_name in live_studio.frame_path_options():
                        textbutton live_studio.safe_display_text(frame_name, 48) action Function(live_studio.set_button_frame_target, node.get("id"), frame_id) selected (action or {}).get("target_frame_id") == frame_id style "live_studio_tree_button"
        elif action_type in ("jump_label", "call_label"):
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "target") style "live_studio_input"
        elif action_type in ("show_screen", "hide_screen"):
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "screen") style "live_studio_input"
        elif action_type in ("set_variable", "change_variable"):
            text "Variable" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "variable") style "live_studio_input"
            if action_type == "change_variable":
                frame:
                    style "live_studio_input_frame"
                    input value live_studio.editor_input_value("action", node.get("id"), "operator") style "live_studio_input"
            text "Value" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "value") style "live_studio_input"
        elif action_type == "run_script":
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "script") style "live_studio_input"

screen live_studio_inspector():
    $ selected, parent_id, kind = live_studio.selected_item()
    vbox:
        spacing 0
        xfill True
        yfill True
        frame:
            style "live_studio_panel_header"
            xfill True
            hbox:
                text "Properties" style "live_studio_panel_header_text"
                null width 1 xfill True
                if kind == "dialogue_controller":
                    text "● Dialogue Mode" style "live_studio_muted_text"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            xfill True
            vbox:
                spacing 7
                xfill True

                if selected is None:
                    $ frame = live_studio.current_frame()
                    text "Nothing selected" style "live_studio_muted_text"
                    text "Project" style "live_studio_small"
                    frame:
                        style "live_studio_input_frame"
                        input value live_studio.editor_input_value("project_name") style "live_studio_input"
                    if frame:
                        text "Frame" style "live_studio_small"
                        frame:
                            style "live_studio_input_frame"
                            input value live_studio.editor_input_value("frame_name", frame.get("id")) style "live_studio_input"
                        text live_studio.safe_display_text("Parent: {}".format((live_studio.frame_by_id(frame.get("parent_id")) or {}).get("name", "None")), 54) style "live_studio_muted_text"
                        text live_studio.safe_display_text(live_studio.flow_summary(), 60) style "live_studio_muted_text"
                        if frame.get("source_ref"):
                            text live_studio.safe_display_text("{}:{}".format(frame.get("source_ref", {}).get("filename") or "runtime", frame.get("source_ref", {}).get("line") or "?"), 58) style "live_studio_muted_text"
                else:
                    hbox:
                        spacing 5
                        text live_studio.safe_display_text(selected.get("name", kind), 52) style "live_studio_heading"
                        text "({})".format(kind.replace("_", " ")) style "live_studio_muted_text" yalign 0.5
                    if selected.get("editability"):
                        text live_studio.safe_display_text("Editability: {}".format(selected.get("editability")), 58) style "live_studio_muted_text"

                    if kind == "dialogue_controller":
                        use live_studio_text_field("Say UI", selected.get("id"), "say_screen", selected.get("say_screen", "say"))
                        use live_studio_text_field("Choice UI", selected.get("id"), "choice_screen", selected.get("choice_screen", "choice"))
                        textbutton "Open Dialogue Workspace" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_button"
                        text "Full scene source" style "live_studio_small"
                        text live_studio.safe_display_text(live_studio.dialogue_source(selected)) style "live_studio_small"
                    elif kind in ("dialogue_event", "dialogue_choice"):
                        text "Edit this entry in the Dialogue workspace." style "live_studio_muted_text"
                        textbutton "Open Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_button"
                    elif kind == "ui_screen":
                        use live_studio_text_field("Name", selected.get("id"), "name", selected.get("name", "screen"))
                        use live_studio_text_field("Role", selected.get("id"), "role", selected.get("role", "screen"))
                        use live_studio_text_field("Layer", selected.get("id"), "layer", selected.get("layer", "screens"))
                        if not selected.get("managed"):
                            text "Runtime screen · unchanged content stays as the exact captured root." style "live_studio_muted_text"
                            text "Converting is approximate and creates an editor-owned copy." style "live_studio_muted_text"
                            textbutton "Convert Screen Copy (Approximate)" action Confirm("Create an editor-owned approximation of this runtime screen? Conditions, loops, custom displayables, and dynamic source behavior may not convert exactly.", Function(live_studio.convert_screen_in_place, selected.get("id"))) style "live_studio_button"
                        else:
                            text "Managed screen" style "live_studio_muted_text"
                    elif kind == "scene":
                        use live_studio_text_field("Scene Name", selected.get("id"), "name", selected.get("name", "Scene"))
                        text live_studio.safe_display_text("Layers: {}".format(", ".join(selected.get("source_layers", [])) or "None"), 58) style "live_studio_muted_text"
                    else:
                        use live_studio_text_field("Name", selected.get("id"), "name", selected.get("name", kind))
                        for group_name, properties in live_studio.selected_property_groups():
                            button:
                                style "live_studio_property_group"
                                action Function(live_studio.toggle_property_group, group_name)
                                hbox:
                                    xfill True
                                    text group_name style "live_studio_property_group_text"
                                    null width 1 xfill True
                                    text ("⌄" if live_studio.property_group_expanded(group_name) else "›") style "live_studio_muted_text"
                            if live_studio.property_group_expanded(group_name):
                                frame:
                                    background None
                                    padding (6, 2)
                                    xfill True
                                    vbox:
                                        spacing 6
                                        xfill True
                                        for property_row in live_studio.property_editor_rows(properties):
                                            if property_row.get("type") == "pair":
                                                $ x_label, x_path = property_row.get("x")
                                                $ y_label, y_path = property_row.get("y")
                                                $ x_value = live_studio.get_path_value(selected, x_path, None)
                                                $ y_value = live_studio.get_path_value(selected, y_path, None)
                                                vbox:
                                                    spacing 3
                                                    xfill True
                                                    text property_row.get("label") style "live_studio_property_label"
                                                    hbox:
                                                        spacing 7
                                                        xfill True
                                                        if isinstance(x_value, bool):
                                                            hbox:
                                                                spacing 3
                                                                text "X" style "live_studio_muted_text"
                                                                textbutton ("On" if x_value else "Off") action Function(live_studio.toggle_item_value, selected.get("id"), x_path) selected x_value style "live_studio_compact_button"
                                                            hbox:
                                                                spacing 3
                                                                text "Y" style "live_studio_muted_text"
                                                                textbutton ("On" if y_value else "Off") action Function(live_studio.toggle_item_value, selected.get("id"), y_path) selected y_value style "live_studio_compact_button"
                                                        else:
                                                            use live_studio_axis_field("X", selected.get("id"), x_path, x_value)
                                                            use live_studio_axis_field("Y", selected.get("id"), y_path, y_value)
                                            else:
                                                $ label = property_row.get("label")
                                                $ path = property_row.get("path")
                                                $ value = live_studio.get_path_value(selected, path, None)
                                                if selected.get("type") == "text" and path == "binding.mode":
                                                    hbox:
                                                        spacing 6
                                                        xfill True
                                                        text "Text Source" style "live_studio_property_label" xsize 102
                                                        textbutton "Text" action Function(live_studio.set_item_value, selected.get("id"), "binding.mode", "literal", "Use literal Ren'Py text") selected str(value or "literal") == "literal" style "live_studio_compact_button"
                                                        textbutton "Value" action Function(live_studio.set_item_value, selected.get("id"), "binding.mode", "expression", "Use Python/Ren'Py value") selected str(value or "literal") != "literal" style "live_studio_compact_button"
                                                elif selected.get("type") == "text" and path == "properties.text" and str(live_studio.get_path_value(selected, "binding.mode", "literal")) != "literal":
                                                    hbox:
                                                        spacing 6
                                                        xfill True
                                                        text "Current Preview" style "live_studio_property_label" xsize 102
                                                        frame:
                                                            style "live_studio_property_input_frame"
                                                            xfill True
                                                            text live_studio.safe_display_text(value if value is not None else "", 80) style "live_studio_property_input"
                                                elif selected.get("type") == "text" and path == "binding.expression" and str(live_studio.get_path_value(selected, "binding.mode", "literal")) == "literal":
                                                    pass
                                                elif isinstance(value, bool):
                                                    hbox:
                                                        spacing 6
                                                        xfill True
                                                        text label style "live_studio_property_label" xsize 102
                                                        textbutton ("On" if value else "Off") action Function(live_studio.toggle_item_value, selected.get("id"), path) selected value style "live_studio_compact_button"
                                                        if live_studio.has_local_override(selected.get("id"), path):
                                                            textbutton "↶" action Function(live_studio.clear_item_override, selected.get("id"), path) style "live_studio_icon_button"
                                                else:
                                                    use live_studio_text_field(label, selected.get("id"), path, value)
                        if kind == "ui_node" and selected.get("type") == "text":
                            $ text_binding = selected.get("binding") if isinstance(selected.get("binding"), dict) else {}
                            if text_binding.get("mode") in ("expression", "runtime", "renpy_text"):
                                text live_studio.safe_display_text("Saved as value: {}".format(text_binding.get("source_expression") or text_binding.get("expression") or "Runtime source not recoverable"), 76) style "live_studio_muted_text"
                        if kind == "ui_node" and not selected.get("widget_id"):
                            text "This runtime widget has no authored Ren'Py id. It is inspect-only until the parent screen is explicitly converted." style "live_studio_muted_text"
                            $ selected_screen = live_studio.screen_for_node(live_studio.resolve_frame(), selected.get("id"))
                            if selected_screen and not selected_screen.get("managed"):
                                textbutton "Convert Parent Screen (Approximate)" action Confirm("Convert this runtime screen in place? This creates an editor-owned approximation; dynamic conditions, loops, and custom displayables may need manual review.", Function(live_studio.convert_screen_in_place, selected_screen.get("id"))) style "live_studio_button"
                        if selected.get("type") in ("button", "textbutton", "imagebutton", "hotspot"):
                            use live_studio_action_editor(selected)

screen live_studio_hierarchy():
    $ state = live_studio.resolve_frame()
    $ rows = live_studio.visible_scene_tree_rows(state) if live_studio.selected_tree_tab == "Scene" else live_studio.visible_ui_tree_rows(state)
    vbox:
        spacing 0
        xfill True
        yfill True
        frame:
            style "live_studio_panel_header"
            xfill True
            hbox:
                spacing 5
                text "Scene Tree" style "live_studio_panel_header_text"
                null width 1 xfill True
                textbutton "Scene" action Function(live_studio.set_tree_tab, "Scene") selected live_studio.selected_tree_tab == "Scene" style "live_studio_tab"
                textbutton "UI" action Function(live_studio.set_tree_tab, "UI") selected live_studio.selected_tree_tab == "UI" style "live_studio_tab"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            xfill True
            vbox:
                spacing 1
                xfill True
                for row in rows:
                    $ item = row.get("item", {})
                    $ row_kind = row.get("kind")
                    $ depth = row.get("depth", 0)
                    $ has_children = row.get("has_children", False)
                    $ open_value = row.get("open", False)
                    hbox:
                        spacing 2
                        xfill True
                        null width depth * 13
                        if has_children:
                            textbutton ("⌄" if open_value else "›") action Function(live_studio.toggle_tree_item, item.get("id"), row_kind in ("scene", "ui_screen", "ui_node")) style "live_studio_icon_button"
                        else:
                            null width 28
                        $ is_ui_folder = row_kind in ("ui_screen", "ui_node") and (row_kind == "ui_screen" or live_studio.is_ui_container(item))
                        $ row_icon = "▣" if row_kind == "dialogue_controller" else ("▰" if is_ui_folder else ("◇" if item.get("type") == "image" else ""))
                        $ row_label = live_studio.safe_display_text("{} {}".format(row_icon, item.get("name", item.get("type", row_kind))), 58)
                        textbutton row_label action Function(live_studio.select_item, item.get("id"), row_kind) selected live_studio.selected_item_id == item.get("id") style "live_studio_tree_button"

screen live_studio_right_panel():
    vbox:
        spacing 0
        xfill True
        yfill True
        frame:
            style "live_studio_panel_header"
            xfill True
            hbox:
                spacing 3
                for tab_name in ("Layers", "History", "Debugger"):
                    textbutton tab_name action Function(live_studio.set_right_panel_tab, tab_name) selected live_studio.right_panel_tab == tab_name style "live_studio_tab"
        if live_studio.right_panel_tab == "History":
            use live_studio_history_panel
        elif live_studio.right_panel_tab == "Debugger":
            use live_studio_debug_panel
        else:
            use live_studio_layers_panel

screen live_studio_layers_panel():
    $ state = live_studio.resolve_frame()
    $ panel_mode = live_studio.layer_panel_mode
    $ layer_rows = live_studio.scene_layer_rows(state) if panel_mode == "Scene" else live_studio.ui_layer_rows(state)
    vbox:
        spacing 0
        xfill True
        yfill True
        frame:
            background Solid("#0f1720")
            padding (8, 7)
            xfill True
            hbox:
                spacing 0
                textbutton "Scene Layers" action Function(live_studio.set_layer_panel_mode, "Scene") selected panel_mode == "Scene" style "live_studio_tab"
                textbutton "UI Layers" action Function(live_studio.set_layer_panel_mode, "UI") selected panel_mode == "UI" style "live_studio_tab"
                null width 1 xfill True
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            xfill True
            vbox:
                spacing 2
                xfill True
                if not layer_rows:
                    text "No {} layers in this frame.".format(panel_mode.lower()) style "live_studio_muted_text"
                for row in layer_rows[:180]:
                    $ item = row.get("item", {})
                    $ row_kind = row.get("kind")
                    $ depth = row.get("depth", 0)
                    $ is_group = row.get("group", False)
                    $ is_selected = live_studio.selected_item_id == item.get("id")
                    if is_group:
                        hbox:
                            spacing 3
                            xfill True
                            if row.get("has_children"):
                                textbutton ("⌄" if row.get("open") else "›") action Function(live_studio.toggle_tree_item, row.get("open_key"), True) style "live_studio_icon_button"
                            else:
                                null width 30
                            button:
                                style "live_studio_layer_group"
                                selected is_selected
                                action Function(live_studio.select_layer_item, item.get("id"), row_kind)
                                xfill True
                                hbox:
                                    spacing 7
                                    frame:
                                        background Solid("#080d13")
                                        padding (2, 2)
                                        xsize live_studio.LAYER_THUMB_WIDTH + 4
                                        ysize live_studio.LAYER_THUMB_HEIGHT + 4
                                        if row_kind == "ui_screen":
                                            add live_studio.layer_thumbnail(item, row_kind, live_studio.LAYER_THUMB_WIDTH, live_studio.LAYER_THUMB_HEIGHT)
                                        else:
                                            text ("D" if item.get("type") == "dialogue" else "S") style "live_studio_accent_text" xalign 0.5 yalign 0.5
                                    vbox:
                                        spacing 1
                                        yalign 0.5
                                        text live_studio.safe_display_text(item.get("name", "Layer"), 30) style "live_studio_layer_group_text"
                                        text live_studio.safe_display_text(item.get("role", "UI screen") if row_kind == "ui_screen" else ", ".join(item.get("source_layers", [])) or "Scene", 34) style "live_studio_muted_text"
                                    null width 1 xfill True
                            textbutton ("●" if item.get("visible", True) else "○") action Function(live_studio.toggle_item_value, item.get("id"), "visible") tooltip "Show or hide" style "live_studio_icon_button"
                            textbutton ("L" if item.get("locked", False) else "·") action Function(live_studio.toggle_item_value, item.get("id"), "locked") tooltip "Lock editing" style "live_studio_icon_button"
                    else:
                        hbox:
                            spacing 3
                            xfill True
                            null width max(0, depth - 1) * 12
                            if row.get("has_children"):
                                textbutton ("⌄" if row.get("open") else "›") action Function(live_studio.toggle_tree_item, row.get("open_key"), False) style "live_studio_icon_button"
                            else:
                                null width 30
                            button:
                                style "live_studio_layer_row"
                                selected is_selected
                                action Function(live_studio.select_layer_item, item.get("id"), row_kind)
                                xfill True
                                hbox:
                                    spacing 7
                                    frame:
                                        background Solid("#080d13")
                                        padding (2, 2)
                                        xsize live_studio.LAYER_THUMB_WIDTH + 4
                                        ysize live_studio.LAYER_THUMB_HEIGHT + 4
                                        if row_kind in ("scene_node", "ui_node"):
                                            add live_studio.layer_thumbnail(item, row_kind, live_studio.LAYER_THUMB_WIDTH, live_studio.LAYER_THUMB_HEIGHT)
                                        else:
                                            text "D" style "live_studio_accent_text" xalign 0.5 yalign 0.5
                                    vbox:
                                        spacing 1
                                        yalign 0.5
                                        text live_studio.safe_display_text(item.get("name", item.get("type", "Layer")), 30) style "live_studio_layer_row_text"
                                        text live_studio.safe_display_text(item.get("widget_id") or item.get("type", "Object"), 32) style "live_studio_muted_text"
                                    null width 1 xfill True
                            textbutton ("●" if item.get("visible", True) else "○") action Function(live_studio.toggle_item_value, item.get("id"), "visible") tooltip "Show or hide" style "live_studio_icon_button"
                            textbutton ("L" if item.get("locked", False) else "·") action Function(live_studio.toggle_item_value, item.get("id"), "locked") tooltip "Lock editing" style "live_studio_icon_button"
                if len(layer_rows) > 180:
                    text "{} additional entries hidden.".format(len(layer_rows) - 180) style "live_studio_muted_text"
        frame:
            background Solid("#0b1118")
            padding (8, 6)
            xfill True
            hbox:
                spacing 5
                textbutton "+ Add" action Function(live_studio.toggle_create_popup) style "live_studio_compact_button"
                null width 1 xfill True
                textbutton "↑" action Function(live_studio.reorder_selected, "forward") sensitive live_studio.selected_item_id is not None style "live_studio_icon_button"
                textbutton "↓" action Function(live_studio.reorder_selected, "backward") sensitive live_studio.selected_item_id is not None style "live_studio_icon_button"
                textbutton "Delete" action Function(live_studio.remove_selected_item) sensitive live_studio.selected_item_id is not None style "live_studio_compact_button"

screen live_studio_structure_panel():
    $ controller = live_studio.selected_dialogue_controller()
    $ source_candidates = live_studio.source_flow_candidates()
    viewport:
        mousewheel True
        draggable True
        scrollbars "vertical"
        yfill True
        xfill True
        vbox:
            spacing 10
            xfill True
            frame:
                background Solid("#101923")
                padding (10, 8)
                xfill True
                vbox:
                    spacing 5
                    hbox:
                        text "Frame Chain" style "live_studio_small"
                        null width 1 xfill True
                        text live_studio.flow_summary() style "live_studio_muted_text"
                    for frame_id in live_studio.frame_order():
                        $ frame = live_studio.frame_by_id(frame_id)
                        textbutton live_studio.safe_display_text("{} {}".format("▶" if frame_id == live_studio.current_frame_id else "•", frame.get("name", "Frame")), 48) action Function(live_studio.select_frame, frame_id) selected frame_id == live_studio.current_frame_id style "live_studio_tree_button"

            frame:
                background Solid("#101923")
                padding (10, 8)
                xfill True
                vbox:
                    spacing 5
                    text "Dialogue Outline" style "live_studio_small"
                    if controller is None:
                        text "No Dialogue object in this frame." style "live_studio_muted_text"
                    else:
                        for index, event in enumerate(controller.get("events", [])):
                            $ label = event.get("text") or event.get("script") or event.get("target") or event.get("type", "Event")
                            textbutton live_studio.safe_display_text("{}  {}".format(index + 1, label), 48) action [Function(live_studio.select_dialogue_event, event.get("id")), Function(live_studio.set_bottom_tab, "Dialogue")] selected event.get("id") == controller.get("selected_event_id") style "live_studio_tree_button"
                            if event.get("type") == "choice":
                                for choice in event.get("choices", []):
                                    text live_studio.safe_display_text("    └ {}".format(choice.get("caption", "Choice")), 50) style "live_studio_muted_text"

            frame:
                background Solid("#101923")
                padding (10, 8)
                xfill True
                vbox:
                    spacing 5
                    hbox:
                        text "Future Frames" style "live_studio_small"
                        null width 1 xfill True
                        textbutton "Refresh" action Function(live_studio.refresh_source_flow_candidates) style "live_studio_compact_button"
                    text live_studio.safe_display_text(live_studio.source_flow_status(), 62) style "live_studio_muted_text"
                    if not source_candidates:
                        text "No static future interaction found." style "live_studio_muted_text"
                    for source_index, candidate in enumerate(source_candidates[:16]):
                        textbutton live_studio.safe_display_text(candidate.get("title", "Next state"), 52) action Function(live_studio.import_source_candidate, source_index) style "live_studio_tree_button"

screen live_studio_history_panel():
    vbox:
        spacing 6
        xfill True
        yfill True
        frame:
            background Solid("#0f1720")
            padding (9, 7)
            xfill True
            hbox:
                text "Edit History" style "live_studio_small"
                null width 1 xfill True
                textbutton "Undo" action Function(live_studio.undo) sensitive bool(live_studio.history) style "live_studio_compact_button"
                textbutton "Redo" action Function(live_studio.redo) sensitive bool(live_studio.redo_stack) style "live_studio_compact_button"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 2
                xfill True
                if not live_studio.history:
                    text "No edits yet." style "live_studio_muted_text"
                for entry in reversed(live_studio.history[-80:]):
                    text live_studio.safe_display_text("• {}".format(entry.get("label", entry.get("type", "Edit"))), 56) style "live_studio_muted_text"

screen live_studio_debug_panel():
    vbox:
        spacing 7
        xfill True
        yfill True
        hbox:
            spacing 5
            text "Debug Snapshot" style "live_studio_small" yalign 0.5
            null width 1 xfill True
            textbutton "Copy Full Report" action Function(live_studio.copy_debug_report) style "live_studio_button"
        $ debug_state = live_studio.resolve_frame()
        $ debug_frame = live_studio.current_frame() or {}
        $ debug_filter = live_studio.runtime.get("last_ui_capture_filter", {})
        text live_studio.safe_display_text("Frame: {} · Rev {} · {}".format(debug_frame.get("name", "None"), live_studio.runtime.get("state_revision", 0), live_studio.runtime.get("last_invalidation_reason", "no invalidation recorded")), 74) style "live_studio_muted_text"
        text live_studio.safe_display_text("Capture: {} UI screens · {} filtered · serial {}".format(debug_filter.get("captured", len(debug_state.get("ui_screens", []))), debug_filter.get("filtered", 0), live_studio.runtime.get("capture_serial", 0)), 74) style "live_studio_muted_text"
        hbox:
            spacing 5
            textbutton "Refresh Views" action [Function(live_studio.invalidate_view_caches, False, "manual debugger refresh"), Function(live_studio.restart)] style "live_studio_compact_button"
            textbutton "Clear Log" action Function(live_studio.clear_diagnostics) style "live_studio_compact_button"
        frame:
            style "live_studio_property_input_frame"
            xfill True
            yfill True
            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"
                xfill True
                yfill True
                text live_studio.safe_display_text(live_studio.debug_report_preview(), None, False) substitute False style "live_studio_small"


screen live_studio_settings_panel():
    vbox:
        spacing 9
        xfill True
        yfill True
        text "Canvas Preview" style "live_studio_small"
        hbox:
            spacing 5
            textbutton "Exact Capture" action Function(live_studio.set_preview_mode, "capture") selected live_studio.preview_mode == "capture" style "live_studio_compact_button"
            textbutton "Editable Layout" action Function(live_studio.set_preview_mode, "layout") selected live_studio.preview_mode == "layout" style "live_studio_compact_button"
        text "Guides and Snapping" style "live_studio_small"
        hbox:
            spacing 5
            textbutton ("Snap On" if live_studio.project_setting("snap_enabled", True) else "Snap Off") action Function(live_studio.toggle_project_setting, "snap_enabled") selected live_studio.project_setting("snap_enabled", True) style "live_studio_compact_button"
            textbutton ("Guides On" if live_studio.project_setting("guides_enabled", True) else "Guides Off") action Function(live_studio.toggle_project_setting, "guides_enabled") selected live_studio.project_setting("guides_enabled", True) style "live_studio_compact_button"
        hbox:
            spacing 5
            textbutton ("Grid On" if live_studio.project_setting("grid_enabled", False) else "Grid Off") action Function(live_studio.toggle_project_setting, "grid_enabled") selected live_studio.project_setting("grid_enabled", False) style "live_studio_compact_button"
            textbutton ("Bounds On" if live_studio.project_setting("show_all_bounds", False) else "Bounds Off") action Function(live_studio.toggle_project_setting, "show_all_bounds") selected live_studio.project_setting("show_all_bounds", False) style "live_studio_compact_button"
        add Solid("#24303e", xsize=402, ysize=1)
        text "Runtime UI Capture" style "live_studio_small"
        text "Only active, rendered gameplay screens are captured. Live Studio always excludes itself." style "live_studio_muted_text"
        textbutton ("Exclude Ren'Py engine/developer screens: On" if live_studio.project_setting("ui_capture_filter_engine_screens", live_studio.UI_CAPTURE_FILTER_ENGINE_SCREENS) else "Exclude Ren'Py engine/developer screens: Off") action Function(live_studio.toggle_ui_capture_engine_filter) selected live_studio.project_setting("ui_capture_filter_engine_screens", live_studio.UI_CAPTURE_FILTER_ENGINE_SCREENS) style "live_studio_button"
        textbutton ("Expose Say/Choice in UI hierarchy: On" if live_studio.project_setting("ui_capture_include_dialogue_screens", live_studio.UI_CAPTURE_DIALOGUE_SCREENS) else "Expose Say/Choice in UI hierarchy: Off") action Function(live_studio.toggle_project_setting, "ui_capture_include_dialogue_screens") selected live_studio.project_setting("ui_capture_include_dialogue_screens", live_studio.UI_CAPTURE_DIALOGUE_SCREENS) style "live_studio_button"
        text "When off, active dialogue presentation stays visible as a frozen canvas preview but is edited from Dialogue, not Layers." style "live_studio_muted_text"
        text "These options apply on the next Fresh Capture." style "live_studio_muted_text"
        $ ui_filter_info = live_studio.runtime.get("last_ui_capture_filter", {})
        if ui_filter_info:
            text live_studio.safe_display_text("Last capture: {captured} active / {filtered} filtered".format(**ui_filter_info), 62) style "live_studio_muted_text"
        textbutton "Fresh Capture" action Confirm("Discard this frame's local edits and recapture the running game?", Function(live_studio.refresh_runtime_capture)) style "live_studio_button"

screen live_studio_bottom_workspace():
    if live_studio.is_extension_bottom_tab():
        use live_studio_extension_workspace
    elif live_studio.bottom_tab == "Dialogue":
        vbox:
            spacing 6
            xfill True
            yfill True
            hbox:
                spacing 4
                text "Dialogue" style "live_studio_accent_text" yalign 0.5
                textbutton "Assets" action Function(live_studio.set_bottom_tab, "Assets") style "live_studio_tab"
                textbutton "Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") selected True style "live_studio_tab"
                for ext in live_studio.visible_extensions():
                    textbutton ext.get("title", ext.get("id")) action Function(live_studio.set_bottom_tab, live_studio.extension_tab_id(ext.get("id"))) style "live_studio_tab"
                null width 1 xfill True
                text live_studio.safe_display_text(live_studio.flow_summary(), 48) style "live_studio_muted_text" yalign 0.5
            use live_studio_dialogue_workspace
    else:
        use live_studio_assets_workspace

screen live_studio_assets_workspace():
    $ editor_left = int(min(live_studio.LEFT_PANEL_MAX, max(live_studio.LEFT_PANEL_MIN, config.screen_width * live_studio.LEFT_PANEL_RATIO)))
    $ editor_right = int(min(live_studio.RIGHT_PANEL_MAX, max(live_studio.RIGHT_PANEL_MIN, config.screen_width * live_studio.RIGHT_PANEL_RATIO)))
    $ asset_area_width = max(280, config.screen_width - editor_left - editor_right - live_studio.ASSET_TREE_WIDTH - 46)
    $ asset_cols = max(2, int(asset_area_width / 128))
    vbox:
        spacing 6
        xfill True
        yfill True
        hbox:
            spacing 4
            text "Assets" style "live_studio_accent_text" yalign 0.5
            for category_value, category_label in live_studio.ASSET_CATEGORIES:
                textbutton category_label action Function(live_studio.set_asset_category, category_value) selected live_studio.asset_category == category_value style "live_studio_tab"
            frame:
                style "live_studio_property_input_frame"
                xsize 240
                hbox:
                    spacing 5
                    text "Search" style "live_studio_muted_text" yalign 0.5
                    input value live_studio.asset_filter_input copypaste True style "live_studio_property_input"
            textbutton "Go" action Function(live_studio.apply_asset_filter) style "live_studio_compact_button"
            if live_studio.asset_filter:
                textbutton "Clear" action Function(live_studio.clear_asset_filter) style "live_studio_compact_button"
            null width 1 xfill True
            textbutton "Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_tab"
            for ext in live_studio.visible_extensions():
                textbutton ext.get("title", ext.get("id")) action Function(live_studio.set_bottom_tab, live_studio.extension_tab_id(ext.get("id"))) style "live_studio_tab"
            textbutton "Grid" action Function(live_studio.set_asset_view_mode, "grid") selected live_studio.asset_view_mode == "grid" style "live_studio_icon_button"
            textbutton "List" action Function(live_studio.set_asset_view_mode, "list") selected live_studio.asset_view_mode == "list" style "live_studio_icon_button"

        hbox:
            spacing 7
            xfill True
            yfill True
            frame:
                background Solid("#0a1017")
                padding (6, 6)
                xsize live_studio.ASSET_TREE_WIDTH
                yfill True
                vbox:
                    spacing 4
                    xfill True
                    hbox:
                        text "Project Assets" style "live_studio_small"
                        null width 1 xfill True
                        textbutton "Home" action Function(live_studio.open_asset_folder, ()) style "live_studio_compact_button"
                    viewport:
                        mousewheel True
                        draggable True
                        scrollbars "vertical"
                        yfill True
                        xfill True
                        vbox:
                            spacing 1
                            xfill True
                            for row in live_studio.asset_tree_rows():
                                $ depth = row.get("depth", 0)
                                $ path = row.get("path", ())
                                hbox:
                                    spacing 1
                                    xfill True
                                    null width depth * 11
                                    if row.get("has_children"):
                                        textbutton ("⌄" if row.get("open") else "›") action Function(live_studio.toggle_asset_folder, path) style "live_studio_icon_button"
                                    else:
                                        null width 30
                                    textbutton live_studio.safe_display_text(row.get("name", "Assets"), 32) action Function(live_studio.open_asset_folder, path) selected row.get("selected", False) style "live_studio_folder_row"

            frame:
                background Solid("#24303e")
                padding (0, 0)
                xsize 1
                yfill True

            vbox:
                spacing 5
                xfill True
                yfill True
                hbox:
                    spacing 4
                    textbutton "Up" action Function(live_studio.asset_go_up) sensitive bool(live_studio.asset_current_path) style "live_studio_compact_button"
                    text live_studio.safe_display_text(live_studio.asset_breadcrumb(), 60) style "live_studio_muted_text" yalign 0.5
                    null width 1 xfill True
                    textbutton live_studio.asset_sort_mode + "  ▾" action Function(live_studio.set_asset_sort_mode, "Name Z-A" if live_studio.asset_sort_mode == "Name A-Z" else ("Recent" if live_studio.asset_sort_mode == "Name Z-A" else ("Oldest" if live_studio.asset_sort_mode == "Recent" else "Name A-Z"))) style "live_studio_compact_button"
                    textbutton "Refresh" action Function(live_studio.refresh_assets) style "live_studio_compact_button"
                    textbutton "←" action Function(live_studio.previous_asset_page) sensitive live_studio.asset_page > 0 style "live_studio_icon_button"
                    text live_studio.asset_page_label() style "live_studio_muted_text" yalign 0.5
                    textbutton "→" action Function(live_studio.next_asset_page) sensitive live_studio.asset_page + 1 < live_studio.asset_page_count() style "live_studio_icon_button"

                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    xfill True
                    if live_studio.asset_view_mode == "list":
                        vbox:
                            spacing 3
                            xfill True
                            for folder in live_studio.asset_folder_entries():
                                textbutton live_studio.safe_display_text("Folder  ·  {}".format(folder.get("name", "Folder")), 72) action Function(live_studio.open_asset_folder, folder.get("path", ())) style "live_studio_folder_row"
                            for asset in live_studio.assets():
                                if asset.get("kind") == "image":
                                    button:
                                        style "live_studio_layer_row"
                                        action Function(live_studio.add_asset_to_current_context, asset.get("name"))
                                        xfill True
                                        hbox:
                                            spacing 8
                                            frame:
                                                style "live_studio_asset_thumb"
                                                xsize 58
                                                ysize 42
                                                add live_studio.asset_thumbnail(asset.get("name"), 50, 34) xalign 0.5 yalign 0.5
                                            vbox:
                                                spacing 1
                                                yalign 0.5
                                                text live_studio.safe_display_text(live_studio.asset_short_name(asset), 54) style "live_studio_layer_row_text"
                                                text live_studio.safe_display_text(asset.get("name", "Image"), 62) style "live_studio_muted_text"
                                else:
                                    frame:
                                        background Solid("#121b25")
                                        padding (8, 5)
                                        xfill True
                                        hbox:
                                            spacing 8
                                            text "Audio" style "live_studio_accent_text" yalign 0.5
                                            text live_studio.safe_display_text(live_studio.asset_short_name(asset), 54) style "live_studio_layer_row_text" yalign 0.5
                                            null width 1 xfill True
                                            textbutton "Music" action Function(live_studio.add_audio_event, asset.get("name"), "music") style "live_studio_compact_button"
                                            textbutton "SFX" action Function(live_studio.add_audio_event, asset.get("name"), "sound") style "live_studio_compact_button"
                    else:
                        vpgrid:
                            cols asset_cols
                            spacing 7
                            xfill True
                            for folder in live_studio.asset_folder_entries():
                                button:
                                    style "live_studio_asset_tile"
                                    action Function(live_studio.open_asset_folder, folder.get("path", ()))
                                    xsize 120
                                    ysize 100
                                    vbox:
                                        spacing 5
                                        xalign 0.5
                                        yalign 0.5
                                        text "Folder" style "live_studio_accent_text" xalign 0.5
                                        text live_studio.safe_display_text(folder.get("name", "Folder"), 21) style "live_studio_asset_tile_text" xalign 0.5 text_align 0.5
                            for asset in live_studio.assets():
                                if asset.get("kind") == "image":
                                    button:
                                        style "live_studio_asset_tile"
                                        action Function(live_studio.add_asset_to_current_context, asset.get("name"))
                                        xsize 120
                                        ysize 100
                                        vbox:
                                            spacing 3
                                            xalign 0.5
                                            frame:
                                                style "live_studio_asset_thumb"
                                                xsize 108
                                                ysize 68
                                                add live_studio.asset_thumbnail(asset.get("name"), 100, 60) xalign 0.5 yalign 0.5
                                            text live_studio.safe_display_text(live_studio.asset_short_name(asset), 21) style "live_studio_asset_tile_text" xalign 0.5 text_align 0.5
                                else:
                                    frame:
                                        background Solid("#18212c")
                                        padding (5, 5)
                                        xsize 120
                                        ysize 100
                                        vbox:
                                            spacing 4
                                            xalign 0.5
                                            yalign 0.5
                                            text "Audio" style "live_studio_accent_text" xalign 0.5
                                            text live_studio.safe_display_text(live_studio.asset_short_name(asset), 20) style "live_studio_asset_tile_text" xalign 0.5 text_align 0.5
                                            hbox:
                                                spacing 2
                                                xalign 0.5
                            textbutton "Music" action Function(live_studio.add_audio_event, asset.get("name"), "music") style "live_studio_compact_button"
                            textbutton "SFX" action Function(live_studio.add_audio_event, asset.get("name"), "sound") style "live_studio_compact_button"


screen live_studio_extension_workspace():
    $ ext = live_studio.active_extension()
    if ext is None:
        vbox:
            spacing 6
            text "Extension unavailable" style "live_studio_heading"
            textbutton "Assets" action Function(live_studio.set_bottom_tab, "Assets") style "live_studio_tab"
    else:
        vbox:
            spacing 6
            xfill True
            yfill True
            hbox:
                spacing 4
                text ext.get("title", "Extension") style "live_studio_accent_text" yalign 0.5
                textbutton "Assets" action Function(live_studio.set_bottom_tab, "Assets") style "live_studio_tab"
                textbutton "Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_tab"
                for other_ext in live_studio.visible_extensions():
                    textbutton other_ext.get("title", other_ext.get("id")) action Function(live_studio.set_bottom_tab, live_studio.extension_tab_id(other_ext.get("id"))) selected other_ext.get("id") == ext.get("id") style "live_studio_tab"
                null width 1 xfill True
                text live_studio.safe_display_text(ext.get("description", ""), 58) style "live_studio_muted_text" yalign 0.5

            hbox:
                spacing 8
                xfill True
                yfill True
                frame:
                    style "live_studio_panel_alt"
                    xsize 300
                    yfill True
                    viewport:
                        mousewheel True
                        draggable True
                        scrollbars "vertical"
                        yfill True
                        vbox:
                            spacing 6
                            text "Commands" style "live_studio_heading"
                            text "Search commands" style "live_studio_muted_text"
                            frame:
                                style "live_studio_property_input_frame"
                                xfill True
                                input value live_studio.extension_filter_input(ext.get("id"), "command") copypaste True style "live_studio_property_input"
                            vbox:
                                spacing 3
                                for category in live_studio.extension_command_categories(ext):
                                    textbutton category action Function(live_studio.set_selected_extension_category, ext.get("id"), category) selected live_studio.selected_extension_category(ext) == category style "live_studio_compact_button"
                            for command in live_studio.filtered_extension_commands(ext):
                                button:
                                    style "live_studio_tool_button"
                                    action (Confirm("This command can write to source files after creating a backup. Continue?", Function(live_studio.run_extension_command, ext.get("id"), command.get("id"))) if command.get("writes") else Function(live_studio.run_extension_command, ext.get("id"), command.get("id")))
                                    xfill True
                                    vbox:
                                        spacing 2
                                        text (command.get("title", command.get("id", "Command")) + ("  [writes]" if command.get("writes") else "")) style "live_studio_button_text"
                                        if command.get("description"):
                                            text live_studio.safe_display_text(command.get("description"), 42) style "live_studio_muted_text"
                            add Solid("#24303e", xsize=290, ysize=1)
                            text "Registry Snapshot" style "live_studio_heading"
                            for row in live_studio.extension_summary_rows(ext):
                                text live_studio.safe_display_text("{}: {}".format(row.get("label", ""), row.get("value", "")), 54) style "live_studio_muted_text"

                frame:
                    style "live_studio_panel_alt"
                    xsize 330
                    yfill True
                    vbox:
                        spacing 6
                        hbox:
                            text "Project Files" style "live_studio_heading" yalign 0.5
                            null width 1 xfill True
                            textbutton "Preview" action Function(live_studio.preview_selected_extension_file) sensitive bool(live_studio.selected_extension_file(ext)) style "live_studio_compact_button"
                        hbox:
                            spacing 3
                            for domain in live_studio.extension_file_domains(ext):
                                textbutton domain action Function(live_studio.set_selected_extension_file_domain, ext.get("id"), domain) selected live_studio.selected_extension_file_domain(ext) == domain style "live_studio_compact_button"
                        text "Search files" style "live_studio_muted_text"
                        frame:
                            style "live_studio_property_input_frame"
                            xfill True
                            input value live_studio.extension_filter_input(ext.get("id"), "file") copypaste True style "live_studio_property_input"
                        viewport:
                            mousewheel True
                            draggable True
                            scrollbars "vertical"
                            yfill True
                            vbox:
                                spacing 2
                                for file_row in live_studio.filtered_extension_file_rows(ext):
                                    $ file_id = file_row.get("id", "")
                                    $ selected_file = live_studio.selected_extension_file(ext) == file_id
                                    button:
                                        style "live_studio_tree_button"
                                        selected selected_file
                                        action Function(live_studio.set_selected_extension_file, ext.get("id"), file_id)
                                        xfill True
                                        vbox:
                                            spacing 1
                                            text live_studio.safe_display_text(file_row.get("label", file_id), 34) style "live_studio_tree_button_text"
                                            text live_studio.safe_display_text("{} · {}".format(file_row.get("domain", ""), file_row.get("path", "")), 42) style "live_studio_muted_text"

                frame:
                    style "live_studio_panel_alt"
                    xfill True
                    yfill True
                    vbox:
                        spacing 6
                        hbox:
                            text live_studio.extension_preview_title() style "live_studio_heading" yalign 0.5
                            null width 1 xfill True
                            textbutton "Copy" action Function(live_studio.copy_extension_preview) sensitive bool(live_studio.extension_preview_text()) style "live_studio_compact_button"
                            textbutton "Apply to File" action Confirm("Back up the selected file and append the generated preview?", Function(live_studio.apply_extension_preview)) sensitive bool(live_studio.extension_preview_text() and live_studio.selected_extension_file(ext)) style "live_studio_compact_button"
                        viewport:
                            mousewheel True
                            draggable True
                            scrollbars "vertical"
                            yfill True
                            frame:
                                background Solid("#080d15")
                                padding (10, 8)
                                xfill True
                                if live_studio.extension_preview_text():
                                    text live_studio.safe_display_text(live_studio.extension_preview_text(), escape_interpolation=False) style "live_studio_small"
                                else:
                                    text "Run a command to generate editable Project Tac code or validation notes." style "live_studio_muted_text"


screen live_studio_dialogue_workspace():
    $ controller = live_studio.selected_dialogue_controller()
    $ event = live_studio.selected_dialogue_event()
    if controller is None:
        vbox:
            spacing 8
            xalign 0.5
            yalign 0.5
            text "This frame has no Dialogue object." style "live_studio_heading"
            text "Dialogue belongs to a Scene; Say and Choice are separate UI screens." style "live_studio_muted_text"
            textbutton "Add Dialogue to Dialogue Scene" action Function(live_studio.ensure_dialogue_controller) style "live_studio_button"
    else:
        vbox:
            spacing 5
            xfill True
            yfill True
            hbox:
                spacing 5
                text "Dialogue Entries — Frame {}/{}".format(live_studio.frame_index() + 1, max(1, len(live_studio.frame_order()))) style "live_studio_small"
                null width 1 xfill True
                textbutton "+ Line" action Function(live_studio.add_dialogue_event, "say") style "live_studio_compact_button"
                textbutton "+ Choice" action Function(live_studio.add_dialogue_event, "choice") style "live_studio_compact_button"
                textbutton "+ Script" action Function(live_studio.add_dialogue_event, "script") style "live_studio_compact_button"
            hbox:
                spacing 8
                xfill True
                yfill True
                frame:
                    style "live_studio_panel_alt"
                    xsize int((config.screen_width - 760) * 0.30)
                    yfill True
                    vbox:
                        spacing 4
                        xfill True
                        viewport:
                            mousewheel True
                            draggable True
                            scrollbars "vertical"
                            yfill True
                            vbox:
                                spacing 2
                                xfill True
                                for index, item in enumerate(controller.get("events", [])):
                                    $ marker = "▶" if item.get("id") in controller.get("frame_event_ids", []) else " "
                                    $ preview = item.get("text") or item.get("script") or item.get("target") or item.get("type", "Event")
                                    textbutton live_studio.safe_display_text("{} {:02d}  {}".format(marker, index + 1, preview), 48) action Function(live_studio.select_dialogue_event, item.get("id")) selected event and event.get("id") == item.get("id") style "live_studio_tree_button"
                        hbox:
                            spacing 3
                            textbutton "Python" action Function(live_studio.add_dialogue_event, "script") style "live_studio_compact_button"
                            textbutton "Ren'Py" action Function(live_studio.add_dialogue_event, "renpy") style "live_studio_compact_button"
                            textbutton "Image" action Function(live_studio.add_dialogue_event, "show_image") style "live_studio_compact_button"
                            textbutton "Audio" action Function(live_studio.add_dialogue_event, "play_sound") style "live_studio_compact_button"
                frame:
                    style "live_studio_panel_alt"
                    xfill True
                    yfill True
                    if event is None:
                        text "Select or add an event." style "live_studio_muted_text"
                    else:
                        viewport:
                            mousewheel True
                            draggable True
                            scrollbars "vertical"
                            yfill True
                            vbox:
                                spacing 6
                                xfill True
                                hbox:
                                    text "Current: {}".format(event.get("type", "say").replace("_", " ").title()) style "live_studio_heading"
                                    null width 1 xfill True
                                    textbutton "Use in Frame" action Function(live_studio.set_active_dialogue_event, event.get("id")) selected event.get("id") in controller.get("frame_event_ids", []) style "live_studio_compact_button"
                                    textbutton "Delete" action Function(live_studio.remove_dialogue_event, event.get("id")) style "live_studio_compact_button"
                                if event.get("type") == "say":
                                    use live_studio_text_field("Speaker", event.get("id"), "speaker", event.get("speaker", ""))
                                    use live_studio_text_field("Dialogue", event.get("id"), "text", event.get("text", ""))
                                elif event.get("type") == "narration":
                                    use live_studio_text_field("Narration", event.get("id"), "text", event.get("text", ""))
                                elif event.get("type") == "script":
                                    use live_studio_text_field("Python command", event.get("id"), "script", event.get("script", ""))
                                elif event.get("type") == "renpy":
                                    use live_studio_text_field("Ren'Py statement", event.get("id"), "script", event.get("script", ""))
                                elif event.get("type") in ("jump", "call"):
                                    use live_studio_text_field("Label", event.get("id"), "target", event.get("target", ""))
                                elif event.get("type") in ("show_image", "hide_image"):
                                    use live_studio_text_field("Image", event.get("id"), "image", event.get("image", ""))
                                elif event.get("type") in ("show_screen", "hide_screen"):
                                    use live_studio_text_field("Screen", event.get("id"), "screen", event.get("screen", ""))
                                elif event.get("type") == "pause":
                                    use live_studio_text_field("Seconds", event.get("id"), "duration", event.get("duration", 0.0))
                                elif event.get("type") == "transition":
                                    use live_studio_text_field("Transition", event.get("id"), "transition", event.get("transition", "dissolve"))
                                elif event.get("type") in ("play_music", "play_sound"):
                                    use live_studio_text_field("Audio file", event.get("id"), "audio", event.get("audio", ""))
                                    use live_studio_text_field("Fade in", event.get("id"), "fadein", event.get("fadein", 0.0))
                                elif event.get("type") == "choice":
                                    use live_studio_text_field("Optional speaker", event.get("id"), "speaker", event.get("speaker", ""))
                                    use live_studio_text_field("Optional prompt", event.get("id"), "text", event.get("text", ""))
                                    hbox:
                                        text "Choices" style "live_studio_small"
                                        null width 1 xfill True
                                        textbutton "+ Choice" action Function(live_studio.add_choice_option, event.get("id")) style "live_studio_compact_button"
                                    for choice in event.get("choices", []):
                                        frame:
                                            style "live_studio_panel"
                                            xfill True
                                            vbox:
                                                spacing 4
                                                use live_studio_text_field("Caption", choice.get("id"), "caption", choice.get("caption", "Choice"))
                                                use live_studio_text_field("Condition", choice.get("id"), "condition", choice.get("condition", ""))
                                                use live_studio_text_field("Script", choice.get("id"), "script", choice.get("script", ""))
                                                use live_studio_text_field("Label target", choice.get("id"), "target", choice.get("target", ""))
                                                viewport:
                                                    mousewheel "horizontal"
                                                    draggable True
                                                    ysize 34
                                                    hbox:
                                                        spacing 3
                                                        for frame_id, frame_name in live_studio.frame_path_options():
                                                            textbutton live_studio.safe_display_text(frame_name, 34) action Function(live_studio.set_item_value, choice.get("id"), "target_frame_id", frame_id, "Set choice frame") selected choice.get("target_frame_id") == frame_id style "live_studio_compact_button"
                                                textbutton "Remove Choice" action Function(live_studio.remove_choice_option, choice.get("id")) style "live_studio_compact_button"
                                if event.get("type") not in ("choice", "return"):
                                    use live_studio_text_field("Condition", event.get("id"), "condition", event.get("condition", ""))

screen live_studio_script_popup():
    button:
        background Solid("#0000009a")
        hover_background Solid("#0000009a")
        selected_background Solid("#0000009a")
        xfill True
        yfill True
        action Function(live_studio.close_script_popup)
    fixed:
        xalign 0.5
        yalign 0.5
        xsize int(config.screen_width * 0.82)
        ysize int(config.screen_height * 0.82)
        # Consume otherwise-unhandled clicks inside the popup so they cannot
        # reach the full-screen dismiss button behind it.
        button:
            background Solid("#0d1627")
            hover_background Solid("#0d1627")
            selected_background Solid("#0d1627")
            xfill True
            yfill True
            action Function(live_studio.consume_event)
        frame:
            background None
            padding (14, 11)
            xfill True
            yfill True
            vbox:
                spacing 8
                xfill True
                yfill True
                hbox:
                    spacing 7
                    text "Generated Ren'Py Script" style "live_studio_heading" yalign 0.5
                    text "Preview, copy, or export without leaving the editor." style "live_studio_muted_text" yalign 0.5
                    null width 1 xfill True
                    textbutton "Close" action Function(live_studio.close_script_popup) style "live_studio_button"
                add Solid("#2b3953", xsize=config.screen_width, ysize=1)
                use live_studio_export_workspace

screen live_studio_export_workspace():
    $ export_section = live_studio.script_export_section
    vbox:
        spacing 5
        xfill True
        yfill True
        hbox:
            spacing 5
            textbutton "story.rpy" action Function(live_studio.set_script_export_section, "story") selected export_section == "story" style "live_studio_tab"
            textbutton "screens.rpy" action Function(live_studio.set_script_export_section, "screens") selected export_section == "screens" style "live_studio_tab"
            textbutton "helpers.rpy" action Function(live_studio.set_script_export_section, "helpers") selected export_section == "helpers" style "live_studio_tab"
            null width 1 xfill True
            textbutton "Regenerate" action Function(live_studio.generate_exports) style "live_studio_compact_button"
            textbutton "Copy Current" action Function(live_studio.copy_export, export_section) style "live_studio_compact_button"
            textbutton "Export Files" action Function(live_studio.export_files) style "live_studio_compact_button"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            frame:
                background Solid("#080d15")
                padding (10, 8)
                xfill True
                text live_studio.safe_display_text(live_studio.export_preview(export_section)) style "live_studio_small"

screen live_studio_project_popup():
    button:
        background Solid("#00000055")
        hover_background Solid("#00000055")
        xfill True
        yfill True
        action Function(live_studio.close_all_popups)
    frame:
        style "live_studio_popup"
        xpos config.screen_width - 520
        ypos live_studio.TOP_BAR_HEIGHT - 1
        xsize 330
        ymaximum int(config.screen_height * 0.72)
        vbox:
            spacing 8
            xfill True
            hbox:
                text "Project" style "live_studio_heading"
                null width 1 xfill True
                textbutton "Close" action Function(live_studio.close_all_popups) style "live_studio_compact_button"
            text live_studio.safe_display_text(live_studio.project_name(), 42) style "live_studio_muted_text"
            textbutton "Save Project" action Function(live_studio.save_project_from_ui) style "live_studio_button"
            textbutton "New Blank Project" action Confirm("Replace the current in-memory project with a blank project?", Function(live_studio.new_blank_project_from_ui)) style "live_studio_button"
            textbutton "Capture Running Game as New Project" action Confirm("Replace the current in-memory project with a fresh runtime capture?", Function(live_studio.new_capture_project_from_ui)) style "live_studio_button"
            add Solid("#24303e", xsize=306, ysize=1)
            text "Saved Projects" style "live_studio_small"
            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"
                ymaximum 260
                vbox:
                    spacing 3
                    xfill True
                    $ project_paths = live_studio.saved_project_paths()
                    if not project_paths:
                        text "No saved Live Studio projects yet." style "live_studio_muted_text"
                    for project_path in project_paths:
                        textbutton live_studio.safe_display_text(live_studio.project_file_label(project_path), 38) action Function(live_studio.load_project_from_ui, project_path) style "live_studio_tree_button"

screen live_studio_settings_popup():
    button:
        background Solid("#00000055")
        hover_background Solid("#00000055")
        xfill True
        yfill True
        action Function(live_studio.close_all_popups)
    frame:
        style "live_studio_popup"
        xpos config.screen_width - 455
        ypos live_studio.TOP_BAR_HEIGHT - 1
        xsize 430
        ysize min(620, config.screen_height - live_studio.TOP_BAR_HEIGHT - 24)
        vbox:
            spacing 8
            xfill True
            yfill True
            hbox:
                text "Editor Settings" style "live_studio_heading"
                null width 1 xfill True
                textbutton "Close" action Function(live_studio.close_all_popups) style "live_studio_compact_button"
            add Solid("#24303e", xsize=402, ysize=1)
            use live_studio_settings_panel


screen live_studio_future_popup():
    button:
        background Solid("#00000066")
        hover_background Solid("#00000066")
        xfill True
        yfill True
        action Function(live_studio.close_all_popups)
    frame:
        style "live_studio_popup"
        xalign 0.5
        yalign 0.5
        xsize min(620, config.screen_width - 80)
        ysize min(520, config.screen_height - 80)
        vbox:
            spacing 9
            xfill True
            yfill True
            hbox:
                text "Choose Future Frame" style "live_studio_heading"
                null width 1 xfill True
                textbutton "Close" action Function(live_studio.close_all_popups) style "live_studio_compact_button"
            text live_studio.safe_display_text(live_studio.source_flow_status(), 90) style "live_studio_muted_text"
            viewport:
                mousewheel True
                draggable True
                scrollbars "vertical"
                xfill True
                yfill True
                vbox:
                    spacing 5
                    xfill True
                    $ future_candidates = live_studio.source_flow_candidates()
                    if not future_candidates:
                        text "No static future interactions were found." style "live_studio_muted_text"
                    for future_index, candidate in enumerate(future_candidates):
                        textbutton live_studio.safe_display_text(candidate.get("title", "Next state"), 82) action Function(live_studio.import_source_candidate, future_index) style "live_studio_tree_button"

screen live_studio_create_popup():
    button:
        background Solid("#00000066")
        hover_background Solid("#00000066")
        xfill True
        yfill True
        action Function(live_studio.close_all_popups)
    frame:
        style "live_studio_popup"
        xalign 0.5
        yalign 0.5
        xsize min(620, config.screen_width - 80)
        ysize min(480, config.screen_height - 80)
        vbox:
            spacing 10
            xfill True
            yfill True
            hbox:
                text "Create" style "live_studio_heading"
                text "Add scene, UI, dialogue, or frame content." style "live_studio_muted_text" yalign 0.5
                null width 1 xfill True
                textbutton "Close" action Function(live_studio.close_all_popups) style "live_studio_compact_button"
            add Solid("#24303e", xsize=590, ysize=1)
            text "Containers" style "live_studio_section_label"
            hbox:
                spacing 6
                textbutton "+ Scene" action Function(live_studio.create_scene, "New Scene", "scene", None) style "live_studio_button"
                textbutton "+ UI Screen" action Function(live_studio.create_editor_ui_screen, None) style "live_studio_button"
                textbutton "+ Say UI" action Function(live_studio.create_say_ui_template, None) style "live_studio_button"
                textbutton "+ Choice UI" action Function(live_studio.create_choice_ui_template, None) style "live_studio_button"
            text "Objects" style "live_studio_section_label"
            hbox:
                spacing 6
                textbutton "+ Image" action [Function(live_studio.set_bottom_tab, "Assets"), Function(live_studio.close_all_popups)] style "live_studio_button"
                textbutton "+ Text" action Function(live_studio.add_scene_text, None) style "live_studio_button"
                textbutton "+ Button" action Function(live_studio.add_scene_button, None) style "live_studio_button"
                textbutton "+ Dialogue" action Function(live_studio.ensure_dialogue_controller, None) style "live_studio_button"
            text "Frames and Flow" style "live_studio_section_label"
            hbox:
                spacing 6
                textbutton "+ Inherited Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_button"
                textbutton "+ Blank Frame" action Function(live_studio.add_frame, "blank", "Blank Frame") style "live_studio_button"
                textbutton "+ Branch" action Function(live_studio.add_branch_frame, "Branch") style "live_studio_button"
                textbutton "Delete Current Frame" action Function(live_studio.remove_current_frame) sensitive len(live_studio.frame_order()) > 1 style "live_studio_button"
            null height 1 yfill True
            text "Create actions remain available here so the main canvas stays uncluttered." style "live_studio_muted_text"

screen live_studio_tools_panel():
    $ selected, parent_id, kind = live_studio.selected_item()
    viewport:
        mousewheel True
        draggable True
        scrollbars "vertical"
        yfill True
        xfill True
        vbox:
            spacing 7
            xfill True
            hbox:
                text "Tools" style "live_studio_accent_text"
                null width 1 xfill True
                textbutton "Undo" action Function(live_studio.undo) sensitive bool(live_studio.history) style "live_studio_compact_button"
                textbutton "Redo" action Function(live_studio.redo) sensitive bool(live_studio.redo_stack) style "live_studio_compact_button"

            text "Transform" style "live_studio_section_label"
            grid 4 1:
                spacing 5
                xfill True
                for value, label in (("select", "Select"), ("move", "Move"), ("resize", "Scale"), ("rotate", "Rotate")):
                    textbutton label action Function(live_studio.set_tool_mode, value) selected live_studio.tool_mode == value style "live_studio_tool_button"

            text "Edit" style "live_studio_section_label"
            grid 4 1:
                spacing 5
                xfill True
                textbutton "Copy" action Function(live_studio.copy_selected) sensitive selected is not None style "live_studio_tool_button"
                textbutton "Paste" action Function(live_studio.paste_copied) sensitive live_studio.runtime.get("clipboard") is not None style "live_studio_tool_button"
                textbutton "Duplicate" action Function(live_studio.duplicate_selected) sensitive selected is not None style "live_studio_tool_button"
                textbutton "Delete" action Function(live_studio.remove_selected_item) sensitive selected is not None style "live_studio_tool_button"

            text "Arrange" style "live_studio_section_label"
            grid 2 2:
                spacing 5
                xfill True
                textbutton "Bring Front" action Function(live_studio.reorder_selected, "front") sensitive selected is not None style "live_studio_tool_button"
                textbutton "Send Back" action Function(live_studio.reorder_selected, "back") sensitive selected is not None style "live_studio_tool_button"
                textbutton "Bring Forward" action Function(live_studio.reorder_selected, "forward") sensitive selected is not None style "live_studio_tool_button"
                textbutton "Send Backward" action Function(live_studio.reorder_selected, "backward") sensitive selected is not None style "live_studio_tool_button"

            text "Other" style "live_studio_section_label"
            grid 3 1:
                spacing 5
                xfill True
                textbutton "Lock" action Function(live_studio.set_item_value, selected.get("id") if selected else None, "locked", True, "Lock item") sensitive selected is not None and not selected.get("locked", False) style "live_studio_tool_button"
                textbutton "Unlock" action Function(live_studio.set_item_value, selected.get("id") if selected else None, "locked", False, "Unlock item") sensitive selected is not None and selected.get("locked", False) style "live_studio_tool_button"
                textbutton "+ Add" action Function(live_studio.toggle_create_popup) style "live_studio_tool_button"
