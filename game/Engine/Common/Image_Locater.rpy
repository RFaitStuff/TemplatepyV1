# =============================================================================
# Auto Image Locator
# =============================================================================
# Character filename grammar:
#
#   <Character><variant?>_<outfit?>_<emotion?>.<ext>
#
# Examples:
#   Alex.png
#   Alex_Sad.png
#   Alex1.png
#   Alex_Outfit1.png
#   Alex_Outfit1_Sad.png
#
# Author-facing syntax is generated directly from the discovered files:
#
#   show alex
#   show alex sad
#   show alex outfit1
#   show alex outfit1 sad
#   show alex 1 outfit1 sad
#
# The `characters ...` names remain available as internal/advanced aliases, but
# normal game scripts do not need to use them.
# =============================================================================


define tod_folders = {"bg"}
define character_folders = {"characters"}
define character_image_aliases = {}
define extra_emotion_names = {"blush", "doubt", "teasing", "neutral"}


default character_outfit_override = {}


init -10 python:
    import os as _os
    import re as _re

    _IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")
    _TOD_ORDER = ["midnight", "night", "evening", "afternoon", "day", None]
    _TOD_RE = _re.compile(
        r"^(.+?)(?:_(midnight|night|evening|afternoon|day)\d*[a-z]*)?$",
        _re.IGNORECASE,
    )
    _CHAR_HEAD_RE = _re.compile(r"^([A-Za-z][A-Za-z0-9_]*?)(\d*)$")


    def get_time_of_day(value):
        if 6 <= value <= 11:
            return "day"
        if 12 <= value <= 17:
            return "afternoon"
        if 18 <= value <= 21:
            return "evening"
        if 22 <= value <= 23:
            return "night"
        return "midnight"


    def _is_character_folder(folder_lc):
        return folder_lc in {value.lower() for value in character_folders}


    def _is_tod_folder(folder_lc):
        return folder_lc in {value.lower() for value in tod_folders}


    def _image_relative_parts(path):
        rel = asset_strip_root(path, asset_image_roots)
        parts = [part for part in rel.split("/") if part]
        if parts and parts[0].lower() == "images":
            parts = parts[1:]
        return parts


    def _known_image_emotions():
        values = set(extra_emotion_names)
        try:
            values.update(MOOD_DEFS.keys())
        except Exception:
            pass
        return {str(value).lower() for value in values}


    def _parse_character_filename(name):
        """Returns (character, variant, outfit, emotion)."""
        parts = name.split("_")
        head = parts[0]
        match = _CHAR_HEAD_RE.match(head)
        if not match:
            return None

        char = match.group(1).lower()
        variant = match.group(2) or ""
        rest = [part.lower() for part in parts[1:] if part]
        known_emotions = _known_image_emotions()
        outfit = None
        emotion = None

        if rest:
            if rest[-1] in known_emotions:
                emotion = rest[-1]
                if len(rest) > 1:
                    outfit = "_".join(rest[:-1])
            elif len(rest) >= 2:
                # Unknown final names still support custom expressions.
                outfit = "_".join(rest[:-1])
                emotion = rest[-1]
            else:
                outfit = rest[0]

        return char, variant, outfit, emotion


    def _parse_tod_filename(name):
        match = _TOD_RE.match(name)
        if not match:
            return name.lower(), None
        return match.group(1).lower(), (match.group(2) or "").lower() or None


    def _build_image_index():
        index = {"characters": {}, "tod": {}, "other": {}}

        for filename in renpy.list_files():
            normalized = asset_norm(filename)
            if not normalized.lower().endswith(_IMG_EXTS):
                continue
            if not asset_under(normalized, asset_image_roots):
                continue

            relative_parts = _image_relative_parts(normalized)
            if len(relative_parts) < 2:
                continue

            folder_parts = relative_parts[:-1]
            if not folder_parts:
                continue

            folder_lc = folder_parts[-1].lower()
            stem = _os.path.splitext(relative_parts[-1])[0]

            if _is_character_folder(folder_lc):
                parsed = _parse_character_filename(stem)
                if not parsed:
                    continue
                char, variant, outfit, emotion = parsed
                variants = index["characters"].setdefault(char, {})
                variants.setdefault(variant, []).append((outfit, emotion, normalized))

            elif _is_tod_folder(folder_lc):
                base, tod = _parse_tod_filename(stem)
                folder = index["tod"].setdefault(folder_lc, {})
                folder.setdefault(base, {}).setdefault(tod, []).append(normalized)

            else:
                folder = index["other"].setdefault(folder_lc, {})
                folder.setdefault(stem.lower(), []).append(normalized)

        for variants in index["characters"].values():
            for entries in variants.values():
                entries.sort(key=lambda entry: (entry[0] or "", entry[1] or "", entry[2]))

        for folder in index["tod"].values():
            for bases in folder.values():
                for paths in bases.values():
                    paths.sort()

        for folder in index["other"].values():
            for paths in folder.values():
                paths.sort()

        return index


init -10 python:

    def _character_source_id(char):
        try:
            return character_image_aliases.get(char, char)
        except Exception:
            return char


    def _current_outfit_for(char):
        try:
            override = character_outfit_override.get(char)
            if override:
                return str(override).lower()
        except Exception:
            pass

        try:
            outfit = area_outfit(current_area_id())
            return str(outfit).lower() if outfit else None
        except Exception:
            return None


    def _current_emotion_for(char):
        try:
            value = _portrait_emotion_for(char)
            return str(value).lower() if value else None
        except Exception:
            return None


    def _entry_score(entry, wanted_outfit, wanted_emotion):
        outfit, emotion, _path = entry
        score = 0

        if wanted_outfit:
            if outfit == wanted_outfit:
                score += 20
            elif outfit is None:
                score += 4
            else:
                score -= 20
        else:
            score += 5 if outfit is None else 0

        if wanted_emotion:
            if emotion == wanted_emotion:
                score += 30
            elif emotion is None:
                score += 3
            else:
                score -= 30
        else:
            score += 6 if emotion is None else 0

        return score


    def _best_character_entry(source_char, variant, wanted_outfit, wanted_emotion):
        variants = image_index.get("characters", {}).get(source_char, {})
        variant_order = []
        if variant:
            variant_order.append(variant)
        if "" not in variant_order:
            variant_order.append("")

        for variant_id in variant_order:
            entries = variants.get(variant_id) or []
            if not entries:
                continue
            scored = [(_entry_score(entry, wanted_outfit, wanted_emotion), entry) for entry in entries]
            scored.sort(key=lambda pair: (pair[0], pair[1][2]), reverse=True)
            if scored:
                return scored[0][1]
        return None


    def _resolve_character_overrides(
        st,
        at,
        source_char,
        variant,
        mood_id,
        forced_outfit,
        forced_emotion,
        auto_outfit,
        auto_emotion,
    ):
        logical_char = mood_id or source_char
        wanted_outfit = _current_outfit_for(logical_char) if auto_outfit else forced_outfit
        wanted_emotion = _current_emotion_for(logical_char) if auto_emotion else forced_emotion
        entry = _best_character_entry(source_char, variant, wanted_outfit, wanted_emotion)
        if entry is None:
            return Null(), None
        return Image(entry[2]), None


    def _character_dynamic(
        source_char,
        variant="",
        mood_id=None,
        forced_outfit=None,
        forced_emotion=None,
        auto_outfit=True,
        auto_emotion=True,
    ):
        return DynamicDisplayable(
            _resolve_character_overrides,
            source_char,
            variant,
            mood_id,
            forced_outfit,
            forced_emotion,
            auto_outfit,
            auto_emotion,
        )


    # Compatibility callbacks used by older code.
    def _resolve_character(st, at, char, variant, mood_id):
        return _resolve_character_overrides(st, at, char, variant, mood_id, None, None, True, True)


    def _resolve_character_forced(st, at, char, variant, outfit, emotion):
        return _resolve_character_overrides(st, at, char, variant, None, outfit, emotion, False, False)


    def _resolve_tod(st, at, folder_lc, base):
        bases = image_index.get("tod", {}).get(folder_lc, {})
        entry = bases.get(base, {})
        if not entry:
            return Null(), None

        try:
            current_time = time
        except Exception:
            current_time = 8

        tod = get_time_of_day(current_time)
        try:
            start_index = _TOD_ORDER.index(tod)
        except ValueError:
            start_index = 0

        for value in _TOD_ORDER[start_index:]:
            paths = entry.get(value)
            if paths:
                return Image(paths[0]), None
        return Null(), None


    def _register_image_if_missing(name, displayable):
        name_tuple = tuple(name.split()) if isinstance(name, str) else tuple(name)
        try:
            if renpy.has_image(name_tuple, exact=True):
                return False
        except Exception:
            pass
        renpy.image(name_tuple, displayable)
        return True


    def _logical_character_ids(source_char):
        result = [source_char]
        for alias, source in character_image_aliases.items():
            if source == source_char and alias not in result:
                result.append(alias)
        return result


    def _register_character_names(source_char, logical_char, variant, entries):
        variant_parts = [variant] if variant else []
        mood_id = logical_char

        # Dynamic base names: current area outfit + current mood.
        dynamic = _character_dynamic(source_char, variant, mood_id)
        _register_image_if_missing(tuple([logical_char] + variant_parts), dynamic)

        # Compact variant alias: alex1 (kept for old scripts).
        if variant:
            _register_image_if_missing(
                (logical_char + variant,),
                _character_dynamic(source_char, variant, mood_id),
            )

        outfits = sorted({entry[0] for entry in entries if entry[0]})
        emotions = sorted({entry[1] for entry in entries if entry[1]})
        combinations = sorted({(entry[0], entry[1]) for entry in entries if entry[0] or entry[1]})

        # Explicit emotion keeps the current outfit automatic.
        for emotion in emotions:
            name = tuple([logical_char] + variant_parts + [emotion])
            _register_image_if_missing(
                name,
                _character_dynamic(
                    source_char,
                    variant,
                    mood_id,
                    forced_emotion=emotion,
                    auto_outfit=True,
                    auto_emotion=False,
                ),
            )

        # Explicit outfit keeps the current mood automatic.
        for outfit in outfits:
            name = tuple([logical_char] + variant_parts + [outfit])
            _register_image_if_missing(
                name,
                _character_dynamic(
                    source_char,
                    variant,
                    mood_id,
                    forced_outfit=outfit,
                    auto_outfit=False,
                    auto_emotion=True,
                ),
            )

        # Explicit outfit + expression forces both.
        for outfit, emotion in combinations:
            attrs = []
            if outfit:
                attrs.append(outfit)
            if emotion:
                attrs.append(emotion)
            if not attrs:
                continue
            name = tuple([logical_char] + variant_parts + attrs)
            _register_image_if_missing(
                name,
                _character_dynamic(
                    source_char,
                    variant,
                    mood_id,
                    forced_outfit=outfit,
                    forced_emotion=emotion,
                    auto_outfit=False,
                    auto_emotion=False,
                ),
            )


init 1 python:
    image_index = _build_image_index()

    # Character registrations.
    for _source_char, _variants in image_index["characters"].items():
        for _variant, _entries in _variants.items():
            # Internal/advanced long names.
            _compact = _source_char + _variant
            _register_image_if_missing(
                ("characters", _compact),
                _character_dynamic(_source_char, _variant, _source_char),
            )
            _register_image_if_missing(
                tuple(["characters", _source_char] + ([_variant] if _variant else [])),
                _character_dynamic(_source_char, _variant, _source_char),
            )

            _outfits = sorted({entry[0] for entry in _entries if entry[0]})
            _emotions = sorted({entry[1] for entry in _entries if entry[1]})
            _combinations = sorted({(entry[0], entry[1]) for entry in _entries if entry[0] or entry[1]})

            for _emotion in _emotions:
                _register_image_if_missing(
                    tuple(["characters", _source_char] + ([_variant] if _variant else []) + [_emotion]),
                    _character_dynamic(
                        _source_char,
                        _variant,
                        _source_char,
                        forced_emotion=_emotion,
                        auto_outfit=True,
                        auto_emotion=False,
                    ),
                )

            for _outfit in _outfits:
                _register_image_if_missing(
                    tuple(["characters", _source_char] + ([_variant] if _variant else []) + [_outfit]),
                    _character_dynamic(
                        _source_char,
                        _variant,
                        _source_char,
                        forced_outfit=_outfit,
                        auto_outfit=False,
                        auto_emotion=True,
                    ),
                )

            for _outfit, _emotion in _combinations:
                _attrs = []
                if _outfit:
                    _attrs.append(_outfit)
                if _emotion:
                    _attrs.append(_emotion)
                if _attrs:
                    _register_image_if_missing(
                        tuple(["characters", _source_char] + ([_variant] if _variant else []) + _attrs),
                        _character_dynamic(
                            _source_char,
                            _variant,
                            _source_char,
                            forced_outfit=_outfit,
                            forced_emotion=_emotion,
                            auto_outfit=False,
                            auto_emotion=False,
                        ),
                    )

            # Preferred short author-facing names, including aliases.
            for _logical_char in _logical_character_ids(_source_char):
                _register_character_names(_source_char, _logical_char, _variant, _entries)

    # Time-of-day folders.
    for _folder, _bases in image_index["tod"].items():
        for _base in _bases:
            _register_image_if_missing(
                (_folder, _base),
                DynamicDisplayable(_resolve_tod, _folder, _base),
            )

    # Plain image folders.
    for _folder, _bases in image_index["other"].items():
        for _base, _paths in _bases.items():
            _register_image_if_missing((_folder, _base), Image(_paths[0]))


init python:

    def list_character_variants(char):
        source = _character_source_id(char)
        return list(image_index.get("characters", {}).get(source, {}).keys())


    def has_character_image(char, variant=""):
        source = _character_source_id(char)
        return variant in image_index.get("characters", {}).get(source, {})


    def list_character_outfits(char):
        source = _character_source_id(char)
        outfits = set()
        for entries in image_index.get("characters", {}).get(source, {}).values():
            for outfit, _emotion, _path in entries:
                if outfit:
                    outfits.add(outfit)
        return sorted(outfits)


    def list_character_emotions(char):
        source = _character_source_id(char)
        emotions = set()
        for entries in image_index.get("characters", {}).get(source, {}).values():
            for _outfit, emotion, _path in entries:
                if emotion:
                    emotions.add(emotion)
        return sorted(emotions)


    def character_image_debug(char):
        """Returns locator data used by the developer diagnostics."""
        source = _character_source_id(char)
        variants = image_index.get("characters", {}).get(source, {})
        return {
            "character": char,
            "source": source,
            "variants": sorted(variants.keys()),
            "outfits": list_character_outfits(char),
            "emotions": list_character_emotions(char),
            "current_outfit": _current_outfit_for(char),
            "current_emotion": _current_emotion_for(char),
        }
