# =============================================================================
# Label Progress Tracker
# =============================================================================
# Developer/debug support for broad completion snapshots.
# =============================================================================


default persistent.seen_labels = set()
default persistent.seen_label_counts = {}


init python:

    def label_progress_category(label):
        text = str(label or "")
        if text.startswith("quest_"):
            return "quest"
        if text.startswith("interact_") or "_interact" in text:
            return "interaction"
        if text in [scene.get("label") for scene in globals().get("gallery_scenes", []) or []]:
            return "gallery"
        if text.startswith("chapter") or text.startswith("story_"):
            return "story"
        return "other"

    def mark_label_seen(label, *args, **kwargs):
        try:
            if getattr(store, "_in_replay", None):
                return
        except Exception:
            pass
        if not label:
            return
        persistent.seen_labels.add(label)
        category = label_progress_category(label)
        counts = persistent.seen_label_counts
        counts[category] = counts.get(category, 0) + 1

    def label_progress_rows():
        buckets = {}
        for label in persistent.seen_labels:
            category = label_progress_category(label)
            buckets[category] = buckets.get(category, 0) + 1
        rows = []
        for category in ("story", "quest", "interaction", "gallery", "other"):
            rows.append({
                "id": category,
                "label": category.title(),
                "value": buckets.get(category, 0),
            })
        return rows

    def label_progress_summary():
        total = len(persistent.seen_labels)
        parts = ["{} {}".format(row["value"], row["label"].lower()) for row in label_progress_rows() if row["value"]]
        if not parts:
            return "No labels seen yet."
        return "{} labels seen: {}".format(total, ", ".join(parts))

    def completion_progress_rows():
        rows = []
        try:
            total_objectives = 0
            done_objectives = 0
            for q in quest_log.values():
                for objective in getattr(q, "objectives", []) or []:
                    total_objectives += 1
                    if getattr(objective, "done", False):
                        done_objectives += 1
            rows.append({"label": "Quest Objectives", "done": done_objectives, "total": total_objectives})
        except Exception:
            rows.append({"label": "Quest Objectives", "done": 0, "total": 0})

        try:
            total_gallery = len(gallery_scenes)
            done_gallery = len([scene for scene in gallery_scenes if is_gallery_unlocked(scene.get("id"))])
            rows.append({"label": "Gallery", "done": done_gallery, "total": total_gallery})
        except Exception:
            rows.append({"label": "Gallery", "done": 0, "total": 0})

        try:
            total_achievements = len(achievement_defs)
            done_achievements = len(getattr(persistent, "achievements", set()))
            rows.append({"label": "Achievements", "done": done_achievements, "total": total_achievements})
        except Exception:
            rows.append({"label": "Achievements", "done": 0, "total": 0})
        return rows


init 999 python:
    try:
        if mark_label_seen not in config.label_callbacks:
            config.label_callbacks.append(mark_label_seen)
    except Exception:
        pass
