"""Small JSON-Schema validator for the repository's offline CI path.

The project intentionally keeps the sync runtime dependency-free. This covers
the JSON Schema features used by the checked-in schemas and returns readable
paths; deployments may additionally run the official ``jsonschema`` package.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from omnisource.http import is_http_url


class SchemaIssue(ValueError):
    """A schema validation failure."""


def validate(
    instance: Any,
    schema: dict[str, Any],
    *,
    schema_dir: Path | None = None,
    path: str = "$",
    _root: dict[str, Any] | None = None,
) -> list[str]:
    """Return all validation errors for ``instance`` against ``schema``."""
    root = _root or schema
    schema_dir = schema_dir or Path.cwd()
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if ref.startswith("#/"):
            target: Any = root
            for part in ref[2:].split("/"):
                target = target.get(part) if isinstance(target, dict) else None
            return (
                [f"{path}: unresolved reference {ref}"]
                if not isinstance(target, dict)
                else validate(instance, target, schema_dir=schema_dir, path=path, _root=root)
            )
        target_path = (schema_dir / ref).resolve()
        try:
            target_schema = json.loads(target_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [f"{path}: cannot load {ref}: {error}"]
        return validate(instance, target_schema, schema_dir=target_path.parent, path=path, _root=target_schema)
    if "oneOf" in schema:
        results = [
            validate(instance, option, schema_dir=schema_dir, path=path, _root=root) for option in schema["oneOf"]
        ]
        if any(not errors for errors in results):
            return []
        return [f"{path}: does not match any oneOf schema"]
    if "anyOf" in schema:
        results = [
            validate(instance, option, schema_dir=schema_dir, path=path, _root=root) for option in schema["anyOf"]
        ]
        if any(not errors for errors in results):
            return []
        return [f"{path}: does not match any anyOf schema"]
    if "allOf" in schema:
        errors: list[str] = []
        for option in schema["allOf"]:
            errors.extend(validate(instance, option, schema_dir=schema_dir, path=path, _root=root))
        return errors

    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None and not _type_matches(instance, expected):
        return [f"{path}: expected {expected}, got {_type_name(instance)}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']!r}")
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if isinstance(instance, str):
        if len(instance) < int(schema.get("minLength", 0)):
            errors.append(f"{path}: string is shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and re.search(str(pattern), instance) is None:
            errors.append(f"{path}: string does not match pattern {pattern!r}")
        if schema.get("format") == "uri" and instance and not is_http_url(instance):
            errors.append(f"{path}: invalid HTTP(S) URI")
    if (
        isinstance(instance, (int, float))
        and not isinstance(instance, bool)
        and "minimum" in schema
        and instance < schema["minimum"]
    ):
        errors.append(f"{path}: number is below minimum")
    if isinstance(instance, list):
        if len(instance) < int(schema.get("minItems", 0)):
            errors.append(f"{path}: array has fewer than minItems")
        if schema.get("uniqueItems"):
            try:
                if len({json.dumps(item, sort_keys=True) for item in instance}) != len(instance):
                    errors.append(f"{path}: array items are not unique")
            except TypeError:
                pass
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate(item, item_schema, schema_dir=schema_dir, path=f"{path}[{index}]", _root=root))
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in instance and isinstance(child_schema, dict):
                    errors.extend(
                        validate(instance[key], child_schema, schema_dir=schema_dir, path=f"{path}.{key}", _root=root)
                    )
    return errors


def validate_file(instance: Any, schema_path: Path) -> list[str]:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{schema_path}: cannot load schema: {error}"]
    if not isinstance(schema, dict):
        return [f"{schema_path}: schema root is not an object"]
    return validate(instance, schema, schema_dir=schema_path.parent)


def _type_matches(value: Any, expected: Any) -> bool:
    options = expected if isinstance(expected, list) else [expected]
    return any(
        {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }.get(item, True)
        for item in options
    )


def _type_name(value: Any) -> str:
    return "null" if value is None else type(value).__name__
