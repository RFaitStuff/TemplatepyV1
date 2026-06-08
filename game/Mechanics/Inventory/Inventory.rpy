# =============================================================================
# Inventory
# =============================================================================
# Pure-data system. Items are defined in `item_defs` (id -> metadata).
# Player carries `{item_id: count}` in `player_inventory`.
#
# API:
#   define_item("lost_pen", name="A Lost Pen", desc="...", icon=None, quest="found_pen")
#   add_item("lost_pen")           # +1
#   add_item("coin", 5)            # +5
#   remove_item("lost_pen")        # -1
#   has_item("lost_pen")
#   item_count("lost_pen")
#   inventory_list()               # [(id, count), ...] for the UI
#
# Item ids are also valid for the `items` field on a registered location -
# show up as clickable spots in the room while a quest flag is active.
# =============================================================================

# item_defs is registry data (identical every playthrough) -> init-time, not a default.
# player_inventory is per-save state -> default.
init -3 python:
    item_defs = {}

default player_inventory = {}


init -2 python:

    def define_item(item_id, **kwargs):
        d = item_defs.setdefault(item_id, {})
        d.update(kwargs)
        d.setdefault("name", item_id.replace("_", " ").title())
        d.setdefault("desc", "")
        d.setdefault("icon", None)
        d.setdefault("quest", None)


init python:

    def add_item(item_id, n=1):
        if not system_enabled("inventory"):
            return None
        if n <= 0:
            return
        player_inventory[item_id] = player_inventory.get(item_id, 0) + n
        try:
            emit("item_added", item_id, n)
        except NameError:
            pass

    def remove_item(item_id, n=1):
        if not system_enabled("inventory"):
            return None
        cur = player_inventory.get(item_id, 0)
        delta = min(cur, n)
        new = max(0, cur - n)
        if new == 0:
            player_inventory.pop(item_id, None)
        else:
            player_inventory[item_id] = new
        if delta > 0:
            try:
                emit("item_removed", item_id, delta)
            except NameError:
                pass

    def has_item(item_id, n=1):
        if not system_enabled("inventory"):
            return False
        return player_inventory.get(item_id, 0) >= n

    def item_count(item_id):
        if not system_enabled("inventory"):
            return 0
        return player_inventory.get(item_id, 0)

    def item_name(item_id):
        return item_defs.get(item_id, {}).get("name", item_id)

    def item_desc(item_id):
        return item_defs.get(item_id, {}).get("desc", "")

    def inventory_list():
        if not system_enabled("inventory"):
            return []
        return sorted(player_inventory.items())
