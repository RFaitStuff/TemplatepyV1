# =============================================================================
# Engine/UI/Choice.rpy - choice menu mechanics for Dialogue Handler
# -----------------------------------------------------------------------------
# Override of Ren'Py's standard `screen choice(items)` plus the helpers needed
# to call it with a particular "side":
#
#     menu (side="left"):         # next menu pops from the LEFT
#         "Yes.":
#             ...
#         "No.":
#             ...
#
# When the menu shows it:
#   1) Animates the choice container in from `side` (left / middle / right).
#   2) Slides every member of the DIALOGUE CAST (`_dialogue_cast`, see
#      Engine/Dialogue/Dialogue_Handler.rpy) into the corresponding target zone:
#        - left   -> cast moves to the right zone   (0.62..0.85)
#        - right  -> cast moves to the left zone    (0.15..0.38)
#        - middle -> each cast member slides outward from center to
#                    whichever side they're already on
#      Multiple cast members are spread evenly inside the target zone.
#   3) Only dialogue-layer cast members move. Location/explore sprites and
#      backgrounds are never transformed by this file.
#   4) On choice, restores everyone to their original dialogue position.
#
# Author overrides:
#   - menu_side(None) (or omitting side) keeps the default behaviour: middle
#     overlay, no displacement.
#   - menu_side(..., displace=False) animates the menu but leaves the cast
#     alone.
#   - dialogue_place(char, "left"|"right"|"middle"|(x,y)) pins a cast
#     member, opting them out of auto-spacing AND auto-displacement.
# =============================================================================


# Per-call state. Cleared after the next choice screen renders.
default _menu_side          = None     # "left" | "middle" | "right" | None
default _menu_displace      = True
default _menu_displaced     = []       # [(char_id, original_xalign)] for restore
default _menu_debug_state   = {}
default _choice_hover_idx   = -1
default left                = "left"
default right               = "right"
default middle              = "middle"
define choice_menu_side_arg_enabled = True


init python:

    # Optional shorthand so authors can write menu(left): / menu(right):
    # as long as Ren'Py menu arguments are enabled in script usage.

    def menu_side(side, displace=True):
        store._menu_side     = side
        store._menu_displace = bool(displace)
        store._menu_debug_state = {
            "requested_side": side,
            "displace": bool(displace),
            "cast_before": list(getattr(store, "_dialogue_cast", {}).keys()),
            "targets": {},
            "moved": [],
            "restored": [],
            "notes": "",
        }
        try:
            _sync_dialogue_cast_from_layer()
        except Exception:
            store._menu_debug_state["notes"] = renpy.exception_only()
        if side and displace:
            _apply_menu_displacement(side)


    # ---- displacement engine -----------------------------------------------
    # NEW MODEL: only the DIALOGUE CAST gets displaced (see Dialogue_Handler.rpy).
    # Free-roaming room NPCs are never moved by the menu - they don't
    # belong to the conversation, so they don't get involved.
    #
    # For each menu side we define the TARGET ZONES the cast slides into:
    #
    #   menu (side="left")   -> cast is pushed to the right zone
    #   menu (side="right")  -> cast is pushed to the left zone
    #   menu (side="middle") -> each cast member slides AWAY from center on
    #                          whichever side they're already on
    #                          (left half  -> 0.10..0.25,
    #                           right half -> 0.75..0.90)
    #
    # When two or more cast members would land in the same zone, they're
    # spread evenly inside it so they keep a clean gap.
    CHOICE_MENU_WIDTH    = 720
    CHOICE_XALIGN_LEFT   = 0.20
    CHOICE_XALIGN_MIDDLE = 0.50
    CHOICE_XALIGN_RIGHT  = 0.80

    DISPLACE_LEFT_ZONE_RIGHT  = (0.65, 0.75)   # menu on left -> cast goes here
    DISPLACE_RIGHT_ZONE_LEFT  = (0.25, 0.35)   # menu on right -> cast goes here
    DISPLACE_MIDDLE_ZONE_L    = (0.10, 0.25)   # menu in middle, left-half cast
    DISPLACE_MIDDLE_ZONE_R    = (0.75, 0.90)   # menu in middle, right-half cast
    MENU_DISPLACE_SECONDS     = 0.25

    def _animated_xalign_fn(trans, st, at):
        start = getattr(trans, "_xa_start", 0.5)
        end = getattr(trans, "_xa_end", 0.5)
        duration = getattr(trans, "_xa_duration", 0.0)
        if duration <= 0 or st >= duration:
            trans.xalign = end
            return None
        frac = st / duration
        frac = frac * frac * (3.0 - 2.0 * frac)
        trans.xalign = start + (end - start) * frac
        return 0

    def _xalign_anim(start, end, yalign=1.0, zoom=0.5, duration=None):
        t = Transform(function=_animated_xalign_fn, yalign=yalign, zoom=zoom)
        t._xa_start = start
        t._xa_end = end
        t._xa_duration = MENU_DISPLACE_SECONDS if duration is None else duration
        return t

    def _spread_in_zone(n, lo, hi):
        if n <= 0:
            return []
        if n == 1:
            return [(lo + hi) / 2.0]
        step = (hi - lo) / float(n - 1)
        return [lo + i * step for i in range(n)]

    def _compute_displacement_targets(side):
        # Returns {char_id: target_xalign} for every cast member that needs
        # to move when the menu pops on `side`.
        cast = store._dialogue_cast
        if not cast or side not in ("left", "right", "middle"):
            return {}

        members = list(cast.keys())
        targets = {}

        if side == "left":
            ordered = sorted(members, key=lambda c: cast[c].get("xalign", 0.5), reverse=True)
            xs = list(reversed(_spread_in_zone(len(ordered), *DISPLACE_LEFT_ZONE_RIGHT)))
            for cid, x in zip(ordered, xs):
                targets[cid] = x

        elif side == "right":
            ordered = sorted(members, key=lambda c: cast[c].get("xalign", 0.5))
            xs = _spread_in_zone(len(ordered), *DISPLACE_RIGHT_ZONE_LEFT)
            for cid, x in zip(ordered, xs):
                targets[cid] = x

        else:  # middle
            def _middle_basis(c):
                x = cast[c].get("xalign", 0.5)
                if abs(x - 0.5) < 0.001:
                    return cast[c].get("origin_x", x)
                return x
            lefts  = [c for c in members if _middle_basis(c) <  0.5]
            rights = [c for c in members if _middle_basis(c) >= 0.5]
            lefts.sort(key=lambda c: cast[c].get("xalign", 0.5))
            rights.sort(key=lambda c: cast[c].get("xalign", 0.5))
            lxs = _spread_in_zone(len(lefts),  *DISPLACE_MIDDLE_ZONE_L)
            rxs = _spread_in_zone(len(rights), *DISPLACE_MIDDLE_ZONE_R)
            for cid, x in zip(lefts, lxs):
                targets[cid] = x
            for cid, x in zip(rights, rxs):
                targets[cid] = x

        return targets

    def _apply_menu_displacement(side, force=False):
        # Move every dialogue-cast member to its target xalign for `side` by
        # temporarily marking them manual and reusing the core layout engine.
        if side not in ("left", "right", "middle"):
            return
        if force and store._menu_displaced:
            _restore_menu_displacement()
        cast = store._dialogue_cast
        if not cast:
            store._menu_debug_state = {
                "requested_side": side,
                "displace": True,
                "cast_before": [],
                "targets": {},
                "moved": [],
                "restored": [],
                "notes": "No dialogue cast to displace.",
            }
            return

        targets = _compute_displacement_targets(side)
        store._menu_debug_state = {
            "requested_side": side,
            "displace": True,
            "cast_before": list(cast.keys()),
            "targets": dict(targets),
            "moved": [],
            "restored": [],
            "notes": "",
        }
        store._menu_displaced[:] = []
        moved = 0

        for cid, target_x in targets.items():
            info = cast.get(cid)
            if not info:
                continue
            cur_x = info.get("xalign", info.get("shown_xalign", 0.5))
            if abs(target_x - cur_x) < 0.001:
                continue
            store._menu_displaced.append({
                "cid": cid,
                "xalign": cur_x,
                "manual": bool(info.get("manual")),
                "shown_xalign": info.get("shown_xalign", cur_x),
            })
            info["manual"] = True
            info["xalign"] = target_x
            store._menu_debug_state["moved"].append(cid)
            moved += 1

        if moved:
            _layout_dialogue_cast(transition=False, animate=True)
        else:
            store._menu_debug_state["notes"] = "Targets matched current cast positions."

    def _choice_prepare_menu_side(side, displace=True):
        try:
            _sync_dialogue_cast_from_layer()
        except Exception:
            store._menu_debug_state = {
                "requested_side": side,
                "displace": bool(displace),
                "cast_before": [],
                "targets": {},
                "moved": [],
                "restored": [],
                "notes": renpy.exception_only(),
            }
        if side and displace:
            _apply_menu_displacement(side, force=True)

    def _restore_menu_displacement():
        # Restore every cast member to the exact xalign/manual flag recorded
        # before the menu displacement.
        displaced_snapshot = [entry for entry in store._menu_displaced if isinstance(entry, dict)]
        changed = False
        for entry in displaced_snapshot:
            cid = entry.get("cid")
            if not cid:
                continue
            info = store._dialogue_cast.get(cid)
            if not info:
                continue
            original_x = entry.get("xalign")
            if isinstance(original_x, (int, float)):
                info["xalign"] = original_x
                changed = True
            info["manual"] = bool(entry.get("manual", False))
            shown_before = entry.get("shown_xalign", original_x if isinstance(original_x, (int, float)) else info.get("shown_xalign", 0.5))
            info["shown_xalign"] = shown_before
            store._menu_debug_state.setdefault("restored", []).append(cid)
        if changed:
            _layout_dialogue_cast(transition=False, animate=True)
        store._menu_displaced[:] = []

    def _animated_xoffset_fn(trans, st, at):
        # Legacy helper kept so old saves that reference _xoffset_anim can
        # still unpickle. New menu displacement no longer uses it.
        start = getattr(trans, "_xo_start", 0)
        end = getattr(trans, "_xo_end", 0)
        duration = getattr(trans, "_xo_duration", 0.0)
        if duration <= 0:
            trans.xoffset = end
            return None
        if st >= duration:
            trans.xoffset = end
            return None
        frac = st / duration
        trans.xoffset = start + (end - start) * frac
        return 0

    def _xoffset_anim(start, end, duration):
        t = Transform(function=_animated_xoffset_fn)
        t._xo_start = start
        t._xo_end = end
        t._xo_duration = duration
        return t

    def _menu_consume_side():
        # Read AND clear so the next plain menu doesn't inherit the side.
        s = store._menu_side
        d = store._menu_displace
        store._menu_side     = None
        store._menu_displace = True
        return s, d

    def _normalize_menu_side(v):
        if not isinstance(v, str):
            return None
        v = v.strip().lower()
        if v in ("left", "right", "middle"):
            return v
        return None


# =============================================================================
# Choice screen override
# -----------------------------------------------------------------------------
# Runs at init 110 so it overrides Ren'Py's default `screen choice` AND the
# simpler one defined in Engine/Common/Screens.rpy.
# =============================================================================
init 110:

    # Signature uses *args/**kwargs so that BOTH of these are valid:
    #   menu:                    -> kwargs={"items": [...]},  args=()
    #   menu("left"):            -> kwargs={"items": [...]},  args=("left",)
    #   menu(side="left"):       -> kwargs={"items": [...], "side": "left"}
    # The default screen sig `(items, side=None)` collides because Ren'Py
    # passes `items` as a kwarg AND `"left"` as a positional, which both
    # try to bind to the first parameter.
    screen choice(*args, **kwargs):
        zorder 50
        on "hide" action Function(_restore_menu_displacement)

        $ items = kwargs.pop("items", [])

        # Read once per show. `default` captures on first render so the value
        # survives re-renders (hover, etc) without being consumed again.
        default _side_pair   = _menu_consume_side()
        default _choice_prepared = False
        $ _pos_side          = (args[0] if args else None) if choice_menu_side_arg_enabled else None
        $ _kw_side           = kwargs.get("side")
        $ _kw_displace       = kwargs.get("displace", None)
        $ _arg_side          = _normalize_menu_side(_pos_side) or _normalize_menu_side(_kw_side)
        $ _side              = _arg_side or _side_pair[0]
        $ _do_displace       = (bool(_kw_displace) if _kw_displace is not None else (_side_pair[1] if _side_pair[0] else True))

        if _side and not _choice_prepared:
            $ _choice_prepare_menu_side(_side, _do_displace)
            $ _choice_prepared = True

        if _side == "left":
            $ _xa, _ya, _intro = CHOICE_XALIGN_LEFT,   0.50, slide_in_left
        elif _side == "right":
            $ _xa, _ya, _intro = CHOICE_XALIGN_RIGHT,  0.50, slide_in_right
        elif _side == "middle":
            $ _xa, _ya, _intro = CHOICE_XALIGN_MIDDLE, 0.50, fade_in
        else:
            $ _xa, _ya, _intro = CHOICE_XALIGN_MIDDLE, 0.50, fade_in

        vbox:
            xalign _xa
            yalign _ya
            spacing 16
            at _intro
            for idx, i in enumerate(items):
                button:
                    xsize CHOICE_MENU_WIDTH
                    background "#ffffff66"
                    hover_background "#ffd27a"
                    xpadding 2
                    ypadding 2
                    action [
                        Function(_auto_record_choice, idx + 1),
                        Function(_restore_menu_displacement),
                        i.action,
                    ]
                    frame:
                        background None
                        xsize (CHOICE_MENU_WIDTH - 4)
                        xpadding 24
                        ypadding 16
                        text "[i.caption]":
                            size 28
                            color "#ffffff"
                            outlines [(2, "#000000", 0, 0)]
                            xalign 0.5
                            text_align 0.5
