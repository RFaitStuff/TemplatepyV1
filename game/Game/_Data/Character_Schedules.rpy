# =============================================================================
# Character schedules
# =============================================================================
# Maps character_id -> time bucket -> location_id.
#
# Time buckets come from get_time_of_day(time):
#   day, afternoon, evening, night, midnight
#
# Keep schedules separate from character setup because they are likely to grow
# conditional rules: weekdays, acts, routes, quests, overrides, and absence.
# =============================================================================

default character_schedules = {
    "alice": {
        "day":       "homeroom",
        "afternoon": "art_room",
        "evening":   "club_room",
        "night":     "roof",
    },
    "alex": {
        "day":       "front",
        "afternoon": "art_room",
        "evening":   "club_room",
        "night":     "roof",
    },
    "bree": {
        "day":       "hallway",
        "afternoon": "archive_room",
        "evening":   "club_room",
        "night":     "roof",
    },
    "cora": {
        "day":       "front",
        "afternoon": "archive_room",
        "evening":   "archive_room",
        "night":     "hallway",
    },
}
