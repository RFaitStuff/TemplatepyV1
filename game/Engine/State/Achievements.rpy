# =============================================================================
# Achievements And Milestones
# =============================================================================
# Optional progress layer. Achievements are persistent; milestones are a light
# authoring helper for things that may unlock achievements, gallery, or perks.
# =============================================================================


default persistent.milestones = set()


init -15 python:
    achievement_defs = {}
    milestone_defs = {}


init python:

    def achievement(achievement_id, title=None, desc=None, hidden=False, icon=None, requires=None, category="general", points=0, target=None, **extra):
        data = achievement_defs.setdefault(achievement_id, {})
        data.update({
            "id": achievement_id,
            "title": title or str(achievement_id).replace("_", " ").title(),
            "desc": desc or "",
            "hidden": bool(hidden),
            "icon": icon,
            "requires": requires,
            "category": category,
            "points": points,
            "target": target,
        })
        data.update(extra)
        return data

    def achievement_title(achievement_id):
        return achievement_defs.get(achievement_id, {}).get("title", str(achievement_id).replace("_", " ").title())

    def achievement_desc(achievement_id):
        return achievement_defs.get(achievement_id, {}).get("desc", "")

    def visible_achievement_rows():
        rows = []
        unlocked = set(getattr(persistent, "achievements", set()))
        known = set(achievement_defs.keys()) | unlocked
        for achievement_id in sorted(known):
            data = achievement_defs.get(achievement_id, {})
            is_unlocked = achievement_id in unlocked
            if data.get("hidden") and not is_unlocked:
                continue
            rows.append({
                "id": achievement_id,
                "title": data.get("title", achievement_title(achievement_id)) if is_unlocked else "???",
                "body": data.get("desc", "") if is_unlocked else "Hidden",
                "unlocked": is_unlocked,
                "icon": data.get("icon"),
                "category": data.get("category", "general"),
                "points": data.get("points", 0),
                "progress": achievement_progress(achievement_id),
                "target": data.get("target"),
            })
        return rows

    def achievement_progress(achievement_id):
        try:
            return int(persistent.achievement_progress.get(achievement_id, 0))
        except Exception:
            return 0

    def set_achievement_progress(achievement_id, value, target=None):
        try:
            value = int(value)
        except Exception:
            value = 0
        persistent.achievement_progress[achievement_id] = max(0, value)
        data = achievement_defs.get(achievement_id, {})
        goal = target if target is not None else data.get("target")
        if goal is not None and value >= int(goal):
            grant_achievement(achievement_id)
        try:
            request_update_state("achievement_progress", achievement=achievement_id, value=value)
        except Exception:
            pass
        return value

    def add_achievement_progress(achievement_id, amount=1, target=None):
        return set_achievement_progress(achievement_id, achievement_progress(achievement_id) + int(amount or 0), target=target)

    def milestone(milestone_id, achievement=None, gallery=None, requires=None, **extra):
        data = milestone_defs.setdefault(milestone_id, {})
        data.update({
            "id": milestone_id,
            "achievement": achievement,
            "gallery": gallery,
            "requires": requires,
        })
        data.update(extra)
        return data

    def mark_milestone(milestone_id):
        persistent.milestones.add(milestone_id)
        data = milestone_defs.get(milestone_id, {})
        achievement_id = data.get("achievement")
        if achievement_id:
            grant_achievement(achievement_id)
        gallery_id = data.get("gallery")
        if gallery_id:
            unlock_gallery(gallery_id)
        try:
            request_update_state("milestone", milestone=milestone_id)
        except Exception:
            pass
        return None

    def has_milestone(milestone_id):
        return milestone_id in persistent.milestones

    def achievements_validation_issues():
        issues = []
        for achievement_id, data in achievement_defs.items():
            if not data.get("title"):
                issues.append("Achievement '{}' has no title.".format(achievement_id))
            if data.get("requires"):
                try:
                    first_missing_requirement(data.get("requires"))
                except Exception:
                    issues.append("Achievement '{}' has an invalid requirement.".format(achievement_id))
            if data.get("target") is not None:
                try:
                    int(data.get("target"))
                except Exception:
                    issues.append("Achievement '{}' target is not a number.".format(achievement_id))

        for milestone_id, data in milestone_defs.items():
            achievement_id = data.get("achievement")
            if achievement_id and achievement_id not in achievement_defs:
                issues.append("Milestone '{}' references missing achievement '{}'.".format(milestone_id, achievement_id))
            gallery_id = data.get("gallery")
            if gallery_id:
                try:
                    if not gallery_scene(gallery_id):
                        issues.append("Milestone '{}' references missing gallery scene '{}'.".format(milestone_id, gallery_id))
                except Exception:
                    issues.append("Milestone '{}' could not validate gallery '{}'.".format(milestone_id, gallery_id))
            if data.get("requires"):
                try:
                    first_missing_requirement(data.get("requires"))
                except Exception:
                    issues.append("Milestone '{}' has an invalid requirement.".format(milestone_id))
        return issues


init 1 python:
    achievement("first_steps", "First Steps", "Started a new story.", category="story", points=5)
    achievement("archive_witness", "Archive Witness", "Completed a private archive scene.", hidden=True, category="character", points=10)
    milestone("started_story", achievement="first_steps")
    milestone("archive_witness_bree", achievement="archive_witness")
    milestone("archive_witness_cora", achievement="archive_witness")


init 999 python:
    try:
        register_project_tac_validator(achievements_validation_issues)
    except Exception:
        pass
