# Entry point and shortcut registration. Live Studio works when a project is
# launched normally from the Ren'Py SDK; it does not require manually setting
# config.developer.

init 900 python in live_studio:
    def compatible_renpy_version():
        try:
            return tuple(renpy.version_tuple[:3]) >= tuple(MIN_RENPY_VERSION)
        except Exception:
            return True

    def enabled_for_this_run():
        if not ENABLED:
            return False
        if REQUIRE_DEVELOPER and not bool(getattr(config, "developer", False)):
            return False
        return True

    def _prepare_open_capture():
        # The shortcut records this in the original game context before
        # invoke_in_new_context creates the modal editor context.
        source = clone(runtime.get("preopen_source") or capture_source_reference())
        if not isinstance(project_data, dict) or not project_data.get("frames"):
            begin_capture_project("Captured Ren'Py Project", source, keep_snapshot=True)
            return

        # Refresh runtime-only references every time the editor opens.
        current = current_frame() or {}
        current_source = current.get("source_ref") or resolve_frame().get("source_ref", {})
        if source_reference_key(source) != source_reference_key(current_source):
            append_runtime_capture_as_frame(source.get("label") or "Runtime Capture", connect=True, source_override=source, keep_snapshot=True)
        else:
            runtime["capture_source"] = source
            refresh_runtime_preview_references(keep_snapshot=True)

    def open_editor():
        if not enabled_for_this_run():
            renpy.notify("Live Studio is disabled")
            return
        if not compatible_renpy_version():
            renpy.notify("Live Studio requires Ren'Py {} or newer".format(".".join(str(i) for i in MIN_RENPY_VERSION)))
            return

        _prepare_open_capture()
        generate_exports()
        refresh_assets()
        refresh_source_flow_candidates()

        window_value = getattr(renpy.store, "_window", None)
        skipping_value = getattr(renpy.store, "_skipping", None)
        quick_menu_exists = hasattr(renpy.store, "quick_menu")
        quick_menu_value = getattr(renpy.store, "quick_menu", None)
        runtime["opened"] = True

        try:
            if hasattr(renpy.store, "_window"):
                renpy.store._window = False
            if hasattr(renpy.store, "_skipping"):
                renpy.store._skipping = False
            if quick_menu_exists:
                renpy.store.quick_menu = False
            renpy.call_screen("live_studio_editor", _with_none=False)
        finally:
            if hasattr(renpy.store, "_window"):
                renpy.store._window = window_value
            if hasattr(renpy.store, "_skipping"):
                renpy.store._skipping = skipping_value
            if quick_menu_exists:
                renpy.store.quick_menu = quick_menu_value
            runtime["drag"] = None
            runtime["opened"] = False

    def open_editor_in_new_context():
        # Capture source/screenshot before entering a new context. The new
        # context is opened without clearing layers so active UI remains
        # available for widget-tree capture.
        runtime["preopen_source"] = capture_source_reference()
        try:
            runtime["source_origin_name"] = renpy.game.context().current
        except Exception:
            runtime["source_origin_name"] = None
        capture_exact_snapshot()
        try:
            renpy.invoke_in_new_context(open_editor, _clear_layers=False)
        finally:
            runtime.pop("preopen_source", None)
            runtime.pop("source_origin_name", None)

init 910 python:
    if live_studio.ENABLED:
        config.keymap.setdefault("live_studio", [])
        if live_studio.OPEN_KEY not in config.keymap["live_studio"]:
            config.keymap["live_studio"].append(live_studio.OPEN_KEY)
        # Init blocks run once per launch, so this is installed exactly once.
        config.underlay.append(renpy.Keymap(live_studio=live_studio.open_editor_in_new_context))
