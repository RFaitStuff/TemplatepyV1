# =============================================================================
# Interface Hide / Screenshot Mode
# =============================================================================
# Clean-view helpers for screenshots, gallery thumbnail capture, and dev previews.
# =============================================================================


default interface_hidden = False
default screenshot_mode = False


init python:

    def set_interface_hidden(value=True):
        global interface_hidden
        interface_hidden = bool(value)
        if interface_hidden:
            for screen_name in (
                "action_menu",
                "inventory_panel",
                "inventory_phone_shell",
                "quest_log",
                "characters_panel",
                "character_gallery_view",
                "gallery_panel",
                "debug_tools_menu",
            ):
                try:
                    renpy.hide_screen(screen_name)
                except Exception:
                    pass
        try:
            renpy.restart_interaction()
        except Exception:
            pass
        return None

    def enter_screenshot_mode():
        global screenshot_mode, reveal_clicks
        screenshot_mode = True
        reveal_clicks = False
        set_interface_hidden(True)
        return None

    def exit_screenshot_mode():
        global screenshot_mode
        screenshot_mode = False
        set_interface_hidden(False)
        return None

    def toggle_screenshot_mode():
        if screenshot_mode or interface_hidden:
            return exit_screenshot_mode()
        return enter_screenshot_mode()

    def interface_visible():
        return not interface_hidden


screen screenshot_mode_controls():
    zorder 1000
    key "K_F12" action Function(toggle_screenshot_mode)
    if screenshot_mode or interface_hidden:
        key "K_h" action Function(exit_screenshot_mode)
        key "K_ESCAPE" action Function(exit_screenshot_mode)
        frame:
            xalign 0.5
            yalign 0.98
            background "#05060acc"
            padding (12, 6)
            text "Screenshot Mode - H/Esc to restore" size 14 color "#d8d8e8"


init python:
    if "screenshot_mode_controls" not in config.overlay_screens:
        config.overlay_screens.append("screenshot_mode_controls")
