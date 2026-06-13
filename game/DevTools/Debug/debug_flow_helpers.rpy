# =============================================================================
# Debug Flow Helpers
# =============================================================================
# Lightweight helpers for QA: temporary skip buttons during long scenes and
# explicit warnings before route-locking or high-impact choices.
# =============================================================================


default debug_skip_target = None


init python:

    def debug_skip(caption="Skip", label=None, pos=(50, 50), release=False):
        global debug_skip_target
        try:
            if not release and not config.developer:
                debug_skip_target = None
                renpy.hide_screen("debug_skip_target")
                return None
        except Exception:
            if not release:
                return None
        if not label:
            debug_skip_target = None
            renpy.hide_screen("debug_skip_target")
            return None
        debug_skip_target = {
            "caption": caption or "Skip",
            "label": label,
            "pos": pos,
        }
        renpy.show_screen("debug_skip_target")
        return None

    def clear_debug_skip():
        global debug_skip_target
        debug_skip_target = None
        renpy.hide_screen("debug_skip_target")
        return None


label major_choice_warning(message="This choice may affect the rest of this route."):
    call screen major_choice_warning(message)
    return


screen debug_skip_target():
    zorder 950
    if debug_skip_target:
        $ _pos = debug_skip_target.get("pos", (50, 50))
        textbutton debug_skip_target.get("caption", "Skip"):
            pos _pos
            text_size 20
            background "#11131fcc"
            hover_background "#623c91dd"
            padding (14, 8)
            action [Function(clear_debug_skip), Jump(debug_skip_target.get("label"))]


screen major_choice_warning(message):
    modal True
    zorder 950
    add "#05040bcc"
    frame:
        align (0.5, 0.5)
        xmaximum 680
        background "#11131ff2"
        padding (34, 28)
        vbox:
            spacing 18
            text "Important Choice":
                xalign 0.5
                size 34
                color "#ffd27a"
            text message:
                xalign 0.5
                text_align 0.5
                size 22
                color "#f5edf7"
            textbutton "Continue":
                xalign 0.5
                text_size 24
                background "#623c91dd"
                hover_background "#7a4cb0dd"
                padding (24, 12)
                action Return(True)
