init -30 python:
    asset_root = "assets"
    asset_image_roots = ("assets/images", "images")
    asset_audio_roots = ("assets/audio", "audio")
    asset_gui_root = "assets/gui"

init -20 python:
    def asset_norm(path):
        if not isinstance(path, str):
            return ""
        return path.replace("\\", "/").strip("/")

    def asset_under(path, roots):
        normalized = asset_norm(path).lower()
        for root in roots:
            root_norm = asset_norm(root).lower()
            if normalized == root_norm or normalized.startswith(root_norm + "/"):
                return True
        return False

    def asset_strip_root(path, roots):
        normalized = asset_norm(path)
        lowered = normalized.lower()
        for root in roots:
            root_norm = asset_norm(root)
            root_lower = root_norm.lower()
            if lowered == root_lower:
                return ""
            if lowered.startswith(root_lower + "/"):
                return normalized[len(root_norm) + 1:]
        return normalized

    def asset_path(kind, *parts):
        if kind == "images":
            root = asset_image_roots[0]
        elif kind == "audio":
            root = asset_audio_roots[0]
        elif kind == "gui":
            root = asset_gui_root
        else:
            root = asset_root
        cleaned = [asset_norm(p) for p in parts if asset_norm(p)]
        return "/".join([asset_norm(root)] + cleaned)
