# Ren'Py Live Studio - configuration and compatibility boundaries.
# Targeted at Ren'Py 8.5.3+. Animation is intentionally not part of this build.

init -1000 python in live_studio:
    from collections import OrderedDict
    from renpy.store import config

    VERSION = 3
    TOOL_NAME = "Ren'Py Live Studio"
    MIN_RENPY_VERSION = (8, 5, 3)

    # Live Studio is a development tool, but it does not require the developer
    # console flag to be manually set. Disable this before shipping a build if
    # the tool folder is kept in the game directory.
    ENABLED = True
    REQUIRE_DEVELOPER = False
    OPEN_KEY = "shift_K_l"

    PROJECT_DIRECTORY = "live_studio_projects"
    EXPORT_DIRECTORY = "live_studio_exports"

    EXPERIMENTAL_REPLACE_BLOCKS = False
    EXPERIMENTAL_PATCH_FILES = False

    DEFAULT_PREVIEW_MODE = "layout"
    DEFAULT_NEW_FRAME_MODE = "inherit"

    # A project may override this mapping from a later init block. Each entry
    # becomes one logical Scene in the frame hierarchy.
    SCENE_GROUPS = OrderedDict([
        ("Master", ("master",)),
        ("Dialogue", ("characters", "dialogue")),
        ("Effects", ("effects",)),
    ])

    UI_LAYERS = ("screens", "overlay", "transient")
    # ScreenDisplayable objects are separated into the UI tree. Other loose
    # displayables on UI/top layers are still captured so nothing visual is lost.
    EXCLUDED_SCENE_LAYERS = ()

    UI_CAPTURE_MAX_DEPTH = 32
    UI_CAPTURE_MAX_NODES = 1600

    # Responsive editor dimensions.
    LEFT_PANEL_MIN = 280
    LEFT_PANEL_MAX = 380
    LEFT_PANEL_RATIO = 0.20
    RIGHT_PANEL_MIN = 270
    RIGHT_PANEL_MAX = 360
    RIGHT_PANEL_RATIO = 0.18
    TOP_BAR_HEIGHT = 48
    BOTTOM_PANEL_MIN = 230
    BOTTOM_PANEL_MAX = 390
    BOTTOM_PANEL_RATIO = 0.30

    CANVAS_PADDING = 10
    CANVAS_BACKGROUND = "#0b111b"
    PANEL_BACKGROUND = "#111827"
    PANEL_ALT_BACKGROUND = "#182235"
    PANEL_BORDER = "#2b3b55"
    TEXT_COLOR = "#e8eef8"
    MUTED_TEXT_COLOR = "#9eabc0"
    ACCENT_COLOR = "#7fb2ff"
    WARNING_COLOR = "#ffca6b"
    ERROR_COLOR = "#ff7d8a"
    SELECTION_COLOR = "#d8c2ff"
    GUIDE_COLOR = "#68d5ff88"

    GRID_ENABLED = True
    GRID_SIZE = 16
    SNAP_ENABLED = True
    SNAP_DISTANCE = 8

    # Export previews are always generated in memory first. No files are
    # written until the explicit Export Files action is used.
    EXPORT_SECTIONS = (
        ("story", "story.rpy"),
        ("screens", "screens.rpy"),
        ("helpers", "live_studio_helpers.rpy"),
    )

    SCENE_PROPERTY_GROUPS = (
        ("Transform", (
            ("X", "properties.xpos"),
            ("Y", "properties.ypos"),
            ("X Anchor", "properties.xanchor"),
            ("Y Anchor", "properties.yanchor"),
            ("X Offset", "properties.xoffset"),
            ("Y Offset", "properties.yoffset"),
            ("Width", "properties.xsize"),
            ("Height", "properties.ysize"),
            ("X Zoom", "properties.xzoom"),
            ("Y Zoom", "properties.yzoom"),
            ("Rotation", "properties.rotate"),
        )),
        ("Appearance", (
            ("Alpha", "properties.alpha"),
            ("Z-order", "zorder"),
            ("Visible", "visible"),
            ("Locked", "locked"),
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
            ("Spacing", "properties.spacing"),
        )),
        ("Appearance", (
            ("Alpha", "properties.alpha"),
            ("Background", "properties.background"),
            ("Visible", "visible"),
            ("Locked", "locked"),
        )),
    )

    IMAGE_BUTTON_PROPERTY_GROUPS = (
        ("Button Images", (
            ("Idle Image", "properties.idle"),
            ("Hover Image", "properties.hover"),
            ("Insensitive Image", "properties.insensitive"),
            ("Selected Idle", "properties.selected_idle"),
            ("Selected Hover", "properties.selected_hover"),
        )),
    )

    TEXT_PROPERTY_GROUPS = (
        ("Text", (
            ("Text", "properties.text"),
            ("Size", "properties.size"),
            ("Color", "properties.color"),
            ("Text Align", "properties.text_align"),
            ("Bold", "properties.bold"),
            ("Italic", "properties.italic"),
        )),
    )

    ACTION_TYPES = (
        ("none", "None"),
        ("jump_frame", "Go to Frame"),
        ("jump_label", "Jump to Label"),
        ("call_label", "Call Label"),
        ("return", "Return"),
        ("show_screen", "Show Screen"),
        ("hide_screen", "Hide Screen"),
        ("set_variable", "Set Variable"),
        ("change_variable", "Change Variable"),
        ("run_script", "Run Script"),
        ("multiple", "Multiple Actions"),
    )
