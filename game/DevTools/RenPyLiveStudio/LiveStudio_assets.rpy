# Asset index used by the bottom Unity-like asset browser.

init -860 python in live_studio:
    asset_cache = None
    audio_cache = None
    asset_filter = ""
    asset_category = "images"

    def refresh_assets():
        global asset_cache, audio_cache
        images = []
        try:
            values = list(renpy.list_images())
        except Exception:
            values = []
        for value in values:
            name = " ".join(value) if isinstance(value, (tuple, list)) else str(value)
            if not name:
                continue
            images.append({
                "name": name,
                "parts": list(value) if isinstance(value, (tuple, list)) else [name],
                "tag": name.split()[0],
                "kind": "image",
            })
        images.sort(key=lambda item: item.get("name", "").lower())

        audio = []
        try:
            files = list(renpy.list_files())
        except Exception:
            files = []
        for filename in files:
            lower = filename.lower()
            if lower.endswith((".ogg", ".opus", ".mp3", ".wav", ".flac", ".webm")):
                audio.append({"name": filename, "kind": "audio"})
        audio.sort(key=lambda item: item.get("name", "").lower())

        asset_cache = images
        audio_cache = audio
        restart()
        return images

    def set_asset_category(value):
        global asset_category
        asset_category = str(value or "images")
        restart()

    def assets():
        if asset_cache is None or audio_cache is None:
            refresh_assets()
        values = audio_cache if asset_category == "audio" else asset_cache
        query = str(asset_filter or "").strip().lower()
        if not query:
            return list(values or [])
        return [item for item in (values or []) if query in item.get("name", "").lower()]

    def set_asset_filter(value):
        global asset_filter
        asset_filter = str(value or "")
        restart()

    def asset_filter_changed(value):
        set_asset_filter(value)

    def asset_displayable(name):
        try:
            return renpy.displayable(name)
        except Exception:
            return None

    def add_asset_to_current_context(asset_name):
        if not asset_name:
            return
        if str(selected_tree_tab).lower() == "ui":
            screen = selected_item()[0] if selected_item()[2] == "ui_screen" else None
            add_ui_image(asset_name, screen_id=screen.get("id") if screen else None)
        else:
            add_image_to_scene(asset_name)
        set_bottom_tab("Assets")
