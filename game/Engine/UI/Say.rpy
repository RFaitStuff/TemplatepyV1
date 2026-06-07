# =============================================================================
# Engine/UI/Say.rpy - custom dialogue box (AC-inspired)
# -----------------------------------------------------------------------------
# Override of Ren'Py's standard `screen say(who, what)`. Layout:
#   - No fullscreen gradient. The dialogue zone is just a transparent
#     bottom strip with the speaker name in an OUTLINE-ONLY box and the
#     dialogue text immediately to its right (small gap).
#   - Eye glyph button at the bottom-right corner hides the entire
#     interface; click again (or press H) to bring it back.
# =============================================================================

init 111:

    style say_name_custom is default:
        color "#ffffff"
        outlines [(2, "#000000", 0, 0)]
        size 28
        bold True

    style say_what_custom is default:
        color "#ffffff"
        outlines [(2, "#000000", 0, 0)]
        size 30
        line_spacing 4

    style say_eye_button is default:
        background "#00000000"
        hover_background "#ffffff22"
        padding (6, 2)

    style say_eye_button_text is default:
        size 32
        color "#ffffffcc"
        outlines [(2, "#000000", 0, 0)]
        hover_color "#ffd27a"

    screen say(who, what):
        zorder 160

        # Dialogue zone: bottom-anchored frame. Background is "95% transparent
        # black" per spec - i.e. alpha 0x0D (~5% opaque). Bump to "#000000f2"
        # (~95% opaque) if you want a heavier dialogue plate.
        frame:
            xalign 0.5
            yalign 1.0
            xsize 1920
            ysize 240
            background "#0000000d"
            padding (0, 0)

            # Name box - outline only, slightly down inside the zone.
            # Outline trick: outer frame supplies the border color via its
            # background; the 2px padding leaves a 2px stripe of border
            # visible around the inner transparent frame. The speaker name
            # is centered within the inner frame.
            if who is not None:
                frame:
                    xpos 60
                    ypos 70
                    background "#ffffff77"
                    xpadding 2
                    ypadding 2
                    frame:
                        background None
                        xpadding 14
                        ypadding 6
                        xminimum 180
                        text who id "who":
                            style "say_name_custom"
                            xalign 0.5
                            text_align 0.5

            # Dialogue text - close to the name (small left gap), and a
            # touch lower so it sits at the name's baseline visually.
            text what id "what":
                style "say_what_custom"
                xpos 270
                ypos 90
                xsize 1560

            # Hide-interface eye glyph (bottom-right).
            textbutton "\u25C9":
                style "say_eye_button"
                text_style "say_eye_button_text"
                xalign 1.0
                yalign 1.0
                xoffset -24
                yoffset -16
                action HideInterface()

        if not renpy.variant("small"):
            add SideImage() xalign 0.0 yalign 1.0
