# =============================================================================
# Engine/UI/Locations.rpy - exploration screen
# -----------------------------------------------------------------------------
# Replaces the old left/right edge arrows with REAL exit hotspots positioned
# inside the scene (e.g. a doorway on the left third of the screen takes you
# to the Hallway). Each location declares its own exits in configure_location:
#
#   configure_location(
#       "homeroom",
#       exits=[
#           {"to": "hallway", "label": "Hallway",
#            "pos": (0.10, 0.55), "size": (220, 480)},
#           {"to": "math_room", "label": "Math Room",
#            "pos": (0.92, 0.55), "size": (220, 480)},
#       ],
#   )
#
# Anything else clickable in the room (NPCs, items, props) goes through the
# action menu (Engine/UI/Action_Menu.rpy) via the smart-mode resolver - one click
# either runs the primary action or opens the action wheel.
# =============================================================================


default reveal_clicks = False


transform exploration_layer_static(xa=0.5, ya=0.5, z=1.0, a=1.0, xo=0, yo=0):
    xalign xa
    yalign ya
    zoom z
    alpha a
    xoffset xo
    yoffset yo


transform exploration_layer_drift(dx=0, dy=0, dur=12.0):
    block:
        xoffset 0
        yoffset 0
        linear dur xoffset dx yoffset dy
        linear dur xoffset 0 yoffset 0
        repeat


screen location_visual_layers(slot=None):
    zorder 1
    for _layer in location_layers(slot=slot):
        if _layer.get("image"):
            $ _pos = _layer.get("pos", (0.5, 0.5))
            $ _offset = _layer.get("offset", (0, 0))
            $ _zoom = _layer.get("zoom", 1.0)
            $ _alpha = _layer.get("alpha", 1.0)
            $ _drift = _layer.get("drift")
            if _drift:
                $ _dx = _drift[0] if isinstance(_drift, (tuple, list)) and len(_drift) > 0 else _layer.get("drift_x", 0)
                $ _dy = _drift[1] if isinstance(_drift, (tuple, list)) and len(_drift) > 1 else _layer.get("drift_y", 0)
                $ _dur = _layer.get("duration", 12.0)
                add _layer.get("image"):
                    at exploration_layer_static(_pos[0], _pos[1], _zoom, _alpha, _offset[0], _offset[1]), exploration_layer_drift(_dx, _dy, _dur)
            else:
                add _layer.get("image"):
                    at exploration_layer_static(_pos[0], _pos[1], _zoom, _alpha, _offset[0], _offset[1])


screen location_nav(npcs_here=[]):
    zorder 10

    # Tracks which NPC is being hovered so we can render a hover bubble
    # over it. Tracks the same for objects so they get readable labels.
    default _hovered_npc    = None
    default _hovered_object = None

    # Backtick / tilde toggles "reveal mode", a temporary highlight pass
    # over every clickable interactable. Useful for players who don't want
    # to hunt-and-peck for hotspots. Hold or tap as needed.
    key "K_BACKQUOTE" action ToggleVariable("reveal_clicks")
    key "K_0" action ToggleVariable("force_action_menu")
    timer 0.05 action Function(sync_explore_npc_highlights, _hovered_npc, reveal_clicks, npcs_here) repeat True

    if reveal_clicks:
        add Solid("#10101088")

    # ---- exits (entrances to other locations) ---------------------------
    $ _exits = location_exits()
    for _ex in _exits:
        $ _epos = _ex.get("pos", (0.5, 0.95))
        $ _sz   = _ex.get("size", (200, 460))
        $ _elock = exit_locked_reason(_ex)
        button:
            xalign _epos[0]
            yalign _epos[1]
            xysize _sz
            xoffset -_sz[0] // 2
            yoffset -_sz[1] // 2
            background ("#ffd84a22" if reveal_clicks else None)
            hover_background "#ffd84a44"
            action If(_elock, Function(renpy.notify, _elock), [Function(decrease_stamina, _ex.get("stamina", 10)), Function(goto_location, _ex["to"]), Jump("explore")])
            tooltip (_elock or _ex.get("label", _ex["to"]))
            # Hover label (entrance name).
            text _ex.get("label", _ex["to"]):
                align (0.5, 1.0)
                yoffset -8
                size 18
                color "#ffffffcc"
                outlines [(2, "#000")]
            # Quest target highlight.
            $ _qmark_exit = quest_marker_text_for_exit(_ex["to"])
            if _qmark_exit:
                fixed:
                    align (0.5, 0.2)
                    at pulse
                    use quest_marker_badge(_qmark_exit)
            if character_marker_for_exit(_ex["to"]):
                add "ui_character_marker":
                    align (0.5, 0.0)
                    yoffset 12
                    at pulse

    # ---- click hotspots over each NPC currently in the room -------------
    for _npc in npcs_here:
        $ _pos = location_character_pos(current_location, _npc)
        $ _npc_img = npc_clickable_image(_npc)
        button:
            xalign _pos[0]
            yalign _pos[1]
            background None
            hover_background None
            focus_mask True
            hovered [SetScreenVariable("_hovered_npc", _npc), Function(set_explore_npc_highlight, _npc, "hover")]
            unhovered [SetScreenVariable("_hovered_npc", None), Function(set_explore_npc_highlight, _npc, ("reveal" if reveal_clicks else None))]
            action Function(handle_interactable_click, _npc, _pos)
            if _npc_img:
                # Invisible image only supplies a sprite-shaped focus mask.
                # The visible character is the already-shown master-layer NPC;
                # highlight is applied to that tag by set_explore_npc_highlight.
                add _npc_img:
                    xalign 0.5
                    yalign 1.0
                    zoom character_default_zoom
                    alpha 0.01
            $ _qmark_npc = quest_marker_text_for_iid(_npc)
            if _qmark_npc:
                fixed:
                    align (0.5, 0.0)
                    yoffset -20
                    at pulse
                    use quest_marker_badge(_qmark_npc)
            if character_marker_for_iid(_npc):
                add "ui_character_marker":
                    align (0.5, 0.0)
                    yoffset -52
                    at pulse

    # ---- click hotspots over active per-room items ----------------------
    for _it, _label, _ipos in location_active_items():
        button:
            xalign _ipos[0]
            yalign _ipos[1]
            xysize (90, 90)
            xoffset -45
            yoffset -45
            background ("#ffd84a4a" if reveal_clicks else "#ffffff20")
            hover_background "#ffd84a70"
            action Function(_handle_item_click, _it, _label)
            tooltip _it
            $ _qmark_item = quest_marker_text_for_iid(_it)
            if _qmark_item:
                fixed:
                    align (0.5, 0.0)
                    at pulse
                    use quest_marker_badge(_qmark_item)

    # ---- click hotspots over registered objects -------------------------
    for _obj in location_objects():
        $ _opos = _obj.get("pos", (0.5, 0.5))
        $ _hitbox = _obj.get("hitbox") or {}
        $ _osz  = _hitbox.get("size", _obj.get("size", (100, 100)))
        $ _oimg = _obj.get("image")
        $ _hover_img = _obj.get("hover_image") or _oimg
        $ _ohov = (_hovered_object == _obj["id"])
        if _ohov:
            $ _obj_matrix = BrightnessMatrix(0.25)
            $ _obj_alpha  = 1.0
        elif reveal_clicks:
            $ _obj_matrix = TintMatrix("#ffd84a")
            $ _obj_alpha  = 0.6
        else:
            $ _obj_matrix = None
            $ _obj_alpha  = 0.01
        button:
            xalign _opos[0]
            yalign _opos[1]
            if _oimg:
                background None
                hover_background None
                focus_mask True
                add (_hover_img if _ohov else _oimg):
                    xalign 0.5
                    yalign 0.5
                    alpha _obj_alpha
                    matrixcolor _obj_matrix
            else:
                xysize _osz
                xoffset -_osz[0] // 2
                yoffset -_osz[1] // 2
                background ("#ffd84a55" if reveal_clicks else None)
                hover_background "#ffd84a88"
            hovered SetScreenVariable("_hovered_object", _obj["id"])
            unhovered SetScreenVariable("_hovered_object", None)
            action Function(handle_interactable_click, _obj["id"], _opos)
            tooltip _obj.get("label", _obj["id"])
            $ _qmark_obj = quest_marker_text_for_iid(_obj["id"])
            if _qmark_obj:
                fixed:
                    align (0.5, 0.0)
                    at pulse
                    use quest_marker_badge(_qmark_obj)

    # ---- character hover bubble -----------------------------------------
    # Floats above whichever NPC is hovered. Shows display name, an
    # interact hint, and quest indicator if relevant.
    if _hovered_npc:
        $ _hpos       = location_character_pos(current_location, _hovered_npc)
        $ _hbubname   = character_display_name(_hovered_npc)
        $ _hbubmood   = mood_state(_hovered_npc) if _hovered_npc in character_stats else "neutral"
        $ _hbubquest  = bool(quest_marker_for_iid(_hovered_npc))
        frame:
            xalign _hpos[0]
            yalign _hpos[1]
            yoffset -540
            background "#0e0e0eee"
            padding (18, 12)
            xminimum 220
            at hover_bubble_t
            vbox:
                spacing 4
                xalign 0.5
                text _hbubname:
                    size 22
                    color "#ffd27a"
                    outlines [(2, "#000000", 0, 0)]
                    xalign 0.5
                if _hbubmood and _hbubmood != "neutral":
                    text "([_hbubmood])":
                        size 14
                        color "#cccccc"
                        xalign 0.5
                text "Click to interact":
                    size 14
                    color "#bbbbbb"
                    xalign 0.5
                if _hbubquest:
                    text "{color=#ffd27a}\u2605 Quest{/color}":
                        size 14
                        xalign 0.5

    # ---- object hover bubble (lighter, just a label) --------------------
    if _hovered_object and not _hovered_npc:
        $ _hop = None
        for _o in location_objects():
            if _o["id"] == _hovered_object:
                $ _hop = _o
        if _hop:
            $ _hopos = _hop.get("pos", (0.5, 0.5))
            frame:
                xalign _hopos[0]
                yalign _hopos[1]
                yoffset -120
                background "#0e0e0ecc"
                padding (12, 6)
                at hover_bubble_t
                text _hop.get("label", _hop["id"]):
                    size 16
                    color "#ffffff"
                    outlines [(2, "#000000", 0, 0)]
                    xalign 0.5

    # ---- tilde-reveal hint ----------------------------------------------
    if reveal_clicks:
        frame:
            xalign 0.5
            yalign 1.0
            yoffset -280
            background "#0e0e0ecc"
            padding (12, 6)
            text "Reveal mode (~) ON":
                size 14
                color "#ffd27a"


# =============================================================================
# Click handlers - ask Smart_Mode whether to run a primary action immediately
# or pop the action wheel.
# =============================================================================
init python:

    def _handle_item_click(item_id, label):
        # Items registered via location["items"] still use their own pickup
        # label (no need for a wheel for a single "pick up" action).
        if not has_seen_action(item_id, "pick_up"):
            mark_action_seen(item_id, "pick_up")
        emit("interactable_clicked", item_id, action_id="pick_up")
        decrease_stamina(20)
        renpy.jump(label)


# =============================================================================
# Lookup helpers used by the screen. Defined here so they live near the screen
# and don't pollute Game/World/Locations.rpy with UI-specific concerns.
# =============================================================================
init python:

    def location_exits(loc_id=None):
        out = []
        for ex in location_data(loc_id).get("exits", []):
            if exit_locked_reason(ex):
                if not ex.get("show_when_locked", False):
                    continue
            target = ex.get("to")
            if target and target in locations and not is_room_unlocked(target):
                if not ex.get("show_when_locked", False):
                    continue
            out.append(ex)
        return out

    def exit_locked_reason(ex):
        requirements = ex.get("requires") or ex.get("show_when") or ex.get("unlock_when")
        if requirements is not None:
            try:
                missing = first_missing_requirement(requirements)
                if missing:
                    return ex.get("locked_message") or missing
            except Exception:
                return ex.get("locked_message") or "Locked"
        target = ex.get("to")
        if target and target in locations and not is_room_unlocked(target):
            return ex.get("locked_message") or "Locked"
        return ""

    def location_objects(loc_id=None):
        out = []
        for obj in location_data(loc_id).get("objects", []):
            requirements = obj.get("requires") or obj.get("show_when") or obj.get("unlock_when")
            if requirements is not None and not meets_requirements(requirements, actor=obj.get("id")):
                continue
            out.append(obj)
        return out

    def npc_clickable_image(char_id):
        try:
            v = location_character_pose(current_location, char_id)
        except Exception:
            v = ""
        try:
            image_id = character_image_aliases.get(char_id, char_id)
        except Exception:
            image_id = char_id
        if v:
            return "characters " + image_id + str(v)
        return "characters " + image_id


# =============================================================================
# Convenience image so per-room files don't have to declare it themselves.
# Drop a real asset at assets/images/UI/quest_marker.* later to override.
# =============================================================================
image ui_quest_marker = Text("!", size=42, color="#ffd27a", outlines=[(3, "#000")])
screen quest_marker_badge(marker_text="!"):
    frame:
        background "#1a1322cc"
        padding (8, 2)
        text "[marker_text]" size 32 color "#ffd27a" outlines [(3, "#000000")]
image ui_character_marker = Text("◆", size=32, color="#b487ff", outlines=[(2, "#000")])
