# =============================================================================
# Alex Dialogue
# =============================================================================


init 10 python:
    register_character_talk("alex", "front_fact", kind="fact", line="I like the front steps. You can see everyone arriving before they see you.", locations="front", times="day")
    register_character_talk("alex", "shared_art_extra", kind="extra", label="alex_art_room_extra", locations="art_room", times="afternoon")
    register_character_talk("alex", "basic_same_face", kind="basic", line="Different person, same face. Try to keep up.")
    register_character_talk("alex", "basic_bored", kind="basic", line="If something interesting happens, wake me up.")
    register_character_interact("alex", "default", "alex_default_interact")
    register_character_interact("alex", "supply_start", "alex_supply_start", locations="front", requires="flag:read_noticeboard", group="alex_supply", once=True, completion_flag="alex_supply_asked", priority=20)
    register_character_interact("alex", "supply_finish", "alex_supply_finish", locations="front", requires="item:lost_pen", group="alex_supply", once=True, completion_flag="alex_supply_done", priority=25)
    register_character_interact("alex", "art_tools_scene", "alex_art_tools_scene", locations="art_room", group="alex_supply", special=True, completion_flag="alex_art_tools_scene_done", priority=100)

