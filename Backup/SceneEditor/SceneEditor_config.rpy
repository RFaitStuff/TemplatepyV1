init -899 python in _viewers:
    # SceneEditor layout sizing.
    # Adjust these values to change how much of the screen the editor uses.
    # Increase scene_editor_canvas_zoom_default to have the scene preview fill more of the canvas by default.
    # After tweaking, reload the game (Shift+R) before reopening the SceneEditor.
    # //top
    scene_editor_top_height = 40
    scene_editor_toolbar_spacing = 10
    scene_editor_toolbar_logo_gap = 20

    # //left
    # //properties (properties)
    scene_editor_sidebar_width = 300
    scene_editor_left_panel_spacing = 8
    scene_editor_property_viewport_spacing = 4
    scene_editor_property_group_spacing = 4
    scene_editor_property_entry_spacing = 4
    scene_editor_property_field_width = 74
    scene_editor_property_field_height = 24
    scene_editor_property_scrollbar_width = 6
    scene_editor_scene_tree_spacing = 4

    # //right
    scene_editor_right_sidebar_width = 310
    scene_editor_right_panel_spacing = 0
    scene_editor_right_panel_tab_spacing = 6
    scene_editor_right_panel_section_spacing = 8
    scene_editor_layer_thumb_size = 48

    # //bottom
    scene_editor_bottom_height = 300

    scene_editor_history_limit = 120
    scene_editor_canvas_zoom_default = 1
    scene_editor_preview_scale = 1.22
    scene_editor_preview_offset_x = 0.588
    scene_editor_preview_offset_y = 0.135
    scene_editor_canvas_zoom_min = 0.25
    scene_editor_canvas_zoom_max = 3.0
    scene_editor_canvas_zoom_step = 0.1
    scene_editor_image_preview = True
    scene_editor_show_missing_images = True
    scene_editor_include_ui_layers = True
    scene_editor_default_added_zorder = 0
    scene_editor_default_added_at_list = [("default", {})]

    # //assets (assets)
    scene_editor_asset_panel_width = 1070
    scene_editor_asset_panel_spacing = 12
    scene_editor_asset_path_spacing = 6
    scene_editor_asset_grid_cols = 6
    scene_editor_asset_grid_spacing = 12
    scene_editor_asset_tile_width = 190
    scene_editor_asset_tile_height = 200
    scene_editor_asset_tile_inner_spacing = 6
    scene_editor_asset_tile_thumb_width = 140
    scene_editor_asset_tile_thumb_height = 100
    scene_editor_asset_thumb_box_size = 150
    scene_editor_asset_label_height = 15
    scene_editor_asset_search_width = 200
    scene_editor_asset_scrollbar_width = 6
    scene_editor_asset_panel_background = "#0e1625"
    scene_editor_asset_tile_background = "#313742"
    scene_editor_asset_tile_border_color = "#1c263d"
    scene_editor_asset_tile_border_highlight = "#314263"
    scene_editor_asset_tile_hover_background = "#5B6D8A22"
    
    scene_editor_audio_grid_cols = 3
    scene_editor_audio_grid_spacing = 12
    scene_editor_audio_tile_width = 180
    scene_editor_audio_tile_height = 96
    scene_editor_audio_tile_thumb_height = 46

    # tools
    scene_editor_tools_panel_background = "#0e1625"
    scene_editor_tools_panel_width = 550
    scene_editor_tools_section_spacing = 10
    scene_editor_tool_button_spacing = 10
    scene_editor_selection_color = "#E7D8FFFF"
    scene_editor_selection_handle_fill = "#FFFFFFFF"
    scene_editor_selection_handle_idle_fill = "#101827FF"
    scene_editor_selection_rotate_handle_fill = "#66CCFFFF"
    scene_editor_selection_outline_thickness = 1
    scene_editor_selection_handle_size = 12
    scene_editor_selection_handle_hit_size = 20
    scene_editor_selection_rotate_handle_size = 16
    scene_editor_selection_rotate_handle_offset = 42
    scene_editor_bottom_section_spacing = 8
    scene_editor_secondary_controls_row_spacing = 8
    scene_editor_secondary_controls_spacing = 10

    scene_editor_property_groups = (
        ("Core", (
            ("Image", "child"),
            ("Xpos", "xpos"),
            ("Ypos", "ypos"),
            ("Zoom", "zoom"),
            ("SizeX", "xzoom"),
            ("SizeY", "yzoom"),
            ("Rotate", "rotate"),
            ("Alpha", "alpha"),
        )),
        ("Position", (
            ("Zpos", "zpos"),
            ("Xaround", "xaround"),
            ("Yaround", "yaround"),
            ("Radius", "radius"),
            ("Angle", "angle"),
        )),
        ("Anchor / Offset", (
            ("XAnchor", "xanchor"),
            ("YAnchor", "yanchor"),
            ("MatrixAnchorX", "matrixanchorX"),
            ("MatrixAnchorY", "matrixanchorY"),
            ("XOffset", "xoffset"),
            ("YOffset", "yoffset"),
        )),
        ("3D / Orientation", (
            ("XRotate", "xrotate"),
            ("YRotate", "yrotate"),
            ("ZRotate", "zrotate"),
            ("XOrientation", "xorientation"),
            ("YOrientation", "yorientation"),
            ("ZOrientation", "zorientation"),
            ("Point To", "point_to"),
            ("ZZoom", "zzoom"),
            ("Perspective", "perspective"),
        )),
        ("Crop", (
            ("CropX", "cropX"),
            ("CropY", "cropY"),
            ("CropW", "cropW"),
            ("CropH", "cropH"),
        )),
        ("Effects", (
            ("Blur", "blur"),
            ("Additive", "additive"),
            ("Blend", "blend"),
            ("DOF", "dof"),
            ("Focusing", "focusing"),
        )),
        ("Pan / Tile", (
            ("XPan", "xpan"),
            ("YPan", "ypan"),
            ("XTile", "xtile"),
            ("YTile", "ytile"),
        )),
        ("Matrix Transform", (
            ("ScaleX", "matrixtransform_1_1_scaleX"),
            ("ScaleY", "matrixtransform_1_2_scaleY"),
            ("ScaleZ", "matrixtransform_1_3_scaleZ"),
            ("OffsetX", "matrixtransform_2_1_offsetX"),
            ("OffsetY", "matrixtransform_2_2_offsetY"),
            ("OffsetZ", "matrixtransform_2_3_offsetZ"),
            ("RotateX", "matrixtransform_3_1_rotateX"),
            ("RotateY", "matrixtransform_3_2_rotateY"),
            ("RotateZ", "matrixtransform_3_3_rotateZ"),
        )),
        ("Matrix Color", (
            ("Invert", "matrixcolor_1_1_invert"),
            ("Contrast", "matrixcolor_2_1_contrast"),
            ("Saturate", "matrixcolor_3_1_saturate"),
            ("Bright", "matrixcolor_4_1_bright"),
            ("Hue", "matrixcolor_5_1_hue"),
        )),
        ("Advanced", (
            ("Function", "function"),
        )),
    )

    scene_editor_primary_props = (
        ("Xpos", "xpos"),
        ("Ypos", "ypos"),
        ("Zoom", "zoom"),
        ("SizeX", "xzoom"),
        ("SizeY", "yzoom"),
        ("Rotate", "rotate"),
        ("Alpha", "alpha"),
        ("XAnchor", "xanchor"),
        ("YAnchor", "yanchor"),
    )

    scene_editor_clone_props = tuple(prop for _group, props in scene_editor_property_groups for _label, prop in props if prop not in ("child", "function"))
