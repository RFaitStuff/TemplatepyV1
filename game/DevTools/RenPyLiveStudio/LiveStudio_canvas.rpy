# Canvas rendering, hit testing, selection, and basic dragging.

init -850 python in live_studio:
    from renpy.store import Solid, Text, Transform
    try:
        import pygame_sdl2 as pygame
    except Exception:
        import pygame

    def canvas_items(state=None):
        state = state or resolve_frame()
        result = []
        order = 0
        for scene_index, scene in enumerate(state.get("scenes", [])):
            if not scene.get("visible", True):
                continue
            for node, _parent_id, depth in walk_nodes(scene.get("nodes", [])):
                if node.get("selectable", True) and node.get("bounds") and node.get("visible", True):
                    result.append((scene_index * 100000 + int(node.get("zorder", order) or order), depth, node, "scene_node"))
                order += 1
        for screen_index, screen in enumerate(state.get("ui_screens", [])):
            if not screen.get("visible", True):
                continue
            for node, _parent_id, depth in walk_nodes(screen.get("nodes", [])):
                if node.get("selectable", True) and node.get("bounds") and node.get("visible", True):
                    result.append((10000000 + screen_index * 100000 + order, depth, node, "ui_node"))
                order += 1
        result.sort(key=lambda value: (value[0], value[1]))
        return result

    def item_stage_bounds(item):
        if not item:
            return None
        original = item.get("bounds") or {}
        properties = item.get("properties") or item.get("resolved_properties") or {}
        explicit_width = properties.get("xsize")
        explicit_height = properties.get("ysize")
        width = explicit_width if explicit_width is not None else original.get("width", 1)
        height = explicit_height if explicit_height is not None else original.get("height", 1)
        try:
            width = float(width or 1)
            height = float(height or 1)
        except Exception:
            width = float(original.get("width", 1) or 1)
            height = float(original.get("height", 1) or 1)

        # Captured bounds already include the runtime transform's zoom. Apply
        # zoom here only to editor-created nodes that have an explicit size.
        if explicit_width is not None or explicit_height is not None:
            xzoom = properties.get("xzoom", properties.get("zoom", 1.0))
            yzoom = properties.get("yzoom", properties.get("zoom", 1.0))
            try:
                width *= float(xzoom or 1.0)
                height *= float(yzoom or 1.0)
            except Exception:
                pass

        if properties.get("xpos") is None and properties.get("ypos") is None:
            return {
                "x": float(original.get("x", 0)),
                "y": float(original.get("y", 0)),
                "width": max(1.0, width),
                "height": max(1.0, height),
            }
        if explicit_width is None and explicit_height is None:
            # Runtime-rendered bounds already include zoom. Preserve that size
            # while still recomputing position/anchor/offset after a drag.
            placement = clone(properties)
            placement["xzoom"] = 1.0
            placement["yzoom"] = 1.0
            placement["zoom"] = 1.0
            return calculate_bounds(placement, width, height)
        return calculate_bounds(properties, width, height)

    def hit_test_stage(x, y):
        for _z, _depth, item, kind in reversed(canvas_items()):
            bounds = item_stage_bounds(item)
            if not bounds:
                continue
            if bounds["x"] <= x <= bounds["x"] + bounds["width"] and bounds["y"] <= y <= bounds["y"] + bounds["height"]:
                return item, kind
        return None, None

    def _draw_rect(render, x, y, width, height, color, thickness=2):
        x = int(round(x))
        y = int(round(y))
        width = max(1, int(round(width)))
        height = max(1, int(round(height)))
        thickness = max(1, int(thickness))
        pieces = (
            (x, y, width, thickness),
            (x, y + height - thickness, width, thickness),
            (x, y, thickness, height),
            (x + width - thickness, y, thickness, height),
        )
        for px, py, pw, ph in pieces:
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

    def _drag_update(stage_x, stage_y):
        drag = runtime.get("drag")
        if not drag:
            return
        item_id = drag.get("item_id")
        dx = stage_x - drag.get("stage_x", stage_x)
        dy = stage_y - drag.get("stage_y", stage_y)
        xpos = drag.get("xpos")
        ypos = drag.get("ypos")
        xoffset = drag.get("xoffset", 0) or 0
        yoffset = drag.get("yoffset", 0) or 0

        if isinstance(xpos, float) and -2.0 <= xpos <= 2.0:
            _quiet_set_drag_value(item_id, "properties.xoffset", xoffset + dx)
        else:
            base_x = xpos if isinstance(xpos, (int, float)) else drag.get("bounds_x", 0)
            _quiet_set_drag_value(item_id, "properties.xpos", base_x + dx)

        if isinstance(ypos, float) and -2.0 <= ypos <= 2.0:
            _quiet_set_drag_value(item_id, "properties.yoffset", yoffset + dy)
        else:
            base_y = ypos if isinstance(ypos, (int, float)) else drag.get("bounds_y", 0)
            _quiet_set_drag_value(item_id, "properties.ypos", base_y + dy)

    def _drag_finish():
        drag = runtime.get("drag")
        runtime["drag"] = None
        if not drag:
            return
        frame = frame_by_id(drag.get("frame_id"))
        if frame is None:
            return
        _record_frame_change("Move item", drag.get("before", {}), clone(frame.get("changes", {})), drag.get("frame_id"))

    class LiveStudioCanvas(renpy.Displayable):
        def __init__(self, **properties):
            super(LiveStudioCanvas, self).__init__(**properties)
            self.last_geometry = (0, 0, 1.0)

        def render(self, width, height, st, at):
            width = max(1, int(width))
            height = max(1, int(height))
            result = renpy.Render(width, height)
            background = renpy.render(Solid(CANVAS_BACKGROUND), width, height, st, at)
            result.blit(background, (0, 0))

            stage_width = float(config.screen_width)
            stage_height = float(config.screen_height)
            scale = min(width / stage_width, height / stage_height)
            preview_width = int(round(stage_width * scale))
            preview_height = int(round(stage_height * scale))
            offset_x = int(round((width - preview_width) / 2.0))
            offset_y = int(round((height - preview_height) / 2.0))
            self.last_geometry = (offset_x, offset_y, scale)

            snapshot = runtime.get("snapshot_displayable")
            if snapshot is not None:
                try:
                    transformed = Transform(snapshot, xzoom=scale, yzoom=scale)
                    rendered = renpy.render(transformed, preview_width, preview_height, st, at)
                    result.blit(rendered, (offset_x, offset_y))
                except Exception as exc:
                    log_diagnostic("warning", "Canvas snapshot render failed: {}".format(exc))

            if preview_mode == "layout":
                shade = renpy.render(Solid("#00000066"), preview_width, preview_height, st, at)
                result.blit(shade, (offset_x, offset_y))
                for _z, _depth, item, kind in canvas_items():
                    bounds = item_stage_bounds(item)
                    if not bounds:
                        continue
                    _draw_rect(
                        result,
                        offset_x + bounds["x"] * scale,
                        offset_y + bounds["y"] * scale,
                        bounds["width"] * scale,
                        bounds["height"] * scale,
                        "#6f8fb866" if kind == "scene_node" else "#65c7b077",
                        1,
                    )

            item, _parent_id, kind = selected_item()
            if item is not None and kind in ("scene_node", "ui_node"):
                bounds = item_stage_bounds(item)
                if bounds:
                    sx = offset_x + bounds["x"] * scale
                    sy = offset_y + bounds["y"] * scale
                    sw = bounds["width"] * scale
                    sh = bounds["height"] * scale
                    _draw_rect(result, sx, sy, sw, sh, SELECTION_COLOR, 2)
                    try:
                        label = Text(item.get("name", kind), size=16, color=TEXT_COLOR, outlines=[(1, "#000000", 0, 0)])
                        label_render = renpy.render(label, max(1, width - int(sx)), 30, st, at)
                        result.blit(label_render, (int(sx), max(0, int(sy) - 22)))
                    except Exception:
                        pass

            return result

        def event(self, ev, x, y, st):
            offset_x, offset_y, scale = self.last_geometry
            if not scale:
                scale = 1.0
            stage_x = (x - offset_x) / scale
            stage_y = (y - offset_y) / scale
            inside = 0 <= stage_x <= config.screen_width and 0 <= stage_y <= config.screen_height

            if ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, "button", None) == 1 and inside:
                item, kind = hit_test_stage(stage_x, stage_y)
                if item is not None:
                    select_item(item.get("id"), kind)
                    properties = item.get("properties", {})
                    bounds = item_stage_bounds(item) or {}
                    frame = current_frame()
                    runtime["drag"] = {
                        "item_id": item.get("id"),
                        "frame_id": current_frame_id,
                        "before": clone(frame.get("changes", {})) if frame else {},
                        "stage_x": stage_x,
                        "stage_y": stage_y,
                        "xpos": properties.get("xpos"),
                        "ypos": properties.get("ypos"),
                        "xoffset": properties.get("xoffset", 0),
                        "yoffset": properties.get("yoffset", 0),
                        "bounds_x": bounds.get("x", 0),
                        "bounds_y": bounds.get("y", 0),
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
                renpy.restart_interaction()
                raise renpy.IgnoreEvent()

            return None

        def visit(self):
            snapshot = runtime.get("snapshot_displayable")
            return [snapshot] if snapshot is not None else []
