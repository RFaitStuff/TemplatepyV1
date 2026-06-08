# =============================================================================
# Alex Dialogue
# =============================================================================


init 10 python:
    register_character_talk("alex", "front_fact", kind="fact", line="I like the front steps. You can see everyone arriving before they see you.", locations="front", times="day")
    register_character_talk("alex", "shared_art_extra", kind="extra", label="alex_art_room_extra", locations="art_room", times="afternoon")
    register_character_talk("alex", "basic_same_face", kind="basic", line="Different person, same face. Try to keep up.")
    register_character_talk("alex", "basic_bored", kind="basic", line="If something interesting happens, wake me up.")
    register_character_interact("alex", "default", "alex_default_interact")

