# Ren'Py Live Studio
# Core configuration. Keep project-specific adapters out of this file.

init -950 python in live_studio:
    from collections import OrderedDict
    from renpy.store import config

    VERSION = 2
    TOOL_NAME = "Ren'Py Live Studio"

    # Shift+L avoids Ren'Py's built-in Shift+E script-editor shortcut.
    OPEN_KEY = "shift_K_l"

    # Project data and generated exports are kept outside normal story files.
    PROJECT_DIRECTORY = "live_studio_projects"
    EXPORT_DIRECTORY = "live_studio_exports"

    # These are only enabled through explicit experimental toggles in the UI.
    EXPERIMENTAL_REPLACE_BLOCKS = False
    EXPERIMENTAL_PATCH_FILES = False

    # The exact runtime screenshot is the safest initial preview. Layout mode can
    # draw editable bounds over it without destroying or re-parenting game UI.
    DEFAULT_PREVIEW_MODE = "capture"

    # Scene layers are grouped into logical scenes in the hierarchy.
    # Games can replace this mapping from another init block.
    SCENE_GROUPS = OrderedDict([
        ("Exploration", ("master",)),
        ("Dialogue", ("characters", "dialogue")),
        ("Effects", ("effects",)),
    ])

    UI_LAYERS = ("screens", "overlay", "transient")
    EXCLUDED_SCENE_LAYERS = ("screens", "overlay", "transient")

    # UI tree capture is intentionally bounded. Complex custom displayables are
    # still retained as inspect-only nodes when this limit is reached.
    UI_CAPTURE_MAX_DEPTH = 24
    UI_CAPTURE_MAX_NODES = 1200

    # Editor geometry. The screen itself calculates responsive sizes from these.
    LEFT_PANEL_MIN = 270
    LEFT_PANEL_MAX = 360
    LEFT_PANEL_RATIO = 0.19
    RIGHT_PANEL_MIN = 260
    RIGHT_PANEL_MAX = 350
    RIGHT_PANEL_RATIO = 0.18
    TOP_BAR_HEIGHT = 46
    BOTTOM_PANEL_MIN = 220
    BOTTOM_PANEL_MAX = 360
    BOTTOM_PANEL_RATIO = 0.28

    CANVAS_PADDING = 10
    CANVAS_BACKGROUND = "#111722"
    PANEL_BACKGROUND = "#111827"
    PANEL_ALT_BACKGROUND = "#182235"
    PANEL_BORDER = "#2b3b55"
    TEXT_COLOR = "#e8eef8"
    MUTED_TEXT_COLOR = "#9eabc0"
    ACCENT_COLOR = "#7fb2ff"
    WARNING_COLOR = "#ffca6b"
    ERROR_COLOR = "#ff7d8a"
    SELECTION_COLOR = "#d8c2ff"

    # New frames inherit resolved state and only store local changes.
    DEFAULT_NEW_FRAME_MODE = "inherit"

    # Export is preview/copy first. Files are only written when the user presses
    # the dedicated Export Files button.
    EXPORT_SECTIONS = (
        ("story", "story.rpy"),
        ("screens", "screens.rpy"),
        ("overrides", "ui_overrides.rpy"),
    )

    # Properties shown in the first inspector implementation.
    SCENE_PROPERTY_GROUPS = (
        ("Transform", (
            ("X", "properties.xpos"),
            ("Y", "properties.ypos"),
            ("X Anchor", "properties.xanchor"),
            ("Y Anchor", "properties.yanchor"),
            ("X Offset", "properties.xoffset"),
            ("Y Offset", "properties.yoffset"),
            ("X Zoom", "properties.xzoom"),
            ("Y Zoom", "properties.yzoom"),
            ("Rotation", "properties.rotate"),
        )),
        ("Appearance", (
            ("Alpha", "properties.alpha"),
            ("Z-order", "zorder"),
            ("Visible", "visible"),
        )),
    )

    UI_PROPERTY_GROUPS = (
        ("Layout", (
            ("X", "properties.xpos"),
            ("Y", "properties.ypos"),
            ("Width", "properties.xsize"),
            ("Height", "properties.ysize"),
            ("X Anchor", "properties.xanchor"),
            ("Y Anchor", "properties.yanchor"),
            ("X Offset", "properties.xoffset"),
            ("Y Offset", "properties.yoffset"),
        )),
        ("Appearance", (
            ("Alpha", "properties.alpha"),
            ("Visible", "visible"),
        )),
    )
