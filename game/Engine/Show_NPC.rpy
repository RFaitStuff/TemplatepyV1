# =============================================================================
# Character display helpers
# =============================================================================
# show_npc(char, ...) takes care of:
#   - Picking the right pose variant for the current location (or the one
#     you ask for explicitly).
#   - Placing the character at a randomized position from the location's
#     position pool (or an explicit (x, y) you pass in).
#   - Standard zoom of 0.5 so portraits are consistently sized.
#   - Honoring react() overrides so a one-line expression doesn't get blown
#     away by the show.
#
# Usage from script:
#   $ show_npc("alice")                          # location decides pose + spot
#   $ show_npc("alice", variant="1")             # force pose 1
#   $ show_npc("alice", pos=(0.7, 1.0))          # force position
#   $ show_npc("alice", emotion="lustful")       # like react(): one-line override
#   $ show_npc("alice", outfit="casual")         # override the area outfit
#   $ hide_npc("alice")
# =============================================================================

# Default zoom for ALL character portraits.
define character_default_zoom = 0.5


# Live registry of characters on screen + the position they're at. Kept up to
# date by show_npc / hide_npc so the choice menu can do collision-aware
# displacement (see Engine/UI/Choice.rpy).
default _visible_npcs = {}        # char_id -> {"pos": (x, y), "locked": bool}


init python:

    def show_npc(
        char, variant=None, pos=None, zoom=None, emotion=None,
        outfit=None, behind=None, transform=None, locked=False,
    ):
        # Show a character on screen with auto-pose, auto-position, and
        # auto-zoom.
        # locked=True marks this position as author-controlled - the choice
        # menu's displacement logic will leave them alone.
        # 1) Pose variant
        if variant is None:
            variant = location_character_pose(current_location, char)
        # 2) Emotion override (react() behaviour)
        if emotion is not None:
            _portrait_override[char] = emotion
        # 3) Outfit override
        if outfit is not None:
            character_outfit_override[char] = outfit
        # 4) Position
        if pos is None:
            pos = location_character_pos(current_location, char)
        if zoom is None:
            zoom = character_default_zoom

        img_attrs = "characters " + char + variant

        if transform is None:
            transform = Transform(
                xalign=pos[0], yalign=pos[1],
                zoom=zoom,
            )
        # Explore sprites always live on master. Dialogue sprites are handled
        # separately by Engine/Dialogue/Dialogue_Handler.rpy.
        renpy.show(
            img_attrs,
            at_list=[transform],
            tag=char,
            layer="master",
            behind=([behind] if behind else []),
        )

        # Track for displacement.
        _visible_npcs[char] = {
            "pos":      pos,
            "zoom":     zoom,
            "variant":  variant,
            "locked":   bool(locked),
            "behind":   behind,
        }

    def hide_npc(char):
        renpy.hide(char, layer="master")
        _portrait_override.pop(char, None)
        character_outfit_override.pop(char, None)
        _visible_npcs.pop(char, None)

    def lock_npc(char, locked=True):
        # Mark a visible character as author-positioned so the choice menu
        # won't auto-displace them.
        if char in _visible_npcs:
            _visible_npcs[char]["locked"] = bool(locked)


# =============================================================================
# show_all_npcs_here() - render every scheduled NPC at their random spots.
# Called by the `explore` label in script.rpy after the scene is set.
# =============================================================================
init python:

    def show_all_npcs_here():
        # Resetting tracker first so any leftovers from a previous room don't
        # falsely trigger menu-displacement.
        _visible_npcs.clear()
        try:
            _npc_highlight_state.clear()
        except NameError:
            pass
        for c in npcs_here():
            show_npc(c)

    _npc_highlight_state = {}

    def set_explore_npc_highlight(char, mode=None):
        if char not in _visible_npcs:
            return None
        info = _visible_npcs.get(char, {})
        key = mode or "none"
        if _npc_highlight_state.get(char) == key:
            return None
        _npc_highlight_state[char] = key
        pos = info.get("pos", (0.5, 1.0))
        zoom = info.get("zoom", character_default_zoom)
        variant = info.get("variant", "")
        behind = info.get("behind", None)
        matrix = None
        if mode == "hover":
            matrix = BrightnessMatrix(0.25)
        elif mode == "reveal":
            matrix = TintMatrix("#ffd84a")
        transform = Transform(
            xalign=pos[0], yalign=pos[1],
            zoom=zoom,
            matrixcolor=matrix,
        )
        renpy.show(
            "characters " + char + variant,
            at_list=[transform],
            tag=char,
            layer="master",
            behind=([behind] if behind else []),
        )
        return None

    def sync_explore_npc_highlights(hovered=None, reveal=False, chars=None):
        if chars is None:
            chars = list(_visible_npcs.keys())
        for char in chars:
            if hovered == char:
                set_explore_npc_highlight(char, "hover")
            elif reveal:
                set_explore_npc_highlight(char, "reveal")
            else:
                set_explore_npc_highlight(char, None)
        return None


# =============================================================================
# Auto-tracking for raw `show alice` style usage
# -----------------------------------------------------------------------------
# Authors prefer the terser `show alice` over `$ show_npc("alice")`. Raw show
# statements bypass our tracker, so we sync `_visible_npcs` to whatever images
# Ren'Py actually has on screen at the start of every interaction.
#
# Raw-shown characters get registered with `locked=True`, which means:
#   - The choice menu's displacement engine leaves them alone (we don't know
#     where the author placed them, so we shouldn't move them).
#   - Talk-mode dim/blur logic still works on them.
# Authors who want auto-displacement should still call `show_npc()`.
# =============================================================================
init python:

    def _known_character_ids():
        # Anything declared via tracked_character() lands in character_stats.
        # Fallback to a small static list if that registry isn't populated.
        try:
            return list(character_stats.keys())
        except Exception:
            return []

    def _sync_visible_npcs_from_shown():
        # While a conversation is active, dialogue cast tracking takes over
        # in Engine/Dialogue/Dialogue_Handler.rpy. Touching `_visible_npcs` here would
        # falsely flag cast members as "in the room" and confuse the menu
        # displacement, so we bail.
        if getattr(store, "_in_dialogue", None):
            return
        try:
            shown = set(renpy.get_showing_tags(layer="master"))
        except Exception:
            return
        known = _known_character_ids()
        # Add any character that's on screen but not yet tracked. Defaults
        # are best-guesses - locked=True so we never displace them.
        for c in known:
            if c in shown and c not in _visible_npcs:
                _visible_npcs[c] = {
                    "pos":     (0.5, 1.0),
                    "zoom":    character_default_zoom,
                    "variant": "",
                    "locked":  True,
                    "behind":  None,
                }
        # Drop any tracker entry whose image is no longer on screen so old
        # data doesn't haunt the next room.
        for c in list(_visible_npcs.keys()):
            if c in known and c not in shown:
                _visible_npcs.pop(c, None)

    if _sync_visible_npcs_from_shown not in config.start_interact_callbacks:
        config.start_interact_callbacks.append(_sync_visible_npcs_from_shown)


# =============================================================================
# Short-form image aliases
# -----------------------------------------------------------------------------
# Lets authors write `show alice` / `show alice 2` instead of having to
# remember the full `show characters alice 2` form. We only register an alias
# when:
#   - The long-form image (e.g. `characters alice 2`) is actually loaded.
#   - The short name isn't already taken by something else in the project.
#
# The alias is a true ImageReference, so all the original image's frames /
# variants / animations are preserved.
# =============================================================================
init 1 python:

    def _alias_to_long(short_attrs, long_attrs):
        # short_attrs: tuple, e.g. ("alice",) or ("alice", "2")
        # long_attrs:  tuple, e.g. ("characters", "alice", "1")
        try:
            from renpy.display.image import ImageReference
        except Exception:
            return
        if renpy.has_image(short_attrs, exact=True):
            return  # don't clobber an existing definition
        if not renpy.has_image(long_attrs, exact=True):
            return  # the original image isn't there - skip
        try:
            renpy.image(short_attrs, ImageReference(long_attrs))
        except Exception:
            pass

    def _autoalias_character_images():
        chars = []
        try:
            chars = list(character_stats.keys())
        except Exception:
            pass
        # Variant/expression attribute candidates worth aliasing. Keep these
        # lists small; adding obscure ones just slows init.
        variants = ["1", "2", "3", "4", "5"]
        expressions = [
            "happy", "sad", "angry", "embarrassed", "lustful", "tired",
            "loving", "blush", "doubt", "teasing", "worried", "neutral",
        ]
        for cid in chars:
            # Default `show alice` -> dynamic area/mood-aware portrait.
            _alias_to_long((cid,), ("characters", cid))

            # Variant aliases: `show alice 1`, `show alice 2`, ...
            for v in variants:
                long_attrs  = ("characters", cid, v)
                short_attrs = (cid, v)
                _alias_to_long(short_attrs, long_attrs)

            # Explicit expression aliases: `show alice happy`.
            for e in expressions:
                _alias_to_long((cid, e), ("characters", cid, e))
                for v in variants:
                    _alias_to_long((cid, v, e), ("characters", cid, v, e))

    _autoalias_character_images()
