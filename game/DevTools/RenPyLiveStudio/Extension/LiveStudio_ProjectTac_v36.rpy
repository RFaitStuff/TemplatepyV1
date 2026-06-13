# Project Tac v3.6 integration: capability negotiation, complete source index,
# structured validation, atomic writes, diffs, and multi-file transactions.
# This remains inside the optional extension so the universal Live Studio core
# never assumes Project Tac's directory layout or data conventions.

init -844 python in live_studio:
    import difflib as _pt_difflib
    import hashlib as _pt_hashlib
    import json as _pt_json
    import os as _pt_os
    import re as _pt_re
    import shutil as _pt_shutil
    import time as _pt_time
    import uuid as _pt_uuid

    PROJECT_TAC_EXTENSION_VERSION = "1.1.0"
    _pt_uncached_file_rows = pt_file_rows

    def pt_file_rows(force=False):
        cached = runtime.get("project_tac_file_rows")
        if cached is not None and not force:
            return list(cached)
        rows = list(_pt_uncached_file_rows() or [])
        runtime["project_tac_file_rows"] = rows
        return list(rows)

    PROJECT_TAC_EXPECTED_CAPABILITIES = {
        "characters": 1,
        "relationships": 1,
        "locations": 2,
        "quests": 2,
        "inventory": 2,
        "gallery": 1,
        "minigames": 1,
        "source_authoring": 2,
        "live_studio_sync": 2,
    }

    def pt_engine_descriptor():
        descriptor = getattr(store, "PROJECT_TAC_ENGINE", None)
        if isinstance(descriptor, dict):
            result = clone(descriptor)
            result.setdefault("engine_version", str(getattr(store, "PROJECT_TAC_VERSION", "unknown")))
            result.setdefault("data_schema", int(getattr(store, "PROJECT_TAC_DATA_SCHEMA", 0) or 0))
            result.setdefault("capabilities", {})
            result["source"] = "PROJECT_TAC_ENGINE"
            return result
        capabilities = {}
        probes = {
            "characters": ("character_stats", "tracked_character"),
            "relationships": ("RELATIONSHIP_STATS", "stat"),
            "locations": ("locations", "location_package"),
            "quests": ("quest_defs", "create_quest"),
            "inventory": ("item_defs", "add_item"),
            "gallery": ("gallery_auto", "gallery_scene"),
            "minigames": ("minigame", "minigame_defs"),
            "source_authoring": (),
            "live_studio_sync": (),
        }
        for name, symbols in probes.items():
            if name in ("source_authoring", "live_studio_sync"):
                capabilities[name] = 2
            else:
                capabilities[name] = 1 if any(hasattr(store, symbol) for symbol in symbols) else 0
        return {
            "engine_version": str(getattr(store, "PROJECT_TAC_VERSION", "unversioned")),
            "data_schema": int(getattr(store, "PROJECT_TAC_DATA_SCHEMA", 0) or 0),
            "capabilities": capabilities,
            "source": "inferred",
        }

    def pt_capability_status(requirements=None):
        descriptor = pt_engine_descriptor()
        capabilities = descriptor.get("capabilities", {}) or {}
        requirements = requirements or PROJECT_TAC_EXPECTED_CAPABILITIES
        missing = []
        for name, minimum in requirements.items():
            try:
                actual = int(capabilities.get(name, 0) or 0)
                minimum = int(minimum or 0)
            except Exception:
                actual, minimum = 0, 0
            if actual < minimum:
                missing.append({"capability": name, "required": minimum, "actual": actual})
        return {"compatible": not missing, "descriptor": descriptor, "missing": missing}

    def pt_capability_report():
        status = pt_capability_status()
        descriptor = status.get("descriptor", {})
        lines = [
            "Project Tac Capability Report",
            "Engine version: {}".format(descriptor.get("engine_version", "unknown")),
            "Data schema: {}".format(descriptor.get("data_schema", 0)),
            "Descriptor source: {}".format(descriptor.get("source", "unknown")),
            "Live Studio extension: {}".format(PROJECT_TAC_EXTENSION_VERSION),
            "Compatible: {}".format("yes" if status.get("compatible") else "no"),
            "",
        ]
        capabilities = descriptor.get("capabilities", {}) or {}
        for name in sorted(set(capabilities) | set(PROJECT_TAC_EXPECTED_CAPABILITIES)):
            lines.append("{}: {} (expected {})".format(name, capabilities.get(name, 0), PROJECT_TAC_EXPECTED_CAPABILITIES.get(name, 0)))
        if status.get("missing"):
            lines.append("")
            for row in status.get("missing"):
                lines.append("MISSING: {capability} requires {required}, found {actual}".format(**row))
        return "\n".join(lines)

    def pt_project_paths():
        descriptor = pt_engine_descriptor()
        paths = descriptor.get("paths", {}) if isinstance(descriptor, dict) else {}
        fallback = getattr(store, "PROJECT_TAC_PATHS", None)
        if isinstance(fallback, dict):
            merged = dict(fallback)
            if isinstance(paths, dict):
                merged.update(paths)
            return merged
        return dict(paths or {}) if isinstance(paths, dict) else {}

    def pt_project_path(key, default=None):
        return pt_project_paths().get(key, default)

    def pt_file_signature(rel_path):
        path = pt_abs_path(rel_path)
        try:
            stat = _pt_os.stat(path)
            return "{}:{}".format(int(stat.st_mtime_ns), int(stat.st_size))
        except Exception:
            return "missing"

    def pt_project_signature(rows=None):
        rows = rows if rows is not None else pt_file_rows()
        digest = _pt_hashlib.sha256()
        for row in sorted(rows, key=lambda value: value.get("path", "")):
            rel = str(row.get("path") or "")
            digest.update(rel.encode("utf-8", "replace"))
            digest.update(b"\0")
            digest.update(pt_file_signature(rel).encode("ascii", "replace"))
            digest.update(b"\n")
        return digest.hexdigest()

    def _pt_block_end(lines, start_index, base_indent=None):
        if base_indent is None:
            base_indent = pt_line_indent(lines[start_index])
        end = start_index + 1
        while end < len(lines):
            line = lines[end]
            if line.strip() and pt_line_indent(line) <= base_indent:
                break
            end += 1
        return end

    def _pt_source_record(kind, object_id, rel, line, end_line=None, name=None, extra=None):
        row = {
            "id": str(object_id or ""),
            "name": str(name or object_id or ""),
            "kind": str(kind or "object"),
            "file": str(rel or ""),
            "line": int(line or 0),
            "end_line": int(end_line or line or 0),
        }
        if extra:
            row.update(json_safe(extra))
        return row

    def pt_scan_source_file(rel_path):
        text = pt_read_file(rel_path, limit=None)
        lines = text.splitlines()
        records = []
        patterns = (
            ("label", _pt_re.compile(r"^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:")),
            ("screen", _pt_re.compile(r"^\s*screen\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:")),
            ("transform", _pt_re.compile(r"^\s*transform\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:")),
            ("style", _pt_re.compile(r"^\s*style\s+([A-Za-z_][A-Za-z0-9_]*)\b")),
            ("image", _pt_re.compile(r"^\s*image\s+([A-Za-z_][A-Za-z0-9_ ]*)\s*=")),
            ("default", _pt_re.compile(r"^\s*default\s+([A-Za-z_][A-Za-z0-9_]*)\s*=")),
            ("define", _pt_re.compile(r"^\s*define\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*=")),
            ("python_function", _pt_re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")),
            ("python_class", _pt_re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b")),
        )
        calls = (
            ("character", _pt_re.compile(r"\btracked_character\s*\([^,\n]+,\s*[\"']([^\"']+)[\"']")),
            ("location", _pt_re.compile(r"\blocation_package\s*\(\s*id\s*=\s*[\"']([^\"']+)[\"']")),
            ("location_definition", _pt_re.compile(r"\bregister_location\s*\(\s*[\"']([^\"']+)[\"']")),
            ("quest", _pt_re.compile(r"\b(?:create_quest|side_quest|char_quest)\s*\(\s*[\"']([^\"']+)[\"']")),
            ("item", _pt_re.compile(r"\bdefine_item\s*\(\s*[\"']([^\"']+)[\"']")),
            ("item_use", _pt_re.compile(r"\bitem_use\s*\(\s*[\"']([^\"']+)[\"']")),
            ("interaction", _pt_re.compile(r"\b(?:object_spot|interactable|register_interactable)\s*\(\s*(?:id\s*=\s*)?[\"']([^\"']+)[\"']")),
            ("gallery", _pt_re.compile(r"\bgallery_auto\s*\(\s*[\"']([^\"']+)[\"']")),
            ("minigame", _pt_re.compile(r"\bminigame\s*\(\s*[\"']([^\"']+)[\"']")),
        )
        generated_begin = _pt_re.compile(r"^\s*#\s*(?:live-studio|project-tac):begin\s+(.+?)\s*$", _pt_re.I)
        generated_end = _pt_re.compile(r"^\s*#\s*(?:live-studio|project-tac):end\s+(.+?)\s*$", _pt_re.I)
        open_regions = {}
        for index, line in enumerate(lines):
            line_number = index + 1
            for kind, regex in patterns:
                match = regex.match(line)
                if match:
                    end_line = _pt_block_end(lines, index) if line.rstrip().endswith(":") else line_number
                    records.append(_pt_source_record(kind, match.group(1).strip(), rel_path, line_number, end_line))
                    break
            for kind, regex in calls:
                match = regex.search(line)
                if match:
                    records.append(_pt_source_record(kind, match.group(1).strip(), rel_path, line_number, line_number))
            match = generated_begin.match(line)
            if match:
                open_regions[match.group(1).strip()] = line_number
            match = generated_end.match(line)
            if match:
                region_id = match.group(1).strip()
                start = open_regions.pop(region_id, line_number)
                records.append(_pt_source_record("generated_region", region_id, rel_path, start, line_number))
            for match in _pt_re.finditer(r"live[_ -]?studio[_ -]id\s*[:=]\s*[\"']?([A-Za-z_][A-Za-z0-9_\-]*)", line, _pt_re.I):
                records.append(_pt_source_record("studio_object_id", match.group(1), rel_path, line_number, line_number))
        return {"path": rel_path, "signature": pt_file_signature(rel_path), "records": records, "lines": len(lines)}

    def pt_build_source_index(force=False):
        rows = pt_file_rows(force)
        signature = pt_project_signature(rows)
        cached = runtime.get("project_tac_source_index")
        if not force and cached and cached.get("signature") == signature:
            return cached
        files = {}
        by_kind = {}
        by_id = {}
        errors = []
        for row in rows:
            rel = row.get("path")
            if not rel:
                continue
            try:
                record = pt_scan_source_file(rel)
                files[rel] = record
                for item in record.get("records", []):
                    by_kind.setdefault(item.get("kind"), []).append(item)
                    by_id.setdefault(item.get("id"), []).append(item)
            except Exception as exc:
                errors.append({"file": rel, "error": repr(exc)})
                log_diagnostic("warning", "Project Tac source file could not be indexed", {"file": rel}, system="project_tac", operation="source_index", category="runtime_inspection", exception=exc)
        index = {
            "signature": signature,
            "created_at": int(_pt_time.time()),
            "files": files,
            "by_kind": by_kind,
            "by_id": by_id,
            "errors": errors,
            "engine": pt_engine_descriptor(),
        }
        runtime["project_tac_source_index"] = index
        metadata = ensure_project().setdefault("project", {}).setdefault("extension_information", {})
        metadata["project_tac"] = {
            "extension_version": PROJECT_TAC_EXTENSION_VERSION,
            "source_signature": signature,
            "indexed_at": index["created_at"],
            "engine": clone(index["engine"]),
        }
        ensure_project().setdefault("project", {})["engine_version"] = index["engine"].get("engine_version")
        return index

    def pt_source_index_report():
        index = pt_build_source_index(False)
        lines = [
            "Project Tac Source Index",
            "Signature: {}".format(index.get("signature")),
            "Files: {}".format(len(index.get("files", {}))),
            "Errors: {}".format(len(index.get("errors", []))),
            "",
        ]
        for kind in sorted(index.get("by_kind", {})):
            lines.append("{}: {}".format(kind, len(index["by_kind"][kind])))
        duplicates = {object_id: rows for object_id, rows in index.get("by_id", {}).items() if len(rows) > 1}
        if duplicates:
            lines.append("")
            lines.append("Repeated identifiers (some may be valid across kinds):")
            for object_id, records in sorted(duplicates.items())[:100]:
                locations = ", ".join("{}:{} ({})".format(row.get("file"), row.get("line"), row.get("kind")) for row in records)
                lines.append("{} -> {}".format(object_id, locations))
        return "\n".join(lines)

    def pt_source_object(kind, object_id):
        index = pt_build_source_index(False)
        return [row for row in index.get("by_kind", {}).get(kind, []) if row.get("id") == object_id]

    def pt_text_hash(text):
        return _pt_hashlib.sha256(str(text or "").encode("utf-8", "replace")).hexdigest()

    def pt_unique_backup_path(path):
        directory = _pt_os.path.join(_pt_os.path.dirname(path), "Backup", "LiveStudio")
        if not _pt_os.path.isdir(directory):
            _pt_os.makedirs(directory)
        stamp = _pt_time.strftime("%Y%m%d_%H%M%S") + "_{:03d}_{}".format(
            int((_pt_time.time() % 1.0) * 1000), _pt_uuid.uuid4().hex[:8]
        )
        return _pt_os.path.join(directory, "{}__{}".format(stamp, _pt_os.path.basename(path)))

    def pt_prepare_change(rel_path, new_text, operation="replace", group="default", allow_create=False):
        rel_path = str(rel_path or "").replace("\\", "/")
        if not rel_path:
            raise Exception("Choose a target file first.")
        if not pt_file_editable(rel_path):
            raise Exception("This file is indexed for reference only: {}".format(rel_path))
        path = pt_abs_path(rel_path)
        exists = _pt_os.path.isfile(path)
        if not exists and not allow_create:
            raise Exception("Target file does not exist: {}".format(rel_path))
        original = ""
        if exists:
            with open(path, "r", encoding="utf-8", errors="replace") as source:
                original = source.read()
        new_text = str(new_text)
        return {
            "id": new_id("source_change"),
            "group": str(group or "default"),
            "operation": str(operation or "replace"),
            "rel_path": rel_path,
            "path": path,
            "exists": exists,
            "allow_create": bool(allow_create),
            "original": original,
            "new_text": new_text,
            "previous_hash": pt_text_hash(original),
            "new_hash": pt_text_hash(new_text),
            "changed": original != new_text,
        }

    def pt_change_diff(change, context=3):
        original = str(change.get("original", "")).splitlines(True)
        updated = str(change.get("new_text", "")).splitlines(True)
        return "".join(_pt_difflib.unified_diff(
            original, updated,
            fromfile=change.get("rel_path", "source") + " (current)",
            tofile=change.get("rel_path", "source") + " (proposed)",
            n=int(context or 3),
        ))

    def pt_validate_change(change):
        errors = []
        warnings = []
        rel = change.get("rel_path", "")
        text = change.get("new_text", "")
        if "\x00" in text:
            errors.append("{} contains a null byte.".format(rel))
        if not rel.lower().endswith(".rpy"):
            warnings.append("{} is not a Ren'Py source file.".format(rel))
        # Conservative structural checks that do not require importing Ren'Py's parser.
        labels = _pt_re.findall(r"(?m)^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:", text)
        screens = _pt_re.findall(r"(?m)^\s*screen\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:", text)
        if len(labels) != len(set(labels)):
            errors.append("{} contains duplicate labels.".format(rel))
        if len(screens) != len(set(screens)):
            errors.append("{} contains duplicate screens.".format(rel))
        return {"errors": errors, "warnings": warnings}

    def _pt_prospective_source_validation(prepared):
        """Validate unique source symbols against the complete proposed project.

        Per-file validation cannot catch a label or screen duplicated in another
        file. Build a prospective symbol table by replacing changed files in the
        current source index with their planned text, then validate direct calls
        and jumps from the changed files against that table.
        """
        errors = []
        warnings = []
        changed_by_rel = {str(row.get("rel_path") or "").replace("\\", "/"): row for row in prepared or []}
        index = pt_build_source_index(False)
        symbols = {"label": {}, "screen": {}}

        def add_symbol(kind, name, rel, line=0):
            if not name:
                return
            symbols.setdefault(kind, {}).setdefault(str(name), []).append({"file": rel, "line": int(line or 0)})

        for rel, file_record in (index.get("files", {}) or {}).items():
            normalized = str(rel or "").replace("\\", "/")
            if normalized in changed_by_rel:
                continue
            for record in file_record.get("records", []) or []:
                if record.get("kind") in ("label", "screen"):
                    add_symbol(record.get("kind"), record.get("id"), normalized, record.get("line"))

        direct_targets = []
        for rel, change in changed_by_rel.items():
            text = str(change.get("new_text", ""))
            for match in _pt_re.finditer(r"(?m)^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:", text):
                add_symbol("label", match.group(1), rel, text.count("\n", 0, match.start()) + 1)
            for match in _pt_re.finditer(r"(?m)^\s*screen\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:", text):
                add_symbol("screen", match.group(1), rel, text.count("\n", 0, match.start()) + 1)
            for match in _pt_re.finditer(r"(?m)^\s*(jump|call)\s+(?!screen\b)([A-Za-z_][A-Za-z0-9_]*)\b", text):
                target = match.group(2)
                if target != "expression":
                    direct_targets.append({"kind": match.group(1), "target": target, "file": rel, "line": text.count("\n", 0, match.start()) + 1})

        for kind in ("label", "screen"):
            for name, locations in symbols.get(kind, {}).items():
                if len(locations) > 1:
                    rendered = ", ".join("{}:{}".format(row.get("file"), row.get("line")) for row in locations[:8])
                    errors.append("Duplicate {} '{}' in prospective project: {}.".format(kind, name, rendered))

        known_labels = set(symbols.get("label", {}))
        for row in direct_targets:
            target = row.get("target")
            exists = target in known_labels
            if not exists:
                try:
                    exists = bool(renpy.has_label(target))
                except Exception:
                    exists = False
            if not exists:
                errors.append("{}:{} {} target '{}' does not exist in the prospective project.".format(row.get("file"), row.get("line"), row.get("kind"), target))
        return {"errors": errors, "warnings": warnings}

    def pt_prepare_change_group(changes, group_id=None):
        prepared = [change for change in changes or [] if change]
        group_id = str(group_id or new_id("change_group"))
        validation = {"errors": [], "warnings": []}
        seen_paths = set()
        for change in prepared:
            normalized_path = _pt_os.path.normcase(_pt_os.path.abspath(change.get("path", "")))
            if normalized_path in seen_paths:
                validation["errors"].append("Source transaction contains the same target more than once: {}".format(change.get("rel_path")))
            seen_paths.add(normalized_path)
            result = pt_validate_change(change)
            validation["errors"].extend(result.get("errors", []))
            validation["warnings"].extend(result.get("warnings", []))
        prospective = _pt_prospective_source_validation(prepared)
        validation["errors"].extend(prospective.get("errors", []))
        validation["warnings"].extend(prospective.get("warnings", []))
        # Keep reports readable when overlapping validators find the same issue.
        validation["errors"] = list(dict.fromkeys(validation["errors"]))
        validation["warnings"] = list(dict.fromkeys(validation["warnings"]))
        plan = {
            "id": group_id,
            "created_at": int(_pt_time.time()),
            "changes": prepared,
            "validation": validation,
            "blocked": bool(validation["errors"]),
        }
        runtime["project_tac_change_plan"] = plan
        return plan

    def pt_apply_change_group(changes, group_id=None):
        plan = changes if isinstance(changes, dict) and "changes" in changes else pt_prepare_change_group(changes, group_id)
        if plan.get("blocked"):
            raise Exception("Source transaction blocked: {}".format("; ".join(plan.get("validation", {}).get("errors", []))))
        changed = [row for row in plan.get("changes", []) if row.get("changed")]
        if not changed:
            plan["applied"] = True
            plan["result"] = {"status": "synchronized", "group": plan.get("id"), "files": []}
            return plan["result"]
        backups = []
        temporaries = []
        replaced = []
        try:
            # Verify every source still matches the previewed version before
            # creating backups or touching any target (TOCTOU protection).
            for row in changed:
                current = ""
                if _pt_os.path.isfile(row.get("path")):
                    with open(row.get("path"), "r", encoding="utf-8", errors="replace") as source:
                        current = source.read()
                if pt_text_hash(current) != row.get("previous_hash"):
                    raise Exception("Source changed after preview: {}. Refresh the plan before applying.".format(row.get("rel_path")))
            # Prepare all final temporary files before touching originals.
            for row in changed:
                parent = _pt_os.path.dirname(row.get("path"))
                if parent and not _pt_os.path.isdir(parent):
                    _pt_os.makedirs(parent)
                temporary = "{}.{}.live_studio_tmp".format(row.get("path"), _pt_uuid.uuid4().hex[:8])
                with open(temporary, "w", encoding="utf-8", newline="") as output:
                    output.write(row.get("new_text", ""))
                    output.flush()
                    try:
                        _pt_os.fsync(output.fileno())
                    except Exception:
                        pass
                temporaries.append((row, temporary))
            # Back up only files that will actually change.
            for row, _temporary in temporaries:
                backup = None
                if row.get("exists"):
                    backup = pt_unique_backup_path(row.get("path"))
                    _pt_shutil.copy2(row.get("path"), backup)
                row["backup"] = backup
                backups.append((row, backup))
            # Atomic replacement per file. Rollback below restores the transaction.
            for row, temporary in temporaries:
                _pt_os.replace(temporary, row.get("path"))
                replaced.append(row)
                with open(row.get("path"), "r", encoding="utf-8", errors="replace") as source:
                    written_hash = pt_text_hash(source.read())
                if written_hash != row.get("new_hash"):
                    raise Exception("Written file hash did not match the prepared result: {}".format(row.get("rel_path")))
            result_files = [{
                "path": row.get("rel_path"), "backup": row.get("backup"),
                "previous_hash": row.get("previous_hash"), "new_hash": row.get("new_hash"),
                "operation": row.get("operation"),
            } for row in changed]
            record_export_history({
                "status": "applied", "operation": "project_tac_transaction",
                "group": plan.get("id"), "files": result_files,
                "validation": plan.get("validation"),
            }) if "record_export_history" in globals() else None
            runtime.pop("project_tac_source_index", None)
            runtime.pop("project_tac_index", None)
            runtime.pop("project_tac_file_rows", None)
            log_diagnostic("info", "Project Tac source transaction applied", {"group": plan.get("id"), "files": result_files}, system="project_tac", operation="source_transaction")
            plan["applied"] = True
            plan["result"] = {"status": "applied", "group": plan.get("id"), "files": result_files}
            return plan["result"]
        except Exception as exc:
            rollback_errors = []
            for row in reversed(replaced):
                backup = row.get("backup")
                try:
                    if backup and _pt_os.path.isfile(backup):
                        _pt_shutil.copy2(backup, row.get("path"))
                    elif not row.get("exists") and _pt_os.path.isfile(row.get("path")):
                        _pt_os.remove(row.get("path"))
                except Exception as rollback_exc:
                    rollback_errors.append({"path": row.get("rel_path"), "error": repr(rollback_exc)})
            log_diagnostic("error", "Project Tac source transaction failed", {"group": plan.get("id"), "rollback_errors": rollback_errors}, system="project_tac", operation="source_transaction", category="source_write", exception=exc, recovery="Backups are stored beside each source file under Backup/LiveStudio.")
            raise
        finally:
            for _row, temporary in temporaries:
                if _pt_os.path.isfile(temporary):
                    try:
                        _pt_os.remove(temporary)
                    except Exception:
                        pass

    def pt_write_file(rel_path, text, allow_create=False):
        change = pt_prepare_change(rel_path, text, "replace", "single_file", allow_create)
        result = pt_apply_change_group([change], "write_{}".format(safe_identifier(rel_path, "file")))
        if result.get("status") == "synchronized":
            return "Already synchronized: {}".format(rel_path)
        row = result.get("files", [{}])[0]
        return "Updated {}\nBackup: {}".format(rel_path, row.get("backup") or "not needed")

    def pt_append_to_file(rel_path, text):
        path = pt_abs_path(rel_path)
        if not _pt_os.path.isfile(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        with open(path, "r", encoding="utf-8", errors="replace") as source:
            original = source.read()
        addition = "\n\n# --- Live Studio Project Tac Insert ---\n" + str(text).rstrip() + "\n"
        updated = original.rstrip() + addition
        change = pt_prepare_change(rel_path, updated, "append", "single_file")
        result = pt_apply_change_group([change], "append_{}".format(safe_identifier(rel_path, "file")))
        if result.get("status") == "synchronized":
            return "Already synchronized: {}".format(rel_path)
        row = result.get("files", [{}])[0]
        return "Updated {}\nBackup: {}".format(rel_path, row.get("backup") or "not needed")

    def pt_replace_in_file(rel_path, old_text, new_text):
        path = pt_abs_path(rel_path)
        if not _pt_os.path.isfile(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        with open(path, "r", encoding="utf-8", errors="replace") as source:
            original = source.read()
        if old_text not in original:
            raise Exception("Could not find the exact source block to replace.")
        updated = original.replace(old_text, new_text, 1)
        change = pt_prepare_change(rel_path, updated, "replace_block", "single_file")
        result = pt_apply_change_group([change], "replace_{}".format(safe_identifier(rel_path, "file")))
        if result.get("status") == "synchronized":
            return "Already synchronized: {}".format(rel_path)
        row = result.get("files", [{}])[0]
        return "Replaced source in {}\nBackup: {}".format(rel_path, row.get("backup") or "not needed")

    _PT_RAW_APPEND_BUILDERS = set((
        "pt_location_template", "pt_dialogue_template", "pt_branch_template",
        "pt_gallery_template", "pt_minigame_template",
    ))

    def pt_command_preview(title, builder):
        before_generation = int(runtime.get("extension_preview_generation", 0))
        text = builder()
        # Typed writers create a source-plan preview themselves. Preserve that
        # metadata instead of downgrading it to a generic report after return.
        if int(runtime.get("extension_preview_generation", 0)) != before_generation:
            return text
        builder_name = getattr(builder, "__name__", "")
        applyable = builder_name in _PT_RAW_APPEND_BUILDERS
        set_extension_preview(
            title, text,
            kind="generated_code" if applyable else "report",
            applyable=applyable,
            metadata={"builder": builder_name, "project_tac": True},
        )
        return text

    def pt_apply_preview(rel_path, text):
        if not rel_path:
            raise Exception("Select a Project Tac source file first.")
        metadata = runtime.get("extension_preview_metadata", {}) or {}
        builder_name = metadata.get("builder")
        if not runtime.get("extension_preview_applyable") or builder_name not in _PT_RAW_APPEND_BUILDERS:
            raise Exception("This preview cannot be appended safely. Use its typed Write command instead.")
        return pt_append_to_file(rel_path, text)

    def pt_structured_validation():
        issues = []
        def add(severity, system, code, object_id, field, message, source=None):
            issues.append({
                "severity": severity, "system": system, "code": code,
                "object_id": str(object_id or ""), "field": str(field or ""),
                "message": str(message), "source": source or {},
            })
        status = pt_capability_status()
        for row in status.get("missing", []):
            add("error", "engine", "capability.missing", row.get("capability"), "capabilities", "Capability '{}' requires version {}, found {}.".format(row.get("capability"), row.get("required"), row.get("actual")))
        index = pt_build_source_index(False)
        for error in index.get("errors", []):
            add("warning", "source_index", "source.unreadable", error.get("file"), "file", error.get("error"), {"file": error.get("file")})
        by_kind = index.get("by_kind", {})
        unique_kinds = ("label", "screen", "quest", "item", "location", "gallery", "minigame")
        for kind in unique_kinds:
            seen = {}
            for row in by_kind.get(kind, []):
                seen.setdefault(row.get("id"), []).append(row)
            for object_id, rows in seen.items():
                if len(rows) > 1:
                    add("error", kind, "{}.duplicate".format(kind), object_id, "id", "Duplicate {} '{}' appears in {} source locations.".format(kind, object_id, len(rows)), rows[0])
        locations = pt_store_dict("locations")
        quests = pt_store_dict("quest_defs")
        items = pt_store_dict("item_defs")
        interactables = pt_store_dict("interactable_defs")
        for quest_id, quest in quests.items():
            targets = []
            if isinstance(quest.get("target"), dict):
                targets.append(("target", quest.get("target")))
            for objective_index, objective in enumerate(quest.get("objectives", []) or []):
                if isinstance(objective, dict) and isinstance(objective.get("target"), dict):
                    targets.append(("objectives[{}].target".format(objective_index), objective.get("target")))
            for field, target in targets:
                location_id = target.get("location")
                if location_id and location_id not in locations:
                    add("error", "quests", "quest.location_missing", quest_id, field + ".location", "Location '{}' does not exist.".format(location_id))
                item_id = target.get("item")
                if item_id and item_id not in items:
                    add("error", "quests", "quest.item_missing", quest_id, field + ".item", "Item '{}' does not exist.".format(item_id))
                object_id = target.get("object")
                if object_id and object_id not in interactables:
                    add("error", "quests", "quest.interactable_missing", quest_id, field + ".object", "Interactable '{}' does not exist.".format(object_id))
        # Location graph and content references.
        for location_id, location in locations.items():
            if not isinstance(location, dict):
                add("error", "locations", "location.invalid", location_id, "definition", "Location definition is not a dictionary.")
                continue
            for index_value, exit_data in enumerate(location.get("exits", []) or []):
                if not isinstance(exit_data, dict):
                    continue
                target_id = exit_data.get("to") or exit_data.get("location")
                if target_id and target_id not in locations:
                    add("error", "locations", "location.exit_missing", location_id, "exits[{}].to".format(index_value), "Exit points to missing location '{}'.".format(target_id))
            for index_value, item_data in enumerate(location.get("items", []) or []):
                if not isinstance(item_data, dict):
                    continue
                item_id = item_data.get("item") or item_data.get("id")
                if item_id and item_id not in items:
                    add("error", "locations", "location.item_missing", location_id, "items[{}]".format(index_value), "Location references missing item '{}'.".format(item_id))
            for index_value, object_data in enumerate(location.get("objects", []) or []):
                if not isinstance(object_data, dict):
                    continue
                object_id = object_data.get("id") or object_data.get("object")
                if object_id and object_id not in interactables:
                    add("warning", "locations", "location.interactable_unregistered", location_id, "objects[{}]".format(index_value), "Object '{}' has no registered interactable definition.".format(object_id))

        # Item and interactable label references. renpy.has_label is queried only
        # when available so this also remains testable outside a full runtime.
        def label_exists(label):
            if not label:
                return True
            try:
                return bool(renpy.has_label(str(label)))
            except Exception:
                return True

        for item_id, item_data in items.items():
            if not isinstance(item_data, dict):
                add("error", "items", "item.invalid", item_id, "definition", "Item definition is not a dictionary.")
                continue
            for field_name in ("use_label", "examine_label"):
                label = item_data.get(field_name)
                if label and not label_exists(label):
                    add("error", "items", "item.label_missing", item_id, field_name, "Label '{}' does not exist.".format(label))

        for interactable_id, interactable in interactables.items():
            if not isinstance(interactable, dict):
                add("error", "interactions", "interactable.invalid", interactable_id, "definition", "Interactable definition is not a dictionary.")
                continue
            seen_actions = set()
            for action_index, action in enumerate(interactable.get("actions", []) or []):
                if not isinstance(action, dict):
                    continue
                action_id = action.get("id")
                if not action_id:
                    add("warning", "interactions", "interactable.action_id_missing", interactable_id, "actions[{}].id".format(action_index), "Action has no stable id.")
                elif action_id in seen_actions:
                    add("error", "interactions", "interactable.action_duplicate", interactable_id, "actions[{}].id".format(action_index), "Duplicate action id '{}'.".format(action_id))
                seen_actions.add(action_id)
                label = action.get("label")
                if label and not label_exists(label):
                    add("error", "interactions", "interactable.label_missing", interactable_id, "actions[{}].label".format(action_index), "Label '{}' does not exist.".format(label))

        runtime["project_tac_validation"] = issues
        counts = {}
        for issue in issues:
            counts[issue.get("severity", "info")] = counts.get(issue.get("severity", "info"), 0) + 1
        runtime["project_tac_validation_counts"] = counts
        return issues

    def pt_validation_report():
        issues = pt_structured_validation()
        if not issues:
            return "No Project Tac validation issues found."
        lines = []
        for issue in issues:
            lines.append("[{severity}] {system} {code} {object_id}.{field}: {message}".format(**issue))
        return "\n".join(lines)

    def pt_validate_project():
        return pt_validation_report()

    def pt_refresh_index():
        runtime.pop("project_tac_index", None)
        runtime.pop("project_tac_source_index", None)
        runtime.pop("project_tac_file_rows", None)
        # Retain the runtime registry snapshot from the original implementation.
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
            "source_index": pt_build_source_index(True),
            "engine": pt_engine_descriptor(),
        }
        runtime["project_tac_index"] = index
        log_diagnostic("info", "Project Tac indexes refreshed", {"files": len(index.get("files", [])), "source_objects": sum(len(rows) for rows in index.get("source_index", {}).get("by_kind", {}).values())}, system="project_tac", operation="refresh_index")
        restart()
        return None

    def pt_summary_rows():
        index = pt_index()
        source_index = pt_build_source_index(False)
        status = pt_capability_status()
        rows = [
            {"label": "Engine", "value": status.get("descriptor", {}).get("engine_version", "unknown")},
            {"label": "Compatibility", "value": "Ready" if status.get("compatible") else "Missing capabilities"},
            {"label": "Current Location", "value": pt_current_location_id() or "unknown"},
            {"label": "Locations", "value": len(index.get("locations", []))},
            {"label": "Quests", "value": len(index.get("quests", []))},
            {"label": "Items", "value": len(index.get("items", []))},
            {"label": "Characters", "value": len(index.get("characters", []))},
            {"label": "Indexed Files", "value": len(source_index.get("files", {}))},
            {"label": "Indexed Objects", "value": sum(len(values) for values in source_index.get("by_kind", {}).values())},
            {"label": "Validation", "value": len(runtime.get("project_tac_validation", []) or [])},
        ]
        return rows

    def pt_source_block(rel_path, line_number, before=0, max_lines=180):
        """Return only the source statement at line_number and its child block.

        The older helper included two preceding context lines and then treated the
        first context line as the editable statement. That could move properties
        into the wrong widget. Context belongs in previews, never in replacement
        ranges.
        """
        path = pt_abs_path(rel_path)
        with open(path, "r", encoding="utf-8", errors="replace") as source:
            lines = source.read().splitlines()
        if not lines:
            return None
        index = min(max(0, int(line_number or 1) - 1), len(lines) - 1)
        if not lines[index].strip():
            # Source locations can occasionally land on a blank line after an
            # autoreload. Search a very small local window, but never cross into
            # an unrelated top-level statement.
            replacement = None
            for candidate in range(index + 1, min(len(lines), index + 4)):
                if lines[candidate].strip():
                    replacement = candidate
                    break
            if replacement is None:
                return None
            index = replacement
        base_indent = pt_line_indent(lines[index])
        end = index + 1
        while end < len(lines) and end - index < int(max_lines or 180):
            current = lines[end]
            if current.strip() and pt_line_indent(current) <= base_indent:
                break
            end += 1
        return {
            "start": index + 1,
            "end": end,
            "lines": lines[index:end],
            "base_indent": base_indent,
            "statement_line": lines[index],
        }

    def _pt_header_code(line):
        result = []
        quote = None
        escaped = False
        for char in str(line):
            if escaped:
                escaped = False
                if quote:
                    result.append(" ")
                else:
                    result.append(char)
                continue
            if char == "\\":
                escaped = True
                result.append(" ")
                continue
            if quote:
                if char == quote:
                    quote = None
                result.append(" ")
                continue
            if char in ("'", '"'):
                quote = char
                result.append(" ")
                continue
            if char == "#":
                break
            result.append(char)
        return "".join(result)

    def _pt_ensure_statement_colon(line):
        text = str(line)
        quote = None
        escaped = False
        comment_index = None
        for index, char in enumerate(text):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if quote:
                if char == quote:
                    quote = None
                continue
            if char in ("'", '"'):
                quote = char
                continue
            if char == "#":
                comment_index = index
                break
        body = text if comment_index is None else text[:comment_index]
        comment = "" if comment_index is None else text[comment_index:]
        if body.rstrip().endswith(":"):
            return text
        whitespace = body[len(body.rstrip()):]
        return body.rstrip() + ":" + whitespace + comment

    def _pt_patch_statement_block(block, patch_lines):
        if not block or not patch_lines:
            return None
        lines = list(block.get("lines") or [])
        if not lines:
            return None
        base_indent = int(block.get("base_indent", pt_line_indent(lines[0])) or 0)
        prop_indent = base_indent + 4
        prop_names = set(line.strip().split(" ", 1)[0] for line in patch_lines if line.strip())
        header_code = _pt_header_code(lines[0])
        inline = [name for name in prop_names if _pt_re.search(r"\b{}\b".format(_pt_re.escape(name)), header_code)]
        if inline:
            raise Exception("Inline properties cannot be patched safely yet: {}. Move them into an indented property block first.".format(", ".join(sorted(inline))))
        lines[0] = _pt_ensure_statement_colon(lines[0])
        kept = [lines[0]]
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and pt_line_indent(line) == prop_indent:
                name = stripped.split(" ", 1)[0]
                if name in prop_names:
                    continue
            kept.append(line)
        insert_at = 1
        while insert_at < len(kept) and not kept[insert_at].strip():
            insert_at += 1
        return kept[:insert_at] + list(patch_lines) + kept[insert_at:]

    def pt_selected_property_patch_change():
        item, _parent, kind = selected_item()
        if not item:
            raise Exception("Select a source-backed UI widget first.")
        if kind != "ui_node":
            raise Exception("Direct property patching currently supports source-backed UI widgets only.")
        if "object_category" in globals() and object_category(item, kind) not in ("source_backed", "runtime_override"):
            raise Exception("The selected object is not source-backed.")
        info = pt_source_info_for_item(item)
        rel = info.get("rel_path")
        line = info.get("line")
        if not rel or not line:
            raise Exception("Selected item has no recoverable source file/line.")
        frame = current_frame() or {}
        overrides = frame.get("changes", {}).get("sets", {}).get(item.get("id"), {}) or {}
        block = pt_source_block(rel, line)
        if not block:
            raise Exception("Could not load the selected source block.")
        patch_lines = pt_property_patch_lines(overrides, block.get("base_indent", 0) + 4)
        if not patch_lines:
            raise Exception("No supported local property overrides are ready to write.")
        new_lines = _pt_patch_statement_block(block, patch_lines)
        original = _pt_read_required(rel)
        source_lines = original.splitlines()
        start = max(0, int(block.get("start", 1)) - 1)
        end = max(start, int(block.get("end", start + 1)))
        expected_lines = list(block.get("lines") or [])
        actual_lines = source_lines[start:end]
        if actual_lines != expected_lines:
            raise Exception("The source block changed after capture. Refresh the source preview before applying.")
        updated_lines = source_lines[:start] + list(new_lines or []) + source_lines[end:]
        updated = "\n".join(updated_lines)
        if original.endswith("\n"):
            updated += "\n"
        change = pt_prepare_change(rel, updated, "property_patch", "selection.property_patch")
        change["source_range"] = [block.get("start"), block.get("end")]
        change["object_id"] = item.get("id")
        change["object_name"] = item.get("name")
        change["expected_block_hash"] = pt_text_hash("\n".join(expected_lines))
        return change

    def pt_selected_property_patch_preview():
        try:
            change = pt_selected_property_patch_change()
        except Exception as exc:
            return "# {}".format(exc)
        diff = pt_change_diff(change)
        return "\n".join([
            "# Property patch preview",
            "# File: {}".format(change.get("rel_path")),
            "# Lines: {}-{}".format(*(change.get("source_range") or ["?", "?"])),
            "# Previous hash: {}".format(change.get("previous_hash")),
            "# New hash: {}".format(change.get("new_hash")),
            "",
            diff or "# Source is already synchronized.",
        ])

    def pt_apply_selected_property_patch():
        try:
            change = pt_selected_property_patch_change()
            plan = pt_prepare_change_group([change], "selection.property_patch")
            return _pt_change_plan_text("Property patch plan", plan)
        except Exception as exc:
            log_diagnostic("error", "Project Tac property patch planning failed", system="project_tac", operation="property_patch_plan", category="source_write", exception=exc, recovery="Refresh the selected source block and review a new unified diff.")
            return "Property patch planning failed: {}".format(exc)

    def _pt_read_required(rel_path):
        path = pt_abs_path(rel_path)
        if not _pt_os.path.isfile(path):
            raise Exception("Target file does not exist: {}".format(rel_path))
        with open(path, "r", encoding="utf-8", errors="replace") as source:
            return source.read()

    def _pt_append_text(original, text):
        addition = "\n\n# --- Live Studio Project Tac Insert ---\n" + str(text).rstrip() + "\n"
        return str(original).rstrip() + addition

    def _pt_insert_into_last_init_text(original, text, rel_path="source"):
        lines = str(original).splitlines()
        init_index = None
        init_pattern = _pt_re.compile(r"^(\s*)init(?:\s+[-+]?\d+)?\s+python(?:\s+in\s+[A-Za-z_][A-Za-z0-9_]*)?\s*:\s*$")
        for index, line in enumerate(lines):
            if init_pattern.match(line):
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
        return "\n".join(lines[:block_end] + insert_lines + lines[block_end:]).rstrip() + "\n"

    def _pt_bracket_delta(line):
        depth = 0
        quote = None
        escaped = False
        for char in str(line):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if quote:
                if char == quote:
                    quote = None
                continue
            if char in ("'", '\"'):
                quote = char
                continue
            if char == "#":
                break
            if char in "[({":
                depth += 1
            elif char in "]) }".replace(" ", ""):
                depth -= 1
        return depth

    def _pt_insert_into_python_list_text(original, list_name, item_text, rel_path="source", fallback_before=None):
        lines = str(original).splitlines()
        pattern = _pt_re.compile(r"^\s*{}\s*=\s*\[".format(_pt_re.escape(list_name)))
        list_start = None
        for index, line in enumerate(lines):
            if pattern.search(line):
                list_start = index
                break
        if list_start is not None:
            depth = 0
            list_end = None
            for index in range(list_start, len(lines)):
                depth += _pt_bracket_delta(lines[index])
                if index > list_start and depth <= 0:
                    list_end = index
                    break
            if list_end is None:
                raise Exception("Could not find the end of {}=[] in {}".format(list_name, rel_path))
            list_indent = pt_line_indent(lines[list_start])
            item_indent = list_indent + 4
            insert_lines = [" " * item_indent + "# --- Live Studio Project Tac Insert ---"]
            insert_lines.extend(pt_indent_text(item_text, item_indent).splitlines())
            return "\n".join(lines[:list_end] + insert_lines + lines[list_end:]).rstrip() + "\n"
        if fallback_before:
            fallback_pattern = _pt_re.compile(r"^\s*{}\s*=\s*[\[\(\{{]".format(_pt_re.escape(fallback_before)))
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
                    return "\n".join(lines[:index] + block + lines[index:]).rstrip() + "\n"
        raise Exception("Could not find {}=[] in {}".format(list_name, rel_path))

    def _pt_change_plan_text(title, plan):
        lines = [
            title,
            "Plan: {}".format(plan.get("id", "pending")),
            "Files: {}".format(len(plan.get("changes", []) or [])),
            "Blocked: {}".format("yes" if plan.get("blocked") else "no"),
        ]
        validation = plan.get("validation", {}) or {}
        for message in validation.get("errors", []) or []:
            lines.append("ERROR: {}".format(message))
        for message in validation.get("warnings", []) or []:
            lines.append("WARNING: {}".format(message))
        for change in plan.get("changes", []) or []:
            lines.extend(["", "=" * 72, "{} · {}".format(change.get("operation", "change"), change.get("rel_path", "source"))])
            if change.get("changed"):
                lines.append(pt_change_diff(change) or "# No textual diff available.")
            else:
                lines.append("# Already synchronized; this file will not be backed up or rewritten.")
        lines.extend(["", "Review the diff, then use Apply Planned Changes in the Project Tac panel."])
        text = "\n".join(lines)
        set_extension_preview(title, text, kind="source_plan", applyable=False, metadata={"plan_id": plan.get("id"), "project_tac": True})
        return text

    def pt_pending_change_plan():
        plan = runtime.get("project_tac_change_plan")
        return plan if isinstance(plan, dict) else None

    def pt_pending_change_status():
        plan = pt_pending_change_plan()
        if not plan:
            return False, "No source change plan is ready."
        if plan.get("applied"):
            return False, "The current source plan has already been applied."
        errors = (plan.get("validation", {}) or {}).get("errors", []) or []
        if errors or plan.get("blocked"):
            return False, "The source plan is blocked by validation errors."
        if not any(change.get("changed") for change in plan.get("changes", []) or []):
            return False, "Every planned file is already synchronized."
        return True, ""

    def pt_apply_pending_change_plan():
        plan = pt_pending_change_plan()
        enabled, reason = pt_pending_change_status()
        if not enabled:
            set_extension_preview("Apply Unavailable", reason, kind="status", applyable=False)
            return reason
        # Re-run structural validation before the transactional TOCTOU/hash checks.
        refreshed = pt_prepare_change_group(plan.get("changes", []), plan.get("id"))
        runtime["project_tac_change_plan"] = refreshed
        if refreshed.get("blocked"):
            text = _pt_change_plan_text("Source Plan Blocked", refreshed)
            return text
        try:
            result = pt_apply_change_group(refreshed)
            text = _pt_transaction_result_text("Project Tac source transaction", result)
            set_extension_preview("Apply Result", text, kind="result", applyable=False, metadata={"plan_id": refreshed.get("id"), "project_tac": True})
            restart()
            return text
        except Exception as exc:
            text = "Source transaction failed: {}".format(exc)
            set_extension_preview("Apply Error", text, kind="error", applyable=False, metadata={"plan_id": refreshed.get("id"), "project_tac": True})
            return text

    def pt_discard_pending_change_plan():
        runtime.pop("project_tac_change_plan", None)
        set_extension_preview("Source Plan", "No Project Tac source plan is pending.", kind="status", applyable=False)
        return None

    def _pt_transaction_result_text(title, result):
        lines = [title, "Status: {}".format(result.get("status", "unknown"))]
        for row in result.get("files", []) or []:
            lines.append("Updated: {}".format(row.get("path")))
            if row.get("backup"):
                lines.append("Backup: {}".format(row.get("backup")))
        return "\n".join(lines)

    def pt_write_quest_template():
        target = pt_project_path("quests_data", "Game/_Data/Quests.rpy")
        original = _pt_read_required(target)
        updated = _pt_insert_into_last_init_text(original, pt_quest_template(), target)
        plan = pt_prepare_change_group([pt_prepare_change(target, updated, "insert_quest", "quest.create")], "quest.create")
        return _pt_change_plan_text("Quest template source plan", plan)

    def pt_write_inventory_template():
        data_target = pt_project_path("items_data", "Game/_Data/Items.rpy")
        content_target = pt_selected_or_default_file(pt_project_path("interaction_default", "Game/Content/Interactions/School/hallway.rpy"), "Game/Content/Interactions/", pt_current_location_file())
        data_original = _pt_read_required(data_target)
        content_original = _pt_read_required(content_target)
        data_updated = _pt_insert_into_last_init_text(data_original, pt_inventory_data_template(), data_target)
        content_updated = _pt_append_text(content_original, pt_inventory_content_template())
        changes = [
            pt_prepare_change(data_target, data_updated, "insert_item", "inventory.create"),
            pt_prepare_change(content_target, content_updated, "append_item_use", "inventory.create"),
        ]
        plan = pt_prepare_change_group(changes, "inventory.create")
        return _pt_change_plan_text("Inventory template source plan", plan)

    def pt_write_dialogue_template():
        target = pt_selected_or_default_file(pt_project_path("dialogue_interact_default", "Game/Content/Dialogue/Interact/Alice.rpy"), "Game/Content/Dialogue/")
        original = _pt_read_required(target)
        updated = _pt_append_text(original, pt_dialogue_template())
        plan = pt_prepare_change_group([pt_prepare_change(target, updated, "append_dialogue", "dialogue.create")], "dialogue.create")
        return _pt_change_plan_text("Dialogue template source plan", plan)

    def pt_write_branch_template():
        target = pt_selected_or_default_file(pt_project_path("story_default", "Game/Content/Story/Act_01/chapter1_intro.rpy"), "Game/Content/Story/")
        original = _pt_read_required(target)
        updated = _pt_append_text(original, pt_branch_template())
        plan = pt_prepare_change_group([pt_prepare_change(target, updated, "append_branch", "branch.create")], "branch.create")
        return _pt_change_plan_text("Branch template source plan", plan)

    def pt_write_gallery_template():
        target = pt_selected_or_default_file(pt_project_path("gallery_content_default", "Game/Content/Dialogue/Interact/Complex_Test_Arc.rpy"), "Game/Content/")
        original = _pt_read_required(target)
        updated = _pt_append_text(original, pt_gallery_template())
        plan = pt_prepare_change_group([pt_prepare_change(target, updated, "append_gallery", "gallery.create")], "gallery.create")
        return _pt_change_plan_text("Gallery template source plan", plan)

    def pt_write_hotspot_template():
        target = pt_selected_or_default_file(pt_project_path("interaction_default", "Game/Content/Interactions/School/hallway.rpy"), "Game/Content/Interactions/", pt_current_location_file())
        parts = pt_hotspot_parts_from_selection()
        if not parts:
            return "# Select an image, UI node, or captured hotspot first."
        original = _pt_read_required(target)
        updated = _pt_insert_into_python_list_text(original, "objects", parts["object"], target, fallback_before="exits")
        updated = _pt_append_text(updated, parts["label"])
        plan = pt_prepare_change_group([pt_prepare_change(target, updated, "insert_hotspot", "hotspot.create")], "hotspot.create")
        return _pt_change_plan_text("Interactable source plan", plan)

    # Upgrade the already-registered extension without copying Project Tac logic
    # into the portable Live Studio core.
    _pt_extension = extension_defs.get("project_tac")
    if _pt_extension is not None:
        _pt_extension["description"] = "Project Tac-native engine authoring, source indexing, validation, and transactional file updates."
        _pt_extension["api_version"] = EXTENSION_API_VERSION
        _pt_extension["capabilities"] = dict(pt_engine_descriptor().get("capabilities", {}) or {})
        _pt_extension["capability_provider"] = lambda: dict(pt_engine_descriptor().get("capabilities", {}) or {})
        _pt_extension["requirements"] = {"source_authoring": 2, "live_studio_sync": 2}
        _pt_extension["summary"] = pt_summary_rows
        _pt_extension["files"] = pt_file_rows
        _pt_extension["file_preview"] = pt_file_preview
        _pt_extension["apply_preview"] = pt_apply_preview
        _seen_commands = set()
        for _command in _pt_extension.get("commands", []) or []:
            _seen_commands.add(_command.get("id"))
            if _command.get("id") == "refresh":
                _command["action"] = pt_refresh_index
            elif _command.get("id") == "validate":
                _command["action"] = lambda: pt_command_preview("Project Tac Validation", pt_validation_report)
            if _command.get("writes"):
                _command["plans_write"] = True
                _command["writes"] = False
                _command.setdefault("requires", {"source_authoring": 2})
                _command.setdefault("extension_api", 2)
                _command["description"] = str(_command.get("description", "")).replace("Back up", "Preview a validated transaction for").replace(" and insert", " and propose inserting").replace(" and append", " and propose appending")
        if "capabilities" not in _seen_commands:
            _pt_extension.setdefault("commands", []).append({
                "id": "capabilities", "title": "Capability Report", "category": "Overview",
                "description": "Compare the running Project Tac engine with this extension's required capabilities.",
                "action": lambda: pt_command_preview("Project Tac Capabilities", pt_capability_report),
            })
        if "source_index" not in _seen_commands:
            _pt_extension.setdefault("commands", []).append({
                "id": "source_index", "title": "Complete Source Index", "category": "Reports",
                "description": "Index labels, screens, transforms, definitions, generated regions, and Studio IDs.",
                "action": lambda: pt_command_preview("Project Tac Source Index", pt_source_index_report),
            })
