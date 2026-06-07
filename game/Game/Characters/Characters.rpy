# Character definitions and author-facing character data.
# Engine helpers used here live in Engine/Character_System.rpy.

default character_stats = {
    "alice": {
        "love": 0,
        "trust":     0,
        "respect":   0,
        "lust":      0,
        "moods":     {"happy": 0, "sad": 0, "angry": 0, "nervous": 0},
        "reactions": {},
        "statuses":  {},
    },
    # Test twin - same stats and image set as Alice but separate state.
    "alex": {
        "love": 0,
        "trust":     0,
        "respect":   0,
        "lust":      0,
        "moods":     {"happy": 0, "sad": 0, "angry": 0, "nervous": 0},
        "reactions": {},
        "statuses":  {},
    },
}


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


# =============================================================================
# Per-character schedule
#   Maps character_id -> { time-of-day -> location_id }.
#   Time-of-day buckets come from get_time_of_day(time):
#       "day", "afternoon", "evening", "night", "midnight".
#   Use is_npc_here("alice") to test if they're in the player's room.
# =============================================================================
default character_schedules = {
    "alice": {
        "day":       "homeroom",   # 06-11
        "afternoon": "art_room",   # 12-17  (also where alex hangs out)
        "evening":   "club_room",  # 18-21  - meets alex in the club room
        "night":     "roof",       # 22-23
    },
    # alex follows a different orbit so you can test her separately - except
    # in the afternoon (Art Room) and evening (Club Room), where they overlap.
    "alex": {
        "day":       "front",
        "afternoon": "art_room",
        "evening":   "club_room",
        "night":     "roof",
    },
}


# Speakable Character() objects. Color is the name-text color in the say box.
define a  = tracked_character("Alice",  "alice",  color="#ff9ec7")  # pink
define a2 = tracked_character("Alex", "alex", color="#7fdf9c")  # green

define character_speakers = {
    "alice": a,
    "alex": a2,
}

