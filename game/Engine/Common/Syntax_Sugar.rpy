# =============================================================================
# Authoring syntax sugar
# =============================================================================

init python:

    class CharacterStatProxy(object):
        def __init__(self, char_id, stat_name, cooldown=None):
            object.__setattr__(self, "char_id", char_id)
            object.__setattr__(self, "stat_name", stat_name)
            object.__setattr__(self, "cooldown", cooldown)

        def __call__(self, amount=None, *cooldowns, **kwargs):
            if amount is None:
                return char_stat(self.char_id, self.stat_name)
            effective = cooldowns or ((self.cooldown,) if self.cooldown else ())
            return stat(self.char_id, self.stat_name, amount, *effective, **kwargs)

        def __iadd__(self, amount):
            self(amount)
            return self

        def __isub__(self, amount):
            self(-amount)
            return self

        def __getattr__(self, name):
            if name == "no":
                return CharacterStatProxy(self.char_id, self.stat_name, "no")
            if name.startswith("d") and name[1:].isdigit():
                return CharacterStatProxy(self.char_id, self.stat_name, name[1:] + "d")
            raise AttributeError(name)

        def __setattr__(self, name, value):
            if isinstance(value, CharacterStatProxy):
                return
            object.__setattr__(self, name, value)

        def set(self, value):
            set_stat(self.char_id, self.stat_name, value)
            return value

        @property
        def value(self):
            return char_stat(self.char_id, self.stat_name)

        def __int__(self):
            return int(self.value)

        def __float__(self):
            return float(self.value)

        def __str__(self):
            return str(self.value)

    class CharacterMoodProxy(object):
        def __init__(self, char_id, mood_name, cooldown=None, duration=None):
            object.__setattr__(self, "char_id", char_id)
            object.__setattr__(self, "mood_name", mood_name)
            object.__setattr__(self, "cooldown", cooldown)
            object.__setattr__(self, "duration", duration)

        def __call__(self, amount=None, duration=None, cooldown=None):
            return mood(self.char_id, self.mood_name, amount, duration=duration if duration is not None else self.duration, cooldown=cooldown if cooldown is not None else self.cooldown)

        def __iadd__(self, amount):
            self(amount)
            return self

        def __isub__(self, amount):
            self(-amount)
            return self

        def set(self, intensity=None, duration=None, cooldown=None):
            return mood(self.char_id, self.mood_name, intensity, duration=duration, cooldown=cooldown)

        def for_hours(self, hours):
            return CharacterMoodProxy(self.char_id, self.mood_name, self.cooldown, hours)

        def __getattr__(self, name):
            if name.startswith("d") and name[1:].isdigit():
                return CharacterMoodProxy(self.char_id, self.mood_name, name[1:] + "d", self.duration)
            raise AttributeError(name)

        def __setattr__(self, name, value):
            if isinstance(value, CharacterMoodProxy):
                return
            object.__setattr__(self, name, value)

        @property
        def value(self):
            try:
                return character_stats.get(self.char_id, {}).get("moods", {}).get(self.mood_name, 0)
            except Exception:
                return 0

        def __int__(self):
            return int(self.value)

        def __float__(self):
            return float(self.value)

        def __str__(self):
            return str(self.value)

    class CharacterAuthorHandle(object):
        def __init__(self, char_id, speaker=None):
            object.__setattr__(self, "_char_id", char_id)
            object.__setattr__(self, "_speaker", speaker)
            object.__setattr__(self, "_stat_cache", {})
            object.__setattr__(self, "_mood_cache", {})

        def __call__(self, *args, **kwargs):
            speaker = object.__getattribute__(self, "_speaker")
            if speaker is None:
                raise Exception("No Character() object is bound to {}".format(object.__getattribute__(self, "_char_id")))
            return speaker(*args, **kwargs)

        def stat(self, *args, **kwargs):
            char_id = object.__getattribute__(self, "_char_id")
            cooldown = kwargs.pop("cooldown", kwargs.pop("cd", None))
            if kwargs:
                parts = []
                for key, value in kwargs.items():
                    parts.extend([key, value])
                if cooldown:
                    parts.append(cooldown)
                return stat(char_id, *parts)
            return stat(char_id, *args)

        stats = stat

        def mood(self, mood_name=None, amount=None, duration=None, cooldown=None):
            return mood(object.__getattribute__(self, "_char_id"), mood_name, amount, duration=duration, cooldown=cooldown)

        def __getattr__(self, name):
            speaker = object.__getattribute__(self, "_speaker")
            if speaker is not None and hasattr(speaker, name):
                return getattr(speaker, name)
            char_id = object.__getattribute__(self, "_char_id")
            if name in globals().get("MOOD_AXES", ()):
                cache = object.__getattribute__(self, "_mood_cache")
                if name not in cache:
                    cache[name] = CharacterMoodProxy(char_id, name)
                return cache[name]
            cache = object.__getattribute__(self, "_stat_cache")
            if name not in cache:
                cache[name] = CharacterStatProxy(char_id, name)
            return cache[name]

        def __setattr__(self, name, value):
            if name.startswith("_"):
                object.__setattr__(self, name, value)
                return
            if isinstance(value, (CharacterStatProxy, CharacterMoodProxy)):
                return
            char_id = object.__getattribute__(self, "_char_id")
            if name in globals().get("MOOD_AXES", ()):
                mood(char_id, name, value)
            else:
                set_stat(char_id, name, value)

    def character_handle(char_id, speaker=None):
        return CharacterAuthorHandle(char_id, speaker)

init 20 python:
    alice = character_handle("alice", character_speakers.get("alice"))
    alex = character_handle("alex", character_speakers.get("alex"))
    bree = character_handle("bree", character_speakers.get("bree"))
    cora = character_handle("cora", character_speakers.get("cora"))
    player = character_handle("player")

init python:

    def _stat_statement_parse(lex):
        rest = lex.rest()
        lex.expect_eol()
        return rest

    def _stat_statement_execute(rest):
        parts = rest.replace(",", " ").split()
        if len(parts) < 3:
            raise Exception("stat statement expects: stat <character> <stat> <amount> [cooldown]")
        char_id, stat_name, amount_text = parts[:3]
        cooldowns = parts[3:]
        char_id = _author_stat_character_id(char_id)
        stat_name = _author_stat_name(char_id, stat_name)
        try:
            amount = int(amount_text)
        except Exception:
            raise Exception("stat statement amount must be an integer, e.g. +1 or -1")
        stat(char_id, stat_name, amount, *cooldowns)

    def _author_norm_id(value):
        return str(value or "").strip().lower().replace(" ", "_")

    def _author_stat_character_id(value):
        raw = str(value or "").strip()
        norm = _author_norm_id(raw)
        if norm in ("mc", "player"):
            return "player"
        try:
            if norm in character_stats:
                return norm
            for cid in character_stats.keys():
                try:
                    if character_display_name(cid).lower() == raw.lower():
                        return cid
                except Exception:
                    pass
        except Exception:
            pass
        return norm

    def _author_stat_name(char_id, value):
        raw = str(value or "").strip()
        norm = _author_norm_id(raw)
        if char_id == "player":
            try:
                for key, data in PLAYER_STAT_DEFS.items():
                    if key.lower() == raw.lower():
                        return key
                    for alias in data.get("aliases", []) or []:
                        if str(alias).lower() == raw.lower():
                            return key
            except Exception:
                pass
            return raw[:1].upper() + raw[1:]
        try:
            for key in CHARACTER_STAT_DEFS.keys():
                if key.lower() == norm:
                    return key
        except Exception:
            pass
        return norm

    renpy.register_statement(
        "stat",
        parse=_stat_statement_parse,
        execute=_stat_statement_execute,
    )

    def _simple_rest_statement_parse(lex):
        rest = lex.rest().strip()
        lex.expect_eol()
        return rest

    def _flag_statement_execute(rest):
        flag_id = str(rest or "").strip()
        if not flag_id:
            raise Exception("flag statement expects: flag <flag_id>")
        set_flag(flag_id)

    def _unflag_statement_execute(rest):
        flag_id = str(rest or "").strip()
        if not flag_id:
            raise Exception("unflag statement expects: unflag <flag_id>")
        clear_flag(flag_id)

    def _item_statement_execute(rest):
        parts = str(rest or "").replace(",", " ").split()
        if not parts:
            raise Exception("item statement expects: item <item_id> [amount]")
        item_id = parts[0]
        amount = 1
        if len(parts) >= 2:
            try:
                amount = int(parts[1])
            except Exception:
                raise Exception("item statement amount must be an integer, e.g. +1 or -1")
        if amount >= 0:
            add_item(item_id, amount)
        else:
            remove_item(item_id, abs(amount))

    def _quest_statement_execute(rest):
        parts = str(rest or "").replace(",", " ").split()
        if not parts:
            raise Exception("quest statement expects: quest <start|discover|track|clear_track|progress|done|complete|fail> ...")
        verb = parts[0].lower()
        if verb in ("clear", "clear_track", "untrack", "off", "none"):
            clear_tracked_quest()
            return
        if len(parts) < 2:
            raise Exception("quest statement '{}' expects a quest id".format(verb))
        qid = parts[1]
        if verb == "start":
            start_quest(qid)
        elif verb in ("discover", "reveal"):
            discover_quest(qid, start=False, track=False)
        elif verb in ("track", "pin"):
            set_tracked_quest(qid)
        elif verb in ("progress", "step", "done"):
            if len(parts) < 3:
                raise Exception("quest {} expects: quest {} <quest_id> <objective_id>".format(verb, verb))
            progress_quest(qid, parts[2])
        elif verb in ("complete", "finish"):
            complete_quest(qid)
        elif verb == "fail":
            fail_quest(qid)
        else:
            raise Exception("Unknown quest statement action '{}'.".format(verb))

    renpy.register_statement(
        "flag",
        parse=_simple_rest_statement_parse,
        execute=_flag_statement_execute,
    )

    renpy.register_statement(
        "unflag",
        parse=_simple_rest_statement_parse,
        execute=_unflag_statement_execute,
    )

    renpy.register_statement(
        "item",
        parse=_simple_rest_statement_parse,
        execute=_item_statement_execute,
    )

    renpy.register_statement(
        "quest",
        parse=_simple_rest_statement_parse,
        execute=_quest_statement_execute,
    )

    def _author_bool(value):
        text = str(value).strip().lower()
        if text in ("1", "true", "yes", "y", "on"):
            return True
        if text in ("0", "false", "no", "n", "off"):
            return False
        return bool(value)

    def _author_float(value, default=None):
        try:
            return float(value)
        except Exception:
            return default

    def _author_show_pos(value):
        text = str(value or "").strip().lower()
        positions = {
            "left": (0.25, 1.0),
            "midleft": (0.33, 1.0),
            "mid_left": (0.33, 1.0),
            "middle": (0.5, 1.0),
            "center": (0.5, 1.0),
            "right": (0.75, 1.0),
            "midright": (0.66, 1.0),
            "mid_right": (0.66, 1.0),
        }
        return positions.get(text)

    def _author_parse_kwargs(text):
        kwargs = {}
        positional = []
        for raw in [part.strip() for part in str(text or "").replace(";", ",").split(",") if part.strip()]:
            if "=" in raw:
                key, value = raw.split("=", 1)
                kwargs[key.strip().lower()] = value.strip().strip("\"'")
            else:
                positional.extend(raw.split())
        return positional, kwargs

    def _show_statement_execute(rest):
        text = str(rest or "").strip()
        if not text:
            raise Exception("Show statement expects: Show <character>(side=Left)")

        args_text = ""
        if "(" in text and text.endswith(")"):
            char_text, args_text = text.split("(", 1)
            char_text = char_text.strip()
            args_text = args_text[:-1]
        else:
            parts = text.split(None, 1)
            char_text = parts[0]
            args_text = parts[1] if len(parts) > 1 else ""

        char_id = _author_stat_character_id(char_text)
        positional, kwargs = _author_parse_kwargs(args_text)

        if positional and "side" not in kwargs and "pos" not in kwargs:
            kwargs["side"] = positional.pop(0)
        if positional and "emotion" not in kwargs:
            kwargs["emotion"] = positional.pop(0)

        pos = None
        side = kwargs.get("side", kwargs.get("at", kwargs.get("position")))
        if side:
            pos = _author_show_pos(side)
        if "pos" in kwargs:
            coords = [p for p in kwargs["pos"].replace("|", " ").replace(":", " ").split() if p]
            if len(coords) >= 2:
                pos = (_author_float(coords[0], 0.5), _author_float(coords[1], 1.0))
        if ("x" in kwargs or "y" in kwargs) and pos is None:
            pos = (_author_float(kwargs.get("x"), 0.5), _author_float(kwargs.get("y"), 1.0))

        locked = kwargs.get("locked")
        if locked is None:
            locked = bool(pos is not None)
        else:
            locked = _author_bool(locked)

        zoom = _author_float(kwargs.get("zoom"), None) if "zoom" in kwargs else None
        show_npc(
            char_id,
            variant=kwargs.get("variant", kwargs.get("pose")),
            pos=pos,
            zoom=zoom,
            emotion=kwargs.get("emotion", kwargs.get("react", kwargs.get("expression"))),
            outfit=kwargs.get("outfit"),
            behind=kwargs.get("behind"),
            locked=locked,
        )

    def _hide_statement_execute(rest):
        char_id = _author_stat_character_id(str(rest or "").strip())
        if not char_id:
            raise Exception("Hide statement expects: Hide <character>")
        hide_npc(char_id)

    renpy.register_statement(
        "Show",
        parse=_simple_rest_statement_parse,
        execute=_show_statement_execute,
    )

    renpy.register_statement(
        "Hide",
        parse=_simple_rest_statement_parse,
        execute=_hide_statement_execute,
    )

    def _mood_statement_execute(rest):
        parts = str(rest or "").replace(",", " ").split()
        if len(parts) < 2:
            raise Exception("mood statement expects: mood <character> <mood> [amount] [duration=N]")
        char_id = _author_stat_character_id(parts[0])
        mood_name = parts[1].lower()
        amount = None
        duration = None
        cooldown = None
        for token in parts[2:]:
            if token.startswith("duration="):
                duration = int(token.split("=", 1)[1])
            elif token.startswith("for="):
                duration = int(token.split("=", 1)[1])
            elif token.endswith("d") or token in ("no", "noa"):
                cooldown = token
            else:
                amount = int(token)
        mood(char_id, mood_name, amount, duration=duration, cooldown=cooldown)

    def _react_statement_execute(rest):
        parts = str(rest or "").replace(",", " ").split()
        if not parts:
            raise Exception("react statement expects: react <character> [expression]")
        char_id = _author_stat_character_id(parts[0])
        expression = parts[1] if len(parts) >= 2 else None
        react(char_id, expression)

    def _milestone_statement_execute(rest):
        milestone_id = str(rest or "").strip()
        if not milestone_id:
            raise Exception("milestone statement expects: milestone <milestone_id>")
        mark_milestone(milestone_id)

    def _gallery_statement_execute(rest):
        gallery_id = str(rest or "").strip()
        if not gallery_id:
            raise Exception("gallery statement expects: gallery <gallery_id>")
        unlock_gallery(gallery_id)

    renpy.register_statement(
        "mood",
        parse=_simple_rest_statement_parse,
        execute=_mood_statement_execute,
    )

    renpy.register_statement(
        "react",
        parse=_simple_rest_statement_parse,
        execute=_react_statement_execute,
    )

    renpy.register_statement(
        "milestone",
        parse=_simple_rest_statement_parse,
        execute=_milestone_statement_execute,
    )

    renpy.register_statement(
        "gallery_unlock",
        parse=_simple_rest_statement_parse,
        execute=_gallery_statement_execute,
    )

    def _bgblur_statement_parse(lex):
        rest = lex.rest().strip()
        lex.expect_eol()
        return rest

    def _bgblur_statement_execute(rest):
        value = rest.lower()
        if value in ("false", "off", "0", "no"):
            BGBlur(False)
        elif value in ("true", "on", "1", "yes", ""):
            BGBlur(True)
        else:
            raise Exception("BGBlur statement expects true/false, on/off, yes/no, or 1/0")

    renpy.register_statement(
        "BGBlur",
        parse=_bgblur_statement_parse,
        execute=_bgblur_statement_execute,
    )
