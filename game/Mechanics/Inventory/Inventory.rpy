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
#   use_item("lost_pen")           # author hook or default feedback
#   item_use("key", "locked_door", label="unlock_door")
#   recipe("stick", "cloth", result="torch")
#
# Item ids are also valid for the `items` field on a registered location -
# show up as clickable spots in the room while a quest flag is active.
# =============================================================================

# item_defs is registry data (identical every playthrough) -> init-time, not a default.
# player_inventory is per-save state -> default.
init -3 python:
    item_defs = {}
    item_use_defs = {}
    item_recipe_defs = {}
    item_combine_fail_defs = {}

    def _item_pair_key(item_a, item_b):
        return tuple(sorted((str(item_a), str(item_b))))

default player_inventory = {}
default failed_item_recipes = set()


init -2 python:

    def define_item(item_id, **kwargs):
        d = item_defs.setdefault(item_id, {})
        d.update(kwargs)
        d.setdefault("name", item_id.replace("_", " ").title())
        d.setdefault("desc", "")
        d.setdefault("icon", None)
        d.setdefault("quest", None)
        d.setdefault("tags", [])
        d.setdefault("quest_item", False)
        d.setdefault("stackable", True)
        d.setdefault("hidden_until", None)
        d.setdefault("show_when", None)
        d.setdefault("use_label", None)
        d.setdefault("examine_label", None)
        d.setdefault("use_message", "Nope.")
        d.setdefault("locked_message", "You can't use that right now.")
        d.setdefault("use_targets", {})
        return d

    def item_use(item_id, target, label=None, requires=None, consume=False, fail=None, success=None, **kwargs):
        target = str(target)
        data = {
            "item": item_id,
            "target": target,
            "label": label,
            "requires": requires,
            "consume": consume,
            "fail": fail,
            "success": success,
        }
        data.update(kwargs)
        item_use_defs[(item_id, target)] = data
        if item_id != "*":
            d = define_item(item_id)
            d.setdefault("use_targets", {})[target] = data
        return data

    register_item_use = item_use

    def recipe(item_a, item_b, result=None, label=None, requires=None, consume=True, fail=None, **kwargs):
        key = _item_pair_key(item_a, item_b)
        data = {
            "items": key,
            "result": result,
            "label": label,
            "requires": requires,
            "consume": consume,
            "fail": fail,
        }
        data.update(kwargs)
        item_recipe_defs[key] = data
        return data

    def combine_fail(item_a, item_b, message):
        item_combine_fail_defs[_item_pair_key(item_a, item_b)] = message
        return message


init python:

    default_item_fail = "Nope."

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

    def item_icon(item_id):
        return item_defs.get(item_id, {}).get("icon", None)

    def item_tags(item_id):
        return list(item_defs.get(item_id, {}).get("tags", []) or [])

    def item_visible(item_id):
        data = item_defs.get(item_id, {})
        requirement = data.get("show_when", data.get("hidden_until", None))
        if not requirement:
            return True
        try:
            return meets_requirements(requirement, item=item_id)
        except Exception:
            return True

    def inventory_visible_items():
        return [(item_id, count) for item_id, count in inventory_list() if item_visible(item_id)]

    def inventory_items_matching(requirement=None, target=None, combine_with=None, allow_any_target=False):
        out = []
        for item_id, count in inventory_visible_items():
            if requirement:
                try:
                    if not item_matches_filter(item_id, requirement, target=target, combine_with=combine_with):
                        continue
                except Exception:
                    continue
            if target is not None and not allow_any_target and not item_has_use_target(item_id, target):
                continue
            if combine_with is not None and not can_combine_items(combine_with, item_id, quiet=True):
                continue
            out.append((item_id, count))
        return out

    def item_matches_filter(item_id, requirement=None, **kwargs):
        if not requirement:
            return True
        rules = requirement if isinstance(requirement, (list, tuple, set)) else [requirement]
        for rule in rules:
            if isinstance(rule, str) and rule.startswith("tag:"):
                wanted = rule.split(":", 1)[1]
                if wanted not in item_tags(item_id):
                    return False
            else:
                if not meets_requirements(rule, item=item_id, **kwargs):
                    return False
        return True

    def select_item(prompt="Use what?", filter=None, target=None, combine_with=None, allow_any_item=False):
        if not system_enabled("inventory"):
            return None
        renpy.show_screen(
            "inventory_item_picker",
            prompt=prompt,
            target=target,
            item_filter=filter,
            combine_with=combine_with,
            allow_any_item=allow_any_item,
        )
        return None

    def inventory_list():
        if not system_enabled("inventory"):
            return []
        return sorted(player_inventory.items())

    def use_item(item_id, target=None):
        if not system_enabled("inventory"):
            return None
        if not has_item(item_id):
            return None
        if target is not None:
            return use_item_on(item_id, target)
        data = item_defs.get(item_id, {})
        requirement = data.get("use_when")
        if requirement:
            try:
                if not meets_requirements(requirement, item=item_id, target=target):
                    renpy.notify(data.get("locked_message", "You can't use that right now."))
                    return None
            except Exception:
                pass
        label = data.get("use_label")
        if label:
            renpy.call_in_new_context(label, item_id, target)
            return True
        renpy.notify(data.get("use_message", "Nope."))
        return False

    def item_use_target_keys(target):
        target = str(target)
        return [(item_id, target) for item_id in ("*",) + tuple(item_defs.keys())]

    def item_use_data(item_id, target):
        target = str(target)
        return (
            item_use_defs.get((item_id, target)) or
            item_defs.get(item_id, {}).get("use_targets", {}).get(target) or
            item_use_defs.get(("*", target))
        )

    def item_has_use_target(item_id, target):
        return item_use_data(item_id, target) is not None

    def target_has_item_use(target):
        target = str(target)
        for item_id in item_defs.keys():
            if item_use_data(item_id, target):
                return True
        return item_use_defs.get(("*", target)) is not None

    def target_has_usable_inventory(target):
        for item_id, count in inventory_visible_items():
            if item_has_use_target(item_id, target):
                return True
        return False

    def can_use_item_on(item_id, target):
        if not system_enabled("inventory") or not has_item(item_id):
            return False
        data = item_use_data(item_id, target)
        if not data:
            return False
        if data.get("always_fail"):
            return False
        requirement = data.get("requires")
        if requirement:
            try:
                return meets_requirements(requirement, item=item_id, target=target)
            except Exception:
                return False
        return True

    def item_use_fail_message(item_id, target):
        data = item_use_data(item_id, target) or {}
        msg = data.get("fail")
        if msg:
            return _format_item_message(msg, item_id=item_id, target=target)
        return _format_item_message(item_defs.get(item_id, {}).get("use_message", default_item_fail), item_id=item_id, target=target)

    def _format_item_message(message, **kwargs):
        try:
            return str(message).format(
                item=kwargs.get("item_id", ""),
                item_name=item_name(kwargs.get("item_id", "")),
                target=kwargs.get("target", ""),
            )
        except Exception:
            return str(message)

    def use_item_on(item_id, target):
        if not system_enabled("inventory"):
            return None
        if not has_item(item_id):
            return None
        data = item_use_data(item_id, target)
        if not data:
            renpy.notify(default_item_fail)
            _remember_failed_recipe_or_use(item_id, target)
            return False
        if not can_use_item_on(item_id, target):
            renpy.notify(item_use_fail_message(item_id, target))
            _remember_failed_recipe_or_use(item_id, target)
            return False
        label = data.get("label")
        if data.get("consume"):
            remove_item(item_id, 1)
        if data.get("success"):
            renpy.notify(_format_item_message(data.get("success"), item_id=item_id, target=target))
        try:
            emit("item_used_on", item_id, target)
        except Exception:
            pass
        if label:
            renpy.call_in_new_context(label, item_id, target)
        return True

    def _remember_failed_recipe_or_use(item_a, item_b):
        try:
            failed_item_recipes.add(_item_pair_key(item_a, item_b))
        except Exception:
            pass

    def can_combine_items(item_a, item_b, quiet=False):
        if not system_enabled("inventory"):
            return False
        if item_a == item_b and item_count(item_a) < 2:
            return False
        if not has_item(item_a) or not has_item(item_b):
            return False
        data = item_recipe_defs.get(_item_pair_key(item_a, item_b))
        if not data:
            return False
        requirement = data.get("requires")
        if requirement:
            try:
                return meets_requirements(requirement, item=item_a, other_item=item_b)
            except Exception:
                return False
        return True

    def combine_items(item_a, item_b):
        if not system_enabled("inventory"):
            return None
        key = _item_pair_key(item_a, item_b)
        data = item_recipe_defs.get(key)
        if not data or not can_combine_items(item_a, item_b):
            msg = item_combine_fail_defs.get(key) or (data.get("fail") if data else None) or default_item_fail
            renpy.notify(_format_item_message(msg, item_id=item_a, target=item_b))
            _remember_failed_recipe_or_use(item_a, item_b)
            return False
        if data.get("consume", True):
            remove_item(item_a, 1)
            remove_item(item_b, 1)
        if data.get("result"):
            add_item(data.get("result"), 1)
        try:
            emit("items_combined", item_a, item_b, data.get("result"))
        except Exception:
            pass
        if data.get("label"):
            renpy.call_in_new_context(data.get("label"), item_a, item_b, data.get("result"))
        return True

    def examine_item(item_id):
        if not system_enabled("inventory"):
            return None
        if not has_item(item_id):
            return None
        data = item_defs.get(item_id, {})
        label = data.get("examine_label")
        if label:
            renpy.call_in_new_context(label, item_id)
            return True
        text = data.get("desc") or data.get("name") or item_id
        renpy.notify(text)
        return False
