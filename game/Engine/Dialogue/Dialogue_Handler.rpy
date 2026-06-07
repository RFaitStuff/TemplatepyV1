# =============================================================================
# Dialogue Handler
# -----------------------------------------------------------------------------
# Owns the boundary between exploration and dialogue.
#
# Exploration:
#   - Background and location NPC sprites live on the master layer.
#   - show_npc()/show_all_npcs_here render scheduled location characters.
#
# Dialogue:
#   - Active speaking characters live on the dialogue layer.
#   - Plain script statements like `show alice` and `show alex happy` are
#     routed to dialogue automatically through config.tag_layer.
#   - When a character joins the dialogue cast, their location sprite is hidden
#     from master until exploration redraws the room.
#   - menu_side() only moves _dialogue_cast entries on this layer.
# =============================================================================


define dialogue_handler_fade_seconds = 0.20
define dialogue_handler_move_seconds = 0.35
define dialogue_handler_zoom = 0.5
define dialogue_defocus_enabled = True
define dialogue_defocus_overlay = "#05070a70"
define dialogue_background_blur = 4.0

default _in_dialogue = None
default _dialogue_cast = {}
default _dialogue_room_snap = {}
default _dialogue_hidden_master = set()
default _dialogue_bg_blur_enabled = True
default _dialogue_debug_state = {}


screen dialogue_defocus():
    zorder 4
    if dialogue_defocus_enabled and _in_dialogue:
        null


transform dialogue_pos(x=0.5, y=1.0, z=0.5):
    xalign 0.5
    xoffset int((x - 0.5) * config.screen_width)
    yalign y
    zoom z


transform dialogue_bg_focus:
    blur 0.0


transform dialogue_bg_blur:
    blur dialogue_background_blur


init -80 python:
    # Keep dialogue sprites visually above the room, below screens/UI.
    try:
        renpy.add_layer("dialogue", above="master")
    except Exception:
        pass
    if "dialogue_defocus" not in config.overlay_screens:
        config.overlay_screens.append("dialogue_defocus")


init -40 python:

    def _dialogue_known_characters():
        try:
            return list(character_speakers.keys())
        except Exception:
            pass
        try:
            return list(character_stats.keys())
        except Exception:
            return []

    def _install_dialogue_tag_layers():
        # Raw `show alice` goes to dialogue; explore rendering explicitly uses
        # master, so location sprites do not get mixed with dialogue sprites.
        try:
            for cid in _dialogue_known_characters():
                config.tag_layer[cid] = "dialogue"
        except Exception:
            pass

    _install_dialogue_tag_layers()


init 100 python:
    _install_dialogue_tag_layers()


init -40 python:
    def is_dialogue_active():
        return bool(store._in_dialogue)

    def _dialogue_pose_xy(pose):
        if isinstance(pose, tuple) and len(pose) == 2:
            return float(pose[0]), float(pose[1])
        if isinstance(pose, (int, float)):
            return float(pose), 1.0
        if pose == "left":
            return 0.25, 1.0
        if pose in ("midleft", "mid_left", "mid-left", "mid left"):
            return 0.33, 1.0
        if pose == "right":
            return 0.75, 1.0
        if pose in ("midright", "mid_right", "mid-right", "mid right"):
            return 0.66, 1.0
        return 0.5, 1.0

    def _dialogue_spread(n, lo=0.20, hi=0.80):
        if n <= 0:
            return []
        if n == 1:
            return [0.5]
        if n == 2:
            return [0.35, 0.65]
        if n == 3:
            return [0.25, 0.50, 0.75]
        step = (hi - lo) / float(n - 1)
        return [lo + i * step for i in range(n)]

    def _dialogue_move_fn(trans, st, at):
        start = getattr(trans, "_dialogue_x_start", 0.5)
        end = getattr(trans, "_dialogue_x_end", 0.5)
        duration = getattr(trans, "_dialogue_duration", 0.0)
        if duration <= 0 or st >= duration:
            trans.xalign = 0.5
            trans.xoffset = int((end - 0.5) * config.screen_width)
            return None
        frac = st / duration
        frac = frac * frac * (3.0 - 2.0 * frac)
        x = start + (end - start) * frac
        trans.xalign = 0.5
        trans.xoffset = int((x - 0.5) * config.screen_width)
        return 0

    def dialogue_move_to(to=0.5, delay=None, flip=False, y=1.0, z=None, start=None):
        positions = {
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
        xzooms = {
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
        target = positions.get(to, to)
        duration = dialogue_handler_move_seconds if delay is None else delay
        zoom = dialogue_handler_zoom if z is None else z
        xzoom_pair = xzooms.get(flip, flip)
        if not isinstance(xzoom_pair, tuple):
            xzoom_pair = (1.0, 1.0)
        t = Transform(function=_dialogue_move_fn, xalign=0.5, yalign=y, zoom=zoom, xzoom=xzoom_pair[0])
        t._dialogue_x_start = target if start is None else start
        t._dialogue_x_end = target
        t._dialogue_duration = duration
        return t

    def _dialogue_variant_from_attrs(cid):
        try:
            attrs = renpy.get_attributes(cid, layer="dialogue") or ()
        except Exception:
            attrs = ()
        variant_parts = []
        for a in attrs:
            if isinstance(a, str) and a.isdigit():
                variant_parts.append(a)
        if not variant_parts:
            return ""
        return " " + " ".join(variant_parts)

    def _dialogue_image_name(cid, info):
        variant = info.get("variant", "")
        expression = info.get("expression", "")
        if expression:
            return "characters " + cid + variant + " " + expression
        return "characters " + cid + variant

    def _hide_master_sprite(cid):
        hidden = False
        error = None
        try:
            renpy.hide(cid, layer="master")
            hidden = True
        except Exception:
            error = renpy.exception_only()
        try:
            _visible_npcs.pop(cid, None)
        except Exception:
            pass
        store._dialogue_hidden_master.add(cid)
        _dialogue_record_debug(cid, "hide_master", ok=hidden, error=error)

    def _hide_dialogue_sprite(cid):
        try:
            renpy.hide(cid, layer="dialogue")
        except Exception:
            pass

    def _dialogue_layer_showing(cid, layer):
        try:
            return bool(renpy.showing(cid, layer=layer))
        except Exception:
            return False

    def _dialogue_record_debug(cid, action, ok=True, image=None, target_x=None, shown_x=None, error=None):
        state = dict(store._dialogue_debug_state.get(cid, {}))
        state["action"] = action
        state["ok"] = bool(ok)
        state["image"] = image or state.get("image", "")
        state["target_x"] = target_x
        state["shown_x"] = shown_x
        state["error"] = error or ""
        state["dialogue_showing"] = _dialogue_layer_showing(cid, "dialogue")
        state["master_showing"] = _dialogue_layer_showing(cid, "master")
        store._dialogue_debug_state[cid] = state

    def _dialogue_origin_x(cid):
        snap = store._dialogue_room_snap or {}
        if cid in snap:
            return snap[cid].get("pos", (0.5, 1.0))[0]
        try:
            return location_character_pos(current_location, cid)[0]
        except Exception:
            return 0.5

    def _set_master_bg_blur(active):
        try:
            use_blur = bool(active and dialogue_defocus_enabled and store._dialogue_bg_blur_enabled)
            renpy.show_layer_at(dialogue_bg_blur if use_blur else dialogue_bg_focus, layer="master")
        except Exception:
            pass

    def BGBlur(value=True):
        store._dialogue_bg_blur_enabled = bool(value)
        _set_master_bg_blur(bool(store._in_dialogue))
        return None

    bg_blur = BGBlur
    set_dialogue_bg_blur = BGBlur

    def _layout_dialogue_cast(transition=False, animate=True):
        cast = store._dialogue_cast
        if not cast:
            return

        auto = [cid for cid, info in cast.items() if not info.get("manual")]
        auto.sort(key=lambda cid: cast[cid].get("origin_x", 0.5))
        xs = dict(zip(auto, _dialogue_spread(len(auto))))

        for cid, info in list(cast.items()):
            if info.get("manual"):
                x = info.get("xalign", 0.5)
                y = info.get("yalign", 1.0)
            else:
                x = xs.get(cid, 0.5)
                y = 1.0
                info["xalign"] = x
                info["yalign"] = y

            z = info.get("zoom", dialogue_handler_zoom)
            old_x = info.get("shown_xalign", x)
            move = animate and abs(old_x - x) >= 0.001
            image_name = _dialogue_image_name(cid, info)
            show_ok = False
            show_error = None
            try:
                renpy.show(
                    image_name,
                    at_list=[dialogue_move_to(x, y=y, z=z, start=old_x) if move else dialogue_pos(x, y, z)],
                    tag=cid,
                    layer="dialogue",
                )
                show_ok = True
            except Exception:
                show_error = renpy.exception_only()
            if show_ok:
                info["shown_xalign"] = x
            _dialogue_record_debug(cid, "layout", ok=show_ok, image=image_name, target_x=x, shown_x=info.get("shown_xalign", old_x), error=show_error)

        if transition:
            try:
                renpy.with_statement(Dissolve(dialogue_handler_fade_seconds))
            except Exception:
                pass

    def begin_dialogue(char_id=None, pos="middle"):
        if store._in_dialogue:
            if char_id:
                dialogue_show(char_id, pos=pos)
            return

        snap = {}
        try:
            for cid, info in list(_visible_npcs.items()):
                snap[cid] = dict(info)
        except Exception:
            pass
        store._dialogue_room_snap = snap
        store._dialogue_cast = {}
        store._dialogue_hidden_master = set()
        store._in_dialogue = char_id or True
        _set_master_bg_blur(True)

        if char_id:
            dialogue_show(char_id, pos=pos, transition=True)

    def end_dialogue():
        if not store._in_dialogue and not store._dialogue_cast:
            store._dialogue_room_snap = {}
            store._dialogue_hidden_master = set()
            return

        for cid in list(store._dialogue_cast.keys()):
            _hide_dialogue_sprite(cid)

        store._dialogue_cast = {}
        store._in_dialogue = None
        store._dialogue_room_snap = {}
        store._dialogue_hidden_master = set()
        _set_master_bg_blur(False)
        try:
            renpy.with_statement(Dissolve(dialogue_handler_fade_seconds))
        except Exception:
            pass

    # Compatibility names used by older scripts.
    enter_dialogue = begin_dialogue
    exit_dialogue = end_dialogue

    def dialogue_show(char_id, variant=None, expression=None, pos=None, manual=None, transition=False):
        if not char_id:
            return
        if not store._in_dialogue:
            store._in_dialogue = char_id
            _set_master_bg_blur(True)
        _hide_master_sprite(char_id)

        info = store._dialogue_cast.get(char_id, {})
        if variant is None:
            variant = info.get("variant")
        if variant is None:
            try:
                variant = location_character_pose(current_location, char_id) or ""
            except Exception:
                variant = ""
        if variant and not str(variant).startswith(" "):
            variant = " " + str(variant)

        if expression is None:
            expression = info.get("expression", "")

        x, y = _dialogue_pose_xy(pos) if pos is not None else (
            info.get("xalign", 0.5),
            info.get("yalign", 1.0),
        )
        if manual is None:
            manual = bool(info.get("manual")) or pos not in (None, "middle", "center")

        store._dialogue_cast[char_id] = {
            "variant": variant,
            "expression": expression or "",
            "manual": bool(manual),
            "xalign": x,
            "yalign": y,
            "zoom": info.get("zoom", dialogue_handler_zoom),
            "origin_x": info.get("origin_x", _dialogue_origin_x(char_id)),
            "shown_xalign": info.get("shown_xalign", x),
        }
        _layout_dialogue_cast(transition=transition)

    def dialogue_ensure_speaker(char_id):
        if not char_id:
            return None
        if not store._in_dialogue:
            begin_dialogue(char_id)
            return None
        if char_id not in store._dialogue_cast:
            dialogue_show(char_id, transition=False)
        return None

    def dialogue_move(char_id, to=0.5, delay=None, flip=False):
        if not char_id:
            return None
        if char_id not in store._dialogue_cast:
            dialogue_show(char_id, transition=False)
        info = store._dialogue_cast.get(char_id)
        if not info:
            return None
        x, y = _dialogue_pose_xy(to)
        old_x = info.get("xalign", info.get("shown_xalign", 0.5))
        info["manual"] = True
        info["xalign"] = x
        info["yalign"] = y
        image_name = _dialogue_image_name(char_id, info)
        show_ok = False
        show_error = None
        try:
            renpy.show(
                image_name,
                at_list=[dialogue_move_to(x, delay=delay, flip=flip, y=y, z=info.get("zoom", dialogue_handler_zoom), start=old_x)],
                tag=char_id,
                layer="dialogue",
            )
            show_ok = True
        except Exception:
            show_error = renpy.exception_only()
        if show_ok:
            info["shown_xalign"] = x
        _dialogue_record_debug(char_id, "move", ok=show_ok, image=image_name, target_x=x, shown_x=info.get("shown_xalign", old_x), error=show_error)
        return None

    def dialogue_hide(char_id):
        if char_id in store._dialogue_cast:
            del store._dialogue_cast[char_id]
        _hide_dialogue_sprite(char_id)
        _layout_dialogue_cast(transition=False)

    def dialogue_place(char_id, pose):
        if char_id not in store._dialogue_cast:
            dialogue_show(char_id, pos=pose, manual=True)
            return
        x, y = _dialogue_pose_xy(pose)
        info = store._dialogue_cast[char_id]
        info["manual"] = True
        info["xalign"] = x
        info["yalign"] = y
        _layout_dialogue_cast(transition=False)

    def _expression_from_attrs(attrs):
        if not attrs:
            return ""
        for a in attrs:
            if isinstance(a, str) and not a.isdigit():
                return a
        return ""

    def _sync_dialogue_cast_from_layer():
        if not getattr(store, "_in_dialogue", None):
            return
        known = set(_dialogue_known_characters())
        try:
            showing = set(renpy.get_showing_tags(layer="dialogue"))
        except Exception:
            showing = set()

        changed = False
        for cid in known:
            if cid in showing:
                try:
                    attrs = renpy.get_attributes(cid, layer="dialogue") or ()
                except Exception:
                    attrs = ()
                variant = _dialogue_variant_from_attrs(cid)
                expression = _expression_from_attrs(attrs)
                if cid not in store._dialogue_cast:
                    origin = _dialogue_origin_x(cid)
                    store._dialogue_cast[cid] = {
                        "variant": variant,
                        "expression": expression,
                        "manual": False,
                        "xalign": origin,
                        "yalign": 1.0,
                        "zoom": dialogue_handler_zoom,
                        "origin_x": origin,
                        "shown_xalign": origin,
                    }
                    _hide_master_sprite(cid)
                    changed = True
                else:
                    info = store._dialogue_cast[cid]
                    if variant and info.get("variant") != variant:
                        info["variant"] = variant
                        changed = True
                    if expression != info.get("expression", ""):
                        info["expression"] = expression
                        changed = True

        for cid in list(store._dialogue_cast.keys()):
            if cid not in showing:
                del store._dialogue_cast[cid]
                changed = True

        if changed:
            _layout_dialogue_cast(transition=False)

    if _sync_dialogue_cast_from_layer not in config.start_interact_callbacks:
        config.start_interact_callbacks.append(_sync_dialogue_cast_from_layer)


init 50 python:
    _install_dialogue_tag_layers()
