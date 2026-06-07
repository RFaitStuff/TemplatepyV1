# =============================================================================
# Engine/UI/Choice.rpy - side-aware choice menus and dialogue displacement
# =============================================================================
# Author syntax:
#
#     menu (side="left"):
#         "Choice":
#             ...
#
# or:
#
#     $ menu_side("left")
#     menu:
#         "Choice":
#             ...
#
# The helper only queues the request. The actual displacement occurs from the
# choice screen's show event, never while the screen is being predicted/evaluated.
# =============================================================================


default _menu_side = None
default _menu_displace = True
default _menu_displaced = []
default _menu_debug_state = {}
default _choice_hover_idx = -1
default left = "left"
default right = "right"
default middle = "middle"

define choice_menu_side_arg_enabled = True


init python:

    CHOICE_MENU_WIDTH = 720
    CHOICE_XALIGN_LEFT = 0.20
    CHOICE_XALIGN_MIDDLE = 0.50
    CHOICE_XALIGN_RIGHT = 0.80

    # A menu on the left only moves cast members that currently overlap the
    # left/menu region. The one-character target is exactly 0.70.
    DISPLACE_LEFT_TRIGGER = 0.60
    DISPLACE_LEFT_ZONE_RIGHT = (0.65, 0.75)

    # Mirrored values for a menu on the right.
    DISPLACE_RIGHT_TRIGGER = 0.40
    DISPLACE_RIGHT_ZONE_LEFT = (0.25, 0.35)

    # A middle menu only moves cast members in the central collision band.
    DISPLACE_MIDDLE_TRIGGER_L = 0.36
    DISPLACE_MIDDLE_TRIGGER_R = 0.64
    DISPLACE_MIDDLE_ZONE_L = (0.10, 0.25)
    DISPLACE_MIDDLE_ZONE_R = (0.75, 0.90)

    MENU_DISPLACE_SECONDS = 0.25


    def _normalize_menu_side(value):
        if not isinstance(value, str):
            return None
        value = value.strip().lower()
        if value in ("left", "right", "middle"):
            return value
        return None


    def menu_side(side, displace=True):
        """Queues the side for the next menu without touching the scene list."""
        side = _normalize_menu_side(side)
        store._menu_side = side
        store._menu_displace = bool(displace)
        store._menu_debug_state = {
            "phase": "queued",
            "requested_side": side,
            "displace": bool(displace),
            "cast_before": list(getattr(store, "_dialogue_cast", {}).keys()),
            "positions_before": {},
            "targets": {},
            "moved": [],
            "skipped": [],
            "restored": [],
            "notes": "Waiting for the choice screen show event.",
        }
        return None


    # -------------------------------------------------------------------------
    # Compatibility transform helpers.
    #
    # Do not attach custom values to a Transform object. renpy.show() calls a
    # Transform as a factory and arbitrary attributes do not survive that copy.
    # Curry the values into the callback instead.
    # -------------------------------------------------------------------------

    def _animated_xalign_fn(*args):
        # Old saves may contain the former 3-argument callback and custom
        # Transform fields. Accept both forms so those saves still load.
        if len(args) == 3:
            trans, st, at = args
            start = getattr(trans, "_xa_start", 0.5)
            end = getattr(trans, "_xa_end", 0.5)
            duration = getattr(trans, "_xa_duration", 0.0)
        else:
            start, end, duration, trans, st, at = args
        if duration <= 0.0 or st >= duration:
            trans.xalign = end
            return None
        frac = max(0.0, min(1.0, st / duration))
        frac = frac * frac * (3.0 - 2.0 * frac)
        trans.xalign = start + (end - start) * frac
        return 0


    def _xalign_anim(start, end, yalign=1.0, zoom=0.5, duration=None):
        duration = MENU_DISPLACE_SECONDS if duration is None else float(duration)
        return Transform(
            function=renpy.curry(_animated_xalign_fn)(float(start), float(end), duration),
            reset=True,
            yalign=yalign,
            zoom=zoom,
        )


    def _animated_xoffset_fn(*args):
        if len(args) == 3:
            trans, st, at = args
            start = getattr(trans, "_xo_start", 0)
            end = getattr(trans, "_xo_end", 0)
            duration = getattr(trans, "_xo_duration", 0.0)
        else:
            start, end, duration, trans, st, at = args
        if duration <= 0.0 or st >= duration:
            trans.xoffset = end
            return None
        frac = max(0.0, min(1.0, st / duration))
        trans.xoffset = start + (end - start) * frac
        return 0


    def _xoffset_anim(start, end, duration):
        return Transform(
            function=renpy.curry(_animated_xoffset_fn)(start, end, float(duration)),
            reset=True,
        )


    def _spread_in_zone(count, lo, hi):
        if count <= 0:
            return []
        if count == 1:
            return [(lo + hi) / 2.0]
        step = (hi - lo) / float(count - 1)
        return [lo + i * step for i in range(count)]


    def _menu_member_x(info):
        value = info.get("xalign", info.get("shown_xalign", 0.5))
        try:
            return float(value)
        except Exception:
            return 0.5


    def _menu_member_can_move(cid, info):
        # dialogue_place/manual placement intentionally pins a character.
        if info.get("menu_locked") or info.get("manual"):
            return False
        return True


    def _compute_displacement_targets(side):
        """Returns targets only for cast members that collide with the menu."""
        cast = getattr(store, "_dialogue_cast", {})
        if not isinstance(cast, dict) or not cast or side not in ("left", "right", "middle"):
            return {}

        movable = [
            cid for cid, info in cast.items()
            if isinstance(info, dict) and _menu_member_can_move(cid, info)
        ]
        targets = {}

        if side == "left":
            candidates = [cid for cid in movable if _menu_member_x(cast[cid]) < DISPLACE_LEFT_TRIGGER]
            candidates.sort(key=lambda cid: _menu_member_x(cast[cid]), reverse=True)
            slots = list(reversed(_spread_in_zone(len(candidates), *DISPLACE_LEFT_ZONE_RIGHT)))
            targets.update(zip(candidates, slots))

        elif side == "right":
            candidates = [cid for cid in movable if _menu_member_x(cast[cid]) > DISPLACE_RIGHT_TRIGGER]
            candidates.sort(key=lambda cid: _menu_member_x(cast[cid]))
            slots = _spread_in_zone(len(candidates), *DISPLACE_RIGHT_ZONE_LEFT)
            targets.update(zip(candidates, slots))

        else:
            candidates = [
                cid for cid in movable
                if DISPLACE_MIDDLE_TRIGGER_L < _menu_member_x(cast[cid]) < DISPLACE_MIDDLE_TRIGGER_R
            ]

            def middle_basis(cid):
                x = _menu_member_x(cast[cid])
                if abs(x - 0.5) < 0.001:
                    try:
                        return float(cast[cid].get("origin_x", x))
                    except Exception:
                        return x
                return x

            left_members = [cid for cid in candidates if middle_basis(cid) < 0.5]
            right_members = [cid for cid in candidates if middle_basis(cid) >= 0.5]
            left_members.sort(key=lambda cid: _menu_member_x(cast[cid]))
            right_members.sort(key=lambda cid: _menu_member_x(cast[cid]))
            targets.update(zip(left_members, _spread_in_zone(len(left_members), *DISPLACE_MIDDLE_ZONE_L)))
            targets.update(zip(right_members, _spread_in_zone(len(right_members), *DISPLACE_MIDDLE_ZONE_R)))

        return dict(targets)


    def _apply_menu_displacement(side, force=False):
        side = _normalize_menu_side(side)
        if side is None:
            return None

        if force and store._menu_displaced:
            _restore_menu_displacement(restart=False)

        cast = getattr(store, "_dialogue_cast", {})
        if not isinstance(cast, dict) or not cast:
            store._menu_debug_state = {
                "phase": "prepared",
                "requested_side": side,
                "displace": True,
                "cast_before": [],
                "positions_before": {},
                "targets": {},
                "moved": [],
                "skipped": [],
                "restored": [],
                "notes": "No dialogue cast to displace.",
            }
            return None

        positions_before = {
            cid: _menu_member_x(info)
            for cid, info in cast.items()
            if isinstance(info, dict)
        }
        targets = _compute_displacement_targets(side)
        skipped = []
        for cid, info in cast.items():
            if not isinstance(info, dict):
                continue
            if cid not in targets and (info.get("manual") or info.get("menu_locked")):
                skipped.append(cid + " (pinned)")

        store._menu_debug_state = {
            "phase": "prepared",
            "requested_side": side,
            "displace": True,
            "cast_before": list(cast.keys()),
            "positions_before": positions_before,
            "targets": dict(targets),
            "moved": [],
            "skipped": skipped,
            "restored": [],
            "notes": "",
        }
        store._menu_displaced[:] = []

        for cid, target_x in targets.items():
            info = cast.get(cid)
            if not isinstance(info, dict):
                continue
            current_x = _menu_member_x(info)
            if abs(float(target_x) - current_x) < 0.001:
                continue

            store._menu_displaced.append({
                "cid": cid,
                "xalign": current_x,
                "yalign": info.get("yalign", 1.0),
                "manual": bool(info.get("manual")),
                "menu_locked": bool(info.get("menu_locked")),
                "shown_xalign": info.get("shown_xalign", current_x),
            })
            info["manual"] = True
            info["menu_locked"] = False
            info["xalign"] = float(target_x)
            store._menu_debug_state["moved"].append(cid)

        if store._menu_displaced:
            _layout_dialogue_cast(transition=False, animate=True)
            store._menu_debug_state["notes"] = "Displacement submitted to the dialogue renderer."
        elif not targets:
            store._menu_debug_state["notes"] = "No unpinned cast member overlapped the selected menu region."
        else:
            store._menu_debug_state["notes"] = "Targets already matched current positions."

        renpy.restart_interaction()
        return None


    def _choice_prepare_menu_side(side, displace=True):
        """Runs once from the choice screen's show event."""
        side = _normalize_menu_side(side)

        # Consume any queued helper request now that the real screen is showing.
        store._menu_side = None
        store._menu_displace = True

        try:
            _sync_dialogue_cast_from_layer()
        except Exception:
            store._menu_debug_state = {
                "phase": "error",
                "requested_side": side,
                "displace": bool(displace),
                "cast_before": [],
                "positions_before": {},
                "targets": {},
                "moved": [],
                "skipped": [],
                "restored": [],
                "notes": renpy.exception_only(),
            }
            return None

        if side and displace:
            return _apply_menu_displacement(side, force=True)

        store._menu_debug_state = {
            "phase": "prepared",
            "requested_side": side,
            "displace": bool(displace),
            "cast_before": list(getattr(store, "_dialogue_cast", {}).keys()),
            "positions_before": {
                cid: _menu_member_x(info)
                for cid, info in getattr(store, "_dialogue_cast", {}).items()
                if isinstance(info, dict)
            },
            "targets": {},
            "moved": [],
            "skipped": [],
            "restored": [],
            "notes": "Menu displayed without cast displacement.",
        }
        return None


    def _restore_menu_displacement(restart=True):
        """Restores the original cast state and animates from the displaced x."""
        snapshot = [entry for entry in store._menu_displaced if isinstance(entry, dict)]
        changed = False

        for entry in snapshot:
            cid = entry.get("cid")
            info = getattr(store, "_dialogue_cast", {}).get(cid)
            if not cid or not isinstance(info, dict):
                continue

            original_x = entry.get("xalign")
            if isinstance(original_x, (int, float)):
                info["xalign"] = float(original_x)
                changed = True
            info["yalign"] = entry.get("yalign", info.get("yalign", 1.0))
            info["manual"] = bool(entry.get("manual", False))
            info["menu_locked"] = bool(entry.get("menu_locked", False))

            # Do not overwrite shown_xalign before layout. It must remain at the
            # displaced target so dialogue_move_to animates back from that point.
            store._menu_debug_state.setdefault("restored", []).append(cid)

        store._menu_displaced[:] = []
        if changed:
            store._menu_debug_state["phase"] = "restoring"
            _layout_dialogue_cast(transition=False, animate=True)
            store._menu_debug_state["phase"] = "restored"

        if restart:
            renpy.restart_interaction()
        return None


# =============================================================================
# Choice screen override
# =============================================================================
init 110:

    screen choice(*args, **kwargs):
        zorder 50

        $ items = kwargs.get("items", [])

        # Local defaults are safe to evaluate repeatedly; no scene state is
        # changed until the show event runs.
        default _queued_side = _normalize_menu_side(_menu_side)
        default _queued_displace = bool(_menu_displace)

        $ _pos_side = (args[0] if args else None) if choice_menu_side_arg_enabled else None
        $ _kw_side = kwargs.get("side")
        $ _kw_displace = kwargs.get("displace", None)
        $ _argument_side = _normalize_menu_side(_pos_side) or _normalize_menu_side(_kw_side)
        $ _side = _argument_side or _queued_side
        $ _do_displace = bool(_kw_displace) if _kw_displace is not None else _queued_displace

        on "show" action Function(_choice_prepare_menu_side, _side, _do_displace)
        on "hide" action Function(_restore_menu_displacement)

        if _side == "left":
            $ _xa, _ya, _intro = CHOICE_XALIGN_LEFT, 0.50, slide_in_left
        elif _side == "right":
            $ _xa, _ya, _intro = CHOICE_XALIGN_RIGHT, 0.50, slide_in_right
        elif _side == "middle":
            $ _xa, _ya, _intro = CHOICE_XALIGN_MIDDLE, 0.50, fade_in
        else:
            $ _xa, _ya, _intro = CHOICE_XALIGN_MIDDLE, 0.50, fade_in

        vbox:
            xalign _xa
            yalign _ya
            spacing 16
            at _intro

            for idx, item in enumerate(items):
                button:
                    xsize CHOICE_MENU_WIDTH
                    background "#ffffff66"
                    hover_background "#ffd27a"
                    xpadding 2
                    ypadding 2
                    action [
                        Function(_auto_record_choice, idx + 1),
                        Function(_restore_menu_displacement),
                        item.action,
                    ]

                    frame:
                        background None
                        xsize (CHOICE_MENU_WIDTH - 4)
                        xpadding 24
                        ypadding 16

                        text "[item.caption]":
                            size 28
                            color "#ffffff"
                            outlines [(2, "#000000", 0, 0)]
                            xalign 0.5
                            text_align 0.5
