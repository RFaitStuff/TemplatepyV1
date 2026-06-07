# Canvas rendering, hierarchy-aware hit testing, and photo-editor manipulation.

init -850 python in live_studio:
    from renpy.store import Fixed, Solid, Text, Transform
    try:
        import pygame_sdl2 as pygame
    except Exception:
        import pygame
    from math import atan2, degrees

    def canvas_items(state=None, selectable_only=True):
        state = state or resolve_frame()
        cache_key = (id(state), bool(selectable_only), int(runtime.get("state_revision", 0)))
        item_cache = runtime.setdefault("canvas_item_cache", {})
        if cache_key in item_cache:
            return item_cache[cache_key]
        result = []
        order = 0
        for scene_index, scene in enumerate(state.get("scenes", [])):
            if not scene.get("visible", True):
                continue
            for node, _parent_id, depth in walk_nodes(scene.get("nodes", [])):
                if node.get("internal"):
                    continue
                if node.get("visible", True) and (not selectable_only or node.get("selectable", True)):
                    result.append((scene_index * 100000 + int(node.get("zorder", order) or order), depth, node, "scene_node"))
                order += 1
        for screen_index, screen in enumerate(state.get("ui_screens", [])):
            if not screen.get("visible", True):
                continue
            for node, _parent_id, depth in walk_nodes(screen.get("nodes", [])):
                if node.get("internal"):
                    continue
                if node.get("visible", True) and (not selectable_only or node.get("selectable", True)):
                    result.append((10000000 + screen_index * 100000 + order, depth, node, "ui_node"))
                order += 1
        result.sort(key=lambda value: (value[0], value[1]))
        item_cache[cache_key] = result
        return result

    def _padding_values(value):
        if value is None:
            return (0.0, 0.0, 0.0, 0.0)
        if isinstance(value, (int, float)):
            amount = float(value)
            return (amount, amount, amount, amount)
        if isinstance(value, (tuple, list)):
            values = list(value)
            if len(values) == 2:
                return (float(values[0]), float(values[1]), float(values[0]), float(values[1]))
            if len(values) >= 4:
                return tuple(float(item) for item in values[:4])
        return (0.0, 0.0, 0.0, 0.0)

    def _managed_size(node, parent_rect):
        props = node.get("properties", {})
        original = node.get("bounds") or {}
        parent_width = max(1.0, float(parent_rect.get("width", config.screen_width)))
        parent_height = max(1.0, float(parent_rect.get("height", config.screen_height)))
        if props.get("xfill"):
            width = parent_width
        elif props.get("xsize") is not None:
            width = position_to_pixels(props.get("xsize"), parent_width)
        else:
            width = float(original.get("width", 1) or 1)
        if props.get("yfill"):
            height = parent_height
        elif props.get("ysize") is not None:
            height = position_to_pixels(props.get("ysize"), parent_height)
        else:
            height = float(original.get("height", 1) or 1)
        return max(1.0, width), max(1.0, height)

    def _managed_rect(node, parent_rect, forced_x=None, forced_y=None):
        props = node.get("properties", {})
        original = node.get("bounds") or {}
        width, height = _managed_size(node, parent_rect)
        parent_width = float(parent_rect.get("width", config.screen_width))
        parent_height = float(parent_rect.get("height", config.screen_height))

        xpos = props.get("xpos")
        ypos = props.get("ypos")
        xanchor = props.get("xanchor")
        yanchor = props.get("yanchor")
        if props.get("xalign") is not None:
            if xpos is None:
                xpos = props.get("xalign")
            if xanchor is None:
                xanchor = props.get("xalign")
        if props.get("yalign") is not None:
            if ypos is None:
                ypos = props.get("yalign")
            if yanchor is None:
                yanchor = props.get("yalign")

        try:
            xoffset = float(props.get("xoffset", 0) or 0)
        except Exception:
            xoffset = 0.0
        try:
            yoffset = float(props.get("yoffset", 0) or 0)
        except Exception:
            yoffset = 0.0

        if forced_x is None:
            if xpos is None:
                # Converted runtime widgets retain absolute measured bounds.
                x = float(original.get("x", parent_rect.get("x", 0)) or 0)
            else:
                x = float(parent_rect.get("x", 0)) + position_to_pixels(xpos, parent_width) - position_to_pixels(xanchor or 0, width) + xoffset
        else:
            x = float(forced_x) + xoffset

        if forced_y is None:
            if ypos is None:
                y = float(original.get("y", parent_rect.get("y", 0)) or 0)
            else:
                y = float(parent_rect.get("y", 0)) + position_to_pixels(ypos, parent_height) - position_to_pixels(yanchor or 0, height) + yoffset
        else:
            y = float(forced_y) + yoffset

        return {"x": x, "y": y, "width": width, "height": height}

    def _active_preview_event(state):
        for controller in state.get("dialogue_controllers", []):
            event = active_dialogue_event(controller, state)
            if event is not None:
                return event
        return None

    def _screen_contains_item(screen, item_id):
        if not screen or not item_id:
            return False
        if screen.get("id") == item_id:
            return True
        return any(node.get("id") == item_id for node, _parent, _depth in walk_nodes(screen.get("nodes", [])))

    def screen_visible_in_canvas(screen, state=None, event=None):
        if not screen or not screen.get("visible", True):
            return False
        role = str(screen.get("role") or "screen").lower()
        if role not in ("say", "choice"):
            return True
        if _screen_contains_item(screen, selected_item_id):
            return True
        event = event or _active_preview_event(state or resolve_frame())
        if role == "say":
            return bool(event and (event.get("type") in ("say", "narration") or (event.get("type") == "choice" and event.get("text"))))
        return bool(event and event.get("type") == "choice")

    def _layout_managed_node(node, parent_rect, result, parent_type="fixed", forced_x=None, forced_y=None):
        rect = _managed_rect(node, parent_rect, forced_x, forced_y)
        result[node.get("id")] = rect
        children = node.get("children", [])
        if not children:
            return rect

        props = node.get("properties", {})
        left, top, right, bottom = _padding_values(props.get("padding"))
        inner = {
            "x": rect["x"] + left,
            "y": rect["y"] + top,
            "width": max(1.0, rect["width"] - left - right),
            "height": max(1.0, rect["height"] - top - bottom),
        }
        node_type = str(node.get("type") or "fixed").lower()
        spacing = float(props.get("spacing", 0) or 0)

        if node_type == "vbox":
            cursor = inner["y"]
            for child in children:
                _width, child_height = _managed_size(child, inner)
                _layout_managed_node(child, inner, result, node_type, forced_y=cursor)
                cursor += child_height + spacing
        elif node_type == "hbox":
            cursor = inner["x"]
            for child in children:
                child_width, _height = _managed_size(child, inner)
                _layout_managed_node(child, inner, result, node_type, forced_x=cursor)
                cursor += child_width + spacing
        elif node_type in ("grid", "vpgrid"):
            cols = max(1, int(props.get("cols", 1) or 1))
            rows = max(1, int((len(children) + cols - 1) / cols))
            cell_width = max(1.0, (inner["width"] - spacing * (cols - 1)) / cols)
            cell_height = max(1.0, (inner["height"] - spacing * (rows - 1)) / rows)
            for index, child in enumerate(children):
                col = index % cols
                row = index // cols
                cell = {
                    "x": inner["x"] + col * (cell_width + spacing),
                    "y": inner["y"] + row * (cell_height + spacing),
                    "width": cell_width,
                    "height": cell_height,
                }
                _layout_managed_node(child, cell, result, node_type)
        else:
            for child in children:
                _layout_managed_node(child, inner, result, node_type)
        return rect

    def effective_item(item):
        """Applies the current drag preview without mutating project state.

        The previous implementation invalidated and deep-resolved the entire
        inherited frame on every mouse-motion event. A transient overlay keeps
        dragging responsive and commits a single change on mouse-up.
        """
        drag = runtime.get("drag") or {}
        if not item or item.get("id") != drag.get("item_id"):
            return item
        preview = drag.get("preview") or {}
        if not preview:
            return item
        result = clone(item)
        for path, value in preview.items():
            set_path_value(result, path, value)
        return result

    def _number_value(value, fallback=0.0):
        try:
            if isinstance(value, dict):
                return float(value.get("absolute", 0) or 0)
            return float(value if value is not None else fallback)
        except Exception:
            return float(fallback)

    def _captured_ui_bounds(node):
        """Keeps measured container-relative UI bounds aligned with overrides.

        Ren'Py layout containers decide a child's final screen position. Rebuilding
        that position from the child's ``xpos`` alone can place its selection box
        at the top-left even though the real widget is inside a VBox/Frame. For
        captured widgets we retain the measured rectangle and apply the editor's
        offset/size deltas to it.
        """
        original = node.get("bounds") or {}
        props = node.get("properties", {}) or {}
        base = node.get("resolved_properties", {}) or {}
        x = _number_value(original.get("x"))
        y = _number_value(original.get("y"))
        width = max(1.0, _number_value(original.get("width"), 1.0))
        height = max(1.0, _number_value(original.get("height"), 1.0))
        x += _number_value(props.get("xoffset")) - _number_value(base.get("xoffset"))
        y += _number_value(props.get("yoffset")) - _number_value(base.get("yoffset"))
        if has_local_override(node.get("id"), "properties.xsize") or (runtime.get("drag") or {}).get("preview", {}).get("properties.xsize") is not None:
            width = max(1.0, position_to_pixels(props.get("xsize"), config.screen_width))
        if has_local_override(node.get("id"), "properties.ysize") or (runtime.get("drag") or {}).get("preview", {}).get("properties.ysize") is not None:
            height = max(1.0, position_to_pixels(props.get("ysize"), config.screen_height))
        return {"x": x, "y": y, "width": width, "height": height}

    def _base_canvas_bounds_map(state):
        key = (id(state), int(runtime.get("state_revision", 0)))
        cache = runtime.setdefault("bounds_cache", {})
        if key in cache:
            return cache[key]
        result = {}
        for scene in state.get("scenes", []):
            if not scene.get("visible", True):
                continue
            for node, _parent, _depth in walk_nodes(scene.get("nodes", [])):
                if node.get("visible", True):
                    result[node.get("id")] = item_bounds(node)

        event = _active_preview_event(state)
        stage = {"x": 0.0, "y": 0.0, "width": float(config.screen_width), "height": float(config.screen_height)}
        for screen in state.get("ui_screens", []):
            if not screen_visible_in_canvas(screen, state, event):
                continue
            if screen.get("managed"):
                for node in screen.get("nodes", []):
                    _layout_managed_node(node, stage, result)
            else:
                for node, _parent, _depth in walk_nodes(screen.get("nodes", [])):
                    if node.get("visible", True):
                        result[node.get("id")] = _captured_ui_bounds(node)
        cache[key] = result
        if len(cache) > 8:
            for old_key in list(cache.keys())[:-5]:
                cache.pop(old_key, None)
        return result

    def canvas_bounds_map(state=None):
        state = state or resolve_frame()
        base = _base_canvas_bounds_map(state)
        drag = runtime.get("drag") or {}
        if not drag or not drag.get("preview"):
            return base

        result = dict(base)
        item, _parent, kind = find_state_item(state, drag.get("item_id"))
        if item is None:
            return result
        current = effective_item(item)
        if kind == "scene_node":
            result[item.get("id")] = item_bounds(current)
            return result

        screen = screen_for_node(state, item.get("id"))
        if screen and screen.get("managed"):
            # Managed containers can move their children, so only this small
            # hierarchy is recomputed during a drag.
            stage = {"x": 0.0, "y": 0.0, "width": float(config.screen_width), "height": float(config.screen_height)}
            for root in screen.get("nodes", []):
                _layout_managed_node(effective_item(root), stage, result)
        else:
            result[item.get("id")] = _captured_ui_bounds(current)
        return result

    def item_stage_bounds(item, bounds_map=None):
        if not item:
            return None
        if bounds_map is not None and item.get("id") in bounds_map:
            return bounds_map.get(item.get("id"))
        return item_bounds(item)

    def hit_test_stage(x, y, state=None, bounds_map=None):
        state = state or resolve_frame()
        bounds_map = bounds_map or canvas_bounds_map(state)
        wanted = "ui_node" if str(selected_tree_tab).lower() == "ui" else "scene_node"
        matches = []
        for zorder, depth, item, kind in reversed(canvas_items(state)):
            if kind != wanted:
                continue
            bounds = item_stage_bounds(item, bounds_map)
            if not bounds:
                continue
            if bounds["x"] <= x <= bounds["x"] + bounds["width"] and bounds["y"] <= y <= bounds["y"] + bounds["height"]:
                matches.append((depth, zorder, item, kind))
        if not matches:
            return None, None
        # Prefer the deepest child, then the visually highest item.
        matches.sort(key=lambda value: (value[0], value[1]), reverse=True)
        return matches[0][2], matches[0][3]

    def _draw_rect(render, x, y, width, height, color, thickness=2):
        x = int(round(x))
        y = int(round(y))
        width = max(1, int(round(width)))
        height = max(1, int(round(height)))
        thickness = max(1, int(thickness))
        for px, py, pw, ph in (
            (x, y, width, thickness),
            (x, y + height - thickness, width, thickness),
            (x, y, thickness, height),
            (x + width - thickness, y, thickness, height),
        ):
            child = renpy.render(Solid(color), max(1, pw), max(1, ph), 0.0, 0.0)
            render.blit(child, (px, py))

    def _draw_line(render, x, y, width, height, color):
        width = max(1, int(round(width)))
        height = max(1, int(round(height)))
        child = renpy.render(Solid(color), width, height, 0.0, 0.0)
        render.blit(child, (int(round(x)), int(round(y))))

    def _canvas_frame_data():
        key = (
            current_frame_id,
            int(runtime.get("state_revision", 0)),
            preview_mode,
            int(runtime.get("drag_revision", 0)),
        )
        cache = runtime.setdefault("canvas_cache", {})
        if cache.get("key") == key:
            return cache.get("state"), cache.get("bounds"), cache.get("preview")

        state = resolve_frame()
        bounds_map = canvas_bounds_map(state)
        if preview_mode == "capture":
            preview = runtime.get("snapshot_displayable")
        else:
            try:
                preview = Fixed(*_layout_preview_children(state, bounds_map), xysize=(int(config.screen_width), int(config.screen_height)))
            except Exception as exc:
                log_diagnostic("error", "Layout preview construction failed", repr(exc))
                preview = runtime.get("snapshot_displayable")

        runtime["canvas_cache"] = {
            "key": key,
            "state": state,
            "bounds": bounds_map,
            "preview": preview,
        }
        return state, bounds_map, preview

    def _set_drag_preview(path, value):
        drag = runtime.get("drag")
        if not drag:
            return
        drag.setdefault("preview", {})[str(path)] = clone(value)
        # Rebuilding a captured ScreenDisplayable is much heavier than moving
        # a scene Transform. Thirty visual updates per second is smooth enough
        # for direct manipulation and leaves headroom for large HUD trees.
        now = time.time()
        last = float(runtime.get("last_drag_render_time", 0.0) or 0.0)
        if now - last >= (1.0 / 30.0):
            runtime["last_drag_render_time"] = now
            runtime["drag_revision"] = int(runtime.get("drag_revision", 0)) + 1
            runtime["canvas_cache"] = {}
            screen_id = drag.get("captured_screen_id")
            if screen_id:
                cache = runtime.setdefault("captured_screen_preview_cache", {})
                for key in list(cache.keys()):
                    if key and key[0] == screen_id:
                        cache.pop(key, None)

    def _snap_value(value):
        if not project_setting("snap_enabled", SNAP_ENABLED):
            return value
        size = float(project_setting("grid_size", GRID_SIZE) or GRID_SIZE)
        if size <= 0:
            return value
        snapped = round(float(value) / size) * size
        if abs(snapped - float(value)) <= SNAP_DISTANCE:
            return snapped
        return value

    def _drag_update(stage_x, stage_y):
        drag = runtime.get("drag")
        if not drag:
            return
        dx = stage_x - drag.get("stage_x", stage_x)
        dy = stage_y - drag.get("stage_y", stage_y)
        mode = drag.get("mode", "move")

        if mode == "resize":
            handle = drag.get("resize_handle") or "se"
            dir_x, dir_y = _RESIZE_DIRECTIONS.get(handle, (1, 1))
            start_x = float(drag.get("bounds_x", 0))
            start_y = float(drag.get("bounds_y", 0))
            start_w = max(1.0, float(drag.get("width", 1)))
            start_h = max(1.0, float(drag.get("height", 1)))
            min_size = 8.0

            new_x, new_y, new_w, new_h = start_x, start_y, start_w, start_h
            if dir_x > 0:
                new_w = max(min_size, start_w + dx)
            elif dir_x < 0:
                new_x = min(start_x + start_w - min_size, start_x + dx)
                new_w = start_w + (start_x - new_x)
            if dir_y > 0:
                new_h = max(min_size, start_h + dy)
            elif dir_y < 0:
                new_y = min(start_y + start_h - min_size, start_y + dy)
                new_h = start_h + (start_y - new_y)

            if dir_x != 0:
                _set_drag_preview("properties.xsize", _snap_value(new_w))
            if dir_y != 0:
                _set_drag_preview("properties.ysize", _snap_value(new_h))
            if dir_x < 0:
                _set_drag_position(dx=new_x - start_x)
            if dir_y < 0:
                _set_drag_position(dy=new_y - start_y)
            return

        if mode == "rotate":
            center_x = float(drag.get("center_x", 0))
            center_y = float(drag.get("center_y", 0))
            angle = degrees(atan2(stage_y - center_y, stage_x - center_x))
            target = float(drag.get("rotate", 0) or 0) + angle - float(drag.get("start_angle", angle))
            _set_drag_preview("properties.rotate", round(target, 2))
            return

        _set_drag_position(dx=dx, dy=dy)

    def _drag_finish():
        global project_dirty
        drag = runtime.get("drag")
        runtime["drag"] = None
        runtime["drag_revision"] = int(runtime.get("drag_revision", 0)) + 1
        if not drag:
            return
        frame = frame_by_id(drag.get("frame_id"))
        if frame is None:
            return
        preview = drag.get("preview") or {}
        if not preview:
            return
        before = clone(drag.get("before", {}))
        item_sets = frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(drag.get("item_id"), {})
        for path, value in preview.items():
            item_sets[str(path)] = clone(value)
        project_dirty = True
        invalidate_resolved_cache()
        after = clone(frame.get("changes", {}))
        label = {"move": "Move item", "resize": "Resize item", "rotate": "Rotate item"}.get(drag.get("mode"), "Edit item")
        _record_frame_change(label, before, after, drag.get("frame_id"))

    def _node_displayable(item, kind, text_override=None):
        props = item.get("properties", {})
        node_type = str(item.get("type") or "").lower()
        content_key = (
            item.get("id"), node_type, str(text_override) if text_override is not None else None,
            props.get("text"), props.get("image"), props.get("idle"), props.get("hover"),
            props.get("background"), props.get("color"), props.get("size"),
            bool(props.get("bold", False)), bool(props.get("italic", False)),
            int(runtime.get("state_revision", 0)),
        )
        cache = runtime.setdefault("preview_source_cache", {})
        if content_key in cache:
            return cache[content_key]

        if node_type == "image":
            image_name = item.get("image") or props.get("image") or item.get("name")
            try:
                result = renpy.displayable(image_name)
            except Exception:
                result = Solid("#7a3444")
        elif node_type == "text":
            result = Text(
                str(text_override if text_override is not None else props.get("text", item.get("text", item.get("name", "Text")))),
                size=int(props.get("size", 30) or 30),
                color=str(props.get("color", TEXT_COLOR)),
                bold=bool(props.get("bold", False)),
                italic=bool(props.get("italic", False)),
            )
        elif node_type == "imagebutton":
            image_name = props.get("idle") or props.get("hover")
            if image_name:
                try:
                    result = renpy.displayable(image_name)
                except Exception:
                    result = None
            else:
                result = None
            if result is None:
                result = Fixed(Solid("#20344dcc"), Transform(Text("Image Button", size=22, color=TEXT_COLOR), xalign=0.5, yalign=0.5))
        elif node_type in ("hotspot", "textbutton", "button"):
            # Canvas preview intentionally does not execute actions.
            label_text = text_override if text_override is not None else props.get("text", item.get("name", "Button"))
            label = Text(str(label_text), size=int(props.get("size", 24) or 24), color=str(props.get("color", TEXT_COLOR)))
            result = Fixed(Solid(str(props.get("background", "#20344dcc"))), Transform(label, xalign=0.5, yalign=0.5))
        elif node_type in ("frame", "window", "fixed", "vbox", "hbox", "viewport", "vpgrid", "grid", "side"):
            background = props.get("background")
            result = Solid(str(background)) if background else NullPreviewDisplayable()
        elif node_type in ("add",):
            try:
                result = renpy.displayable(props.get("image") or item.get("image") or item.get("name"))
            except Exception:
                result = NullPreviewDisplayable()
        else:
            result = NullPreviewDisplayable()
        cache[content_key] = result
        if len(cache) > 420:
            for old_key in list(cache.keys())[:-300]:
                cache.pop(old_key, None)
        return result

    class NullPreviewDisplayable(renpy.Displayable):
        def render(self, width, height, st, at):
            return renpy.Render(max(1, int(width)), max(1, int(height)))

    def _ui_node_screen_map(state):
        result = {}
        for screen in state.get("ui_screens", []):
            for node, _parent, _depth in walk_nodes(screen.get("nodes", [])):
                result[node.get("id")] = screen
        return result

    def _dialogue_preview_text(item, screen, event):
        if not screen or not event:
            return None
        role = str(screen.get("role") or "screen").lower()
        binding_value = item.get("binding") or item.get("properties", {}).get("binding") or item.get("widget_id") or ""
        if isinstance(binding_value, dict):
            binding = str(item.get("widget_id") or "").lower().split(".")[-1]
        else:
            binding = str(binding_value).lower().split(".")[-1]
        if role == "say" and (event.get("type") in ("say", "narration") or event.get("type") == "choice"):
            if binding == "who":
                return event.get("speaker", "")
            if binding == "what":
                return event.get("text", "")
        return None

    def _first_choice_template(screen):
        if not screen:
            return None
        for node, _parent, _depth in walk_nodes(screen.get("nodes", [])):
            if str(node.get("type") or "").lower() in ("button", "textbutton"):
                return node.get("id")
        return None

    def _layout_preview_children(state, bounds_map=None):
        bounds_map = bounds_map or canvas_bounds_map(state)
        scene_children = []
        managed_ui_children = []
        captured_screen_children = []
        screen_by_node = _ui_node_screen_map(state)
        event = _active_preview_event(state)
        choice_templates = {}

        for _z, _depth, item, kind in canvas_items(state, selectable_only=False):
            item = effective_item(item)
            screen = screen_by_node.get(item.get("id")) if kind == "ui_node" else None
            if screen is not None:
                if not screen_visible_in_canvas(screen, state, event):
                    continue
                if not screen.get("managed"):
                    continue
            bounds = item_stage_bounds(item, bounds_map)
            if not bounds or not item.get("visible", True):
                continue

            text_override = _dialogue_preview_text(item, screen, event)
            role = str((screen or {}).get("role") or "screen").lower()
            template_id = choice_templates.setdefault(screen.get("id"), _first_choice_template(screen)) if screen and role == "choice" else None
            repeat_choices = []
            if template_id == item.get("id") and event and event.get("type") == "choice":
                repeat_choices = event.get("choices", []) or []

            preview_entries = []
            if repeat_choices:
                spacing = float(item.get("properties", {}).get("spacing", 10) or 10)
                for choice_index, choice in enumerate(repeat_choices):
                    repeated_bounds = clone(bounds)
                    repeated_bounds["y"] += choice_index * (repeated_bounds["height"] + spacing)
                    preview_entries.append((repeated_bounds, choice.get("caption", "Choice")))
            else:
                preview_entries.append((bounds, text_override))

            for preview_bounds, preview_text in preview_entries:
                displayable = _node_displayable(item, kind, preview_text)
                props = item.get("properties", {})
                transform_kwargs = {
                    "xpos": int(round(preview_bounds.get("x", 0))),
                    "ypos": int(round(preview_bounds.get("y", 0))),
                    "xysize": (max(1, int(round(preview_bounds.get("width", 1)))), max(1, int(round(preview_bounds.get("height", 1))))),
                }
                if props.get("alpha") is not None:
                    transform_kwargs["alpha"] = float(props.get("alpha", 1.0) or 0.0)
                if props.get("rotate"):
                    transform_kwargs["rotate"] = float(props.get("rotate") or 0.0)
                try:
                    transformed = Transform(displayable, **transform_kwargs)
                    if kind == "scene_node":
                        scene_children.append(transformed)
                    else:
                        managed_ui_children.append(transformed)
                except Exception as exc:
                    log_diagnostic("warning", "Preview item could not be rendered", {"item": item.get("name"), "error": repr(exc)})

        # Runtime screens sit above scene layers, matching Ren'Py's normal
        # layer order. They are temporary references and never serialized.
        for screen in state.get("ui_screens", []):
            if screen.get("managed") or not screen_visible_in_canvas(screen, state, event):
                continue
            root = captured_screen_preview(screen)
            if root is not None:
                try:
                    captured_screen_children.append(Transform(root, xpos=0, ypos=0))
                except Exception as exc:
                    log_diagnostic("warning", "Captured screen preview failed", {"screen": screen.get("name"), "error": repr(exc)})

        return scene_children + captured_screen_children + managed_ui_children

    def _thumbnail_source_for_item(item, kind):
        if not item:
            return None
        if kind == "scene_node":
            image_name = item.get("image") or item.get("properties", {}).get("image")
            if image_name:
                try:
                    return renpy.displayable(image_name)
                except Exception:
                    pass
            return runtime.get("scene_displayables", {}).get(item.get("id"))
        if kind == "ui_node":
            # A small semantic preview is dramatically cheaper than re-rendering
            # the original runtime widget (which may contain an entire subtree).
            return _node_displayable(item, kind)
        if kind == "ui_screen":
            for node, _parent, _depth in walk_nodes(item.get("nodes", [])):
                if not node.get("internal"):
                    return _thumbnail_source_for_item(node, "ui_node")
            return None
        return None

    class SafeLayerThumbnail(renpy.Displayable):
        def __init__(self, source, width, height, label="Preview", **properties):
            super(SafeLayerThumbnail, self).__init__(**properties)
            self.width = max(1, int(width))
            self.height = max(1, int(height))
            self.child = Transform(source, fit="contain", xsize=self.width, ysize=self.height, xalign=0.5, yalign=0.5)
            self.placeholder = Fixed(
                Solid("#111a2b", xsize=self.width, ysize=self.height),
                Transform(Text(str(label), size=9, color=MUTED_TEXT_COLOR), xalign=0.5, yalign=0.5),
                xysize=(self.width, self.height),
            )

        def render(self, width, height, st, at):
            try:
                return renpy.render(self.child, self.width, self.height, st, at)
            except Exception:
                return renpy.render(self.placeholder, self.width, self.height, st, at)

        def visit(self):
            # Child rendering is explicit. Keeping thumbnail trees out of the
            # main screen visit pass avoids per_interact work for every layer row.
            return []

    def layer_thumbnail(item, kind, width=LAYER_THUMB_WIDTH, height=LAYER_THUMB_HEIGHT):
        width = max(1, int(width))
        height = max(1, int(height))
        key = (item.get("id") if item else None, str(kind), width, height, int(runtime.get("state_revision", 0)))
        cache = runtime.setdefault("item_thumbnail_cache", {})
        if key in cache:
            return cache[key]
        source = _thumbnail_source_for_item(item, kind)
        if source is None:
            value = Fixed(Solid("#111a2b", xsize=width, ysize=height), Transform(Text("UI" if str(kind).startswith("ui") else "Scene", size=10, color=MUTED_TEXT_COLOR), xalign=0.5, yalign=0.5), xysize=(width, height))
        else:
            value = SafeLayerThumbnail(source, width, height, "No preview")
        cache[key] = value
        if len(cache) > 240:
            for old_key in list(cache.keys())[:-180]:
                cache.pop(old_key, None)
        return value

    _RESIZE_DIRECTIONS = {
        "nw": (-1, -1), "n": (0, -1), "ne": (1, -1),
        "e": (1, 0), "se": (1, 1), "s": (0, 1),
        "sw": (-1, 1), "w": (-1, 0),
    }

    def _point_inside_bounds(x, y, bounds):
        return bool(bounds and bounds.get("x", 0) <= x <= bounds.get("x", 0) + bounds.get("width", 0) and bounds.get("y", 0) <= y <= bounds.get("y", 0) + bounds.get("height", 0))

    def _selection_handles(bounds, scale):
        if not bounds:
            return {}
        size = max(5.0, 9.0 / max(0.001, float(scale or 1.0)))
        half = size / 2.0
        x = float(bounds.get("x", 0))
        y = float(bounds.get("y", 0))
        w = max(1.0, float(bounds.get("width", 1)))
        h = max(1.0, float(bounds.get("height", 1)))
        points = {
            "nw": (x, y), "n": (x + w / 2.0, y), "ne": (x + w, y),
            "e": (x + w, y + h / 2.0), "se": (x + w, y + h),
            "s": (x + w / 2.0, y + h), "sw": (x, y + h), "w": (x, y + h / 2.0),
        }
        result = {name: {"x": px - half, "y": py - half, "width": size, "height": size} for name, (px, py) in points.items()}
        rotate_y = y - max(18.0 / max(0.001, float(scale or 1.0)), size * 2.25)
        result["rotate"] = {"x": x + w / 2.0 - half, "y": rotate_y - half, "width": size, "height": size}
        return result

    def _handle_at(x, y, bounds, scale, include_rotate=True):
        for name, rect in _selection_handles(bounds, scale).items():
            if name == "rotate" and not include_rotate:
                continue
            if _point_inside_bounds(x, y, rect):
                return name
        return None

    def _begin_canvas_drag(item, kind, mode, stage_x, stage_y, bounds, resize_handle=None):
        global preview_mode
        if item is None or item.get("locked", False):
            return False
        if kind == "ui_node" and not item.get("widget_id"):
            renpy.notify("This captured widget has no Ren'Py id. Convert its UI screen to a managed copy to edit it.")
            return False
        # Exact Capture is a static screenshot. Direct manipulation switches to
        # Editable Layout so the real preview object follows its selection box.
        if preview_mode == "capture":
            preview_mode = "layout"
            runtime["canvas_cache"] = {}

        props = item.get("properties", {}) or {}
        frame = current_frame()
        selected_screen = screen_for_node(resolve_frame(), item.get("id")) if kind == "ui_node" else None
        center_x = float(bounds.get("x", 0)) + float(bounds.get("width", 1)) / 2.0
        center_y = float(bounds.get("y", 0)) + float(bounds.get("height", 1)) / 2.0
        runtime["drag"] = {
            "mode": mode,
            "resize_handle": resize_handle,
            "item_id": item.get("id"),
            "frame_id": current_frame_id,
            "ui_node": kind == "ui_node",
            "captured_screen_id": selected_screen.get("id") if selected_screen and not selected_screen.get("managed") else None,
            "before": clone(frame.get("changes", {})) if frame else {},
            "stage_x": stage_x,
            "stage_y": stage_y,
            "xpos": props.get("xpos"),
            "ypos": props.get("ypos"),
            "xoffset": props.get("xoffset", 0),
            "yoffset": props.get("yoffset", 0),
            "bounds_x": float(bounds.get("x", 0)),
            "bounds_y": float(bounds.get("y", 0)),
            "width": max(1.0, float(bounds.get("width", 1))),
            "height": max(1.0, float(bounds.get("height", 1))),
            "rotate": props.get("rotate", 0),
            "center_x": center_x,
            "center_y": center_y,
            "start_angle": degrees(atan2(stage_y - center_y, stage_x - center_x)),
            "preview": {},
        }
        runtime["last_drag_render_time"] = 0.0
        return True

    def _set_drag_position(dx=None, dy=None):
        drag = runtime.get("drag") or {}
        xpos = drag.get("xpos")
        ypos = drag.get("ypos")
        if dx is not None:
            if drag.get("ui_node") or (isinstance(xpos, float) and -2.0 <= xpos <= 2.0):
                _set_drag_preview("properties.xoffset", _snap_value(float(drag.get("xoffset", 0) or 0) + dx))
            else:
                base_x = xpos if isinstance(xpos, (int, float)) else drag.get("bounds_x", 0)
                _set_drag_preview("properties.xpos", _snap_value(float(base_x) + dx))
        if dy is not None:
            if drag.get("ui_node") or (isinstance(ypos, float) and -2.0 <= ypos <= 2.0):
                _set_drag_preview("properties.yoffset", _snap_value(float(drag.get("yoffset", 0) or 0) + dy))
            else:
                base_y = ypos if isinstance(ypos, (int, float)) else drag.get("bounds_y", 0)
                _set_drag_preview("properties.ypos", _snap_value(float(base_y) + dy))

    class LiveStudioCanvas(renpy.Displayable):
        def __init__(self, **properties):
            super(LiveStudioCanvas, self).__init__(**properties)
            self.last_geometry = (0, 0, 1.0)
            runtime["canvas_instance"] = self

        def render(self, width, height, st, at):
            width = max(1, int(width))
            height = max(1, int(height))
            result = renpy.Render(width, height)
            result.blit(renpy.render(Solid(CANVAS_BACKGROUND), width, height, st, at), (0, 0))

            stage_width = float(config.screen_width)
            stage_height = float(config.screen_height)
            fit_scale = min(width / stage_width, height / stage_height)
            scale = fit_scale * float(canvas_zoom or 1.0)
            preview_width = max(1, int(round(stage_width * scale)))
            preview_height = max(1, int(round(stage_height * scale)))
            offset_x = int(round((width - preview_width) / 2.0))
            offset_y = int(round((height - preview_height) / 2.0))
            self.last_geometry = (offset_x, offset_y, scale)

            state, bounds_map, preview = _canvas_frame_data()

            if preview is not None:
                try:
                    transformed = Transform(preview, xysize=(preview_width, preview_height))
                    result.blit(renpy.render(transformed, preview_width, preview_height, st, at), (offset_x, offset_y))
                except Exception as exc:
                    log_diagnostic("warning", "Canvas preview render failed", repr(exc))

            if project_setting("grid_enabled", GRID_ENABLED):
                grid_size = max(2, int(project_setting("grid_size", GRID_SIZE) or GRID_SIZE))
                step = max(2, int(round(grid_size * scale)))
                for gx in range(offset_x, offset_x + preview_width + 1, step):
                    _draw_line(result, gx, offset_y, 1, preview_height, "#ffffff0d")
                for gy in range(offset_y, offset_y + preview_height + 1, step):
                    _draw_line(result, offset_x, gy, preview_width, 1, "#ffffff0d")

            if project_setting("guides_enabled", GUIDES_ENABLED):
                center_x = offset_x + preview_width / 2.0
                center_y = offset_y + preview_height / 2.0
                _draw_line(result, center_x, offset_y, 1, preview_height, GUIDE_COLOR)
                _draw_line(result, offset_x, center_y, preview_width, 1, GUIDE_COLOR)

            # Full widget boxes are optional. Keeping them off by default makes
            # captured screens readable and avoids hundreds of tiny render calls.
            if preview_mode == "layout" and project_setting("show_all_bounds", SHOW_ALL_BOUNDS):
                for _z, _depth, item, kind in canvas_items(state):
                    bounds = item_stage_bounds(item, bounds_map)
                    if bounds:
                        _draw_rect(result, offset_x + bounds["x"] * scale, offset_y + bounds["y"] * scale, bounds["width"] * scale, bounds["height"] * scale, "#6f8fb844" if kind == "scene_node" else "#65c7b055", 1)

            item, _parent_id, kind = selected_item(state)
            if item is not None and kind in ("scene_node", "ui_node"):
                bounds = item_stage_bounds(item, bounds_map)
                if bounds:
                    sx = offset_x + bounds["x"] * scale
                    sy = offset_y + bounds["y"] * scale
                    sw = bounds["width"] * scale
                    sh = bounds["height"] * scale
                    _draw_rect(result, sx, sy, sw, sh, SELECTION_COLOR, 2)
                    label = Text(item.get("name", kind), size=16, color=TEXT_COLOR, outlines=[(1, "#000000", 0, 0)])
                    result.blit(renpy.render(label, max(1, width - int(sx)), 30, st, at), (int(sx), max(0, int(sy) - 22)))
                    if not item.get("locked", False) and tool_mode in ("select", "resize", "rotate"):
                        for handle_name, handle in _selection_handles(bounds, scale).items():
                            hx = offset_x + handle["x"] * scale
                            hy = offset_y + handle["y"] * scale
                            hw = max(5, int(round(handle["width"] * scale)))
                            hh = max(5, int(round(handle["height"] * scale)))
                            handle_color = "#8f63ff" if handle_name == "rotate" else "#f2eaff"
                            result.blit(renpy.render(Solid(handle_color), hw, hh, st, at), (int(round(hx)), int(round(hy))))
            return result

        def event(self, ev, x, y, st):
            offset_x, offset_y, scale = self.last_geometry
            scale = scale or 1.0
            stage_x = (x - offset_x) / scale
            stage_y = (y - offset_y) / scale
            inside = 0 <= stage_x <= config.screen_width and 0 <= stage_y <= config.screen_height

            if ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, "button", None) == 1 and inside:
                state = resolve_frame()
                bounds_map = canvas_bounds_map(state)
                selected, _selected_parent, selected_kind = selected_item(state)
                selected_bounds = item_stage_bounds(selected, bounds_map) if selected_kind in ("scene_node", "ui_node") else None

                # Selection handles take priority. Select mode behaves like the
                # original editor: dragging the object moves it, while edge/corner
                # handles resize and the upper handle rotates.
                if selected is not None and selected_bounds and not selected.get("locked", False):
                    handle = _handle_at(stage_x, stage_y, selected_bounds, scale, include_rotate=True)
                    if handle == "rotate" and tool_mode in ("select", "rotate"):
                        global preview_mode
                        preview_mode = "layout"
                        if _begin_canvas_drag(selected, selected_kind, "rotate", stage_x, stage_y, selected_bounds):
                            runtime["canvas_cache"] = {}
                            renpy.redraw(self, 0)
                            raise renpy.IgnoreEvent()
                    elif handle in _RESIZE_DIRECTIONS and tool_mode in ("select", "resize"):
                        preview_mode = "layout"
                        if _begin_canvas_drag(selected, selected_kind, "resize", stage_x, stage_y, selected_bounds, handle):
                            runtime["canvas_cache"] = {}
                            renpy.redraw(self, 0)
                            raise renpy.IgnoreEvent()
                    elif _point_inside_bounds(stage_x, stage_y, selected_bounds) and tool_mode in ("select", "move"):
                        preview_mode = "layout"
                        if _begin_canvas_drag(selected, selected_kind, "move", stage_x, stage_y, selected_bounds):
                            runtime["canvas_cache"] = {}
                            renpy.redraw(self, 0)
                            raise renpy.IgnoreEvent()

                item, kind = hit_test_stage(stage_x, stage_y, state, bounds_map)
                if item is not None:
                    select_item_live(item.get("id"), kind)
                    bounds = item_stage_bounds(item, bounds_map) or {}
                    drag_mode = "move" if tool_mode == "select" else tool_mode
                    if drag_mode in ("move", "resize", "rotate") and not item.get("locked", False):
                        preview_mode = "layout"
                        resize_handle = "se" if drag_mode == "resize" else None
                        if _begin_canvas_drag(item, kind, drag_mode, stage_x, stage_y, bounds, resize_handle):
                            runtime["canvas_cache"] = {}
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                clear_selection_live()
                raise renpy.IgnoreEvent()

            if ev.type == pygame.MOUSEMOTION and runtime.get("drag"):
                buttons = getattr(ev, "buttons", (0, 0, 0))
                if buttons and buttons[0]:
                    _drag_update(stage_x, stage_y)
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()

            if ev.type == pygame.MOUSEBUTTONUP and getattr(ev, "button", None) == 1 and runtime.get("drag"):
                _drag_update(stage_x, stage_y)
                runtime["drag_revision"] = int(runtime.get("drag_revision", 0)) + 1
                runtime["canvas_cache"] = {}
                _drag_finish()
                restart()
                raise renpy.IgnoreEvent()
            return None

        def visit(self):
            # Do not expose every captured runtime screen as a permanent child.
            # Ren'Py calls per_interact on visited ScreenDisplayables, which made
            # the editor repeatedly update the entire game's HUD/UI tree even
            # while those roots were only capture references. Preview screens are
            # rendered explicitly and safely inside render().
            snapshot = runtime.get("snapshot_displayable")
            return [snapshot] if snapshot is not None else []


init -849 python in live_studio:
    def canvas_displayable():
        value = runtime.get("canvas_instance")
        if not isinstance(value, LiveStudioCanvas):
            value = LiveStudioCanvas()
            runtime["canvas_instance"] = value
        return value
