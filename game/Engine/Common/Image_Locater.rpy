# =============================================================================
# Auto Image Locator
# =============================================================================
# Filename grammar (per folder type):
#
#   characters/  ->  <Char><variant?>_<outfit?>_<emotion?>.<ext>
#                    Example files:
#                       Alice.png                  (bare)
#                       Alice_Happy.png            (emotion only)
#                       Alice1.png                 (alt pose / variant 1)
#                       Alice_School_Happy.png     (outfit + emotion)
#                       alex_School_Sad.png      (variant 2 + outfit + emotion)
#
#   bg/          ->  <base>_<tod><digit?><letter?>.<ext>      (time-of-day)
#                    Example: classroom1_day.webp, smp_roof_evening1.webp
#
#   anything else -> plain image register (no smart parsing)
#
# Use from script:
#   show characters alice           # auto: variant 0, current outfit, current mood
#   show characters alice1          # variant 1
#   show characters alex          # alias-mapped to alice via character_image_aliases
#
# Outfit comes from the player's current AREA (Locations/Areas registry).
# Emotion comes from react() override > image-affecting mood > none.
# =============================================================================


# Folders that should resolve time-of-day variants. Add more as needed.
define tod_folders = {"bg"}

# Folders that use the character grammar above (mood/outfit aware).
define character_folders = {"characters"}

# Image aliases: alias_id -> source_id. Reuse another character's images.
define character_image_aliases = {}


init -10 python:
    import os as _os
    import re as _re

    _IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")
    _TOD_ORDER = ["midnight", "night", "evening", "afternoon", "day", None]
    _TOD_RE = _re.compile(
        r"^(.+?)(?:_(midnight|night|evening|afternoon|day)\d*[a-z]*)?$",
        _re.IGNORECASE,
    )
    _CHAR_HEAD_RE = _re.compile(r"^([A-Za-z]+)(\d*)$")

    def get_time_of_day(t):
        if 6 <= t <= 11:  return "day"
        if 12 <= t <= 17: return "afternoon"
        if 18 <= t <= 21: return "evening"
        if 22 <= t <= 23: return "night"
        return "midnight"

    def _is_character_folder(folder_lc):
        return folder_lc in {f.lower() for f in character_folders}

    def _is_tod_folder(folder_lc):
        return folder_lc in {f.lower() for f in tod_folders}

    def _image_relative_parts(path):
        rel = asset_strip_root(path, asset_image_roots)
        parts = [p for p in rel.split("/") if p]
        if parts and parts[0].lower() == "images":
            parts = parts[1:]
        return parts

    # ---------------- character filename parsing ----------------
    def _parse_character_filename(name):
        """Alice1_School_Happy -> ('alice', '1', 'school', 'happy')
        Last underscore segment is treated as EMOTION if it matches a known
        emotion name (MOOD_DEFS keys + any registered extra), otherwise OUTFIT.
        """
        parts = name.split("_")
        head = parts[0]
        m = _CHAR_HEAD_RE.match(head)
        if not m:
            return None
        char = m.group(1).lower()
        variant = m.group(2) or ""
        rest = [p.lower() for p in parts[1:]]
        emotion = None
        outfit = None
        if rest:
            try:
                known_emotions = set(MOOD_DEFS.keys()) | set(extra_emotion_names)
            except NameError:
                known_emotions = set()
            if rest[-1] in known_emotions or len(rest) >= 2:
                # Treat last segment as emotion if it's recognized OR if there
                # are at least 2 segments (so something else can be the outfit).
                emotion = rest[-1]
                if len(rest) >= 2:
                    outfit = "_".join(rest[:-1])
            else:
                outfit = rest[-1]
        return (char, variant, outfit, emotion)

    # ---------------- bg / generic filename parsing ----------------
    def _parse_tod_filename(name):
        """smp_roof_evening1 -> ('smp_roof', 'evening')."""
        m = _TOD_RE.match(name)
        if not m:
            return (name.lower(), None)
        return (m.group(1).lower(), (m.group(2) or "").lower() or None)

    # ---------------- index builder ----------------
    def _build_image_index():
        """Returns:
            characters: {char: {variant: [(outfit, emotion, path), ...]}}
            tod:        {folder: {base: {tod: [paths]}}}
            other:      {folder: {base: [paths]}}
        """
        index = {"characters": {}, "tod": {}, "other": {}}
        for f in renpy.list_files():
            f_norm = asset_norm(f)
            if not f_norm.lower().endswith(_IMG_EXTS):
                continue
            if not asset_under(f_norm, asset_image_roots):
                continue
            path_parts = _image_relative_parts(f_norm)
            if len(path_parts) < 2:
                continue
            path_parts = path_parts[:-1]
            if not path_parts:
                continue
            folder_lc = path_parts[-1].lower()
            stem = _os.path.splitext(_image_relative_parts(f_norm)[-1])[0]

            if _is_character_folder(folder_lc):
                parsed = _parse_character_filename(stem)
                if not parsed:
                    continue
                char, variant, outfit, emotion = parsed
                d = index["characters"].setdefault(char, {})
                d.setdefault(variant, []).append((outfit, emotion, f_norm))
            elif _is_tod_folder(folder_lc):
                base, tod = _parse_tod_filename(stem)
                fdict = index["tod"].setdefault(folder_lc, {})
                fdict.setdefault(base, {}).setdefault(tod, []).append(f_norm)
            else:
                ofold = index["other"].setdefault(folder_lc, {})
                ofold.setdefault(stem.lower(), []).append(f_norm)
        # stable ordering
        for char_d in index["characters"].values():
            for entries in char_d.values():
                entries.sort(key=lambda t: (t[0] or "", t[1] or "", t[2]))
        for folder in index["tod"].values():
            for bases in folder.values():
                for tod, paths in bases.items():
                    paths.sort()
        for folder in index["other"].values():
            for paths in folder.values():
                paths.sort()
        return index


# Optional: extra emotion names (for filenames whose suffix isn't in MOOD_DEFS).
# E.g. "blush", "doubt", "teasing" - stylistic faces that can be requested by
# react("alice", "blush") or appear in filenames like Alice_Blush.png.
# Must be `define` (not `default`) - the locator reads it at init time.
define extra_emotion_names = {"blush", "doubt", "teasing", "neutral"}

# Per-character outfit override (set by show_npc/setup if you want to force
# a specific outfit irrespective of the area). Cleared by show_npc(..., outfit=None).
default character_outfit_override = {}


# =============================================================================
# Resolver
# =============================================================================
init -10 python:

    def _current_outfit_for(char):
        """Look up outfit from the current area, with optional per-char override.
        Pulls from `area_outfit_for(current_area())` if defined - otherwise None."""
        try:
            ovr = character_outfit_override.get(char)
            if ovr:
                return ovr.lower()
        except (NameError, AttributeError):
            pass
        try:
            return area_outfit(current_area_id()) or None
        except Exception:
            return None

    def _current_emotion_for(char):
        """react() override > image-affecting mood > None."""
        try:
            return _portrait_emotion_for(char)
        except NameError:
            return None

    def _score_entry(entry, want_outfit, want_emotion):
        """Higher score = better match. Negative penalty for unwanted specificity."""
        outfit, emotion, _path = entry
        score = 0
        if want_outfit and outfit == want_outfit:
            score += 4
        elif want_outfit and outfit:
            return -1   # wrong outfit on hand: skip entirely
        elif outfit and not want_outfit:
            score -= 1   # has outfit we don't want
        if want_emotion and emotion == want_emotion:
            score += 6
        elif want_emotion and emotion:
            return -1   # wrong emotion: skip
        elif emotion and not want_emotion:
            score -= 1
        return score

    def _resolve_character(st, at, char, variant, mood_id):
        """DynamicDisplayable callback for a character image."""
        idx = image_index.get("characters", {}).get(char, {})
        if not idx:
            return Null(), 0.0
        want_outfit  = _current_outfit_for(mood_id or char)
        want_emotion = _current_emotion_for(mood_id or char)

        # Variant fallback chain: requested variant -> "" (bare).
        for v in ([variant, ""] if variant else [""]):
            entries = idx.get(v)
            if not entries:
                continue
            scored = []
            for e in entries:
                s = _score_entry(e, want_outfit, want_emotion)
                if s >= 0:
                    scored.append((s, e))
            if not scored:
                continue
            scored.sort(key=lambda se: se[0], reverse=True)
            best = scored[0][1]
            return Image(best[2]), 0.0
        return Null(), 0.0

    def _resolve_character_forced(st, at, char, variant, outfit, emotion):
        """Resolve an explicit script image like `show alice happy`.

        Explicit images intentionally ignore the area's outfit and the
        character's current mood. This gives authors a clean override when
        they ask for a concrete expression in dialogue.
        """
        idx = image_index.get("characters", {}).get(char, {})
        if not idx:
            return Null(), 0.0
        entries = idx.get(variant or "")
        if not entries:
            return Null(), 0.0
        scored = []
        for e in entries:
            s = _score_entry(e, outfit, emotion)
            if s >= 0:
                scored.append((s, e))
        if not scored:
            return Null(), 0.0
        scored.sort(key=lambda se: se[0], reverse=True)
        return Image(scored[0][1][2]), 0.0

    def _resolve_tod(st, at, folder_lc, base):
        """DynamicDisplayable callback for a tod-aware bg image."""
        bases = image_index.get("tod", {}).get(folder_lc, {})
        entry = bases.get(base, {})
        if not entry:
            return Null(), 0.0
        try:
            current_time = time
        except NameError:
            current_time = 8
        tod = get_time_of_day(current_time)
        try:
            tod_start = _TOD_ORDER.index(tod)
        except ValueError:
            tod_start = 0
        for v in _TOD_ORDER[tod_start:]:
            paths = entry.get(v)
            if paths:
                return Image(paths[0]), 0.0
        return Null(), 0.0


# =============================================================================
# Image registration
# =============================================================================
init 1 python:
    image_index = _build_image_index()

    # Build alias reverse map.
    _aliases_by_source = {}
    for _alias_id, _src_id in character_image_aliases.items():
        _aliases_by_source.setdefault(_src_id, []).append(_alias_id)

    # ---- characters ----
    for _char, _variants in image_index["characters"].items():
        for _variant in _variants:
            _name = _char + _variant
            renpy.image(
                "characters " + _name,
                DynamicDisplayable(_resolve_character, _char, _variant, None),
            )
            if _variant:
                renpy.image(
                    "characters " + _char + " " + _variant,
                    DynamicDisplayable(_resolve_character, _char, _variant, None),
                )

            _emotions = sorted(
                set(_emotion for _outfit, _emotion, _path in _variants[_variant] if _emotion)
            )
            for _emotion in _emotions:
                renpy.image(
                    "characters " + _name + " " + _emotion,
                    DynamicDisplayable(_resolve_character_forced, _char, _variant, None, _emotion),
                )
                if _variant:
                    renpy.image(
                        "characters " + _char + " " + _variant + " " + _emotion,
                        DynamicDisplayable(_resolve_character_forced, _char, _variant, None, _emotion),
                    )

            # Aliases (e.g. alex -> alice).
            for _alias in _aliases_by_source.get(_char, []):
                renpy.image(
                    "characters " + _alias + _variant,
                    DynamicDisplayable(_resolve_character, _char, _variant, _alias),
                )
                if _variant:
                    renpy.image(
                        "characters " + _alias + " " + _variant,
                        DynamicDisplayable(_resolve_character, _char, _variant, _alias),
                    )

    # ---- tod folders (bg) ----
    for _folder, _bases in image_index["tod"].items():
        for _base in _bases:
            renpy.image(
                _folder + " " + _base,
                DynamicDisplayable(_resolve_tod, _folder, _base),
            )

    # ---- plain folders (Scenes, etc) ----
    for _folder, _bases in image_index["other"].items():
        for _base, _paths in _bases.items():
            renpy.image("%s %s" % (_folder, _base), Image(_paths[0]))


# =============================================================================
# Helpers exposed to script
# =============================================================================
init python:

    def list_character_variants(char):
        """Returns the list of variant suffixes available for `char` (e.g. ['', '1'])."""
        return list(image_index.get("characters", {}).get(char, {}).keys())

    def has_character_image(char, variant=""):
        return variant in image_index.get("characters", {}).get(char, {})

    def list_character_outfits(char):
        outs = set()
        for variant_entries in image_index.get("characters", {}).get(char, {}).values():
            for outfit, _e, _p in variant_entries:
                if outfit:
                    outs.add(outfit)
        return sorted(outs)
