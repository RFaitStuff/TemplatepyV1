# JSON-safe model factories and generic tree helpers.

init -940 python in live_studio:
    import copy
    import json
    import re
    import time
    import uuid

    def new_id(prefix):
        return "{}_{}".format(prefix, uuid.uuid4().hex[:10])

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

    def json_safe(value, depth=0):
        """Converts runtime values into project-safe JSON values."""
        if depth > 64:
            return repr(value)
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, bytes):
            return "<bytes:{}>".format(len(value))
        if isinstance(value, (list, tuple, set)):
            return [json_safe(item, depth + 1) for item in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                try:
                    safe_key = str(key)
                except Exception:
                    safe_key = repr(key)
                result[safe_key] = json_safe(item, depth + 1)
            return result
        return repr(value)

    def new_project(name="Untitled Live Studio Project"):
        project_id = safe_identifier(name.lower(), "project")
        return {
            "version": VERSION,
            "project": {
                "id": project_id,
                "name": name,
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
            "name": name,
            "parent_id": parent_id,
            "root_state": clone(root_state) if root_state is not None else None,
            "changes": {
                "sets": {},
                "adds": [],
                "removes": [],
                "reorders": [],
            },
            "edges": [],
            "notes": "",
        }

    def new_scene(name, source_layers=None, scene_type="scene"):
        return {
            "id": new_id("scene"),
            "name": name,
            "type": scene_type,
            "source_layers": list(source_layers or []),
            "visible": True,
            "locked": False,
            "nodes": [],
        }

    def new_scene_node(name, node_type="image", **kwargs):
        node = {
            "id": new_id("node"),
            "name": str(name or node_type.title()),
            "type": node_type,
            "visible": True,
            "locked": False,
            "selectable": True,
            "children": [],
            "properties": {},
            "bounds": None,
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
            "nodes": [],
            "source": {},
        }

    def new_ui_node(name, node_type="displayable", widget_id=None):
        return {
            "id": new_id("ui"),
            "name": str(name or node_type),
            "type": node_type,
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

    def new_dialogue_controller(name="Dialogue"):
        return {
            "id": new_id("dialogue"),
            "name": name,
            "say_screen": "say",
            "choice_screen": "choice",
            "events": [],
            "active_event_id": None,
            "selected_event_id": None,
            "source": {},
        }

    def new_dialogue_event(event_type="say"):
        event = {
            "id": new_id("event"),
            "type": event_type,
            "speaker": "",
            "text": "",
            "condition": "",
            "script": "",
            "target": "",
            "choices": [],
            "notes": "",
        }
        if event_type == "choice":
            event["choices"] = [
                {
                    "id": new_id("choice"),
                    "caption": "Choice",
                    "condition": "",
                    "target": "",
                    "script": "",
                }
            ]
        return event

    def walk_nodes(nodes, parent_id=None, depth=0):
        for node in nodes or []:
            yield node, parent_id, depth
            for child, child_parent, child_depth in walk_nodes(node.get("children", []), node.get("id"), depth + 1):
                yield child, child_parent, child_depth

    def iter_state_items(state):
        for scene in state.get("scenes", []):
            yield scene, None, "scene"
            for node, parent_id, depth in walk_nodes(scene.get("nodes", []), scene.get("id"), 0):
                yield node, parent_id, "scene_node"
        for ui_screen in state.get("ui_screens", []):
            yield ui_screen, None, "ui_screen"
            for node, parent_id, depth in walk_nodes(ui_screen.get("nodes", []), ui_screen.get("id"), 0):
                yield node, parent_id, "ui_node"
        for controller in state.get("dialogue_controllers", []):
            yield controller, None, "dialogue_controller"
            for event in controller.get("events", []):
                yield event, controller.get("id"), "dialogue_event"
                for choice in event.get("choices", []):
                    yield choice, event.get("id"), "dialogue_choice"

    def find_state_item(state, item_id):
        if not item_id:
            return None, None, None
        for item, parent_id, kind in iter_state_items(state):
            if item.get("id") == item_id:
                return item, parent_id, kind
        return None, None, None

    def get_path_value(target, path, default=None):
        current = target
        for part in str(path or "").split("."):
            if not part:
                continue
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set_path_value(target, path, value):
        parts = [part for part in str(path or "").split(".") if part]
        if not parts:
            return
        current = target
        for part in parts[:-1]:
            child = current.get(part)
            if not isinstance(child, dict):
                child = {}
                current[part] = child
            current = child
        current[parts[-1]] = value

    def remove_item_from_state(state, item_id):
        def remove_from(nodes):
            for index, node in enumerate(list(nodes or [])):
                if node.get("id") == item_id:
                    del nodes[index]
                    return True
                if remove_from(node.get("children", [])):
                    return True
            return False

        for collection_name in ("scenes", "ui_screens", "dialogue_controllers"):
            collection = state.get(collection_name, [])
            for index, item in enumerate(list(collection)):
                if item.get("id") == item_id:
                    del collection[index]
                    return True
                if collection_name in ("scenes", "ui_screens") and remove_from(item.get("nodes", [])):
                    return True
                if collection_name == "dialogue_controllers":
                    events = item.get("events", [])
                    for event_index, event in enumerate(list(events)):
                        if event.get("id") == item_id:
                            del events[event_index]
                            return True
                        choices = event.get("choices", [])
                        for choice_index, choice in enumerate(list(choices)):
                            if choice.get("id") == item_id:
                                del choices[choice_index]
                                return True
        return False

    def append_to_parent(state, parent_id, collection, value):
        parent, _parent_id, kind = find_state_item(state, parent_id)
        if parent is None:
            return False
        if collection == "children":
            parent.setdefault("children", []).append(clone(value))
            return True
        if collection == "events" and kind == "dialogue_controller":
            parent.setdefault("events", []).append(clone(value))
            return True
        if collection == "choices" and kind == "dialogue_event":
            parent.setdefault("choices", []).append(clone(value))
            return True
        if collection == "nodes" and kind in ("scene", "ui_screen"):
            parent.setdefault("nodes", []).append(clone(value))
            return True
        return False
