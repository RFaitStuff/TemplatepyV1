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
        "Coolness": {"default": 0, "label": "Coolness", "color": "#64d6ff", "min": 0, "max": 20, "aliases": ["cool"]},
        "Strength": {"default": 0, "label": "Strength", "color": "#ff8a8a", "min": 0, "max": 20},
        "Intelligence": {"default": 0, "label": "Intelligence", "color": "#b8a7ff", "min": 0, "max": 20, "aliases": ["brains"]},
        "Charisma": {"default": 0, "label": "Charisma", "color": "#ffd27a", "min": 0, "max": 20},
        "Agility": {"default": 0, "label": "Agility", "color": "#9ce8b2", "min": 0, "max": 20},
        "Lust": {"default": 0, "label": "Lust", "color": "#ff9ec7", "min": 0, "max": 20},
        "Love": {"default": 0, "label": "Love", "color": "#ff8de7", "min": 0, "max": 20},
    }

    perk("smooth_talker", stat="Coolness", requires="Coolness>=10", title="Smooth Talker", desc="Cool choices unlock more often.")
    perk("sharp_reader", stat="Intelligence", requires="Intelligence>=10", title="Sharp Reader", desc="Notice hidden context in investigations.")
    perk("warm_presence", stat="Charisma", requires="Charisma>=10", title="Warm Presence", desc="Some tense conversations soften.")

    def initial_character_state():
        state = {name: data.get("default", 0) for name, data in CHARACTER_STAT_DEFS.items()}
        state["moods"] = {name: 0 for name in MOOD_DEFS.keys()}
        state["reactions"] = {name: data.get("default", False) for name, data in REACTION_DEFS.items()}
        state["statuses"] = {name: data.get("default", 0) for name, data in STATUS_DEFS.items()}
        return state

    def initial_character_stats(character_ids):
        return {char_id: initial_character_state() for char_id in character_ids}

# Test characters Bree and Cora intentionally reuse Alice's image set through
# character_image_aliases in Engine/Images/Image_Locater.rpy.
default character_stats = initial_character_stats(("alice", "alex", "bree", "cora"))


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
    "bree": [
        {"id": "favorite_place", "label": "Favorite Place", "text": "She likes rooms with locked cabinets and bad lighting."},
        {"id": "hobby", "label": "Hobby", "text": "She builds tests for systems that claim they are finished."},
        {"id": "secret", "label": "Secret", "text": "She knows which school records were rewritten."},
    ],
    "cora": [
        {"id": "favorite_place", "label": "Favorite Place", "text": "She prefers stairwells because nobody looks up."},
        {"id": "hobby", "label": "Hobby", "text": "She annotates every rumor with a confidence score."},
        {"id": "secret", "label": "Secret", "text": "She can identify people by their footsteps."},
    ],
}
default unlocked_character_facts = {}


# Speakable Character() objects. Color is the name-text color in the say box.
define a  = tracked_character("Alice",  "alice",  color="#ff9ec7")  # pink
define a2 = tracked_character("Alex", "alex", color="#7fdf9c")  # green
define b  = tracked_character("Bree", "bree", color="#9ec7ff")
define c  = tracked_character("Cora", "cora", color="#ffd27a")

define character_speakers = {
    "alice": a,
    "alex": a2,
    "bree": b,
    "cora": c,
}

