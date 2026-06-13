# =============================================================================
# Phone State
# =============================================================================
# Lightweight per-save phone content. The phone UI lives beside inventory, so
# extras like notes, messages, tutorials, contacts, and badges do not clutter HUD.
# =============================================================================


default phone_active_app = "stats"
default phone_notes = []
default phone_tutorials_seen = []
default phone_messages = []
default phone_contacts = {}
default phone_dialog_state = {}


init -15 python:
    phone_app_defs = {}
    phone_app_order = []


init python:

    def phone_app(app_id, label=None, requires=None, order=100, screen=None, icon=None, **extra):
        data = phone_app_defs.setdefault(app_id, {})
        data.update({
            "id": app_id,
            "label": label or str(app_id).replace("_", " ").title(),
            "requires": requires,
            "order": order,
            "screen": screen,
            "icon": icon,
        })
        data.update(extra)
        if app_id not in phone_app_order:
            phone_app_order.append(app_id)
        phone_app_order.sort(key=lambda key: phone_app_defs.get(key, {}).get("order", 100))
        return data

    def note_task(text, done=None, requires=None, **extra):
        entry = {"text": text, "done": done, "requires": requires}
        entry.update(extra)
        return entry

    def phone_note(note_id, title=None, body=None, rows=None, requires=None, **extra):
        entry = {
            "id": note_id,
            "title": title or note_id,
            "body": body or "",
            "rows": list(rows or []),
            "requires": requires,
        }
        entry.update(extra)
        for index, old in enumerate(phone_notes):
            if isinstance(old, dict) and old.get("id") == note_id:
                phone_notes[index] = entry
                return entry
        phone_notes.append(entry)
        return entry

    def phone_note_task_done(task):
        if not isinstance(task, dict):
            return False
        done = task.get("done")
        if done is None:
            return bool(task.get("complete", False))
        try:
            return meets_requirements(done)
        except Exception:
            return False

    def visible_phone_note_rows(note):
        rows = []
        for row in (note or {}).get("rows", []) or []:
            if not isinstance(row, dict):
                rows.append(row)
                continue
            requirement = row.get("requires")
            if requirement:
                try:
                    if not meets_requirements(requirement):
                        continue
                except Exception:
                    continue
            rows.append(row)
        return rows

    def phone_tutorial(tutorial_id, title=None, body=None, **extra):
        entry = {"id": tutorial_id, "title": title or tutorial_id, "body": body or ""}
        entry.update(extra)
        for index, old in enumerate(phone_tutorials_seen):
            if isinstance(old, dict) and old.get("id") == tutorial_id:
                phone_tutorials_seen[index] = entry
                return entry
        phone_tutorials_seen.append(entry)
        return entry

    def reset_phone_tutorials():
        phone_tutorials_seen[:] = []
        renpy.notify("Tutorials reset.")
        try:
            request_update_state("tutorials_reset")
        except Exception:
            pass
        return None

    def phone_contact(contact_id, name=None, avatar=None, requires=None, **extra):
        entry = {"id": contact_id, "name": name or contact_id, "avatar": avatar, "requires": requires}
        entry.update(extra)
        phone_contacts[contact_id] = entry
        return entry

    def phone_text(sender, body, contact=None, title=None, **extra):
        if title:
            display_title = title
        elif sender in globals().get("character_stats", {}):
            display_title = character_display_name(sender)
        else:
            display_title = str(sender).title()
        entry = {
            "sender": sender,
            "contact": contact or sender,
            "title": display_title,
            "body": body,
            "day": globals().get("day", 0),
            "time": globals().get("time", 0),
        }
        entry.update(extra)
        phone_messages.append(entry)
        try:
            request_update_state("phone_message", sender=sender, contact=entry.get("contact"))
        except Exception:
            pass
        return entry

    def dialog_mode(mode=None, contact=None, side="left", title=None, body=None, **extra):
        global phone_dialog_state
        if not mode:
            phone_dialog_state = {}
            return None
        data = {
            "mode": mode,
            "contact": contact,
            "side": side,
            "title": title,
            "body": body,
        }
        data.update(extra)
        phone_dialog_state = data
        renpy.show_screen("phone_dialog_overlay")
        return None

    def clear_dialog_mode():
        global phone_dialog_state
        phone_dialog_state = {}
        renpy.hide_screen("phone_dialog_overlay")
        return None

    def phone_visible_entries(entries):
        out = []
        for entry in entries or []:
            if not isinstance(entry, dict):
                out.append(entry)
                continue
            requirement = entry.get("requires")
            if requirement:
                try:
                    if not meets_requirements(requirement):
                        continue
                except Exception:
                    continue
            out.append(entry)
        return out

    def visible_phone_contacts():
        return phone_visible_entries(phone_contacts.values())


init 1 python:
    phone_app("stats", "Stats", order=10)
    phone_app("notes", "Notes", order=30)
    phone_app("messages", "Messages", order=40)
    phone_app("contacts", "Contacts", order=50)
    phone_app("tutorials", "Tutorials", order=60)
    phone_app("achievements", "Badges", order=70)
    phone_app("gallery", "Gallery", order=80, requires="system:gallery")
