# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Schema registry for Bidder Workspace Manifest contract v1."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = "1.0.0"

_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas" / "v1"

# Logical schema id → filename under schemas/v1/
SCHEMA_FILES: dict[str, str] = {
	"common_defs": "common_defs.json",
	"source_binding": "source_binding.json",
	"compile_request": "compile_request.json",
	"manifest_envelope": "manifest_envelope.json",
	"payload_core": "payload_core.json",
	"submission_policy": "submission_policy.json",
	"bindings": "bindings.json",
	"section_group_task_field_collection": "section_group_task_field_collection.json",
	"condition_calculation_ast": "condition_calculation_ast.json",
	"evidence": "evidence.json",
	"validation_diagnostic": "validation_diagnostic.json",
	"dependency_invalidation": "dependency_invalidation.json",
	"role_authority": "role_authority.json",
	"workflow_gates": "workflow_gates.json",
	"resource_descriptor": "resource_descriptor.json",
	"projections": "projections.json",
	"addendum_diff_impact": "addendum_diff_impact.json",
	"response_instance": "response_instance.json",
	"confirmation": "confirmation.json",
	"submission_receipt": "submission_receipt.json",
	"migration_plan_run": "migration_plan_run.json",
}


def schemas_dir() -> Path:
	return _SCHEMAS_DIR


@lru_cache(maxsize=None)
def load_schema(schema_id: str) -> dict[str, Any]:
	if schema_id not in SCHEMA_FILES:
		raise KeyError(f"Unknown schema id: {schema_id}")
	path = _SCHEMAS_DIR / SCHEMA_FILES[schema_id]
	with path.open(encoding="utf-8") as fh:
		data = json.load(fh)
	if not isinstance(data, dict):
		raise ValueError(f"Schema {schema_id} must be a JSON object")
	return data


def list_schema_ids() -> list[str]:
	return sorted(SCHEMA_FILES.keys())
