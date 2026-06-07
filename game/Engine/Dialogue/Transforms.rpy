# =============================================================================
# Misc/Transforms.rpy - reusable motion library
# -----------------------------------------------------------------------------
# Drop these on any displayable with `at <name>` to get instant polish:
#
#   at fade_in                  - 0.4s ease-in fade
#   at slide_in_left            - slides in from off-screen left
#   at slide_in_right           - slides in from off-screen right
#   at slide_in_top             - drops from above
#   at slide_in_bottom          - rises from below
#   at pop_in                   - tiny scale-in
#   at hover_lift               - hover state lifts the displayable 8px up
#   at hover_zoom               - hover state zooms 1.0 -> 1.05
#   at hover_glow               - hover state crossfades to brighter
#   at pulse                    - infinite gentle scale pulse (highlights)
#   at shake                    - one-shot horizontal shake
#   at displace_left            - char displacement helper for menu(side="left")
#   at displace_right           - char displacement helper for menu(side="right")
#   at displace_reset           - return to original position
#
# Scale every animation with persistent.motion (1.0 = normal, 0.5 = double
# speed, 2.0 = half speed). Set persistent.motion = 0 to disable animations.
# =============================================================================


default persistent.motion = 1.0


# Convenience: clamp the multiplier so 0 means "instant".
init python:
    def _mt(x):
        m = persistent.motion if persistent.motion is not None else 1.0
        if m <= 0:
            return 0.0001
        return x * m

    transform_positions = {
        "left": 0.0,
        "midleft": 0.33,
        "mid_left": 0.33,
        "mid-left": 0.33,
        "mid left": 0.33,
        "center": 0.5,
        "middle": 0.5,
        "mid": 0.5,
        "midright": 0.66,
        "mid_right": 0.66,
        "mid-right": 0.66,
        "mid right": 0.66,
        "right": 1.0,
    }

    transform_xzooms = {
        True: (-1.0, -1.0),
        False: (1.0, 1.0),
        "left": (1.0, 1.0),
        "right": (-1.0, -1.0),
        "leftright": (1.0, -1.0),
        "left_right": (1.0, -1.0),
        "left-right": (1.0, -1.0),
        "left right": (1.0, -1.0),
        "rightleft": (-1.0, 1.0),
        "right_left": (-1.0, 1.0),
        "right-left": (-1.0, 1.0),
        "right left": (-1.0, 1.0),
    }


# ---------- entry / fade transforms ------------------------------------------
transform fade_in(wait=0.0):
    alpha 0.0
    pause _mt(wait)
    easein _mt(0.4) alpha 1.0

transform fade_out(wait=0.0):
    alpha 1.0
    pause _mt(wait)
    easeout _mt(0.3) alpha 0.0

transform slide_in_left(wait=0.0):
    subpixel True
    xoffset -250
    alpha 0.0
    pause _mt(wait)
    easein_quint _mt(0.45) xoffset 0 alpha 1.0

transform slide_in_right(wait=0.0):
    subpixel True
    xoffset 250
    alpha 0.0
    pause _mt(wait)
    easein_quint _mt(0.45) xoffset 0 alpha 1.0

transform slide_in_top(wait=0.0):
    subpixel True
    yoffset -120
    alpha 0.0
    pause _mt(wait)
    easein_quint _mt(0.45) yoffset 0 alpha 1.0

transform slide_in_bottom(wait=0.0):
    subpixel True
    yoffset 120
    alpha 0.0
    pause _mt(wait)
    easein_quint _mt(0.45) yoffset 0 alpha 1.0

transform pop_in(wait=0.0):
    subpixel True
    zoom 0.7
    alpha 0.0
    pause _mt(wait)
    easein_quint _mt(0.35) zoom 1.0 alpha 1.0


# ---------- hover transforms -------------------------------------------------
transform hover_lift:
    on idle:
        easein_quint _mt(0.18) yoffset 0
    on hover:
        easein_quint _mt(0.18) yoffset -8

transform hover_zoom:
    subpixel True
    transform_anchor True
    on idle:
        easein_quint _mt(0.2) zoom 1.0
    on hover:
        easein_quint _mt(0.2) zoom 1.05

transform hover_glow:
    on idle:
        easein _mt(0.2) matrixcolor BrightnessMatrix(0.0)
    on hover:
        easein _mt(0.2) matrixcolor BrightnessMatrix(0.15)


# ---------- attention transforms ---------------------------------------------
transform pulse:
    subpixel True
    transform_anchor True
    block:
        ease _mt(0.7) zoom 1.05
        ease _mt(0.7) zoom 1.0
        repeat

transform shake:
    block:
        linear _mt(0.05) xoffset -8
        linear _mt(0.05) xoffset 8
        linear _mt(0.05) xoffset -6
        linear _mt(0.05) xoffset 6
        linear _mt(0.05) xoffset 0


# ---------- character displacement -------------------------------------------
# These use *_offset overrides; combine them with a base position transform.
# Driven by Engine/Choice_Displace.rpy at menu time. Author transforms applied
# on top will win because show_npc() re-shows with the latest at_list.
transform displace_left:
    subpixel True
    easein _mt(0.35) xoffset -260

transform displace_right:
    subpixel True
    easein _mt(0.35) xoffset 260

transform displace_reset:
    subpixel True
    easein _mt(0.35) xoffset 0


transform move_to(to=0.5, delay=0.5, flip=False):
    subpixel True
    xzoom transform_xzooms.get(flip, flip)[0]
    easein _mt(delay) xalign transform_positions.get(to, to)
    xzoom transform_xzooms.get(flip, flip)[1]


# ---------- hover bubble (used by character/object hover popups) -------------
transform hover_bubble_t:
    subpixel True
    alpha 0.0
    yoffset 12
    easein _mt(0.18) alpha 1.0 yoffset 0
