# =============================================================================
# Story Flags
# -----------------------------------------------------------------------------
# Per-playthrough story flags + active narrative route. Resets on a new game.
# Use `persistent_*` (see Persistent.rpy) for things that should carry across
# playthroughs.
#
# The actual inventory lives in Engine/State/Inventory.rpy (id -> count). This
# file used to define a parallel `add_item / has_item / remove_item` over a
# simple list which conflicted with the Inventory module - removed.
# =============================================================================

# -----------------------------------------------------------------------------
# Arbitrary story progress flags. Use string ids like "met_alice", "act1_done".
# -----------------------------------------------------------------------------
default story_flags = set()

# -----------------------------------------------------------------------------
# Active narrative route (None if undecided).
# -----------------------------------------------------------------------------
default current_route = None


init -3 python:
    route_defs = {}

    def register_route(route_id, title=None, **extra):
        route_id = str(route_id)
        data = route_defs.setdefault(route_id, {})
        data.update({
            "id": route_id,
            "title": title or route_id.replace("_", " ").title(),
        })
        data.update(extra)
        return data


init python:

    # --- flags --------------------------------------------------------------
    def set_flag(flag):
        already = flag in story_flags
        story_flags.add(flag)
        # Notify quest manager (if loaded) so flag-driven quests update.
        try:
            _quests_on_flag(flag)
        except NameError:
            pass
        if not already:
            try:
                emit("flag_set", flag)
            except NameError:
                pass

    def clear_flag(flag):
        story_flags.discard(flag)

    def has_flag(flag):
        return flag in story_flags

    # --- routes -------------------------------------------------------------
    def set_route(route):
        global current_route
        current_route = str(route) if route is not None else None
        set_flag("route_" + str(route))

    def on_route(route):
        return current_route == str(route)

    def story_flag_validation_issues():
        issues = []
        for route_id, data in (globals().get("route_defs", {}) or {}).items():
            if not isinstance(data, dict):
                issues.append("Route '{}' should be a dictionary definition.".format(route_id))
                continue
            if data.get("id") and data.get("id") != route_id:
                issues.append("Route '{}' has mismatched id '{}'.".format(route_id, data.get("id")))
            reqs = data.get("requires")
            if reqs:
                try:
                    first_missing_requirement(reqs)
                except Exception:
                    issues.append("Route '{}' has invalid requirements '{}'.".format(route_id, reqs))
        return issues


init 999 python:
    try:
        register_project_tac_validator(story_flag_validation_issues)
    except Exception:
        pass
