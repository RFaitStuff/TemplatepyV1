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

    $ _def = get_interactable(iid) or {"title": iid, "actions": []}
    $ _actions = interactable_actions(iid, only_available=not bool(getattr(store, "debug_all_actions_visible", False)))

    # Transparent click-away area. The menu itself appears above the clicked
    # thing, not in the middle of the screen.
    button:
        action Hide("action_menu")
        background "#00000000"
        xfill True
        yfill True

    frame:
        xalign pos[0]
        yalign pos[1]
        yoffset -170
        background "#1a1a1aee"
        padding (24, 20)
        xminimum 320
        at pop_in
        vbox:
            spacing 10
            text "[_def[\"title\"]]" size 22 color "#ffd27a" xalign 0.5

            if not _actions:
                text "(Nothing to do here right now.)" size 14 color "#888888" italic True
            else:
                for _a in _actions:
                    $ _seen = action_is_darkened(iid, _a)
                    button:
                        xminimum 280
                        ypadding 10
                        xpadding 14
                        background ("#171717" if _seen else "#222222")
                        hover_background "#333333"
                        action [
                            Hide("action_menu"),
                            Function(_run_interactable_action, iid, _a),
                        ]
                        hbox:
                            spacing 12
                            if _a.get("icon"):
                                add _a["icon"] xysize (32, 32) yalign 0.5
                            text _a["title"] size 18 color ("#888888" if _seen else "#ffffff") yalign 0.5
                            if _seen:
                                text "(quiet)" size 12 color "#666666" yalign 0.5

            null height 6
            textbutton "Cancel" xalign 0.5 action Hide("action_menu") text_size 14
