# Ren'Py Live Studio interface.
# Layout: slim project bar, Inspector + Scene Tree on the left, canvas in the
# center, Layers/Structure/History on the right, and Assets/Dialogue + compact
# tools along the bottom. This intentionally follows the original editor.

style live_studio_text is default:
    color "#d9e4ff"
    size 15

style live_studio_muted_text is live_studio_text:
    color "#8494bb"
    size 13

style live_studio_heading is live_studio_text:
    color "#f4f7ff"
    size 17
    bold True

style live_studio_small is live_studio_text:
    size 12

style live_studio_panel is frame:
    background Solid("#0e1625")
    padding (9, 7)

style live_studio_panel_alt is frame:
    background Solid("#111b2e")
    padding (8, 6)

style live_studio_panel_header is frame:
    background Solid("#0f1828")
    padding (10, 6)

style live_studio_panel_header_text is live_studio_text:
    color "#7598ff"
    size 14
    bold True

style live_studio_button is button:
    background Solid("#18243b")
    hover_background Solid("#233452")
    selected_background Solid("#5635c7")
    insensitive_background Solid("#111827")
    padding (10, 5)

style live_studio_button_text is live_studio_text:
    color "#cbd8f7"
    hover_color "#ffffff"
    selected_color "#ffffff"
    insensitive_color "#56637e"
    size 13

style live_studio_compact_button is live_studio_button:
    padding (7, 4)

style live_studio_compact_button_text is live_studio_button_text:
    size 12

style live_studio_icon_button is live_studio_button:
    padding (8, 4)

style live_studio_icon_button_text is live_studio_button_text:
    size 13

style live_studio_tab is button:
    background None
    hover_background Solid("#ffffff12")
    selected_background Solid("#5b3ef7")
    padding (9, 5)

style live_studio_tab_text is live_studio_button_text:
    color "#788ab2"
    selected_color "#ffffff"
    size 13

style live_studio_tree_button is button:
    background None
    hover_background Solid("#ffffff0d")
    selected_background Solid("#4d2fa3")
    padding (6, 3)
    xfill True

style live_studio_tree_button_text is live_studio_text:
    color "#aebbd7"
    selected_color "#ffffff"
    size 12
    text_align 0.0

style live_studio_input is input:
    color "#f7f9ff"
    size 13

style live_studio_input_frame is frame:
    background Solid("#0a1120")
    padding (7, 4)
    xfill True

style live_studio_property_group is button:
    background None
    hover_background Solid("#ffffff0b")
    padding (4, 4)
    xfill True

style live_studio_property_group_text is live_studio_text:
    color "#d5def4"
    size 12

style live_studio_asset_tile is button:
    background Solid("#202938")
    hover_background Solid("#2c3850")
    padding (5, 5)

style live_studio_asset_tile_text is live_studio_small:
    color "#d7e1f7"

style live_studio_asset_thumb is frame:
    background Solid("#131b28")
    padding (4, 4)

style live_studio_accent_text is live_studio_text:
    color "#9864ff"
    bold True

# All editor viewports inherit these through the root style_prefix. The thumb is
# deliberately narrow so scrolling never steals meaningful inspector space.
style live_studio_viewport is viewport:
    xfill True
    yfill True

style live_studio_vscrollbar is vscrollbar:
    xsize live_studio.SCROLLBAR_WIDTH
    base_bar Solid("#111a2a")
    thumb Solid("#7550e8")
    bar_resizing False

style live_studio_scrollbar is scrollbar:
    ysize live_studio.SCROLLBAR_WIDTH
    base_bar Solid("#111a2a")
    thumb Solid("#7550e8")
    bar_resizing False

style live_studio_layer_group is button:
    background Solid("#111c30")
    hover_background Solid("#172641")
    selected_background Solid("#332265")
    padding (6, 5)
    xfill True

style live_studio_layer_group_text is live_studio_text:
    size 12
    bold True
    color "#dfe8ff"

style live_studio_layer_row is button:
    background None
    hover_background Solid("#ffffff0b")
    selected_background Solid("#4e2bb0")
    padding (4, 3)
    xfill True

style live_studio_layer_row_text is live_studio_text:
    size 11
    color "#b9c6df"
    selected_color "#ffffff"

style live_studio_folder_row is button:
    background None
    hover_background Solid("#ffffff0b")
    selected_background Solid("#233a64")
    padding (3, 2)
    xfill True

style live_studio_folder_row_text is live_studio_text:
    size 11
    color "#aebbd7"
    selected_color "#ffffff"

style live_studio_property_label is live_studio_muted_text:
    size 12
    yalign 0.5

style live_studio_property_input_frame is frame:
    background Solid("#09111f")
    padding (5, 2)
    xfill True
    yminimum 27

style live_studio_property_input is live_studio_input:
    size 12

screen live_studio_editor():
    modal True
    style_prefix "live_studio"
    zorder 9999

    key "game_menu" action [Function(live_studio.flush_pending_input_edits), Return()]
    key "K_ESCAPE" action [Function(live_studio.flush_pending_input_edits), Return()]
    key "K_DELETE" action Function(live_studio.remove_selected_item)
    key "ctrl_K_z" action Function(live_studio.undo)
    key "ctrl_K_y" action Function(live_studio.redo)
    key "ctrl_K_c" action Function(live_studio.copy_selected)
    key "ctrl_K_v" action Function(live_studio.paste_copied)
    key "K_q" action Function(live_studio.set_tool_mode, "select")
    key "K_g" action Function(live_studio.set_tool_mode, "move")
    key "K_s" action Function(live_studio.set_tool_mode, "resize")
    key "K_r" action Function(live_studio.set_tool_mode, "rotate")

    # Commits one field-level undo entry after typing pauses. The Input itself
    # stays responsive and does not restart the full editor on every character.
    timer 0.80 repeat True action Function(live_studio.flush_pending_input_edits_if_idle, 0.70)

    $ sw = config.screen_width
    $ sh = config.screen_height
    $ left_width = int(min(live_studio.LEFT_PANEL_MAX, max(live_studio.LEFT_PANEL_MIN, sw * live_studio.LEFT_PANEL_RATIO)))
    $ right_width = int(min(live_studio.RIGHT_PANEL_MAX, max(live_studio.RIGHT_PANEL_MIN, sw * live_studio.RIGHT_PANEL_RATIO)))
    $ bottom_tools_width = int(min(live_studio.BOTTOM_TOOLS_MAX, max(live_studio.BOTTOM_TOOLS_MIN, sw * live_studio.BOTTOM_TOOLS_RATIO)))
    $ top_height = live_studio.TOP_BAR_HEIGHT
    $ bottom_height = int(min(live_studio.BOTTOM_PANEL_MAX, max(live_studio.BOTTOM_PANEL_MIN, sh * live_studio.BOTTOM_PANEL_RATIO)))
    $ nav_height = live_studio.FRAME_NAV_HEIGHT
    $ upper_height = sh - top_height - bottom_height
    $ canvas_height = max(180, upper_height - nav_height)
    $ canvas_width = max(420, sw - left_width - right_width)
    $ bottom_workspace_width = max(420, sw - left_width - bottom_tools_width)

    add Solid("#080e18")

    use live_studio_top_bar(top_height)

    frame:
        style "live_studio_panel"
        xpos 0
        ypos top_height
        xsize left_width
        ysize sh - top_height
        padding (0, 0)
        vbox:
            spacing 0
            xfill True
            yfill True
            frame:
                style "live_studio_panel_alt"
                padding (0, 0)
                xfill True
                ysize int((sh - top_height) * 0.52)
                use live_studio_inspector
            add Solid("#26334d", xsize=left_width, ysize=1)
            frame:
                style "live_studio_panel_alt"
                padding (0, 0)
                xfill True
                yfill True
                use live_studio_hierarchy

    frame:
        background Solid(live_studio.CANVAS_BACKGROUND)
        padding (0, 0)
        xpos left_width
        ypos top_height
        xsize canvas_width
        ysize canvas_height
        add live_studio.canvas_displayable()

    frame:
        background Solid("#0d1524")
        padding (8, 4)
        xpos left_width
        ypos top_height + canvas_height
        xsize canvas_width
        ysize nav_height
        use live_studio_frame_nav

    frame:
        style "live_studio_panel"
        padding (0, 0)
        xpos sw - right_width
        ypos top_height
        xsize right_width
        ysize upper_height
        use live_studio_right_panel

    frame:
        background Solid("#0e1625")
        padding (9, 7)
        xpos left_width
        ypos sh - bottom_height
        xsize bottom_workspace_width
        ysize bottom_height
        use live_studio_bottom_workspace

    frame:
        background Solid("#0e1625")
        padding (9, 7)
        xpos sw - bottom_tools_width
        ypos sh - bottom_height
        xsize bottom_tools_width
        ysize bottom_height
        use live_studio_tools_panel

screen live_studio_top_bar(top_height):
    frame:
        background Solid("#0d1423")
        padding (12, 4)
        xpos 0
        ypos 0
        xfill True
        ysize top_height
        hbox:
            spacing 7
            yalign 0.5
            xfill True

            text "Ren'Py live studio" style "live_studio_heading" yalign 0.5
            null width 16

            text "Zoom" style "live_studio_muted_text" yalign 0.5
            textbutton "{:.0f}% ▾".format(live_studio.canvas_zoom * 100) action Function(live_studio.reset_canvas_zoom) style "live_studio_compact_button"
            textbutton "−" action Function(live_studio.zoom_canvas, -live_studio.CANVAS_ZOOM_STEP) sensitive live_studio.canvas_zoom > live_studio.CANVAS_ZOOM_MIN style "live_studio_icon_button"
            textbutton "+" action Function(live_studio.zoom_canvas, live_studio.CANVAS_ZOOM_STEP) sensitive live_studio.canvas_zoom < live_studio.CANVAS_ZOOM_MAX style "live_studio_icon_button"

            null width 18
            text "Snap" style "live_studio_muted_text" yalign 0.5
            textbutton ("On" if live_studio.project_setting("snap_enabled", True) else "Off") action Function(live_studio.toggle_project_setting, "snap_enabled") selected live_studio.project_setting("snap_enabled", True) style "live_studio_compact_button"
            textbutton "{}px ▾".format(live_studio.project_setting("grid_size", live_studio.GRID_SIZE)) action Function(live_studio.set_project_setting, "grid_size", 8 if live_studio.project_setting("grid_size", 16) == 16 else (32 if live_studio.project_setting("grid_size", 16) == 8 else 16)) style "live_studio_compact_button"

            null width 1 xfill True

            textbutton "💾 Save" action Function(live_studio.save_project) style "live_studio_button"
            textbutton "▱ Project" action Function(live_studio.set_right_panel_tab, "Structure") selected live_studio.right_panel_tab == "Structure" style "live_studio_button"
            textbutton "▶ Preview" action Function(live_studio.set_preview_mode, "layout" if live_studio.preview_mode == "capture" else "capture") selected live_studio.preview_mode == "layout" style "live_studio_button"
            textbutton "</> Extract Script" action Function(live_studio.set_bottom_tab, "Export") style "live_studio_button"
            textbutton "⚙ Settings" action Function(live_studio.set_right_panel_tab, "Debug") selected live_studio.right_panel_tab == "Debug" style "live_studio_button"
            textbutton "Close" action [Function(live_studio.flush_pending_input_edits), Return()] style "live_studio_button"

screen live_studio_frame_nav():
    hbox:
        spacing 8
        xfill True
        yalign 0.5
        textbutton "+ Insert" action Function(live_studio.add_frame, "inherit", None) style "live_studio_compact_button"
        textbutton "Empty" action Function(live_studio.add_frame, "blank", "Blank Frame") style "live_studio_compact_button"
        null width 1 xfill True
        textbutton "← Prev Frame" action Function(live_studio.previous_frame) sensitive live_studio.frame_index() > 0 style "live_studio_compact_button"
        text "Frame {}/{}".format(live_studio.frame_index() + 1, max(1, len(live_studio.frame_order()))) style "live_studio_text" yalign 0.5
        textbutton "Next Frame →" action Function(live_studio.next_frame) sensitive live_studio.frame_index() + 1 < len(live_studio.frame_order()) style "live_studio_compact_button"
        null width 1 xfill True
        textbutton "Duplicate" action Function(live_studio.duplicate_frame_detached) style "live_studio_compact_button"

screen live_studio_text_field(label, item_id, path, value, label_width=102):
    hbox:
        spacing 6
        xfill True
        yminimum 29
        text label style "live_studio_property_label" xsize label_width
        frame:
            style "live_studio_property_input_frame"
            xfill True
            input value live_studio.editor_input_value("property", item_id, path) style "live_studio_property_input"
        if live_studio.has_local_override(item_id, path):
            textbutton "↶" action Function(live_studio.clear_item_override, item_id, path) tooltip "Revert to inherited value" style "live_studio_icon_button"

screen live_studio_axis_field(axis, item_id, path, value):
    hbox:
        spacing 3
        xfill True
        text axis style "live_studio_muted_text" xsize 12 yalign 0.5
        frame:
            style "live_studio_property_input_frame"
            xfill True
            input value live_studio.editor_input_value("property", item_id, path) style "live_studio_property_input"
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
                        textbutton frame_name action Function(live_studio.set_button_frame_target, node.get("id"), frame_id) selected (action or {}).get("target_frame_id") == frame_id style "live_studio_tree_button"
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
                        text "Parent: {}".format((live_studio.frame_by_id(frame.get("parent_id")) or {}).get("name", "None")) style "live_studio_muted_text"
                        text live_studio.flow_summary() style "live_studio_muted_text"
                        if frame.get("source_ref"):
                            text "{}:{}".format(frame.get("source_ref", {}).get("filename") or "runtime", frame.get("source_ref", {}).get("line") or "?") style "live_studio_muted_text"
                else:
                    hbox:
                        spacing 5
                        text selected.get("name", kind) style "live_studio_heading"
                        text "({})".format(kind.replace("_", " ")) style "live_studio_muted_text" yalign 0.5
                    if selected.get("editability"):
                        text "Editability: {}".format(selected.get("editability")) style "live_studio_muted_text"

                    if kind == "dialogue_controller":
                        use live_studio_text_field("Say UI", selected.get("id"), "say_screen", selected.get("say_screen", "say"))
                        use live_studio_text_field("Choice UI", selected.get("id"), "choice_screen", selected.get("choice_screen", "choice"))
                        textbutton "Open Dialogue Workspace" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_button"
                        text "Full scene source" style "live_studio_small"
                        text live_studio.dialogue_source(selected) style "live_studio_small"
                    elif kind in ("dialogue_event", "dialogue_choice"):
                        text "Edit this entry in the Dialogue workspace." style "live_studio_muted_text"
                        textbutton "Open Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_button"
                    elif kind == "ui_screen":
                        use live_studio_text_field("Name", selected.get("id"), "name", selected.get("name", "screen"))
                        use live_studio_text_field("Role", selected.get("id"), "role", selected.get("role", "screen"))
                        use live_studio_text_field("Layer", selected.get("id"), "layer", selected.get("layer", "screens"))
                        if not selected.get("managed"):
                            text "Captured screen · inspect first, convert a copy to edit/export." style "live_studio_muted_text"
                            textbutton "Convert to Managed Copy" action Function(live_studio.convert_screen_to_managed, selected.get("id")) style "live_studio_button"
                        else:
                            text "Managed screen" style "live_studio_muted_text"
                    elif kind == "scene":
                        use live_studio_text_field("Scene Name", selected.get("id"), "name", selected.get("name", "Scene"))
                        text "Layers: {}".format(", ".join(selected.get("source_layers", [])) or "None") style "live_studio_muted_text"
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
                                                            text str(value if value is not None else "") style "live_studio_property_input"
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
                                text "Saved as value: {}".format(text_binding.get("source_expression") or text_binding.get("expression") or "Runtime source not recoverable") style "live_studio_muted_text"
                        if kind == "ui_node" and not selected.get("widget_id"):
                            text "This runtime widget has no stable Ren'Py id. Its value can be inspected, but visual movement requires converting the parent screen to a managed copy." style "live_studio_muted_text"
                            $ selected_screen = live_studio.screen_for_node(live_studio.resolve_frame(), selected.get("id"))
                            if selected_screen and not selected_screen.get("managed"):
                                textbutton "Make Parent Screen Editable" action Function(live_studio.convert_screen_to_managed, selected_screen.get("id")) style "live_studio_button"
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
                            textbutton ("⌄" if open_value else "›") action Function(live_studio.toggle_tree_item, item.get("id"), row_kind in ("scene", "ui_screen")) style "live_studio_icon_button"
                        else:
                            null width 28
                        $ row_icon = "◆" if row_kind == "dialogue_controller" else ("◇" if item.get("type") == "image" else "")
                        textbutton "{} {}".format(row_icon, item.get("name", item.get("type", row_kind))) action Function(live_studio.select_item, item.get("id"), row_kind) selected live_studio.selected_item_id == item.get("id") style "live_studio_tree_button"

screen live_studio_right_panel():
    vbox:
        spacing 0
        xfill True
        yfill True
        frame:
            style "live_studio_panel_header"
            xfill True
            hbox:
                spacing 5
                for tab_name in ("Layers", "Structure", "History", "Debug"):
                    textbutton tab_name action Function(live_studio.set_right_panel_tab, tab_name) selected live_studio.right_panel_tab == tab_name style "live_studio_tab"
        if live_studio.right_panel_tab == "Structure":
            use live_studio_structure_panel
        elif live_studio.right_panel_tab == "History":
            use live_studio_history_panel
        elif live_studio.right_panel_tab == "Debug":
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
            background Solid("#0c1525")
            padding (7, 5)
            xfill True
            hbox:
                spacing 4
                textbutton "Scene Layers" action Function(live_studio.set_layer_panel_mode, "Scene") selected panel_mode == "Scene" style "live_studio_tab"
                textbutton "UI Layers" action Function(live_studio.set_layer_panel_mode, "UI") selected panel_mode == "UI" style "live_studio_tab"
                null width 1 xfill True
                text "Back → Front" style "live_studio_muted_text" yalign 0.5
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            xfill True
            vbox:
                spacing 1
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
                                null width 25
                            button:
                                style "live_studio_layer_group"
                                selected is_selected
                                action Function(live_studio.select_layer_item, item.get("id"), row_kind)
                                xfill True
                                hbox:
                                    spacing 5
                                    if row_kind == "ui_screen":
                                        frame:
                                            background Solid("#0a1220")
                                            padding (2, 2)
                                            xsize live_studio.LAYER_THUMB_WIDTH + 4
                                            ysize live_studio.LAYER_THUMB_HEIGHT + 4
                                            add live_studio.layer_thumbnail(item, row_kind, live_studio.LAYER_THUMB_WIDTH, live_studio.LAYER_THUMB_HEIGHT)
                                    else:
                                        fixed:
                                            xsize live_studio.LAYER_THUMB_WIDTH + 4
                                            ysize live_studio.LAYER_THUMB_HEIGHT + 4
                                            add Solid("#0a1220")
                                            text ("DIALOGUE" if item.get("type") == "dialogue" else "SCENE") style "live_studio_muted_text" xalign 0.5 yalign 0.5
                                    vbox:
                                        spacing 1
                                        yalign 0.5
                                        text item.get("name", "Layer") style "live_studio_layer_group_text"
                                        text (item.get("role", "UI screen") if row_kind == "ui_screen" else ", ".join(item.get("source_layers", [])) or "Scene container") style "live_studio_muted_text"
                                    null width 1 xfill True
                            textbutton ("●" if item.get("visible", True) else "○") action Function(live_studio.toggle_item_value, item.get("id"), "visible") tooltip "Show or hide" style "live_studio_icon_button"
                    else:
                        hbox:
                            spacing 3
                            xfill True
                            null width max(0, depth - 1) * 13
                            if depth > 1:
                                fixed:
                                    xsize 8
                                    ysize live_studio.LAYER_THUMB_HEIGHT + 8
                                    add Solid("#2c3a54", xsize=1, ysize=live_studio.LAYER_THUMB_HEIGHT + 8) xpos 3
                                    add Solid("#2c3a54") xsize 6 ysize 1 xpos 3 ypos 20
                            if row.get("has_children"):
                                textbutton ("⌄" if row.get("open") else "›") action Function(live_studio.toggle_tree_item, row.get("open_key"), False) style "live_studio_icon_button"
                            else:
                                null width 25
                            button:
                                style "live_studio_layer_row"
                                selected is_selected
                                action Function(live_studio.select_layer_item, item.get("id"), row_kind)
                                xfill True
                                hbox:
                                    spacing 6
                                    frame:
                                        background Solid("#0a1220")
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
                                        text item.get("name", item.get("type", "Layer")) style "live_studio_layer_row_text"
                                        if item.get("widget_id"):
                                            text "id: {}".format(item.get("widget_id")) style "live_studio_muted_text"
                                        elif row_kind == "ui_node":
                                            text item.get("type", "UI") style "live_studio_muted_text"
                                    null width 1 xfill True
                            textbutton ("●" if item.get("visible", True) else "○") action Function(live_studio.toggle_item_value, item.get("id"), "visible") tooltip "Show or hide" style "live_studio_icon_button"
                            textbutton ("L" if item.get("locked", False) else "·") action Function(live_studio.toggle_item_value, item.get("id"), "locked") tooltip "Lock editing" style "live_studio_icon_button"
                if len(layer_rows) > 180:
                    text "{} additional entries hidden for performance. Collapse or simplify the captured screen.".format(len(layer_rows) - 180) style "live_studio_muted_text"

screen live_studio_structure_panel():
    $ controller = live_studio.selected_dialogue_controller()
    vbox:
        spacing 8
        xfill True
        yfill True
        text "Frame Chain" style "live_studio_small"
        viewport:
            mousewheel True
            draggable True
            ymaximum 180
            vbox:
                spacing 2
                xfill True
                for frame_id in live_studio.frame_order():
                    $ frame = live_studio.frame_by_id(frame_id)
                    textbutton "{} {}".format("▶" if frame_id == live_studio.current_frame_id else "•", frame.get("name", "Frame")) action Function(live_studio.select_frame, frame_id) selected frame_id == live_studio.current_frame_id style "live_studio_tree_button"
        text "Dialogue Outline" style "live_studio_small"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            ymaximum 235
            vbox:
                spacing 2
                xfill True
                if controller is None:
                    text "No Dialogue object in this frame." style "live_studio_muted_text"
                else:
                    for index, event in enumerate(controller.get("events", [])):
                        $ label = event.get("text") or event.get("script") or event.get("target") or event.get("type", "Event")
                        textbutton "{}  {}".format(index + 1, label[:46]) action [Function(live_studio.select_dialogue_event, event.get("id")), Function(live_studio.set_bottom_tab, "Dialogue")] selected event.get("id") == controller.get("selected_event_id") style "live_studio_tree_button"
                        if event.get("type") == "choice":
                            for choice in event.get("choices", []):
                                text "    └ {}".format(choice.get("caption", "Choice")) style "live_studio_muted_text"

        hbox:
            text "Next Source State" style "live_studio_small"
            null width 1 xfill True
            textbutton "Refresh" action Function(live_studio.refresh_source_flow_candidates) style "live_studio_compact_button"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 2
                xfill True
                $ source_candidates = live_studio.source_flow_candidates()
                if not source_candidates:
                    text "No static next interaction found." style "live_studio_muted_text"
                for source_index, candidate in enumerate(source_candidates[:12]):
                    textbutton candidate.get("title", "Next state") action Function(live_studio.import_source_candidate, source_index) style "live_studio_tree_button"

screen live_studio_history_panel():
    vbox:
        spacing 6
        xfill True
        yfill True
        hbox:
            text "History" style "live_studio_small"
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
                for entry in reversed(live_studio.history[-60:]):
                    text "• {}".format(entry.get("label", entry.get("type", "Edit"))) style "live_studio_muted_text"

screen live_studio_debug_panel():
    vbox:
        spacing 7
        xfill True
        yfill True
        text "Canvas" style "live_studio_small"
        hbox:
            spacing 4
            textbutton "Exact" action Function(live_studio.set_preview_mode, "capture") selected live_studio.preview_mode == "capture" style "live_studio_compact_button"
            textbutton "Editable" action Function(live_studio.set_preview_mode, "layout") selected live_studio.preview_mode == "layout" style "live_studio_compact_button"
        hbox:
            spacing 4
            textbutton ("Guides On" if live_studio.project_setting("guides_enabled", True) else "Guides Off") action Function(live_studio.toggle_project_setting, "guides_enabled") selected live_studio.project_setting("guides_enabled", True) style "live_studio_compact_button"
            textbutton ("Grid On" if live_studio.project_setting("grid_enabled", False) else "Grid Off") action Function(live_studio.toggle_project_setting, "grid_enabled") selected live_studio.project_setting("grid_enabled", False) style "live_studio_compact_button"
        textbutton ("All Bounds On" if live_studio.project_setting("show_all_bounds", False) else "All Bounds Off") action Function(live_studio.toggle_project_setting, "show_all_bounds") selected live_studio.project_setting("show_all_bounds", False) style "live_studio_compact_button"
        text "Runtime Capture" style "live_studio_small"
        text "The game remains intact behind the editor." style "live_studio_muted_text"
        textbutton "Fresh Capture" action Confirm("Discard this frame's local edits and recapture the running game?", Function(live_studio.refresh_runtime_capture)) style "live_studio_button"
        hbox:
            text "Diagnostics" style "live_studio_small"
            null width 1 xfill True
            textbutton "Clear" action Function(live_studio.clear_diagnostics) style "live_studio_compact_button"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 4
                xfill True
                if not live_studio.runtime.get("diagnostics"):
                    text "No diagnostics." style "live_studio_muted_text"
                for entry in live_studio.runtime.get("diagnostics", [])[-30:]:
                    text "{} · {}".format(entry.get("level", "info").upper(), entry.get("message", "")) style "live_studio_muted_text"

screen live_studio_bottom_workspace():
    vbox:
        spacing 6
        xfill True
        yfill True
        hbox:
            spacing 5
            $ workspace_title = "Dialogue" if live_studio.bottom_tab == "Dialogue" else ("Script" if live_studio.bottom_tab == "Export" else "Assets")
            text workspace_title style "live_studio_heading"
            textbutton "Assets" action Function(live_studio.set_bottom_tab, "Assets") selected live_studio.bottom_tab == "Assets" style "live_studio_tab"
            textbutton "Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") selected live_studio.bottom_tab == "Dialogue" style "live_studio_tab"
            textbutton "Script" action Function(live_studio.set_bottom_tab, "Export") selected live_studio.bottom_tab == "Export" style "live_studio_tab"
            null width 1 xfill True
            text live_studio.flow_summary() style "live_studio_muted_text" yalign 0.5
        if live_studio.bottom_tab == "Dialogue":
            use live_studio_dialogue_workspace
        elif live_studio.bottom_tab == "Export":
            use live_studio_export_workspace
        else:
            use live_studio_assets_workspace

screen live_studio_assets_workspace():
    vbox:
        spacing 5
        xfill True
        yfill True
        hbox:
            spacing 4
            for category_value, category_label in live_studio.ASSET_CATEGORIES:
                textbutton category_label action Function(live_studio.set_asset_category, category_value) selected live_studio.asset_category == category_value style "live_studio_tab"
            null width 8
            textbutton live_studio.asset_sort_mode + " ▾" action Function(live_studio.set_asset_sort_mode, "Name Z-A" if live_studio.asset_sort_mode == "Name A-Z" else ("Recent" if live_studio.asset_sort_mode == "Name Z-A" else ("Oldest" if live_studio.asset_sort_mode == "Recent" else "Name A-Z"))) style "live_studio_compact_button"
            null width 1 xfill True
            frame:
                style "live_studio_property_input_frame"
                xsize 225
                hbox:
                    spacing 4
                    text "⌕" style "live_studio_muted_text" yalign 0.5
                    input value live_studio.asset_filter_input style "live_studio_property_input"
            textbutton "Search" action Function(live_studio.apply_asset_filter) style "live_studio_compact_button"
            if live_studio.asset_filter:
                textbutton "Clear" action Function(live_studio.clear_asset_filter) style "live_studio_compact_button"
            textbutton "Refresh" action Function(live_studio.refresh_assets) style "live_studio_compact_button"
        hbox:
            spacing 6
            xfill True
            yfill True
            frame:
                background Solid("#0a1220")
                padding (4, 4)
                xsize live_studio.ASSET_TREE_WIDTH
                yfill True
                vbox:
                    spacing 3
                    xfill True
                    hbox:
                        text "Project Assets" style "live_studio_small"
                        null width 1 xfill True
                        textbutton "⌂" action Function(live_studio.open_asset_folder, ()) style "live_studio_icon_button"
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
                                        null width 25
                                    textbutton ("▣ " if not path else "▱ ") + row.get("name", "Assets") action Function(live_studio.open_asset_folder, path) selected row.get("selected", False) style "live_studio_folder_row"
            frame:
                background Solid("#26334d")
                padding (0, 0)
                xsize 1
                yfill True
            vbox:
                spacing 5
                xfill True
                yfill True
                hbox:
                    spacing 4
                    textbutton "↑" action Function(live_studio.asset_go_up) sensitive bool(live_studio.asset_current_path) style "live_studio_icon_button"
                    text live_studio.asset_breadcrumb() style "live_studio_muted_text" yalign 0.5
                    null width 1 xfill True
                    textbutton "←" action Function(live_studio.previous_asset_page) sensitive live_studio.asset_page > 0 style "live_studio_icon_button"
                    text live_studio.asset_page_label() style "live_studio_muted_text" yalign 0.5
                    textbutton "→" action Function(live_studio.next_asset_page) sensitive live_studio.asset_page + 1 < live_studio.asset_page_count() style "live_studio_icon_button"
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    xfill True
                    $ asset_cols = max(3, int((config.screen_width - live_studio.ASSET_TREE_WIDTH - 710) / 145))
                    vpgrid:
                        cols asset_cols
                        spacing 7
                        xfill True
                        for folder in live_studio.asset_folder_entries():
                            button:
                                style "live_studio_asset_tile"
                                action Function(live_studio.open_asset_folder, folder.get("path", ()))
                                xsize 132
                                ysize 102
                                vbox:
                                    spacing 4
                                    xalign 0.5
                                    yalign 0.5
                                    text "▰" style "live_studio_heading" xalign 0.5
                                    text folder.get("name", "Folder") style "live_studio_asset_tile_text" xalign 0.5 text_align 0.5
                        for asset in live_studio.assets():
                            if asset.get("kind") == "image":
                                button:
                                    style "live_studio_asset_tile"
                                    action Function(live_studio.add_asset_to_current_context, asset.get("name"))
                                    xsize 132
                                    ysize 102
                                    vbox:
                                        spacing 3
                                        xalign 0.5
                                        frame:
                                            style "live_studio_asset_thumb"
                                            xsize 118
                                            ysize 72
                                            add live_studio.asset_thumbnail(asset.get("name"), 110, 64) xalign 0.5 yalign 0.5
                                        text live_studio.asset_short_name(asset) style "live_studio_asset_tile_text" xalign 0.5 text_align 0.5
                            else:
                                button:
                                    style "live_studio_asset_tile"
                                    action NullAction()
                                    xsize 132
                                    ysize 102
                                    vbox:
                                        spacing 3
                                        xalign 0.5
                                        yalign 0.5
                                        text "♪" style "live_studio_heading" xalign 0.5
                                        text live_studio.asset_short_name(asset) style "live_studio_asset_tile_text" xalign 0.5 text_align 0.5
                                        hbox:
                                            spacing 2
                                            xalign 0.5
                                            textbutton "Music" action Function(live_studio.add_audio_event, asset.get("name"), "music") style "live_studio_compact_button"
                                            textbutton "SFX" action Function(live_studio.add_audio_event, asset.get("name"), "sound") style "live_studio_compact_button"

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
                                    textbutton "{} {:02d}  {}".format(marker, index + 1, preview[:42]) action Function(live_studio.select_dialogue_event, item.get("id")) selected event and event.get("id") == item.get("id") style "live_studio_tree_button"
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
                                                            textbutton frame_name action Function(live_studio.set_item_value, choice.get("id"), "target_frame_id", frame_id, "Set choice frame") selected choice.get("target_frame_id") == frame_id style "live_studio_compact_button"
                                                textbutton "Remove Choice" action Function(live_studio.remove_choice_option, choice.get("id")) style "live_studio_compact_button"
                                if event.get("type") not in ("choice", "return"):
                                    use live_studio_text_field("Condition", event.get("id"), "condition", event.get("condition", ""))

screen live_studio_export_workspace():
    default export_section = "story"
    vbox:
        spacing 5
        xfill True
        yfill True
        hbox:
            spacing 5
            textbutton "story.rpy" action SetScreenVariable("export_section", "story") selected export_section == "story" style "live_studio_tab"
            textbutton "screens.rpy" action SetScreenVariable("export_section", "screens") selected export_section == "screens" style "live_studio_tab"
            textbutton "helpers.rpy" action SetScreenVariable("export_section", "helpers") selected export_section == "helpers" style "live_studio_tab"
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
                text live_studio.export_preview(export_section) style "live_studio_small"

screen live_studio_tools_panel():
    $ selected, parent_id, kind = live_studio.selected_item()
    vbox:
        spacing 6
        xfill True
        yfill True
        hbox:
            text "Tools" style "live_studio_accent_text"
            null width 1 xfill True
            textbutton "Undo" action Function(live_studio.undo) sensitive bool(live_studio.history) style "live_studio_compact_button"
            textbutton "Redo" action Function(live_studio.redo) sensitive bool(live_studio.redo_stack) style "live_studio_compact_button"

        text "Edit" style "live_studio_muted_text"
        hbox:
            spacing 5
            for value, label in (("select", "▣ Select"), ("move", "✣ Move"), ("resize", "◱ Scale"), ("rotate", "⟳ Rotate")):
                textbutton label action Function(live_studio.set_tool_mode, value) selected live_studio.tool_mode == value style "live_studio_compact_button"

        text "Edit Objects" style "live_studio_muted_text"
        hbox:
            spacing 5
            textbutton "Copy" action Function(live_studio.copy_selected) sensitive selected is not None style "live_studio_compact_button"
            textbutton "Paste" action Function(live_studio.paste_copied) sensitive live_studio.runtime.get("clipboard") is not None style "live_studio_compact_button"
            textbutton "Duplicate" action Function(live_studio.duplicate_selected) sensitive selected is not None style "live_studio_compact_button"
            textbutton "Delete" action Function(live_studio.remove_selected_item) sensitive selected is not None style "live_studio_compact_button"

        text "Arrange" style "live_studio_muted_text"
        hbox:
            spacing 5
            textbutton "Bring Front" action Function(live_studio.reorder_selected, "front") sensitive selected is not None style "live_studio_compact_button"
            textbutton "Send Back" action Function(live_studio.reorder_selected, "back") sensitive selected is not None style "live_studio_compact_button"
            textbutton "Forward" action Function(live_studio.reorder_selected, "forward") sensitive selected is not None style "live_studio_compact_button"
            textbutton "Backward" action Function(live_studio.reorder_selected, "backward") sensitive selected is not None style "live_studio_compact_button"

        text "Create" style "live_studio_muted_text"
        hbox:
            spacing 5
            textbutton "+ Scene" action Function(live_studio.create_scene, "New Scene", "scene", None) style "live_studio_compact_button"
            textbutton "+ UI" action Function(live_studio.create_editor_ui_screen, None) style "live_studio_compact_button"
            textbutton "+ Say UI" action Function(live_studio.create_say_ui_template, None) style "live_studio_compact_button"
            textbutton "+ Choice UI" action Function(live_studio.create_choice_ui_template, None) style "live_studio_compact_button"
        hbox:
            spacing 5
            textbutton "+ Image" action Function(live_studio.set_bottom_tab, "Assets") style "live_studio_compact_button"
            textbutton "+ Text" action Function(live_studio.add_scene_text, None) style "live_studio_compact_button"
            textbutton "+ Button" action Function(live_studio.add_scene_button, None) style "live_studio_compact_button"
            textbutton "+ Dialogue" action Function(live_studio.ensure_dialogue_controller, None) style "live_studio_compact_button"

        null height 1 yfill True
        hbox:
            spacing 5
            textbutton "+ Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_compact_button"
            textbutton "+ Branch" action Function(live_studio.add_branch_frame, "Branch") style "live_studio_compact_button"
            textbutton "Blank" action Function(live_studio.add_frame, "blank", "Blank Frame") style "live_studio_compact_button"
            textbutton "Delete Frame" action Function(live_studio.remove_current_frame) sensitive len(live_studio.frame_order()) > 1 style "live_studio_compact_button"
