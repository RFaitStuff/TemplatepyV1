init -897 python in _viewers:
    scene_editor_image_filter = ""
    scene_editor_image_folder_filter = "All"
    scene_editor_browser_scroll = 0
    scene_editor_image_tree_expanded = set([""])
    scene_editor_asset_mode = "Images"
    scene_editor_asset_sort_mode = "Recent"
    scene_editor_asset_tab = "Images"
    scene_editor_right_panel_tab = "Layers"
    scene_editor_image_candidates_cache = None
    scene_editor_image_candidates_grouped_cache = None
    scene_editor_image_candidates_ordered_cache = None
    scene_editor_image_tree_cache = None
    scene_editor_audio_assets_cache = {}

    def scene_editor_clear_asset_browser_cache():
        global scene_editor_image_candidates_cache
        global scene_editor_image_candidates_grouped_cache
        global scene_editor_image_candidates_ordered_cache
        global scene_editor_image_tree_cache
        global scene_editor_audio_assets_cache
        scene_editor_image_candidates_cache = None
        scene_editor_image_candidates_grouped_cache = None
        scene_editor_image_candidates_ordered_cache = None
        scene_editor_image_tree_cache = None
        scene_editor_audio_assets_cache = {}
        if "scene_editor_hover_image_name" in globals():
            globals()["scene_editor_hover_image_name"] = None
        if "scene_editor_clear_image_name_cache" in globals():
            scene_editor_clear_image_name_cache()
        scene_editor_thumbnail_cache.clear()

    def scene_editor_cached_image_name_candidates():
        global scene_editor_image_candidates_cache
        if scene_editor_image_candidates_cache is None:
            scene_editor_image_candidates_cache = tuple(get_image_name_candidates())
        return scene_editor_image_candidates_cache

    def scene_editor_candidate_parts(name):
        if isinstance(name, str):
            return tuple(name.split())
        if isinstance(name, tuple):
            return name
        return tuple(str(name).split())

    def scene_editor_find_image_candidate(image_name):
        requested = scene_editor_candidate_parts(image_name)
        if not requested:
            return None
        for candidate in scene_editor_cached_image_name_candidates():
            candidate = scene_editor_candidate_parts(candidate)
            if candidate == requested:
                return candidate
        for candidate in scene_editor_cached_image_name_candidates():
            candidate = scene_editor_candidate_parts(candidate)
            if candidate and candidate[0] == requested[0] and set(candidate) == set(requested):
                return candidate
        return None

    if "ShowImage" not in globals():
        @renpy.pure
        class ShowImage(renpy.store.Action, renpy.store.DictEquality):
            def __init__(self, image_name_tuple):
                self.image_name_tuple = image_name_tuple
                self.string = " ".join(image_name_tuple)
                self.check = None

            def __call__(self):
                if self.check is None:
                    for n in scene_editor_cached_image_name_candidates():
                        if set(n) == set(self.string.split()) and n[0] == self.string.split()[0]:
                            self.string = " ".join(n)
                            try:
                                for fn in renpy.display.image.images[n].predict_files():
                                    if not renpy.loader.loadable(fn):
                                        self.check = False
                                        break
                                else:
                                    self.check = True
                            except Exception:
                                self.check = True
                try:
                    if self.check:
                        renpy.show(self.string, at_list=[renpy.store.truecenter], layer="screens", tag="preview")
                    else:
                        renpy.show("preview", what=renpy.text.text.Text("No files", color="#ff0000"), at_list=[renpy.store.truecenter], layer="screens")
                except Exception:
                    renpy.show("preview", what=renpy.text.text.Text("No files", color="#F00"), at_list=[renpy.store.truecenter], layer="screens")
                renpy.restart_interaction()

    def scene_editor_image_files_for_name(name_tuple):
        try:
            return list(renpy.display.image.images[name_tuple].predict_files())
        except Exception:
            return []

    def scene_editor_image_folder(name_tuple):
        files = scene_editor_image_files_for_name(name_tuple)
        if files:
            folder = files[0].replace("\\", "/").rsplit("/", 1)[0]
            return folder if folder else "Root"
        if len(name_tuple) > 1:
            return name_tuple[0]
        return "Other"


    def scene_editor_image_candidates_grouped():
        global scene_editor_image_candidates_grouped_cache
        if scene_editor_image_candidates_grouped_cache is not None:
            return scene_editor_image_candidates_grouped_cache
        groups = {}
        for name in scene_editor_cached_image_name_candidates():
            folder = scene_editor_image_folder(name)
            groups.setdefault(folder, []).append(" ".join(name))
        scene_editor_image_candidates_grouped_cache = groups
        return groups

    def scene_editor_image_candidates_ordered():
        global scene_editor_image_candidates_ordered_cache
        if scene_editor_image_candidates_ordered_cache is not None:
            return scene_editor_image_candidates_ordered_cache
        ordered = []
        for name in scene_editor_cached_image_name_candidates():
            folder = scene_editor_image_folder(name)
            ordered.append((folder, " ".join(name)))
        scene_editor_image_candidates_ordered_cache = tuple(ordered)
        return ordered

    def scene_editor_list_audio_assets(limit=500):
        cache_key = (scene_editor_asset_sort_mode, limit)
        if cache_key in scene_editor_audio_assets_cache:
            return list(scene_editor_audio_assets_cache[cache_key])
        files = []
        try:
            candidates = renpy.list_files()
        except Exception:
            candidates = []
        if not candidates:
            return files
        allowed = (".ogg", ".mp3", ".wav", ".flac", ".opus", ".m4a", ".aac")
        for path in candidates:
            if not isinstance(path, str):
                continue
            normalized = path.replace("\\", "/")
            if normalized.lower().endswith(allowed):
                files.append(normalized)
        mode = scene_editor_asset_sort_mode
        if mode == "Name A-Z":
            files = sorted(files, key=lambda n: n.lower())
        elif mode == "Name Z-A":
            files = sorted(files, key=lambda n: n.lower(), reverse=True)
        elif mode == "Recent":
            files = list(reversed(files))
        elif mode == "Oldest":
            files = list(files)
        files = files[:limit]
        scene_editor_audio_assets_cache[cache_key] = tuple(files)
        return files

    def scene_editor_set_asset_mode(mode):
        global scene_editor_asset_mode
        scene_editor_asset_mode = mode
        scene_editor_clear_asset_browser_cache()
        renpy.restart_interaction()

    def scene_editor_set_asset_tab(tab):
        global scene_editor_asset_mode, scene_editor_asset_tab, scene_editor_image_current_path
        scene_editor_asset_tab = tab
        if tab == "Audio":
            scene_editor_asset_mode = "Audio"
        else:
            scene_editor_asset_mode = "Images"
            _tab_folders = {"Characters": ("characters",), "Backgrounds": ("bg",), "GUI": ("gui",)}
            if tab in _tab_folders:
                _target = _tab_folders[tab]
                _root = scene_editor_image_tree_root()
                _node = _root
                _valid = []
                for _part in _target:
                    _child = _node["children"].get(_part)
                    if _child is None:
                        break
                    _node = _child
                    _valid.append(_part)
                scene_editor_image_current_path = tuple(_valid)
            else:
                scene_editor_image_current_path = ()
        scene_editor_clear_asset_browser_cache()
        renpy.restart_interaction()

    def scene_editor_set_asset_sort_mode(mode):
        global scene_editor_asset_sort_mode
        scene_editor_asset_sort_mode = mode
        scene_editor_clear_asset_browser_cache()
        renpy.restart_interaction()

    def scene_editor_refresh_asset_browser():
        scene_editor_clear_asset_browser_cache()
        renpy.restart_interaction()

    def scene_editor_activate_asset_search():
        scene_editor_set_asset_search_active(True)

    def scene_editor_deactivate_asset_search():
        scene_editor_set_asset_search_active(False)

    def scene_editor_toggle_name_sort():
        global scene_editor_asset_sort_mode
        if scene_editor_asset_sort_mode == "Name A-Z":
            scene_editor_asset_sort_mode = "Name Z-A"
        else:
            scene_editor_asset_sort_mode = "Name A-Z"
        scene_editor_clear_asset_browser_cache()
        renpy.restart_interaction()

    def scene_editor_set_right_panel_tab(tab):
        global scene_editor_right_panel_tab
        scene_editor_right_panel_tab = tab
        renpy.restart_interaction()

    def scene_editor_normalize_folder_parts(folder):
        if not folder:
            return ()
        normalized = folder.replace("\\", "/").strip("/")
        parts = [part for part in normalized.split("/") if part]
        if parts and parts[0].lower() == "game":
            parts.pop(0)
        return tuple(parts)

    def scene_editor_image_tree_root():
        global scene_editor_image_tree_cache
        if scene_editor_image_tree_cache is not None:
            return scene_editor_image_tree_cache
        root = {"children": {}, "files": [], "path": ()}
        ordered = scene_editor_image_candidates_ordered()
        for folder, image_name in ordered:
            parts = scene_editor_normalize_folder_parts(folder)
            node = root
            prefix = []
            for part in parts:
                prefix.append(part)
                key = tuple(prefix)
                node = node["children"].setdefault(part, {"children": {}, "files": [], "path": key})
            node["files"].append(image_name)
        scene_editor_image_tree_cache = root
        return root

    def scene_editor_find_tree_node(path, root=None):
        if root is None:
            root = scene_editor_image_tree_root()
        node = root
        for part in path:
            child = node["children"].get(part)
            if child is None:
                return root
            node = child
        return node

    def scene_editor_current_folder_entries(filter_text=None, sort_mode=None):
        global scene_editor_image_current_path
        if filter_text is None:
            filter_text = scene_editor_image_filter
        if sort_mode is None:
            sort_mode = scene_editor_asset_sort_mode
        root = scene_editor_image_tree_root()
        node = root
        valid_path = []
        for part in scene_editor_image_current_path:
            child = node["children"].get(part)
            if child is None:
                scene_editor_image_current_path = tuple(valid_path)
                node = root
                break
            node = child
            valid_path.append(part)
        folder_names = list(node["children"].keys())
        file_names = list(node["files"])
        if sort_mode in ("Name A-Z", "Name Z-A"):
            folder_names = sorted(folder_names, key=lambda n: n.lower(), reverse=(sort_mode == "Name Z-A"))
            file_names = sorted(file_names, key=lambda n: n.lower(), reverse=(sort_mode == "Name Z-A"))
        elif sort_mode == "Recent":
            folder_names = list(reversed(folder_names))
            file_names = list(reversed(file_names))
        else:
            folder_names = list(folder_names)
            file_names = list(file_names)
        filter_parts = [part.lower() for part in filter_text.split() if part]
        if filter_parts:
            filtered_files = []
            for image_name in file_names:
                lower_name = image_name.lower()
                if all(part in lower_name for part in filter_parts):
                    filtered_files.append(image_name)
            file_names = filtered_files
        folders = []
        for name in folder_names:
            folders.append({
                "name": name,
                "path": tuple(valid_path + [name]),
            })
        folders.sort(key=lambda entry: entry["name"].lower())
        return folders, file_names

    def scene_editor_current_folder_label():
        if not scene_editor_image_current_path:
            return "Game"
        return "/".join(scene_editor_image_current_path)

    def scene_editor_can_go_up_asset_folder():
        return bool(scene_editor_image_current_path)

    def scene_editor_open_asset_folder(path):
        global scene_editor_image_current_path
        scene_editor_set_asset_search_active(False)
        if isinstance(path, (list, tuple)):
            target = tuple(path)
        elif isinstance(path, str):
            target = tuple(part for part in path.split("/") if part)
        else:
            target = (str(path),)
        root = scene_editor_image_tree_root()
        node = root
        for part in target:
            child = node["children"].get(part)
            if child is None:
                return
            node = child
        scene_editor_image_current_path = target
        scene_editor_thumbnail_cache.clear()
        renpy.restart_interaction()

    def scene_editor_go_up_asset_folder():
        global scene_editor_image_current_path
        if not scene_editor_image_current_path:
            return
        scene_editor_set_asset_search_active(False)
        scene_editor_image_current_path = scene_editor_image_current_path[:-1]
        scene_editor_thumbnail_cache.clear()
        renpy.restart_interaction()

    def scene_editor_reset_asset_folder():
        global scene_editor_image_current_path
        if scene_editor_image_current_path:
            scene_editor_set_asset_search_active(False)
            scene_editor_image_current_path = ()
            scene_editor_thumbnail_cache.clear()
            renpy.restart_interaction()

    def scene_editor_filter_images(filter_text=None, folder=None, sort_mode=None, path=None):
        if filter_text is None:
            filter_text = scene_editor_image_filter
        if sort_mode is None:
            sort_mode = scene_editor_asset_sort_mode
        filter_parts = [part.lower() for part in filter_text.split() if part]
        ordered = scene_editor_image_candidates_ordered()
        result = []
        normalized_path = tuple(path) if path else None
        if sort_mode in ("Name A-Z", "Name Z-A"):
            ordered = sorted(ordered, key=lambda item: item[1].lower(), reverse=(sort_mode == "Name Z-A"))
        elif sort_mode == "Recent":
            ordered = list(reversed(ordered))
        else:
            ordered = list(ordered)
        for group_name, image_name in ordered:
            if folder and folder != "All" and group_name != folder:
                continue
            parts = scene_editor_normalize_folder_parts(group_name)
            if normalized_path is not None:
                if tuple(parts) != normalized_path:
                    continue
            lower_name = image_name.lower()
            if all(part in lower_name for part in filter_parts):
                result.append((group_name, image_name))
        return result

    def scene_editor_set_image_filter(text):
        global scene_editor_image_filter
        scene_editor_image_filter = text
        renpy.restart_interaction()

    def scene_editor_unique_tag(base_tag, layer):
        state = get_image_state(layer)
        if base_tag not in state:
            return base_tag
        for i in range(2, 999):
            tag = base_tag + str(i)
            if tag not in state:
                return tag
        return None

    def scene_editor_apply_image_name(image_name, layer=None, replace_tag=None):

        global scene_editor_selected_layer, scene_editor_selected_tag
        scene_editor_set_asset_search_active(False)
        if layer is None:
            layer = scene_editor_selected_layer
        if current_time < scene_keyframes[current_scene][1]:
            renpy.notify(_("can't change values before the start time of the current scene"))
            return
        name_tuple = scene_editor_candidate_parts(image_name)
        canonical = scene_editor_find_image_candidate(name_tuple)
        if canonical is None:
            renpy.notify(_("Please select a valid image"))
            return
        image_name = " ".join(canonical)
        display_name = canonical[-1]
        scene_editor_push_history()
        if replace_tag is not None:
            set_keyframe((replace_tag, layer, "child"), (image_name, persistent._viewer_transition), time=current_time)
            scene_editor_clear_runtime_caches()
            change_time(current_time)
            return
        base_tag = display_name
        added_tag = scene_editor_unique_tag(base_tag, layer)
        if added_tag is None:
            renpy.notify(_("too many same tag images is used"))
            return
        image_state[current_scene].setdefault(layer, {})[added_tag] = {}
        scene_editor_captured_displayables[current_scene].setdefault(layer, {})[added_tag] = None
        image_state[current_scene][layer][added_tag]["at_list"] = list(scene_editor_default_added_at_list)
        scene_editor_append_zorder(layer, added_tag)
        for prop in transform_props:
            if prop == "child":
                image_state[current_scene][layer][added_tag][prop] = (image_name, None)
                if current_scene == 0 or current_time > scene_keyframes[current_scene][1]:
                    set_keyframe((added_tag, layer, prop), (image_name, persistent._viewer_transition))
            elif prop in ("matrixtransform", "matrixcolor"):
                for matrix_prop, value in load_matrix(prop, None):
                    image_state[current_scene][layer][added_tag][matrix_prop] = value
            else:
                image_state[current_scene][layer][added_tag][prop] = property_default_value.get(prop)
        scene_editor_selected_layer = layer
        scene_editor_selected_tag = added_tag
        scene_editor_clear_runtime_caches()
        reset((added_tag, layer, "child"))
        change_time(current_time)

    def scene_editor_replace_with_first_filtered_image():
        if scene_editor_selected_tag is None:
            return
        filtered = scene_editor_filter_images(path=scene_editor_image_current_path)
        if not filtered:
            renpy.notify(_("Select an image from the browser"))
            return
        scene_editor_apply_image_name(filtered[0][1], scene_editor_selected_layer, scene_editor_selected_tag)

    def scene_editor_preview_image(image_name):
        global scene_editor_hover_image_name
        scene_editor_hover_image_name = image_name
        if not scene_editor_image_preview:
            return

    def scene_editor_hide_preview():
        global scene_editor_hover_image_name
        scene_editor_hover_image_name = None
        renpy.restart_interaction()
