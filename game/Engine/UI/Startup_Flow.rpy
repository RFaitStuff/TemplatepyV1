# =============================================================================
# Startup Flow
# =============================================================================
# Registry-driven startup notices: content warnings, photosensitivity warnings,
# build notices, or template-specific gates. Entries can be remembered through
# persistent data so the player is not nagged every launch.
# =============================================================================


default persistent.startup_screens_seen = set()


init -15 python:
    startup_screen_defs = []

    def startup_screen(screen_id, title=None, body=None, remember=True, requires=None, kind="notice", **extra):
        data = {
            "id": screen_id,
            "title": title or str(screen_id).replace("_", " ").title(),
            "body": body or "",
            "remember": remember,
            "requires": requires,
            "kind": kind,
        }
        data.update(extra)
        for index, old in enumerate(startup_screen_defs):
            if old.get("id") == screen_id:
                startup_screen_defs[index] = data
                return data
        startup_screen_defs.append(data)
        return data

    def visible_startup_screens():
        rows = []
        seen = getattr(persistent, "startup_screens_seen", set())
        if not isinstance(seen, set):
            persistent.startup_screens_seen = set(seen or [])
            seen = persistent.startup_screens_seen
        for entry in startup_screen_defs:
            if entry.get("remember") and entry.get("id") in seen:
                continue
            requirement = entry.get("requires")
            if requirement:
                try:
                    if not meets_requirements(requirement):
                        continue
                except Exception:
                    continue
            rows.append(entry)
        return rows

    def reset_startup_screens():
        persistent.startup_screens_seen = set()
        try:
            renpy.notify("Startup notices reset.")
        except Exception:
            pass
        return None


label run_startup_screens:
    $ _startup_rows = visible_startup_screens()
    while _startup_rows:
        $ _startup_entry = _startup_rows.pop(0)
        call screen startup_notice(_startup_entry)
        if _startup_entry.get("remember"):
            $ persistent.startup_screens_seen.add(_startup_entry.get("id"))
    return


screen startup_notice(entry):
    tag startup_notice
    modal True
    zorder 1000
    add "#05040bee"
    frame:
        align (0.5, 0.5)
        xmaximum 840
        background "#11131ff2"
        padding (42, 34)
        vbox:
            spacing 20
            text entry.get("title", "Notice"):
                xalign 0.5
                text_align 0.5
                size 40
                color "#ff8de7"
            if entry.get("body"):
                text entry.get("body"):
                    xalign 0.5
                    text_align 0.5
                    size 22
                    color "#f5edf7"
                    line_spacing 6
            hbox:
                xalign 0.5
                spacing 18
                textbutton entry.get("continue_text", "Continue"):
                    text_size 24
                    background "#623c91dd"
                    hover_background "#7a4cb0dd"
                    padding (24, 12)
                    action Return(True)
                if entry.get("allow_quit", False):
                    textbutton entry.get("quit_text", "Quit"):
                        text_size 24
                        background "#292b38dd"
                        hover_background "#3d4050dd"
                        padding (24, 12)
                        action Quit(confirm=False)
