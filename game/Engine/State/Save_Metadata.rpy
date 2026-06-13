# =============================================================================
# Save Metadata
# =============================================================================
# Adds readable project-specific metadata to Ren'Py save slots and provides a
# small compatibility gate for older/newer template saves.
# =============================================================================


define project_save_id = "project_tac"
define supported_save_version = "1.0"


init -20 python:

    def _version_tuple(value):
        parts = []
        for part in str(value or "0").replace("-", ".").split("."):
            try:
                parts.append(int(part))
            except Exception:
                digits = "".join(ch for ch in part if ch.isdigit())
                parts.append(int(digits or 0))
        return tuple(parts or [0])

    def save_metadata_summary():
        bits = []
        try:
            bits.append("Player: " + player_display_name())
        except Exception:
            pass
        try:
            loc = current_location
            if loc:
                bits.append("Location: " + location_name(loc))
        except Exception:
            pass
        try:
            if system_enabled("time"):
                bits.append("Day {}".format(globals().get("day", 1)))
        except Exception:
            pass
        try:
            tracked = globals().get("tracked_quest_id", None)
            if tracked:
                q = quest_log.get(tracked)
                if q:
                    bits.append("Tracking: " + q.title)
        except Exception:
            pass
        return " | ".join(bits)

    def add_project_save_json(json_data):
        try:
            json_data["project_save_id"] = project_save_id
            json_data["project_version"] = config.version
            json_data["supported_save_version"] = supported_save_version
            json_data["player_name"] = player_display_name()
            json_data["save_summary"] = save_metadata_summary()
            json_data["current_location"] = globals().get("current_location", None)
            json_data["tracked_quest"] = globals().get("tracked_quest_id", None)
        except Exception:
            pass

    def save_slot_status(slot):
        if not FileLoadable(slot):
            return "empty"
        slot_project = FileJson(slot, "project_save_id", None)
        if slot_project and slot_project != project_save_id:
            return "foreign"
        slot_version = FileJson(slot, "supported_save_version", None)
        if slot_version and _version_tuple(slot_version) > _version_tuple(supported_save_version):
            return "newer"
        return "valid"

    def save_slot_summary(slot):
        summary = FileJson(slot, "save_summary", "")
        if summary:
            return summary
        pieces = []
        player = FileJson(slot, "player_name", "")
        if player:
            pieces.append("Player: " + player)
        location = FileJson(slot, "current_location", "")
        if location:
            pieces.append("Location: " + str(location).replace("_", " ").title())
        return " | ".join(pieces)

    if add_project_save_json not in config.save_json_callbacks:
        config.save_json_callbacks.append(add_project_save_json)
