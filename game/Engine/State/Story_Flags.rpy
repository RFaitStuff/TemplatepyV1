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
        current_route = route
        set_flag("route_" + str(route))

    def on_route(route):
        return current_route == route
