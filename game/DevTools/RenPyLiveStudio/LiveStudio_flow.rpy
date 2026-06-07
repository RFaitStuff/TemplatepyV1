# Frame flow, branches, runtime history, and structured destinations.

init -880 python in live_studio:
    def frame_edges(frame_id=None):
        frame = frame_by_id(frame_id or current_frame_id)
        return frame.get("edges", []) if frame else []

    def _add_frame_edge_no_restart(source_id, target_id, edge_type="advance", label="", condition=""):
        source = frame_by_id(source_id)
        if source is None or frame_by_id(target_id) is None:
            return None
        for edge in source.setdefault("edges", []):
            if edge.get("target_frame_id") == target_id and edge.get("type") == edge_type:
                edge["label"] = str(label or edge.get("label", ""))
                edge["condition"] = str(condition or edge.get("condition", ""))
                return edge
        edge = {
            "id": new_id("edge"),
            "type": str(edge_type or "advance"),
            "label": str(label or ""),
            "target_frame_id": target_id,
            "condition": str(condition or ""),
        }
        source["edges"].append(edge)
        return edge

    def add_frame_edge(source_id, target_id, edge_type="advance", label="", condition=""):
        global project_dirty
        edge = _add_frame_edge_no_restart(source_id, target_id, edge_type, label, condition)
        if edge:
            project_dirty = True
            restart()
        return edge

    def remove_frame_edge(edge_id, source_id=None):
        global project_dirty
        source = frame_by_id(source_id or current_frame_id)
        if source is None:
            return False
        edges = source.setdefault("edges", [])
        before = len(edges)
        edges[:] = [edge for edge in edges if edge.get("id") != edge_id]
        changed = before != len(edges)
        if changed:
            project_dirty = True
            restart()
        return changed

    def add_branch_frame(label="Branch"):
        source_id = current_frame_id
        frame = add_frame("inherit", label, True)
        if source_id and frame:
            add_frame_edge(source_id, frame.get("id"), "branch", label)
        return frame

    def explicit_next_frame_ids(frame_id=None):
        return [edge.get("target_frame_id") for edge in frame_edges(frame_id) if edge.get("target_frame_id")]

    def expected_next_frame_id(frame_id=None):
        frame_id = frame_id or current_frame_id
        edges = frame_edges(frame_id)
        advance = [e for e in edges if e.get("type") in ("advance", "runtime") and e.get("target_frame_id")]
        if len(advance) == 1:
            return advance[0].get("target_frame_id")
        if len(edges) == 1:
            return edges[0].get("target_frame_id")
        if edges:
            return None
        order = frame_order()
        try:
            index = order.index(frame_id)
        except ValueError:
            return None
        if index + 1 < len(order):
            return order[index + 1]
        return None

    def go_expected_next():
        target = expected_next_frame_id()
        if target:
            select_frame(target)

    def go_runtime_previous():
        trace = runtime.get("runtime_trace", [])
        if len(trace) < 2:
            return
        current_key = source_reference_key((current_frame() or {}).get("source_ref", {}))
        position = None
        for index in range(len(trace) - 1, -1, -1):
            if trace[index].get("key") == current_key or trace[index].get("frame_id") == current_frame_id:
                position = index
                break
        if position is None:
            position = len(trace) - 1
        if position > 0:
            target = trace[position - 1].get("frame_id")
            if frame_by_id(target):
                select_frame(target)

    def set_button_frame_target(node_id, frame_id):
        item, _parent_id, kind = find_state_item(resolve_frame(), node_id)
        if item is None or kind not in ("ui_node", "scene_node"):
            return
        action = primary_action(item) if kind == "ui_node" else None
        if action is None:
            actions = clone(item.get("actions", []))
            action = new_action("jump_frame")
            actions.append(action)
        else:
            actions = clone(item.get("actions", []))
            for candidate in actions:
                if candidate.get("id") == action.get("id"):
                    action = candidate
                    break
        action["type"] = "jump_frame"
        action["target_frame_id"] = frame_id or ""
        set_item_value(node_id, "actions", actions, "Set button destination")
        if frame_id:
            add_frame_edge(current_frame_id, frame_id, "button", item.get("name", "Button"))

    def flow_summary(frame_id=None):
        frame_id = frame_id or current_frame_id
        frame = frame_by_id(frame_id)
        if frame is None:
            return "No frame"
        edges = frame.get("edges", [])
        if not edges:
            target = expected_next_frame_id(frame_id)
            return "Next: {}".format((frame_by_id(target) or {}).get("name", "End") if target else "End")
        return "{} outgoing path{}".format(len(edges), "" if len(edges) == 1 else "s")

    def frame_path_options():
        return [(frame_id, (frame_by_id(frame_id) or {}).get("name", "Frame")) for frame_id in frame_order()]

# Conservative runtime-only source preview. This uses Ren'Py's AST for short-
# lived inspection only; no AST node is placed in project/save data.
init -879 python in live_studio:
    import ast

    SOURCE_INTERACTION_TYPES = ("Say", "Menu", "Pause")

    def _source_current_node():
        try:
            name = runtime.get("source_origin_name") or renpy.game.context().current
            if name is None:
                return None
            return renpy.game.script.lookup(name)
        except Exception as exc:
            log_diagnostic("warning", "Could not inspect current script statement", repr(exc))
            return None

    def _source_imspec(node):
        value = getattr(node, "imspec", None)
        if not value:
            return None
        try:
            image = value[0]
            image_name = " ".join(image) if isinstance(image, (tuple, list)) else str(image)
        except Exception:
            return None
        layer = getattr(node, "layer", None)
        tag = None
        try:
            if len(value) >= 6:
                tag = value[2]
                layer = value[4]
            elif len(value) == 3:
                layer = value[2]
        except Exception:
            pass
        if not tag and image_name:
            tag = image_name.split()[0]
        return {
            "image": image_name,
            "tag": str(tag or ""),
            "layer": str(layer or "master"),
        }

    def _source_node_data(node):
        node_type = type(node).__name__
        data = {
            "type": node_type,
            "filename": str(getattr(node, "filename", "") or ""),
            "line": int(getattr(node, "linenumber", 0) or 0),
            "name": json_safe(getattr(node, "name", None)),
        }
        if node_type == "Say":
            raw_speaker = str(getattr(node, "who", "") or "")
            speaker = raw_speaker
            if raw_speaker:
                try:
                    literal_speaker = ast.literal_eval(raw_speaker)
                    if isinstance(literal_speaker, str):
                        speaker = literal_speaker
                except Exception:
                    pass
            data["speaker"] = speaker
            data["speaker_expression"] = raw_speaker
            data["text"] = str(getattr(node, "what", "") or "")
        elif node_type == "Menu":
            choices = []
            prompt = ""
            for caption, condition, block in getattr(node, "items", []) or []:
                if block is None:
                    if caption and not prompt:
                        prompt = str(caption)
                    continue
                choices.append({
                    "caption": str(caption or "Choice"),
                    "condition": str(condition or ""),
                    "target_source": {
                        "filename": str(getattr(block[0], "filename", "") or "") if block else "",
                        "line": int(getattr(block[0], "linenumber", 0) or 0) if block else 0,
                    },
                })
            data["choices"] = choices
            data["text"] = prompt
        elif node_type in ("Show", "Scene", "Hide"):
            data["imspec"] = _source_imspec(node)
        elif node_type == "Jump":
            data["target"] = str(getattr(node, "target", "") or "")
            data["dynamic"] = bool(getattr(node, "expression", False))
        elif node_type == "Call":
            data["target"] = str(getattr(node, "label", "") or "")
            data["dynamic"] = bool(getattr(node, "expression", False))
        elif node_type == "Python":
            code = getattr(getattr(node, "code", None), "source", "")
            data["script"] = str(code or "")
        elif node_type == "UserStatement":
            data["statement"] = str(getattr(node, "line", "") or "")
        return data

    def _source_successors(node):
        """Returns (node, branch label, condition) without evaluating Python."""
        if node is None:
            return []
        node_type = type(node).__name__
        result = []
        try:
            if node_type == "Menu":
                for caption, condition, block in getattr(node, "items", []) or []:
                    if block:
                        result.append((block[0], str(caption or "Choice"), str(condition or "")))
                return result
            if node_type == "If":
                for condition, block in getattr(node, "entries", []) or []:
                    if block:
                        label = "Else" if str(condition) == "True" else "If {}".format(condition)
                        result.append((block[0], label, str(condition or "")))
                next_node = getattr(node, "next", None)
                if next_node is not None:
                    result.append((next_node, "Fallthrough", ""))
                return result
            if node_type == "While":
                block = getattr(node, "block", None) or []
                if block:
                    result.append((block[0], "Loop", str(getattr(node, "condition", "") or "")))
                if getattr(node, "next", None) is not None:
                    result.append((node.next, "After loop", ""))
                return result
            if node_type == "Jump" and not bool(getattr(node, "expression", False)):
                target = renpy.game.script.lookup_or_none(getattr(node, "target", None))
                return [(target, "Jump", "")] if target is not None else []
            if node_type == "Call" and not bool(getattr(node, "expression", False)):
                target = renpy.game.script.lookup_or_none(getattr(node, "label", None))
                return [(target, "Call", "")] if target is not None else []
        except Exception:
            pass
        next_node = getattr(node, "next", None)
        return [(next_node, "", "")] if next_node is not None else []

    def _source_candidate_title(data, branch=""):
        node_type = data.get("type", "Statement")
        if node_type == "Say":
            speaker = data.get("speaker") or "Narration"
            text = str(data.get("text") or "").replace("\n", " ")
            title = "{}: {}".format(speaker, text[:52] + ("…" if len(text) > 52 else ""))
        elif node_type == "Menu":
            title = "Choice menu ({} options)".format(len(data.get("choices", [])))
        elif node_type == "Pause":
            title = "Pause / interaction"
        elif node_type == "UserStatement":
            title = data.get("statement") or "Custom statement"
        elif node_type in ("Return",):
            title = "Return / end of call"
        else:
            title = node_type
        return "{} → {}".format(branch, title) if branch else title

    def refresh_source_flow_candidates(limit=24, restart_ui=True):
        candidates = []
        current = _source_current_node()
        if current is None:
            runtime["source_candidates"] = []
            return []

        starts = _source_successors(current)
        # When the current interaction is a menu, its successors are the real
        # next branches. For normal interactions, next is usually linear.
        queue = []
        for node, branch, condition in starts:
            if node is not None:
                queue.append((node, branch, condition, []))
        visited = set()

        while queue and len(candidates) < limit:
            node, branch, condition, steps = queue.pop(0)
            identity = id(node)
            visit_key = (identity, branch)
            if visit_key in visited:
                continue
            visited.add(visit_key)
            data = _source_node_data(node)
            node_type = data.get("type")

            interaction = node_type in SOURCE_INTERACTION_TYPES
            if node_type == "UserStatement":
                statement = str(data.get("statement", "")).strip().lower()
                interaction = statement.startswith("call screen") or statement.startswith("pause")
            if node_type in ("Return",):
                interaction = True

            if interaction:
                candidates.append({
                    "title": _source_candidate_title(data, branch),
                    "branch": branch,
                    "condition": condition,
                    "statement": data,
                    "steps": clone(steps),
                    "source_ref": {
                        "filename": data.get("filename", ""),
                        "line": data.get("line", 0),
                        "statement": node_type.lower(),
                        "label": "",
                    },
                })
                continue

            new_steps = steps + [data]
            successors = _source_successors(node)
            if not successors:
                candidates.append({
                    "title": _source_candidate_title(data, branch),
                    "branch": branch,
                    "condition": condition,
                    "statement": data,
                    "steps": clone(steps),
                    "source_ref": {
                        "filename": data.get("filename", ""),
                        "line": data.get("line", 0),
                        "statement": node_type.lower(),
                        "label": "",
                    },
                })
                continue
            for successor, child_branch, child_condition in successors:
                if successor is None:
                    continue
                combined_branch = branch
                if child_branch:
                    combined_branch = "{} / {}".format(branch, child_branch).strip(" /")
                queue.append((successor, combined_branch, child_condition or condition, new_steps))

        runtime["source_candidates"] = candidates
        if restart_ui:
            restart()
        return candidates

    def source_flow_candidates():
        if "source_candidates" not in runtime:
            return refresh_source_flow_candidates(restart_ui=False)
        return runtime.get("source_candidates", [])

    def _remove_images_for_source(layer, tag=None):
        state = resolve_frame()
        for scene in state.get("scenes", []):
            for node, _parent, _depth in list(walk_nodes(scene.get("nodes", []))):
                if node.get("type") not in ("image", "displayable"):
                    continue
                if str(node.get("layer") or "master") != str(layer or "master"):
                    continue
                if tag and str(node.get("tag") or "") != str(tag):
                    continue
                remove_item(node.get("id"), "Apply source visual change")

    def _apply_source_visual_step(step):
        step_type = step.get("type")
        imspec = step.get("imspec") or {}
        if step_type == "Scene":
            _remove_images_for_source(imspec.get("layer") or "master")
        elif step_type in ("Show", "Hide"):
            _remove_images_for_source(imspec.get("layer") or "master", imspec.get("tag"))
        if step_type in ("Scene", "Show") and imspec.get("image"):
            scene = ensure_scene("Master")
            node = add_image_to_scene(imspec.get("image"), scene.get("id"))
            set_item_value(node.get("id"), "layer", imspec.get("layer") or "master", "Set imported image layer")
            set_item_value(node.get("id"), "tag", imspec.get("tag") or imspec.get("image", "").split()[0], "Set imported image tag")


    def _create_imported_choice_branches(menu_frame, event_id, source_choices):
        """Creates inherited branch placeholders for a statically-known menu."""
        if menu_frame is None or not event_id:
            return []
        branches = []
        choices = []
        insert_index = frame_index(menu_frame.get("id")) + 1
        for offset, source_choice in enumerate(source_choices or []):
            caption = str(source_choice.get("caption") or "Choice")
            branch = new_frame(caption, parent_id=menu_frame.get("id"))
            branch["stop_fallthrough"] = True
            target_source = clone(source_choice.get("target_source") or {})
            branch["source_ref"] = {
                "filename": target_source.get("filename", ""),
                "line": target_source.get("line", 0),
                "statement": "branch",
                "label": "",
            }
            _restore_frame_internal(branch, insert_index + offset)
            _history_push({
                "type": "add_frame",
                "label": "Add imported choice branch",
                "frame": clone(branch),
                "index": insert_index + offset,
                "previous_frame_id": menu_frame.get("id"),
                "previous_stop_before": bool(menu_frame.get("stop_fallthrough", False)),
                "previous_stop_after": bool(menu_frame.get("stop_fallthrough", False)),
            })
            _add_frame_edge_no_restart(
                menu_frame.get("id"), branch.get("id"), "choice", caption,
                str(source_choice.get("condition") or ""),
            )
            choice = new_choice_option(caption)
            choice["condition"] = str(source_choice.get("condition") or "")
            choice["target_frame_id"] = branch.get("id")
            choices.append(choice)
            branches.append(branch)
        if choices:
            set_item_value(event_id, "choices", choices, "Create choice branch frames")
        return branches

    def import_source_candidate(index):
        global project_dirty
        candidates = source_flow_candidates()
        try:
            candidate = candidates[int(index)]
        except Exception:
            return None
        source_frame_id = current_frame_id
        frame = add_frame("inherit", candidate.get("title") or "Imported Source Frame")
        if frame is None:
            return None
        frame["source_ref"] = clone(candidate.get("source_ref", {}))
        frame["source_preview"] = json_safe(candidate)
        for step in candidate.get("steps", []):
            _apply_source_visual_step(step)
            if step.get("type") == "Python" and str(step.get("script", "")).strip():
                command_event = add_dialogue_event("script")
                if command_event:
                    set_item_value(command_event.get("id"), "script", step.get("script", ""), "Import Python command")
            elif step.get("type") == "UserStatement" and str(step.get("statement", "")).strip():
                command_event = add_dialogue_event("renpy")
                if command_event:
                    set_item_value(command_event.get("id"), "script", step.get("statement", ""), "Import Ren'Py statement")

        statement = candidate.get("statement", {})
        statement_type = statement.get("type")
        if statement_type == "Say":
            event_type = "say" if statement.get("speaker") else "narration"
            event = add_dialogue_event(event_type)
            if event:
                set_item_value(event.get("id"), "speaker", statement.get("speaker", ""), "Import speaker")
                set_item_value(event.get("id"), "text", statement.get("text", ""), "Import dialogue")
        elif statement_type == "Menu":
            event = add_dialogue_event("choice")
            if event:
                if statement.get("text"):
                    set_item_value(event.get("id"), "text", statement.get("text", ""), "Import menu prompt")
                source_choices = statement.get("choices", [])
                branches = _create_imported_choice_branches(frame, event.get("id"), source_choices)
                if not branches:
                    choices = []
                    for item in source_choices:
                        choice = new_choice_option(item.get("caption", "Choice"))
                        choice["condition"] = item.get("condition", "")
                        choices.append(choice)
                    set_item_value(event.get("id"), "choices", choices or [new_choice_option()], "Import choices")
        elif statement_type == "Pause":
            add_dialogue_event("pause")
        elif statement_type == "UserStatement":
            event = add_dialogue_event("renpy")
            if event:
                set_item_value(event.get("id"), "script", statement.get("statement", ""), "Import custom statement")

        if source_frame_id:
            add_frame_edge(source_frame_id, frame.get("id"), "branch" if candidate.get("branch") else "advance", candidate.get("branch", ""), candidate.get("condition", ""))
        project_dirty = True
        select_frame(frame.get("id"))
        return frame
