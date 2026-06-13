# =============================================================================
# Engine/UI/Action_Menu.rpy - the action wheel popup
# -----------------------------------------------------------------------------
# Shown when the smart-mode resolver decides the player has more than one
# meaningful choice for an interactable. Lists every available action and
# runs it on click (after marking it seen so smart-mode can skip the wheel
# next time).
#
# Look-and-feel is intentionally minimal so it'll still work before final
# UI assets land. Replace the frame background / button styles to skin it.
# =============================================================================


screen action_menu(iid, pos=(0.5, 0.5)):
    tag popup
    modal True
    zorder 220

    if interface_hidden:
        timer 0.01 action Hide("action_menu")

    $ _def = get_interactable(iid) or {"title": iid, "actions": []}
    $ _actions = interactable_actions(iid, only_available=False)
    $ _place = action_menu_place(pos, len(_actions))

    # Transparent click-away area. The menu itself appears above the clicked
    # thing, not in the middle of the screen.
    button:
        action Hide("action_menu")
        background "#00000000"
        xfill True
        yfill True

    frame:
        xalign _place["xalign"]
        yalign _place["yalign"]
        xoffset _place["xoffset"]
        yoffset _place["yoffset"]
        background "#1a1a1aee"
        padding (24, 20)
        xminimum 320
        xmaximum 420
        at pop_in
        vbox:
            spacing 10
            text "[_def[\"title\"]]" size 22 color "#ffd27a" xalign 0.5

            if not _actions:
                text "(Nothing to do here right now.)" size 14 color "#888888" italic True
            else:
                for _a in _actions:
                    $ _seen = action_is_darkened(iid, _a)
                    $ _lock = action_locked_reason(iid, _a)
                    $ _is_locked = bool(_lock)
                    $ _status = action_menu_status(iid, _a, _lock)
                    $ _hint = action_menu_hint(iid, _a, _lock)
                    button:
                        xminimum 280
                        ypadding 10
                        xpadding 14
                        background ("#121217" if _is_locked else ("#171717" if _seen else "#222222"))
                        hover_background ("#222232" if _is_locked else "#333333")
                        action ([Function(renpy.notify, _lock)] if _is_locked else [Hide("action_menu"), Function(_run_interactable_action, iid, _a)])
                        hbox:
                            spacing 12
                            if _a.get("icon"):
                                add _a["icon"] xysize (32, 32) yalign 0.5
                            vbox:
                                spacing 2
                                text _a["title"] size 18 color ("#666a78" if _is_locked else ("#888888" if _seen else "#ffffff"))
                                if _hint:
                                    text _hint size 12 color ("#8b779f" if _is_locked else "#8f8f9f")
                            if _status:
                                text _status size 12 color action_menu_status_color(_status) yalign 0.5

            null height 6
            textbutton "Cancel" xalign 0.5 action Hide("action_menu") text_size 14


init python:

    def action_menu_place(pos=(0.5, 0.5), action_count=0):
        x = max(0.18, min(0.82, float(pos[0] if pos else 0.5)))
        y = float(pos[1] if pos else 0.5)
        estimated_h = 112 + max(1, int(action_count)) * 54
        if y < 0.36:
            return {"xalign": x, "yalign": y, "xoffset": 0, "yoffset": 80}
        if y > 0.74:
            return {"xalign": x, "yalign": y, "xoffset": 0, "yoffset": -min(260, estimated_h)}
        return {"xalign": x, "yalign": y, "xoffset": 0, "yoffset": -min(180, estimated_h // 2)}

    def action_menu_status(iid, action, lock_reason=""):
        if lock_reason:
            return "Locked"
        aid = action.get("id")
        if action.get("once") and has_seen_action(iid, aid):
            return "Done"
        if action_first_time(iid, aid):
            return "New"
        if action_first_time_today(iid, aid):
            return "New Today"
        if action.get("repeatable", True):
            return "Again"
        return ""

    def action_menu_status_color(status):
        if status == "Locked":
            return "#7d6b8f"
        if status in ("New", "New Today"):
            return "#ffd27a"
        if status == "Done":
            return "#6f7788"
        return "#666666"

    def action_menu_hint(iid, action, lock_reason=""):
        if lock_reason:
            return lock_reason
        if action.get("tooltip"):
            return action.get("tooltip")
        if action.get("once") and not has_seen_action(iid, action.get("id")):
            return "One-time action"
        if has_seen_action(iid, action.get("id")) and action.get("repeat_hint"):
            return action.get("repeat_hint")
        return ""
