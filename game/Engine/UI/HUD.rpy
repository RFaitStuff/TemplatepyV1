# =============================================================================
# Engine/UI/HUD.rpy - top bar + side notifications + nav buttons
# -----------------------------------------------------------------------------
# This is the always-on overlay. The exploration screen (Engine/UI/Locations.rpy)
# layers click hotspots underneath it.
#
# Tunables you can tweak in this file:
#   hud_visible                 master kill-switch
#   hud_location_bar_size       top location image size (w, h)
#   hud_location_title_size     current-location text size
#   hud_location_objective_size current-task text size
#   hud_chars_button_size       characters button image size (w, h)
# =============================================================================


default hud_visible = True
default hud_hide_objective = False
default _hud_last_objective_click = 0.0
default _hud_last_chartarget_click = 0.0
default _hud_glow_love_t = -10.0
default _hud_glow_lust_t = -10.0
default _hud_tick = 0
define hud_location_bar_size = (760, 98)
define hud_location_title_size = 28
define hud_location_objective_size = 16
define hud_chars_button_size = (110, 110)
define hud_chars_image_zoom = 0.085
define hud_chars_image_zoom_hover = 0.095
# Glow fade curve (seconds): in -> peak hold -> out
define hud_glow_in_dur   = 0.18
define hud_glow_hold_dur = 0.20
define hud_glow_out_dur  = 0.70

image ui_hud_characters = "assets/images/UI/HUD/Characters.png"
image ui_hud_characters_love = "assets/images/UI/HUD/Characters_Love.png"
image ui_hud_characters_lust = "assets/images/UI/HUD/Characters_Lust.png"
image ui_hud_location = "assets/images/UI/HUD/Location.png"


init python:

    import time as _time

    def _hud_objective_click():
        # Single click = no-op (kept bright). Double-click within 0.35s hides.
        global hud_hide_objective, _hud_last_objective_click
        now = _time.time()
        if now - _hud_last_objective_click <= 0.35:
            hud_hide_objective = True
        _hud_last_objective_click = now
        return None

    def _hud_show_objective():
        global hud_hide_objective
        hud_hide_objective = False
        return None

    def _hud_chartarget_click():
        # Double-click character target -> untrack the character.
        global _hud_last_chartarget_click
        now = _time.time()
        if now - _hud_last_chartarget_click <= 0.35:
            try:
                clear_tracked_character()
            except NameError:
                pass
        _hud_last_chartarget_click = now
        return None

    def _hud_trigger_char_glow(which):
        # Called from _apply_stat_delta on love/lust gains.
        global _hud_glow_love_t, _hud_glow_lust_t
        now = _time.time()
        if which == "love":
            _hud_glow_love_t = now
        elif which == "lust":
            _hud_glow_lust_t = now

    def _hud_glow_alpha(elapsed):
        # Quick fade-in, brief hold, quick fade-out. Returns 0..1.
        if elapsed < 0:
            return 0.0
        i = hud_glow_in_dur
        h = hud_glow_hold_dur
        o = hud_glow_out_dur
        if elapsed < i:
            return elapsed / i
        if elapsed < i + h:
            return 1.0
        if elapsed < i + h + o:
            return max(0.0, 1.0 - (elapsed - i - h) / o)
        return 0.0

    def _hud_tick_inc():
        # Pumped by the HUD timer; used so screens that read time-based glow
        # alpha re-evaluate every frame they need to animate.
        global _hud_tick
        _hud_tick += 1

    def hud_now():
        return _time.time()


screen hud():
    zorder 100

    $ _dev_restore_open_ui()

    if not hud_visible:
        null
    else:
        # ---- top-left: day / time / stamina ----------------------------------
        frame:
            background "#000000a0"
            xalign 0.0
            yalign 0.0
            xoffset 20
            yoffset 20
            padding (16, 12)
            at slide_in_top
            vbox:
                spacing 6
                text "[weekday_name()] - Day [day]" size 22 color "#ffffff"
                text "[convert_to_12hr_format(time)]" size 22 color "#ffd27a"
                text "Stamina: [stamina]/[get_max_stamina()]" size 20 color "#aef0ae"
                hbox:
                    spacing 8
                    textbutton ("Sleep" if time_skip_sleep_hour <= time < time_skip_wake_hour else "Skip Hour") action Function(skip_hour) text_size 14

        # ---- top-center: location label + active quest objective ------------
        # Drive frame-by-frame redraws so the glow overlays animate smoothly.
        timer 0.05 action Function(_hud_tick_inc) repeat True

        vbox:
            xalign 0.5
            yalign 0.0
            yoffset -6
            # Real padding between siblings; visual tuck-under is done with a
            # per-child yoffset so the objective slides up over the bar
            # without dragging the character-target up with it.
            spacing 12
            at slide_in_top

            # Location bar with focus_mask: hitbox follows the artwork pixels,
            # so the toggle area no longer extends past the visible image.
            button:
                xysize hud_location_bar_size
                xalign 0.5
                yalign 0.0
                background None
                hover_background None
                focus_mask True
                action ToggleVariable("reveal_clicks")
                alternate ToggleVariable("reveal_clicks")
                add "ui_hud_location":
                    xalign 0.5
                    yalign 0.0
                    fit "contain"
                text "[location_name()]":
                    xalign 0.5
                    yalign 0.3
                    size hud_location_title_size
                    color "#ffffff"
                    outlines [(2, "#000000")]

            $ _qt = quest_target_for_current_location()
            if _qt and not hud_hide_objective:
                # Click = no-op, double-click hides. Right-click also reveals
                # (safety net even though the quest log now has a pin button).
                button:
                    xalign 0.5
                    yoffset -22   # tuck visually under the location bar
                    background "#1f1f1f4f"
                    hover_background "#2b2b2b88"
                    padding (14, 5)
                    action Function(_hud_objective_click)
                    alternate Function(_hud_show_objective)
                    text "[_qt]":
                        size hud_location_objective_size
                        color "#ffd27a"
            $ _ct = character_target_for_current_location()
            if _ct:
                button:
                    xalign 0.5
                    # When the objective is visible the natural spacing (12)
                    # already gives breathing room. When it is hidden, mimic
                    # the objective's tuck-under so the row sits flush with
                    # the bar instead of leaving a big gap.
                    yoffset (0 if (_qt and not hud_hide_objective) else -22)
                    background "#623c9166"
                    hover_background "#7a4cb088"
                    padding (14, 5)
                    action Function(_hud_chartarget_click)
                    alternate Function(clear_tracked_character)
                    text "[_ct]" size 14 color "#cfb1ff"

        # ---- top-right: menu buttons (quests, inventory, etc) ---------------
        hbox:
            xalign 1.0
            yalign 0.0
            xoffset -20
            yoffset 7.5
            spacing 8
            at slide_in_top
            textbutton "Quests"     action [Function(_dev_set_open_ui, "quest_log"), Show("quest_log")]        text_size 16
            textbutton "Inventory"  action [Function(_dev_set_open_ui, "inventory_panel"), Show("inventory_panel")]  text_size 16

            # Characters button + animated love/lust glow overlays. The
            # imagebutton itself is the click target; the glow images are
            # purely decorative and sit at the same anchor & zoom.
            fixed:
                xysize hud_chars_button_size

                imagebutton:
                    idle Transform("ui_hud_characters", zoom=hud_chars_image_zoom)
                    hover Composite(
                        hud_chars_button_size,
                        (0, 0), Transform("ui_hud_characters", zoom=hud_chars_image_zoom_hover),
                        (0, 0), Transform("ui_hud_characters_love", zoom=hud_chars_image_zoom_hover, matrixcolor=SaturationMatrix(0.0), alpha=0.55),
                    )
                    xysize hud_chars_button_size
                    action [Function(_dev_set_open_ui, "characters_panel"), Show("characters_panel")]

                # Read tick so the screen re-evaluates each frame.
                $ _ = _hud_tick
                $ _now = hud_now()
                $ _aLove = _hud_glow_alpha(_now - _hud_glow_love_t)
                $ _aLust = _hud_glow_alpha(_now - _hud_glow_lust_t)
                if _aLove > 0:
                    add "ui_hud_characters_love":
                        align (0.5, 0.5)
                        zoom hud_chars_image_zoom
                        alpha _aLove
                if _aLust > 0:
                    add "ui_hud_characters_lust":
                        align (0.5, 0.5)
                        zoom hud_chars_image_zoom
                        alpha _aLust

        # Notification toasts are rendered by `notification_overlay` so they
        # stay visible even when dialogue/UI layers change.
        null


screen notification_overlay():
    zorder 210
    use notification_stack()


init python:
    if "notification_overlay" not in config.overlay_screens:
        config.overlay_screens.append("notification_overlay")


# =============================================================================
# Notification stack screen
# -----------------------------------------------------------------------------
# Renders every entry in `_notify_active`. Quest toasts are routed to a
# separate top-center stack so they sit visually under the location label;
# everything else stacks at the top-right, flush to the screen edge.
# Expiry is handled centrally via the periodic callback in
# Engine/Notifications.rpy (see _tick_notifications). No per-card timers.
# =============================================================================
screen notification_stack():
    zorder 210

    # Tick the central expiry sweeper while the screen is shown. Screen
    # timers fire even when the game is idle waiting for input (e.g. inside
    # a `say` interaction), so this is what guarantees toasts disappear on
    # time, not only after the player advances dialogue.
    timer 0.25 action Function(_tick_notifications) repeat True

    # ---- right-edge stack: info / stat / mood / item -----------------
    $ _right_toasts = [_n for _n in _notify_active if _n.get("kind") != "quest"]
    for _i, _n in enumerate(_right_toasts):
        $ _y = 120 + _i * 76
        use _notification_card_right(_n, _y)

    # ---- top-center stack: quest toasts under the location label ----
    $ _quest_toasts = [_n for _n in _notify_active if _n.get("kind") == "quest"]
    for _i, _n in enumerate(_quest_toasts):
        $ _yq = 96 + _i * 60
        use _notification_card_quest(_n, _yq)


screen _notification_card_right(n, y):
    frame:
        xalign 1.0
        ypos y
        xoffset 0
        at notification_card_right_t
        background "#1a1a1aee"
        padding (16, 10)
        xminimum 280
        ymaximum 64
        hbox:
            spacing 12
            frame:
                background (n.get("color") or "#ffd27a")
                xysize (8, 40)
            text n["text"] size 16 color (n.get("color") or "#ffffff") yalign 0.5


screen _notification_card_quest(n, y):
    frame:
        xalign 0.5
        ypos y
        at notification_card_quest_t
        background "#1f1f1fee"
        padding (18, 8)
        xminimum 360
        ymaximum 56
        hbox:
            spacing 10
            xalign 0.5
            text "{color=#ffd27a}\u2605{/color}" size 18 yalign 0.5
            text n["text"] size 16 color (n.get("color") or "#ffd27a") yalign 0.5


# Slide-in animations. Slide-out is implicit: when the active entry is
# removed by the periodic sweep, the screen re-renders without it.
transform notification_card_right_t:
    subpixel True
    xoffset 320
    alpha 0.0
    easein _mt(0.35) xoffset 0 alpha 1.0

transform notification_card_quest_t:
    subpixel True
    yoffset -40
    alpha 0.0
    easein _mt(0.35) yoffset 0 alpha 1.0
