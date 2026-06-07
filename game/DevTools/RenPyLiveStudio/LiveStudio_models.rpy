# JSON-safe project model and generic hierarchy helpers.

init -990 python in live_studio:
    import copy
    import json
    import re
    import time
    import uuid

    def new_id(prefix):
        return "{}_{}".format(prefix, uuid.uuid4().hex[:12])

    def safe_identifier(value, fallback="item"):
        text = str(value or "").strip()
        text = re.sub(r"[^0-9A-Za-z_]+", "_", text).strip("_")
        if not text:
            text = fallback
        if text[0].isdigit():
            text = "_" + text
        return text

    def clone(value):
        return copy.deepcopy(value)

    def json_safe(value, depth=0, seen=None):
        """Converts runtime values into data safe for JSON project files."""
        if seen is None:
            seen = set()
        if depth > 96:
            return "<maximum-depth>"
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, bytes):
            return "<bytes:{}>".format(len(value))
        identity = id(value)
        if identity in seen:
            return "<recursive-reference>"
        if isinstance(value, (list, tuple, set)):
            seen.add(identity)
            result = [json_safe(item, depth + 1, seen) for item in value]
            seen.discard(identity)
            return result
        if isinstance(value, dict):
            seen.add(identity)
            result = {}
            for key, item in value.items():
                try:
                    safe_key = str(key)
                except Exception:
                    safe_key = repr(key)
                result[safe_key] = json_safe(item, depth + 1, seen)
            seen.discard(identity)
            return result
        return repr(value)

    def new_project(name="Untitled Live Studio Project"):
        project_id = safe_identifier(name.lower(), "project")
        return {
            "version": VERSION,
            "project": {
                "id": project_id,
                "name": str(name),
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
                "entry_frame_id": None,
            },
            "frames": {},
            "frame_order": [],
            "assets": {},
            "settings": {
                "experimental_replace_blocks": False,
                "experimental_patch_files": False,
                "snap_enabled": SNAP_ENABLED,
                "grid_enabled": GRID_ENABLED,
                "grid_size": GRID_SIZE,
            },
        }

    def empty_frame_state():
        return {
            "source_ref": {},
            "scenes": [],
            "ui_screens": [],
            "dialogue_controllers": [],
        }

    def new_frame(name="Frame", parent_id=None, root_state=None):
        return {
            "id": new_id("frame"),
            "name": str(name or "Frame"),
            "parent_id": parent_id,
            "root_state": clone(root_state) if root_state is not None else None,
            "changes": {
                "sets": {},
                "adds": [],
                "removes": [],
                "reorders": [],
            },
            "edges": [],
            "stop_fallthrough": False,
            "notes": "",
            "source_ref": {},
        }

    def new_scene(name, source_layers=None, scene_type="scene"):
        return {
            "id": new_id("scene"),
            "name": str(name or "Scene"),
            "type": str(scene_type or "scene"),
            "source_layers": list(source_layers or []),
            "visible": True,
            "locked": False,
            "nodes": [],
            "source": {},
        }

    def new_scene_node(name, node_type="image", **kwargs):
        node = {
            "id": new_id("node"),
            "name": str(name or node_type.title()),
            "type": str(node_type or "image"),
            "visible": True,
            "locked": False,
            "selectable": True,
            "children": [],
            "properties": {},
            "bounds": None,
            "zorder": 0,
            "actions": [],
            "source": {},
        }
        node.update(kwargs)
        return node

    def new_ui_screen(name, layer="screens", tag=None, zorder=0):
        return {
            "id": new_id("screen"),
            "name": str(name or "screen"),
            "tag": str(tag or name or "screen"),
            "layer": str(layer or "screens"),
            "zorder": int(zorder or 0),
            "visible": True,
            "locked": False,
            "editability": "inspect",
            "managed": False,
            "role": "screen",
            "nodes": [],
            "source": {},
        }

    def new_ui_node(name, node_type="fixed", widget_id=None):
        return {
            "id": new_id("ui"),
            "name": str(name or node_type),
            "type": str(node_type or "fixed"),
            "widget_id": widget_id,
            "visible": True,
            "locked": False,
            "selectable": True,
            "editability": "editable" if widget_id else "inspect",
            "properties": {},
            "resolved_properties": {},
            "bounds": None,
            "actions": [],
            "children": [],
            "source": {},
        }

    def new_action(action_type="none"):
        return {
            "id": new_id("action"),
            "type": str(action_type or "none"),
            "target_frame_id": "",
            "target": "",
            "variable": "",
            "operator": "=",
            "value": "",
            "script": "",
            "screen": "",
            "condition": "",
            "actions": [],
            "source": {},
        }

    def new_dialogue_controller(name="Dialogue", scene_id=None):
        return {
            "id": new_id("dialogue"),
            "name": str(name or "Dialogue"),
            "scene_id": scene_id,
            "say_screen": "say",
            "choice_screen": "choice",
            "events": [],
            # Ordered commands that execute in the current frame. A frame may
            # contain many non-interaction commands and one main interaction.
            "frame_event_ids": [],
            "active_event_id": None,
            "selected_event_id": None,
            "source": {},
        }

    def new_dialogue_event(event_type="say"):
        event_type = str(event_type or "say")
        event = {
            "id": new_id("event"),
            "type": event_type,
            "speaker": "",
            "text": "",
            "condition": "",
            "script": "",
            "target": "",
            "target_frame_id": "",
            "image": "",
            "screen": "",
            "transition": "",
            "duration": 0.0,
            "audio": "",
            "channel": "music",
            "fadein": 0.0,
            "fadeout": 0.0,
            "choices": [],
            "notes": "",
        }
        if event_type == "choice":
            event["choices"].append(new_choice_option())
        return event

    def new_choice_option(caption="Choice"):
        return {
            "id": new_id("choice"),
            "caption": str(caption or "Choice"),
            "condition": "",
            "target": "",
            "target_frame_id": "",
            "script": "",
        }

    def walk_nodes(nodes, parent_id=None, depth=0):
        for node in nodes or []:
            yield node, parent_id, depth
            for child, child_parent, child_depth in walk_nodes(node.get("children", []), node.get("id"), depth + 1):
                yield child, child_parent, child_depth

    def iter_state_items(state):
        for scene in state.get("scenes", []):
            yield scene, None, "scene"
            for node, parent_id, _depth in walk_nodes(scene.get("nodes", []), scene.get("id"), 0):
                yield node, parent_id, "scene_node"
        for screen in state.get("ui_screens", []):
            yield screen, None, "ui_screen"
            for node, parent_id, _depth in walk_nodes(screen.get("nodes", []), screen.get("id"), 0):
                yield node, parent_id, "ui_node"
        for controller in state.get("dialogue_controllers", []):
            yield controller, controller.get("scene_id"), "dialogue_controller"
            for event in controller.get("events", []):
                yield event, controller.get("id"), "dialogue_event"
                for choice in event.get("choices", []):
                    yield choice, event.get("id"), "dialogue_choice"
                for action in event.get("actions", []):
                    yield action, event.get("id"), "action"

    def find_state_item(state, item_id):
        if not item_id:
            return None, None, None
        for item, parent_id, kind in iter_state_items(state):
            if item.get("id") == item_id:
                return item, parent_id, kind
        return None, None, None

    def get_path_value(target, path, default=None):
        value = target
        for part in str(path or "").split("."):
            if not part:
                continue
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def set_path_value(target, path, value):
        parts = [part for part in str(path or "").split(".") if part]
        if not parts:
            return False
        current = target
        for part in parts[:-1]:
            if not isinstance(current.get(part), dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = clone(value)
        return True

    def _remove_from_nodes(nodes, item_id):
        for index in range(len(nodes) - 1, -1, -1):
            node = nodes[index]
            if node.get("id") == item_id:
                del nodes[index]
                return True
            if _remove_from_nodes(node.get("children", []), item_id):
                return True
        return False

    def remove_item_from_state(state, item_id):
        for collection_name in ("scenes", "ui_screens", "dialogue_controllers"):
            collection = state.get(collection_name, [])
            for index in range(len(collection) - 1, -1, -1):
                item = collection[index]
                if item.get("id") == item_id:
                    del collection[index]
                    return True
                if collection_name in ("scenes", "ui_screens"):
                    if _remove_from_nodes(item.get("nodes", []), item_id):
                        return True
                elif collection_name == "dialogue_controllers":
                    events = item.get("events", [])
                    for event_index in range(len(events) - 1, -1, -1):
                        event = events[event_index]
                        if event.get("id") == item_id:
                            del events[event_index]
                            return True
                        choices = event.get("choices", [])
                        for choice_index in range(len(choices) - 1, -1, -1):
                            if choices[choice_index].get("id") == item_id:
                                del choices[choice_index]
                                return True
        return False

    def _find_node_collection(nodes, parent_id):
        for node in nodes or []:
            if node.get("id") == parent_id:
                return node.setdefault("children", [])
            found = _find_node_collection(node.get("children", []), parent_id)
            if found is not None:
                return found
        return None

    def append_to_parent(state, parent_id, collection, value, root_collection=None):
        if root_collection:
            state.setdefault(root_collection, []).append(clone(value))
            return True
        parent, _grandparent, kind = find_state_item(state, parent_id)
        if parent is None:
            return False
        if collection == "children":
            parent.setdefault("children", []).append(clone(value))
            return True
        if collection == "nodes" and kind in ("scene", "ui_screen"):
            parent.setdefault("nodes", []).append(clone(value))
            return True
        if collection == "events" and kind == "dialogue_controller":
            parent.setdefault("events", []).append(clone(value))
            return True
        if collection == "choices" and kind == "dialogue_event":
            parent.setdefault("choices", []).append(clone(value))
            return True
        if collection == "actions":
            parent.setdefault("actions", []).append(clone(value))
            return True
        return False

    def reorder_item_in_parent(state, item_id, direction):
        def move_in(collection):
            for index, item in enumerate(collection):
                if item.get("id") == item_id:
                    if direction == "front":
                        target = len(collection) - 1
                    elif direction == "back":
                        target = 0
                    elif direction == "forward":
                        target = min(len(collection) - 1, index + 1)
                    else:
                        target = max(0, index - 1)
                    if target != index:
                        value = collection.pop(index)
                        collection.insert(target, value)
                    return True
                if move_in(item.get("children", [])):
                    return True
            return False
        for scene in state.get("scenes", []):
            if move_in(scene.get("nodes", [])):
                return True
        for screen in state.get("ui_screens", []):
            if move_in(screen.get("nodes", [])):
                return True
        for controller in state.get("dialogue_controllers", []):
            if move_in(controller.get("events", [])):
                return True
        return False
