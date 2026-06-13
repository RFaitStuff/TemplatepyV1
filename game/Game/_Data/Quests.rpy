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
        discoverable=True,
        guide_precision="characters",
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
        track_on_start="force",
        guide_precision="exact",
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

    create_quest(
        "found_pen",
        title="A Lost Pen",
        desc="Someone dropped a pen in the hallway.",
        category="misc",
        start_flag="quest_found_pen",
        discover=True,
        target={"item": "lost_pen", "location": "hallway"},
        steps=[
            step("pickup", "Pick up the pen", flag="got_pen", target={"item": "lost_pen", "location": "hallway"}),
        ],
    )

    char_quest(
        "alice_roof_scene",
        character="alice",
        title="A Quiet Signal",
        description="Alice keeps glancing toward the roof after the noticeboard changes.",
        unlock_when="flag:read_noticeboard",
        discoverable=True,
        guide_precision="characters",
        target={"npc": "alice", "location": "roof"},
        objectives=[
            step("roof_talk", "Talk with Alice on the roof", flag="alice_roof_signal_done", target={"npc": "alice", "location": "roof", "action": "interact", "label": "alice_roof_signal"}),
            step("trust_choice", "Choose how much to tell Alice", flag="alice_roof_signal_choice", target={"npc": "alice", "location": "roof"}),
        ],
    )

    char_quest(
        "alex_supply_run",
        character="alex",
        title="Borrowed Tools",
        description="Alex wants a small favor while you are already searching campus.",
        unlock_when="flag:read_noticeboard",
        discoverable=True,
        guide_precision="area",
        target={"npc": "alex", "location": "front"},
        objectives=[
            step("ask", "Ask Alex what she needs", flag="alex_supply_asked", target={"npc": "alex", "location": "front", "action": "interact", "label": "alex_supply_start"}),
            step("pen", "Bring Alex a pen from the hallway", flag="alex_supply_done", target={"item": "lost_pen", "location": "hallway"}),
        ],
    )

    side_quest(
        "archive_keyhunt",
        title="The Locked Archive",
        description="Bree says the noticeboard message points to a forgotten archive.",
        start_flag="complex_arc_available",
        discoverable=True,
        guide_precision="area",
        track_next="archive_evidence",
        target={"npc": "bree", "location": "hallway"},
        objectives=[
            {
                "oid": "briefing",
                "text": "Ask Bree about the noticeboard code",
                "flag": "bree_archive_briefed",
                "target": {
                    "npc": "bree",
                    "location": "hallway",
                    "action": "quest",
                    "label": "quest_bree_archive_briefing",
                    "time_sensitive": True,
                    "locks_time": True,
                    "locks_interact": True,
                    "allowed_interactables": ["bree"],
                    "lock_message": "Bree is waiting with the archive lead. I should talk to her first.",
                    "guide_precision": "location",
                },
            },
            {
                "oid": "key",
                "text": "Pick up the archive key in the hallway",
                "flag": "got_archive_key",
                "target": {"item": "archive_key", "location": "hallway"},
            },
            {
                "oid": "door",
                "text": "Unlock the Records Archive",
                "flag": "archive_room_unlocked",
                "target": {
                    "object": "archive_door",
                    "location": "hallway",
                    "label": "archive_door_unlock",
                },
            },
        ],
    )

    side_quest(
        "archive_evidence",
        title="Records Under Glass",
        description="Search the archive and choose what kind of evidence matters.",
        start_flag="archive_keyhunt_done",
        discoverable=True,
        guide_precision="location",
        track_next="bree_cora_confrontation",
        target={"location": "archive_room"},
        objectives=[
            {
                "oid": "enter",
                "text": "Enter the Records Archive",
                "flag": "entered_archive_room",
                "target": {"location": "archive_room"},
            },
            {
                "oid": "drive",
                "text": "Recover the sealed drive",
                "flag": "got_sealed_drive",
                "target": {"item": "sealed_drive", "location": "archive_room"},
            },
            {
                "oid": "badge",
                "text": "Inspect the glass badge",
                "flag": "glass_badge_checked",
                "target": {
                    "object": "glass_badge_case",
                    "location": "archive_room",
                    "label": "archive_badge_case",
                },
            },
            {
                "oid": "branch",
                "text": "Decide how to handle the evidence",
                "flag": "archive_evidence_decided",
                "target": {
                    "object": "archive_terminal",
                    "location": "archive_room",
                    "label": "archive_terminal_decode",
                },
            },
        ],
    )

    char_quest(
        "bree_cora_confrontation",
        character="bree",
        title="Two Versions of the Truth",
        description="Bree and Cora disagree about what the archive proves.",
        start_flag="archive_evidence_done",
        discoverable=True,
        guide_precision="characters",
        target={
            "characters": ["bree", "cora"],
            "location": "archive_room",
            "action": "quest",
            "label": "quest_cora_confrontation",
        },
        objectives=[
            {
                "oid": "bring_bree",
                "text": "Get Bree and Cora in the archive together",
                "flag": "bree_cora_met_archive",
                "target": {
                    "targets": [
                        guide_target("character:bree", location="archive_room", precision="characters"),
                        guide_target("character:cora", location="archive_room", precision="characters"),
                    ],
                    "location": "archive_room",
                    "action": "quest",
                    "label": "quest_cora_confrontation",
                },
            },
            {
                "oid": "choose_side",
                "text": "Choose which lead to follow",
                "flag": "bree_cora_side_chosen",
                "target": {
                    "npc": "bree",
                    "location": "archive_room",
                    "action": "quest",
                    "label": "quest_bree_cora_choice",
                },
            },
            {
                "oid": "report",
                "text": "Report the result at the noticeboard",
                "flag": "complex_arc_reported",
                "target": {
                    "object": "noticeboard",
                    "location": "front",
                    "label": "noticeboard_complex_report",
                },
            },
        ],
    )
