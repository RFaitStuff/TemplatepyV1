# =============================================================================
# Rollback And Branch Save Helpers
# =============================================================================
# Writer-facing helpers:
#   $ stop_rollback_here()
#   $ branch_save_zone("archive_choice", "Archive Choice")
# =============================================================================

default persistent.branch_save_zones = set()
default branch_save_zone_titles = {}


init python:

    def stop_rollback_here(message=None):
        try:
            renpy.block_rollback()
        except Exception:
            pass
        if message:
            try:
                renpy.notify(message)
            except Exception:
                pass
        return None

    def branch_save_zone(zone_id, title=None):
        zone_id = str(zone_id)
        title = title or zone_id.replace("_", " ").title()
        branch_save_zone_titles[zone_id] = title
        try:
            persistent.branch_save_zones.add(zone_id)
        except Exception:
            pass
        try:
            renpy.save("branch_" + zone_id, "[Branch] " + title)
        except Exception:
            pass
        return None

    def branch_save_zones():
        zones = []
        for zone_id in sorted(getattr(persistent, "branch_save_zones", set()) or set()):
            zones.append({
                "id": zone_id,
                "slot": "branch_" + zone_id,
                "title": branch_save_zone_titles.get(zone_id, zone_id.replace("_", " ").title()),
            })
        return zones


label rollback_stop(message=None):
    $ stop_rollback_here(message)
    return
