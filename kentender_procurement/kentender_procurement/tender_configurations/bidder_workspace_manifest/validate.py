# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Closed-object JSON Schema subset validator (stdlib only; no jsonschema dep)."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.digest import (
	is_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.registry import (
	load_schema,
)


class ManifestSchemaError(Exception):
	"""Raised when an instance fails closed schema validation."""

	def __init__(self, message: str, *, path: str = "$") -> None:
		self.path = path
		super().__init__(f"{path}: {message}" if path else message)


def validate_against_schema(instance: Any, schema_id: str) -> None:
	schema = load_schema(schema_id)
	_validate(instance, schema, path="$", root_schema=schema, schema_id=schema_id)


def _resolve_ref(ref: str, root_schema: dict[str, Any], schema_id: str) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.registry import (
		SCHEMA_FILES,
	)

	if ref.startswith("#/$defs/"):
		name = ref[len("#/$defs/") :]
		defs = root_schema.get("$defs") or {}
		if name not in defs:
			raise ManifestSchemaError(f"unresolved $ref {ref}", path="$")
		target = defs[name]
		if not isinstance(target, dict):
			raise ManifestSchemaError(f"$ref {ref} is not an object schema", path="$")
		return target
	if ref.startswith("common_defs#/$defs/"):
		common = load_schema("common_defs")
		name = ref.split("/")[-1]
		defs = common.get("$defs") or {}
		if name not in defs:
			raise ManifestSchemaError(f"unresolved $ref {ref}", path="$")
		target = defs[name]
		if not isinstance(target, dict):
			raise ManifestSchemaError(f"$ref {ref} is not an object schema", path="$")
		return target
	# Cross-schema registry id (e.g. "submission_policy")
	if ref in SCHEMA_FILES and ref != schema_id:
		target = load_schema(ref)
		if not isinstance(target, dict):
			raise ManifestSchemaError(f"$ref {ref} is not an object schema", path="$")
		return target
	raise ManifestSchemaError(f"unsupported $ref {ref}", path="$")


def _validate(
	instance: Any,
	schema: dict[str, Any],
	*,
	path: str,
	root_schema: dict[str, Any],
	schema_id: str,
) -> None:
	if "$ref" in schema:
		resolved = _resolve_ref(str(schema["$ref"]), root_schema, schema_id)
		merged = {k: v for k, v in schema.items() if k != "$ref"}
		# Prefer resolved schema; overlay non-ref keys from referrer if any.
		effective = {**resolved, **merged} if merged else resolved
		_validate(instance, effective, path=path, root_schema=root_schema, schema_id=schema_id)
		return

	if "const" in schema and instance != schema["const"]:
		raise ManifestSchemaError(f"expected const {schema['const']!r}", path=path)

	if "enum" in schema and instance not in schema["enum"]:
		raise ManifestSchemaError(f"value not in enum {schema['enum']!r}", path=path)

	expected_type = schema.get("type")
	if expected_type is not None:
		_check_type(instance, expected_type, path=path)

	if "pattern" in schema:
		import re

		if not isinstance(instance, str) or not re.fullmatch(str(schema["pattern"]), instance):
			raise ManifestSchemaError(f"does not match pattern {schema['pattern']!r}", path=path)

	if "minLength" in schema:
		if not isinstance(instance, str) or len(instance) < int(schema["minLength"]):
			raise ManifestSchemaError(f"shorter than minLength {schema['minLength']}", path=path)

	# Custom digest format marker used by common_defs Hash
	if schema.get("format") == "sha256-digest" and not is_sha256_digest(instance):
		raise ManifestSchemaError("must be sha256:<64 lowercase hex>", path=path)

	if expected_type == "object" or (expected_type is None and isinstance(instance, dict)):
		if isinstance(instance, dict):
			_validate_object(instance, schema, path=path, root_schema=root_schema, schema_id=schema_id)

	if expected_type == "array" or (expected_type is None and isinstance(instance, list)):
		if isinstance(instance, list):
			items_schema = schema.get("items")
			if isinstance(items_schema, dict):
				for i, item in enumerate(instance):
					_validate(
						item,
						items_schema,
						path=f"{path}[{i}]",
						root_schema=root_schema,
						schema_id=schema_id,
					)


def _check_type(instance: Any, expected: str | list[str], *, path: str) -> None:
	types = expected if isinstance(expected, list) else [expected]
	ok = False
	for t in types:
		if t == "object" and isinstance(instance, dict):
			ok = True
		elif t == "array" and isinstance(instance, list):
			ok = True
		elif t == "string" and isinstance(instance, str):
			ok = True
		elif t == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
			ok = True
		elif t == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool):
			ok = True
		elif t == "boolean" and isinstance(instance, bool):
			ok = True
		elif t == "null" and instance is None:
			ok = True
	if not ok:
		raise ManifestSchemaError(f"expected type {expected!r}, got {type(instance).__name__}", path=path)


def _validate_object(
	instance: dict[str, Any],
	schema: dict[str, Any],
	*,
	path: str,
	root_schema: dict[str, Any],
	schema_id: str,
) -> None:
	properties: dict[str, Any] = schema.get("properties") or {}
	required = schema.get("required") or []
	for key in required:
		if key not in instance:
			raise ManifestSchemaError(f"missing required property {key!r}", path=path)

	additional = schema.get("additionalProperties", True)
	for key, value in instance.items():
		if key in properties:
			_validate(
				value,
				properties[key],
				path=f"{path}.{key}",
				root_schema=root_schema,
				schema_id=schema_id,
			)
			continue
		if additional is False:
			raise ManifestSchemaError(f"unknown property {key!r}", path=path)
		if isinstance(additional, dict):
			_validate(
				value,
				additional,
				path=f"{path}.{key}",
				root_schema=root_schema,
				schema_id=schema_id,
			)
