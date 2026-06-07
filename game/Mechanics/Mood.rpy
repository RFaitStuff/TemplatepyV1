# =============================================================================
# Mood System
# =============================================================================
# A character's "mood" is actually a bundle of overlapping emotions, each with
# its own intensity (0..mood_max_intensity). The dominant emotion is whichever
# has the highest weighted_intensity = intensity * priority_weight.
#
# Three knobs per emotion in MOOD_DEFS:
#   category        - "good" / "mix" / "bad" (purely informational, used by UI)
#   priority        - weight bias when picking the dominant emotion
#                     (e.g. "tired" 1.2 beats "happy" 1.0 at equal intensity)
#   affects_image   - True  = portraits swap to <char>_<emotion>
#                     False = state-only (e.g. "worried" doesn't change image)
#
# Setting an emotion also slightly lowers INCOMPATIBLE emotions so a character
# can't be deeply happy and deeply sad at the same time. Compatible-but-mixed
# emotions are allowed (e.g. sad + angry, sad + tired, happy + lustful).
#
# Emotions decay over time (every mood_decay_interval_hours) so characters
# gradually drift back to neutral if nothing reinforces the feeling.
#
# Quick API:
#   set_mood("alice", "happy")          # bump happy, lower its incompatibles
#   set_mood("alice", "happy", 7)       # explicit intensity
#   worsen_mood("alice", "sad", 2)      # add 2 to sad (e.g. talking irritated her)
#   add_mood("alice", "happy", -3)      # raw delta (clamped 0..max)
#   mood("alice")                       # dominant IMAGE-AFFECTING mood, or "neutral"
#   mood_state("alice")                 # dominant ANY emotion, image-affecting or not
#   mood_intensity("alice", "happy")    # specific intensity
#   all_moods("alice")                  # full {emotion: intensity} dict
# =============================================================================


# -----------------------------------------------------------------------------
# Tunable knobs
# -----------------------------------------------------------------------------
define mood_decay_interval_hours = 3   # auto-decay every N in-game hours
define mood_decay_amount         = 1   # intensity removed per decay tick
define mood_max_intensity        = 15
define mood_default_intensity    = 5   # fallback when set_mood() is called bare


# -----------------------------------------------------------------------------
# MOOD DEFINITIONS
# Add or remove emotions here - the rest of the system picks them up.
#   {emotion: (category, priority, affects_image)}
# -----------------------------------------------------------------------------
define MOOD_DEFS = {
    "happy":   ("mood", 1.0, True),
    "sad":     ("mood", 1.0, True),
    "angry":   ("mood", 1.0, True),
    "nervous": ("mood", 1.0, True),
}


# -----------------------------------------------------------------------------
# INCOMPATIBILITY MATRIX
#   Setting `key` LOWERS each listed emotion by the given amount.
#   1.0 = strong opposition, 0.5 = mild dampening.
#   Asymmetric is fine (e.g. happy crushes sad more than sad crushes happy).
# -----------------------------------------------------------------------------
define MOOD_INCOMPAT = {
    "happy": {"sad": 2, "angry": 1, "nervous": 1},
    "sad": {"happy": 2},
    "angry": {"happy": 1, "nervous": 1},
    "nervous": {"happy": 1, "angry": 1},
}


# Per-character hour counter for the auto-decay tick.
default _mood_hour_count = {}

# (char, mood_name) -> hours remaining before auto-clear. Set via mood(..., duration=N).
default _mood_expirations = {}


# =============================================================================
# Implementation
# =============================================================================
init python:

    # ---- internals -------------------------------------------------------
    def _ensure_mood_dict(char):
        try:
            d = ensure_character_state(char)
        except NameError:
            d = character_stats.setdefault(char, {})
            if not isinstance(d.get("moods"), dict):
                d["moods"] = {}
        return d["moods"]

    def _moods_of(char):
        try:
            return ensure_character_state(char).get("moods", {})
        except NameError:
            return character_stats.get(char, {}).get("moods", {})

    def _is_known_mood(name):
        return name in MOOD_DEFS

    def _affects_image(name):
        return _is_known_mood(name) and MOOD_DEFS[name][2]

    def _priority(name):
        return MOOD_DEFS[name][1] if _is_known_mood(name) else 1.0

    def _emit_mood_changed(char, mood_name, delta, new_value):
        try:
            emit("mood_changed", char, mood_name, delta, new_value)
        except NameError:
            pass

    def _can_apply_mood_with_cd(char, mood_name, cooldown):
        if cooldown is None:
            return True
        if not isinstance(cooldown, str):
            return True
        tok = cooldown.strip().lower()
        key = "mood:%s" % mood_name
        try:
            if tok in ("no", "noa"):
                return reward_once_ever(char, key)
            if tok.endswith("da"):
                tok = tok[:-1]
            if tok.endswith("d") and tok[:-1].isdigit():
                return reward_once(char, key, int(tok[:-1]))
        except NameError:
            return True
        return True

    # ---- queries ---------------------------------------------------------
    def all_moods(char):
        return dict(_moods_of(char))

    def mood_intensity(char, mood_name=None):
        moods = _moods_of(char)
        if mood_name is None:
            mood_name = mood_state(char)
        if mood_name == "neutral":
            return 0
        return moods.get(mood_name, 0)

    def mood_category(name):
        return MOOD_DEFS.get(name, ("none", 1.0, True))[0]

    def mood_state(char):
        """Dominant emotion (image-affecting or not). 'neutral' if none."""
        moods = {k: v for k, v in _moods_of(char).items() if v > 0}
        if not moods:
            return "neutral"
        # Highest weighted intensity wins. Ties: lexical for stability.
        return max(
            moods.items(),
            key=lambda kv: (kv[1] * _priority(kv[0]), kv[0]),
        )[0]

    def mood(char, mood_name=None, amount=None, duration=None, cooldown=None):
        """Unified mood API.

            mood("alice")                 -> dominant IMAGE-AFFECTING mood (or 'neutral')
            mood("alice", "happy")        -> SET happy at default intensity
            mood("alice", "happy", 2)     -> ADD 2 to happy intensity
            mood("alice", "sad", -1)      -> ADD -1 (relieve)
            mood("alice", "happy", duration=6)  -> auto-clear after 6 in-game hours
            mood("alice", "happy", 2, "3d")     -> add 2 with 3-day cooldown

        Pass mood_name=None or "neutral" to clear all moods on this character.
        """
        if mood_name is not None:
            if mood_name == "neutral":
                _ensure_mood_dict(char).clear()
                _clear_mood_expirations(char)
                return mood(char)
            if not _can_apply_mood_with_cd(char, mood_name, cooldown):
                return mood(char)
            if amount is None:
                set_mood(char, mood_name)
            else:
                add_mood(char, mood_name, amount)
            if duration is not None:
                _set_mood_expiration(char, mood_name, duration)
            return mood(char)

        moods = {k: v for k, v in _moods_of(char).items() if v > 0}
        if not moods:
            return "neutral"
        candidates = [(k, v) for k, v in moods.items() if _affects_image(k)]
        if not candidates:
            return "neutral"
        return max(
            candidates,
            key=lambda kv: (kv[1] * _priority(kv[0]), kv[0]),
        )[0]

    # ---- mutators --------------------------------------------------------
    def add_mood(char, mood_name, delta):
        """Adjust intensity of `mood_name` by `delta` (clamped to 0..max)."""
        if not mood_name or mood_name == "neutral":
            return
        if not _is_known_mood(mood_name):
            return
        moods = _ensure_mood_dict(char)
        cur = moods.get(mood_name, 0)
        new_val = max(0, min(mood_max_intensity, cur + delta))
        moods[mood_name] = new_val
        applied_delta = new_val - cur
        if applied_delta != 0:
            _emit_mood_changed(char, mood_name, applied_delta, new_val)

    def set_mood(char, mood_name, intensity=None):
        """Bump `mood_name` to AT LEAST `intensity`, then dampen incompatibles.

        - intensity=None uses mood_default_intensity.
        - mood_name=None or "neutral" clears all moods on this character.
        """
        if mood_name in (None, "neutral"):
            _ensure_mood_dict(char).clear()
            return
        if not _is_known_mood(mood_name):
            return
        if intensity is None:
            intensity = mood_default_intensity

        moods = _ensure_mood_dict(char)
        old = moods.get(mood_name, 0)
        moods[mood_name] = max(old, max(0, min(mood_max_intensity, intensity)))
        new_val = moods[mood_name]
        if new_val != old:
            _emit_mood_changed(char, mood_name, new_val - old, new_val)

        # Dampen incompatibles per the matrix.
        for k, drop in MOOD_INCOMPAT.get(mood_name, {}).items():
            if k in moods:
                moods[k] -= drop
                if moods[k] <= 0:
                    moods[k] = 0

    def worsen_mood(char, mood_name, amount=1):
        add_mood(char, mood_name, amount)

    def relieve_mood(char, mood_name, amount=1):
        add_mood(char, mood_name, -amount)

    def _set_mood_expiration(char, mood_name, duration_hours):
        if duration_hours is None or duration_hours <= 0:
            _mood_expirations.pop((char, mood_name), None)
            return
        _mood_expirations[(char, mood_name)] = int(duration_hours)

    def _clear_mood_expirations(char):
        for k in list(_mood_expirations.keys()):
            if k[0] == char:
                del _mood_expirations[k]

    def _tick_mood_expirations(hours):
        for k in list(_mood_expirations.keys()):
            remaining = _mood_expirations[k] - hours
            if remaining <= 0:
                char, name = k
                moods = _moods_of(char)
                if name in moods:
                    moods[name] = 0
                    _emit_mood_changed(char, name, -1, 0)
                del _mood_expirations[k]
            else:
                _mood_expirations[k] = remaining

    def decay_moods(char, amount=1):
        """Reduce every active mood on `char` by `amount`."""
        moods = _moods_of(char)
        for k in list(moods.keys()):
            moods[k] -= amount
            if moods[k] <= 0:
                moods[k] = 0

    # ---- auto decay ------------------------------------------------------
    def _decay_all_moods_tick(hours):
        for char in list(character_stats.keys()):
            n = _mood_hour_count.get(char, 0) + hours
            ticks, leftover = divmod(n, mood_decay_interval_hours)
            _mood_hour_count[char] = leftover
            if ticks > 0:
                decay_moods(char, ticks * mood_decay_amount)


init 5 python:
    on_hour_advance(_decay_all_moods_tick)
    on_hour_advance(_tick_mood_expirations)


# =============================================================================
# react() - one-line expression override
# -----------------------------------------------------------------------------
# Temporarily forces a portrait without touching mood state. Pair with the
# bare react(char) call to revert back to the mood-driven portrait.
#     $ react("alice", "embarrassed")
#     a "..."
#     $ react("alice")            # back to mood-driven
#
# Internally we just push an "override emotion" onto the character that the
# image locator checks BEFORE looking at mood. show_npc()/show automatically
# pick this up; nothing else to wire.
# =============================================================================

# char_id -> override emotion or None (cleared after each show_npc() call).
default _portrait_override = {}

init python:
    def react(char, expression=None):
        """Force `char`'s next portrait to <emotion>. Pass None to clear.
        Uses show_npc() so position/zoom/tag stay consistent with the rest
        of the framework - the character keeps the spot they're standing in.
        """
        if expression:
            _portrait_override[char] = expression
        else:
            _portrait_override.pop(char, None)
        # Re-show in place if she's already visible.
        try:
            # If we're in a dialogue and this char is in the cast, re-render
            # via the cast layout so her position/zoom in the conversation
            # stay correct. show_npc() uses the ROOM position, which would
            # yank her back to the wrong spot mid-dialogue.
            if char in getattr(store, "_dialogue_cast", {}):
                _layout_dialogue_cast(transition=False)
            elif renpy.showing(char, layer="master"):
                show_npc(char)
        except Exception:
            pass

    def _portrait_emotion_for(char):
        """Used by Image_Locater: react() override > image-affecting mood > none."""
        ovr = _portrait_override.get(char)
        if ovr:
            return ovr
        m = mood(char)
        return m if m and m != "neutral" else None
