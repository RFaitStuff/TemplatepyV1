# =============================================================================
# Engine/World/Location_Package.rpy
# -----------------------------------------------------------------------------
# Author-facing wrappers for making exploration locations in one readable block.
# These helpers call the existing registries instead of replacing them.
# =============================================================================

init -2 python:

    def action(
        id,
        label=None,
        title=None,
        requires=None,
        icon=None,
        primary=False,
        tooltip=None,
        once=False,
        repeatable=True,
        quiet_after_seen=True,
        repeat_hint=None,
        seen_message=None,
        **kwargs
    ):
        raw_id = str(id)
        action_id = kwargs.pop("action_id", None) or _action_id_from_title(raw_id)
        action_title = title or raw_id.replace("_", " ").title()
        data = {
            "id": action_id,
            "title": action_title,
            "label": label,
            "requires": requires,
            "icon": icon,
            "primary": primary,
            "tooltip": tooltip,
            "once": once,
            "repeatable": repeatable,
            "quiet_after_seen": quiet_after_seen,
            "repeat_hint": repeat_hint,
            "seen_message": seen_message,
        }
        data.update(kwargs)
        return data

    def _action_id_from_title(value):
        text = str(value).strip()
        if text.lower() == text and " " not in text:
            return text
        out = []
        last_was_sep = False
        for ch in text.lower():
            if ch.isalnum():
                out.append(ch)
                last_was_sep = False
            elif not last_was_sep:
                out.append("_")
                last_was_sep = True
        return "".join(out).strip("_") or "action"

    def item_spot(item, pos=(0.5, 0.5), label=None, requires=None, while_flag=None, hide_flag=None, size=None, **kwargs):
        data = {
            "item": item,
            "label": label or ("pickup_" + str(item)),
            "pos": pos,
        }
        if requires is not None:
            data["requires"] = requires
        if while_flag is not None:
            data["while_flag"] = while_flag
        if hide_flag is not None:
            data["hide_flag"] = hide_flag
        if size is not None:
            data["size"] = size
        data.update(kwargs)
        return data

    def exit_spot(to, label=None, pos=(0.5, 0.95), size=(200, 460), requires=None, locked_message=None, show_when_locked=False, **kwargs):
        data = {
            "to": to,
            "label": label or location_name(to),
            "pos": pos,
            "size": size,
        }
        if requires is not None:
            data["requires"] = requires
        if locked_message is not None:
            data["locked_message"] = locked_message
        if show_when_locked:
            data["show_when_locked"] = True
        data.update(kwargs)
        return data

    def explore_layer(
        image,
        slot="overlay",
        pos=(0.5, 0.5),
        zoom=1.0,
        alpha=1.0,
        drift=None,
        order=0,
        requires=None,
        show_when=None,
        available_if=None,
        **kwargs
    ):
        data = {
            "image": image,
            "slot": slot,
            "pos": pos,
            "zoom": zoom,
            "alpha": alpha,
            "drift": drift,
            "order": order,
        }
        if requires is not None:
            data["requires"] = requires
        if show_when is not None:
            data["show_when"] = show_when
        if available_if is not None:
            data["available_if"] = available_if
        data.update(kwargs)
        return data

    parallax_layer = explore_layer

    def object_spot(
        id,
        name=None,
        pos=(0.5, 0.5),
        size=(100, 100),
        image=None,
        hover_image=None,
        hitbox=None,
        actions=None,
        requires=None,
        kind="object",
        desc=None,
        allow_item_use=False,
        **kwargs
    ):
        data = {
            "id": id,
            "label": name or str(id).replace("_", " ").title(),
            "pos": pos,
            "size": size,
        }
        if image is not None:
            data["image"] = image
        if hover_image is not None:
            data["hover_image"] = hover_image
        if hitbox is not None:
            data["hitbox"] = _normalize_hitbox(hitbox, size=size)
        if requires is not None:
            data["requires"] = requires
        data.update(kwargs)

        interactable_extra = {}
        if desc is not None:
            interactable_extra["desc"] = desc
        if allow_item_use:
            interactable_extra["allow_item_use"] = True
        register_interactable(
            id,
            kind=kind,
            title=data["label"],
            actions=_prepare_object_actions(id, actions or [], desc=desc),
            **interactable_extra
        )
        return data

    def location_package(
        id,
        name=None,
        area=None,
        bg=None,
        variants=None,
        unlocked=True,
        order_after=None,
        positions=None,
        npcs=None,
        items=None,
        objects=None,
        exits=None,
        layers=None,
        parallax=None,
        talk=None,
        on_enter=None,
        first_visit=None,
        first_visit_today=None,
        main_loop=None,
        hover_fade=None,
        scene_dissolve=None,
        **kwargs
    ):
        register_location(
            id,
            name=name,
            bg=bg,
            area=area,
            variants=variants,
            unlocked=unlocked,
            order_after=order_after,
        )

        loc_positions = dict(positions or {})
        if npcs:
            for entry in npcs:
                if isinstance(entry, str):
                    loc_positions.setdefault(entry, [(0.5, 1.0)])
                elif isinstance(entry, (tuple, list)) and len(entry) >= 2:
                    cid = entry[0]
                    loc_positions.setdefault(cid, [])
                    if isinstance(entry[1], list):
                        loc_positions[cid].extend(entry[1])
                    else:
                        loc_positions[cid].append(entry[1])

        packaged_items = [_normalize_item_spot(it) for it in (items or [])]
        packaged_objects = [_normalize_object_spot(obj) for obj in (objects or [])]
        packaged_exits = [_normalize_exit_spot(ex) for ex in (exits or [])]
        raw_layers = list(layers or []) + list(parallax or [])
        packaged_layers = [_normalize_explore_layer(layer) for layer in raw_layers]

        extra = dict(kwargs)
        if first_visit is not None:
            extra["first_visit"] = first_visit
        if first_visit_today is not None:
            extra["first_visit_today"] = first_visit_today
        if main_loop is not None:
            extra["main_loop"] = main_loop
        if hover_fade is not None:
            extra["hover_fade"] = hover_fade
        if scene_dissolve is not None:
            extra["scene_dissolve"] = scene_dissolve

        configure_location(
            id,
            positions=loc_positions,
            items=packaged_items,
            objects=packaged_objects,
            exits=packaged_exits,
            layers=packaged_layers,
            talk=talk,
            on_enter=on_enter,
            **extra
        )
        return location_data(id)

    def _prepare_object_actions(iid, actions, desc=None):
        prepared = []
        if desc is not None and not any(a.get("id") == "investigate" for a in actions):
            prepared.append(action("investigate", label="_auto_investigate", title="Investigate", primary=not bool(actions)))
        for a in actions:
            if isinstance(a, dict):
                prepared.append(a)
            elif isinstance(a, (tuple, list)):
                prepared.append(action(*a))
        return prepared

    def _normalize_item_spot(it):
        if isinstance(it, dict):
            return dict(it)
        if isinstance(it, str):
            return item_spot(it)
        if isinstance(it, (tuple, list)):
            return item_spot(*it)
        return dict(it)

    def _normalize_object_spot(obj):
        if isinstance(obj, dict):
            return dict(obj)
        return obj

    def _normalize_exit_spot(ex):
        if isinstance(ex, dict):
            return dict(ex)
        if isinstance(ex, str):
            return exit_spot(ex)
        if isinstance(ex, (tuple, list)):
            return exit_spot(*ex)
        return dict(ex)

    def _normalize_explore_layer(layer):
        if isinstance(layer, dict):
            return dict(layer)
        if isinstance(layer, str):
            return explore_layer(layer)
        if isinstance(layer, (tuple, list)):
            return explore_layer(*layer)
        return dict(layer)

    def _normalize_hitbox(hitbox, size=(100, 100)):
        if isinstance(hitbox, dict):
            return dict(hitbox)
        if hitbox in ("opaque", "image", "alpha"):
            return {"type": "opaque"}
        if isinstance(hitbox, str):
            if hitbox.startswith("rect:"):
                values = _hitbox_numbers(hitbox[5:])
                if len(values) >= 4:
                    return {"type": "rect", "rect": tuple(values[:4]), "size": _rect_hitbox_size(values[:4], size)}
            if hitbox.startswith("poly:"):
                return {"type": "poly", "points": _hitbox_points(hitbox[5:]), "size": size}
            if hitbox.startswith("mask:"):
                return {"type": "mask", "mask": hitbox[5:].strip(), "size": size}
        return {"type": "custom", "value": hitbox, "size": size}

    def _hitbox_numbers(text):
        out = []
        for raw in str(text).replace(",", " ").split():
            try:
                out.append(float(raw))
            except Exception:
                pass
        return out

    def _hitbox_points(text):
        nums = _hitbox_numbers(text)
        return [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]

    def _rect_hitbox_size(rect, fallback):
        x, y, w, h = rect
        if 0 < w <= 1 and 0 < h <= 1:
            return (int(config.screen_width * w), int(config.screen_height * h))
        return (int(w), int(h))


label _auto_investigate:
    $ _iid = _pending_interactable_id
    $ _def = get_interactable(_iid) or {}
    $ _desc = _def.get("desc") or "There is nothing unusual here."
    "[_desc]"
    jump explore
