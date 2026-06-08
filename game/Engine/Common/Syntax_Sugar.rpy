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
    player = character_handle("player")

init python:

    def _stat_statement_parse(lex):
        rest = lex.rest()
        lex.expect_eol()
        return rest

    def _stat_statement_execute(rest):
        parts = rest.split()
        if len(parts) != 3:
            raise Exception("stat statement expects: stat <character> <stat> <amount>")
        char_id, stat_name, amount_text = parts
        try:
            amount = int(amount_text)
        except Exception:
            raise Exception("stat statement amount must be an integer, e.g. +1 or -1")
        stat(char_id, stat_name, amount)

    renpy.register_statement(
        "stat",
        parse=_stat_statement_parse,
        execute=_stat_statement_execute,
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
