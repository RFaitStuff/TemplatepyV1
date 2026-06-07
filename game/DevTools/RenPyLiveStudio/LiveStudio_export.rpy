# Preview/copy-first export. Writing and source patching are always explicit.

init -870 python in live_studio:
    import difflib
    import os
    import shutil
    import time

    export_cache = {}
    last_export_directory = None

    def copy_text_to_clipboard(text):
        try:
            renpy.set_clipboard(str(text))
            return True
        except Exception:
            try:
                from pygame import scrap, locals
                scrap.put(locals.SCRAP_TEXT, str(text).encode("utf-8"))
                return True
            except Exception:
                return False

    def quote_renpy_string(value):
        # repr() safely escapes quotes, backslashes, tabs, and newlines and is
        # accepted by Ren'Py anywhere a Python-style string literal is used.
        return repr(str(value or ""))

    def format_value(value):
        if isinstance(value, str):
            if value.startswith("#"):
                return repr(value)
            return repr(value)
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, dict) and "absolute" in value:
            absolute = value.get("absolute", 0)
            relative = value.get("relative", 0)
            if relative and absolute:
                return "absolute({}) + {}".format(absolute, relative)
            if relative:
                return str(relative)
            return str(absolute)
        return repr(value)

    def image_node_map(state):
        result = {}
        for scene in state.get("scenes", []):
            for node, _parent, _depth in walk_nodes(scene.get("nodes", [])):
                if node.get("type") == "image":
                    result[node.get("id")] = node
        return result

    def screen_map(state):
        return dict((screen.get("id"), screen) for screen in state.get("ui_screens", []))

    def node_show_lines(node, indent="    "):
        image_name = node.get("image") or node.get("name")
        if not image_name:
            return []
        tag = node.get("tag") or str(image_name).split()[0]
        layer = node.get("layer") or "master"
        command = "{}show {}".format(indent, image_name)
        if tag and tag != str(image_name).split()[0]:
            command += " as {}".format(safe_identifier(tag, "image"))
        if layer != "master":
            command += " onlayer {}".format(layer)
        lines = [command + ":"]
        properties = node.get("properties", {})
        emitted = False
        for key in ("xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset", "xzoom", "yzoom", "rotate", "alpha"):
            value = properties.get(key)
            default = {"xoffset": 0, "yoffset": 0, "xzoom": 1.0, "yzoom": 1.0, "rotate": 0.0, "alpha": 1.0}.get(key, None)
            if value is None or value == default:
                continue
            lines.append("{}    {} {}".format(indent, key, format_value(value)))
            emitted = True
        if not emitted:
            lines[-1] = lines[-1][:-1]
        return lines

    def frame_visual_diff_lines(frame_id, indent="    "):
        frame = frame_by_id(frame_id)
        state = resolve_frame(frame_id)
        current = image_node_map(state)
        if frame and frame.get("parent_id"):
            previous = image_node_map(resolve_frame(frame.get("parent_id")))
        else:
            previous = {}

        lines = []
        for item_id, old_node in previous.items():
            if item_id not in current:
                tag = old_node.get("tag") or str(old_node.get("image") or old_node.get("name", "image")).split()[0]
                layer = old_node.get("layer") or "master"
                command = "{}hide {}".format(indent, safe_identifier(tag, "image"))
                if layer != "master":
                    command += " onlayer {}".format(layer)
                lines.append(command)

        for item_id, node in current.items():
            old = previous.get(item_id)
            if old is None or old.get("image") != node.get("image") or old.get("properties") != node.get("properties") or old.get("visible") != node.get("visible"):
                if node.get("visible", True):
                    lines.extend(node_show_lines(node, indent))
                elif old is not None:
                    tag = node.get("tag") or str(node.get("image") or node.get("name", "image")).split()[0]
                    lines.append("{}hide {}".format(indent, safe_identifier(tag, "image")))
        return lines

    def frame_ui_diff_lines(frame_id, indent="    "):
        frame = frame_by_id(frame_id)
        state = resolve_frame(frame_id)
        current = dict((key, value) for key, value in screen_map(state).items() if value.get("managed"))
        previous_state = resolve_frame(frame.get("parent_id")) if frame and frame.get("parent_id") else empty_frame_state()
        previous = dict((key, value) for key, value in screen_map(previous_state).items() if value.get("managed"))
        lines = []
        for screen_id, old_screen in previous.items():
            if screen_id not in current or not current.get(screen_id, {}).get("visible", True):
                lines.append("{}hide screen {}".format(indent, safe_identifier(old_screen.get("name"), "screen")))
        for screen_id, screen in current.items():
            old = previous.get(screen_id)
            if screen.get("visible", True) and (old is None or not old.get("visible", True)):
                lines.append("{}show screen {}".format(indent, safe_identifier(screen.get("name"), "screen")))
        return lines

    def frame_dialogue_lines(frame_id, indent="    "):
        frame = frame_by_id(frame_id)
        state = resolve_frame(frame_id)
        parent_state = resolve_frame(frame.get("parent_id")) if frame and frame.get("parent_id") else empty_frame_state()
        parent_controllers = dict((item.get("id"), item) for item in parent_state.get("dialogue_controllers", []))
        lines = []
        for controller in state.get("dialogue_controllers", []):
            active_id = controller.get("active_event_id")
            if not active_id:
                continue
            parent = parent_controllers.get(controller.get("id"))
            if parent and parent.get("active_event_id") == active_id:
                continue
            event = next((item for item in controller.get("events", []) if item.get("id") == active_id), None)
            if event is None:
                continue
            current_only = clone(controller)
            current_only["events"] = [clone(event)]
            source = dialogue_source(current_only)
            if source.strip():
                for line in source.splitlines():
                    lines.append(indent + line if line else "")
        return lines

    def frame_label(frame):
        # Human-readable names are not guaranteed unique. Stable ID suffixes
        # prevent duplicate label declarations after renames or branching.
        base = safe_identifier(frame.get("name") or "frame", "frame")
        suffix = safe_identifier(frame.get("id") or new_id("frame"), "frame")[-8:]
        return "{}_{}".format(base, suffix)

    def build_story_export():
        data = ensure_project()
        lines = [
            "# Generated by Ren'Py Live Studio.",
            "# Review this preview before placing it in your project.",
            "",
        ]
        order = data.get("frame_order", [])
        for index, frame_id in enumerate(order):
            frame = frame_by_id(frame_id)
            if frame is None:
                continue
            lines.append("label {}:".format(frame_label(frame)))
            source = resolve_frame(frame_id).get("source_ref", {})
            if source.get("filename"):
                lines.append("    # Captured from {}:{}".format(source.get("filename"), source.get("line") or "?"))
            frame_lines = []
            if not frame.get("parent_id"):
                root_layers = []
                for scene in resolve_frame(frame_id).get("scenes", []):
                    for node, _parent_id, _depth in walk_nodes(scene.get("nodes", [])):
                        if node.get("type") == "image" and node.get("layer") not in root_layers:
                            root_layers.append(node.get("layer") or "master")
                for layer in root_layers:
                    frame_lines.append("    scene" if layer == "master" else "    scene onlayer {}".format(layer))
            frame_lines.extend(frame_visual_diff_lines(frame_id))
            frame_lines.extend(frame_ui_diff_lines(frame_id))
            frame_lines.extend(frame_dialogue_lines(frame_id))
            if not frame_lines:
                frame_lines.append("    pass")
            lines.extend(frame_lines)

            edges = frame.get("edges", [])
            if len(edges) == 1:
                target = frame_by_id(edges[0].get("target_frame_id"))
                if target:
                    lines.append("    jump {}".format(frame_label(target)))
            elif not edges and index + 1 < len(order):
                target = frame_by_id(order[index + 1])
                if target:
                    lines.append("    jump {}".format(frame_label(target)))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def created_ui_screens():
        seen = set()
        result = []
        for frame_id in frame_order():
            state = resolve_frame(frame_id)
            for screen in state.get("ui_screens", []):
                if screen.get("id") in seen:
                    continue
                if screen.get("managed") and screen.get("source", {}).get("created_by") == "live_studio":
                    seen.add(screen.get("id"))
                    result.append(screen)
        return result

    def emit_ui_node(node, indent="    "):
        lines = []
        node_type = node.get("type")
        props = node.get("properties", {})
        widget_id = safe_identifier(node.get("widget_id") or node.get("id"), "widget")
        if node_type == "text":
            lines.append("{}text {}:".format(indent, quote_renpy_string(props.get("text", node.get("name", "Text")))))
        elif node_type in ("textbutton", "button"):
            lines.append("{}textbutton {}:".format(indent, quote_renpy_string(props.get("text", node.get("name", "Button")))))
        elif node_type in ("vbox", "hbox", "fixed", "frame", "viewport"):
            lines.append("{}{}:".format(indent, node_type))
        elif node_type == "grid":
            # Grid requires row/column positional arguments. Until those are
            # modeled explicitly, export a Fixed rather than invalid syntax.
            lines.append("{}fixed:".format(indent))
        else:
            lines.append("{}fixed:".format(indent))
        lines.append("{}    id {}".format(indent, quote_renpy_string(widget_id)))
        common_keys = ("xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset", "xsize", "ysize", "xalign", "yalign", "alpha")
        for key in common_keys:
            if key in props and props.get(key) is not None:
                lines.append("{}    {} {}".format(indent, key, format_value(props.get(key))))
        if node_type in ("text", "textbutton", "button"):
            for key in ("size", "color"):
                if key in props and props.get(key) is not None:
                    lines.append("{}    {} {}".format(indent, key, format_value(props.get(key))))
        if node_type in ("textbutton", "button"):
            action = (node.get("actions") or [None])[0]
            if action and action.get("type") == "jump_frame":
                target = frame_by_id(action.get("data", {}).get("target_frame_id"))
                if target:
                    lines.append("{}    action Jump({})".format(indent, quote_renpy_string(frame_label(target))))
                else:
                    lines.append("{}    action NullAction()".format(indent))
            else:
                lines.append("{}    action NullAction()".format(indent))
        for child in node.get("children", []):
            lines.extend(emit_ui_node(child, indent + "    "))
        return lines

    def build_screens_export():
        lines = [
            "# UI screens created by Ren'Py Live Studio.",
            "# Existing handwritten screens are not replaced by this file.",
            "",
        ]
        screens = created_ui_screens()
        if not screens:
            lines.append("# No editor-owned UI screens yet.")
            return "\n".join(lines) + "\n"
        for screen in screens:
            lines.append("screen {}():".format(safe_identifier(screen.get("name"), "live_studio_screen")))
            if not screen.get("nodes"):
                lines.append("    pass")
            for node in screen.get("nodes", []):
                lines.extend(emit_ui_node(node, "    "))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def collect_widget_overrides():
        result = {}
        for frame_id in frame_order():
            frame = frame_by_id(frame_id)
            if frame is None:
                continue
            state = resolve_frame(frame_id)
            changes = frame.get("changes", {}).get("sets", {})
            frame_values = {}
            for screen in state.get("ui_screens", []):
                screen_name = screen.get("name")
                for node, _parent_id, _depth in walk_nodes(screen.get("nodes", [])):
                    widget_id = node.get("widget_id")
                    node_changes = changes.get(node.get("id"), {})
                    property_changes = {}
                    for path, value in node_changes.items():
                        if path.startswith("properties."):
                            property_changes[path.split(".", 1)[1]] = value
                    if widget_id and property_changes:
                        frame_values.setdefault(screen_name, {}).setdefault(widget_id, {}).update(property_changes)
            if frame_values:
                result[frame_label(frame)] = frame_values
        return result

    def build_overrides_export():
        overrides = collect_widget_overrides()
        lines = [
            "# Widget property overrides generated by Ren'Py Live Studio.",
            "# Structure: frame label -> screen name -> widget id -> properties.",
            "# Pass live_studio_widget_overrides[frame_label][screen_name] through _widget_properties.",
            "",
            "define live_studio_widget_overrides = {}".format(repr(overrides)),
            "",
        ]
        return "\n".join(lines)

    def generate_exports():
        global export_cache
        export_cache = {
            "story": build_story_export(),
            "screens": build_screens_export(),
            "overrides": build_overrides_export(),
        }
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
            renpy.notify("Live Studio files exported")
            return directory
        except Exception as exc:
            log_diagnostic("error", "Export failed: {}".format(exc), {"directory": directory})
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
            backup = path + ".live_studio_backup"
            if os.path.isfile(path):
                shutil.copy2(path, backup)
            temporary = path + ".tmp"
            with open(temporary, "w", encoding="utf-8") as output:
                output.write(updated)
            os.replace(temporary, path)
            renpy.notify("Editor-owned block replaced")
            return True
        except Exception as exc:
            log_diagnostic("error", "Block replacement failed: {}".format(exc), {"path": path})
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
            log_diagnostic("error", "Handwritten patch failed: {}".format(exc), {"path": path})
            renpy.notify("Patch failed")
            return False
