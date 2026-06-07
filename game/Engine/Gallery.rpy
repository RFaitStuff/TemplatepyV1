# =============================================================================
# Gallery
# =============================================================================
# Replays story scenes WITHOUT advancing or mutating the live save.
#
# The big win here: gallery scenes are just regular labels - the SAME labels
# used by the live game. There is no parallel "_replay" copy to maintain.
#
# How isolation works:
#   1) play_gallery() calls renpy.call_replay(label).
#   2) Ren'Py snapshots all `default`-declared store variables, sets the
#      built-in `_in_replay` to the label name, runs the scene, and on return
#      restores every default automatically. Inventory changes, flag flips,
#      mood swings, stat gains - all reverted.
#   3) Persistent state is NOT auto-reverted, so anything you don't want to
#      re-trigger on replay must check `_in_replay`. The unlocks are already
#      gated in Engine/State/Persistent.rpy:
#          def unlock_gallery(name):
#              if getattr(store, "_in_replay", None): return
#              persistent.galleryunlocks.add(name)
#      Apply the same one-line guard to any other persistent.* mutation, or
#      to anything else you don't want to fire during a replay.
#
# Usage from a story file:
#   init python:
#       register_gallery_scene(
#           gallery_id="ch1_intro",
#           title="Chapter 1 - Introduction",
#           label="chapter1_intro",          # the SAME label the live game runs
#           thumbnail="mainstory story1",
#           group="Main",
#       )
#
#   # in dialogue:
#   $ unlock_gallery("ch1_intro")            # auto-no-op during replay
# =============================================================================


# Registry (init-time, identical across saves).
init -3 python:
    gallery_scenes = []

    def register_gallery_scene(gallery_id, title, label, thumbnail=None, group="Main"):
        gallery_scenes.append({
            "id":        gallery_id,
            "title":     title,
            "label":     label,
            "thumbnail": thumbnail,
            "group":     group,
        })


init python:

    def play_gallery(gallery_id):
        # Find the registered scene and hand it to Ren'Py's replay machinery.
        # call_replay sandboxes ALL `default`-declared store state for us.
        scene_def = next((s for s in gallery_scenes if s["id"] == gallery_id), None)
        if not scene_def:
            return
        renpy.call_replay(scene_def["label"])

    def unlocked_gallery_scenes():
        return [s for s in gallery_scenes if is_gallery_unlocked(s["id"])]

    def gallery_groups():
        # {group_name: [scene_def, ...]} for the UI to lay out.
        out = {}
        for s in gallery_scenes:
            out.setdefault(s["group"], []).append(s)
        return out

    def _scene_matches_character(scene_def, char_id):
        gid = str(scene_def.get("id", "")).lower()
        ttl = str(scene_def.get("title", "")).lower()
        grp = str(scene_def.get("group", "")).lower()
        cid = str(char_id or "").lower()
        if not cid:
            return False
        return (cid in gid) or (cid in ttl) or (cid == grp)

    def character_gallery_scenes(char_id):
        return [s for s in gallery_scenes if _scene_matches_character(s, char_id)]

    def extra_gallery_scenes():
        chars = []
        try:
            chars = list(character_stats.keys())
        except Exception:
            chars = []

        out = []
        for s in gallery_scenes:
            grp = str(s.get("group", "")).strip().lower()
            if grp in ("extra", "extras"):
                out.append(s)
                continue
            if not any(_scene_matches_character(s, c) for c in chars):
                out.append(s)
        return out
