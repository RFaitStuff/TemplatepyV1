# Area and location definitions.
# Registry helpers used here live in Engine/Location_System.rpy.

# =============================================================================
# AREA + LOCATION REGISTRY
# -----------------------------------------------------------------------------
# Edit the entries below to add/remove rooms.
# =============================================================================
init -2 python:

    # ---- AREAS ----
    register_area("school",   name="School",   outfit="school")
    register_area("outdoors", name="Outdoors", outfit=None)

    # ---- LOCATIONS ----
    # School
    register_location("homeroom",  name="Homeroom",  bg="classroom1",  area="school", variants={"alice": [""]})
    register_location("math_room", name="Math Room", bg="classroom2",  area="school", variants={"alice": ["", "1"]})
    register_location("art_room",  name="Art Room",  bg="classroom3",  area="school", variants={"alice": [""], "alex": [""]})
    register_location("hallway",   name="Hallway",   bg="smp_hallway", area="school", variants={"alice": [""]})
    register_location("roof",      name="Roof",      bg="smp_roof",    area="school", variants={"alice": [""], "alex": [""]})

    register_location("club_room", name="Club Room",  bg="smp_club1",   area="school", order_after="art_room", variants={"alice": [""], "alex": [""]})

    # Outdoors
    register_location("front",     name="School Front", bg="smp_front", area="outdoors", variants={"alice": [""], "alex": [""]})


