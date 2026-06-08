# Cached Unity-style asset browser. The left side is a folder tree built from
# the actual source files behind registered Ren'Py images; the right side shows
# only the current folder. Thumbnails are created lazily for the visible page.

init -860 python in live_studio:
    from renpy.store import Fixed, Solid, Text, Transform

    asset_cache = None
    audio_cache = None
    asset_thumbnail_cache = {}
    asset_view_cache = {}
    asset_tree_cache = {}
    asset_tree_rows_cache = {}
    asset_filter = ""
    asset_filter_draft = ""
    asset_category = "images"
    asset_sort_mode = "Name A-Z"
    asset_page = 0
    asset_current_path = ()
    asset_expanded_paths = set([()])

    # Keep the top-level browser simple. Character, background, and GUI
    # organization is represented by the real folder tree instead of duplicate
    # category tabs.
    ASSET_CATEGORIES = (
        ("images", "Images"),
        ("audio", "Audio"),
    )

    ASSET_SORT_MODES = ("Name A-Z", "Name Z-A", "Recent", "Oldest")

    def _registered_image_target(name):
        try:
            return renpy.display.image.images.get(tuple(str(name).split()))
        except Exception:
            return None

    def _image_source_files(target):
        if target is None:
            return []
        try:
            return [str(value).replace("\\", "/") for value in (target.predict_files() or []) if value]
        except Exception:
            return []

    def _previewable_registered_image(name, target):
        if target is None:
            return False
        parts = tuple(str(name).split())
        if not parts:
            return False
        class_name = type(target).__name__.lower()
        if parts[0].lower() == "text" or "parameterizedtext" in class_name or "parameterized" in class_name:
            return False
        return True

    def _asset_bucket(name, files):
        lower_name = str(name).lower()
        lower_path = " ".join(files).lower()
        combined = lower_name + " " + lower_path
        first = lower_name.split()[0] if lower_name.split() else ""
        if first in ("bg", "background") or "/bg/" in combined or "/background" in combined:
            return "backgrounds"
        if first in ("gui", "ui") or "/gui/" in combined or "/ui/" in combined:
            return "gui"
        if any(token in combined for token in ("/characters/", "/character/", "/sprites/", "/sprite/", " side ")):
            return "characters"
        return "images"

    def _normalize_asset_path(filename):
        normalized = str(filename or "").replace("\\", "/").strip("/")
        parts = [part for part in normalized.split("/") if part]
        if parts and parts[0].lower() == "game":
            parts.pop(0)
        return tuple(parts)

    def _image_folder_parts(name, files, bucket):
        if files:
            parts = list(_normalize_asset_path(files[0]))
            if parts:
                parts.pop()  # filename
            return tuple(parts)
        tag = str(name or "image").split()[0]
        return ("Registered Images", bucket.title(), tag)

    def refresh_assets(restart_ui=True):
        global asset_cache, audio_cache, asset_thumbnail_cache, asset_view_cache
        global asset_tree_cache, asset_tree_rows_cache, asset_page, asset_current_path, asset_expanded_paths
        images = []
        try:
            values = list(renpy.list_images())
        except Exception:
            values = []

        for index, value in enumerate(values):
            name = " ".join(value) if isinstance(value, (tuple, list)) else str(value)
            if not name:
                continue
            target = _registered_image_target(name)
            if not _previewable_registered_image(name, target):
                continue
            files = _image_source_files(target)
            bucket = _asset_bucket(name, files)
            images.append({
                "name": name,
                "parts": list(value) if isinstance(value, (tuple, list)) else name.split(),
                "tag": name.split()[0],
                "kind": "image",
                "bucket": bucket,
                "files": files,
                "folder": _image_folder_parts(name, files, bucket),
                "index": index,
            })

        audio = []
        try:
            files = list(renpy.list_files())
        except Exception:
            files = []
        for index, filename in enumerate(files):
            if not isinstance(filename, str):
                continue
            normalized = filename.replace("\\", "/")
            lower = normalized.lower()
            if lower.endswith((".ogg", ".opus", ".mp3", ".wav", ".flac", ".webm", ".m4a", ".aac")):
                path = list(_normalize_asset_path(normalized))
                if path:
                    path.pop()
                audio.append({"name": normalized, "kind": "audio", "folder": tuple(path), "index": index})

        asset_cache = images
        audio_cache = audio
        asset_thumbnail_cache = {}
        asset_view_cache = {}
        asset_tree_cache = {}
        asset_tree_rows_cache = {}
        asset_page = 0
        asset_current_path = ()
        asset_expanded_paths = set([()])
        if restart_ui:
            restart()
        return images

    def ensure_assets():
        global asset_category
        if asset_category not in ("images", "audio"):
            asset_category = "images"
        if asset_cache is None or audio_cache is None:
            refresh_assets(restart_ui=False)

    def _category_assets():
        ensure_assets()
        if asset_category == "audio":
            return list(audio_cache or [])
        return [item for item in (asset_cache or []) if _previewable_registered_image(item.get("name"), _registered_image_target(item.get("name")))]

    def _build_asset_tree():
        cache_key = asset_category
        cached = asset_tree_cache.get(cache_key)
        if cached is not None:
            return cached
        root = {"name": "Assets", "path": (), "children": {}, "assets": []}
        for item in _category_assets():
            node = root
            prefix = []
            for part in item.get("folder", ()):
                prefix.append(part)
                node = node["children"].setdefault(part, {
                    "name": part,
                    "path": tuple(prefix),
                    "children": {},
                    "assets": [],
                })
            node["assets"].append(item)
        asset_tree_cache[cache_key] = root
        return root

    def _tree_node(path=None):
        path = tuple(asset_current_path if path is None else path)
        node = _build_asset_tree()
        for part in path:
            node = node.get("children", {}).get(part)
            if node is None:
                return _build_asset_tree()
        return node

    def set_asset_category(value):
        global asset_category, asset_page, asset_current_path, asset_expanded_paths
        value = str(value or "images").lower()
        if value not in [entry[0] for entry in ASSET_CATEGORIES]:
            value = "images"
        asset_category = value
        asset_page = 0
        asset_current_path = ()
        asset_expanded_paths = set([()])
        asset_tree_rows_cache.clear()
        restart()

    def set_asset_sort_mode(value):
        global asset_sort_mode, asset_page
        value = str(value or "Name A-Z")
        if value not in ASSET_SORT_MODES:
            value = "Name A-Z"
        asset_sort_mode = value
        asset_page = 0
        asset_view_cache.clear()
        restart()

    class AssetFilterInputValue(renpy.store.InputValue):
        default = False
        editable = True
        returnable = False

        def __init__(self):
            try:
                super(AssetFilterInputValue, self).__init__()
            except Exception:
                pass

        def get_text(self):
            return str(asset_filter_draft)

        def set_text(self, value):
            # Match the original SceneEditor behavior: every typed character is
            # immediately reflected by the asset results. Keeping a separate
            # committed query meant the Input changed while the browser still
            # filtered with the old value until Enter/Go was pressed.
            global asset_filter, asset_filter_draft, asset_page
            value = str(value or "")
            if value == asset_filter_draft and value == asset_filter:
                return
            asset_filter_draft = value
            asset_filter = value
            asset_page = 0
            asset_view_cache.clear()
            try:
                renpy.restart_interaction()
            except Exception:
                pass

        def enter(self):
            apply_asset_filter()
            return None

    asset_filter_input = AssetFilterInputValue()

    def set_asset_filter(value, restart_ui=True):
        global asset_filter, asset_filter_draft, asset_page
        asset_filter = str(value or "")
        asset_filter_draft = asset_filter
        asset_page = 0
        asset_view_cache.clear()
        if restart_ui:
            restart()

    def apply_asset_filter():
        set_asset_filter(asset_filter_draft)

    def clear_asset_filter():
        set_asset_filter("")

    def _sort_assets(values):
        values = list(values)
        if asset_sort_mode == "Name Z-A":
            values.sort(key=lambda item: item.get("name", "").lower(), reverse=True)
        elif asset_sort_mode == "Recent":
            values.sort(key=lambda item: item.get("index", 0), reverse=True)
        elif asset_sort_mode == "Oldest":
            values.sort(key=lambda item: item.get("index", 0))
        else:
            values.sort(key=lambda item: item.get("name", "").lower())
        return values

    def _folder_assets_unpaged():
        query = str(asset_filter or "").strip().lower()
        cache_key = (asset_category, tuple(asset_current_path), query, asset_sort_mode)
        cached = asset_view_cache.get(cache_key)
        if cached is not None:
            return cached
        if query:
            parts = [part for part in query.split() if part]
            values = [item for item in _category_assets() if all(part in item.get("name", "").lower() or any(part in f.lower() for f in item.get("files", [])) for part in parts)]
        else:
            values = list(_tree_node().get("assets", []))
        values = _sort_assets(values)
        asset_view_cache[cache_key] = values
        return values

    def asset_folder_entries():
        if str(asset_filter or "").strip():
            return []
        node = _tree_node()
        values = list(node.get("children", {}).values())
        values.sort(key=lambda item: item.get("name", "").lower())
        return values

    def asset_tree_rows():
        key = (asset_category, tuple(asset_current_path), tuple(sorted(asset_expanded_paths)))
        cached = asset_tree_rows_cache.get(key)
        if cached is not None:
            return cached
        rows = []
        root = _build_asset_tree()
        def append(node, depth):
            path = tuple(node.get("path", ()))
            children = node.get("children", {})
            opened = path in asset_expanded_paths
            rows.append({
                "name": node.get("name", "Assets"),
                "path": path,
                "depth": depth,
                "has_children": bool(children),
                "open": opened,
                "selected": path == tuple(asset_current_path),
            })
            if opened:
                for name in sorted(children, key=lambda value: value.lower()):
                    append(children[name], depth + 1)
        append(root, 0)
        asset_tree_rows_cache[key] = rows
        if len(asset_tree_rows_cache) > 24:
            asset_tree_rows_cache.clear()
            asset_tree_rows_cache[key] = rows
        return rows

    def toggle_asset_folder(path):
        path = tuple(path or ())
        if path in asset_expanded_paths:
            if path:
                asset_expanded_paths.discard(path)
        else:
            asset_expanded_paths.add(path)
        asset_tree_rows_cache.clear()
        restart()

    def open_asset_folder(path):
        global asset_current_path, asset_page
        path = tuple(path or ())
        if _tree_node(path) is None:
            return
        asset_current_path = path
        asset_page = 0
        # Expand this path and all its ancestors.
        for index in range(len(path) + 1):
            asset_expanded_paths.add(path[:index])
        asset_tree_rows_cache.clear()
        restart()

    def asset_go_up():
        open_asset_folder(tuple(asset_current_path[:-1]))

    def asset_breadcrumb():
        return "Assets" + (" / " + " / ".join(asset_current_path) if asset_current_path else "")

    def asset_total():
        return len(_folder_assets_unpaged())

    def asset_page_count():
        return max(1, int((asset_total() + ASSET_PAGE_SIZE - 1) / ASSET_PAGE_SIZE))

    def asset_page_label():
        count = asset_page_count()
        return "{}/{} · {} items".format(min(asset_page + 1, count), count, asset_total())

    def set_asset_page(value):
        global asset_page
        try:
            value = int(value)
        except Exception:
            value = 0
        asset_page = max(0, min(asset_page_count() - 1, value))
        restart()

    def previous_asset_page():
        set_asset_page(asset_page - 1)

    def next_asset_page():
        set_asset_page(asset_page + 1)

    def assets():
        values = _folder_assets_unpaged()
        page = max(0, min(asset_page, asset_page_count() - 1))
        start = page * ASSET_PAGE_SIZE
        return values[start:start + ASSET_PAGE_SIZE]

    def asset_short_name(asset):
        name = str((asset or {}).get("name", ""))
        if (asset or {}).get("kind") == "audio":
            return name.rsplit("/", 1)[-1]
        files = (asset or {}).get("files") or []
        if files:
            return files[0].rsplit("/", 1)[-1]
        return name.split()[-1] if name.split() else name

    class SafeAssetThumbnail(renpy.Displayable):
        def __init__(self, source, width, height, **properties):
            super(SafeAssetThumbnail, self).__init__(**properties)
            self.width = max(1, int(width))
            self.height = max(1, int(height))
            self.child = Transform(source, fit="contain", xsize=self.width, ysize=self.height, xalign=0.5, yalign=0.5)
            self.placeholder = Fixed(
                Solid("#101827", xsize=self.width, ysize=self.height),
                Transform(Text("Preview unavailable", size=10, color=MUTED_TEXT_COLOR), xalign=0.5, yalign=0.5),
                xysize=(self.width, self.height),
            )

        def render(self, width, height, st, at):
            try:
                return renpy.render(self.child, self.width, self.height, st, at)
            except Exception:
                return renpy.render(self.placeholder, self.width, self.height, st, at)

        def visit(self):
            return []

    def asset_thumbnail(name, width=ASSET_THUMB_WIDTH, height=ASSET_THUMB_HEIGHT):
        width = max(1, int(width))
        height = max(1, int(height))
        key = (str(name), width, height)
        cached = asset_thumbnail_cache.get(key)
        if cached is not None:
            return cached
        target = _registered_image_target(name)
        if not _previewable_registered_image(name, target):
            thumb = Solid("#101827", xsize=width, ysize=height)
            asset_thumbnail_cache[key] = thumb
            return thumb
        thumb = SafeAssetThumbnail(target, width, height)
        asset_thumbnail_cache[key] = thumb
        return thumb

    def add_asset_to_current_context(asset_name):
        if not asset_name:
            return
        if str(selected_tree_tab).lower() == "ui":
            screen = selected_item()[0] if selected_item()[2] == "ui_screen" else None
            add_ui_image(asset_name, screen_id=screen.get("id") if screen else None)
        else:
            add_image_to_scene(asset_name)
        set_bottom_tab("Assets")
