# Canvas rendering, hierarchy-aware hit testing, and photo-editor manipulation.

init -850 python in live_studio:
    from renpy.store import Fixed, Solid, Text, Transform
    try:
        import pygame_sdl2 as pygame
    except Exception:
        import pygame

    def canvas_items(state=None, selectable_only=True):
        state = state or resolve_frame()
        result = []
        order = 0
        for scene_index, scene in enumerate(state.get("scenes", [])):
            if not scene.get("visible", True):
                continue
            for node, _parent_id, depth in walk_nodes(scene.get("nodes", [])):
                if node.get("visible", True) and (not selectable_only or node.get("selectable", True)):
                    result.append((scene_index * 100000 + int(node.get("zorder", order) or order), depth, node, "scene_node"))
                order += 1
        for screen_index, screen in enumerate(state.get("ui_screens", [])):
            if not screen.get("visible", True):
                continue
            for node, _parent_id, depth in walk_nodes(screen.get("nodes", [])):
                if node.get("visible", True) and (not selectable_only or node.get("selectable", True)):
                    result.append((10000000 + screen_index * 100000 + order, depth, node, "ui_node"))
                order += 1
        result.sort(key=lambda value: (value[0], value[1]))
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

    def canvas_bounds_map(state=None):
        state = state or resolve_frame()
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
                        result[node.get("id")] = item_bounds(node)
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

    def _quiet_set_drag_value(item_id, path, value):
        global project_dirty
        frame = current_frame()
        if frame is None:
            return
        frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(item_id, {})[path] = value
        invalidate_resolved_cache()
        project_dirty = True

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
        item_id = drag.get("item_id")
        dx = stage_x - drag.get("stage_x", stage_x)
        dy = stage_y - drag.get("stage_y", stage_y)
        mode = drag.get("mode", "move")

        if mode == "resize":
            width = max(1.0, float(drag.get("width", 1)) + dx)
            height = max(1.0, float(drag.get("height", 1)) + dy)
            _quiet_set_drag_value(item_id, "properties.xsize", _snap_value(width))
            _quiet_set_drag_value(item_id, "properties.ysize", _snap_value(height))
            return

        if mode == "rotate":
            _quiet_set_drag_value(item_id, "properties.rotate", float(drag.get("rotate", 0) or 0) + dx * 0.5)
            return

        xpos = drag.get("xpos")
        ypos = drag.get("ypos")
        xoffset = drag.get("xoffset", 0) or 0
        yoffset = drag.get("yoffset", 0) or 0
        # Screen-language children are positioned by their parent layout. Move
        # them with offsets so dragging never turns a parent-relative widget
        # into an accidental full-screen coordinate.
        if drag.get("ui_node") or (isinstance(xpos, float) and -2.0 <= xpos <= 2.0):
            _quiet_set_drag_value(item_id, "properties.xoffset", _snap_value(xoffset + dx))
        else:
            base_x = xpos if isinstance(xpos, (int, float)) else drag.get("bounds_x", 0)
            _quiet_set_drag_value(item_id, "properties.xpos", _snap_value(base_x + dx))
        if drag.get("ui_node") or (isinstance(ypos, float) and -2.0 <= ypos <= 2.0):
            _quiet_set_drag_value(item_id, "properties.yoffset", _snap_value(yoffset + dy))
        else:
            base_y = ypos if isinstance(ypos, (int, float)) else drag.get("bounds_y", 0)
            _quiet_set_drag_value(item_id, "properties.ypos", _snap_value(base_y + dy))

    def _drag_finish():
        drag = runtime.get("drag")
        runtime["drag"] = None
        if not drag:
            return
        frame = frame_by_id(drag.get("frame_id"))
        if frame is None:
            return
        label = {"move": "Move item", "resize": "Resize item", "rotate": "Rotate item"}.get(drag.get("mode"), "Edit item")
        _record_frame_change(label, drag.get("before", {}), clone(frame.get("changes", {})), drag.get("frame_id"))

    def _node_displayable(item, kind, text_override=None):
        props = item.get("properties", {})
        node_type = str(item.get("type") or "").lower()
        if node_type == "image":
            image_name = item.get("image") or props.get("image") or item.get("name")
            try:
                return renpy.displayable(image_name)
            except Exception:
                return Solid("#7a3444")
        if node_type == "text":
            return Text(
                str(text_override if text_override is not None else props.get("text", item.get("text", item.get("name", "Text")))),
                size=int(props.get("size", 30) or 30),
                color=str(props.get("color", TEXT_COLOR)),
                bold=bool(props.get("bold", False)),
                italic=bool(props.get("italic", False)),
            )
        if node_type == "imagebutton":
            image_name = props.get("idle") or props.get("hover")
            if image_name:
                try:
                    return renpy.displayable(image_name)
                except Exception:
                    pass
            return Fixed(Solid("#20344dcc"), Transform(Text("Image Button", size=22, color=TEXT_COLOR), xalign=0.5, yalign=0.5))
        if node_type in ("hotspot", "textbutton", "button"):
            # Canvas preview intentionally does not execute actions.
            label_text = text_override if text_override is not None else props.get("text", item.get("name", "Button"))
            label = Text(str(label_text), size=int(props.get("size", 24) or 24), color=str(props.get("color", TEXT_COLOR)))
            return Fixed(Solid(str(props.get("background", "#20344dcc"))), Transform(label, xalign=0.5, yalign=0.5))
        if node_type in ("frame", "window", "fixed", "vbox", "hbox", "viewport", "vpgrid", "grid", "side"):
            background = props.get("background")
            return Solid(str(background)) if background else NullPreviewDisplayable()
        if node_type in ("add",):
            try:
                return renpy.displayable(props.get("image") or item.get("image") or item.get("name"))
            except Exception:
                return NullPreviewDisplayable()
        return NullPreviewDisplayable()

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
        binding = str(item.get("binding") or item.get("properties", {}).get("binding") or item.get("widget_id") or "").lower().split(".")[-1]
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
            root = runtime_screen_root(screen)
            if root is not None:
                try:
                    captured_screen_children.append(Transform(root, xpos=0, ypos=0))
                except Exception as exc:
                    log_diagnostic("warning", "Captured screen preview failed", {"screen": screen.get("name"), "error": repr(exc)})

        return scene_children + captured_screen_children + managed_ui_children

    class LiveStudioCanvas(renpy.Displayable):
        def __init__(self, **properties):
            super(LiveStudioCanvas, self).__init__(**properties)
            self.last_geometry = (0, 0, 1.0)

        def render(self, width, height, st, at):
            width = max(1, int(width))
            height = max(1, int(height))
            result = renpy.Render(width, height)
            result.blit(renpy.render(Solid(CANVAS_BACKGROUND), width, height, st, at), (0, 0))

            stage_width = float(config.screen_width)
            stage_height = float(config.screen_height)
            scale = min(width / stage_width, height / stage_height)
            preview_width = max(1, int(round(stage_width * scale)))
            preview_height = max(1, int(round(stage_height * scale)))
            offset_x = int(round((width - preview_width) / 2.0))
            offset_y = int(round((height - preview_height) / 2.0))
            self.last_geometry = (offset_x, offset_y, scale)

            state = resolve_frame()
            bounds_map = canvas_bounds_map(state)
            if preview_mode == "capture":
                preview = runtime.get("snapshot_displayable")
            else:
                try:
                    preview = Fixed(*_layout_preview_children(state, bounds_map), xysize=(int(stage_width), int(stage_height)))
                except Exception as exc:
                    log_diagnostic("error", "Layout preview construction failed", repr(exc))
                    preview = runtime.get("snapshot_displayable")

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
                    _draw_rect(result, gx, offset_y, 1, preview_height, "#ffffff10", 1)
                for gy in range(offset_y, offset_y + preview_height + 1, step):
                    _draw_rect(result, offset_x, gy, preview_width, 1, "#ffffff10", 1)

            # Bounds remain visible in layout mode, making unsupported/runtime
            # widgets selectable even when Ren'Py cannot recreate their visuals.
            if preview_mode == "layout":
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
                item, kind = hit_test_stage(stage_x, stage_y, state, bounds_map)
                if item is not None:
                    select_item(item.get("id"), kind)
                    if tool_mode in ("move", "resize", "rotate") and not item.get("locked", False):
                        props = item.get("properties", {})
                        bounds = item_stage_bounds(item, bounds_map) or {}
                        frame = current_frame()
                        runtime["drag"] = {
                            "mode": tool_mode,
                            "item_id": item.get("id"),
                            "frame_id": current_frame_id,
                            "ui_node": kind == "ui_node",
                            "before": clone(frame.get("changes", {})) if frame else {},
                            "stage_x": stage_x,
                            "stage_y": stage_y,
                            "xpos": props.get("xpos"),
                            "ypos": props.get("ypos"),
                            "xoffset": props.get("xoffset", 0),
                            "yoffset": props.get("yoffset", 0),
                            "bounds_x": bounds.get("x", 0),
                            "bounds_y": bounds.get("y", 0),
                            "width": bounds.get("width", 1),
                            "height": bounds.get("height", 1),
                            "rotate": props.get("rotate", 0),
                        }
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()
                clear_selection()
                raise renpy.IgnoreEvent()

            if ev.type == pygame.MOUSEMOTION and runtime.get("drag"):
                buttons = getattr(ev, "buttons", (0, 0, 0))
                if buttons and buttons[0]:
                    _drag_update(stage_x, stage_y)
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent()

            if ev.type == pygame.MOUSEBUTTONUP and getattr(ev, "button", None) == 1 and runtime.get("drag"):
                _drag_update(stage_x, stage_y)
                _drag_finish()
                restart()
                raise renpy.IgnoreEvent()
            return None

        def visit(self):
            children = []
            snapshot = runtime.get("snapshot_displayable")
            if snapshot is not None:
                children.append(snapshot)
            for value in runtime.get("screen_index", {}).values():
                root = value.get("root") if isinstance(value, dict) else None
                if root is not None and root not in children:
                    children.append(root)
            return children
