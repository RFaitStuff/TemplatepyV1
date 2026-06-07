# Main Live Studio interface.

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
    textalign 0.0

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

    $ sw = config.screen_width
    $ sh = config.screen_height
    $ left_width = int(min(live_studio.LEFT_PANEL_MAX, max(live_studio.LEFT_PANEL_MIN, sw * live_studio.LEFT_PANEL_RATIO)))
    $ right_width = int(min(live_studio.RIGHT_PANEL_MAX, max(live_studio.RIGHT_PANEL_MIN, sw * live_studio.RIGHT_PANEL_RATIO)))
    $ top_height = live_studio.TOP_BAR_HEIGHT
    $ bottom_height = int(min(live_studio.BOTTOM_PANEL_MAX, max(live_studio.BOTTOM_PANEL_MIN, sh * live_studio.BOTTOM_PANEL_RATIO)))
    $ body_height = sh - top_height
    $ center_width = sw - left_width - right_width

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
                        ysize int(body_height * 0.47)
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
            spacing 7
            yalign 0.5
            xfill True

            text live_studio.TOOL_NAME style "live_studio_heading" yalign 0.5
            text "•" style "live_studio_muted_text" yalign 0.5
            text live_studio.project_name() style "live_studio_text" yalign 0.5

            null width 12

            textbutton "◀" action Function(live_studio.previous_frame) style "live_studio_icon_button"
            textbutton "▶" action Function(live_studio.go_expected_next) style "live_studio_icon_button"
            textbutton "+ Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_button"
            textbutton "+ Branch" action Function(live_studio.add_branch_frame, "Branch") style "live_studio_button"

            null width 8

            textbutton "Undo" action Function(live_studio.undo) sensitive bool(live_studio.history) style "live_studio_button"
            textbutton "Redo" action Function(live_studio.redo) sensitive bool(live_studio.redo_stack) style "live_studio_button"

            null width 8

            textbutton "Capture" action Function(live_studio.set_preview_mode, "capture") selected live_studio.preview_mode == "capture" style "live_studio_tab"
            textbutton "Layout" action Function(live_studio.set_preview_mode, "layout") selected live_studio.preview_mode == "layout" style "live_studio_tab"

            null width 8

            textbutton "Save" action Function(live_studio.save_project) style "live_studio_button"
            textbutton "Export" action Function(live_studio.set_bottom_tab, "Export") style "live_studio_button"

            null width 8
            text live_studio.flow_summary() style "live_studio_muted_text" yalign 0.5

            null width 1 xfill True

            textbutton "Close" action Return() style "live_studio_button"

screen live_studio_inspector():
    $ selected, parent_id, kind = live_studio.selected_item()

    vbox:
        spacing 7
        xfill True
        yfill True

        text "Inspector" style "live_studio_heading"

        if selected is None:
            text "Select an image, UI widget, screen, scene, or Dialogue object." style "live_studio_muted_text"
            null height 4
            text "Project" style "live_studio_small"
            frame:
                style "live_studio_input_frame"
                input default live_studio.project_name() changed live_studio.set_project_name style "live_studio_input"
            $ frame = live_studio.current_frame()
            if frame:
                text "Frame" style "live_studio_small"
                frame:
                    style "live_studio_input_frame"
                    input default frame.get("name", "Frame") changed live_studio.frame_name_changed(frame.get("id")) style "live_studio_input"
                text "Parent: {}".format((live_studio.frame_by_id(frame.get("parent_id")) or {}).get("name", "None")) style "live_studio_muted_text"
                $ change_summary = "Changes: {} properties, {} additions, {} removals".format(sum(len(values) for values in frame.get("changes", {}).get("sets", {}).values()), len(frame.get("changes", {}).get("adds", [])), len(frame.get("changes", {}).get("removes", [])))
                text change_summary style "live_studio_muted_text"
        else:
            hbox:
                spacing 5
                text selected.get("name", kind) style "live_studio_heading"
                text "({})".format(kind) style "live_studio_muted_text" yalign 0.5

            if selected.get("source"):
                text "Source: {}".format(selected.get("source", {}).get("screen") or selected.get("source", {}).get("layer") or selected.get("source", {}).get("filename") or "runtime") style "live_studio_muted_text"

            if kind == "dialogue_controller":
                text "Full dialogue source" style "live_studio_small"
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    text live_studio.dialogue_source(selected) style "live_studio_small"
            elif kind in ("dialogue_event", "dialogue_choice"):
                text "Edit this event in the Dialogue workspace below." style "live_studio_muted_text"
                textbutton "Open Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") style "live_studio_button"
            else:
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    vbox:
                        spacing 7
                        xfill True
                        for group_name, properties in live_studio.scene_property_groups(kind):
                            text group_name style "live_studio_small"
                            for label, path in properties:
                                $ value = live_studio.get_path_value(selected, path, None)
                                if isinstance(value, bool):
                                    hbox:
                                        spacing 6
                                        text label style "live_studio_muted_text" xsize 90
                                        textbutton ("On" if value else "Off") action Function(live_studio.toggle_item_value, selected.get("id"), path) selected value style "live_studio_button"
                                else:
                                    vbox:
                                        spacing 2
                                        text label style "live_studio_muted_text"
                                        hbox:
                                            spacing 4
                                            frame:
                                                style "live_studio_input_frame"
                                                xfill True
                                                input default ("None" if value is None else str(value)) changed live_studio.property_changed(selected.get("id"), path) style "live_studio_input"
                                            if live_studio.has_local_override(selected.get("id"), path):
                                                textbutton "↶" action Function(live_studio.clear_item_override, selected.get("id"), path) style "live_studio_icon_button"

                if kind == "ui_node":
                    text "Editability: {}".format(selected.get("editability", "inspect")) style "live_studio_muted_text"
                    if selected.get("actions"):
                        text "Actions" style "live_studio_small"
                        for action in selected.get("actions", []):
                            text live_studio.action_summary(action) style "live_studio_muted_text"

screen live_studio_hierarchy():
    $ state = live_studio.resolve_frame()

    vbox:
        spacing 6
        xfill True
        yfill True

        hbox:
            spacing 5
            text "Hierarchy" style "live_studio_heading"
            null width 1 xfill True
            textbutton "Scene" action Function(live_studio.set_tree_tab, "Scene") selected live_studio.selected_tree_tab == "Scene" style "live_studio_tab"
            textbutton "UI" action Function(live_studio.set_tree_tab, "UI") selected live_studio.selected_tree_tab == "UI" style "live_studio_tab"

        viewport:
            mousewheel True
            draggable True
            scrollbars "vertical"
            yfill True

            vbox:
                spacing 3
                xfill True

                text "Frames" style "live_studio_small"
                for frame_id in live_studio.frame_order():
                    $ frame = live_studio.frame_by_id(frame_id)
                    textbutton (("▶ " if frame_id == live_studio.current_frame_id else "  ") + frame.get("name", "Frame")):
                        action Function(live_studio.select_frame, frame_id)
                        selected frame_id == live_studio.current_frame_id
                        style "live_studio_tree_button"

                null height 6

                if live_studio.selected_tree_tab == "Scene":
                    text "Scenes" style "live_studio_small"
                    for scene in state.get("scenes", []):
                        textbutton "▾ {}".format(scene.get("name", "Scene")):
                            action Function(live_studio.select_item, scene.get("id"), "scene")
                            selected live_studio.selected_item_id == scene.get("id")
                            style "live_studio_tree_button"
                        for node in scene.get("nodes", []):
                            use live_studio_tree_node(node, 1, "scene_node")
                else:
                    text "UI Screens" style "live_studio_small"
                    for ui_screen in state.get("ui_screens", []):
                        textbutton "▾ {} [{}]".format(ui_screen.get("name", "Screen"), ui_screen.get("layer", "screens")):
                            action Function(live_studio.select_item, ui_screen.get("id"), "ui_screen")
                            selected live_studio.selected_item_id == ui_screen.get("id")
                            style "live_studio_tree_button"
                        for node in ui_screen.get("nodes", []):
                            use live_studio_tree_node(node, 1, "ui_node")

screen live_studio_tree_node(node, depth=0, kind="scene_node"):
    $ is_dialogue = node.get("type") == "dialogue" and node.get("controller_id")
    $ target_id = node.get("controller_id") if is_dialogue else node.get("id")
    $ target_kind = "dialogue_controller" if is_dialogue else kind
    $ prefix = "  " * depth
    $ icon = "◆" if is_dialogue else ("▸" if node.get("children") else "•")

    textbutton "{}{} {}".format(prefix, icon, node.get("name", node.get("type", "Node"))):
        action Function(live_studio.select_item, target_id, target_kind)
        selected live_studio.selected_item_id == target_id
        style "live_studio_tree_button"

    for child in node.get("children", []):
        use live_studio_tree_node(child, depth + 1, kind)

screen live_studio_bottom_workspace():
    vbox:
        spacing 6
        xfill True
        yfill True

        hbox:
            spacing 5
            textbutton "Assets" action Function(live_studio.set_bottom_tab, "Assets") selected live_studio.bottom_tab == "Assets" style "live_studio_tab"
            textbutton "Dialogue" action Function(live_studio.set_bottom_tab, "Dialogue") selected live_studio.bottom_tab == "Dialogue" style "live_studio_tab"
            textbutton "Export" action Function(live_studio.set_bottom_tab, "Export") selected live_studio.bottom_tab == "Export" style "live_studio_tab"
            textbutton "Diagnostics ({})".format(len(live_studio.runtime.get("diagnostics", []))) action Function(live_studio.set_bottom_tab, "Diagnostics") selected live_studio.bottom_tab == "Diagnostics" style "live_studio_tab"

        if live_studio.bottom_tab == "Assets":
            use live_studio_assets_workspace
        elif live_studio.bottom_tab == "Dialogue":
            use live_studio_dialogue_workspace
        elif live_studio.bottom_tab == "Export":
            use live_studio_export_workspace
        else:
            use live_studio_diagnostics_workspace

screen live_studio_assets_workspace():
    vbox:
        spacing 5
        xfill True
        yfill True

        hbox:
            spacing 6
            frame:
                style "live_studio_input_frame"
                xsize 280
                input default live_studio.asset_filter changed live_studio.asset_filter_changed style "live_studio_input"
            textbutton "Refresh" action Function(live_studio.refresh_assets) style "live_studio_button"
            text "Click an image to add it to the current scene." style "live_studio_muted_text" yalign 0.5

        vpgrid:
            cols 5
            spacing 8
            xfill True
            yfill True
            mousewheel True
            draggable True
            scrollbars "vertical"

            for asset in live_studio.assets()[:300]:
                button:
                    action Function(live_studio.add_image_to_scene, asset.get("name"), None)
                    style "live_studio_button"
                    xsize 180
                    ysize 80
                    vbox:
                        spacing 3
                        text asset.get("name", "image") style "live_studio_small" xmaximum 164
                        text asset.get("tag", "") style "live_studio_muted_text"

screen live_studio_dialogue_workspace():
    $ controller = live_studio.selected_dialogue_controller()
    $ event = live_studio.selected_dialogue_event()

    hbox:
        spacing 8
        xfill True
        yfill True

        frame:
            style "live_studio_panel_alt"
            xsize 300
            yfill True

            vbox:
                spacing 5
                xfill True
                yfill True

                hbox:
                    text "Dialogue Events" style "live_studio_heading"
                    null width 1 xfill True
                    if controller is None:
                        textbutton "+ Dialogue" action Function(live_studio.ensure_dialogue_controller) style "live_studio_button"

                hbox:
                    spacing 4
                    for event_type in live_studio.DIALOGUE_EVENT_TYPES:
                        textbutton "+{}".format(event_type.title()) action Function(live_studio.add_dialogue_event, event_type) style "live_studio_icon_button"

                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    yfill True
                    vbox:
                        spacing 3
                        xfill True
                        if controller:
                            for dialogue_event in controller.get("events", []):
                                $ preview = dialogue_event.get("text") or dialogue_event.get("script") or dialogue_event.get("target") or dialogue_event.get("type")
                                $ active_prefix = "▶ " if controller.get("active_event_id") == dialogue_event.get("id") else "  "
                                textbutton "{}{}: {}".format(active_prefix, dialogue_event.get("type", "event").title(), str(preview)[:35]):
                                    action Function(live_studio.select_dialogue_event, dialogue_event.get("id"))
                                    selected event and event.get("id") == dialogue_event.get("id")
                                    style "live_studio_tree_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            yfill True

            if event is None:
                text "Select or add a dialogue event." style "live_studio_muted_text"
            else:
                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    vbox:
                        spacing 6
                        xfill True
                        hbox:
                            spacing 6
                            text "{} Event".format(event.get("type", "Event").title()) style "live_studio_heading"
                            null width 1 xfill True
                            if controller and controller.get("active_event_id") == event.get("id"):
                                text "Current Frame Event" style "live_studio_muted_text" yalign 0.5
                            else:
                                textbutton "Set Current" action Function(live_studio.set_active_dialogue_event, event.get("id")) style "live_studio_button"

                        if event.get("type") == "say":
                            text "Speaker" style "live_studio_muted_text"
                            frame:
                                style "live_studio_input_frame"
                                input default str(event.get("speaker", "")) changed live_studio.property_changed(event.get("id"), "speaker") style "live_studio_input"
                            text "Text" style "live_studio_muted_text"
                            frame:
                                style "live_studio_input_frame"
                                input default str(event.get("text", "")) changed live_studio.property_changed(event.get("id"), "text") style "live_studio_input" multiline True
                        elif event.get("type") == "narration":
                            text "Text" style "live_studio_muted_text"
                            frame:
                                style "live_studio_input_frame"
                                input default str(event.get("text", "")) changed live_studio.property_changed(event.get("id"), "text") style "live_studio_input" multiline True
                        elif event.get("type") == "script":
                            text "Python command (without $)" style "live_studio_muted_text"
                            frame:
                                style "live_studio_input_frame"
                                input default str(event.get("script", "")) changed live_studio.property_changed(event.get("id"), "script") style "live_studio_input" multiline True
                        elif event.get("type") in ("jump", "call"):
                            text "Target label or frame" style "live_studio_muted_text"
                            frame:
                                style "live_studio_input_frame"
                                input default str(event.get("target", "")) changed live_studio.property_changed(event.get("id"), "target") style "live_studio_input"
                        elif event.get("type") == "condition":
                            text "Condition" style "live_studio_muted_text"
                            frame:
                                style "live_studio_input_frame"
                                input default str(event.get("condition", "")) changed live_studio.property_changed(event.get("id"), "condition") style "live_studio_input"
                        elif event.get("type") == "choice":
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
                                        text "Caption" style "live_studio_muted_text"
                                        frame:
                                            style "live_studio_input_frame"
                                            input default str(choice.get("caption", "")) changed live_studio.property_changed(choice.get("id"), "caption") style "live_studio_input"
                                        hbox:
                                            spacing 6
                                            vbox:
                                                xfill True
                                                text "Condition" style "live_studio_muted_text"
                                                frame:
                                                    style "live_studio_input_frame"
                                                    input default str(choice.get("condition", "")) changed live_studio.property_changed(choice.get("id"), "condition") style "live_studio_input"
                                            vbox:
                                                xfill True
                                                text "Target" style "live_studio_muted_text"
                                                frame:
                                                    style "live_studio_input_frame"
                                                    input default str(choice.get("target", "")) changed live_studio.property_changed(choice.get("id"), "target") style "live_studio_input"
                                        text "Script" style "live_studio_muted_text"
                                        frame:
                                            style "live_studio_input_frame"
                                            input default str(choice.get("script", "")) changed live_studio.property_changed(choice.get("id"), "script") style "live_studio_input"

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
            textbutton "ui_overrides.rpy" action SetScreenVariable("export_section", "overrides") selected export_section == "overrides" style "live_studio_tab"
            null width 1 xfill True
            textbutton "Regenerate" action Function(live_studio.generate_exports) style "live_studio_button"
            textbutton "Copy Current" action Function(live_studio.copy_export, export_section) style "live_studio_button"
            textbutton "Export All Files" action Function(live_studio.export_files) style "live_studio_button"

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
            text "Capture and export diagnostics" style "live_studio_heading"
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
                text "Create" style "live_studio_small"
                textbutton "Add Image from Assets" action Function(live_studio.set_bottom_tab, "Assets") style "live_studio_button"
                textbutton "Add UI Text" action Function(live_studio.add_ui_text, None) style "live_studio_button"
                textbutton "Add UI Button" action Function(live_studio.add_ui_button, None) style "live_studio_button"
                textbutton "Add Dialogue" action Function(live_studio.ensure_dialogue_controller) style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Selection" style "live_studio_small"
                text (selected.get("name", "Nothing selected") if selected else "Nothing selected") style "live_studio_muted_text"
                textbutton "Toggle Visible" action Function(live_studio.toggle_item_value, selected.get("id"), "visible") sensitive selected is not None style "live_studio_button"
                textbutton "Delete" action Function(live_studio.remove_selected_item) sensitive selected is not None style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Frame" style "live_studio_small"
                textbutton "Next Inherited Frame" action Function(live_studio.add_frame, "inherit", None) style "live_studio_button"
                textbutton "Blank Frame" action Function(live_studio.add_frame, "blank", "Blank Frame") style "live_studio_button"
                textbutton "Duplicate and Detach" action Function(live_studio.duplicate_frame_detached) style "live_studio_button"
                textbutton "Delete Frame" action Function(live_studio.remove_current_frame) sensitive len(live_studio.frame_order()) > 1 style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Capture" style "live_studio_small"
                text "Runtime remains untouched behind this editor." style "live_studio_muted_text"
                textbutton "Refresh Current Frame Capture" action Confirm("Replace this frame with a fresh runtime capture?", Function(live_studio.refresh_runtime_capture)) style "live_studio_button"

        frame:
            style "live_studio_panel_alt"
            xfill True
            vbox:
                spacing 5
                text "Experimental Source Editing" style "live_studio_small"
                textbutton ("Block replacement: On" if live_studio.project_setting("experimental_replace_blocks") else "Block replacement: Off"):
                    action Confirm("This feature edits files between Live Studio markers and creates a backup. Enable it for this project?", Function(live_studio.toggle_project_setting, "experimental_replace_blocks"))
                    selected live_studio.project_setting("experimental_replace_blocks")
                    style "live_studio_button"
                textbutton ("Handwritten patching: On" if live_studio.project_setting("experimental_patch_files") else "Handwritten patching: Off"):
                    action Confirm("Handwritten patching is experimental and may conflict with external edits. Enable it for this project?", Function(live_studio.toggle_project_setting, "experimental_patch_files"))
                    selected live_studio.project_setting("experimental_patch_files")
                    style "live_studio_button"
                text "No patch runs automatically; these only unlock the experimental APIs." style "live_studio_muted_text"

        null height 1 yfill True

        text "Animation is not included in this build." style "live_studio_muted_text"
