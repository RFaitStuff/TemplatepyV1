# Preview/copy-first export. New files are generated in memory. Writing files,
# replacing marker blocks, and patching handwritten source are explicit actions.

init -870 python in live_studio:
    import hashlib
    import os
    import shutil
    import time

    export_cache = {}
    last_export_directory = None

    def copy_text_to_clipboard(text):
        text = str(text or "")
        # ActionEditor3 uses pygame's clipboard. Keep the same proven fallback,
        # while preferring Ren'Py's public clipboard API when available.
        try:
            setter = getattr(renpy, "set_clipboard", None)
            if setter is not None:
                setter(text)
                return True
        except Exception:
            pass
        try:
            try:
                import pygame_sdl2 as pygame
            except Exception:
                import pygame
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
            return True
        except Exception as exc:
            log_diagnostic("warning", "Clipboard copy failed", repr(exc))
            return False

    def quote_renpy_string(value):
        return repr(str(value or ""))

    def format_value(value):
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, dict) and ("absolute" in value or "relative" in value):
            absolute_value = value.get("absolute", 0)
            relative_value = value.get("relative", 0)
            if absolute_value and relative_value:
                return "absolute({}) + {}".format(absolute_value, relative_value)
            if relative_value:
                return repr(relative_value)
            return "absolute({})".format(absolute_value)
        return repr(value)

    def python_expression(value, default="None"):
        value = str(value or "").strip()
        return value if value else default

    def frame_label(frame):
        if not frame:
            return "missing_frame"
        base = safe_identifier(frame.get("name") or "frame", "frame")
        suffix = safe_identifier(frame.get("id") or "frame", "frame")[-8:]
        return "ls_{}_{}".format(base, suffix)

    def _fingerprint(value):
        payload = json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]

    def image_node_map(state):
        result = {}
        for scene in state.get("scenes", []):
            for node, _parent, _depth in walk_nodes(scene.get("nodes", [])):
                if node.get("type") in ("image", "displayable"):
                    result[node.get("id")] = node
        return result

    def non_image_scene_nodes(state):
        result = []
        for scene in state.get("scenes", []):
            if not scene.get("visible", True):
                continue
            for node, _parent, _depth in walk_nodes(scene.get("nodes", [])):
                if node.get("type") not in ("image", "displayable") and node.get("visible", True):
                    result.append(node)
        return result

    def screen_map(state, managed_only=False):
        result = {}
        for screen in state.get("ui_screens", []):
            if managed_only and not screen.get("managed"):
                continue
            result[screen.get("id")] = screen
        return result

    def _transform_property_lines(properties, indent):
        lines = []
        defaults = {
            "xoffset": 0,
            "yoffset": 0,
            "xzoom": 1.0,
            "yzoom": 1.0,
            "zoom": 1.0,
            "rotate": 0.0,
            "alpha": 1.0,
        }
        for key in (
            "xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset",
            "xsize", "ysize", "xzoom", "yzoom", "zoom", "rotate", "alpha",
        ):
            if key not in properties:
                continue
            value = properties.get(key)
            if value is None or (key in defaults and value == defaults[key]):
                continue
            lines.append("{}{} {}".format(indent, key, format_value(value)))
        return lines

    def node_show_lines(node, indent="    "):
        if node.get("type") == "displayable" and not node.get("image"):
            return ["{}# Unsupported captured displayable: {}".format(indent, node.get("name", "displayable"))]
        image_name = str(node.get("image") or node.get("name") or "").strip()
        if not image_name:
            return []
        tag = str(node.get("tag") or image_name.split()[0])
        layer = str(node.get("layer") or "master")
        command = "{}show {}".format(indent, image_name)
        if tag and tag != image_name.split()[0]:
            command += " as {}".format(safe_identifier(tag, "image"))
        if layer != "master":
            command += " onlayer {}".format(safe_identifier(layer, "master"))
        try:
            zorder = int(node.get("zorder", 0) or 0)
        except Exception:
            zorder = 0
        if zorder:
            command += " zorder {}".format(zorder)
        property_lines = _transform_property_lines(node.get("properties", {}), indent + "    ")
        if property_lines:
            return [command + ":"] + property_lines
        return [command]

    def _hide_image_line(node, indent="    "):
        image_name = str(node.get("image") or node.get("name") or "image")
        tag = safe_identifier(node.get("tag") or image_name.split()[0], "image")
        layer = str(node.get("layer") or "master")
        command = "{}hide {}".format(indent, tag)
        if layer != "master":
            command += " onlayer {}".format(safe_identifier(layer, "master"))
        return command

    def frame_visual_diff_lines(frame_id, indent="    "):
        frame = frame_by_id(frame_id)
        state = resolve_frame(frame_id)
        current = image_node_map(state)
        previous = image_node_map(resolve_frame(frame.get("parent_id"))) if frame and frame.get("parent_id") else {}
        lines = []

        for item_id, old_node in previous.items():
            new_node = current.get(item_id)
            if new_node is None or not new_node.get("visible", True):
                lines.append(_hide_image_line(old_node, indent))

        for item_id, node in current.items():
            if not node.get("visible", True):
                continue
            old = previous.get(item_id)
            changed = old is None
            if old is not None:
                for key in ("image", "tag", "layer", "zorder", "properties", "visible"):
                    if old.get(key) != node.get(key):
                        changed = True
                        break
            if changed:
                if old is not None and (old.get("tag") != node.get("tag") or old.get("layer") != node.get("layer")):
                    lines.append(_hide_image_line(old, indent))
                lines.extend(node_show_lines(node, indent))
        return lines

    def action_expression(action):
        action = action or new_action("none")
        action_type = action.get("type", "none")
        if action_type == "jump_frame":
            target = frame_by_id(action.get("target_frame_id"))
            return "Jump({})".format(quote_renpy_string(frame_label(target))) if target else "NullAction()"
        if action_type == "jump_label":
            return "Jump({})".format(quote_renpy_string(action.get("target")))
        if action_type == "call_label":
            return "Call({})".format(quote_renpy_string(action.get("target")))
        if action_type == "return":
            return "Return({})".format(python_expression(action.get("value"), "None"))
        if action_type == "show_screen":
            return "Show({})".format(quote_renpy_string(action.get("screen") or action.get("target")))
        if action_type == "hide_screen":
            return "Hide({})".format(quote_renpy_string(action.get("screen") or action.get("target")))
        if action_type == "set_variable":
            return "SetVariable({}, {})".format(
                quote_renpy_string(action.get("variable")),
                python_expression(action.get("value"), "None"),
            )
        if action_type == "change_variable":
            return "Function(live_studio_change_variable, {}, {}, {})".format(
                quote_renpy_string(action.get("variable")),
                quote_renpy_string(action.get("operator") or "+="),
                python_expression(action.get("value"), "0"),
            )
        if action_type == "run_script":
            return "Function(live_studio_run_script, {})".format(quote_renpy_string(action.get("script")))
        if action_type == "multiple":
            values = [action_expression(child) for child in action.get("actions", [])]
            return "[{}]".format(", ".join(values)) if values else "NullAction()"
        return "NullAction()"

    def _emit_common_screen_properties(node, indent):
        props = node.get("properties", {})
        node_type = str(node.get("type") or "fixed").lower()
        lines = []
        common = (
            "xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset",
            "xsize", "ysize", "xalign", "yalign", "xfill", "yfill",
            "alpha", "rotate", "xzoom", "yzoom",
        )
        for key in common:
            if key in props and props.get(key) is not None:
                lines.append("{}{} {}".format(indent, key, format_value(props.get(key))))
        if node_type in ("hbox", "vbox", "grid", "vpgrid") and props.get("spacing") is not None:
            lines.append("{}spacing {}".format(indent, format_value(props.get("spacing"))))
        if node_type in ("frame", "window", "button", "textbutton") and props.get("padding") is not None:
            lines.append("{}padding {}".format(indent, format_value(props.get("padding"))))
        if node_type == "viewport":
            for key in ("mousewheel", "draggable", "scrollbars"):
                if props.get(key) is not None:
                    lines.append("{}{} {}".format(indent, key, format_value(props.get(key))))
        return lines

    def emit_ui_node(node, indent="    ", context=None):
        if not node.get("visible", True):
            return []
        context = context if context is not None else {}
        lines = []
        node_type = str(node.get("type") or "fixed").lower()
        props = node.get("properties", {})
        children = node.get("children", [])
        widget_id = safe_identifier(node.get("widget_id") or node.get("id"), "widget")
        role = context.get("role", "screen")

        # A managed choice screen uses the first button as the repeatable
        # template for Ren'Py's ChoiceReturn items. This retains the button's
        # visual properties while keeping the menu fully dynamic.
        is_choice_template = role == "choice" and node_type in ("button", "textbutton") and not context.get("choice_emitted")
        if role == "choice" and node_type in ("button", "textbutton") and context.get("choice_emitted"):
            return []
        if is_choice_template:
            context["choice_emitted"] = True
            lines.append("{}for i in items:".format(indent))
            lines.append("{}    textbutton i.caption:".format(indent))
            property_indent = indent + "        "
            lines.extend(_emit_common_screen_properties(node, property_indent))
            for key in ("size", "color", "font", "bold", "italic", "text_align", "outlines"):
                if key in props and props.get(key) is not None:
                    lines.append("{}text_{} {}".format(property_indent, key, format_value(props.get(key))))
            if props.get("background") is not None:
                lines.append("{}background {}".format(property_indent, format_value(props.get("background"))))
            if props.get("hover_background") is not None:
                lines.append("{}hover_background {}".format(property_indent, format_value(props.get("hover_background"))))
            lines.append("{}action i.action".format(property_indent))
            return lines

        text_button = node_type == "textbutton" or (node_type == "button" and not children)
        generic_button = node_type == "button" and bool(children)
        image_button = node_type == "imagebutton"

        if node_type == "text":
            binding = str(node.get("binding") or props.get("binding") or widget_id).lower().split(".")[-1]
            if role == "say" and binding in ("who", "what"):
                context["say_{}_emitted".format(binding)] = True
                lines.append('{}text ({} or ""):'.format(indent, binding))
            else:
                lines.append("{}text {}:".format(indent, quote_renpy_string(props.get("text", node.get("name", "Text")))))
        elif text_button:
            lines.append("{}textbutton {}:".format(indent, quote_renpy_string(props.get("text", node.get("name", "Button")))))
        elif generic_button:
            lines.append("{}button:".format(indent))
        elif image_button:
            lines.append("{}imagebutton:".format(indent))
        elif node_type in ("image", "add"):
            image_name = props.get("image") or node.get("image") or node.get("name")
            lines.append("{}add {}:".format(indent, quote_renpy_string(image_name)))
        elif node_type in ("fixed", "frame", "vbox", "hbox", "viewport", "vpgrid", "side", "window", "grid"):
            if node_type == "grid" and props.get("cols") and props.get("rows"):
                lines.append("{}grid {} {}:".format(indent, int(props.get("cols")), int(props.get("rows"))))
            elif node_type == "side" and props.get("positions"):
                lines.append("{}side {}:".format(indent, quote_renpy_string(props.get("positions"))))
            elif node_type == "vpgrid" and props.get("cols"):
                lines.append("{}vpgrid:".format(indent))
                lines.append("{}    cols {}".format(indent, int(props.get("cols"))))
            elif node_type in ("grid", "side"):
                lines.append("{}fixed:".format(indent))
            else:
                lines.append("{}{}:".format(indent, node_type))
        else:
            lines.append("{}fixed:".format(indent))

        lines.append("{}    id {}".format(indent, quote_renpy_string(widget_id)))
        lines.extend(_emit_common_screen_properties(node, indent + "    "))

        text_keys = ("size", "color", "font", "bold", "italic", "text_align", "outlines")
        if node_type == "text":
            for key in text_keys:
                if key in props and props.get(key) is not None:
                    lines.append("{}    {} {}".format(indent, key, format_value(props.get(key))))
        elif text_button:
            for key in text_keys:
                if key in props and props.get(key) is not None:
                    lines.append("{}    text_{} {}".format(indent, key, format_value(props.get(key))))

        if node_type in ("frame", "window", "button", "textbutton") and props.get("background") is not None:
            lines.append("{}    background {}".format(indent, format_value(props.get("background"))))
        if node_type in ("button", "textbutton") and props.get("hover_background") is not None:
            lines.append("{}    hover_background {}".format(indent, format_value(props.get("hover_background"))))
        if image_button:
            for state_name in ("idle", "hover", "insensitive", "selected_idle", "selected_hover"):
                image_name = props.get(state_name)
                if image_name:
                    lines.append("{}    {} {}".format(indent, state_name, quote_renpy_string(image_name)))
        if text_button or generic_button or image_button:
            lines.append("{}    action {}".format(indent, action_expression(primary_action(node))))

        children_to_emit = children
        if text_button or image_button:
            children_to_emit = []
        elif (generic_button or node_type in ("frame", "window", "viewport")) and len(children) > 1:
            lines.append("{}    fixed:".format(indent))
            for child in children:
                lines.extend(emit_ui_node(child, indent + "        ", context))
            children_to_emit = []
        for child in children_to_emit:
            lines.extend(emit_ui_node(child, indent + "    ", context))
        return lines

    def _managed_screen_definition(screen, variant_name):
        role = str(screen.get("role") or "screen").lower()
        if role == "say":
            lines = ["screen {}(who=None, what=None):".format(variant_name)]
        elif role == "choice":
            lines = ["screen {}(items):".format(variant_name)]
        else:
            lines = ["screen {}():".format(variant_name)]
        context = {"role": role, "choice_emitted": False, "say_who_emitted": False, "say_what_emitted": False}
        if not screen.get("nodes"):
            if role == "choice":
                lines.extend([
                    "    vbox:",
                    "        for i in items:",
                    "            textbutton i.caption action i.action",
                ])
            else:
                lines.append("    pass")
        else:
            for node in screen.get("nodes", []):
                lines.extend(emit_ui_node(node, "    ", context))
            if role == "choice" and not context.get("choice_emitted"):
                lines.extend([
                    "    vbox:",
                    "        xalign 0.5",
                    "        yalign 0.5",
                    "        for i in items:",
                    "            textbutton i.caption action i.action",
                ])
            elif role == "say" and not context.get("say_what_emitted"):
                lines.extend([
                    "    text (what or \"\"):",
                    "        id \"what\"",
                    "        xalign 0.5",
                    "        yalign 0.85",
                ])
        return lines

    def _scene_overlay_definition(name, state):
        nodes = non_image_scene_nodes(state)
        if not nodes:
            return None, []
        lines = ["screen {}():".format(name), "    fixed:", "        id \"scene_overlay_root\""]
        for node in nodes:
            node_type = node.get("type")
            props = clone(node.get("properties", {}))
            if node_type == "text":
                ui_node = new_ui_node(node.get("name", "Text"), "text", safe_identifier(node.get("id"), "text"))
                ui_node["properties"] = props
                ui_node["visible"] = node.get("visible", True)
                lines.extend(emit_ui_node(ui_node, "        "))
            elif node_type == "hotspot":
                ui_node = new_ui_node(node.get("name", "Button"), "textbutton", safe_identifier(node.get("id"), "button"))
                ui_node["properties"] = props
                ui_node["actions"] = clone(node.get("actions", []))
                ui_node["visible"] = node.get("visible", True)
                lines.extend(emit_ui_node(ui_node, "        "))
        return name, lines

    def _screen_export_variants():
        definitions = []
        mapping = {}
        seen = {}
        for frame_id in frame_order():
            state = resolve_frame(frame_id)
            mapping[frame_id] = {}
            for screen in state.get("ui_screens", []):
                if not screen.get("managed") or not screen.get("visible", True):
                    continue
                logical_id = screen.get("id")
                clean = clone(screen)
                clean.pop("source", None)
                clean.pop("editability", None)
                fingerprint = _fingerprint(clean)
                key = (logical_id, fingerprint)
                if key not in seen:
                    base = safe_identifier(screen.get("name"), "live_studio_screen")
                    variant_name = "{}_{}_{}".format(base, safe_identifier(logical_id, "screen")[-6:], fingerprint[:8])
                    seen[key] = variant_name
                    definitions.append(_managed_screen_definition(screen, variant_name))
                mapping[frame_id][logical_id] = seen[key]
        return definitions, mapping

    def _overlay_export_variants():
        definitions = []
        mapping = {}
        seen = {}
        for frame_id in frame_order():
            state = resolve_frame(frame_id)
            nodes = non_image_scene_nodes(state)
            if not nodes:
                mapping[frame_id] = None
                continue
            clean = []
            for node in nodes:
                value = clone(node)
                value.pop("source", None)
                value.pop("bounds", None)
                clean.append(value)
            fingerprint = _fingerprint(clean)
            name = seen.get(fingerprint)
            if name is None:
                name = "ls_scene_overlay_{}".format(fingerprint[:8])
                seen[fingerprint] = name
                _name, lines = _scene_overlay_definition(name, state)
                if lines:
                    definitions.append(lines)
            mapping[frame_id] = name
        return definitions, mapping

    def _dialogue_active_event(frame_id):
        state = resolve_frame(frame_id)
        for controller in state.get("dialogue_controllers", []):
            event = active_dialogue_event(controller, state)
            if event:
                return event
        return None

    def _captured_screen_map(state):
        result = {}
        for screen in state.get("ui_screens", []):
            if screen.get("managed") or not screen.get("visible", True):
                continue
            if str(screen.get("role") or "").lower() in ("say", "choice"):
                continue
            result[screen.get("id")] = screen
        return result

    def _captured_screen_local_overrides(frame_id, screen):
        frame = frame_by_id(frame_id)
        if not frame or not screen:
            return False
        sets = frame.get("changes", {}).get("sets", {})
        for node, _parent_id, _depth in walk_nodes(screen.get("nodes", [])):
            if any(path.startswith("properties.") for path in sets.get(node.get("id"), {})):
                return True
        return False

    def _dialogue_entries(frame_id):
        frame = frame_by_id(frame_id)
        state = resolve_frame(frame_id)
        root_frame = not bool((frame or {}).get("parent_id"))
        result = []
        sets = (frame or {}).get("changes", {}).get("sets", {})
        for controller in state.get("dialogue_controllers", []):
            local = sets.get(controller.get("id"), {})
            if not root_frame and "frame_event_ids" not in local and "active_event_id" not in local:
                continue
            events_by_id = {event.get("id"): event for event in controller.get("events", [])}
            event_ids = list(controller.get("frame_event_ids", []) or [])
            if "frame_event_ids" not in controller and controller.get("active_event_id"):
                event_ids = [controller.get("active_event_id")]
            for event_id in event_ids:
                event = events_by_id.get(event_id)
                if event is not None:
                    result.append((controller, event))
        return result

    def _dialogue_entry(frame_id):
        entries = _dialogue_entries(frame_id)
        return entries[-1] if entries else (None, None)

    def _dialogue_entry_event(frame_id):
        entries = _dialogue_entries(frame_id)
        return entries[-1][1] if entries else None

    def _dialogue_screen_variant(state, current_screens, controller, role):
        if not controller:
            return None
        requested = controller.get("say_screen" if role == "say" else "choice_screen") or role
        candidates = []
        for screen in state.get("ui_screens", []):
            if not screen.get("managed") or not screen.get("visible", True):
                continue
            if screen.get("id") not in current_screens:
                continue
            score = 0
            if screen.get("id") == requested or screen.get("name") == requested or screen.get("tag") == requested:
                score += 10
            if screen.get("role") == role:
                score += 5
            if score:
                candidates.append((score, current_screens.get(screen.get("id"))))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _dialogue_event_terminates(event):
        if not event:
            return False
        return event.get("type") in ("jump", "return", "choice")

    def _frame_flow_lines(frame, index, indent="    "):
        events = [event for _controller, event in _dialogue_entries(frame.get("id"))]
        if any(_dialogue_event_terminates(event) for event in events):
            return []
        edges = [edge for edge in frame.get("edges", []) if frame_by_id(edge.get("target_frame_id"))]
        if len(edges) == 1:
            return ["{}jump {}".format(indent, frame_label(frame_by_id(edges[0].get("target_frame_id"))))]
        if len(edges) > 1:
            lines = ["{}menu:".format(indent)]
            for edge in edges:
                target = frame_by_id(edge.get("target_frame_id"))
                caption = edge.get("label") or (target or {}).get("name") or "Continue"
                condition = str(edge.get("condition", "")).strip()
                suffix = " if {}".format(condition) if condition else ""
                lines.append("{}    {}{}:".format(indent, quote_renpy_string(caption), suffix))
                lines.append("{}        jump {}".format(indent, frame_label(target)))
            return lines
        if frame.get("stop_fallthrough", False):
            return ["{}return".format(indent)]
        order = frame_order()
        if index + 1 < len(order):
            target = frame_by_id(order[index + 1])
            if target:
                return ["{}jump {}".format(indent, frame_label(target))]
        return []

    def build_story_export(screen_variants=None, overlay_variants=None):
        data = ensure_project()
        if screen_variants is None:
            _defs, screen_variants = _screen_export_variants()
        if overlay_variants is None:
            _defs, overlay_variants = _overlay_export_variants()
        lines = [
            "# Generated by Ren'Py Live Studio.",
            "# Copy this preview into a project file or use Export Files.",
            "",
        ]
        order = data.get("frame_order", [])
        for index, frame_id in enumerate(order):
            frame = frame_by_id(frame_id)
            if frame is None:
                continue
            state = resolve_frame(frame_id)
            lines.append("label {}:".format(frame_label(frame)))
            source = frame.get("source_ref") or state.get("source_ref", {})
            if source.get("filename"):
                lines.append("    # Captured from {}:{}".format(source.get("filename"), source.get("line") or "?"))

            body = []
            if not frame.get("parent_id"):
                layers = ["master"]
                for node in image_node_map(state).values():
                    layer = node.get("layer") or "master"
                    if layer not in layers:
                        layers.append(layer)
                for layer in layers:
                    body.append("    scene" if layer == "master" else "    scene onlayer {}".format(safe_identifier(layer, "master")))

            body.extend(frame_visual_diff_lines(frame_id))

            # Scene text/hotspots are exported as one screen-space overlay per frame.
            current_overlay = overlay_variants.get(frame_id)
            parent_overlay = overlay_variants.get(frame.get("parent_id")) if frame.get("parent_id") else None
            if parent_overlay and parent_overlay != current_overlay:
                body.append("    hide screen {}".format(parent_overlay))
            if current_overlay and current_overlay != parent_overlay:
                body.append("    show screen {}".format(current_overlay))

            current_screens = screen_variants.get(frame_id, {})
            parent_screens = screen_variants.get(frame.get("parent_id"), {}) if frame.get("parent_id") else {}
            dialogue_template_ids = set(
                screen.get("id") for screen in state.get("ui_screens", [])
                if str(screen.get("role") or "").lower() in ("say", "choice")
            )
            parent_state = resolve_frame(frame.get("parent_id")) if frame.get("parent_id") else empty_frame_state()
            parent_dialogue_template_ids = set(
                screen.get("id") for screen in parent_state.get("ui_screens", [])
                if str(screen.get("role") or "").lower() in ("say", "choice")
            )
            for logical_id, previous_variant in parent_screens.items():
                if logical_id in parent_dialogue_template_ids:
                    continue
                current_variant = current_screens.get(logical_id)
                if current_variant != previous_variant:
                    body.append("    hide screen {}".format(previous_variant))
            for logical_id, variant in current_screens.items():
                if logical_id in dialogue_template_ids:
                    continue
                if parent_screens.get(logical_id) != variant:
                    body.append("    show screen {}".format(variant))

            # Recreate ordinary captured screens such as HUDs and apply
            # frame-local widget overrides through Ren'Py's public
            # _widget_properties interface. Say/choice screens are handled by
            # dialogue and menus instead.
            current_captured = _captured_screen_map(state)
            parent_captured = _captured_screen_map(parent_state)
            for logical_id, previous_screen in parent_captured.items():
                current_screen = current_captured.get(logical_id)
                if current_screen is None or current_screen.get("name") != previous_screen.get("name"):
                    body.append("    hide screen {}".format(safe_identifier(previous_screen.get("name"), "screen")))
            for logical_id, screen in current_captured.items():
                previous_screen = parent_captured.get(logical_id)
                should_show = previous_screen is None or _captured_screen_local_overrides(frame_id, screen)
                if should_show:
                    body.append("    $ live_studio_show_captured_screen({}, {}, {})".format(
                        quote_renpy_string(screen.get("name")),
                        quote_renpy_string(frame_label(frame)),
                        quote_renpy_string(screen.get("layer") or "screens"),
                    ))

            for controller, event in _dialogue_entries(frame_id):
                say_variant = _dialogue_screen_variant(state, current_screens, controller, "say")
                choice_variant = _dialogue_screen_variant(state, current_screens, controller, "choice")
                body.extend("    " + line if line else "" for line in dialogue_event_source(
                    event, say_screen=say_variant, choice_screen=choice_variant))

            body.extend(_frame_flow_lines(frame, index))
            if not body:
                body.append("    pass")
            lines.extend(body)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def build_screens_export():
        screen_definitions, _screen_mapping = _screen_export_variants()
        overlay_definitions, _overlay_mapping = _overlay_export_variants()
        lines = [
            "# Screens generated by Ren'Py Live Studio.",
            "# Captured handwritten screens remain in their original files unless converted.",
            "",
        ]
        definitions = screen_definitions + overlay_definitions
        if not definitions:
            lines.append("# No editor-owned screens or scene overlays yet.")
        else:
            for definition in definitions:
                lines.extend(definition)
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def collect_widget_overrides():
        result = {}
        for frame_id in frame_order():
            frame = frame_by_id(frame_id)
            if frame is None:
                continue
            state = resolve_frame(frame_id)
            sets = frame.get("changes", {}).get("sets", {})
            frame_values = {}
            for screen in state.get("ui_screens", []):
                if screen.get("managed"):
                    continue
                screen_name = screen.get("name")
                for node, _parent_id, _depth in walk_nodes(screen.get("nodes", [])):
                    widget_id = node.get("widget_id")
                    property_changes = {}
                    for path, value in sets.get(node.get("id"), {}).items():
                        if path.startswith("properties."):
                            property_changes[path.split(".", 1)[1]] = value
                    if widget_id and property_changes:
                        frame_values.setdefault(screen_name, {}).setdefault(widget_id, {}).update(property_changes)
            if frame_values:
                result[frame_label(frame)] = frame_values
        return result

    def _dialogue_speakers():
        speakers = {}
        for frame_id in frame_order():
            for controller in resolve_frame(frame_id).get("dialogue_controllers", []):
                for event in controller.get("events", []):
                    if event.get("type") not in ("say", "choice"):
                        continue
                    display_name = str(event.get("speaker", "")).strip()
                    if not display_name:
                        continue
                    variable = safe_identifier(display_name, "speaker")
                    speakers.setdefault(variable, display_name)
        return speakers

    def build_helpers_export():
        overrides = collect_widget_overrides()
        lines = [
            "# Helper functions, inferred characters, and optional overrides generated by Ren'Py Live Studio.",
            "",
        ]
        speakers = _dialogue_speakers()
        if speakers:
            lines.append("# Remove a generated character definition if your project already defines that variable.")
            for variable, display_name in sorted(speakers.items()):
                lines.append("define {} = Character({})".format(variable, quote_renpy_string(display_name)))
            lines.append("")
        lines.extend([
            "define live_studio_widget_overrides = {}".format(repr(overrides)),
            "",
            "init python:",
            "    def live_studio_show_captured_screen(name, frame_key, layer='screens'):",
            "        frame_values = live_studio_widget_overrides.get(frame_key, {})",
            "        properties = frame_values.get(name, {})",
            "        kwargs = {'_widget_properties': properties}",
            "        if layer:",
            "            kwargs['_layer'] = layer",
            "        renpy.show_screen(name, **kwargs)",
            "",
            "    def live_studio_run_script(source):",
            "        exec(source, renpy.store.__dict__, renpy.store.__dict__)",
            "",
            "    def live_studio_change_variable(name, operator, value):",
            "        parts = str(name).split('.')",
            "        owner = renpy.store",
            "        for part in parts[:-1]:",
            "            if isinstance(owner, dict):",
            "                owner = owner[part]",
            "            else:",
            "                owner = getattr(owner, part)",
            "        field = parts[-1]",
            "        current = owner.get(field, 0) if isinstance(owner, dict) else getattr(owner, field, 0)",
            "        if operator == '+=':",
            "            result = current + value",
            "        elif operator == '-=':",
            "            result = current - value",
            "        elif operator == '*=':",
            "            result = current * value",
            "        elif operator == '/=':",
            "            result = current / value",
            "        else:",
            "            result = value",
            "        if isinstance(owner, dict):",
            "            owner[field] = result",
            "        else:",
            "            setattr(owner, field, result)",
            "",
        ])
        return "\n".join(lines)

    def _validate_python_source(source, mode, context, errors):
        source = str(source or "").strip()
        if not source:
            return
        try:
            compile(source, "<Live Studio {}>".format(context), mode)
        except Exception as exc:
            errors.append("{} is not valid Python: {}".format(context, exc))

    def _validate_action_model(action, context, errors, warnings):
        if not action:
            return
        action_type = action.get("type", "none")
        if action_type == "jump_frame" and not frame_by_id(action.get("target_frame_id")):
            warnings.append("{} has no valid destination frame".format(context))
        elif action_type in ("jump_label", "call_label") and not str(action.get("target", "")).strip():
            warnings.append("{} has no label destination".format(context))
        elif action_type in ("show_screen", "hide_screen") and not str(action.get("screen") or action.get("target") or "").strip():
            warnings.append("{} has no screen name".format(context))
        elif action_type in ("set_variable", "change_variable"):
            if not str(action.get("variable", "")).strip():
                warnings.append("{} has no variable name".format(context))
            _validate_python_source(action.get("value"), "eval", "{} value".format(context), errors)
        elif action_type == "run_script":
            _validate_python_source(action.get("script"), "exec", "{} script".format(context), errors)
        elif action_type == "multiple":
            for index, child in enumerate(action.get("actions", []) or []):
                _validate_action_model(child, "{} action {}".format(context, index + 1), errors, warnings)

    def validate_project_model():
        errors = []
        warnings = []
        data = ensure_project()
        frames = data.get("frames", {})

        # Parent chains must terminate and reference real frames.
        for frame_id, frame in frames.items():
            seen = set()
            current = frame
            while current and current.get("parent_id"):
                parent_id = current.get("parent_id")
                if parent_id not in frames:
                    errors.append("Frame '{}' inherits from a missing frame".format(frame.get("name", frame_id)))
                    break
                if parent_id in seen or parent_id == frame_id:
                    errors.append("Frame '{}' has an inheritance cycle".format(frame.get("name", frame_id)))
                    break
                seen.add(parent_id)
                current = frames.get(parent_id)
            for edge in frame.get("edges", []) or []:
                if not frame_by_id(edge.get("target_frame_id")):
                    errors.append("Frame '{}' has an outgoing path to a missing frame".format(frame.get("name", frame_id)))
                _validate_python_source(edge.get("condition"), "eval", "Frame '{}' path condition".format(frame.get("name", frame_id)), errors)

            state = resolve_frame(frame_id)
            managed_names = set()
            for screen in state.get("ui_screens", []) or []:
                if not screen.get("managed"):
                    continue
                screen_name = safe_identifier(screen.get("name"), "screen")
                if screen_name in managed_names:
                    errors.append("Frame '{}' contains duplicate managed screen name '{}'".format(frame.get("name", frame_id), screen_name))
                managed_names.add(screen_name)
                widget_ids = set()
                for node, _parent_id, _depth in walk_nodes(screen.get("nodes", [])):
                    widget_id = safe_identifier(node.get("widget_id") or node.get("id"), "widget")
                    if widget_id in widget_ids:
                        errors.append("Managed screen '{}' contains duplicate widget id '{}'".format(screen_name, widget_id))
                    widget_ids.add(widget_id)
                    for action_index, action in enumerate(node.get("actions", []) or []):
                        _validate_action_model(action, "{} / {} button {}".format(frame.get("name", frame_id), screen_name, action_index + 1), errors, warnings)

            for scene in state.get("scenes", []) or []:
                for node, _parent_id, _depth in walk_nodes(scene.get("nodes", [])):
                    for action_index, action in enumerate(node.get("actions", []) or []):
                        _validate_action_model(action, "{} / {} hotspot {}".format(frame.get("name", frame_id), scene.get("name", "Scene"), action_index + 1), errors, warnings)

            for controller in state.get("dialogue_controllers", []) or []:
                events = controller.get("events", []) or []
                by_id = {event.get("id"): event for event in events}
                queue = list(controller.get("frame_event_ids", []) or [])
                missing = [event_id for event_id in queue if event_id not in by_id]
                if missing:
                    errors.append("Frame '{}' dialogue queue contains missing events".format(frame.get("name", frame_id)))
                interactions = [by_id[event_id] for event_id in queue if event_id in by_id and dialogue_event_is_interaction(by_id[event_id])]
                if len(interactions) > 1:
                    errors.append("Frame '{}' contains more than one dialogue interaction".format(frame.get("name", frame_id)))
                for event in events:
                    event_context = "Frame '{}' {} event".format(frame.get("name", frame_id), event.get("type", "dialogue"))
                    _validate_python_source(event.get("condition"), "eval", event_context + " condition", errors)
                    if event.get("type") == "script":
                        _validate_python_source(event.get("script"), "exec", event_context, errors)
                    if event.get("type") in ("jump", "call") and not str(event.get("target", "")).strip():
                        warnings.append("{} has no label target".format(event_context))
                    if event.get("type") == "choice":
                        if not event.get("choices"):
                            warnings.append("{} has no choices".format(event_context))
                        for choice in event.get("choices", []) or []:
                            choice_context = "{} choice '{}'".format(event_context, choice.get("caption", "Choice"))
                            _validate_python_source(choice.get("condition"), "eval", choice_context + " condition", errors)
                            _validate_python_source(choice.get("script"), "exec", choice_context + " script", errors)
                            target_frame_id = str(choice.get("target_frame_id", "") or "")
                            if target_frame_id and not frame_by_id(target_frame_id):
                                errors.append("{} points to a missing frame".format(choice_context))
                            if not target_frame_id and not str(choice.get("target", "")).strip() and not str(choice.get("script", "")).strip():
                                warnings.append("{} has no destination or command".format(choice_context))
        return {"errors": errors, "warnings": warnings}

    def validate_exports(values):
        import re
        model_result = validate_project_model()
        errors = list(model_result.get("errors", []))
        warnings = list(model_result.get("warnings", []))
        for section, text in values.items():
            if "\x00" in text:
                errors.append("{} contains a null byte".format(section))
            for line_number, line in enumerate(text.splitlines(), 1):
                if line.strip() and (len(line) - len(line.lstrip(" "))) % 4:
                    warnings.append("{}:{} uses non-4-space indentation".format(section, line_number))
        labels = re.findall(r"(?m)^label\s+([A-Za-z_][A-Za-z0-9_]*)\s*:", values.get("story", ""))
        screens = re.findall(r"(?m)^screen\s+([A-Za-z_][A-Za-z0-9_]*)", values.get("screens", ""))
        if len(labels) != len(set(labels)):
            errors.append("Generated story contains duplicate labels")
        if len(screens) != len(set(screens)):
            errors.append("Generated UI contains duplicate screen names")
        for label in labels:
            if not label.startswith("ls_"):
                warnings.append("Generated label {} does not use the Live Studio prefix".format(label))
        helper_text = values.get("helpers", "")
        marker = "init python:\n"
        if marker in helper_text:
            python_block = helper_text.split(marker, 1)[1]
            python_lines = []
            for line in python_block.splitlines():
                python_lines.append(line[4:] if line.startswith("    ") else line)
            _validate_python_source("\n".join(python_lines), "exec", "generated helper block", errors)
        result = {"errors": errors, "warnings": warnings}
        runtime["export_validation"] = result
        return result

    def generate_exports():
        global export_cache
        screen_definitions, screen_mapping = _screen_export_variants()
        overlay_definitions, overlay_mapping = _overlay_export_variants()
        # build_screens_export recomputes small mappings to keep each builder
        # callable on its own; story receives the already computed mappings.
        export_cache = {
            "story": build_story_export(screen_mapping, overlay_mapping),
            "screens": build_screens_export(),
            "helpers": build_helpers_export(),
        }
        result = validate_exports(export_cache)
        for message in result.get("errors", []):
            log_diagnostic("error", message)
        for message in result.get("warnings", []):
            log_diagnostic("warning", message)
        return export_cache

    def export_preview(section):
        if section not in export_cache:
            generate_exports()
        return export_cache.get(section, "")

    def copy_export(section):
        text = export_preview(section)
        if copy_text_to_clipboard(text):
            renpy.notify("{} copied".format(section))
        else:
            renpy.notify("Clipboard copy failed")

    def export_files():
        global last_export_directory
        values = generate_exports()
        project_id = safe_identifier(ensure_project().get("project", {}).get("id"), "project")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        directory = os.path.join(config.gamedir, EXPORT_DIRECTORY, "{}_{}".format(project_id, timestamp))
        try:
            if not os.path.isdir(directory):
                os.makedirs(directory)
            for section, filename in EXPORT_SECTIONS:
                with open(os.path.join(directory, filename), "w", encoding="utf-8") as output:
                    output.write(values.get(section, ""))
            last_export_directory = directory
            renpy.notify("Exported to {}".format(directory))
            return directory
        except Exception as exc:
            log_diagnostic("error", "Export failed", {"directory": directory, "error": repr(exc)})
            renpy.notify("Export failed")
            return None

    def replace_editor_owned_blocks(path, section="story"):
        settings = ensure_project().get("settings", {})
        if not settings.get("experimental_replace_blocks", False):
            renpy.notify("Experimental block replacement is disabled")
            return False
        marker_id = safe_identifier(ensure_project().get("project", {}).get("id"), "project")
        begin = "# live-studio:begin {} {}".format(marker_id, section)
        end = "# live-studio:end {} {}".format(marker_id, section)
        replacement = begin + "\n" + export_preview(section).rstrip() + "\n" + end
        try:
            original = ""
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as source:
                    original = source.read()
            if begin in original and end in original:
                prefix, remainder = original.split(begin, 1)
                _old, suffix = remainder.split(end, 1)
                updated = prefix + replacement + suffix
            else:
                updated = original.rstrip() + "\n\n" + replacement + "\n"
            if os.path.isfile(path):
                shutil.copy2(path, path + ".live_studio_backup")
            temporary = path + ".tmp"
            with open(temporary, "w", encoding="utf-8") as output:
                output.write(updated)
            os.replace(temporary, path)
            renpy.notify("Editor-owned block replaced")
            return True
        except Exception as exc:
            log_diagnostic("error", "Block replacement failed", {"path": path, "error": repr(exc)})
            return False

    def patch_handwritten_file(path, expected_text, replacement_text):
        settings = ensure_project().get("settings", {})
        if not settings.get("experimental_patch_files", False):
            renpy.notify("Experimental handwritten patching is disabled")
            return False
        try:
            with open(path, "r", encoding="utf-8") as source:
                original = source.read()
            if expected_text not in original:
                raise ValueError("The expected source block no longer matches the file")
            updated = original.replace(expected_text, replacement_text, 1)
            shutil.copy2(path, path + ".live_studio_backup")
            temporary = path + ".tmp"
            with open(temporary, "w", encoding="utf-8") as output:
                output.write(updated)
            os.replace(temporary, path)
            renpy.notify("Handwritten file patched")
            return True
        except Exception as exc:
            log_diagnostic("error", "Handwritten patch failed", {"path": path, "error": repr(exc)})
            renpy.notify("Patch failed")
            return False
