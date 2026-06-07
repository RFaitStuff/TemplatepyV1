# Main Live Studio interface. The layout intentionally follows the original
# editor: project tools on top, inspector/tree left, canvas center, workspace
# below, and creation/arrangement tools on the right.

style live_studio_text is default:
    color "#e8eef8"
    size 16

style live_studio_muted_text is live_studio_text:
    color "#9eabc0"
    size 14

style live_studio_heading is live_studio_text:
    size 18
    bold True

style live_studio_small is live_studio_text:
    size 13

style live_studio_panel is frame:
    background Solid("#111827")
    padding (10, 8)

style live_studio_panel_alt is frame:
    background Solid("#182235")
    padding (8, 7)

style live_studio_button is button:
    background Solid("#202c40")
    hover_background Solid("#2b3c57")
    selected_background Solid("#36527a")
    insensitive_background Solid("#161f2d")
    padding (9, 5)

style live_studio_button_text is live_studio_text:
    size 14

style live_studio_icon_button is live_studio_button:
    padding (7, 4)

style live_studio_icon_button_text is live_studio_button_text:
    size 13

style live_studio_tree_button is button:
    background None
    hover_background Solid("#263750")
    selected_background Solid("#36527a")
    padding (5, 3)
    xfill True

style live_studio_tree_button_text is live_studio_text:
    size 14
    text_align 0.0

style live_studio_input is input:
    color "#ffffff"
    size 14

style live_studio_input_frame is frame:
    background Solid("#0d1420")
    padding (7, 4)
    xfill True

style live_studio_tab is live_studio_button:
    padding (10, 5)

style live_studio_tab_text is live_studio_button_text:
    size 13

screen live_studio_editor():
    modal True
    zorder 9999

    key "game_menu" action Return()
    key "K_ESCAPE" action Return()
    key "K_DELETE" action Function(live_studio.remove_selected_item)
    key "ctrl_K_z" action Function(live_studio.undo)
    key "ctrl_K_y" action Function(live_studio.redo)
    key "ctrl_K_c" action Function(live_studio.copy_selected)
    key "ctrl_K_v" action Function(live_studio.paste_copied)

    $ sw = config.screen_width
    $ sh = config.screen_height
    $ left_width = int(min(live_studio.LEFT_PANEL_MAX, max(live_studio.LEFT_PANEL_MIN, sw * live_studio.LEFT_PANEL_RATIO)))
    $ right_width = int(min(live_studio.RIGHT_PANEL_MAX, max(live_studio.RIGHT_PANEL_MIN, sw * live_studio.RIGHT_PANEL_RATIO)))
    $ top_height = live_studio.TOP_BAR_HEIGHT
    $ bottom_height = int(min(live_studio.BOTTOM_PANEL_MAX, max(live_studio.BOTTOM_PANEL_MIN, sh * live_studio.BOTTOM_PANEL_RATIO)))
    $ body_height = sh - top_height
    $ center_width = max(400, sw - left_width - right_width)

    add Solid("#0a0f18")

    vbox:
        spacing 0
        xfill True
        yfill True

        use live_studio_top_bar(top_height)

        hbox:
            spacing 0
            xfill True
            ysize body_height

            frame:
                style "live_studio_panel"
                xsize left_width
                yfill True
                vbox:
                    spacing 8
                    xfill True
                    yfill True
                    frame:
                        style "live_studio_panel_alt"
                        xfill True
                        ysize int(body_height * 0.48)
                        use live_studio_inspector
                    frame:
                        style "live_studio_panel_alt"
                        xfill True
                        yfill True
                        use live_studio_hierarchy

            frame:
                background Solid("#0b111b")
                padding (8, 8)
                xsize center_width
                yfill True
                vbox:
                    spacing 8
                    xfill True
                    yfill True
                    frame:
                        background Solid(live_studio.CANVAS_BACKGROUND)
                        padding (0, 0)
                        xfill True
                        yfill True
                        add live_studio.LiveStudioCanvas()
                    frame:
                        style "live_studio_panel"
                        xfill True
                        ysize bottom_height
                        use live_studio_bottom_workspace

            frame:
                style "live_studio_panel"
                xsize right_width
                yfill True
                use live_studio_tools_panel

screen live_studio_top_bar(top_height):
    frame:
        background Solid("#0d1420")
        padding (10, 5)
        xfill True
        ysize top_height
        hbox:
            spacing 6
            yalign 0.5
            xfill True

            text live_studio.TOOL_NAME style "live_studio_heading" yalign 0.5
            text "•" style "live_studio_muted_text" yalign 0.5
            text live_studio.project_name() style "live_studio_text" yalign 0.5
            null width 8

            textbutton "◀" action Function(live_studio.previous_frame) sensitive live_studio.frame_index() > 0 style "live_studio_icon_button"
            textbutton "▶" action Function(live_studio.go_expected_next) sensitive live_studio.expected_next_frame_id() is not None style "live_studio_icon_button"
            textbutton "+ Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_button"
            textbutton "+ Branch" action Function(live_studio.add_branch_frame, "Branch") style "live_studio_button"
            null width 5

            textbutton "Undo" action Function(live_studio.undo) sensitive bool(live_studio.history) style "live_studio_button"
            textbutton "Redo" action Function(live_studio.redo) sensitive bool(live_studio.redo_stack) style "live_studio_button"
            null width 5

            textbutton "Exact" action Function(live_studio.set_preview_mode, "capture") selected live_studio.preview_mode == "capture" style "live_studio_tab"
            textbutton "Editable" action Function(live_studio.set_preview_mode, "layout") selected live_studio.preview_mode == "layout" style "live_studio_tab"
            null width 5

            textbutton "New" action Confirm("Start a blank Live Studio project? Unsaved editor changes will be replaced.", Function(live_studio.begin_blank_project, "Untitled Live Studio Project")) style "live_studio_button"
            textbutton "Save" action Function(live_studio.save_project) style "live_studio_button"
            textbutton "Code" action Function(live_studio.set_bottom_tab, "Export") style "live_studio_button"

            null width 1 xfill True
            text live_studio.flow_summary() style "live_studio_muted_text" yalign 0.5
            textbutton "Close" action Return() style "live_studio_button"

screen live_studio_text_field(label, item_id, path, value):
    vbox:
        spacing 2
        xfill True
        hbox:
            spacing 4
            text label style "live_studio_muted_text"
            null width 1 xfill True
            if live_studio.has_local_override(item_id, path):
                textbutton "↶" action Function(live_studio.clear_item_override, item_id, path) style "live_studio_icon_button"
        frame:
            style "live_studio_input_frame"
            input value live_studio.editor_input_value("property", item_id, path) style "live_studio_input"

screen live_studio_action_editor(node):
    $ action = live_studio.primary_action(node)
    $ action_type = (action or {}).get("type", "none")
    vbox:
        spacing 5
        xfill True
        text "Button Logic" style "live_studio_small"
        text live_studio.action_summary(action) style "live_studio_muted_text"
        viewport:
            mousewheel "horizontal"
            draggable True
            xfill True
            ysize 36
            hbox:
                spacing 4
                for action_value, action_label in live_studio.ACTION_TYPES:
                    textbutton action_label action Function(live_studio.set_node_action_type, node.get("id"), action_value) selected action_type == action_value style "live_studio_tab"

        if action_type == "jump_frame":
            text "Destination Frame" style "live_studio_muted_text"
            viewport:
                mousewheel True
                draggable True
                ymaximum 125
                vbox:
                    spacing 3
                    xfill True
                    for frame_id, frame_name in live_studio.frame_path_options():
                        textbutton frame_name action Function(live_studio.set_button_frame_target, node.get("id"), frame_id) selected (action or {}).get("target_frame_id") == frame_id style "live_studio_tree_button"
        elif action_type in ("jump_label", "call_label"):
            text "Label" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "target") style "live_studio_input"
        elif action_type in ("show_screen", "hide_screen"):
            text "Screen" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "screen") style "live_studio_input"
        elif action_type in ("set_variable", "change_variable"):
            text "Variable" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "variable") style "live_studio_input"
            if action_type == "change_variable":
                text "Operator (=, +=, -=, *=, /=)" style "live_studio_muted_text"
                frame:
                    style "live_studio_input_frame"
                    input value live_studio.editor_input_value("action", node.get("id"), "operator") style "live_studio_input"
            text "Value (Ren'Py expression)" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "value") style "live_studio_input"
        elif action_type == "run_script":
            text "Ren'Py/Python command" style "live_studio_muted_text"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("action", node.get("id"), "script") style "live_studio_input"

screen live_studio_inspector():
    $ selected, parent_id, kind = live_studio.selected_item()
    vbox:
        spacing 7
        xfill True
        yfill True
        text "Inspector" style "live_studio_heading"

        if selected is None:
            text "Nothing selected" style "live_studio_muted_text"
            text "Project" style "live_studio_small"
            frame:
                style "live_studio_input_frame"
                input value live_studio.editor_input_value("project_name") style "live_studio_input"
            $ frame = live_studio.current_frame()
            if frame:
                text "Frame" style "live_studio_small"
                frame:
                    style "live_studio_input_frame"
                    input value live_studio.editor_input_value("frame_name", frame.get("id")) style "live_studio_input"
                text "Parent: {}".format((live_studio.frame_by_id(frame.get("parent_id")) or {}).get("name", "None")) style "live_studio_muted_text"
                text "{}".format(live_studio.flow_summary()) style "live_studio_muted_text"
                if frame.get("source_ref"):
                    text "Source: {}:{}".format(frame.get("source_ref", {}).get("filename") or "runtime", frame.get("source_ref", {}).get("line") or "?") style "live_studio_muted_text"
        else:
            hbox:
                spacing 5
                text selected.get("name", kind) style "live_studio_heading"
                text "({})".format(kind.replace("_", " ")) style "live_studio_muted_text" yalign 0.5
            if selected.get("editability"):
                text "Editability: {}".format(selected.get("editability")) style "live_studio_muted_text"

            if kind == "dialogue_controller":
                use live_studio_text_field("Say UI screen", selected.get("id"), "say_screen", selected.get("say_screen", "say"))
                use live_studio_text_field("Choice UI screen", selected.get("id"), "choice_screen", selected.get("choice_screen", "choice"))
                text "Full scene dialogue" style "live_studio_small"
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    text live_studio.dialogue_source(selected) style "live_studio_small"
            elif kind in ("dialogue_event", "dialogue_choice"):
                text "This event is edited in the Dialogue workspace." style "live_studio_muted_text"
                textbutton "Open Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_button"
            elif kind == "ui_screen":
                use live_studio_text_field("Name", selected.get("id"), "name", selected.get("name", "screen"))
                use live_studio_text_field("Role", selected.get("id"), "role", selected.get("role", "screen"))
                use live_studio_text_field("Layer", selected.get("id"), "layer", selected.get("layer", "screens"))
                text "Use role 'say' or 'choice' to connect a managed screen to Dialogue." style "live_studio_muted_text"
                if not selected.get("managed"):
                    text "Captured screens are inspected live. Convert a copy to make every supported child exportable." style "live_studio_muted_text"
                    textbutton "Convert to Managed Copy" action Function(live_studio.convert_screen_to_managed, selected.get("id")) style "live_studio_button"
                else:
                    text "Managed screen: fully generated by Live Studio" style "live_studio_muted_text"
            elif kind == "scene":
                use live_studio_text_field("Scene Name", selected.get("id"), "name", selected.get("name", "Scene"))
                text "Layers: {}".format(", ".join(selected.get("source_layers", [])) or "None") style "live_studio_muted_text"
            else:
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    vbox:
                        spacing 7
                        xfill True
                        use live_studio_text_field("Name", selected.get("id"), "name", selected.get("name", kind))
                        for group_name, properties in live_studio.selected_property_groups():
                            text group_name style "live_studio_small"
                            for label, path in properties:
                                $ value = live_studio.get_path_value(selected, path, None)
                                if isinstance(value, bool):
                                    hbox:
                                        spacing 5
                                        text label style "live_studio_muted_text" xsize 105
                                        textbutton ("On" if value else "Off") action Function(live_studio.toggle_item_value, selected.get("id"), path) selected value style "live_studio_button"
                                else:
                                    use live_studio_text_field(label, selected.get("id"), path, value)
                        if selected.get("type") in ("button", "textbutton", "imagebutton", "hotspot"):
                            use live_studio_action_editor(selected)

screen live_studio_hierarchy():
    $ state = live_studio.resolve_frame()
    vbox:
        spacing 6
        xfill True
        yfill True
        hbox:
            spacing 5
            text "Frame Hierarchy" style "live_studio_heading"
            null width 1 xfill True
            textbutton "Scene" action Function(live_studio.set_tree_tab, "Scene") selected live_studio.selected_tree_tab == "Scene" style "live_studio_tab"
            textbutton "UI" action Function(live_studio.set_tree_tab, "UI") selected live_studio.selected_tree_tab == "UI" style "live_studio_tab"

        viewport:
            mousewheel "horizontal"
            draggable True
            xfill True
            ysize 38
            hbox:
                spacing 4
                for frame_id in live_studio.frame_order():
                    $ frame = live_studio.frame_by_id(frame_id)
                    textbutton frame.get("name", "Frame") action Function(live_studio.select_frame, frame_id) selected frame_id == live_studio.current_frame_id style "live_studio_tab"

        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 2
                xfill True
                if live_studio.selected_tree_tab == "Scene":
                    for scene in state.get("scenes", []):
                        textbutton "▾  {}".format(scene.get("name", "Scene")) action Function(live_studio.select_item, scene.get("id"), "scene") selected live_studio.selected_item_id == scene.get("id") style "live_studio_tree_button"
                        for node, parent_id, depth in live_studio.walk_nodes(scene.get("nodes", []), scene.get("id"), 0):
                            hbox:
                                spacing 2
                                null width 14 + depth * 14
                                textbutton "{}  {}".format("◇" if node.get("type") == "image" else "•", node.get("name", node.get("type", "Object"))) action Function(live_studio.select_item, node.get("id"), "scene_node") selected live_studio.selected_item_id == node.get("id") style "live_studio_tree_button"
                        for controller in state.get("dialogue_controllers", []):
                            if controller.get("scene_id") == scene.get("id"):
                                hbox:
                                    null width 14
                                    textbutton "◆  Dialogue" action Function(live_studio.select_item, controller.get("id"), "dialogue_controller") selected live_studio.selected_item_id == controller.get("id") style "live_studio_tree_button"
                else:
                    for ui_screen in state.get("ui_screens", []):
                        $ prefix = "●" if ui_screen.get("managed") else "○"
                        textbutton "{}  {}".format(prefix, ui_screen.get("name", "screen")) action Function(live_studio.select_item, ui_screen.get("id"), "ui_screen") selected live_studio.selected_item_id == ui_screen.get("id") style "live_studio_tree_button"
                        for node, parent_id, depth in live_studio.walk_nodes(ui_screen.get("nodes", []), ui_screen.get("id"), 0):
                            hbox:
                                spacing 2
                                null width 14 + depth * 14
                                textbutton "•  {}".format(node.get("name", node.get("type", "Widget"))) action Function(live_studio.select_item, node.get("id"), "ui_node") selected live_studio.selected_item_id == node.get("id") style "live_studio_tree_button"

screen live_studio_bottom_workspace():
    vbox:
        spacing 5
        xfill True
        yfill True
        hbox:
            spacing 5
            textbutton "Assets" action Function(live_studio.set_bottom_tab, "Assets") selected live_studio.bottom_tab == "Assets" style "live_studio_tab"
            textbutton "Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") selected live_studio.bottom_tab == "Dialogue" style "live_studio_tab"
            textbutton "Code" action Function(live_studio.set_bottom_tab, "Export") selected live_studio.bottom_tab == "Export" style "live_studio_tab"
            textbutton "Diagnostics ({})".format(len(live_studio.runtime.get("diagnostics", []))) action Function(live_studio.set_bottom_tab, "Diagnostics") selected live_studio.bottom_tab == "Diagnostics" style "live_studio_tab"
            null width 1 xfill True
            text "Frame {}/{}".format(live_studio.frame_index() + 1, max(1, len(live_studio.frame_order()))) style "live_studio_muted_text" yalign 0.5

        if live_studio.bottom_tab == "Dialogue":
            use live_studio_dialogue_workspace
        elif live_studio.bottom_tab == "Export":
            use live_studio_export_workspace
        elif live_studio.bottom_tab == "Diagnostics":
            use live_studio_diagnostics_workspace
        else:
            use live_studio_assets_workspace

screen live_studio_assets_workspace():
    vbox:
        spacing 5
        xfill True
        yfill True
        hbox:
            spacing 5
            textbutton "Images" action Function(live_studio.set_asset_category, "images") selected live_studio.asset_category == "images" style "live_studio_tab"
            textbutton "Audio" action Function(live_studio.set_asset_category, "audio") selected live_studio.asset_category == "audio" style "live_studio_tab"
            frame:
                style "live_studio_input_frame"
                xfill True
                input default live_studio.asset_filter changed live_studio.asset_filter_changed style "live_studio_input"
            textbutton "Refresh" action Function(live_studio.refresh_assets) style "live_studio_button"

        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vpgrid:
                cols max(1, int((config.screen_width - 700) / 180))
                spacing 6
                for asset in live_studio.assets():
                    frame:
                        style "live_studio_panel_alt"
                        xsize 170
                        ysize 112
                        if asset.get("kind") == "image":
                            button:
                                style "live_studio_tree_button"
                                action Function(live_studio.add_asset_to_current_context, asset.get("name"))
                                vbox:
                                    spacing 3
                                    xalign 0.5
                                    add asset.get("name") xysize (120, 72)
                                    text asset.get("name") style "live_studio_small" text_align 0.5 xalign 0.5
                        else:
                            vbox:
                                spacing 5
                                xalign 0.5
                                yalign 0.5
                                text "♪" style "live_studio_heading" xalign 0.5
                                text asset.get("name") style "live_studio_small" text_align 0.5 xalign 0.5
                                hbox:
                                    spacing 3
                                    xalign 0.5
                                    textbutton "Music" action Function(live_studio.add_audio_event, asset.get("name"), "music") style "live_studio_button"
                                    textbutton "Sound" action Function(live_studio.add_audio_event, asset.get("name"), "sound") style "live_studio_button"

screen live_studio_dialogue_workspace():
    $ controller = live_studio.selected_dialogue_controller()
    $ event = live_studio.selected_dialogue_event()
    if controller is None:
        vbox:
            spacing 8
            xalign 0.5
            yalign 0.5
            text "This frame has no Dialogue object." style "live_studio_heading"
            text "Dialogue belongs to a Scene; Say and Choice remain separate UI screens." style "live_studio_muted_text"
            textbutton "Add Dialogue to Dialogue Scene" action Function(live_studio.ensure_dialogue_controller) style "live_studio_button"
    else:
        hbox:
            spacing 8
            xfill True
            yfill True
            frame:
                style "live_studio_panel_alt"
                xsize int((config.screen_width - 700) * 0.32)
                yfill True
                vbox:
                    spacing 5
                    hbox:
                        text "Events" style "live_studio_heading"
                        null width 1 xfill True
                        textbutton "+ Say" action Function(live_studio.add_dialogue_event, "say") style "live_studio_button"
                        textbutton "+ Choice" action Function(live_studio.add_dialogue_event, "choice") style "live_studio_button"
                    viewport:
                        mousewheel True
                        draggable True
                        scrollbars "vertical"
                        yfill True
                        vbox:
                            spacing 3
                            xfill True
                            for index, item in enumerate(controller.get("events", [])):
                                $ marker = "▶" if item.get("id") == controller.get("active_event_id") else " "
                                textbutton "{} {:02d}  {}".format(marker, index + 1, item.get("type", "say").replace("_", " ").title()) action Function(live_studio.select_dialogue_event, item.get("id")) selected event and event.get("id") == item.get("id") style "live_studio_tree_button"
                    hbox:
                        spacing 4
                        textbutton "Python" action Function(live_studio.add_dialogue_event, "script") style "live_studio_button"
                        textbutton "Ren'Py" action Function(live_studio.add_dialogue_event, "renpy") style "live_studio_button"
                        textbutton "Image" action Function(live_studio.add_dialogue_event, "show_image") style "live_studio_button"
                        textbutton "Screen" action Function(live_studio.add_dialogue_event, "show_screen") style "live_studio_button"
                        textbutton "Music" action Function(live_studio.add_dialogue_event, "play_music") style "live_studio_button"
                        textbutton "Sound" action Function(live_studio.add_dialogue_event, "play_sound") style "live_studio_button"
                        textbutton "More" action Function(live_studio.add_dialogue_event, "transition") style "live_studio_button"
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
                                text "Current Event: {}".format(event.get("type", "say").replace("_", " ").title()) style "live_studio_heading"
                                null width 1 xfill True
                                textbutton "Use in Frame" action Function(live_studio.set_active_dialogue_event, event.get("id")) selected event.get("id") == controller.get("active_event_id") style "live_studio_button"
                                textbutton "Delete" action Function(live_studio.remove_dialogue_event, event.get("id")) style "live_studio_button"
                            if event.get("type") == "say":
                                use live_studio_text_field("Speaker", event.get("id"), "speaker", event.get("speaker", ""))
                                use live_studio_text_field("Dialogue", event.get("id"), "text", event.get("text", ""))
                            elif event.get("type") == "narration":
                                use live_studio_text_field("Narration", event.get("id"), "text", event.get("text", ""))
                            elif event.get("type") == "script":
                                use live_studio_text_field("Python command (without $)", event.get("id"), "script", event.get("script", ""))
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
                            elif event.get("type") == "stop_audio":
                                use live_studio_text_field("Channel", event.get("id"), "channel", event.get("channel", "music"))
                                use live_studio_text_field("Fade out", event.get("id"), "fadeout", event.get("fadeout", 0.0))
                            elif event.get("type") == "choice":
                                use live_studio_text_field("Optional speaker", event.get("id"), "speaker", event.get("speaker", ""))
                                use live_studio_text_field("Optional menu prompt", event.get("id"), "text", event.get("text", ""))
                                hbox:
                                    text "Choices" style "live_studio_heading"
                                    null width 1 xfill True
                                    textbutton "+ Choice" action Function(live_studio.add_choice_option, event.get("id")) style "live_studio_button"
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
                                            text "Or choose a visual frame target:" style "live_studio_muted_text"
                                            viewport:
                                                mousewheel "horizontal"
                                                draggable True
                                                ysize 38
                                                hbox:
                                                    spacing 4
                                                    for frame_id, frame_name in live_studio.frame_path_options():
                                                        textbutton frame_name action Function(live_studio.set_item_value, choice.get("id"), "target_frame_id", frame_id, "Set choice frame") selected choice.get("target_frame_id") == frame_id style "live_studio_tab"
                                            textbutton "Remove Choice" action Function(live_studio.remove_choice_option, choice.get("id")) style "live_studio_button"
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
            textbutton "Regenerate" action Function(live_studio.generate_exports) style "live_studio_button"
            textbutton "Copy Current" action Function(live_studio.copy_export, export_section) style "live_studio_button"
            textbutton "Export Files" action Function(live_studio.export_files) style "live_studio_button"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            frame:
                background Solid("#090d14")
                padding (10, 8)
                xfill True
                text live_studio.export_preview(export_section) style "live_studio_small"

screen live_studio_diagnostics_workspace():
    vbox:
        spacing 5
        xfill True
        yfill True
        hbox:
            text "Diagnostics" style "live_studio_heading"
            null width 1 xfill True
            textbutton "Clear" action Function(live_studio.clear_diagnostics) style "live_studio_button"
        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True
            vbox:
                spacing 5
                xfill True
                if not live_studio.runtime.get("diagnostics"):
                    text "No diagnostics." style "live_studio_muted_text"
                for entry in live_studio.runtime.get("diagnostics", []):
                    frame:
                        style "live_studio_panel_alt"
                        xfill True
                        vbox:
                            text entry.get("level", "info").upper() style "live_studio_small"
                            text entry.get("message", "") style "live_studio_text"
                            if entry.get("context"):
                                text repr(entry.get("context")) style "live_studio_muted_text"

screen live_studio_tools_panel():
    $ selected, parent_id, kind = live_studio.selected_item()
    vbox:
        spacing 8
        xfill True
        yfill True
        text "Tools" style "live_studio_heading"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Canvas" style "live_studio_small"
                hbox:
                    spacing 4
                    for value, label in (("select", "Select"), ("move", "Move"), ("resize", "Resize"), ("rotate", "Rotate")):
                        textbutton label action Function(live_studio.set_tool_mode, value) selected live_studio.tool_mode == value style "live_studio_tab"
                textbutton ("Grid: On" if live_studio.project_setting("grid_enabled", True) else "Grid: Off") action Function(live_studio.toggle_project_setting, "grid_enabled") selected live_studio.project_setting("grid_enabled", True) style "live_studio_button"
                textbutton ("Snap: On" if live_studio.project_setting("snap_enabled", True) else "Snap: Off") action Function(live_studio.toggle_project_setting, "snap_enabled") selected live_studio.project_setting("snap_enabled", True) style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Create" style "live_studio_small"
                textbutton "New Scene" action Function(live_studio.create_scene, "New Scene", "scene", None) style "live_studio_button"
                textbutton "New UI Screen" action Function(live_studio.create_editor_ui_screen, None) style "live_studio_button"
                textbutton "New Say UI" action Function(live_studio.create_say_ui_template, None) style "live_studio_button"
                textbutton "New Choice UI" action Function(live_studio.create_choice_ui_template, None) style "live_studio_button"
                textbutton "Image from Assets" action Function(live_studio.set_bottom_tab, "Assets") style "live_studio_button"
                textbutton "Scene Text" action Function(live_studio.add_scene_text, None) style "live_studio_button"
                textbutton "Scene Button / Hotspot" action Function(live_studio.add_scene_button, None) style "live_studio_button"
                textbutton "UI Text" action Function(live_studio.add_ui_text, None, None) style "live_studio_button"
                textbutton "UI Button" action Function(live_studio.add_ui_button, None, None) style "live_studio_button"
                textbutton "UI Image Button" action Function(live_studio.add_ui_image_button, None, None, None) style "live_studio_button"
                textbutton "UI Frame" action Function(live_studio.add_ui_container, "frame", None, None) style "live_studio_button"
                textbutton "Dialogue Object" action Function(live_studio.ensure_dialogue_controller, None) style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Selection" style "live_studio_small"
                text (selected.get("name", "Nothing selected") if selected else "Nothing selected") style "live_studio_muted_text"
                hbox:
                    spacing 4
                    textbutton "Copy" action Function(live_studio.copy_selected) sensitive selected is not None style "live_studio_button"
                    textbutton "Paste" action Function(live_studio.paste_copied) sensitive live_studio.runtime.get("clipboard") is not None style "live_studio_button"
                    textbutton "Duplicate" action Function(live_studio.duplicate_selected) sensitive selected is not None style "live_studio_button"
                hbox:
                    spacing 4
                    textbutton "Back" action Function(live_studio.reorder_selected, "back") sensitive selected is not None style "live_studio_button"
                    textbutton "Forward" action Function(live_studio.reorder_selected, "forward") sensitive selected is not None style "live_studio_button"
                    textbutton "Delete" action Function(live_studio.remove_selected_item) sensitive selected is not None style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Frames" style "live_studio_small"
                textbutton "Next Inherited Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_button"
                textbutton "Branch from Current" action Function(live_studio.add_branch_frame, "Branch") style "live_studio_button"
                textbutton "Blank Frame" action Function(live_studio.add_frame, "blank", "Blank Frame") style "live_studio_button"
                textbutton "Duplicate and Detach" action Function(live_studio.duplicate_frame_detached) style "live_studio_button"
                textbutton "Delete Frame" action Function(live_studio.remove_current_frame) sensitive len(live_studio.frame_order()) > 1 style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Runtime Capture" style "live_studio_small"
                text "The game remains intact behind this modal editor." style "live_studio_muted_text"
                textbutton "Replace Current with Fresh Capture" action Confirm("Discard this frame's local edits and recapture the running game?", Function(live_studio.refresh_runtime_capture)) style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                hbox:
                    text "Next Game States" style "live_studio_small"
                    null width 1 xfill True
                    textbutton "Refresh" action Function(live_studio.refresh_source_flow_candidates) style "live_studio_button"
                $ source_candidates = live_studio.source_flow_candidates()
                if source_candidates:
                    for source_index, candidate in enumerate(source_candidates[:6]):
                        textbutton candidate.get("title", "Next statement") action Function(live_studio.import_source_candidate, source_index) style "live_studio_tree_button"
                else:
                    text "No statically predictable next interaction. It may be controlled by Python or runtime input." style "live_studio_muted_text"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Saved Projects" style "live_studio_small"
                if not live_studio.saved_project_paths():
                    text "No saved Live Studio projects yet." style "live_studio_muted_text"
                for filename, path in live_studio.saved_project_paths()[:4]:
                    textbutton filename action Confirm("Load this Live Studio project? Unsaved editor changes will be replaced.", Function(live_studio.load_project, path)) style "live_studio_tree_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Experimental File Editing" style "live_studio_small"
                textbutton ("Marker blocks: On" if live_studio.project_setting("experimental_replace_blocks") else "Marker blocks: Off") action Confirm("Enable experimental marker-block replacement for this project? Backups are created before writes.", Function(live_studio.toggle_project_setting, "experimental_replace_blocks")) selected live_studio.project_setting("experimental_replace_blocks") style "live_studio_button"
                textbutton ("Handwritten patching: On" if live_studio.project_setting("experimental_patch_files") else "Handwritten patching: Off") action Confirm("Enable experimental handwritten source patching? Conflicts can still require manual resolution.", Function(live_studio.toggle_project_setting, "experimental_patch_files")) selected live_studio.project_setting("experimental_patch_files") style "live_studio_button"

        null height 1 yfill True
        text "Animation is intentionally excluded from this build." style "live_studio_muted_text"
