# Project Tac extension for Ren'Py Live Studio.
# This file is optional project glue: it never changes Live Studio's base model.

init -845 python in live_studio:
    import os
    import re
    import shutil
    import time
    import renpy.store as store

    def pt_available():
        return hasattr(store, "project_save_id") and getattr(store, "project_save_id", None) == "project_tac"

    def pt_store_dict(name):
        value = getattr(store, name, {})
        return value if isinstance(value, dict) else {}

    def pt_store_list(name):
        value = getattr(store, name, [])
        return value if isinstance(value, (list, tuple, set)) else []

    def pt_game_dir():
        return os.path.abspath(getattr(store.config, "gamedir", "game"))

    def pt_abs_path(rel_path):
        rel_path = str(rel_path or "").replace("\\", "/").lstrip("/")
        root = pt_game_dir()
        path = os.path.abspath(os.path.join(root, rel_path))
        if os.path.commonpath([root, path]) != root:
            raise Exception("Refusing to access path outside game directory: {}".format(rel_path))
        return path

    def pt_read_file(rel_path, limit=18000):
        path = pt_abs_path(rel_path)
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        if limit and len(text) > limit:
            return text[:limit] + "\n\n# ... preview truncated ..."
        return text

    def pt_file_domain(rel_path):
        rel = str(rel_path).replace("\\", "/")
        if rel.startswith("Engine/"):
            return "Engine"
        if rel.startswith("Mechanics/"):
            return "Mechanics"
        if rel.startswith("Game/_Data/"):
            return "Data"
        if rel.startswith("Game/Content/"):
            return "Content"
        if rel in ("screens.rpy", "gui.rpy", "options.rpy", "script.rpy"):
            return "Root"
        if rel.startswith("DevTools/"):
            return "DevTools"
        return "Other"

    def pt_file_editable(rel_path):
        rel = str(rel_path).replace("\\", "/")
        return (
            rel.startswith("Game/_Data/") or
            rel.startswith("Game/Content/") or
            rel.startswith("Engine/UI/") or
            rel in ("screens.rpy", "gui.rpy", "options.rpy", "script.rpy")
        )

    def pt_file_rows():
        rows = []
        root = pt_game_dir()
        include_roots = ("Engine", "Mechanics", "Game", "DevTools")
        root_files = ("script.rpy", "screens.rpy", "options.rpy", "gui.rpy")
        current_location_file = pt_current_location_file(refresh=False)
        for filename in root_files:
            path = os.path.join(root, filename)
            if os.path.exists(path):
                rows.append({
                    "id": filename,
                    "path": filename,
                    "label": filename,
                    "domain": pt_file_domain(filename),
                    "editable": pt_file_editable(filename),
                    "recommended": filename == current_location_file,
                })
        for base in include_roots:
            base_path = os.path.join(root, base)
            if not os.path.isdir(base_path):
                continue
            for dirpath, dirnames, filenames in os.walk(base_path):
                dirnames[:] = [d for d in dirnames if d.lower() not in ("cache", "saves", "tl", "libs", "backup")]
                for filename in filenames:
                    if not filename.endswith(".rpy"):
                        continue
                    path = os.path.join(dirpath, filename)
                    rel = os.path.relpath(path, root).replace("\\", "/")
                    rows.append({
                        "id": rel,
                        "path": rel,
                        "label": (rel.split("/")[-1] + ("  [current]" if rel == current_location_file else "")),
                        "domain": pt_file_domain(rel),
                        "editable": pt_file_editable(rel),
                        "recommended": rel == current_location_file,
                    })
        rows.sort(key=lambda row: (0 if row.get("recommended") else 1, row.get("domain", ""), row.get("path", "")))
        return rows

    def pt_backup_file(rel_path):
        path = pt_abs_path(rel_path)
        if not os.path.exists(path):
            raise Exception("Cannot backup missing file: {}".format(rel_path))
        backup_dir = os.path.join(os.path.dirname(path), "Backup", "LiveStudio")
        if not os.path.isdir(backup_dir):
            os.makedirs(backup_dir)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = "{}__{}".format(stamp, os.path.basename(path))
        backup_path = os.path.join(backup_dir, backup_name)
        shutil.copy2(path, backup_path)
        return backup_path

    def pt_write_file(rel_path, text, allow_create=False):
        if not rel_path:
            raise Exception("Choose a target file first.")
        path = pt_abs_path(rel_path)
        exists = os.path.exists(path)
        if not exists and not allow_create:
            raise Exception("Target file does not exist: {}".format(rel_path))
        if not pt_file_editable(rel_path):
            raise Exception("This file is indexed for reference only. Choose a Data, Content, Engine/UI, or root UI file.")
        backup = None
        if exists:
            backup = pt_backup_file(rel_path)
        elif allow_create:
            parent = os.path.dirname(path)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(str(text))
        log_diagnostic("info", "Project Tac file written", {"file": rel_path, "backup": backup})
        if backup:
            return "Updated {}\nBackup: {}".format(rel_path, backup)
        return "Created {}".format(rel_path)

    def pt_append_to_file(rel_path, text):
        if not rel_path:
            raise Exception("Choose a target file first.")
        path = pt_abs_path(rel_path)
        if not os.path.exists(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        if not pt_file_editable(rel_path):
            raise Exception("This file is indexed for reference only. Choose a Data, Content, Engine/UI, or root UI file.")
        backup = pt_backup_file(rel_path)
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            old = handle.read()
        addition = "\n\n# --- Live Studio Project Tac Insert ---\n" + str(text).rstrip() + "\n"
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(old.rstrip() + addition)
        log_diagnostic("info", "Project Tac file updated", {"file": rel_path, "backup": backup})
        return "Updated {}\nBackup: {}".format(rel_path, backup)

    def pt_indent_text(text, spaces):
        prefix = " " * int(spaces or 0)
        rows = []
        for line in str(text).strip().splitlines():
            rows.append(prefix + line if line.strip() else "")
        return "\n".join(rows)

    def pt_insert_into_last_init_python(rel_path, text):
        if not rel_path:
            raise Exception("Choose a target file first.")
        path = pt_abs_path(rel_path)
        if not os.path.exists(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        if not pt_file_editable(rel_path):
            raise Exception("This file is reference-only.")
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        init_index = None
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("init") and stripped.endswith("python:"):
                init_index = index
        if init_index is None:
            raise Exception("No init python block found in {}".format(rel_path))
        init_indent = pt_line_indent(lines[init_index])
        block_end = len(lines)
        for index in range(init_index + 1, len(lines)):
            if lines[index].strip() and pt_line_indent(lines[index]) <= init_indent:
                block_end = index
                break
        body_indent = init_indent + 4
        insert_lines = ["", " " * body_indent + "# --- Live Studio Project Tac Insert ---"]
        insert_lines.extend(pt_indent_text(text, body_indent).splitlines())
        new_text = "\n".join(lines[:block_end] + insert_lines + lines[block_end:]).rstrip() + "\n"
        return pt_write_file(rel_path, new_text)

    def pt_insert_before_last_init_end(rel_path, text):
        return pt_insert_into_last_init_python(rel_path, text)

    def pt_find_matching_list_end(lines, start_index):
        depth = 0
        for index in range(start_index, len(lines)):
            text = lines[index]
            depth += text.count("[")
            depth -= text.count("]")
            if index > start_index and depth <= 0:
                return index
        return None

    def pt_insert_into_python_list(rel_path, list_name, item_text, fallback_before=None):
        path = pt_abs_path(rel_path)
        if not os.path.exists(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        if not pt_file_editable(rel_path):
            raise Exception("This file is reference-only.")
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()

        list_start = None
        pattern = re.compile(r"^\s*{}\s*=\s*\[".format(re.escape(list_name)))
        for index, line in enumerate(lines):
            if pattern.search(line):
                list_start = index
                break

        if list_start is not None:
            list_end = pt_find_matching_list_end(lines, list_start)
            if list_end is None:
                raise Exception("Could not find the end of {}=[] in {}".format(list_name, rel_path))
            list_indent = pt_line_indent(lines[list_start])
            item_indent = list_indent + 4
            insert_lines = [" " * item_indent + "# --- Live Studio Project Tac Insert ---"]
            insert_lines.extend(pt_indent_text(item_text, item_indent).splitlines())
            new_text = "\n".join(lines[:list_end] + insert_lines + lines[list_end:]).rstrip() + "\n"
            return pt_write_file(rel_path, new_text)

        if fallback_before:
            fallback_pattern = re.compile(r"^\s*{}\s*=\s*[\[\({{]".format(re.escape(fallback_before)))
            for index, line in enumerate(lines):
                if fallback_pattern.search(line):
                    list_indent = pt_line_indent(line)
                    item_indent = list_indent + 4
                    block = [
                        " " * list_indent + "{}=[".format(list_name),
                        " " * item_indent + "# --- Live Studio Project Tac Insert ---",
                    ]
                    block.extend(pt_indent_text(item_text, item_indent).splitlines())
                    block.append(" " * list_indent + "],")
                    new_text = "\n".join(lines[:index] + block + lines[index:]).rstrip() + "\n"
                    return pt_write_file(rel_path, new_text)

        raise Exception("Could not find {}=[] in {}".format(list_name, rel_path))

    def pt_replace_in_file(rel_path, old_text, new_text):
        if not rel_path:
            raise Exception("Choose a target file first.")
        path = pt_abs_path(rel_path)
        if not os.path.exists(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        if not pt_file_editable(rel_path):
            raise Exception("This file is reference-only.")
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            old = handle.read()
        if old_text not in old:
            raise Exception("Could not find the exact source block to replace.")
        backup = pt_backup_file(rel_path)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(old.replace(old_text, new_text, 1))
        log_diagnostic("info", "Project Tac source block replaced", {"file": rel_path, "backup": backup})
        return "Replaced source in {}\nBackup: {}".format(rel_path, backup)

    def pt_source_info_for_item(item=None):
        if item is None:
            item, _parent, kind = selected_item()
        else:
            kind = None
        if not item:
            return {}
        source = item.get("source") or {}
        screen_language = source.get("screen_language") or {}
        location = source.get("location") or screen_language.get("location")
        filename = ""
        line = 0
        if isinstance(location, (list, tuple)) and len(location) >= 2:
            filename = location[0]
            try:
                line = int(location[1])
            except Exception:
                line = 0
        elif isinstance(location, str):
            filename = location
        if not filename:
            filename = source.get("source") or source.get("filename") or screen_language.get("filename") or ""
        return {
            "item": item,
            "kind": kind,
            "source": source,
            "screen_language": screen_language,
            "filename": filename,
            "rel_path": pt_source_filename_to_rel(filename),
            "line": line,
        }

    def pt_line_indent(line):
        return len(line) - len(line.lstrip(" "))

    def pt_source_block(rel_path, line_number, before=2, max_lines=90):
        path = pt_abs_path(rel_path)
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        if not lines:
            return None
        index = max(0, int(line_number or 1) - 1)
        index = min(index, len(lines) - 1)
        start = max(0, index - int(before or 0))
        while start > 0 and not lines[start].strip():
            start += 1
            break
        base_indent = pt_line_indent(lines[index]) if lines[index].strip() else 0
        end = index + 1
        while end < len(lines) and end - start < max_lines:
            text = lines[end]
            if text.strip() and pt_line_indent(text) <= base_indent:
                break
            end += 1
        return {
            "start": start + 1,
            "end": end,
            "lines": lines[start:end],
            "base_indent": base_indent,
        }

    def pt_format_source_value(value):
        if isinstance(value, bool):
            return "True" if value else "False"
        if value is None:
            return "None"
        return repr(value)

    def pt_property_patch_lines(overrides, indent):
        allowed = (
            "properties.xpos", "properties.ypos", "properties.xalign", "properties.yalign",
            "properties.xoffset", "properties.yoffset", "properties.xanchor", "properties.yanchor",
            "properties.xsize", "properties.ysize", "properties.xfill", "properties.yfill",
            "properties.alpha", "properties.rotate", "properties.zoom", "properties.xzoom", "properties.yzoom",
            "properties.background", "properties.text", "properties.size", "properties.color", "properties.text_align",
        )
        rows = []
        for path, value in sorted((overrides or {}).items()):
            if path not in allowed:
                continue
            prop = path.split(".", 1)[1]
            rows.append("{}{} {}".format(" " * indent, prop, pt_format_source_value(value)))
        return rows

    def pt_patch_block_with_properties(block, patch_lines):
        if not block or not patch_lines:
            return None
        lines = list(block.get("lines") or [])
        if not lines:
            return None
        base_indent = block.get("base_indent", pt_line_indent(lines[0]))
        prop_indent = base_indent + 4
        prop_names = set(line.strip().split(" ", 1)[0] for line in patch_lines if line.strip())
        kept = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if index > 0 and stripped:
                name = stripped.split(" ", 1)[0]
                if pt_line_indent(line) == prop_indent and name in prop_names:
                    continue
            kept.append(line)
        insert_at = 1
        while insert_at < len(kept) and not kept[insert_at].strip():
            insert_at += 1
        return kept[:insert_at] + patch_lines + kept[insert_at:]

    def pt_selected_source_block_preview():
        item, _parent, kind = selected_item()
        info = pt_source_info_for_item(item)
        rel = info.get("rel_path")
        line = info.get("line")
        if not rel or not line:
            return "# Selected item has no recoverable source file/line."
        block = pt_source_block(rel, line)
        if not block:
            return "# Could not load source block."
        numbered = []
        current = block["start"]
        for text in block["lines"]:
            numbered.append("{:04d}: {}".format(current, text))
            current += 1
        return "\n".join([
            "# Source block for selected {}".format(kind or "item"),
            "# File: {}".format(rel),
            "# Lines: {}-{}".format(block["start"], block["end"]),
            "",
        ] + numbered)

    def pt_selected_property_patch_preview():
        item, _parent, kind = selected_item()
        if not item:
            return "# Select a source-backed UI item first."
        info = pt_source_info_for_item(item)
        rel = info.get("rel_path")
        line = info.get("line")
        if not rel or not line:
            return "# Selected item has no recoverable source file/line."
        frame = current_frame() or {}
        overrides = frame.get("changes", {}).get("sets", {}).get(item.get("id"), {}) or {}
        block = pt_source_block(rel, line)
        if not block:
            return "# Could not load source block."
        patch_lines = pt_property_patch_lines(overrides, block.get("base_indent", 0) + 4)
        if not patch_lines:
            return "# No supported local property overrides to write. Move/resize/edit the selected widget first."
        new_lines = pt_patch_block_with_properties(block, patch_lines)
        return "\n".join([
            "# Property patch preview",
            "# File: {}".format(rel),
            "# Lines: {}-{}".format(block["start"], block["end"]),
            "# This replaces/updates supported property lines under the selected widget.",
            "",
            "\n".join(new_lines),
        ])

    def pt_apply_selected_property_patch():
        item, _parent, _kind = selected_item()
        if not item:
            return "# Select a source-backed UI item first."
        info = pt_source_info_for_item(item)
        rel = info.get("rel_path")
        line = info.get("line")
        if not rel or not line:
            return "# Selected item has no recoverable source file/line."
        frame = current_frame() or {}
        overrides = frame.get("changes", {}).get("sets", {}).get(item.get("id"), {}) or {}
        block = pt_source_block(rel, line)
        if not block:
            return "# Could not load source block."
        patch_lines = pt_property_patch_lines(overrides, block.get("base_indent", 0) + 4)
        if not patch_lines:
            return "# No supported local property overrides to write."
        new_lines = pt_patch_block_with_properties(block, patch_lines)
        old_text = "\n".join(block["lines"])
        new_text = "\n".join(new_lines)
        return pt_replace_in_file(rel, old_text, new_text)

    def pt_current_location_id():
        return str(getattr(store, "current_location", "") or "")

    def pt_current_location_file(refresh=True):
        loc_id = pt_current_location_id()
        if not loc_id:
            return ""
        index = runtime.get("project_tac_index", {}) if not refresh else pt_index()
        location_files = index.get("location_files", {}) if isinstance(index, dict) else {}
        return location_files.get(loc_id, "")

    def pt_select_current_location_file():
        rel = pt_current_location_file(refresh=True)
        loc_id = pt_current_location_id()
        if not rel:
            return "No Project Tac source file is mapped for current_location={!r}.".format(loc_id)
        set_selected_extension_file("project_tac", rel)
        set_extension_preview("Current Location Source", pt_file_preview(rel))
        return "Selected current location source:\n{} -> {}".format(loc_id, rel)

    def pt_select_project_file(rel_path):
        if not rel_path:
            return "No file selected."
        set_selected_extension_file("project_tac", rel_path)
        set_extension_preview("Project Source", pt_file_preview(rel_path))
        return "Selected Project Tac source:\n{}".format(rel_path)

    def pt_registry_source_report():
        index = pt_index()
        source_maps = index.get("source_maps", {}) or {}
        rows = [
            "# Project Tac registry sources",
            "",
            "These are direct source locations Studio can inspect before generating or rewriting code.",
            "",
        ]
        if not source_maps:
            rows.append("No registry source maps are available. Refresh the Project Tac index.")
            return "\n".join(rows)
        for kind in sorted(source_maps.keys()):
            entries = source_maps.get(kind) or {}
            if not entries:
                continue
            rows.append("## {}".format(kind.replace("_", " ").title()))
            for item_id, meta in sorted(entries.items()):
                rows.append("- {} -> {}:{}".format(item_id, meta.get("file", ""), meta.get("line", "")))
            rows.append("")
        return "\n".join(rows).rstrip()

    def pt_label_source_report():
        index = pt_index()
        labels = index.get("label_sources", {}) or {}
        rows = [
            "# Project Tac content labels",
            "",
            "Story, dialogue, and interaction labels found under Game/Content.",
            "",
        ]
        if not labels:
            rows.append("No content labels are mapped. Refresh the Project Tac index.")
            return "\n".join(rows)
        grouped = {}
        for label_id, meta in labels.items():
            grouped.setdefault(meta.get("kind", "content"), []).append((label_id, meta))
        for kind in sorted(grouped.keys()):
            rows.append("## {}".format(kind.replace("_", " ").title()))
            for label_id, meta in sorted(grouped[kind]):
                rows.append("- {} -> {}:{}".format(label_id, meta.get("file", ""), meta.get("line", "")))
            rows.append("")
        return "\n".join(rows).rstrip()

    def pt_file_coverage_report():
        rows = [
            "# Project Tac file coverage",
            "",
            "Every indexed .rpy file can be previewed from the Project Tac tab. Editable files can also receive backed-up writes.",
            "",
        ]
        grouped = {}
        editable = 0
        for row in pt_file_rows():
            domain = row.get("domain", "Other")
            grouped.setdefault(domain, []).append(row)
            if row.get("editable"):
                editable += 1
        rows.append("Indexed files: {}".format(sum(len(v) for v in grouped.values())))
        rows.append("Writable files: {}".format(editable))
        rows.append("")
        for domain in sorted(grouped.keys()):
            rows.append("## {}".format(domain))
            for row in grouped[domain]:
                marker = "write" if row.get("editable") else "read"
                recommended = " current" if row.get("recommended") else ""
                rows.append("- [{}{}] {}".format(marker, recommended, row.get("path", row.get("id", ""))))
            rows.append("")
        return "\n".join(rows).rstrip()

    def pt_ui_source_report():
        index = pt_index()
        ui_maps = index.get("ui_sources", {}) or {}
        rows = [
            "# Project Tac UI sources",
            "",
            "Screens, styles, transforms, image declarations, GUI defines, and defaults mapped from root UI files and Engine/UI.",
            "",
        ]
        if not ui_maps:
            rows.append("No UI source maps are available. Refresh the Project Tac index.")
            return "\n".join(rows)
        for kind in sorted(ui_maps.keys()):
            entries = ui_maps.get(kind) or {}
            if not entries:
                continue
            rows.append("## {}".format(kind.replace("_", " ").title()))
            for item_id, meta in sorted(entries.items()):
                rows.append("- {} -> {}:{}".format(item_id, meta.get("file", ""), meta.get("line", "")))
            rows.append("")
        return "\n".join(rows).rstrip()

    def pt_engine_api_report():
        index = pt_index()
        api_maps = index.get("api_sources", {}) or {}
        rows = [
            "# Project Tac Engine and Mechanics APIs",
            "",
            "Callable helpers, classes, screens, labels, defaults, defines, and transforms mapped from Engine/ and Mechanics/.",
            "",
        ]
        if not api_maps:
            rows.append("No Engine/Mechanics API map is available. Refresh the Project Tac index.")
            return "\n".join(rows)
        for domain in ("engine", "mechanics"):
            groups = api_maps.get(domain, {}) or {}
            if not groups:
                continue
            rows.append("## {}".format(domain.title()))
            for kind in sorted(groups.keys()):
                entries = groups.get(kind) or {}
                if not entries:
                    continue
                rows.append("### {}".format(kind.replace("_", " ").title()))
                for item_id, meta in sorted(entries.items()):
                    rows.append("- {} -> {}:{}".format(item_id, meta.get("file", ""), meta.get("line", "")))
                rows.append("")
        return "\n".join(rows).rstrip()

    def pt_select_data_file(kind):
        targets = {
            "characters": "Game/_Data/Characters.rpy",
            "schedules": "Game/_Data/Character_Schedules.rpy",
            "locations": "Game/_Data/Areas_Locations.rpy",
            "items": "Game/_Data/Items.rpy",
            "quests": "Game/_Data/Quests.rpy",
        }
        rel = targets.get(kind)
        if not rel:
            return "Unknown data file kind: {}".format(kind)
        return pt_select_project_file(rel)

    def pt_select_ui_file(kind):
        targets = {
            "screens": "screens.rpy",
            "gui": "gui.rpy",
            "project_ui": "Engine/UI/Screens.rpy",
            "hud": "Engine/UI/HUD.rpy",
            "locations": "Engine/UI/Locations.rpy",
            "choice": "Engine/UI/Choice.rpy",
        }
        rel = targets.get(kind)
        if not rel:
            return "Unknown UI file kind: {}".format(kind)
        return pt_select_project_file(rel)

    def pt_select_engine_file(kind):
        targets = {
            "location_engine": "Engine/World/Location_System.rpy",
            "location_package": "Engine/World/Location_Package.rpy",
            "interactables": "Engine/World/Interactables.rpy",
            "dialogue": "Engine/Dialogue/Dialogue_Handler.rpy",
            "image_locator": "Engine/Images/Image_Locater.rpy",
            "characters": "Engine/Characters/Character_System.rpy",
            "gallery": "Engine/Gallery.rpy",
            "requirements": "Engine/Common/Requirements.rpy",
            "story_flags": "Engine/State/Story_Flags.rpy",
        }
        rel = targets.get(kind)
        if not rel:
            return "Unknown engine file kind: {}".format(kind)
        return pt_select_project_file(rel)

    def pt_select_mechanic_file(kind):
        targets = {
            "quest_runtime": "Mechanics/Quest/Quest_Runtime.rpy",
            "quest_guide": "Mechanics/Quest/Quest_Guide.rpy",
            "inventory": "Mechanics/Inventory/Inventory.rpy",
            "time_stamina": "Mechanics/Time_Stamina.rpy",
            "mood": "Mechanics/Mood.rpy",
            "minigames": "Mechanics/Minigames.rpy",
        }
        rel = targets.get(kind)
        if not rel:
            return "Unknown mechanic file kind: {}".format(kind)
        return pt_select_project_file(rel)

    def pt_refresh_index():
        location_files = pt_location_file_map()
        source_maps = pt_registry_source_maps()
        label_sources = pt_content_label_sources()
        ui_sources = pt_ui_source_maps()
        api_sources = pt_engine_api_source_maps()
        index = {
            "locations": sorted(pt_store_dict("locations").keys()),
            "location_files": location_files,
            "source_maps": source_maps,
            "label_sources": label_sources,
            "ui_sources": ui_sources,
            "api_sources": api_sources,
            "quests": sorted(pt_store_dict("quest_defs").keys()),
            "items": sorted(pt_store_dict("item_defs").keys()),
            "characters": sorted(pt_store_dict("character_stats").keys()),
            "branches": sorted(pt_store_dict("branch_defs").keys()),
            "systems": sorted(getattr(store, "SYSTEM_DEFAULTS", {}).keys()) if hasattr(store, "SYSTEM_DEFAULTS") else [],
            "text_tags": sorted(getattr(store.config, "custom_text_tags", {}).keys()),
            "image_aliases": dict(getattr(store, "character_image_aliases", {}) or {}),
            "files": pt_file_rows(),
        }
        runtime["project_tac_index"] = index
        log_diagnostic("info", "Project Tac index refreshed", {
            "locations": len(index["locations"]),
            "quests": len(index["quests"]),
            "items": len(index["items"]),
            "characters": len(index["characters"]),
            "location_files": len(location_files),
            "source_maps": sum(len(items) for items in source_maps.values()),
            "labels": len(label_sources),
            "ui_sources": sum(len(items) for items in ui_sources.values()),
            "api_sources": sum(len(items) for groups in api_sources.values() for items in groups.values()),
            "files": len(index["files"]),
        })
        restart()
        return None

    def pt_index():
        if "project_tac_index" not in runtime:
            pt_refresh_index()
        return runtime.get("project_tac_index", {})

    def pt_summary_rows():
        index = pt_index()
        rows = [
            {"label": "Current Location", "value": pt_current_location_id() or "unknown"},
            {"label": "Locations", "value": len(index.get("locations", []))},
            {"label": "Quests", "value": len(index.get("quests", []))},
            {"label": "Items", "value": len(index.get("items", []))},
            {"label": "Characters", "value": len(index.get("characters", []))},
            {"label": "Branches", "value": len(index.get("branches", []))},
            {"label": "Systems", "value": ", ".join(index.get("systems", [])[:8])},
            {"label": "Text Tags", "value": ", ".join(index.get("text_tags", [])[:12])},
            {"label": "Indexed Files", "value": len(index.get("files", []))},
        ]
        aliases = index.get("image_aliases", {})
        if aliases:
            rows.append({"label": "Image Aliases", "value": ", ".join("{}->{}".format(k, v) for k, v in sorted(aliases.items()))})
        location_files = index.get("location_files", {})
        if location_files:
            rows.append({"label": "Location Sources", "value": "{} mapped".format(len(location_files))})
        source_maps = index.get("source_maps", {})
        if source_maps:
            rows.append({"label": "Registry Sources", "value": ", ".join("{}:{}".format(k, len(v)) for k, v in sorted(source_maps.items()) if v)})
        label_sources = index.get("label_sources", {})
        if label_sources:
            by_kind = {}
            for meta in label_sources.values():
                kind = meta.get("kind", "content")
                by_kind[kind] = by_kind.get(kind, 0) + 1
            rows.append({"label": "Content Labels", "value": ", ".join("{}:{}".format(k, by_kind[k]) for k in sorted(by_kind))})
        ui_sources = index.get("ui_sources", {})
        if ui_sources:
            rows.append({"label": "UI Sources", "value": ", ".join("{}:{}".format(k, len(v)) for k, v in sorted(ui_sources.items()) if v)})
        api_sources = index.get("api_sources", {})
        if api_sources:
            rows.append({"label": "Engine APIs", "value": ", ".join("{}:{}".format(domain, sum(len(v) for v in groups.values())) for domain, groups in sorted(api_sources.items()) if groups)})
        current_file = pt_current_location_file(refresh=False)
        if current_file:
            rows.append({"label": "Current Source", "value": current_file})
        return rows

    def pt_file_preview(rel_path):
        return pt_read_file(rel_path)

    def pt_location_file_map():
        out = {}
        for row in pt_file_rows():
            rel = row.get("path")
            if not rel or not str(rel).replace("\\", "/").startswith("Game/Content/Interactions/"):
                continue
            try:
                text = pt_read_file(rel, limit=None)
            except Exception:
                continue
            for match in re.finditer(r"location_package\s*\(\s*id\s*=\s*[\"']([^\"']+)[\"']", text):
                out[match.group(1)] = rel
        return out

    def pt_scan_call_sources(patterns, file_prefixes=None):
        out = {}
        for row in pt_file_rows():
            rel = row.get("path")
            if not rel:
                continue
            rel = str(rel).replace("\\", "/")
            if file_prefixes and not any(rel.startswith(prefix) for prefix in file_prefixes):
                continue
            try:
                text = pt_read_file(rel, limit=None)
            except Exception:
                continue
            lines = text.splitlines()
            for kind, pattern in patterns:
                rx = re.compile(pattern)
                for index, line in enumerate(lines):
                    match = rx.search(line)
                    if not match:
                        continue
                    item_id = match.group(1)
                    out.setdefault(kind, {})[item_id] = {
                        "id": item_id,
                        "kind": kind,
                        "file": rel,
                        "line": index + 1,
                    }
        return out

    def pt_registry_source_maps():
        maps = pt_scan_call_sources([
            ("items", r"\bdefine_item\s*\(\s*[\"']([^\"']+)[\"']"),
            ("item_uses", r"\bitem_use\s*\(\s*[\"']([^\"']+)[\"']"),
            ("recipes", r"\brecipe\s*\(\s*[\"']([^\"']+)[\"']"),
            ("quests", r"\b(?:create_quest|side_quest|char_quest)\s*\(\s*[\"']([^\"']+)[\"']"),
            ("gallery", r"\bgallery_auto\s*\(\s*[\"']([^\"']+)[\"']"),
            ("minigames", r"\bminigame\s*\(\s*[\"']([^\"']+)[\"']"),
            ("perks", r"\bperk\s*\(\s*[\"']([^\"']+)[\"']"),
            ("achievements", r"\bachievement\s*\(\s*[\"']([^\"']+)[\"']"),
            ("areas", r"\bregister_area\s*\(\s*[\"']([^\"']+)[\"']"),
            ("location_defs", r"\bregister_location\s*\(\s*[\"']([^\"']+)[\"']"),
        ], file_prefixes=("Game/", "Mechanics/", "Engine/State/"))

        character_maps = pt_scan_call_sources([
            ("characters", r"\btracked_character\s*\([^,\n]+,\s*[\"']([^\"']+)[\"']"),
        ], file_prefixes=("Game/_Data/",))

        for kind, items in character_maps.items():
            maps.setdefault(kind, {}).update(items)
        return maps

    def pt_content_label_sources():
        out = {}
        for row in pt_file_rows():
            rel = row.get("path")
            if not rel:
                continue
            rel = str(rel).replace("\\", "/")
            if not rel.startswith("Game/Content/"):
                continue
            try:
                text = pt_read_file(rel, limit=None)
            except Exception:
                continue
            if "/Dialogue/Talk/" in rel:
                kind = "talk"
            elif "/Dialogue/Interact/" in rel:
                kind = "dialogue_interact"
            elif "/Interactions/" in rel:
                kind = "world_interactions"
            elif "/Story/" in rel:
                kind = "story"
            else:
                kind = "content"
            for index, line in enumerate(text.splitlines()):
                match = re.match(r"^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:", line)
                if not match:
                    continue
                label_id = match.group(1)
                out[label_id] = {
                    "id": label_id,
                    "kind": kind,
                    "file": rel,
                    "line": index + 1,
                }
        return out

    def pt_ui_source_maps():
        ui_prefixes = ("Engine/UI/", "Engine/Dialogue/", "Engine/Images/")
        out = {}
        patterns = [
            ("screens", re.compile(r"^\s*screen\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:)")),
            ("styles", re.compile(r"^\s*style\s+([A-Za-z_][A-Za-z0-9_]*)\b")),
            ("transforms", re.compile(r"^\s*transform\s+([A-Za-z_][A-Za-z0-9_]*)\b")),
            ("images", re.compile(r"^\s*image\s+([A-Za-z_][A-Za-z0-9_ ]*)\s*=")),
            ("gui_defines", re.compile(r"^\s*define\s+(gui\.[A-Za-z_][A-Za-z0-9_]*)\s*=")),
            ("defaults", re.compile(r"^\s*default\s+([A-Za-z_][A-Za-z0-9_]*)\s*=")),
        ]
        for row in pt_file_rows():
            rel = row.get("path")
            if not rel:
                continue
            rel = str(rel).replace("\\", "/")
            if rel not in ("screens.rpy", "gui.rpy") and not rel.startswith(ui_prefixes):
                continue
            try:
                text = pt_read_file(rel, limit=None)
            except Exception:
                continue
            for index, line in enumerate(text.splitlines()):
                for kind, rx in patterns:
                    match = rx.match(line)
                    if not match:
                        continue
                    item_id = match.group(1).strip()
                    out.setdefault(kind, {})[item_id] = {
                        "id": item_id,
                        "kind": kind,
                        "file": rel,
                        "line": index + 1,
                    }
        return out

    def pt_engine_api_source_maps():
        out = {}
        patterns = [
            ("functions", re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")),
            ("classes", re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b")),
            ("screens", re.compile(r"^\s*screen\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:)")),
            ("labels", re.compile(r"^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:")),
            ("defaults", re.compile(r"^\s*default\s+([A-Za-z_][A-Za-z0-9_]*)\s*=")),
            ("defines", re.compile(r"^\s*define\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*=")),
            ("transforms", re.compile(r"^\s*transform\s+([A-Za-z_][A-Za-z0-9_]*)\b")),
        ]
        for row in pt_file_rows():
            rel = row.get("path")
            if not rel:
                continue
            rel = str(rel).replace("\\", "/")
            if not (rel.startswith("Engine/") or rel.startswith("Mechanics/")):
                continue
            try:
                text = pt_read_file(rel, limit=None)
            except Exception:
                continue
            domain = "mechanics" if rel.startswith("Mechanics/") else "engine"
            for index, line in enumerate(text.splitlines()):
                for kind, rx in patterns:
                    match = rx.match(line)
                    if not match:
                        continue
                    item_id = match.group(1).strip()
                    out.setdefault(domain, {}).setdefault(kind, {})[item_id] = {
                        "id": item_id,
                        "kind": kind,
                        "domain": domain,
                        "file": rel,
                        "line": index + 1,
                    }
        return out

    def pt_selected_bounds():
        item, _parent, kind = selected_item()
        if not item:
            return None
        bounds = item.get("bounds")
        if not bounds:
            props = item.get("properties", {})
            width = props.get("xsize") or 120
            height = props.get("ysize") or 120
            bounds = calculate_bounds(props, width, height)
        return {
            "item": item,
            "kind": kind,
            "x": float(bounds.get("x", 0)),
            "y": float(bounds.get("y", 0)),
            "width": max(1, int(bounds.get("width", 1))),
            "height": max(1, int(bounds.get("height", 1))),
        }

    def pt_hotspot_from_selection():
        data = pt_selected_bounds()
        if not data:
            return "# Select an image, UI node, or captured hotspot first."
        item = data["item"]
        center_x = round((data["x"] + data["width"] / 2.0) / float(store.config.screen_width), 3)
        center_y = round((data["y"] + data["height"] / 2.0) / float(store.config.screen_height), 3)
        image_name = item.get("image") or item.get("name") or ""
        object_id = safe_identifier(image_name.split()[-1] if image_name else item.get("name", "object"), "object")
        object_code = pt_hotspot_object_code(object_id, image_name, center_x, center_y, data["width"], data["height"])
        label_code = pt_hotspot_label_code(object_id)
        return object_code + "\n\n" + label_code

    def pt_hotspot_object_code(object_id, image_name, center_x, center_y, width, height):
        return "\n".join([
            "object_spot(",
            "    {!r},".format(object_id),
            "    name={!r},".format(object_id.replace("_", " ").title()),
            "    pos=({}, {}),".format(center_x, center_y),
            "    size=({}, {}),".format(width, height),
            "    image={!r},".format(image_name) if image_name else "    # image=\"registered image name\",",
            "    allow_item_use=True,",
            "    actions=[",
            "        action(\"Inspect\", \"{}_inspect\", primary=True, once=True),".format(object_id),
            "    ],",
            "),",
        ])

    def pt_hotspot_label_code(object_id):
        return "\n".join([
            "label {}_inspect:".format(object_id),
            "    \"Describe what the player notices.\"",
            "    jump explore",
        ])

    def pt_hotspot_parts_from_selection():
        data = pt_selected_bounds()
        if not data:
            return None
        item = data["item"]
        center_x = round((data["x"] + data["width"] / 2.0) / float(store.config.screen_width), 3)
        center_y = round((data["y"] + data["height"] / 2.0) / float(store.config.screen_height), 3)
        image_name = item.get("image") or item.get("name") or ""
        object_id = safe_identifier(image_name.split()[-1] if image_name else item.get("name", "object"), "object")
        return {
            "id": object_id,
            "object": pt_hotspot_object_code(object_id, image_name, center_x, center_y, data["width"], data["height"]),
            "label": pt_hotspot_label_code(object_id),
        }

    def pt_location_template():
        return "\n".join([
            "location_package(",
            "    id=\"new_location\",",
            "    name=\"New Location\",",
            "    area=\"school\",",
            "    bg=\"bg_image_name\",",
            "    positions={",
            "        \"alice\": [(0.35, 1.0)],",
            "    },",
            "    layers=[",
            "        explore_layer(\"bg_image_name\", slot=\"background\", zoom=1.02, drift=(8, 0), duration=18.0),",
            "    ],",
            "    objects=[",
            "        object_spot(\"desk\", name=\"Desk\", pos=(0.55, 0.62), size=(180, 120), allow_item_use=True),",
            "    ],",
            "    exits=[",
            "        exit_spot(\"hallway\", label=\"Hallway\", pos=(0.5, 0.92), size=(260, 140)),",
            "    ],",
            ")",
        ])

    def pt_quest_template():
        return "\n".join([
            "create_quest(",
            "    \"new_quest\",",
            "    title=\"New Quest\",",
            "    desc=\"Short player-facing quest description.\",",
            "    discover=True,",
            "    unlock_when=req(\"flag:intro_done\"),",
            "    guide_precision=\"area\",",
            "    target={\"location\": \"hallway\"},",
            "    steps=[",
            "        step(\"start\", \"Inspect the clue\", flag=\"new_quest_started\", target={\"object\": \"desk\", \"location\": \"new_location\"}),",
            "        step(\"finish\", \"Talk to Alice\", flag=\"new_quest_done\", target={\"npc\": \"alice\", \"location\": \"hallway\"}),",
            "    ],",
            ")",
        ])

    def pt_dialogue_template():
        return "\n".join([
            "label alice_new_scene:",
            "    $ begin_dialogue(\"alice\", pos=\"left\")",
            "    a \"Write the scene like normal.\"",
            "    $ menu_side(\"right\")",
            "    menu:",
            "        \"Confident answer. {color=#ffd27a}(Coolness 10){/color}\" if can(\"stat:Coolness>=10\"):",
            "            $ stat(\"player\", \"Coolness\", 1, \"3d\")",
            "            a \"That worked.\"",
            "        \"Kind answer. {color=#ffd27a}(Alice Love 10){/color}\" if can(\"Alice.Love>=10\"):",
            "            $ alice.trust(1, \"3d\")",
            "            a \"I knew you would say that.\"",
            "    $ end_dialogue()",
            "    return",
        ])

    def pt_branch_template():
        return "\n".join([
            "$ branch_point(\"new_branch\")",
            "$ stop_rollback_here()",
            "menu:",
            "    \"Take Alice's route.\":",
            "        $ take_branch(\"new_branch\", \"alice\")",
            "        jump alice_route",
            "    \"Take Alex's route.\":",
            "        $ take_branch(\"new_branch\", \"alex\")",
            "        jump alex_route",
        ])

    def pt_image_locator_reference():
        aliases = pt_index().get("image_aliases", {})
        alias_lines = ["character_image_aliases = {"]
        if aliases:
            for key, value in sorted(aliases.items()):
                alias_lines.append("    {!r}: {!r},".format(key, value))
        else:
            alias_lines.append("    \"temporary_character\": \"alice\",")
        alias_lines.append("}")
        return "\n".join([
            "# Auto image locator patterns",
            "# Character files: Alice.png, Alice_Happy.png, Alice_Outfit1_Sad.png",
            "# Author-facing show helpers:",
            "$ Show(\"Alice\", side=\"Left\")",
            "$ Show(\"Alice\", emotion=\"Happy\", side=\"Right\")",
            "$ Hide(\"Alice\")",
            "",
            "# Temporary image aliases for test characters:",
        ] + alias_lines)

    def pt_inventory_template():
        return "\n".join([
            "define_item(\"lockpick\", name=\"Lockpick\", desc=\"Thin enough for old doors.\", tags=[\"tool\"], quest_item=True)",
            "",
            "item_use(",
            "    \"lockpick\",",
            "    \"archive_door\",",
            "    label=\"use_lockpick_on_archive_door\",",
            "    requires=req(\"stat:Coolness>=10\"),",
            "    consume=False,",
            "    fail=\"The lockpick slips. You need a steadier hand.\",",
            ")",
            "",
            "item_use(\"*\", \"archive_door\", fail=\"I don't think {item_name} will work on this door.\", always_fail=True)",
            "recipe(\"coded_slip\", \"glass_badge\", result=\"matched_badge_clue\")",
            "",
            "label use_lockpick_on_archive_door(item_id=None, target=None):",
            "    \"You work the pick under the old latch.\"",
            "    $ unlock_room(\"archive_room\")",
            "    $ set_flag(\"archive_room_unlocked\")",
            "    jump explore",
        ])

    def pt_inventory_data_template():
        return "\n".join([
            "define_item(\"lockpick\", name=\"Lockpick\", desc=\"Thin enough for old doors.\", tags=[\"tool\"], quest_item=True)",
            "",
            "item_use(",
            "    \"lockpick\",",
            "    \"archive_door\",",
            "    label=\"use_lockpick_on_archive_door\",",
            "    requires=req(\"stat:Coolness>=10\"),",
            "    consume=False,",
            "    fail=\"The lockpick slips. You need a steadier hand.\",",
            ")",
            "",
            "item_use(\"*\", \"archive_door\", fail=\"I don't think {item_name} will work on this door.\", always_fail=True)",
            "recipe(\"coded_slip\", \"glass_badge\", result=\"matched_badge_clue\")",
        ])

    def pt_inventory_content_template():
        return "\n".join([
            "label use_lockpick_on_archive_door(item_id=None, target=None):",
            "    \"You work the pick under the old latch.\"",
            "    $ unlock_room(\"archive_room\")",
            "    $ set_flag(\"archive_room_unlocked\")",
            "    jump explore",
        ])

    def pt_gallery_template():
        return "\n".join([
            "gallery_auto(",
            "    \"alice_private_signal_scene\",",
            "    character=\"alice\",",
            "    group=\"Alice\",",
            "    unlock=\"flag:alice_private_signal_scene_done\",",
            "    scene_image=\"bg smp_roof\",",
            "    autounlock=False,",
            ")",
            "",
            "label alice_private_signal_scene:",
            "    scene bg smp_roof",
            "    show alice at left",
            "    a \"This scene can unlock itself when finished.\"",
            "    $ set_flag(\"alice_private_signal_scene_done\")",
            "    return",
        ])

    def pt_minigame_template():
        return "\n".join([
            "minigame(",
            "    \"door_lockpick\",",
            "    label=\"door_lockpick_minigame\",",
            "    skip_label=\"door_lockpick_skip\",",
            "    skip_result=\"win\",",
            "    requires=req(\"item:lockpick\"),",
            "    fail_forward=True,",
            ")",
            "",
            "label door_lockpick_minigame(game_id=None):",
            "    # Replace this with a real screen or mechanic later.",
            "    \"You test the lock.\"",
            "    $ complete_minigame(game_id, \"win\")",
            "    return",
            "",
            "label door_lockpick_skip(game_id=None):",
            "    \"You bypass the lockpick challenge.\"",
            "    return",
            "",
            "$ start_minigame(\"door_lockpick\")",
        ])

    def pt_minigame_data_template():
        return "\n".join([
            "minigame(",
            "    \"door_lockpick\",",
            "    label=\"door_lockpick_minigame\",",
            "    skip_label=\"door_lockpick_skip\",",
            "    skip_result=\"win\",",
            "    requires=req(\"item:lockpick\"),",
            "    fail_forward=True,",
            ")",
        ])

    def pt_minigame_content_template():
        return "\n".join([
            "label door_lockpick_minigame(game_id=None):",
            "    # Replace this with a real screen or mechanic later.",
            "    \"You test the lock.\"",
            "    $ complete_minigame(game_id, \"win\")",
            "    return",
            "",
            "label door_lockpick_skip(game_id=None):",
            "    \"You bypass the lockpick challenge.\"",
            "    return",
        ])

    def pt_text_transform_reference():
        return "\n".join([
            "# Kinetic text tags",
            "a \"{wave}Excited text.{/wave}\"",
            "a \"{shake}Scared text.{/shake}\"",
            "a \"{fade}Slow reveal text.{/fade}\"",
            "a \"{swell}Soft emphasis.{/swell}\"",
            "a \"{rainbow}Unstable color.{/rainbow}\"",
            "a \"{glitch}Heavy glitch, accessibility-toggle aware.{/glitch}\"",
            "",
            "# Common character placement",
            "$ Show(\"Alice\", side=\"Left\")",
            "$ Show(\"Alex\", side=\"Right\")",
            "$ Show(\"Alice\", emotion=\"Happy\", side=\"Middle\")",
            "",
            "# Exploration parallax layer",
            "explore_layer(\"bg smp_noticeboard\", slot=\"overlay\", alpha=0.25, zoom=1.04, drift=(10, 0), duration=18.0)",
        ])

    def pt_source_filename_to_rel(filename):
        value = str(filename or "").replace("\\", "/")
        if not value:
            return ""
        marker = "/game/"
        lower = value.lower()
        if marker in lower:
            return value[lower.rfind(marker) + len(marker):]
        if lower.startswith("game/"):
            return value[5:]
        return value.lstrip("/")

    def pt_selected_source_report():
        item, _parent, kind = selected_item()
        if not item:
            return "# Select a captured scene or UI item first."
        source = item.get("source") or {}
        screen_language = source.get("screen_language") or {}
        filename = ""
        line = ""
        location = source.get("location") or screen_language.get("location")
        if isinstance(location, (list, tuple)) and len(location) >= 2:
            filename = location[0]
            line = location[1]
        elif isinstance(location, str):
            filename = location
        if not filename:
            filename = source.get("source") or source.get("filename") or screen_language.get("filename") or ""
        rel = pt_source_filename_to_rel(filename)
        frame = current_frame() or {}
        overrides = (frame.get("changes", {}).get("sets", {}).get(item.get("id"), {}) or {})
        rows = [
            "# Direct source patch candidate",
            "# Kind: {}".format(kind),
            "# Item: {}".format(item.get("name", item.get("id", ""))),
            "# Source file: {}".format(rel or "unknown"),
            "# Source line: {}".format(line or "unknown"),
            "# Widget id: {}".format(item.get("widget_id") or "none"),
            "",
            "# Current Live Studio overrides:",
        ]
        if overrides:
            for key, value in sorted(overrides.items()):
                rows.append("#   {} = {!r}".format(key, value))
        else:
            rows.append("#   No local overrides yet. Move/resize/edit the selected item first.")
        rows.extend([
            "",
            "# This report is intentionally conservative. For safe direct rewriting,",
            "# Live Studio must find the exact source block, back it up, then replace",
            "# only the matching property lines. Use file preview to inspect the target.",
        ])
        return "\n".join(rows)

    def pt_validate_project():
        issues = []
        locations = pt_store_dict("locations")
        quest_defs = pt_store_dict("quest_defs")
        item_defs = pt_store_dict("item_defs")
        interactables = pt_store_dict("interactable_defs")
        for qid, q in quest_defs.items():
            targets = []
            if isinstance(q.get("target"), dict):
                targets.append(q.get("target"))
            for obj in q.get("objectives", []) or []:
                if isinstance(obj, dict) and isinstance(obj.get("target"), dict):
                    targets.append(obj.get("target"))
            for target in targets:
                loc = target.get("location")
                if loc and loc not in locations:
                    issues.append("Quest {} targets missing location {}".format(qid, loc))
                obj = target.get("object")
                if obj and obj not in interactables:
                    issues.append("Quest {} targets missing interactable {}".format(qid, obj))
                item = target.get("item")
                if item and item not in item_defs:
                    issues.append("Quest {} targets missing item {}".format(qid, item))
        if not issues:
            issues.append("No Project Tac registry issues found.")
        return "\n".join(issues)

    def pt_command_preview(title, builder):
        text = builder()
        set_extension_preview(title, text)
        return text

    def pt_apply_preview(rel_path, text):
        return pt_append_to_file(rel_path, text)

    def pt_selected_or_default_file(default_rel, prefix=None, preferred_rel=None):
        selected = selected_extension_file(active_extension())
        if selected and (prefix is None or str(selected).replace("\\", "/").startswith(prefix)):
            return selected
        if preferred_rel and (prefix is None or str(preferred_rel).replace("\\", "/").startswith(prefix)):
            return preferred_rel
        return default_rel

    def pt_write_quest_template():
        target = "Game/_Data/Quests.rpy"
        result = pt_insert_into_last_init_python(target, pt_quest_template())
        return "\n".join([
            "Wrote quest template.",
            result,
            "",
            "Inserted inside the quest definition init block so it loads as data, not loose script.",
        ])

    def pt_write_inventory_template():
        data_target = "Game/_Data/Items.rpy"
        content_target = pt_selected_or_default_file("Game/Content/Interactions/School/hallway.rpy", "Game/Content/Interactions/", pt_current_location_file())
        data_result = pt_insert_into_last_init_python(data_target, pt_inventory_data_template())
        content_result = pt_append_to_file(content_target, pt_inventory_content_template())
        return "\n".join([
            "Wrote inventory template.",
            data_result,
            content_result,
            "",
            "Item definitions went to data. The item-use label went to interaction content.",
        ])

    def pt_write_dialogue_template():
        target = pt_selected_or_default_file("Game/Content/Dialogue/Interact/Alice.rpy", "Game/Content/Dialogue/")
        result = pt_append_to_file(target, pt_dialogue_template())
        return "\n".join([
            "Wrote dialogue template.",
            result,
        ])

    def pt_write_branch_template():
        target = pt_selected_or_default_file("Game/Content/Story/Act_01/chapter1_intro.rpy", "Game/Content/Story/")
        result = pt_append_to_file(target, pt_branch_template())
        return "\n".join([
            "Wrote branch template.",
            result,
        ])

    def pt_write_gallery_template():
        target = pt_selected_or_default_file("Game/Content/Dialogue/Interact/Complex_Test_Arc.rpy", "Game/Content/")
        result = pt_append_to_file(target, pt_gallery_template())
        return "\n".join([
            "Wrote gallery template.",
            result,
            "",
            "Gallery registration stays beside the scene so the unlocker and content remain easy to read together.",
        ])

    def pt_write_hotspot_template():
        target = pt_selected_or_default_file("Game/Content/Interactions/School/hallway.rpy", "Game/Content/Interactions/", pt_current_location_file())
        parts = pt_hotspot_parts_from_selection()
        if not parts:
            return "# Select an image, UI node, or captured hotspot first."
        object_result = pt_insert_into_python_list(target, "objects", parts["object"], fallback_before="exits")
        label_result = pt_append_to_file(target, parts["label"])
        return "\n".join([
            "Wrote interactable snippet.",
            object_result,
            label_result,
            "",
            "Inserted object_spot into the location package and appended its inspect label.",
        ])

    def pt_writer_target_report():
        selected = selected_extension_file(active_extension()) or ""
        current_loc = pt_current_location_id()
        current_file = pt_current_location_file()
        source_maps = (pt_index().get("source_maps", {}) or {})
        mapped_counts = ", ".join("{}:{}".format(kind, len(values)) for kind, values in sorted(source_maps.items()) if values)
        label_count = len(pt_index().get("label_sources", {}) or {})
        ui_maps = (pt_index().get("ui_sources", {}) or {})
        ui_counts = ", ".join("{}:{}".format(kind, len(values)) for kind, values in sorted(ui_maps.items()) if values)
        api_maps = (pt_index().get("api_sources", {}) or {})
        api_counts = ", ".join("{}:{}".format(domain, sum(len(values) for values in groups.values())) for domain, groups in sorted(api_maps.items()) if groups)
        rows = [
            "# Project Tac writer targets",
            "",
            "Selected file: {}".format(selected or "none"),
            "Current location: {}".format(current_loc or "unknown"),
            "Current location source: {}".format(current_file or "not mapped"),
            "Mapped registries: {}".format(mapped_counts or "none"),
            "Mapped content labels: {}".format(label_count),
            "Mapped UI sources: {}".format(ui_counts or "none"),
            "Mapped Engine/Mechanics APIs: {}".format(api_counts or "none"),
            "",
            "Quest template -> Game/_Data/Quests.rpy",
            "Inventory data -> Game/_Data/Items.rpy",
            "Inventory use label -> {}".format(pt_selected_or_default_file("Game/Content/Interactions/School/hallway.rpy", "Game/Content/Interactions/", current_file)),
            "Interactable object/label -> {}".format(pt_selected_or_default_file("Game/Content/Interactions/School/hallway.rpy", "Game/Content/Interactions/", current_file)),
            "Dialogue template -> {}".format(pt_selected_or_default_file("Game/Content/Dialogue/Interact/Alice.rpy", "Game/Content/Dialogue/")),
            "Branch template -> {}".format(pt_selected_or_default_file("Game/Content/Story/Act_01/chapter1_intro.rpy", "Game/Content/Story/")),
            "Gallery template -> {}".format(pt_selected_or_default_file("Game/Content/Dialogue/Interact/Complex_Test_Arc.rpy", "Game/Content/")),
            "",
            "Manual selection wins when it matches the writer's content domain.",
            "Current-location source is used for interaction writers when no interaction file is selected.",
        ]
        return "\n".join(rows)

    def pt_categorize_commands(commands):
        categories = {
            "refresh": "Overview",
            "validate": "Overview",
            "select_current_location": "Overview",
            "target_report": "Overview",
            "file_coverage": "Overview",
            "registry_sources": "Reports",
            "label_sources": "Reports",
            "ui_sources": "Reports",
            "api_sources": "Reports",
            "select_characters_data": "Open Data",
            "select_schedules_data": "Open Data",
            "select_locations_data": "Open Data",
            "select_items_data": "Open Data",
            "select_quests_data": "Open Data",
            "select_screens_ui": "Open UI",
            "select_gui_ui": "Open UI",
            "select_project_ui": "Open UI",
            "select_hud_ui": "Open UI",
            "select_locations_ui": "Open UI",
            "select_location_engine": "Open Engine",
            "select_location_package": "Open Engine",
            "select_interactables_engine": "Open Engine",
            "select_dialogue_engine": "Open Engine",
            "select_image_locator": "Open Engine",
            "select_quest_runtime": "Open Mechanics",
            "select_inventory_mechanic": "Open Mechanics",
            "select_time_stamina": "Open Mechanics",
            "hotspot": "Generate",
            "write_hotspot": "Write",
            "location": "Generate",
            "quest": "Generate",
            "write_quest": "Write",
            "dialogue": "Generate",
            "write_dialogue": "Write",
            "branch": "Generate",
            "write_branch": "Write",
            "images": "Reference",
            "inventory": "Generate",
            "write_inventory": "Write",
            "gallery": "Generate",
            "write_gallery": "Write",
            "minigame": "Generate",
            "text_transforms": "Reference",
            "source_report": "Direct Edit",
            "source_block": "Direct Edit",
            "property_patch_preview": "Direct Edit",
            "property_patch_apply": "Direct Edit",
        }
        for command in commands:
            command.setdefault("category", categories.get(command.get("id"), "General"))
        return commands

    register_extension(
        "project_tac",
        title="Project Tac",
        description="Authoring helpers for locations, quests, branches, dialogue, parallax layers, and engine registries.",
        summary=pt_summary_rows,
        files=pt_file_rows,
        file_preview=pt_file_preview,
        apply_preview=pt_apply_preview,
        available=pt_available,
        order=10,
        commands=pt_categorize_commands([
            {"id": "refresh", "title": "Refresh Project Index", "description": "Re-scan Project Tac registries.", "action": pt_refresh_index},
            {"id": "validate", "title": "Validate Registries", "description": "Find missing quest targets and bad references.", "action": lambda: pt_command_preview("Project Tac Validation", pt_validate_project)},
            {"id": "select_current_location", "title": "Select Current Location File", "description": "Pick the source file that defines the runtime current_location.", "action": lambda: pt_command_preview("Current Location Source", pt_select_current_location_file)},
            {"id": "target_report", "title": "Writer Target Report", "description": "Preview the exact files typed write commands will touch.", "action": lambda: pt_command_preview("Writer Target Report", pt_writer_target_report)},
            {"id": "registry_sources", "title": "Registry Source Report", "description": "List source files and lines for Project Tac data definitions.", "action": lambda: pt_command_preview("Registry Source Report", pt_registry_source_report)},
            {"id": "label_sources", "title": "Content Label Report", "description": "List story, dialogue, and interaction labels by source file.", "action": lambda: pt_command_preview("Content Label Report", pt_label_source_report)},
            {"id": "file_coverage", "title": "File Coverage Report", "description": "List every indexed file and whether Studio can write to it.", "action": lambda: pt_command_preview("File Coverage Report", pt_file_coverage_report)},
            {"id": "ui_sources", "title": "UI Source Report", "description": "List screens, styles, transforms, images, GUI defines, and defaults.", "action": lambda: pt_command_preview("UI Source Report", pt_ui_source_report)},
            {"id": "api_sources", "title": "Engine API Report", "description": "List callable Engine and Mechanics helpers by source file.", "action": lambda: pt_command_preview("Engine API Report", pt_engine_api_report)},
            {"id": "select_characters_data", "title": "Open Characters Data", "description": "Select the character definitions file.", "action": lambda: pt_command_preview("Characters Data", lambda: pt_select_data_file("characters"))},
            {"id": "select_schedules_data", "title": "Open Schedules Data", "description": "Select the character schedules file.", "action": lambda: pt_command_preview("Schedules Data", lambda: pt_select_data_file("schedules"))},
            {"id": "select_locations_data", "title": "Open Locations Data", "description": "Select the area/location definitions file.", "action": lambda: pt_command_preview("Locations Data", lambda: pt_select_data_file("locations"))},
            {"id": "select_items_data", "title": "Open Items Data", "description": "Select the item definitions file.", "action": lambda: pt_command_preview("Items Data", lambda: pt_select_data_file("items"))},
            {"id": "select_quests_data", "title": "Open Quests Data", "description": "Select the quest definitions file.", "action": lambda: pt_command_preview("Quests Data", lambda: pt_select_data_file("quests"))},
            {"id": "select_screens_ui", "title": "Open Root Screens", "description": "Select root screens.rpy.", "action": lambda: pt_command_preview("Root Screens", lambda: pt_select_ui_file("screens"))},
            {"id": "select_gui_ui", "title": "Open GUI Config", "description": "Select root gui.rpy.", "action": lambda: pt_command_preview("GUI Config", lambda: pt_select_ui_file("gui"))},
            {"id": "select_project_ui", "title": "Open Project UI Screens", "description": "Select Engine/UI/Screens.rpy.", "action": lambda: pt_command_preview("Project UI Screens", lambda: pt_select_ui_file("project_ui"))},
            {"id": "select_hud_ui", "title": "Open HUD UI", "description": "Select Engine/UI/HUD.rpy.", "action": lambda: pt_command_preview("HUD UI", lambda: pt_select_ui_file("hud"))},
            {"id": "select_locations_ui", "title": "Open Locations UI", "description": "Select Engine/UI/Locations.rpy.", "action": lambda: pt_command_preview("Locations UI", lambda: pt_select_ui_file("locations"))},
            {"id": "select_location_engine", "title": "Open Location Engine", "description": "Select Engine/World/Location_System.rpy.", "action": lambda: pt_command_preview("Location Engine", lambda: pt_select_engine_file("location_engine"))},
            {"id": "select_location_package", "title": "Open Location Package", "description": "Select Engine/World/Location_Package.rpy.", "action": lambda: pt_command_preview("Location Package", lambda: pt_select_engine_file("location_package"))},
            {"id": "select_interactables_engine", "title": "Open Interactables Engine", "description": "Select Engine/World/Interactables.rpy.", "action": lambda: pt_command_preview("Interactables Engine", lambda: pt_select_engine_file("interactables"))},
            {"id": "select_dialogue_engine", "title": "Open Dialogue Engine", "description": "Select Engine/Dialogue/Dialogue_Handler.rpy.", "action": lambda: pt_command_preview("Dialogue Engine", lambda: pt_select_engine_file("dialogue"))},
            {"id": "select_image_locator", "title": "Open Image Locator", "description": "Select Engine/Images/Image_Locater.rpy.", "action": lambda: pt_command_preview("Image Locator", lambda: pt_select_engine_file("image_locator"))},
            {"id": "select_quest_runtime", "title": "Open Quest Runtime", "description": "Select Mechanics/Quest/Quest_Runtime.rpy.", "action": lambda: pt_command_preview("Quest Runtime", lambda: pt_select_mechanic_file("quest_runtime"))},
            {"id": "select_inventory_mechanic", "title": "Open Inventory Mechanic", "description": "Select Mechanics/Inventory/Inventory.rpy.", "action": lambda: pt_command_preview("Inventory Mechanic", lambda: pt_select_mechanic_file("inventory"))},
            {"id": "select_time_stamina", "title": "Open Time/Stamina", "description": "Select Mechanics/Time_Stamina.rpy.", "action": lambda: pt_command_preview("Time Stamina", lambda: pt_select_mechanic_file("time_stamina"))},
            {"id": "hotspot", "title": "Selection -> Interactable", "description": "Generate object_spot code from the selected canvas bounds.", "action": lambda: pt_command_preview("Interactable From Selection", pt_hotspot_from_selection)},
            {"id": "write_hotspot", "title": "Write Interactable", "description": "Back up the selected or current-location interaction file and insert the generated selection hotspot.", "writes": True, "action": lambda: pt_command_preview("Write Interactable Result", pt_write_hotspot_template)},
            {"id": "location", "title": "Location Template", "description": "Generate a location_package starter with parallax, objects, exits, and positions.", "action": lambda: pt_command_preview("Location Template", pt_location_template)},
            {"id": "quest", "title": "Quest Template", "description": "Generate a short create_quest starter.", "action": lambda: pt_command_preview("Quest Template", pt_quest_template)},
            {"id": "write_quest", "title": "Write Quest Template", "description": "Back up Game/_Data/Quests.rpy and insert the quest template inside its init block.", "writes": True, "action": lambda: pt_command_preview("Write Quest Result", pt_write_quest_template)},
            {"id": "dialogue", "title": "Dialogue Template", "description": "Generate Project Tac dialogue with side menu and stat requirements.", "action": lambda: pt_command_preview("Dialogue Template", pt_dialogue_template)},
            {"id": "write_dialogue", "title": "Write Dialogue Template", "description": "Back up the selected dialogue file and append the generated scene.", "writes": True, "action": lambda: pt_command_preview("Write Dialogue Result", pt_write_dialogue_template)},
            {"id": "branch", "title": "Branch Template", "description": "Generate branch point and permanent branch-save compatible script.", "action": lambda: pt_command_preview("Branch Template", pt_branch_template)},
            {"id": "write_branch", "title": "Write Branch Template", "description": "Back up the selected story file and append the generated branch.", "writes": True, "action": lambda: pt_command_preview("Write Branch Result", pt_write_branch_template)},
            {"id": "images", "title": "Image Locator Reference", "description": "Show image alias and Show/Hide helper syntax.", "action": lambda: pt_command_preview("Image Locator Reference", pt_image_locator_reference)},
            {"id": "inventory", "title": "Inventory/Item Template", "description": "Generate item, item-use, wildcard fail, and crafting examples.", "action": lambda: pt_command_preview("Inventory Template", pt_inventory_template)},
            {"id": "write_inventory", "title": "Write Inventory Template", "description": "Back up item data and interaction content, then place each part in the right file.", "writes": True, "action": lambda: pt_command_preview("Write Inventory Result", pt_write_inventory_template)},
            {"id": "gallery", "title": "Gallery Template", "description": "Generate gallery_auto and scene unlock example.", "action": lambda: pt_command_preview("Gallery Template", pt_gallery_template)},
            {"id": "write_gallery", "title": "Write Gallery Template", "description": "Back up the selected content file and append gallery registration plus scene.", "writes": True, "action": lambda: pt_command_preview("Write Gallery Result", pt_write_gallery_template)},
            {"id": "minigame", "title": "Minigame Template", "description": "Generate universal minigame registration and skip-mode labels.", "action": lambda: pt_command_preview("Minigame Template", pt_minigame_template)},
            {"id": "text_transforms", "title": "Text/Transform Reference", "description": "Show kinetic text, character placement, and parallax snippets.", "action": lambda: pt_command_preview("Text And Transform Reference", pt_text_transform_reference)},
            {"id": "source_report", "title": "Selection Source Report", "description": "Inspect source metadata and property overrides for direct-file editing.", "action": lambda: pt_command_preview("Selection Source Report", pt_selected_source_report)},
            {"id": "source_block", "title": "Preview Source Block", "description": "Show the exact source block behind the selected item.", "action": lambda: pt_command_preview("Selected Source Block", pt_selected_source_block_preview)},
            {"id": "property_patch_preview", "title": "Preview Property Patch", "description": "Generate a direct source patch from selected item overrides.", "action": lambda: pt_command_preview("Property Patch Preview", pt_selected_property_patch_preview)},
            {"id": "property_patch_apply", "title": "Apply Property Patch", "description": "Back up the source file and write selected item property overrides directly.", "writes": True, "action": lambda: pt_command_preview("Property Patch Result", pt_apply_selected_property_patch)},
        ]),
    )
