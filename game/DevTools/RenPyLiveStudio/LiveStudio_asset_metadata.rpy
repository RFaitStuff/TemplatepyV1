# Persistent, automatically-derived asset metadata.
# This does not add artificial browser categories. It enriches the real folder
# tree with data that Project Tac extensions and future authoring tools can use.

init -859 python in live_studio:
    import hashlib as _asset_hashlib
    import json as _asset_json
    import os as _asset_os
    import re as _asset_re
    import time as _asset_time

    ASSET_METADATA_SCHEMA = 1
    ASSET_TIME_VARIANTS = ("day", "afternoon", "evening", "night", "midnight")
    asset_metadata_by_name = {}
    asset_metadata_issues = []
    asset_metadata_signature = ""

    _asset_refresh_without_metadata = refresh_assets

    def _asset_metadata_cache_path():
        try:
            root = _project_storage_root()
        except Exception:
            root = _asset_os.path.join(config.gamedir, PROJECT_DIRECTORY)
        directory = _asset_os.path.join(root, "cache")
        return directory, _asset_os.path.join(directory, "asset_metadata.json")

    def _asset_existing_path(value):
        value = str(value or "").replace("\\", "/").lstrip("/")
        candidates = [
            _asset_os.path.join(config.gamedir, value),
            _asset_os.path.join(_asset_os.path.dirname(config.gamedir), value),
        ]
        for candidate in candidates:
            if _asset_os.path.isfile(candidate):
                return _asset_os.path.abspath(candidate)
        return None

    def _asset_row_signature(rows):
        digest = _asset_hashlib.sha256()
        for item in sorted(rows or [], key=lambda row: (str(row.get("kind", "")), str(row.get("name", "")))):
            digest.update(str(item.get("kind", "")).encode("utf-8", "replace"))
            digest.update(b"\0")
            digest.update(str(item.get("name", "")).encode("utf-8", "replace"))
            digest.update(b"\0")
            sources = item.get("files", []) or ([item.get("name")] if item.get("kind") == "audio" else [])
            for source in sorted(str(value or "").replace("\\", "/") for value in sources):
                digest.update(source.encode("utf-8", "replace"))
                path = _asset_existing_path(source)
                if path:
                    try:
                        stat = _asset_os.stat(path)
                        digest.update(":{}:{}".format(int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1000000000))), int(stat.st_size)).encode("ascii"))
                    except Exception:
                        pass
                digest.update(b"\n")
        return digest.hexdigest()

    def _asset_time_variant(name, sources):
        values = [str(name or "")] + [str(source or "") for source in sources or []]
        pattern = r"(?:^|[_\- ])({})(?:\.[A-Za-z0-9]+)?$".format("|".join(ASSET_TIME_VARIANTS))
        for value in values:
            stem = value.replace("\\", "/").rsplit("/", 1)[-1].lower()
            match = _asset_re.search(pattern, stem)
            if match:
                return match.group(1)
        return None

    def _asset_character_expression(item):
        name = str(item.get("name") or "")
        sources = [str(value or "").replace("\\", "/") for value in item.get("files", []) or []]
        character = None
        expression = None
        for source in sources:
            parts = [part for part in source.split("/") if part]
            lowered = [part.lower() for part in parts]
            for marker in ("characters", "character", "sprites", "sprite"):
                if marker in lowered:
                    index = lowered.index(marker)
                    if index + 1 < len(parts):
                        character = parts[index + 1].rsplit(".", 1)[0]
                        break
            if character:
                break
        name_parts = name.split()
        if character is None and item.get("bucket") == "characters" and name_parts:
            character = name_parts[0]
        if character:
            candidates = list(name_parts[1:])
            if not candidates and sources:
                stem = sources[0].rsplit("/", 1)[-1].rsplit(".", 1)[0]
                prefix = str(character).lower() + "_"
                candidates = [stem[len(prefix):] if stem.lower().startswith(prefix) else stem]
            if candidates:
                expression = "_".join(candidates)
                for suffix in ASSET_TIME_VARIANTS:
                    if expression.lower().endswith("_" + suffix):
                        expression = expression[:-(len(suffix) + 1)]
                        break
        return character, expression

    def _derive_asset_metadata(item):
        sources = list(item.get("files", []) or [])
        kind = str(item.get("kind") or "asset")
        bucket = str(item.get("bucket") or kind)
        character, expression = _asset_character_expression(item)
        metadata_kind = {
            "characters": "character_expression",
            "backgrounds": "background",
            "gui": "ui_image",
        }.get(bucket, "audio" if kind == "audio" else "image")
        existing_sources = []
        for source in sources or ([item.get("name")] if kind == "audio" else []):
            path = _asset_existing_path(source)
            if path:
                existing_sources.append(path)
        return {
            "name": str(item.get("name") or ""),
            "kind": metadata_kind,
            "browser_kind": kind,
            "bucket": bucket,
            "sources": sources,
            "existing_sources": existing_sources,
            "folder": list(item.get("folder", ()) or ()),
            "character": character,
            "expression": expression,
            "time_variant": _asset_time_variant(item.get("name"), sources),
            "generated_at": int(_asset_time.time()),
        }

    def _load_asset_metadata_cache(signature):
        _directory, path = _asset_metadata_cache_path()
        if not _asset_os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as source:
                payload = _asset_json.load(source)
            if int(payload.get("schema", 0) or 0) != ASSET_METADATA_SCHEMA:
                return None
            if payload.get("signature") != signature:
                return None
            metadata = payload.get("metadata")
            return metadata if isinstance(metadata, dict) else None
        except Exception as exc:
            log_diagnostic("warning", "Asset metadata cache could not be read", {"path": path}, system="assets", operation="metadata_cache_read", category="compatibility_fallback", exception=exc)
            return None

    def _save_asset_metadata_cache(signature, metadata, issues):
        directory, path = _asset_metadata_cache_path()
        payload = {
            "format": "renpy_live_studio_asset_metadata",
            "schema": ASSET_METADATA_SCHEMA,
            "signature": signature,
            "saved_at": int(_asset_time.time()),
            "metadata": metadata,
            "issues": issues,
        }
        try:
            if "_atomic_write_json" in globals():
                _atomic_write_json(path, payload)
            else:
                if not _asset_os.path.isdir(directory):
                    _asset_os.makedirs(directory)
                temporary = path + ".tmp"
                with open(temporary, "w", encoding="utf-8") as output:
                    _asset_json.dump(json_safe(payload), output, indent=2, sort_keys=True, ensure_ascii=False)
                    output.write("\n")
                _asset_os.replace(temporary, path)
        except Exception as exc:
            log_diagnostic("warning", "Asset metadata cache could not be written", {"path": path}, system="assets", operation="metadata_cache_write", category="compatibility_fallback", exception=exc)

    def build_asset_metadata(force=False):
        global asset_metadata_by_name, asset_metadata_issues, asset_metadata_signature
        rows = list(asset_cache or []) + list(audio_cache or [])
        signature = _asset_row_signature(rows)
        metadata = None if force else _load_asset_metadata_cache(signature)
        if metadata is None:
            metadata = {}
            for item in rows:
                key = "{}:{}".format(item.get("kind", "asset"), item.get("name", ""))
                metadata[key] = _derive_asset_metadata(item)
        issues = []
        source_owners = {}
        for key, row in metadata.items():
            sources = row.get("sources", []) or []
            if row.get("browser_kind") == "image" and not sources:
                issues.append({"severity": "info", "code": "asset.source_runtime_only", "asset": row.get("name"), "message": "Registered image has no recoverable source file."})
            for source in sources:
                source_owners.setdefault(str(source).lower(), []).append(key)
        for source, owners in source_owners.items():
            if len(owners) > 1:
                issues.append({"severity": "warning", "code": "asset.source_shared", "asset": source, "message": "Source file is registered by multiple image names: {}".format(", ".join(owners[:8]))})
        asset_metadata_by_name = metadata
        asset_metadata_issues = issues
        asset_metadata_signature = signature
        for item in rows:
            key = "{}:{}".format(item.get("kind", "asset"), item.get("name", ""))
            item["metadata"] = clone(metadata.get(key, {}))
        _save_asset_metadata_cache(signature, metadata, issues)
        runtime["asset_metadata_revision"] = int(runtime.get("asset_metadata_revision", 0)) + 1
        runtime["asset_metadata_summary"] = {
            "signature": signature,
            "assets": len(metadata),
            "issues": len(issues),
            "characters": len([row for row in metadata.values() if row.get("character")]),
            "time_variants": len([row for row in metadata.values() if row.get("time_variant")]),
        }
        return metadata

    def refresh_assets(restart_ui=True):
        result = _asset_refresh_without_metadata(False)
        build_asset_metadata(False)
        if restart_ui:
            restart()
        return result

    def asset_metadata_for(name, kind="image"):
        ensure_assets()
        if not asset_metadata_by_name:
            build_asset_metadata(False)
        return asset_metadata_by_name.get("{}:{}".format(kind, name), {})

    def asset_metadata_report():
        ensure_assets()
        if not asset_metadata_by_name:
            build_asset_metadata(False)
        summary = runtime.get("asset_metadata_summary", {})
        lines = [
            "Ren'Py Live Studio Asset Metadata",
            "Signature: {}".format(summary.get("signature", "")),
            "Assets: {}".format(summary.get("assets", 0)),
            "Character expressions: {}".format(summary.get("characters", 0)),
            "Time variants: {}".format(summary.get("time_variants", 0)),
            "Issues: {}".format(summary.get("issues", 0)),
            "",
        ]
        for issue in asset_metadata_issues[:100]:
            lines.append("[{severity}] {code} {asset}: {message}".format(**issue))
        return "\n".join(lines)
