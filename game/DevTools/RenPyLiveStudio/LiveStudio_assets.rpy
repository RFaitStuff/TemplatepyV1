# Lightweight asset index. It intentionally avoids animation and ATL concerns.

init -860 python in live_studio:
    asset_cache = None
    asset_filter = ""

    def refresh_assets():
        global asset_cache
        images = []
        try:
            values = list(renpy.list_images())
        except Exception:
            values = []
        for value in values:
            name = " ".join(value) if isinstance(value, (tuple, list)) else str(value)
            images.append({
                "name": name,
                "parts": list(value) if isinstance(value, (tuple, list)) else [name],
                "tag": name.split()[0] if name else "image",
            })
        images.sort(key=lambda item: item.get("name", "").lower())
        asset_cache = images
        renpy.restart_interaction()
        return images

    def assets():
        if asset_cache is None:
            refresh_assets()
        query = str(asset_filter or "").strip().lower()
        if not query:
            return list(asset_cache or [])
        return [item for item in (asset_cache or []) if query in item.get("name", "").lower()]

    def set_asset_filter(value):
        global asset_filter
        asset_filter = str(value or "")
        renpy.restart_interaction()

    def asset_filter_changed(value):
        set_asset_filter(value)

    def asset_displayable(name):
        try:
            return renpy.displayable(name)
        except Exception:
            return None
