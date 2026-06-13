# =============================================================================
# Player Identity
# =============================================================================
# Per-save protagonist identity. Writers can use `[player_display_name()]` in
# narration, and `p "Line"` for player dialogue.
# =============================================================================


default player_first_name = "Taylor"
default player_last_name = ""
default player_name_color = "#8fd7ff"
default player_setup_done = False


define p = Character("[player_display_name()]", color="#8fd7ff")


init -20 python:
    PLAYER_NAME_COLORS = [
        ("Sky", "#8fd7ff"),
        ("Rose", "#ff9ec7"),
        ("Gold", "#ffd27a"),
        ("Green", "#9be88f"),
        ("Violet", "#c7a3ff"),
        ("White", "#f5edf7"),
    ]


init python:

    def player_display_name():
        first = str(player_first_name or "Taylor").strip() or "Taylor"
        last = str(player_last_name or "").strip()
        if last:
            return "{} {}".format(first, last)
        return first

    def set_player_identity(first=None, last=None, color=None):
        global player_first_name, player_last_name, player_name_color, player_setup_done, p
        first = str(first or "").strip()
        last = str(last or "").strip()
        if not first:
            first = "Taylor"
        player_first_name = first
        player_last_name = last
        valid_colors = [value for label, value in PLAYER_NAME_COLORS]
        if color in valid_colors:
            player_name_color = color
        p = Character("[player_display_name()]", color=player_name_color)
        player_setup_done = True
        return None

    def reset_player_identity_setup():
        global player_setup_done
        player_setup_done = False
        return None
