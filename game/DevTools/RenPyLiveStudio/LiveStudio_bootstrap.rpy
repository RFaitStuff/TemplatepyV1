# Entry point and developer key binding.

init 900 python in live_studio:
    def open_editor():
        if not config.developer:
            renpy.notify("Live Studio is only available in developer mode")
            return

        begin_capture_project("Captured Scene")
        generate_exports()
        refresh_assets()

        window_value = getattr(renpy.store, "_window", None)
        skipping_value = getattr(renpy.store, "_skipping", None)
        quick_menu_value = getattr(renpy.store, "quick_menu", None)

        try:
            if hasattr(renpy.store, "_window"):
                renpy.store._window = False
            if hasattr(renpy.store, "_skipping"):
                renpy.store._skipping = False
            if hasattr(renpy.store, "quick_menu"):
                renpy.store.quick_menu = False
            renpy.call_screen("live_studio_editor", _with_none=False, _mode="screen")
        finally:
            if hasattr(renpy.store, "_window"):
                renpy.store._window = window_value
            if hasattr(renpy.store, "_skipping"):
                renpy.store._skipping = skipping_value
            if hasattr(renpy.store, "quick_menu"):
                renpy.store.quick_menu = quick_menu_value
            runtime["drag"] = None

    def open_editor_in_new_context():
        renpy.invoke_in_new_context(open_editor)

init 910 python:
    if config.developer:
        config.keymap.setdefault("live_studio", [live_studio.OPEN_KEY])
        if live_studio.OPEN_KEY not in config.keymap["live_studio"]:
            config.keymap["live_studio"].append(live_studio.OPEN_KEY)
        config.underlay.append(renpy.Keymap(live_studio=live_studio.open_editor_in_new_context))
