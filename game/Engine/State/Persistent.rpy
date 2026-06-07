# =============================================================================
# Persistent State (carries across playthroughs)
# -----------------------------------------------------------------------------
# ONLY put things here that should survive starting a new game:
#   - Gallery / CG unlocks
#   - Endings seen
#   - Achievements
#   - Newgame+ style perks
# Everything else (story progress, current room, inventory, etc.) belongs in
# the regular `default ...` files so it resets per playthrough.
# =============================================================================

default persistent.galleryunlocks = set()
default persistent.endingsseen    = set()
default persistent.achievements   = set()


init python:

    # --- gallery ------------------------------------------------------------
    def unlock_gallery(name):
        # No-op during gallery replay so re-watching never re-grants unlocks
        # or re-fires anything else gated on _in_replay.
        if getattr(store, "_in_replay", None):
            return
        persistent.galleryunlocks.add(name)

    def is_gallery_unlocked(name):
        return name in persistent.galleryunlocks

    # --- endings ------------------------------------------------------------
    def mark_ending(ending_id):
        persistent.endingsseen.add(ending_id)

    def has_seen_ending(ending_id):
        return ending_id in persistent.endingsseen

    # --- achievements -------------------------------------------------------
    def grant_achievement(name):
        if name not in persistent.achievements:
            persistent.achievements.add(name)
            renpy.notify("Achievement unlocked: %s" % name)

    def has_achievement(name):
        return name in persistent.achievements
