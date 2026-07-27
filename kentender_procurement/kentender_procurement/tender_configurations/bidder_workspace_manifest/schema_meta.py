# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 2 schema preflight: draft declaration, $ref resolution, keyword allowlist."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.registry import (
	SCHEMA_FILES,
	load_schema,
	schemas_dir,
)

JSON_SCHEMA_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

ALLOWED_KEYWORDS: frozenset[str] = frozenset(
	{
		"$schema",
		"$id",
		"$defs",
		"$ref",
		"type",
		"properties",
		"required",
		"additionalProperties",
		"items",
		"enum",
		"const",
		"pattern",
		"format",
		"minLength",
		"title",
		"schema_version",
		"description",
	}
)


class SchemaMetaError(Exception):
	pass


def _iter_schema_nodes(node: Any, path: str = "$"):
	yield path, node
	if isinstance(node, dict):
		for key, value in node.items():
			yield from _iter_schema_nodes(value, f"{path}.{key}")
	elif isinstance(node, list):
		for i, value in enumerate(node):
			yield from _iter_schema_nodes(value, f"{path}[{i}]")


def collect_unsupported_keywords(schema: dict[str, Any]) -> list[str]:
	bad: list[str] = []
	for path, node in _iter_schema_nodes(schema):
		if not isinstance(node, dict):
			continue
		# Only treat keys that look like schema keywords at schema-object positions.
		# Heuristic: object that has type/properties/$ref/$defs or is root-like.
		is_schema_obj = any(
			k in node
			for k in ("type", "properties", "$ref", "$defs", "items", "enum", "const", "additionalProperties")
		) or path == "$"
		if not is_schema_obj:
			continue
		for key in node:
			if key not in ALLOWED_KEYWORDS and not key.startswith("x-"):
				# property names under "properties" are not keywords
				if path.endswith(".properties") or ".properties." in path:
					continue
				# keys inside properties map are field names
				parent_is_props = path.rsplit(".", 1)[-1] == "properties" or path.endswith("properties")
				if parent_is_props:
					continue
				bad.append(f"{path}: {key}")
	# Refine: walk properly — only check keyword positions
	return _collect_unsupported_strict(schema)


def _collect_unsupported_strict(schema: dict[str, Any]) -> list[str]:
	bad: list[str] = []

	def walk(node: Any, path: str, *, in_properties_map: bool = False) -> None:
		if not isinstance(node, dict):
			if isinstance(node, list):
				for i, item in enumerate(node):
					walk(item, f"{path}[{i}]", in_properties_map=False)
			return
		if in_properties_map:
			for prop_name, prop_schema in node.items():
				walk(prop_schema, f"{path}.{prop_name}", in_properties_map=False)
			return
		for key, value in node.items():
			if key not in ALLOWED_KEYWORDS:
				bad.append(f"{path}: unsupported keyword {key!r}")
				continue
			if key == "properties" and isinstance(value, dict):
				walk(value, f"{path}.properties", in_properties_map=True)
			elif key == "$defs" and isinstance(value, dict):
				for def_name, def_schema in value.items():
					walk(def_schema, f"{path}.$defs.{def_name}", in_properties_map=False)
			elif key == "additionalProperties" and isinstance(value, dict):
				walk(value, f"{path}.additionalProperties", in_properties_map=False)
			elif key == "items":
				walk(value, f"{path}.items", in_properties_map=False)
			elif key in ("required", "enum", "type", "const", "pattern", "format", "minLength", "title", "schema_version", "description", "$schema", "$id", "$ref"):
				continue
			else:
				walk(value, f"{path}.{key}", in_properties_map=False)

	walk(schema, "$", in_properties_map=False)
	return bad


def resolve_all_refs(schema: dict[str, Any], *, schema_id: str) -> None:
	"""Ensure every $ref in the schema document resolves (local $defs or common_defs)."""
	common = load_schema("common_defs") if schema_id != "common_defs" else schema
	local_defs = schema.get("$defs") or {}

	for path, node in _iter_schema_nodes(schema):
		if not isinstance(node, dict) or "$ref" not in node:
			continue
		ref = str(node["$ref"])
		if ref.startswith("#/$defs/"):
			name = ref[len("#/$defs/") :]
			if name not in local_defs:
				raise SchemaMetaError(f"{schema_id}{path}: unresolved $ref {ref}")
		elif ref.startswith("common_defs#/$defs/"):
			name = ref.split("/")[-1]
			defs = common.get("$defs") or {}
			if name not in defs:
				raise SchemaMetaError(f"{schema_id}{path}: unresolved $ref {ref}")
		elif ref in SCHEMA_FILES and ref != schema_id:
			# Cross-schema registry id (e.g. submission_policy)
			continue
		else:
			raise SchemaMetaError(f"{schema_id}{path}: unsupported $ref form {ref}")


def assert_draft_declared(schema: dict[str, Any], *, schema_id: str) -> None:
	draft = schema.get("$schema")
	if draft != JSON_SCHEMA_DRAFT_2020_12:
		raise SchemaMetaError(
			f"{schema_id}: $schema must be {JSON_SCHEMA_DRAFT_2020_12!r}, got {draft!r}"
		)


def meta_validate_all_schemas() -> list[str]:
	"""Return list of schema ids validated; raise SchemaMetaError on first hard failure."""
	validated: list[str] = []
	for schema_id in sorted(SCHEMA_FILES.keys()):
		schema = load_schema(schema_id)
		assert_draft_declared(schema, schema_id=schema_id)
		bad = _collect_unsupported_strict(schema)
		if bad:
			raise SchemaMetaError(f"{schema_id}: unsupported keywords: {bad[:5]}")
		resolve_all_refs(schema, schema_id=schema_id)
		validated.append(schema_id)
	return validated


def load_coverage_ledger() -> dict[str, Any]:
	path = Path(__file__).resolve().parent / "fixtures" / "schema_coverage_ledger.json"
	with path.open(encoding="utf-8") as fh:
		return json.load(fh)


def assert_coverage_ledger_complete() -> None:
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
		REQUIRED_PERSISTENCE_CONCEPTS,
	)

	ledger = load_coverage_ledger()
	schema_ids = set(SCHEMA_FILES.keys())
	mapped = set(ledger.get("schema_ids") or [])
	missing = sorted(schema_ids - mapped)
	extra = sorted(mapped - schema_ids)
	if missing or extra:
		raise SchemaMetaError(f"coverage ledger mismatch missing={missing} extra={extra}")
	concepts = ledger.get("persistence_concepts") or {}
	if not concepts:
		raise SchemaMetaError("coverage ledger missing persistence_concepts")
	for concept, meta in concepts.items():
		sid = meta.get("schema_id")
		if sid and sid not in schema_ids:
			raise SchemaMetaError(f"concept {concept} maps to unknown schema_id {sid}")
		if not meta.get("doctype"):
			raise SchemaMetaError(f"concept {concept} missing doctype")
	required_missing = sorted(REQUIRED_PERSISTENCE_CONCEPTS - set(concepts.keys()))
	if required_missing:
		raise SchemaMetaError(
			f"coverage ledger missing required persistence concepts: {required_missing}"
		)
