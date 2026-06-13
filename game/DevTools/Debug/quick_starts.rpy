# =============================================================================
# Debug Quick Starts
# =============================================================================
# QA presets for jumping into useful test states without replaying the whole
# opening. Presets intentionally use public engine APIs.
# =============================================================================


init -10 python:
    quick_start_defs = {}
    quick_start_order = []


init python:

    def quick_start(preset_id, title=None, desc=None, setup=None, location=None, requires=None, order=100, **extra):
        data = quick_start_defs.setdefault(preset_id, {})
        data.update({
            "id": preset_id,
            "title": title or str(preset_id).replace("_", " ").title(),
            "desc": desc or "",
            "setup": setup,
            "location": location,
            "requires": requires,
            "order": order,
        })
        data.update(extra)
        if preset_id not in quick_start_order:
            quick_start_order.append(preset_id)
        quick_start_order.sort(key=lambda key: quick_start_defs.get(key, {}).get("order", 100))
        return data

    def visible_quick_starts():
        out = []
        for preset_id in quick_start_order:
            data = quick_start_defs.get(preset_id)
            if not data:
                continue
            requires = data.get("requires")
            if requires:
                try:
                    if not meets_requirements(requires):
                        continue
                except Exception:
                    continue
            out.append(data)
        return out

    def apply_quick_start(preset_id):
        preset = quick_start_defs.get(preset_id)
        if not preset:
            renpy.notify("Missing quick start: {}".format(preset_id))
            return None

        setup = preset.get("setup")
        try:
            if callable(setup):
                setup()
            elif isinstance(setup, str) and renpy.has_label(setup):
                renpy.call_in_new_context(setup)
        except Exception as error:
            renpy.log("Quick start '{}' failed: {!r}".format(preset_id, error))
            renpy.notify("Quick start failed. See log.")
            return None

        location = preset.get("location")
        if location:
            try:
                unlock_room(location)
                goto_location(location)
            except Exception as error:
                renpy.log("Quick start location failed: {!r}".format(error))

        try:
            request_update_state("quick_start", preset=preset_id)
        except Exception:
            pass
        renpy.hide_screen("debug_tools_menu")
        renpy.jump("explore")
        return None


init 1 python:

    def _qs_archive_ready():
        set_flag("read_noticeboard")
        set_flag("complex_arc_available")
        set_flag("bree_archive_briefed")
        set_flag("archive_room_unlocked")
        set_flag("archive_evidence_decided")
        unlock_room("archive_room")
        add_item("archive_key")
        add_item("sealed_drive")
        phone_contact("bree", name="Bree", status="Archive route test.")
        phone_contact("cora", name="Cora", status="Archive route test.")

    def _qs_bree_special_ready():
        _qs_archive_ready()
        set_flag("bree_review_evidence_done")
        set_flag("bree_hallway_followup_done")
        set_flag("bree_roof_pressure_done")

    def _qs_cora_special_ready():
        _qs_archive_ready()
        set_flag("cora_cabinet_hint_done")
        set_flag("cora_front_warning_done")
        set_flag("cora_archive_afterthought_done")
        set_flag("glass_badge_checked")

    quick_start(
        "archive_ready",
        title="Archive Ready",
        desc="Noticeboard done, archive unlocked, key items added.",
        setup=_qs_archive_ready,
        location="archive_room",
        order=10,
    )
    quick_start(
        "bree_special_ready",
        title="Bree Special Ready",
        desc="All Bree archive interactions completed except the special scene.",
        setup=_qs_bree_special_ready,
        location="archive_room",
        order=20,
    )
    quick_start(
        "cora_special_ready",
        title="Cora Special Ready",
        desc="All Cora archive interactions completed except the special scene.",
        setup=_qs_cora_special_ready,
        location="archive_room",
        order=30,
    )
