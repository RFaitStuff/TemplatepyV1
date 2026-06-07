# Frame flow, branches, and navigation targets.

init -880 python in live_studio:
    def frame_edges(frame_id=None):
        frame = frame_by_id(frame_id or current_frame_id)
        return frame.get("edges", []) if frame else []

    def add_frame_edge(source_id, target_id, edge_type="advance", label=""):
        global project_dirty
        source = frame_by_id(source_id)
        if source is None or frame_by_id(target_id) is None:
            return
        edge = {
            "id": new_id("edge"),
            "type": edge_type,
            "label": str(label or ""),
            "target_frame_id": target_id,
            "condition": "",
        }
        source.setdefault("edges", []).append(edge)
        project_dirty = True
        renpy.restart_interaction()

    def add_branch_frame(label="Branch"):
        source_id = current_frame_id
        frame = add_frame("inherit", label)
        if source_id and frame:
            add_frame_edge(source_id, frame.get("id"), "branch", label)
        return frame

    def expected_next_frame_id(frame_id=None):
        frame_id = frame_id or current_frame_id
        edges = frame_edges(frame_id)
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

    def set_button_frame_target(node_id, frame_id):
        item, _parent_id, kind = find_state_item(resolve_frame(), node_id)
        if item is None or kind != "ui_node":
            return
        actions = clone(item.get("actions", []))
        action = None
        for candidate in actions:
            if candidate.get("slot") == "action":
                action = candidate
                break
        if action is None:
            action = {"slot": "action", "type": "jump_frame", "editable": True, "data": {}, "repr": ""}
            actions.append(action)
        action["type"] = "jump_frame"
        action["editable"] = True
        action.setdefault("data", {})["target_frame_id"] = frame_id
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
