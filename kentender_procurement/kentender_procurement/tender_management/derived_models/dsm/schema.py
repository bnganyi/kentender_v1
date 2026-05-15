# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0300 — DSM schema constants (Cursor pack §9).

Runtime validation lives in ``dsm.validator``; this module holds typed allow-lists
and stable ``frappe.throw`` titles for schema violations.
"""

from __future__ import annotations

from typing import Any

# Stable title for structural / prohibited-content validation (tracker §4).
DSM_SCHEMA_INVALID = "DSM_SCHEMA_INVALID"

# Stable title for generation preconditions / unexpected failures (DERIVED-0310).
DSM_GENERATION_FAILED = "DSM_GENERATION_FAILED"

DSM_REQUIREMENT_TYPES: frozenset[str] = frozenset(
	{
		"Form",
		"Document",
		"BOQRateEntry",
		"Declaration",
		"TechnicalProposal",
		"Acknowledgement",
		"System",
	},
)

DSM_SUPPLIER_ACTIONS: frozenset[str] = frozenset(
	{
		"CompleteForm",
		"UploadDocument",
		"EnterRates",
		"Acknowledge",
		"Confirm",
		"Declare",
	},
)

# Pack §9 — BOQ rate entry shape (DERIVED-0310 will align generator).
DSM_BOQ_RATE_EDITABLE_FIELDS: frozenset[str] = frozenset({"rate"})
DSM_BOQ_RATE_LOCKED_FIELDS: frozenset[str] = frozenset(
	{"item_number", "description", "unit", "quantity"},
)
DSM_BOQ_RATE_COMPUTED_FIELDS: frozenset[str] = frozenset({"amount"})

# Keys that must not appear anywhere in DSM JSON (arithmetic / evaluation / award).
DSM_PROHIBITED_KEYS: frozenset[str] = frozenset(
	{
		"arithmetic_correction",
		"arithmetic_corrections",
		"boq_arithmetic_correction",
		"responsiveness_outcome",
		"responsiveness",
		"ranking",
		"evaluation_score",
		"evaluation_scores",
		"scoring",
		"award_decision",
		"contract_award",
		"evaluated_price",
		"manual_evaluation_criteria",
	},
)

DSM_REQUIREMENT_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"requirement_code",
		"requirement_type",
		"label",
		"description",
		"mandatory",
		"condition",
		"supplier_action",
		"validation_rule_code",
		"source_trace",
	},
)

DSM_BOQ_RATE_ENTRY_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"enabled",
		"editable_fields",
		"locked_fields",
		"computed_fields",
	},
)

DSM_ADDENDUM_ACK_ALLOWED_KEYS: frozenset[str] = frozenset({"addendum_code", "mandatory"})

# Stub / fingerprint fields allowed alongside pack §9 content (DERIVED-0100 / stubs).
DSM_LEGACY_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"std_inst",
		"output_type",
		"template_version_code",
		"applicability_profile_code",
		"parameter_rows",
		"attachment_rows",
		"works_requirement_rows",
		"has_boq",
	},
)

DSM_OPTIONAL_PACK_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"submission_deadline",
		"submission_mode",
		"output_code",
		"tender_code",
		"instance_code",
		"version_number",
	},
)

DSM_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"requirements",
		"boq_rate_entry",
		"addendum_acknowledgements",
	},
)

DSM_KNOWN_TOP_LEVEL_KEYS: frozenset[str] = (
	DSM_REQUIRED_TOP_LEVEL_KEYS
	| DSM_LEGACY_TOP_LEVEL_KEYS
	| DSM_OPTIONAL_PACK_TOP_LEVEL_KEYS
)


def dsm_default_boq_rate_entry(*, enabled: bool) -> dict[str, Any]:
	"""Pack §9 BOQ rate-entry block (``enabled`` reflects instance BOQ presence in stubs)."""
	return {
		"enabled": bool(enabled),
		"editable_fields": ["rate"],
		"locked_fields": ["item_number", "description", "unit", "quantity"],
		"computed_fields": ["amount"],
	}
