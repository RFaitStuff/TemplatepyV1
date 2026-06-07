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
        button:
            xalign _epos[0]
            yalign _epos[1]
            xysize _sz
            xoffset -_sz[0] // 2
            yoffset -_sz[1] // 2
            background ("#ffd84a22" if reveal_clicks else None)
            hover_background "#ffd84a44"
            action [Function(decrease_stamina, _ex.get("stamina", 10)), Function(goto_location, _ex["to"]), Jump("explore")]
            tooltip _ex.get("label", _ex["to"])
            # Hover label (entrance name).
            text _ex.get("label", _ex["to"]):
                align (0.5, 1.0)
                yoffset -8
                size 18
                color "#ffffffcc"
                outlines [(2, "#000")]
            # Quest target highlight.
            if quest_marker_for_exit(_ex["to"]):
                add "ui_quest_marker":
                    align (0.5, 0.2)
                    at pulse
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
            if quest_marker_for_iid(_npc):
                add "ui_quest_marker":
                    align (0.5, 0.0)
                    yoffset -20
                    at pulse
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
            if quest_marker_for_iid(_it):
                add "ui_quest_marker":
                    align (0.5, 0.0)
                    at pulse

    # ---- click hotspots over registered objects -------------------------
    for _obj in location_objects():
        $ _opos = _obj.get("pos", (0.5, 0.5))
        $ _osz  = _obj.get("size", (100, 100))
        $ _oimg = _obj.get("image")
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
                add _oimg:
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
            if quest_marker_for_iid(_obj["id"]):
                add "ui_quest_marker":
                    align (0.5, 0.0)
                    at pulse

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
        return list(location_data(loc_id).get("exits", []))

    def location_objects(loc_id=None):
        return list(location_data(loc_id).get("objects", []))

    def npc_clickable_image(char_id):
        try:
            v = location_character_pose(current_location, char_id)
        except Exception:
            v = ""
        if v:
            return "characters " + char_id + str(v)
        return "characters " + char_id


# =============================================================================
# Convenience image so per-room files don't have to declare it themselves.
# Drop a real asset at assets/images/UI/quest_marker.* later to override.
# =============================================================================
image ui_quest_marker = Text("!", size=42, color="#ffd27a", outlines=[(3, "#000")])
image ui_character_marker = Text("◆", size=32, color="#b487ff", outlines=[(2, "#000")])
