# =============================================================================
# Main Menu Layers
# =============================================================================
# Optional layered/parallax-like visuals for the main menu. Empty by default.
# =============================================================================


init -10 python:
    main_menu_layers = []


init python:

    def main_menu_layer(image, pos=(0.5, 0.5), zoom=1.0, alpha=1.0, drift=None, order=0, **extra):
        data = {
            "image": image,
            "pos": pos,
            "zoom": zoom,
            "alpha": alpha,
            "drift": drift,
            "order": order,
        }
        data.update(extra)
        main_menu_layers.append(data)
        main_menu_layers.sort(key=lambda item: item.get("order", 0))
        return data


transform main_menu_layer_static(xa=0.5, ya=0.5, z=1.0, a=1.0, xo=0, yo=0):
    xalign xa
    yalign ya
    zoom z
    alpha a
    xoffset xo
    yoffset yo


transform main_menu_layer_drift(dx=0, dy=0, dur=16.0):
    block:
        xoffset 0
        yoffset 0
        linear dur xoffset dx yoffset dy
        linear dur xoffset 0 yoffset 0
        repeat


screen main_menu_visual_layers():
    for _layer in main_menu_layers:
        if _layer.get("image"):
            $ _pos = _layer.get("pos", (0.5, 0.5))
            $ _offset = _layer.get("offset", (0, 0))
            $ _zoom = _layer.get("zoom", 1.0)
            $ _alpha = _layer.get("alpha", 1.0)
            $ _drift = _layer.get("drift")
            if _drift:
                $ _dx = _drift[0] if isinstance(_drift, (tuple, list)) and len(_drift) > 0 else _layer.get("drift_x", 0)
                $ _dy = _drift[1] if isinstance(_drift, (tuple, list)) and len(_drift) > 1 else _layer.get("drift_y", 0)
                $ _dur = _layer.get("duration", 16.0)
                add _layer.get("image"):
                    at main_menu_layer_static(_pos[0], _pos[1], _zoom, _alpha, _offset[0], _offset[1]), main_menu_layer_drift(_dx, _dy, _dur)
            else:
                add _layer.get("image"):
                    at main_menu_layer_static(_pos[0], _pos[1], _zoom, _alpha, _offset[0], _offset[1])
