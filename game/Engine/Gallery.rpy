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
        title=None,
        label=None,
        thumbnail=None,
        group="Main",
        character=None,
        characters=None,
        unlock=None,
        autounlock=False,
        setup=None,
        scene_image=None,
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

        if label is None:
            label = gallery_id
        if title is None:
            title = _gallery_title_from_id(gallery_id)
        if thumbnail is None:
            thumbnail = scene_image

        scene = {
            "id": gallery_id,
            "title": title,
            "label": label,
            "thumbnail": thumbnail,
            "group": group,
            "characters": [str(value) for value in linked_characters if value],
            "unlock": unlock,
            "autounlock": bool(autounlock),
            "setup": setup,
            "scene_image": scene_image,
        }
        scene.update(extra)

        for index, existing in enumerate(gallery_scenes):
            if existing.get("id") == gallery_id:
                gallery_scenes[index] = scene
                return scene

        gallery_scenes.append(scene)
        return scene


    def _gallery_title_from_id(gallery_id):
        text = str(gallery_id or "Scene").replace("_", " ").replace("-", " ").strip()
        if not text:
            return "Scene"
        return " ".join(part[:1].upper() + part[1:] for part in text.split())


    def _gallery_scene_def(gallery_id):
        return next((scene for scene in gallery_scenes if scene.get("id") == gallery_id), None)


    def gallery_scene(gallery_id, **kwargs):
        if kwargs:
            return gallery_register(gallery_id, **kwargs)
        return _gallery_scene_def(gallery_id)


    def gallery_register(
        gallery_id,
        title=None,
        label=None,
        character=None,
        characters=None,
        thumbnail=None,
        group="Main",
        unlock=None,
        autounlock=False,
        setup=None,
        scene_image=None,
        **extra
    ):
        return register_gallery_scene(
            gallery_id=gallery_id,
            title=title,
            label=label or gallery_id,
            thumbnail=thumbnail,
            group=group,
            character=character,
            characters=characters,
            unlock=unlock,
            autounlock=autounlock,
            setup=setup,
            scene_image=scene_image,
            **extra
        )


    def gallery_auto(label, character=None, characters=None, **kwargs):
        kwargs.setdefault("autounlock", True)
        return gallery_register(
            gallery_id=kwargs.pop("gallery_id", label),
            label=label,
            character=character,
            characters=characters,
            **kwargs
        )


    def replay_scene(label, **kwargs):
        kwargs.setdefault("autounlock", True)
        return gallery_register(
            gallery_id=kwargs.pop("gallery_id", label),
            label=label,
            **kwargs
        )


    def gallery(gallery_id, **kwargs):
        if kwargs:
            return gallery_register(gallery_id, **kwargs)
        return gallery_scene(gallery_id)


init python:


    def gallery_unlock_available(gallery_id):
        scene_def = _gallery_scene_def(gallery_id)
        if not scene_def:
            return False
        unlock = scene_def.get("unlock")
        if unlock is None:
            return False
        try:
            return meets_requirements(unlock)
        except Exception:
            return False


    def _run_gallery_setup(scene_def):
        setup = scene_def.get("setup")
        if not setup:
            return
        if callable(setup):
            setup()
            return
        if isinstance(setup, str) and renpy.has_label(setup):
            renpy.call(setup)


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

        _run_gallery_setup(scene_def)
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


    def _gallery_label_reached(label, *args, **kwargs):
        try:
            if getattr(store, "_in_replay", None):
                return
        except Exception:
            pass
        for scene in gallery_scenes:
            if scene.get("autounlock") and scene.get("label") == label:
                unlock_gallery(scene.get("id"))


init 999 python:
    try:
        if hasattr(config, "label_callbacks"):
            if _gallery_label_reached not in config.label_callbacks:
                config.label_callbacks.append(_gallery_label_reached)
    except Exception:
        pass
