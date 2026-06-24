"""Small dependency-free validator for akashi fixture parser outputs.

It intentionally covers the subset of lexicon shape used by akashi R0/R1
fixtures: required fields, primitive types, arrays, object refs, const values,
knownValues, and numeric/string bounds.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def validate_record(record: dict[str, Any], lexicon: dict[str, Any]) -> None:
    """Raise ValueError when a record does not match the lexicon main record."""
    schema = lexicon["defs"]["main"]["record"]
    required = schema.get("required", [])
    props = schema["properties"]

    for field in required:
        if field not in record:
            raise ValueError(f"{lexicon['id']}: missing required field {field}")

    for field, value in record.items():
        if field not in props:
            raise ValueError(f"{lexicon['id']}: unknown field {field}")
        _validate_value(
            value,
            props[field],
            lexicon=lexicon,
            path=f"{lexicon['id']}.{field}",
        )


def validate_records(records: Iterable[dict[str, Any]], lexicon: dict[str, Any]) -> None:
    """Validate a sequence of records against one akashi lexicon."""
    for record in records:
        validate_record(record, lexicon)


def _validate_value(
    value: Any,
    schema: dict[str, Any],
    *,
    lexicon: dict[str, Any],
    path: str,
) -> None:
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: expected const {schema['const']!r}")

    if "knownValues" in schema and value not in schema["knownValues"]:
        raise ValueError(f"{path}: unknown value {value!r}")

    schema_type = schema["type"]
    if schema_type == "ref":
        ref_name = schema["ref"].lstrip("#")
        _validate_object(value, lexicon["defs"][ref_name], lexicon=lexicon, path=path)
    elif schema_type == "object":
        _validate_object(value, schema, lexicon=lexicon, path=path)
    elif schema_type == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path}: expected array")
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError(f"{path}: shorter than minLength {schema['minLength']}")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(value):
                _validate_value(
                    item,
                    item_schema,
                    lexicon=lexicon,
                    path=f"{path}[{i}]",
                )
    elif schema_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"{path}: expected string")
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError(f"{path}: longer than maxLength {schema['maxLength']}")
    elif schema_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{path}: expected integer")
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"{path}: above maximum {schema['maximum']}")
    elif schema_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"{path}: expected boolean")
    else:
        raise ValueError(f"{path}: unsupported schema type {schema_type}")


def _validate_object(
    value: Any,
    schema: dict[str, Any],
    *,
    lexicon: dict[str, Any],
    path: str,
) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    props = schema.get("properties", {})
    for field in schema.get("required", []):
        if field not in value:
            raise ValueError(f"{path}: missing required object field {field}")
    for field, child in value.items():
        if field not in props:
            raise ValueError(f"{path}: unknown object field {field}")
        _validate_value(
            child,
            props[field],
            lexicon=lexicon,
            path=f"{path}.{field}",
        )


__all__ = ["validate_record", "validate_records"]
