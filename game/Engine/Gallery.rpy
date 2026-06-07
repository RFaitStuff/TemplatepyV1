# =============================================================================
# Gallery
# =============================================================================
# Gallery scenes replay the same labels used by the live game. Runtime state
# declared with `default` is restored by Ren'Py replay mode; persistent writes
# should continue to guard against `_in_replay`.
# =============================================================================


init -3 python:
    gallery_scenes = []


    def register_gallery_scene(
        gallery_id,
        title,
        label,
        thumbnail=None,
        group="Main",
        character=None,
        characters=None,
        **extra
    ):
        """Registers or updates a gallery entry.

        `character="alice"` remains supported for the original cheat-sheet
        syntax. `characters=["alice", "alex"]` is preferred for multi-character
        scenes. Registration is idempotent, so init ordering cannot create
        duplicate cards.
        """
        linked_characters = []
        if characters is not None:
            if isinstance(characters, str):
                linked_characters.append(characters)
            else:
                linked_characters.extend(characters)
        if character and character not in linked_characters:
            linked_characters.append(character)

        scene = {
            "id": gallery_id,
            "title": title,
            "label": label,
            "thumbnail": thumbnail,
            "group": group,
            "characters": [str(value) for value in linked_characters if value],
        }
        scene.update(extra)

        for index, existing in enumerate(gallery_scenes):
            if existing.get("id") == gallery_id:
                gallery_scenes[index] = scene
                return scene

        gallery_scenes.append(scene)
        return scene


init python:

    def gallery_scene(gallery_id):
        return next((scene for scene in gallery_scenes if scene.get("id") == gallery_id), None)


    def play_gallery(gallery_id):
        try:
            if not system_enabled("gallery"):
                return None
        except Exception:
            pass

        scene_def = gallery_scene(gallery_id)
        if not scene_def:
            renpy.notify("Gallery scene '{}' is not registered.".format(gallery_id))
            return None

        label = scene_def.get("label")
        if not label or not renpy.has_label(label):
            renpy.notify("Gallery scene '{}' has a missing replay label.".format(gallery_id))
            try:
                renpy.log("Gallery '{}' points to missing label {!r}.".format(gallery_id, label))
            except Exception:
                pass
            return None

        renpy.call_replay(label)
        return None


    def unlocked_gallery_scenes():
        return [scene for scene in gallery_scenes if is_gallery_unlocked(scene.get("id"))]


    def gallery_groups():
        groups = {}
        for scene in gallery_scenes:
            groups.setdefault(scene.get("group", "Main"), []).append(scene)
        return groups


    def _scene_matches_character(scene_def, char_id):
        cid = str(char_id or "").lower()
        if not cid:
            return False

        explicit = [str(value).lower() for value in scene_def.get("characters", [])]
        if explicit:
            return cid in explicit

        # Backward compatibility for old registrations without metadata.
        gallery_id = str(scene_def.get("id", "")).lower()
        title = str(scene_def.get("title", "")).lower()
        group = str(scene_def.get("group", "")).lower()
        return cid in gallery_id or cid in title or cid == group


    def character_gallery_scenes(char_id):
        return [scene for scene in gallery_scenes if _scene_matches_character(scene, char_id)]


    def extra_gallery_scenes():
        try:
            characters = list(character_stats.keys())
        except Exception:
            characters = []

        result = []
        for scene in gallery_scenes:
            group = str(scene.get("group", "")).strip().lower()
            if group in ("extra", "extras"):
                result.append(scene)
                continue
            if not any(_scene_matches_character(scene, cid) for cid in characters):
                result.append(scene)
        return result


    def gallery_validation_issues():
        issues = []
        seen = set()
        for scene in gallery_scenes:
            gallery_id = scene.get("id")
            if not gallery_id:
                issues.append("Gallery entry has no id: {!r}".format(scene))
                continue
            if gallery_id in seen:
                issues.append("Duplicate gallery id: {}".format(gallery_id))
            seen.add(gallery_id)
            label = scene.get("label")
            if not label or not renpy.has_label(label):
                issues.append("Gallery '{}' has missing label '{}'.".format(gallery_id, label))
        return issues
