# Ren'Py Live Studio - configuration and compatibility boundaries.
# Targeted at Ren'Py 8.5.3+. Animation is intentionally not part of this build.

init -1000 python in live_studio:
    from collections import OrderedDict
    from renpy.store import config

    VERSION = 7
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

    DEFAULT_PREVIEW_MODE = "capture"
    DEFAULT_NEW_FRAME_MODE = "inherit"

    # A project may override this mapping from a later init block. Each entry
    # becomes one logical Scene in the frame hierarchy.
    SCENE_GROUPS = OrderedDict([
        ("Master", ("master",)),
        ("Dialogue", ("characters", "dialogue")),
        ("Effects", ("effects",)),
    ])

    UI_LAYERS = ("screens", "overlay", "transient", "top")
    # UI-only runtime layers are captured exclusively by the UI subsystem.
    # They are deliberately omitted from the Scene tree and Scene layers panel.
    EXCLUDED_SCENE_LAYERS = UI_LAYERS

    UI_CAPTURE_MAX_DEPTH = 32
    UI_CAPTURE_MAX_NODES = 900

    # Responsive editor dimensions.
    LEFT_PANEL_MIN = 280
    LEFT_PANEL_MAX = 330
    LEFT_PANEL_RATIO = 0.18
    RIGHT_PANEL_MIN = 285
    RIGHT_PANEL_MAX = 340
    RIGHT_PANEL_RATIO = 0.18
    BOTTOM_TOOLS_MIN = 430
    BOTTOM_TOOLS_MAX = 560
    BOTTOM_TOOLS_RATIO = 0.29
    TOP_BAR_HEIGHT = 42
    FRAME_NAV_HEIGHT = 38
    BOTTOM_PANEL_MIN = 270
    BOTTOM_PANEL_MAX = 340
    BOTTOM_PANEL_RATIO = 0.31

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
    GUIDE_COLOR = "#39ff7a88"

    GRID_ENABLED = False
    GRID_SIZE = 16
    SNAP_ENABLED = True
    SNAP_DISTANCE = 8
    GUIDES_ENABLED = True
    SHOW_ALL_BOUNDS = False

    CANVAS_ZOOM_MIN = 0.35
    CANVAS_ZOOM_MAX = 2.50
    CANVAS_ZOOM_STEP = 0.10

    ASSET_PAGE_SIZE = 36

    # Compact editor chrome. These values are also used by custom scrollbar
    # styles in LiveStudio_screens.rpy.
    SCROLLBAR_WIDTH = 4
    ASSET_TREE_WIDTH = 210
    LAYER_THUMB_WIDTH = 58
    LAYER_THUMB_HEIGHT = 38
    ASSET_THUMB_WIDTH = 132
    ASSET_THUMB_HEIGHT = 82

    # Export previews are always generated in memory first. No files are
    # written until the explicit Export Files action is used.
    EXPORT_SECTIONS = (
        ("story", "story.rpy"),
        ("screens", "screens.rpy"),
        ("helpers", "live_studio_helpers.rpy"),
    )

    SCENE_PROPERTY_GROUPS = (
        ("Position", (
            ("X", "properties.xpos"),
            ("Y", "properties.ypos"),
            ("X Offset", "properties.xoffset"),
            ("Y Offset", "properties.yoffset"),
            ("X Anchor", "properties.xanchor"),
            ("Y Anchor", "properties.yanchor"),
        )),
        ("Size & Transform", (
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
        ("Position", (
            ("X", "properties.xpos"),
            ("Y", "properties.ypos"),
            ("X Offset", "properties.xoffset"),
            ("Y Offset", "properties.yoffset"),
            ("X Align", "properties.xalign"),
            ("Y Align", "properties.yalign"),
            ("X Anchor", "properties.xanchor"),
            ("Y Anchor", "properties.yanchor"),
        )),
        ("Size & Layout", (
            ("Width", "properties.xsize"),
            ("Height", "properties.ysize"),
            ("X Fill", "properties.xfill"),
            ("Y Fill", "properties.yfill"),
            ("Spacing", "properties.spacing"),
            ("Padding", "properties.padding"),
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
            ("Text / Preview", "properties.text"),
            ("Value / Expression", "binding.expression"),
            ("Text Source", "binding.mode"),
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
