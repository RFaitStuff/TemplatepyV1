# =============================================================================
# Dialogue Handler
# =============================================================================
# Exploration sprites live on master. Active conversation sprites live on the
# dialogue layer. Author-facing image syntax remains short and direct:
#
#     show alex
#     show alex sad
#     show alex outfit1 sad
#
# The dialogue cast is the authoritative layout model. Rendering is performed
# in one place, and render callbacks publish their actual interpolated position
# to _dialogue_render_debug for developer diagnostics.
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


# Kept for old scripts/saves. The core renderer now uses dialogue_position_to(),
# which can report its actual position to the debug overlay.
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
    try:
        renpy.add_layer("dialogue", above="master")
    except Exception:
        pass

    if "dialogue_defocus" not in config.overlay_screens:
        config.overlay_screens.append("dialogue_defocus")


init -40 python:

    # Runtime-only renderer samples. This is diagnostic state, not gameplay
    # state, so it is intentionally not declared with default.
    _dialogue_render_debug = {}


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
        try:
            for cid in _dialogue_known_characters():
                config.tag_layer[cid] = "dialogue"
        except Exception:
            pass


    def _dialogue_log_error(context, error):
        try:
            renpy.log("Dialogue Handler [{}]: {}".format(context, error))
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


    def _dialogue_spread(count, lo=0.20, hi=0.80):
        if count <= 0:
            return []
        if count == 1:
            return [0.5]
        if count == 2:
            return [0.35, 0.65]
        if count == 3:
            return [0.25, 0.50, 0.75]
        step = (hi - lo) / float(count - 1)
        return [lo + i * step for i in range(count)]


    # -------------------------------------------------------------------------
    # Renderer transforms
    # -------------------------------------------------------------------------

    def _dialogue_record_render(cid, x, target, start, duration, st, mode):
        if not cid:
            return
        _dialogue_render_debug[cid] = {
            "x": float(x),
            "target": float(target),
            "start": float(start),
            "duration": float(duration),
            "st": float(st),
            "mode": mode,
            "complete": bool(duration <= 0.0 or st >= duration),
        }


    def _dialogue_move_fn(*args):
        # Values are curried into the callback because renpy.show() calls each
        # supplied Transform as a factory. Arbitrary Transform attributes are
        # not preserved by that copy. The 3-argument branch keeps old saves
        # containing the former callback loadable.
        if len(args) == 3:
            trans, st, at = args
            cid = None
            start = getattr(trans, "_dialogue_x_start", 0.5)
            end = getattr(trans, "_dialogue_x_end", 0.5)
            duration = getattr(trans, "_dialogue_duration", 0.0)
        else:
            cid, start, end, duration, trans, st, at = args
        if duration <= 0.0 or st >= duration:
            x = end
            trans.xalign = 0.5
            trans.xoffset = int((end - 0.5) * config.screen_width)
            _dialogue_record_render(cid, x, end, start, duration, st, "move")
            return None

        frac = max(0.0, min(1.0, st / duration))
        frac = frac * frac * (3.0 - 2.0 * frac)
        x = start + (end - start) * frac
        trans.xalign = 0.5
        trans.xoffset = int((x - 0.5) * config.screen_width)
        _dialogue_record_render(cid, x, end, start, duration, st, "move")
        return 0


    def _dialogue_static_fn(cid, x, trans, st, at):
        trans.xalign = 0.5
        trans.xoffset = int((x - 0.5) * config.screen_width)
        _dialogue_record_render(cid, x, x, x, 0.0, st, "static")
        return None


    def _dialogue_flip_pair(flip):
        pairs = {
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
        value = pairs.get(flip, flip)
        return value if isinstance(value, tuple) else (1.0, 1.0)


    def dialogue_move_to(to=0.5, delay=None, flip=False, y=1.0, z=None, start=None, char_id=None):
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
        target = float(positions.get(to, to))
        start_x = target if start is None else float(start)
        duration = dialogue_handler_move_seconds if delay is None else float(delay)
        zoom = dialogue_handler_zoom if z is None else z
        xzoom_pair = _dialogue_flip_pair(flip)

        return Transform(
            function=renpy.curry(_dialogue_move_fn)(char_id, start_x, target, duration),
            reset=True,
            xalign=0.5,
            yalign=y,
            zoom=zoom,
            xzoom=xzoom_pair[0],
        )


    def dialogue_position_to(x=0.5, y=1.0, z=None, flip=False, char_id=None):
        x = float(x)
        zoom = dialogue_handler_zoom if z is None else z
        xzoom_pair = _dialogue_flip_pair(flip)
        return Transform(
            function=renpy.curry(_dialogue_static_fn)(char_id, x),
            reset=True,
            xalign=0.5,
            yalign=y,
            zoom=zoom,
            xzoom=xzoom_pair[0],
        )


    # -------------------------------------------------------------------------
    # Image attribute normalization
    # -------------------------------------------------------------------------

    def _dialogue_known_emotions():
        values = set()
        try:
            values.update(MOOD_DEFS.keys())
        except Exception:
            pass
        try:
            values.update(extra_emotion_names)
        except Exception:
            pass
        values.update(("neutral", "happy", "sad", "angry", "nervous"))
        return values


    def _dialogue_known_outfits(cid):
        try:
            return set(list_character_outfits(cid))
        except Exception:
            return set()


    def _dialogue_clean_attrs(cid, attrs):
        clean = []
        cid_lc = str(cid).lower()
        for value in attrs or ():
            if not isinstance(value, str):
                continue
            token = value.strip().lower()
            if not token or token in ("characters", cid_lc):
                continue
            clean.append(token)
        return clean


    def _dialogue_parse_attrs(cid, attrs):
        clean = _dialogue_clean_attrs(cid, attrs)
        emotions = _dialogue_known_emotions()
        outfits = _dialogue_known_outfits(cid)
        variant = ""
        outfit = ""
        expression = ""
        unknown = []

        for token in clean:
            if token.isdigit() and not variant:
                variant = token
            elif token in emotions:
                expression = token
            elif token in outfits:
                outfit = token
            else:
                unknown.append(token)

        # Support custom outfit/expression names not yet listed in the index.
        if unknown:
            if len(unknown) >= 2:
                outfit = outfit or unknown[0]
                expression = expression or unknown[-1]
            elif not expression and not outfit:
                expression = unknown[0]
            elif not outfit:
                outfit = unknown[0]
            elif not expression:
                expression = unknown[0]

        return {
            "variant": variant,
            "outfit": outfit,
            "expression": expression,
            "attrs": clean,
        }


    def _dialogue_current_attrs(cid):
        try:
            attrs = renpy.get_attributes(cid, layer="dialogue") or ()
        except Exception:
            attrs = ()
        return _dialogue_parse_attrs(cid, attrs)


    def _dialogue_variant_from_attrs(cid):
        return _dialogue_current_attrs(cid).get("variant", "")


    def _expression_from_attrs(attrs, cid=None):
        if cid:
            return _dialogue_parse_attrs(cid, attrs).get("expression", "")
        for value in attrs or ():
            if isinstance(value, str) and not value.isdigit():
                return value
        return ""


    def _dialogue_image_name(cid, info):
        parts = [str(cid)]
        variant = str(info.get("variant", "") or "").strip()
        outfit = str(info.get("outfit", "") or "").strip()
        expression = str(info.get("expression", "") or "").strip()

        if variant:
            parts.append(variant)
        if outfit:
            parts.append(outfit)
        if expression:
            parts.append(expression)

        short_name = tuple(parts)
        try:
            if renpy.has_image(short_name, exact=True):
                return " ".join(parts)
        except Exception:
            pass

        long_parts = ["characters"] + parts
        try:
            if renpy.has_image(tuple(long_parts), exact=True):
                return " ".join(long_parts)
        except Exception:
            pass

        # Dynamic base fallback keeps the game running even when an explicit
        # combination is missing.
        try:
            if renpy.has_image((str(cid),), exact=True):
                return str(cid)
        except Exception:
            pass
        return "characters " + str(cid)


    # -------------------------------------------------------------------------
    # Scene/layer helpers and debug state
    # -------------------------------------------------------------------------

    def _hide_master_sprite(cid):
        hidden = False
        error = None
        try:
            renpy.hide(cid, layer="master")
            hidden = True
        except Exception:
            error = renpy.exception_only()
            _dialogue_log_error("hide master {}".format(cid), error)
        try:
            _visible_npcs.pop(cid, None)
        except Exception:
            pass
        store._dialogue_hidden_master.add(cid)
        _dialogue_record_debug(cid, "hide_master", ok=hidden, error=error)


    def _hide_dialogue_sprite(cid):
        try:
            renpy.hide(cid, layer="dialogue")
        except Exception as error:
            _dialogue_log_error("hide dialogue {}".format(cid), error)


    def _dialogue_layer_showing(cid, layer):
        try:
            return bool(renpy.showing(cid, layer=layer))
        except Exception:
            return False


    def _dialogue_record_debug(cid, action, ok=True, image=None, target_x=None, shown_x=None, error=None, attrs=None):
        state = dict(store._dialogue_debug_state.get(cid, {}))
        state["action"] = action
        state["ok"] = bool(ok)
        state["image"] = image or state.get("image", "")
        state["target_x"] = target_x
        state["requested_x"] = shown_x
        state["error"] = error or ""
        state["attrs"] = list(attrs or state.get("attrs", []))
        state["dialogue_showing"] = _dialogue_layer_showing(cid, "dialogue")
        state["master_showing"] = _dialogue_layer_showing(cid, "master")
        render = _dialogue_render_debug.get(cid, {})
        state["render_x"] = render.get("x")
        state["render_target"] = render.get("target")
        state["render_mode"] = render.get("mode", "")
        state["render_complete"] = render.get("complete")
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
        except Exception as error:
            _dialogue_log_error("background blur", error)


    def BGBlur(value=True):
        store._dialogue_bg_blur_enabled = bool(value)
        _set_master_bg_blur(bool(store._in_dialogue))
        return None


    bg_blur = BGBlur
    set_dialogue_bg_blur = BGBlur


    # -------------------------------------------------------------------------
    # Authoritative cast renderer
    # -------------------------------------------------------------------------

    def _layout_dialogue_cast(transition=False, animate=True):
        cast = store._dialogue_cast
        if not isinstance(cast, dict) or not cast:
            return None

        automatic = [cid for cid, info in cast.items() if not info.get("manual")]
        automatic.sort(key=lambda cid: cast[cid].get("origin_x", 0.5))
        automatic_x = dict(zip(automatic, _dialogue_spread(len(automatic))))

        for cid, info in list(cast.items()):
            if not isinstance(info, dict):
                continue

            if info.get("manual"):
                x = float(info.get("xalign", 0.5))
                y = float(info.get("yalign", 1.0))
            else:
                x = float(automatic_x.get(cid, 0.5))
                y = 1.0
                info["xalign"] = x
                info["yalign"] = y

            zoom = info.get("zoom", dialogue_handler_zoom)
            old_x = float(info.get("shown_xalign", x))
            should_move = bool(animate and abs(old_x - x) >= 0.001)
            image_name = _dialogue_image_name(cid, info)
            show_ok = False
            show_error = None

            try:
                transform = (
                    dialogue_move_to(x, y=y, z=zoom, start=old_x, char_id=cid)
                    if should_move
                    else dialogue_position_to(x, y=y, z=zoom, char_id=cid)
                )
                renpy.show(
                    image_name,
                    at_list=[transform],
                    tag=cid,
                    layer="dialogue",
                )
                show_ok = True
            except Exception:
                show_error = renpy.exception_only()
                _dialogue_log_error("layout {}".format(cid), show_error)

            if show_ok:
                info["requested_xalign"] = x
                info["shown_xalign"] = x

            _dialogue_record_debug(
                cid,
                "layout",
                ok=show_ok,
                image=image_name,
                target_x=x,
                shown_x=info.get("shown_xalign", old_x),
                error=show_error,
                attrs=info.get("source_attrs", []),
            )

        if transition:
            try:
                renpy.with_statement(Dissolve(dialogue_handler_fade_seconds))
            except Exception as error:
                _dialogue_log_error("layout transition", error)
        return None


    def begin_dialogue(char_id=None, pos="middle"):
        try:
            renpy.hide_screen("location_visual_layers")
        except Exception:
            pass
        if store._in_dialogue:
            if char_id:
                dialogue_show(char_id, pos=pos)
            return None

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
        return None


    def end_dialogue():
        try:
            clear_dialog_mode()
        except Exception:
            pass
        if not store._in_dialogue and not store._dialogue_cast:
            store._dialogue_room_snap = {}
            store._dialogue_hidden_master = set()
            return None

        for cid in list(store._dialogue_cast.keys()):
            _hide_dialogue_sprite(cid)

        store._dialogue_cast = {}
        store._in_dialogue = None
        store._dialogue_room_snap = {}
        store._dialogue_hidden_master = set()
        _dialogue_render_debug.clear()
        _set_master_bg_blur(False)

        try:
            renpy.with_statement(Dissolve(dialogue_handler_fade_seconds))
        except Exception as error:
            _dialogue_log_error("end transition", error)
        return None


    enter_dialogue = begin_dialogue
    exit_dialogue = end_dialogue


    def dialogue_show(
        char_id,
        variant=None,
        expression=None,
        outfit=None,
        pos=None,
        manual=None,
        transition=False,
    ):
        if not char_id:
            return None

        if not store._in_dialogue:
            store._in_dialogue = char_id
            _set_master_bg_blur(True)

        # Capture author-written attributes before re-showing the image. This
        # preserves `show alex sad` when the Character callback first registers
        # Alex as a dialogue speaker.
        parsed = _dialogue_current_attrs(char_id) if _dialogue_layer_showing(char_id, "dialogue") else {
            "variant": "",
            "outfit": "",
            "expression": "",
            "attrs": [],
        }

        _hide_master_sprite(char_id)
        info = store._dialogue_cast.get(char_id, {})

        if variant is None:
            variant = info.get("variant") or parsed.get("variant")
        if variant is None:
            try:
                variant = location_character_pose(current_location, char_id) or ""
            except Exception:
                variant = ""

        if outfit is None:
            outfit = info.get("outfit") or parsed.get("outfit", "")
        if expression is None:
            expression = info.get("expression") or parsed.get("expression", "")

        x, y = _dialogue_pose_xy(pos) if pos is not None else (
            info.get("xalign", 0.5),
            info.get("yalign", 1.0),
        )

        if manual is None:
            manual = bool(info.get("manual")) or pos not in (None, "middle", "center")

        store._dialogue_cast[char_id] = {
            "variant": str(variant or "").strip(),
            "outfit": str(outfit or "").strip(),
            "expression": str(expression or "").strip(),
            "source_attrs": list(parsed.get("attrs", [])),
            "manual": bool(manual),
            "menu_locked": bool(info.get("menu_locked", manual)),
            "xalign": float(x),
            "yalign": float(y),
            "zoom": info.get("zoom", dialogue_handler_zoom),
            "origin_x": info.get("origin_x", _dialogue_origin_x(char_id)),
            "shown_xalign": info.get("shown_xalign", float(x)),
            "requested_xalign": info.get("requested_xalign", float(x)),
        }
        _layout_dialogue_cast(transition=transition)
        return None


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
        if not isinstance(info, dict):
            return None

        x, y = _dialogue_pose_xy(to)
        old_x = float(info.get("shown_xalign", info.get("xalign", 0.5)))
        info["manual"] = True
        info["menu_locked"] = True
        info["xalign"] = x
        info["yalign"] = y

        image_name = _dialogue_image_name(char_id, info)
        show_ok = False
        show_error = None
        try:
            renpy.show(
                image_name,
                at_list=[dialogue_move_to(
                    x,
                    delay=delay,
                    flip=flip,
                    y=y,
                    z=info.get("zoom", dialogue_handler_zoom),
                    start=old_x,
                    char_id=char_id,
                )],
                tag=char_id,
                layer="dialogue",
            )
            show_ok = True
        except Exception:
            show_error = renpy.exception_only()
            _dialogue_log_error("move {}".format(char_id), show_error)

        if show_ok:
            info["requested_xalign"] = x
            info["shown_xalign"] = x

        _dialogue_record_debug(
            char_id,
            "move",
            ok=show_ok,
            image=image_name,
            target_x=x,
            shown_x=info.get("shown_xalign", old_x),
            error=show_error,
            attrs=info.get("source_attrs", []),
        )
        renpy.restart_interaction()
        return None


    def dialogue_hide(char_id):
        if char_id in store._dialogue_cast:
            del store._dialogue_cast[char_id]
        _dialogue_render_debug.pop(char_id, None)
        _hide_dialogue_sprite(char_id)
        _layout_dialogue_cast(transition=False)
        return None


    def dialogue_place(char_id, pose):
        if char_id not in store._dialogue_cast:
            dialogue_show(char_id, pos=pose, manual=True)
            return None

        x, y = _dialogue_pose_xy(pose)
        info = store._dialogue_cast[char_id]
        info["manual"] = True
        info["menu_locked"] = True
        info["xalign"] = x
        info["yalign"] = y
        _layout_dialogue_cast(transition=False)
        return None


    def dialogue_release(char_id):
        """Returns a pinned character to automatic cast spacing."""
        info = store._dialogue_cast.get(char_id)
        if not isinstance(info, dict):
            return None
        info["manual"] = False
        info["menu_locked"] = False
        _layout_dialogue_cast(transition=False)
        return None


    def _sync_dialogue_cast_from_layer():
        if not getattr(store, "_in_dialogue", None):
            return None

        known = set(_dialogue_known_characters())
        try:
            showing = set(renpy.get_showing_tags(layer="dialogue"))
        except Exception:
            showing = set()

        changed = False
        for cid in known:
            if cid not in showing:
                continue

            parsed = _dialogue_current_attrs(cid)
            if cid not in store._dialogue_cast:
                origin = _dialogue_origin_x(cid)
                store._dialogue_cast[cid] = {
                    "variant": parsed.get("variant", ""),
                    "outfit": parsed.get("outfit", ""),
                    "expression": parsed.get("expression", ""),
                    "source_attrs": list(parsed.get("attrs", [])),
                    "manual": False,
                    "menu_locked": False,
                    "xalign": origin,
                    "yalign": 1.0,
                    "zoom": dialogue_handler_zoom,
                    "origin_x": origin,
                    "shown_xalign": origin,
                    "requested_xalign": origin,
                }
                _hide_master_sprite(cid)
                changed = True
            else:
                info = store._dialogue_cast[cid]
                for key in ("variant", "outfit", "expression"):
                    value = parsed.get(key, "")
                    if value != info.get(key, ""):
                        info[key] = value
                        changed = True
                info["source_attrs"] = list(parsed.get("attrs", []))

        for cid in list(store._dialogue_cast.keys()):
            if cid not in showing:
                del store._dialogue_cast[cid]
                _dialogue_render_debug.pop(cid, None)
                changed = True

        if changed:
            _layout_dialogue_cast(transition=False)
        return None


    if _sync_dialogue_cast_from_layer not in config.start_interact_callbacks:
        config.start_interact_callbacks.append(_sync_dialogue_cast_from_layer)


init 50 python:
    _install_dialogue_tag_layers()
