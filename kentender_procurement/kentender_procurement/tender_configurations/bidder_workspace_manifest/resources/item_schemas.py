# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Closed canonical item field sets per resource type (Phase 4 oracle recovery).

Excludes extraction-only / environment fields. Source lineage is retained separately
via source_refs on the resource descriptor.
"""

from __future__ import annotations

from typing import Any

# resource_id -> (resource_type, collection_name, identity_key, ordering_keys, allowed_fields)
NSSF_RESOURCE_SPECS: dict[str, dict[str, Any]] = {
	"RESOURCE-NSSF-REQUIREMENT-GROUPS": {
		"resource_type": "requirement_group",
		"collection": "requirement_groups",
		"schema_ref": "bwmf/item/requirement_group",
		"schema_version": "1.0.0",
		"identity_key": "group_key",
		"ordering_contract": ["order_weight", "group_key"],
		"fields": ("group_key", "order_weight", "label"),
	},
	"RESOURCE-NSSF-REQUIREMENTS": {
		"resource_type": "requirement",
		"collection": "requirements",
		"schema_ref": "bwmf/item/requirement",
		"schema_version": "1.0.0",
		"identity_key": "requirement_key",
		"ordering_contract": ["order_weight", "requirement_key"],
		"fields": (
			"requirement_key",
			"group_key",
			"order_weight",
			"mandatory",
			"contract_carry_forward",
		),
	},
	"RESOURCE-NSSF-PRELIMINARY-CRITERIA": {
		"resource_type": "preliminary_criterion",
		"collection": "preliminary_criteria",
		"schema_ref": "bwmf/item/preliminary_criterion",
		"schema_version": "1.0.0",
		"identity_key": "criterion_key",
		"ordering_contract": ["order_weight", "criterion_key"],
		"fields": ("criterion_key", "order_weight", "label"),
	},
	"RESOURCE-NSSF-QUALIFICATION-CRITERIA": {
		"resource_type": "qualification_criterion",
		"collection": "qualification_criteria",
		"schema_ref": "bwmf/item/qualification_criterion",
		"schema_version": "1.0.0",
		"identity_key": "criterion_key",
		"ordering_contract": ["order_weight", "criterion_key"],
		"fields": ("criterion_key", "order_weight", "label"),
	},
	"RESOURCE-NSSF-TECHNICAL-SCORING": {
		"resource_type": "evaluation_criterion",
		"collection": "technical_scoring",
		"schema_ref": "bwmf/item/evaluation_criterion",
		"schema_version": "1.0.0",
		"identity_key": "criterion_key",
		"ordering_contract": ["order_weight", "criterion_key"],
		"fields": ("criterion_key", "order_weight", "max_score"),
	},
	"RESOURCE-NSSF-SCHEDULE": {
		"resource_type": "implementation_schedule_row",
		"collection": "schedule_rows",
		"schema_ref": "bwmf/item/implementation_schedule_row",
		"schema_version": "1.0.0",
		"identity_key": "row_key",
		"ordering_contract": ["order_weight", "row_key"],
		"fields": ("row_key", "order_weight", "label"),
	},
	"RESOURCE-NSSF-PRICE-LINES": {
		"resource_type": "price_line",
		"collection": "price_lines",
		"schema_ref": "bwmf/item/price_line",
		"schema_version": "1.0.0",
		"identity_key": "line_key",
		"ordering_contract": ["order_weight", "line_key"],
		"fields": ("line_key", "order_weight", "label"),
	},
	"RESOURCE-NSSF-CONTRACT-CONDITIONS": {
		"resource_type": "contract_condition",
		"collection": "contract_conditions",
		"schema_ref": "bwmf/item/contract_condition",
		"schema_version": "1.0.0",
		"identity_key": "condition_key",
		"ordering_contract": ["order_weight", "condition_key"],
		"fields": ("condition_key", "order_weight", "label"),
	},
	"RESOURCE-NSSF-DECISIONS": {
		"resource_type": "controlled_decision",
		"collection": "decisions",
		"schema_ref": "bwmf/item/controlled_decision",
		"schema_version": "1.0.0",
		"identity_key": "decision_id",
		"ordering_contract": ["order_weight", "decision_id"],
		"fields": ("decision_id", "order_weight", "status"),
	},
}

NSSF_RESOURCE_ORDER: tuple[str, ...] = tuple(NSSF_RESOURCE_SPECS.keys())

# Forbidden keys never retained in canonical item arrays
FORBIDDEN_ITEM_KEYS: frozenset[str] = frozenset(
	{
		"pdf_page",
		"page",
		"bbox",
		"coordinates",
		"wizard_target",
		"extraction_meta",
		"legacy_schema",
		"db_name",
		"file_path",
		"host",
		"url",
	}
)
