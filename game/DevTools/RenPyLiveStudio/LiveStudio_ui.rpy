# UI screen/widget inspection, managed UI creation, and structured actions.

init -960 python in live_studio:
    import ast as _py_ast
    import re as _ui_re
    import os as _ui_os
    import copy as _ui_copy

    try:
        from renpy.display.screen import ScreenDisplayable
    except Exception:
        ScreenDisplayable = ()

    class FrozenRuntimeDisplayable(renpy.Displayable):
        """A non-interactive render snapshot of one captured runtime screen.

        The original runtime screen tree can contain DynamicDisplayables, text
        substitutions, and screen-language functions that re-run at interaction
        boundaries. Live Studio only needs the pixels that were active when the
        editor opened. Caching the first Render keeps untouched gameplay UI
        visually stable while scene objects are edited and prevents a copied
        screen from losing imagebutton states or evaluating against editor scope.
        """

        def __init__(self, child, offered_width=None, offered_height=None, **properties):
            super(FrozenRuntimeDisplayable, self).__init__(**properties)
            self.child = child
            self.offered_width = int(offered_width or config.screen_width)
            self.offered_height = int(offered_height or config.screen_height)
            self._frozen_render = None
            self._freeze_error = None

        def freeze(self):
            if self._frozen_render is not None or self.child is None:
                return self._frozen_render
            try:
                self._frozen_render = renpy.render(
                    self.child, self.offered_width, self.offered_height, 0.0, 0.0
                )
            except Exception as exc:
                self._freeze_error = repr(exc)
            return self._frozen_render

        def render(self, width, height, st, at):
            frozen = self.freeze()
            if frozen is None:
                return renpy.Render(max(1, int(width)), max(1, int(height)))
            try:
                render_width, render_height = frozen.get_size()
            except Exception:
                render_width, render_height = self.offered_width, self.offered_height
            result = renpy.Render(max(1, int(render_width)), max(1, int(render_height)))
            result.blit(frozen, (0, 0))
            return result

        def visit(self):
            # The cached Render is drawn explicitly. Returning the source child
            # would cause Ren'Py to call per_interact on the captured game UI.
            return []

    def freeze_runtime_displayable(displayable):
        if displayable is None:
            return None
        frozen = FrozenRuntimeDisplayable(displayable, config.screen_width, config.screen_height)
        if frozen.freeze() is None:
            log_diagnostic("warning", "Runtime screen could not be frozen", frozen._freeze_error or {})
            return displayable
        return frozen

    KNOWN_RENPY_ACTIONS = {
        "Jump", "Call", "Return", "Show", "Hide", "ToggleScreen", "ShowMenu",
        "SetVariable", "SetField", "ToggleVariable", "ToggleField", "Play",
        "Stop", "Queue", "If", "Confirm", "NullAction", "Function",
    }


    def _screen_source_path(screen_displayable):
        location = getattr(getattr(screen_displayable, "screen", None), "location", None)
        if isinstance(location, (tuple, list)) and location:
            location = location[0]
        return str(location or "").replace("\\", "/").lower()

    def _source_is_renpy_engine_screen(source_path):
        value = str(source_path or "").replace("\\", "/").lower()
        if not value:
            return False
        return (
            "/renpy/common/" in value
            or value.startswith("renpy/common/")
            or "/renpy/screens/" in value
            or value.startswith("renpy/screens/")
            or "/renpy/display/" in value
            or value.startswith("renpy/display/")
        )

    def _source_is_project_developer_screen(source_path):
        value = str(source_path or "").replace("\\", "/").lower()
        if not value:
            return False
        developer_segments = (
            "/devtools/", "/developer/", "/debug/", "/debugger/",
            "/tools/debug", "/engine/debug",
        )
        return any(segment in value for segment in developer_segments)

    def _screen_capture_decision(screen_name, screen_displayable, layer):
        lowered = str(screen_name or "").lower()
        if lowered.startswith("live_studio"):
            return False, "live_studio_self"
        if getattr(screen_displayable, "child", None) is None:
            return False, "inactive_no_child"

        role = _screen_role(screen_name)
        include_dialogue = bool(project_setting("ui_capture_include_dialogue_screens", UI_CAPTURE_DIALOGUE_SCREENS))
        if role in ("say", "choice") and not include_dialogue:
            return False, "dialogue_presentation_managed_separately"

        filter_engine = bool(project_setting("ui_capture_filter_engine_screens", UI_CAPTURE_FILTER_ENGINE_SCREENS))
        if not filter_engine:
            return True, "filter_disabled"

        if lowered in UI_CAPTURE_EXCLUDED_SCREEN_NAMES:
            return False, "excluded_name"
        for pattern in globals().get("UI_CAPTURE_EXCLUDED_SCREEN_PATTERNS", ()):
            if pattern and str(pattern).lower() in lowered:
                return False, "excluded_pattern:{}".format(pattern)

        source_path = _screen_source_path(screen_displayable)
        if _source_is_renpy_engine_screen(source_path):
            if role in UI_CAPTURE_ALLOWED_COMMON_ROLES:
                return True, "allowed_gameplay_common"
            return False, "renpy_engine_source"
        if _source_is_project_developer_screen(source_path):
            return False, "project_developer_source"
        return True, "active_project_screen"

    def _screen_should_capture(screen_name, screen_displayable, layer):
        return _screen_capture_decision(screen_name, screen_displayable, layer)[0]

    def _is_primary_dialogue_presentation(screen_name):
        lowered = str(screen_name or "").strip().lower()
        names = {"say", "choice"}
        try:
            configured = getattr(config, "say_screen_name", None)
            if configured:
                names.add(str(configured).strip().lower())
        except Exception:
            pass
        return lowered in names

    def screen_name_from_displayable(displayable, fallback="screen"):
        value = getattr(displayable, "screen_name", None)
        if value:
            if isinstance(value, (tuple, list)):
                return " ".join(str(part) for part in value)
            return str(value)
        value = getattr(displayable, "name", None)
        return str(value or fallback)

    def _action_data(action):
        result = {}
        try:
            for key, value in vars(action).items():
                if key.startswith("_"):
                    continue
                result[key] = json_safe(value)
        except Exception:
            pass
        return result

    def serialize_action(action):
        if action is None:
            return None
        if isinstance(action, (list, tuple)):
            return {
                "id": new_id("action"),
                "type": "multiple",
                "editable": True,
                "actions": [item for item in (serialize_action(child) for child in action) if item],
                "source": {"captured_by": "runtime"},
            }
        action_type = action.__class__.__name__
        data = _action_data(action)
        internal = {
            "id": new_id("action"),
            "type": action_type,
            "editable": action_type in KNOWN_RENPY_ACTIONS,
            "data": data,
            "repr": repr(action),
            "source": {"captured_by": "runtime", "runtime_type": action_type},
        }
        # Normalize common Ren'Py actions into Live Studio action types when
        # their fields can be recovered safely.
        if action_type == "Jump":
            internal.update({"type": "jump_label", "target": data.get("label") or data.get("target") or "", "editable": True})
        elif action_type == "Call":
            internal.update({"type": "call_label", "target": data.get("label") or data.get("target") or "", "editable": True})
        elif action_type == "Return":
            internal.update({"type": "return", "editable": True})
        elif action_type == "Show":
            internal.update({"type": "show_screen", "screen": data.get("screen") or data.get("name") or "", "editable": True})
        elif action_type == "Hide":
            internal.update({"type": "hide_screen", "screen": data.get("screen") or data.get("name") or "", "editable": True})
        elif action_type == "SetVariable":
            internal.update({"type": "set_variable", "variable": data.get("variable") or data.get("name") or "", "value": data.get("value", ""), "editable": True})
        return internal

    def displayable_actions(displayable):
        result = []
        for attribute in ("action", "clicked", "alternate", "hovered", "unhovered"):
            try:
                value = getattr(displayable, attribute, None)
            except Exception:
                value = None
            serialized = serialize_action(value)
            if serialized:
                serialized["slot"] = attribute
                result.append(serialized)
        return result

    def displayable_children(displayable):
        result = []
        visit = getattr(displayable, "visit", None)
        if callable(visit):
            try:
                result = list(visit() or [])
            except Exception:
                result = []
        if not result:
            child = getattr(displayable, "child", None)
            if child is not None:
                result = [child]
        unique = []
        seen = set()
        for child in result:
            if child is None or id(child) in seen:
                continue
            seen.add(id(child))
            unique.append(child)
        return unique


    def collect_render_bounds(displayable):
        """Maps runtime displayables to absolute bounds from Ren'Py's render tree.

        Placement properties alone are relative to each layout container and
        cannot locate VBox/HBox children. The Render tree records the actual
        blit offsets after layout, so this provides the visual bounds used by
        the hierarchy and hit-testing overlay.
        """
        result = {}
        try:
            root_render = renpy.render(displayable, config.screen_width, config.screen_height, 0.0, 0.0)
        except Exception as exc:
            log_diagnostic("warning", "Could not inspect screen render tree", repr(exc))
            return result

        def add_bounds(runtime_displayable, x, y, width, height):
            key = id(runtime_displayable)
            value = {"x": float(x), "y": float(y), "width": max(1.0, float(width)), "height": max(1.0, float(height))}
            old = result.get(key)
            if old is None:
                result[key] = value
            else:
                left = min(old["x"], value["x"])
                top = min(old["y"], value["y"])
                right = max(old["x"] + old["width"], value["x"] + value["width"])
                bottom = max(old["y"] + old["height"], value["y"] + value["height"])
                result[key] = {"x": left, "y": top, "width": right - left, "height": bottom - top}

        def walk(render, offset_x, offset_y, ancestors):
            identity = id(render)
            # Render trees may be DAGs: the same cached render can be blitted at
            # multiple positions. Only reject a true cycle in the current path.
            if identity in ancestors:
                return
            next_ancestors = set(ancestors)
            next_ancestors.add(identity)
            try:
                width, height = render.get_size()
            except Exception:
                width, height = (1, 1)
            for runtime_displayable in getattr(render, "render_of", []) or []:
                add_bounds(runtime_displayable, offset_x, offset_y, width, height)
            for child_entry in getattr(render, "children", []) or []:
                try:
                    child, child_x, child_y = child_entry[0], child_entry[1], child_entry[2]
                except Exception:
                    continue
                if hasattr(child, "children") and hasattr(child, "render_of"):
                    walk(child, offset_x + float(child_x), offset_y + float(child_y), next_ancestors)
        walk(root_render, 0.0, 0.0, set())
        return result

    def ui_widget_reverse_map(screen_displayable):
        result = {}
        for attribute in ("widgets", "base_widgets"):
            values = getattr(screen_displayable, attribute, None)
            if not isinstance(values, dict):
                continue
            for widget_id, displayable in values.items():
                if displayable is not None:
                    result[id(displayable)] = str(widget_id)
        return result

    def ui_node_type(displayable):
        class_name = displayable.__class__.__name__
        lowered = class_name.lower()
        if "imagebutton" in lowered:
            return "imagebutton"
        if "button" in lowered:
            return "button"
        if lowered == "text" or lowered.endswith("text"):
            return "text"
        if "window" in lowered or "frame" in lowered:
            return "frame"
        if "viewport" in lowered:
            return "viewport"
        if "vpgrid" in lowered:
            return "vpgrid"
        if "grid" in lowered:
            return "grid"
        if "vbox" in lowered:
            return "vbox"
        if "hbox" in lowered:
            return "hbox"
        if "fixed" in lowered or "multibox" in lowered:
            return "fixed"
        if "bar" in lowered:
            return "bar"
        if "input" in lowered:
            return "input"
        if "drag" in lowered:
            return "drag"
        if "transform" in lowered:
            return "transform"
        if "image" in lowered:
            return "image"
        return "custom"

    def safe_widget_properties(widget_id, screen_name, layer):
        if not widget_id:
            return {}
        try:
            values = renpy.get_displayable_properties(widget_id, screen=screen_name, layer=layer)
            return json_safe(values or {})
        except Exception:
            return {}

    def _expr_source(value):
        if value is None:
            return ""
        try:
            return str(value).strip()
        except Exception:
            return ""

    def _literal_expression(value):
        source = _expr_source(value)
        if not source:
            return None, False
        try:
            return _py_ast.literal_eval(source), True
        except Exception:
            return None, False

    def _screen_ast_metadata(screen_displayable):
        """Returns source metadata keyed by explicit screen-language widget id.

        Screen-language AST nodes preserve the original positional expression,
        unlike the runtime Text displayable which generally only exposes the
        evaluated value. This lets dynamic HUD text export as ``text time_text``
        rather than freezing the value visible during capture.
        """
        result = {"__by_location__": {}, "__anonymous__": {}}
        screen_definition = getattr(screen_displayable, "screen", None)
        root = getattr(screen_definition, "ast", None)
        if root is None:
            return result

        def walk(node):
            keywords = {}
            try:
                keywords = dict(getattr(node, "keyword", []) or [])
            except Exception:
                keywords = {}
            widget_id = None
            raw_id = keywords.get("id")
            if raw_id is not None:
                literal, is_literal = _literal_expression(raw_id)
                if is_literal and literal is not None:
                    widget_id = str(literal)
            node_name = str(getattr(node, "name", "") or "")
            positional = [_expr_source(value) for value in (getattr(node, "positional", []) or [])]
            location = getattr(node, "location", None)
            metadata = {
                "widget_id": widget_id,
                "node_name": node_name,
                "positional": positional,
                "keywords": {str(key): _expr_source(value) for key, value in keywords.items()},
                "location": json_safe(location),
            }
            if widget_id:
                result[widget_id] = metadata
            normalized_name = node_name.lower().strip()
            if normalized_name:
                result["__anonymous__"].setdefault(normalized_name, []).append(metadata)
            if location:
                try:
                    location_key = (str(location[0]), int(location[1]))
                    result["__by_location__"].setdefault(location_key, []).append(metadata)
                except Exception:
                    pass
            for child in getattr(node, "children", []) or []:
                walk(child)
            # Conditional blocks hold children inside entries.
            for entry in getattr(node, "entries", []) or []:
                try:
                    block = entry[-1]
                except Exception:
                    block = None
                if block is not None:
                    walk(block)
        try:
            walk(root)
        except Exception as exc:
            log_diagnostic("warning", "Screen source metadata could not be inspected", repr(exc))
        return result

    def _runtime_source_location(displayable):
        value = getattr(displayable, "_location", None)
        if not value:
            return None
        try:
            return (str(value[0]), int(value[1]))
        except Exception:
            return None

    def _source_meta_for_displayable(source_metadata, widget_id, node_type, displayable):
        if widget_id and widget_id in source_metadata:
            return source_metadata.get(widget_id, {})
        location = _runtime_source_location(displayable)
        candidates = list(source_metadata.get("__by_location__", {}).get(location, [])) if location else []
        compatible = {
            "text": ("text",),
            "button": ("button", "textbutton", "imagebutton", "hotspot"),
            "imagebutton": ("imagebutton",),
            "image": ("add", "image"),
            "frame": ("frame", "window"),
            "vbox": ("vbox",),
            "hbox": ("hbox",),
            "viewport": ("viewport",),
            "vpgrid": ("vpgrid",),
            "grid": ("grid",),
            "input": ("input",),
            "bar": ("bar", "vbar"),
        }.get(node_type, (node_type,))
        for metadata in candidates:
            if str(metadata.get("node_name") or "").lower() in compatible:
                return metadata
        return {}

    def _text_preview_value(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            parts = []
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
            if parts:
                return "".join(parts)
        try:
            return str(value)
        except Exception:
            return ""

    def _human_widget_name(widget_id):
        value = str(widget_id or "").strip()
        if not value:
            return ""
        words = value.replace("-", " ").replace("_", " ").split()
        return " ".join(word[:1].upper() + word[1:] for word in words)

    def _captured_node_name(widget_id, node_type, displayable, source_meta, counter):
        if widget_id:
            return _human_widget_name(widget_id)
        runtime_type = displayable.__class__.__name__
        if node_type == "text":
            expression = ((source_meta or {}).get("positional") or [""])[0]
            if expression:
                return "Text · {}".format(expression[:34])
            preview = _text_preview_value(getattr(displayable, "text", None))
            if preview:
                return "Text · {}".format(preview.replace("\n", " ")[:34])
        if node_type == "image":
            image_name = displayable_image_name(displayable)
            if image_name:
                return image_name
        if node_type in ("button", "imagebutton"):
            return "{} {}".format(node_type.replace("image", "Image ").title(), counter)
        if node_type == "custom":
            return runtime_type
        return "{} {}".format(node_type.title(), counter)

    def _first_child_label(children):
        for child in children or []:
            if child.get("internal"):
                value = _first_child_label(child.get("children", []))
                if value:
                    return value
            binding = child.get("binding")
            if isinstance(binding, dict):
                value = binding.get("preview") or binding.get("expression")
            else:
                value = child.get("properties", {}).get("text")
            if value:
                return str(value).replace("\n", " ")[:36]
            value = _first_child_label(child.get("children", []))
            if value:
                return value
        return ""

    def _text_binding(displayable, source_meta):
        resolved = _text_preview_value(getattr(displayable, "text", None))
        positional = list((source_meta or {}).get("positional") or [])
        expression = positional[0] if positional else ""
        if expression:
            literal, is_literal = _literal_expression(expression)
            if is_literal and isinstance(literal, str):
                # A quoted Ren'Py text string can still be dynamic through text
                # substitution, for example ``"[weekday_name()]"``. Preserve
                # the exact source expression instead of freezing the captured
                # Monday/Tuesday preview.
                dynamic_text = ("[" in literal) or ("{" in literal)
                mode = "renpy_text" if dynamic_text else "literal"
                return {
                    "mode": mode,
                    "expression": expression if dynamic_text else "",
                    "source_expression": expression,
                    "preview": resolved or literal,
                }, literal
            return {"mode": "expression", "expression": expression, "source_expression": expression, "preview": resolved}, resolved
        return {"mode": "runtime", "expression": "", "source_expression": "", "preview": resolved}, resolved

    def _neutral_runtime_wrapper(node_type, widget_id, actions, children, displayable, placement=None, measured=None):
        """Returns True only for anonymous wrappers that add no authored layout.

        Ren'Py inserts Fixed/MultiBox/Transform helpers around conditions and
        screen roots. Exposing them produces full-screen selectable boxes such
        as ``HUD Root`` or invisible debug roots. We flatten only wrappers with
        no id, action, background, clipping, or non-default transform so child
        coordinates remain valid.
        """
        if widget_id or actions or not children:
            return False
        node_type = str(node_type or "").lower()
        runtime_name = displayable.__class__.__name__.lower()
        if runtime_name in ("showif", "condition_switch", "conditionswitch", "dynamicdisplayable", "imagemapcache"):
            return True
        placement = placement or {}
        transform_keys = {
            "xpos", "ypos", "xanchor", "yanchor", "xalign", "yalign",
            "xoffset", "yoffset", "rotate", "zoom", "xzoom", "yzoom",
            "crop", "matrixtransform", "perspective",
        }
        for key in transform_keys:
            value = placement.get(key)
            if value in (None, 0, 0.0, 1, 1.0, False):
                continue
            return False
        if node_type in ("transform", "custom"):
            return True
        if node_type == "fixed" and runtime_name in ("fixed", "multibox"):
            return True
        return False

    def _displayable_content_properties(displayable, node_type, source_meta=None):
        result = {}
        binding = None
        if node_type == "text":
            binding, preview = _text_binding(displayable, source_meta)
            result["text"] = preview
        elif node_type == "button":
            result.setdefault("text", "Button")
        elif node_type == "imagebutton":
            for state_name in ("idle", "hover", "insensitive", "selected_idle", "selected_hover"):
                value = getattr(displayable, state_name, None)
                if value is None:
                    continue
                image_name = displayable_image_name(value)
                if image_name:
                    result[state_name] = image_name
        image_name = displayable_image_name(displayable)
        if image_name and node_type == "image":
            result["image"] = image_name
        return result, binding

    def _captured_bounds_union(children):
        rects = [child.get("bounds") for child in children if child.get("bounds")]
        if not rects:
            return None
        left = min(float(rect.get("x", 0)) for rect in rects)
        top = min(float(rect.get("y", 0)) for rect in rects)
        right = max(float(rect.get("x", 0)) + float(rect.get("width", 0)) for rect in rects)
        bottom = max(float(rect.get("y", 0)) + float(rect.get("height", 0)) for rect in rects)
        return {"x": left, "y": top, "width": max(1.0, right-left), "height": max(1.0, bottom-top)}

    def _captured_node_is_meaningful(node_type, measured, child_nodes, actions, properties):
        if child_nodes:
            return True
        # A runtime leaf is only gameplay UI when it actually participated in
        # the captured render. visit() also exposes prediction/inactive branches.
        if measured is None:
            return False
        node_type = str(node_type or "").lower()
        if node_type in ("text", "image", "add", "button", "textbutton", "imagebutton", "bar", "input", "hotspot", "drag"):
            return True
        if actions:
            return True
        return bool(properties.get("background") or properties.get("foreground") or properties.get("image"))

    def capture_ui_nodes(displayable, reverse_map, render_bounds, source_metadata, screen_name, layer, depth, counter, ancestors, structural_path="0"):
        if displayable is None or id(displayable) in ancestors:
            return []
        if depth > UI_CAPTURE_MAX_DEPTH or counter[0] >= UI_CAPTURE_MAX_NODES:
            return []
        next_ancestors = set(ancestors)
        next_ancestors.add(id(displayable))
        counter[0] += 1

        widget_id = reverse_map.get(id(displayable))
        node_type = ui_node_type(displayable)
        source_meta = _source_meta_for_displayable(source_metadata, widget_id, node_type, displayable)
        actions = displayable_actions(displayable)
        child_nodes = []
        for child_index, child in enumerate(displayable_children(displayable)):
            child_path = "{}.{}".format(structural_path, child_index)
            child_nodes.extend(capture_ui_nodes(child, reverse_map, render_bounds, source_metadata, screen_name, layer, depth + 1, counter, next_ancestors, child_path))

        measured = render_bounds.get(id(displayable))
        widget_properties = safe_widget_properties(widget_id, screen_name, layer)
        placement = placement_properties(displayable)
        properties = clone(widget_properties)
        for key, value in placement.items():
            properties.setdefault(key, value)
        content_properties, binding = _displayable_content_properties(displayable, node_type, source_meta)
        properties.update({key: value for key, value in content_properties.items() if key not in properties})

        try:
            runtime_visible = bool(getattr(displayable, "visible", True))
        except Exception:
            runtime_visible = True
        try:
            runtime_alpha = float(properties.get("alpha", 1.0) if properties.get("alpha") is not None else 1.0)
        except Exception:
            runtime_alpha = 1.0
        if not runtime_visible or runtime_alpha <= 0.0001:
            return []

        if not _captured_node_is_meaningful(node_type, measured, child_nodes, actions, properties):
            return []
        if _neutral_runtime_wrapper(node_type, widget_id, actions, child_nodes, displayable, placement, measured):
            return child_nodes

        name = _captured_node_name(widget_id, node_type, displayable, source_meta, counter[0])
        child_label = _first_child_label(child_nodes)
        if not widget_id and child_label:
            if node_type in ("button", "textbutton", "imagebutton"):
                name = "{} · {}".format("Image Button" if node_type == "imagebutton" else "Button", child_label)
            elif node_type in ("frame", "window"):
                name = "{} · {}".format(node_type.title(), child_label)
        node = new_ui_node(name, node_type, widget_id)
        location_key = source_meta.get("location") or ""
        identity_part = "id:{}".format(widget_id) if widget_id else "path:{}".format(structural_path)
        node["id"] = stable_capture_id("ui_node", screen_name, layer, identity_part, node_type, location_key)
        node["source"] = {
            "screen": screen_name, "layer": layer,
            "runtime_type": displayable.__class__.__name__, "captured_by": "runtime",
            "location": clone(source_meta.get("location")), "screen_language": clone(source_meta),
            "structural_path": structural_path, "rendered_at_capture": measured is not None,
            "provenance": "runtime_observed",
        }
        node["properties"] = properties
        node["captured_properties"] = clone(properties)
        node["resolved_properties"] = clone(placement)
        if binding is not None:
            node["binding"] = binding
        node["bounds"] = clone(measured) if measured is not None else (_captured_bounds_union(child_nodes) or calculate_bounds(placement, *displayable_size(displayable), apply_zoom=False))
        node["actions"] = actions
        node["children"] = child_nodes
        if not widget_id and node_type in ("custom", "transform"):
            node["internal"] = True
            node["selectable"] = False
        if not widget_id:
            node["editability"] = "inspect" if node_type in ("custom", "transform") else "limited"
        elif node["actions"] and not all(action.get("editable") for action in node["actions"]):
            node["editability"] = "limited"
        else:
            node["editability"] = "editable"
        runtime.setdefault("ui_displayables", {})[node["id"]] = displayable
        runtime.setdefault("widget_displayables", {})[node["id"]] = displayable
        return [node]

    def capture_ui_node(displayable, reverse_map, render_bounds, screen_name, layer, depth, counter, ancestors, source_metadata=None):
        values = capture_ui_nodes(displayable, reverse_map, render_bounds, source_metadata or {}, screen_name, layer, depth, counter, ancestors, "0")
        if not values:
            return None
        if len(values) == 1:
            return values[0]
        wrapper = new_ui_node("{} Root".format(_human_widget_name(screen_name) or screen_name), "fixed", None)
        wrapper["editability"] = "inspect"
        wrapper["selectable"] = False
        wrapper["children"] = values
        wrapper["bounds"] = _captured_bounds_union(values)
        wrapper["source"] = {"screen": screen_name, "layer": layer, "captured_by": "runtime", "synthetic": True, "provenance": "runtime_structure"}
        return wrapper

    def _captured_root_is_structural(root_node, screen_name=None):
        """Treats a transparent screen root as the screen folder itself."""
        if not root_node:
            return False
        source = root_node.get("source") or {}
        if source.get("synthetic"):
            return True
        if root_node.get("actions"):
            return False
        if str(root_node.get("type") or "").lower() not in ("fixed", "custom", "transform"):
            return False
        props = root_node.get("properties") or {}
        if props.get("background") or props.get("foreground") or props.get("image"):
            return False
        raw_widget_id = str(root_node.get("widget_id") or "").strip()
        raw_screen_id = str(screen_name or source.get("screen") or "").strip()
        widget_id = safe_identifier(raw_widget_id, "root").lower().strip("_") if raw_widget_id else ""
        screen_id = safe_identifier(raw_screen_id, "screen").lower().strip("_") if raw_screen_id else ""
        structural_ids = {"root", "screen_root", "hud_root"}
        if screen_id:
            structural_ids.update((screen_id, screen_id + "_root", screen_id + "root"))
        if widget_id and widget_id in structural_ids and root_node.get("children"):
            return True
        bounds = root_node.get("bounds") or {}
        area = float(bounds.get("width", 0) or 0) * float(bounds.get("height", 0) or 0)
        stage_area = float(config.screen_width) * float(config.screen_height)
        return bool(root_node.get("children")) and area >= stage_area * 0.72

    def _screen_role(name):
        lowered = str(name or "").lower()
        if lowered == "say" or "dialogue" in lowered:
            return "say"
        if lowered == "choice" or "choice" in lowered:
            return "choice"
        if "quick" in lowered:
            return "quick_menu"
        if "hud" in lowered:
            return "hud"
        return "screen"


    def screen_runtime_key(screen_or_name, tag=None, layer=None):
        if isinstance(screen_or_name, dict):
            screen = screen_or_name
            name = screen.get("name") or screen.get("tag") or "screen"
            tag = screen.get("tag") or name
            layer = screen.get("layer") or "screens"
        else:
            name = screen_or_name or tag or "screen"
            tag = tag or name
            layer = layer or "screens"
        return (str(name), str(tag), str(layer))

    def runtime_screen_root(screen):
        if not screen:
            return None
        direct = runtime.get("screen_roots", {}).get(screen.get("id"))
        if direct is not None:
            return direct
        entry = runtime.get("screen_index", {}).get(screen_runtime_key(screen))
        if entry is not None:
            return entry.get("root")
        # Tags can be altered by transient/say screens. A same-name/layer
        # fallback keeps saved projects previewable in a later SDK run.
        for key, value in runtime.get("screen_index", {}).items():
            if key[0] == str(screen.get("name")) and key[2] == str(screen.get("layer") or "screens"):
                return value.get("root")
        return None

    def runtime_screen_entry(screen):
        if not screen:
            return None
        direct = runtime.get("screen_index", {}).get(screen_runtime_key(screen))
        if direct is not None:
            return direct
        for key, value in runtime.get("screen_index", {}).items():
            if key[0] == str(screen.get("name")) and key[2] == str(screen.get("layer") or "screens"):
                return value
        return None

    _WIDGET_PREVIEW_PROPERTIES = {
        "xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset",
        "xsize", "ysize", "xalign", "yalign", "xfill", "yfill",
        "alpha", "rotate", "xzoom", "yzoom", "zoom", "background",
        "foreground", "padding", "spacing", "color", "size", "font",
        "bold", "italic", "text_align", "outlines",
    }

    def _apply_widget_override(override, node, current=None):
        current = current or node
        props = current.get("properties", {}) or {}
        baseline = node.get("captured_properties", {}) or node.get("resolved_properties", {}) or {}
        for key in _WIDGET_PREVIEW_PROPERTIES:
            if key not in props or props.get(key) is None:
                continue
            # Only emit a widget override when Live Studio changed the captured
            # value. Authored style values and dynamic runtime content remain intact.
            if key in baseline and props.get(key) == baseline.get(key):
                continue
            override[key] = props.get(key)

    def _screen_widget_overrides(screen):
        cache_key = (screen.get("id"), int(runtime.get("state_revision", 0)))
        cache = runtime.setdefault("widget_override_cache", {})
        base = cache.get(cache_key)
        if base is None:
            entry = runtime_screen_entry(screen)
            base = {}
            if entry is not None:
                original = entry.get("widget_properties", {})
                if isinstance(original, dict):
                    for widget_id, values in original.items():
                        try:
                            base[str(widget_id)] = dict(values or {})
                        except Exception:
                            base[str(widget_id)] = {}
            for node, _parent_id, _depth in walk_nodes(screen.get("nodes", [])):
                widget_id = node.get("widget_id")
                if not widget_id:
                    continue
                _apply_widget_override(base.setdefault(str(widget_id), {}), node)
            cache[cache_key] = base
            if len(cache) > 16:
                for old_key in list(cache.keys())[:-10]:
                    cache.pop(old_key, None)

        # Drag previews intentionally do not rebuild runtime ScreenDisplayables.
        # The selection rectangle follows the pointer and committed UI appears on
        # mouse-up. This keeps dynamic text, imagebutton states, and project scope
        # from being re-evaluated thirty times per second inside the editor.
        return base

    def captured_screen_override_signature(screen):
        """A stable key containing only Live Studio-authored widget changes.

        Scene edits and selection changes must not invalidate/re-evaluate a
        captured HUD. The previous cache key used the global state revision, so
        moving a character rebuilt every edited screen even though none of its
        widget overrides changed.
        """
        values = []
        if not screen:
            return tuple(values)
        for node, _parent, _depth in walk_nodes(screen.get("nodes", [])):
            widget_id = node.get("widget_id")
            if not widget_id:
                continue
            props = node.get("properties", {}) or {}
            baseline = node.get("captured_properties", {}) or node.get("resolved_properties", {}) or {}
            for key in sorted(_WIDGET_PREVIEW_PROPERTIES):
                if key not in props or props.get(key) is None:
                    continue
                value = props.get(key)
                if key in baseline and value == baseline.get(key):
                    continue
                values.append((str(widget_id), str(key), repr(json_safe(value))))
        return tuple(values)

    def captured_screen_has_overrides(screen):
        return bool(captured_screen_override_signature(screen))

    def captured_screen_preview(screen):
        """Returns a static runtime preview, applying committed id overrides once.

        Untouched screens always use the exact frozen render captured when Live
        Studio opened. An edited source-backed screen is copied with its original
        scope and widget properties, rendered once, and frozen immediately. It is
        never re-evaluated because a Scene object moved, selection changed, or an
        inspector panel restarted the interaction. Captured UI commits visually
        on mouse-up/property commit rather than rebuilding on every drag event.
        """
        if not screen:
            return None
        entry = runtime_screen_entry(screen)
        exact_root = runtime_screen_root(screen)
        signature = captured_screen_override_signature(screen)
        if entry is None or not signature:
            return exact_root
        capture_serial = (entry or {}).get("capture_serial", runtime.get("capture_serial"))
        source_frame_id = runtime.get("active_preview_source_frame_id")
        key = (screen.get("id"), source_frame_id, capture_serial, signature)
        cache = runtime.setdefault("captured_screen_preview_cache", {})
        if key in cache:
            return cache[key]
        original = entry.get("displayable")
        if original is None:
            return exact_root
        try:
            try:
                preview = original.copy()
            except Exception:
                preview = _ui_copy.copy(original)
            preview.widget_properties = _screen_widget_overrides(screen)
            # Preserve the original screen definition/scope, but force a single
            # rebuild that consumes the new id properties. The resulting pixels
            # are frozen below and no longer participate in later interactions.
            preview.child = None
            if hasattr(preview, "children"):
                preview.children = []
            if hasattr(original, "phase"):
                preview.phase = original.phase
            if hasattr(preview, "transient"):
                preview.transient = False
            frozen_preview = freeze_runtime_displayable(preview)
            if frozen_preview is None:
                frozen_preview = exact_root
            cache[key] = frozen_preview
            if len(cache) > 24:
                for old_key in list(cache.keys())[:-16]:
                    cache.pop(old_key, None)
            return frozen_preview
        except Exception as exc:
            log_diagnostic("warning", "Captured screen copy could not apply overrides; exact root retained", {"screen": screen.get("name"), "error": repr(exc)})
            return exact_root

    def capture_ui_state():
        result = []
        scene_list = scene_lists()
        runtime["ui_displayables"] = {}
        runtime["widget_displayables"] = {}
        runtime["screen_roots"] = {}
        runtime["screen_raw_roots"] = {}
        runtime["screen_frozen_roots"] = {}
        runtime["screen_displayables"] = {}
        runtime["screen_index"] = {}
        runtime["captured_screen_preview_cache"] = {}
        runtime["active_screen_ids"] = set()
        runtime["active_screen_names"] = []
        runtime["dialogue_presentation_roots"] = []
        inspected_screens = 0
        reasons = {}
        decisions = []
        if scene_list is None or not ScreenDisplayable:
            log_diagnostic("warning", "ScreenDisplayable was unavailable; UI capture was skipped.")
            return result

        ordered_layers = list(UI_LAYERS)
        for layer in runtime_layer_names(scene_list):
            if layer not in ordered_layers:
                ordered_layers.append(layer)
        for layer in ordered_layers:
            try:
                entries = list(scene_list.layers.get(layer, [])) if isinstance(scene_list.layers, dict) else list(scene_list.layers[layer])
            except Exception:
                entries = []
            for index, entry in enumerate(entries):
                tag = entry_tag(entry)
                if not tag:
                    continue
                try:
                    displayable = scene_list.get_displayable_by_tag(layer, tag)
                except Exception:
                    displayable = None
                if not isinstance(displayable, ScreenDisplayable):
                    continue
                inspected_screens += 1
                screen_name = screen_name_from_displayable(displayable, tag)
                allowed, reason = _screen_capture_decision(screen_name, displayable, layer)
                decisions.append({
                    "name": screen_name, "tag": str(tag), "layer": str(layer),
                    "allowed": bool(allowed), "reason": reason,
                    "source": _screen_source_path(displayable),
                })
                if not allowed:
                    reasons[reason] = int(reasons.get(reason, 0)) + 1
                    # Say/choice presentation belongs to Dialogue, not the UI
                    # hierarchy. Keep an exact frozen visual so entering Editable
                    # Layout does not make dialogue scenes lose their text box,
                    # dynamic values, or imagebutton artwork.
                    if reason == "dialogue_presentation_managed_separately" and _is_primary_dialogue_presentation(screen_name):
                        presentation_root = getattr(displayable, "child", None)
                        if presentation_root is not None:
                            frozen_presentation = freeze_runtime_displayable(presentation_root)
                            if frozen_presentation is not None:
                                runtime.setdefault("dialogue_presentation_roots", []).append({
                                    "id": stable_capture_id("dialogue_presentation", screen_name, tag, layer),
                                    "name": screen_name, "tag": str(tag), "layer": str(layer),
                                    "zorder": entry_zorder(entry, index), "root": frozen_presentation,
                                })
                    continue

                location = getattr(getattr(displayable, "screen", None), "location", None)
                location_key = json_safe(location)
                screen = new_ui_screen(screen_name, layer, tag, entry_zorder(entry, index))
                screen["id"] = stable_capture_id("ui_screen", screen_name, tag, layer, location_key)
                screen["managed"] = False
                screen["role"] = _screen_role(screen_name)
                # The stock quick menu is useful to inspect but is rarely meant
                # to be dragged while composing a story scene. Lock the screen
                # folder by default; users can unlock it from Layers when needed.
                if screen["role"] == "quick_menu":
                    screen["locked"] = True
                screen["source"] = {
                    "screen": screen_name, "layer": layer, "tag": tag,
                    "captured_by": "runtime", "provenance": "runtime_observed",
                    "location": location_key, "capture_reason": reason,
                    "runtime_instance": repr(getattr(displayable, "screen_name", None)),
                }
                reverse_map = ui_widget_reverse_map(displayable)
                source_metadata = _screen_ast_metadata(displayable)
                screen["source"]["source_widget_count"] = len([key for key in source_metadata if not str(key).startswith("__")])
                render_bounds = collect_render_bounds(displayable)
                root = getattr(displayable, "child", None)
                counter = [0]
                root_node = capture_ui_node(root, reverse_map, render_bounds, screen_name, layer, 0, counter, set(), source_metadata)
                if root_node is None:
                    reasons["empty_or_inactive"] = int(reasons.get("empty_or_inactive", 0)) + 1
                    continue
                if _captured_root_is_structural(root_node, screen_name):
                    screen["nodes"].extend(root_node.get("children", []))
                    screen["source"]["root_flattened"] = True
                    screen["source"]["flattened_root_widget_id"] = root_node.get("widget_id")
                    screen["source"]["flattened_root_properties"] = clone(root_node.get("properties", {}))
                else:
                    screen["nodes"].append(root_node)
                    screen["source"]["root_flattened"] = False
                if not screen["nodes"]:
                    reasons["empty_or_inactive"] = int(reasons.get("empty_or_inactive", 0)) + 1
                    continue
                screen["editability"] = "limited" if reverse_map else "inspect"
                result.append(screen)
                frozen_root = freeze_runtime_displayable(root)
                runtime["screen_displayables"][screen["id"]] = displayable
                runtime["screen_raw_roots"][screen["id"]] = root
                runtime["screen_frozen_roots"][screen["id"]] = frozen_root
                runtime["screen_roots"][screen["id"]] = frozen_root
                runtime["active_screen_ids"].add(screen["id"])
                runtime["active_screen_names"].append(screen.get("name"))
                runtime["screen_index"][screen_runtime_key(screen)] = {
                    "root": frozen_root, "raw_root": root, "displayable": displayable, "screen_id": screen.get("id"),
                    "scope": getattr(displayable, "scope", {}), "screen": getattr(displayable, "screen", None),
                    "tag": getattr(displayable, "tag", None), "layer": getattr(displayable, "layer", layer),
                    "widget_properties": getattr(displayable, "widget_properties", {}),
                    "capture_serial": runtime.get("capture_serial"),
                    "frozen": isinstance(frozen_root, FrozenRuntimeDisplayable),
                }
                reasons["captured"] = int(reasons.get("captured", 0)) + 1
        filtered = max(0, inspected_screens - len(result))
        runtime["last_ui_capture_filter"] = {
            "inspected": inspected_screens, "captured": len(result), "filtered": filtered,
            "filter_enabled": bool(project_setting("ui_capture_filter_engine_screens", UI_CAPTURE_FILTER_ENGINE_SCREENS)),
            "reasons": reasons, "captured_names": [screen.get("name") for screen in result],
            "captured_ids": [screen.get("id") for screen in result],
            "decisions": decisions[-240:],
        }
        log_diagnostic("info", "UI capture classified runtime screens", runtime["last_ui_capture_filter"])
        return result

    def screen_for_node(state, node_id):
        state = state or resolve_frame()
        for screen in state.get("ui_screens", []):
            if screen.get("id") == node_id:
                return screen
            for node, _parent, _depth in walk_nodes(screen.get("nodes", [])):
                if node.get("id") == node_id:
                    return screen
        return None

    def ui_screen_by_name(state, name):
        for screen in state.get("ui_screens", []):
            if screen.get("name") == name or screen.get("tag") == name:
                return screen
        return None


    def create_editor_ui_screen(name=None):
        state = resolve_frame()
        base = safe_identifier(name or "live_studio_ui", "live_studio_ui")
        existing = set(screen.get("name") for screen in state.get("ui_screens", []))
        final_name = base
        index = 2
        while final_name in existing:
            final_name = "{}_{}".format(base, index)
            index += 1
        created = new_ui_screen(final_name, "screens", final_name, 50)
        created["managed"] = True
        created["editability"] = "editable"
        created["source"] = {"created_by": "live_studio"}
        root = new_ui_node("Root", "fixed", "root")
        root["properties"] = {"xfill": True, "yfill": True}
        root["source"] = {"created_by": "live_studio", "screen": final_name}
        created["nodes"].append(root)
        add_change(None, None, created, root_collection="ui_screens", label="Add UI screen")
        select_item(created.get("id"), "ui_screen")
        set_tree_tab("UI")
        return created

    def _unique_managed_screen_name(base_name):
        base = safe_identifier(base_name, "live_studio_screen")
        existing = set()
        for screen in resolve_frame().get("ui_screens", []):
            existing.add(str(screen.get("name") or ""))
            existing.add(str(screen.get("tag") or ""))
        candidate = base
        index = 2
        while candidate in existing:
            candidate = "{}_{}".format(base, index)
            index += 1
        return candidate

    def _managed_screen_base(name, role="screen", zorder=50):
        screen = new_ui_screen(name, "screens", name, zorder)
        screen["managed"] = True
        screen["editability"] = "editable"
        screen["role"] = role
        screen["source"] = {"created_by": "live_studio"}
        return screen

    def create_say_ui_template(name=None):
        """Creates an editor-owned say screen wired to the Dialogue object."""
        name = _unique_managed_screen_name(name or "live_studio_say")
        screen = _managed_screen_base(name, "say", 80)

        root = new_ui_node("Say Root", "fixed", "say_root")
        root["properties"] = {"xfill": True, "yfill": True}

        window = new_ui_node("Dialogue Window", "window", "window")
        window["properties"] = {
            "xalign": 0.5, "yalign": 1.0, "xsize": int(config.screen_width * 0.92),
            "ysize": int(config.screen_height * 0.25), "background": "#101522e8",
            "padding": 28, "alpha": 1.0,
        }

        content = new_ui_node("Dialogue Content", "vbox", "say_content")
        content["properties"] = {"xfill": True, "yfill": True, "spacing": 10}

        who = new_ui_node("Speaker", "text", "who")
        who["binding"] = "who"
        who["properties"] = {
            "text": "Character", "xalign": 0.0, "size": 30,
            "color": "#8ecbff", "bold": True, "alpha": 1.0,
        }

        what = new_ui_node("Dialogue Text", "text", "what")
        what["binding"] = "what"
        what["properties"] = {
            "text": "Dialogue appears here.", "xalign": 0.0, "size": 28,
            "color": "#ffffff", "alpha": 1.0,
        }

        content["children"] = [who, what]
        window["children"] = [content]
        root["children"] = [window]
        for node, _parent, _depth in walk_nodes([root]):
            node["editability"] = "editable"
            node["source"] = {"created_by": "live_studio", "screen": name}
        screen["nodes"] = [root]

        add_change(None, None, screen, root_collection="ui_screens", label="Add Say UI template")
        controller = ensure_dialogue_controller()
        if controller is not None:
            set_item_value(controller.get("id"), "say_screen", screen.get("id"), "Use Say UI template")
        select_item(screen.get("id"), "ui_screen")
        set_tree_tab("UI")
        return screen

    def create_choice_ui_template(name=None):
        """Creates an editor-owned choice screen wired to the Dialogue object."""
        name = _unique_managed_screen_name(name or "live_studio_choice")
        screen = _managed_screen_base(name, "choice", 90)

        root = new_ui_node("Choice Root", "fixed", "choice_root")
        root["properties"] = {"xfill": True, "yfill": True}

        choices = new_ui_node("Choice List", "vbox", "choice_list")
        choices["properties"] = {
            "xalign": 0.5, "yalign": 0.5, "xsize": min(760, int(config.screen_width * 0.72)),
            "spacing": 16, "alpha": 1.0,
        }

        button = new_ui_node("Choice Button", "button", "choice_button")
        button["properties"] = {
            "text": "Choice", "xfill": True, "ysize": 76,
            "background": "#17253ee8", "hover_background": "#2d5484f2",
            "color": "#ffffff", "size": 28, "text_align": 0.5,
            "padding": 18, "alpha": 1.0,
        }
        choices["children"] = [button]
        root["children"] = [choices]
        for node, _parent, _depth in walk_nodes([root]):
            node["editability"] = "editable"
            node["source"] = {"created_by": "live_studio", "screen": name}
        screen["nodes"] = [root]

        add_change(None, None, screen, root_collection="ui_screens", label="Add Choice UI template")
        controller = ensure_dialogue_controller()
        if controller is not None:
            set_item_value(controller.get("id"), "choice_screen", screen.get("id"), "Use Choice UI template")
        select_item(screen.get("id"), "ui_screen")
        set_tree_tab("UI")
        return screen

    def ensure_editor_ui_screen(screen_id=None, name="live_studio_ui"):
        state = resolve_frame()
        screen = None
        if screen_id:
            screen, _parent, kind = find_state_item(state, screen_id)
            if kind != "ui_screen":
                screen = None
        if screen is None:
            selected, _parent, kind = selected_item(state)
            if kind == "ui_screen" and selected.get("managed"):
                screen = selected
        if screen is None:
            screen = ui_screen_by_name(state, name)
        if screen is None or not screen.get("managed"):
            created = new_ui_screen(name, "screens", name, 50)
            created["managed"] = True
            created["editability"] = "editable"
            created["source"] = {"created_by": "live_studio"}
            root = new_ui_node("Root", "fixed", "root")
            root["properties"] = {"xfill": True, "yfill": True}
            root["source"] = {"created_by": "live_studio", "screen": name}
            created["nodes"].append(root)
            add_change(None, None, created, root_collection="ui_screens", label="Add UI screen")
            screen = next((item for item in resolve_frame().get("ui_screens", []) if item.get("id") == created.get("id")), created)
        return screen

    def _managed_parent(screen_id=None, parent_id=None):
        screen = ensure_editor_ui_screen(screen_id)
        if screen is None:
            return None, None
        if parent_id:
            parent, _grandparent, kind = find_state_item(resolve_frame(), parent_id)
            if kind == "ui_node":
                return screen, parent
        selected, _parent, kind = selected_item()
        if kind == "ui_node" and selected.get("source", {}).get("screen") == screen.get("name"):
            return screen, selected
        root = screen.get("nodes", [None])[0] if screen.get("nodes") else None
        return screen, root

    def _add_managed_node(node, screen_id=None, parent_id=None, label="Add UI item"):
        screen, parent = _managed_parent(screen_id, parent_id)
        if screen is None:
            return None
        node["source"] = {"created_by": "live_studio", "screen": screen.get("name")}
        node["editability"] = "editable"
        if parent is not None:
            parent_type = str(parent.get("type") or "fixed").lower()
            props = node.setdefault("properties", {})
            if parent_type == "vbox":
                alignment = props.get("xalign", props.get("xpos", 0.5))
                props.pop("xpos", None)
                props.pop("xanchor", None)
                props.pop("ypos", None)
                props.pop("yanchor", None)
                props["xalign"] = alignment
            elif parent_type == "hbox":
                alignment = props.get("yalign", props.get("ypos", 0.5))
                props.pop("xpos", None)
                props.pop("xanchor", None)
                props.pop("ypos", None)
                props.pop("yanchor", None)
                props["yalign"] = alignment
            elif parent_type in ("grid", "vpgrid"):
                for key in ("xpos", "ypos", "xanchor", "yanchor"):
                    props.pop(key, None)
        if parent is not None and parent.get("type") in ("fixed", "frame", "vbox", "hbox", "grid", "viewport", "vpgrid"):
            add_change(parent.get("id"), "children", node, label=label)
        else:
            add_change(screen.get("id"), "nodes", node, label=label)
        select_item(node.get("id"), "ui_node")
        return node

    def add_ui_text(screen_id=None, parent_id=None):
        node = new_ui_node("Text", "text", safe_identifier(new_id("text"), "text"))
        node["properties"] = {
            "text": "New text", "xpos": 0.5, "ypos": 0.5,
            "xanchor": 0.5, "yanchor": 0.5, "xsize": 400, "ysize": 60,
            "size": 30, "color": "#ffffff", "text_align": 0.5, "alpha": 1.0,
        }
        node["bounds"] = {"x": config.screen_width * 0.5 - 200, "y": config.screen_height * 0.5 - 30, "width": 400, "height": 60}
        return _add_managed_node(node, screen_id, parent_id, "Add UI text")

    def add_ui_button(screen_id=None, parent_id=None):
        node = new_ui_node("Button", "button", safe_identifier(new_id("button"), "button"))
        node["properties"] = {
            "text": "Button", "xpos": 0.5, "ypos": 0.5,
            "xanchor": 0.5, "yanchor": 0.5, "xsize": 260, "ysize": 70,
            "background": "#20344dcc", "hover_background": "#31537add",
            "color": "#ffffff", "alpha": 1.0,
        }
        node["actions"] = [new_action("jump_frame")]
        node["bounds"] = {"x": config.screen_width * 0.5 - 130, "y": config.screen_height * 0.5 - 35, "width": 260, "height": 70}
        return _add_managed_node(node, screen_id, parent_id, "Add UI button")

    def add_ui_image_button(image_name=None, screen_id=None, parent_id=None):
        image_name = str(image_name or "")
        node = new_ui_node("Image Button", "imagebutton", safe_identifier(new_id("imagebutton"), "imagebutton"))
        node["properties"] = {
            "idle": image_name, "hover": image_name,
            "xpos": 0.5, "ypos": 0.5, "xanchor": 0.5, "yanchor": 0.5,
            "xsize": 260, "ysize": 90, "alpha": 1.0,
        }
        node["actions"] = [new_action("jump_frame")]
        node["bounds"] = {"x": config.screen_width * 0.5 - 130, "y": config.screen_height * 0.5 - 45, "width": 260, "height": 90}
        return _add_managed_node(node, screen_id, parent_id, "Add UI image button")

    def add_ui_image(image_name=None, screen_id=None, parent_id=None):
        image_name = str(image_name or "")
        node = new_ui_node(image_name or "Image", "image", safe_identifier(new_id("image"), "image"))
        node["properties"] = {
            "image": image_name, "xpos": 0.5, "ypos": 0.5,
            "xanchor": 0.5, "yanchor": 0.5, "xsize": 300, "ysize": 300,
            "alpha": 1.0,
        }
        node["bounds"] = {"x": config.screen_width * 0.5 - 150, "y": config.screen_height * 0.5 - 150, "width": 300, "height": 300}
        return _add_managed_node(node, screen_id, parent_id, "Add UI image")

    def add_ui_container(container_type="fixed", screen_id=None, parent_id=None):
        container_type = container_type if container_type in ("fixed", "frame", "vbox", "hbox", "grid", "viewport") else "fixed"
        node = new_ui_node(container_type.title(), container_type, safe_identifier(new_id(container_type), container_type))
        node["properties"] = {
            "xpos": 0.5, "ypos": 0.5, "xanchor": 0.5, "yanchor": 0.5,
            "xsize": 500, "ysize": 300, "spacing": 10,
            "background": "#152033aa" if container_type == "frame" else None,
            "alpha": 1.0,
        }
        node["bounds"] = {"x": config.screen_width * 0.5 - 250, "y": config.screen_height * 0.5 - 150, "width": 500, "height": 300}
        return _add_managed_node(node, screen_id, parent_id, "Add UI container")

    UI_CONTAINER_TYPES = set(("fixed", "frame", "window", "vbox", "hbox", "grid", "viewport", "vpgrid", "side"))

    def is_ui_container(node):
        return bool(node and str(node.get("type") or "").lower() in UI_CONTAINER_TYPES)

    def _convert_node_to_managed_in_place(node, screen_name, used_widget_ids=None):
        """Creates an editor-owned approximation while preserving tree identity."""
        used_widget_ids = used_widget_ids if used_widget_ids is not None else set()
        converted = clone(node)
        raw_widget_id = converted.get("widget_id") or converted.get("type") or "widget"
        base_widget_id = safe_identifier(raw_widget_id, "widget")
        widget_id = base_widget_id
        suffix = 2
        while widget_id in used_widget_ids:
            widget_id = "{}_{}".format(base_widget_id, suffix)
            suffix += 1
        used_widget_ids.add(widget_id)
        converted["widget_id"] = widget_id
        supported_types = {"fixed", "frame", "window", "vbox", "hbox", "grid", "viewport", "vpgrid", "text", "button", "textbutton", "image", "add", "imagebutton", "side"}
        converted["editability"] = "editable" if str(converted.get("type") or "").lower() in supported_types else "limited"
        converted["source"] = {"created_by": "live_studio", "converted_from": clone(node.get("source", {})), "screen": screen_name, "provenance": "converted_approximation"}
        converted["actions"] = [clone(action) for action in converted.get("actions", []) if action.get("editable")]
        children = []
        for child in converted.get("children", []):
            if child.get("internal") and child.get("children"):
                for grandchild in child.get("children", []):
                    children.append(_convert_node_to_managed_in_place(grandchild, screen_name, used_widget_ids))
            elif not child.get("internal"):
                children.append(_convert_node_to_managed_in_place(child, screen_name, used_widget_ids))
        converted["children"] = children
        converted.pop("internal", None)
        return converted

    def convert_screen_in_place(screen_id):
        """Explicitly converts one runtime screen without creating a duplicate."""
        global project_dirty, selected_item_id, selected_item_kind
        state = resolve_frame()
        screen, _parent, kind = find_state_item(state, screen_id)
        if kind != "ui_screen" or screen is None or screen.get("managed"):
            return screen
        frame = current_frame()
        if frame is None:
            return screen
        before = clone(frame.get("changes", {}))
        screen_name = safe_identifier(screen.get("name", "screen"), "screen")
        used_widget_ids = set()
        converted_nodes = [_convert_node_to_managed_in_place(root, screen_name, used_widget_ids) for root in screen.get("nodes", [])]
        sets = frame.setdefault("changes", {}).setdefault("sets", {}).setdefault(screen.get("id"), {})
        sets["managed"] = True
        sets["editability"] = "editable"
        sets["nodes"] = converted_nodes
        sets["source"] = {"created_by": "live_studio", "converted_from": clone(screen.get("source", {})), "provenance": "converted_approximation"}
        after = clone(frame.get("changes", {}))
        invalidate_resolved_cache(True, "runtime UI screen converted explicitly")
        project_dirty = True
        _record_frame_change("Convert UI screen approximation", before, after)
        selected_item_id = screen.get("id")
        selected_item_kind = "ui_screen"
        log_diagnostic("warning", "Runtime screen converted to an editor-owned approximation", {"screen": screen.get("name"), "nodes": len(converted_nodes)})
        restart()
        return find_state_item(resolve_frame(), screen.get("id"))[0]

    def ensure_ui_node_editable(node_id):
        """Compatibility wrapper. Conversion is now explicit, never automatic."""
        state = resolve_frame()
        screen = screen_for_node(state, node_id)
        if screen is None:
            return None
        if not screen.get("managed"):
            return None
        return find_state_item(state, node_id)[0]

    def primary_action(node):
        actions = node.get("actions", []) if node else []
        return actions[0] if actions else None

    def set_node_action_type(node_id, action_type):
        node, _parent, kind = find_state_item(resolve_frame(), node_id)
        if kind not in ("ui_node", "scene_node"):
            return
        actions = clone(node.get("actions", []))
        if actions:
            action = actions[0]
            replacement = new_action(action_type)
            replacement["id"] = action.get("id", replacement["id"])
            actions[0] = replacement
        else:
            actions = [new_action(action_type)]
        set_item_value(node_id, "actions", actions, "Change button action")

    def action_field_changed(node_id, field):
        def changed(value):
            node, _parent, kind = find_state_item(resolve_frame(), node_id)
            if kind not in ("ui_node", "scene_node"):
                return
            actions = clone(node.get("actions", []))
            if not actions:
                actions = [new_action("none")]
            actions[0][field] = parse_editor_value(value, actions[0].get(field, ""))
            set_item_value(node_id, "actions", actions, "Edit button action")
        return changed

    def action_type_changed(node_id):
        return lambda value: set_node_action_type(node_id, value)

    def action_summary(action):
        if not action:
            return "No action"
        action_type = action.get("type", "none")
        if action_type == "jump_frame":
            return "Go to frame: {}".format((frame_by_id(action.get("target_frame_id")) or {}).get("name", "Not set"))
        if action_type in ("jump_label", "call_label"):
            return "{}: {}".format(action_type.replace("_", " ").title(), action.get("target") or "Not set")
        if action_type in ("show_screen", "hide_screen"):
            return "{}: {}".format(action_type.replace("_", " ").title(), action.get("screen") or "Not set")
        if action_type == "multiple":
            return "Multiple actions ({})".format(len(action.get("actions", [])))
        return action_type.replace("_", " ").title()
