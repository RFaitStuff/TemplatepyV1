# =============================================================================
# Branches
# =============================================================================
# Lightweight branching-story support. A "branch point" is a labeled decision:
# the player picks one of several outcomes, the engine records it, and an
# in-game visualizer (Branches popup) shows the tree + lets the player rewind
# to ANY previously-encountered branch point and try a different path.
#
# How it works:
#   1) Author registers branch points in `_register_all_branches` (called once
#      at game start).
#   2) Story script reaches a branch:
#         $ branch_point("intro_path")         # auto-saves so we can rewind
#         menu:
#             "Walk alone.":
#                 $ take_branch("intro_path", "alone")
#                 jump intro_alone
#             "Look for Alice.":
#                 $ take_branch("intro_path", "alice")
#                 jump intro_alice
#   3) The visualizer (Branches button on the nav HUD) lists every registered
#      branch point. Visited ones show which choice you took; unvisited ones
#      are greyed. Clicking a visited branch loads the auto-save from that
#      point so you can replay from there.
#
# State stored:
#   current_branch_path (per-save)        - choices the player has taken
#   persistent.branches_visited (cross)   - every (branch, choice) ever taken
#   Auto-saves named "branch_<branch_id>" for rewind
# =============================================================================


# Registry (init-time, identical across saves).
init -3 python:
    branch_defs = {}     # branch_id -> {title, parent, choices: {cid: {title, label}}}


# Per-save player state.
default current_branch_path = {}              # branch_id -> chosen choice_id

# Cross-playthrough state.
default persistent.branches_visited = set()   # set of (branch_id, choice_id)
default persistent.branches_seen    = set()   # set of branch_id reached at all


# =============================================================================
# Registration & API
# =============================================================================
init -3 python:

    def register_branch(branch_id, title, choices, parent=None):
        # branch_id - short id (e.g. "intro_path")
        # title     - short label shown in the visualizer
        # choices   - {choice_id: {"title": ..., "label": ...}}
        # parent    - branch_id this one is downstream of, for the tree view
        branch_defs[branch_id] = {
            "title":   title,
            "parent":  parent,
            "choices": dict(choices),
        }


init python:

    def branch_point(branch_id):
        # Mark the branch as encountered and snapshot a save the player can
        # later rewind to from the visualizer. Call this just BEFORE the menu
        # that offers the choices.
        if branch_id not in branch_defs:
            return
        persistent.branches_seen.add(branch_id)
        try:
            branch_save_zone(branch_id, branch_defs[branch_id]["title"])
        except Exception:
            pass

    def take_branch(branch_id, choice_id):
        # Record which choice was taken at this branch point.
        current_branch_path[branch_id] = choice_id
        persistent.branches_visited.add((branch_id, choice_id))

    def has_taken_branch(branch_id, choice_id=None):
        # If choice_id is None, returns True iff the player has taken ANY
        # choice at this branch in the current save.
        cur = current_branch_path.get(branch_id)
        if choice_id is None:
            return cur is not None
        return cur == choice_id

    def branch_choice_taken(branch_id):
        # Returns the choice_id chosen at this branch in the current save, or None.
        return current_branch_path.get(branch_id)

    def rewind_to_branch(branch_id):
        # Load the auto-save snapshot taken at branch_point().
        try:
            renpy.load("branch_" + branch_id)
        except Exception:
            renpy.notify("No saved point for this branch.")

    def branch_tree():
        # Return [(branch_id, def, depth)] sorted by parent->child depth, for
        # the visualizer.
        depths = {}
        def depth_of(bid):
            if bid in depths:
                return depths[bid]
            d = branch_defs.get(bid, {})
            p = d.get("parent")
            depths[bid] = 0 if not p else depth_of(p) + 1
            return depths[bid]
        out = [(bid, branch_defs[bid], depth_of(bid)) for bid in branch_defs]
        out.sort(key=lambda t: (t[2], t[0]))
        return out


# =============================================================================
# Branch registry - every story branch lives here.
# Story scripts call branch_point() / take_branch() referencing these ids.
# =============================================================================
label _register_all_branches:
    python:
        register_branch(
            "archive_evidence_method",
            title="Archive Evidence Method",
            choices={
                "crosscheck": {"title": "Cross-check badge and drive", "label": "archive_terminal_decode"},
                "isolate": {"title": "Isolate the drive", "label": "archive_terminal_decode"},
                "direct": {"title": "Decode directly", "label": "archive_terminal_decode"},
            },
        )

        register_branch(
            "bree_cora_route",
            title="Bree and Cora Route",
            parent="archive_evidence_method",
            choices={
                "bree": {"title": "Back Bree's reconstruction", "label": "quest_bree_cora_choice"},
                "cora": {"title": "Back Cora's warning", "label": "quest_bree_cora_choice"},
                "neutral": {"title": "Refuse both readings", "label": "quest_bree_cora_choice"},
                "both": {"title": "Name both as witnesses", "label": "quest_bree_cora_choice"},
            },
        )
    return
