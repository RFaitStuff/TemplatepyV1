# =============================================================================
# Quest definitions
# =============================================================================
# Register every quest here. Story code should usually call set_flag(...) for
# checkpoints; the quest runtime auto-starts, progresses, and completes.
# =============================================================================

init 5 python:
    char_quest(
        "meet_alice",
        character="alice",
        title="Catch up with Alice",
        description="You haven't seen Alice all morning. Find her.",
        start_flag="quest_meet_alice",
        target={"npc": "alice"},
        objectives=[
            {
                "oid":    "find_her",
                "text":   "Locate Alice somewhere on campus",
                "flag":   "met_alice",
                "target": {"npc": "alice"},
            },
            {
                "oid":    "talk_to_her",
                "text":   "Have a real conversation with her",
                "flag":   "talked_alice",
                "target": {"npc": "alice", "action": "talk"},
            },
        ],
    )

    side_quest(
        "noticeboard_check",
        title="Read the Noticeboard",
        description="Someone said there was a flyer with your name on it.",
        start_flag="quest_noticeboard",
        target={
            "object": "noticeboard",
            "location": "front",
            "time_sensitive": True,
            "locks_time": True,
            "allowed_interactables": ["noticeboard"],
            "lock_message": "I should read the noticeboard before getting sidetracked.",
        },
        objectives=[
            {
                "oid": "read",
                "text": "Find the noticeboard out front",
                "flag": "read_noticeboard",
                "target": {"object": "noticeboard", "location": "front", "time_sensitive": True},
            },
        ],
    )

    define_quest(
        "found_pen",
        title="A Lost Pen",
        description="Someone dropped a pen in the hallway.",
        category="misc",
        start_flag="quest_found_pen",
        target={"item": "lost_pen", "location": "hallway"},
        objectives=[
            {
                "oid": "pickup",
                "text": "Pick up the pen",
                "flag": "got_pen",
                "target": {"item": "lost_pen", "location": "hallway"},
            },
        ],
    )


label _register_all_quests:
    return
