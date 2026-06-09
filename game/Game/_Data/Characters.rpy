# Character definitions and author-facing character data.
# Engine helpers used here live in Engine/Characters/Character_System.rpy.

init -20 python:
    CHARACTER_STAT_DEFS = {
        "love": {"label": "Love", "default": 0},
        "trust": {"label": "Trust", "default": 0},
        "respect": {"label": "Respect", "default": 0},
        "lust": {"label": "Lust", "default": 0},
    }

    MOOD_DEFS = {
        "happy":   ("mood", 1.0, True),
        "sad":     ("mood", 1.0, True),
        "angry":   ("mood", 1.0, True),
        "nervous": ("mood", 1.0, True),
    }

    MOOD_INCOMPAT = {
        "happy": {"sad": 2, "angry": 1, "nervous": 1},
        "sad": {"happy": 2},
        "angry": {"happy": 1, "nervous": 1},
        "nervous": {"happy": 1, "angry": 1},
    }

    REACTION_DEFS = {
        "embarrassed": {"default": False},
        "jealous": {"default": False},
        "shy": {"default": False},
        "confused": {"default": False},
        "confident": {"default": False},
    }

    STATUS_DEFS = {
        "tired": {"default": 0},
        "sick": {"default": 0},
        "hurt": {"default": 0},
    }

    PLAYER_STAT_DEFS = {
        "Coolness": {"default": 0},
        "Strength": {"default": 0},
        "Intelligence": {"default": 0},
        "Charisma": {"default": 0},
        "Agility": {"default": 0},
        "Lust": {"default": 0},
        "Love": {"default": 0},
    }

    def initial_character_state():
        state = {name: data.get("default", 0) for name, data in CHARACTER_STAT_DEFS.items()}
        state["moods"] = {name: 0 for name in MOOD_DEFS.keys()}
        state["reactions"] = {name: data.get("default", False) for name, data in REACTION_DEFS.items()}
        state["statuses"] = {name: data.get("default", 0) for name, data in STATUS_DEFS.items()}
        return state

    def initial_character_stats(character_ids):
        return {char_id: initial_character_state() for char_id in character_ids}

# Test twin Alex currently shares Alice's image set but has separate state.
default character_stats = initial_character_stats(("alice", "alex"))


default character_fact_defs = {
    "alice": [
        {"id": "favorite_place", "label": "Favorite Place", "text": "She likes quiet places above the school."},
        {"id": "hobby", "label": "Hobby", "text": "She sketches when nobody is watching."},
        {"id": "secret", "label": "Secret", "text": "She keeps a private notebook."},
    ],
    "alex": [
        {"id": "favorite_place", "label": "Favorite Place", "text": "She prefers busy rooms with easy exits."},
        {"id": "hobby", "label": "Hobby", "text": "She collects odd rumors."},
        {"id": "secret", "label": "Secret", "text": "She notices more than she admits."},
    ],
}
default unlocked_character_facts = {}


# Speakable Character() objects. Color is the name-text color in the say box.
define a  = tracked_character("Alice",  "alice",  color="#ff9ec7")  # pink
define a2 = tracked_character("Alex", "alex", color="#7fdf9c")  # green

define character_speakers = {
    "alice": a,
    "alex": a2,
}

