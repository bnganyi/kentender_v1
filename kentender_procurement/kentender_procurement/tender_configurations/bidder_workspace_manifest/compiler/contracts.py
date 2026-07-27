# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Response vs display contract digests (contract §10.3).

Stable object IDs are independent of display labels/instructions.
Response meaning excludes presentation metadata; display covers labels only.
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)

DISPLAY_KEYS: frozenset[str] = frozenset(
	{
		"label",
		"title",
		"instruction",
		"instructions",
		"help_text",
		"help",
		"description",
		"display_label",
		"alias",
		"provenance_label",
	}
)

# Keys that contribute to response / legal meaning (labels excluded).
RESPONSE_KEYS: frozenset[str] = frozenset(
	{
		"requirement_key",
		"group_key",
		"criterion_key",
		"line_key",
		"row_key",
		"condition_key",
		"decision_id",
		"item_key",
		"section_key",
		"section_instance_id",
		"section_type",
		"mandatory",
		"required",
		"contract_carry_forward",
		"max_score",
		"order_weight",
		"resource_refs",
		"completion_rule_ref",
		"invalidation_policy_ref",
		"response_schema",
		"response_type",
		"field_type",
		"options",
		"option_key",
		"legal_text_ref",
	}
)


def _project_row(row: dict[str, Any], *, keys: frozenset[str]) -> dict[str, Any]:
	return {k: row[k] for k in sorted(row.keys()) if k in keys}


def _project_collections(
	collections: dict[str, Any], *, keys: frozenset[str]
) -> dict[str, list[dict[str, Any]]]:
	out: dict[str, list[dict[str, Any]]] = {}
	for name in sorted(collections.keys()):
		rows = collections.get(name) or []
		projected: list[dict[str, Any]] = []
		for row in rows:
			if isinstance(row, dict):
				projected.append(_project_row(row, keys=keys))
		out[name] = projected
	return out


def compute_object_contracts(
	*,
	collections: dict[str, Any],
	sections: list[dict[str, Any]],
) -> dict[str, str]:
	"""Return aggregate response / display contract digests for the compile graph."""
	response_material = {
		"collections": _project_collections(collections, keys=RESPONSE_KEYS),
		"sections": [_project_row(s, keys=RESPONSE_KEYS) for s in sections if isinstance(s, dict)],
	}
	display_material = {
		"collections": _project_collections(collections, keys=DISPLAY_KEYS | {"requirement_key", "group_key", "criterion_key", "decision_id", "section_key"}),
		"sections": [
			_project_row(s, keys=DISPLAY_KEYS | {"section_key", "section_instance_id"})
			for s in sections
			if isinstance(s, dict)
		],
	}
	return {
		"response_contract_digest": jcs_sha256_digest(response_material),
		"display_contract_digest": jcs_sha256_digest(display_material),
	}
