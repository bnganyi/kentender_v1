# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0400 — DOM schema constants (Cursor pack §10 / std engine §8).

Runtime validation: ``dom.validator.validate_dom_source_traces``.
"""

from __future__ import annotations

from typing import Any

from frappe.model.document import Document

# Stable title for DOM structural / prohibited-content validation (tracker §4).
DOM_SCHEMA_INVALID = "DOM_SCHEMA_INVALID"

# Stable title for DOM generation preconditions / unexpected failures (DERIVED-0410).
DOM_GENERATION_FAILED = "DOM_GENERATION_FAILED"

DOM_FIELD_TYPES: frozenset[str] = frozenset(
	{
		"Text",
		"DateTime",
		"Currency",
		"Boolean",
		"Number",
		"List",
		"System",
	},
)

DOM_DISCLOSURE_STATUSES: frozenset[str] = frozenset(
	{
		"Disclosed",
		"RecordedOnly",
		"Internal",
	},
)

# Pack §10 / std engine §8.3 — canonical ``prohibited_actions`` manifest (order-free).
DOM_PACK_PROHIBITED_ACTIONS: frozenset[str] = frozenset(
	{
		"arithmetic_correction",
		"responsiveness_determination",
		"evaluation_ranking",
	},
)

# Keys that must not appear anywhere in DOM JSON (§8.5 / pack prohibited DOM content).
DOM_PROHIBITED_KEYS: frozenset[str] = frozenset(
	{
		"arithmetic_correction",
		"arithmetic_corrections",
		"boq_arithmetic_correction",
		"responsiveness",
		"responsiveness_outcome",
		"responsiveness_determination",
		"responsive",
		"non_responsive",
		"qualification",
		"qualification_check",
		"qualification_checks",
		"prequalification_outcome",
		"evaluation_ranking",
		"ranking",
		"evaluation_score",
		"evaluation_scores",
		"evaluation_outcome",
		"evaluation_comment",
		"evaluation_comments",
		"scoring",
		"corrected_evaluated_boq_total",
		"manual_evaluation_criteria",
		"stages",
		"rules",
	},
)

DOM_REGISTER_FIELD_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"field_code",
		"label",
		"field_type",
		"mandatory",
		"disclosure_status",
		"source_trace",
	},
)

DOM_LEGACY_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
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

DOM_OPTIONAL_PACK_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"opening_datetime",
		"opening_location",
		"output_code",
		"tender_code",
		"instance_code",
		"version_number",
	},
)

DOM_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"register_fields",
		"prohibited_actions",
	},
)

DOM_KNOWN_TOP_LEVEL_KEYS: frozenset[str] = (
	DOM_REQUIRED_TOP_LEVEL_KEYS | DOM_LEGACY_TOP_LEVEL_KEYS | DOM_OPTIONAL_PACK_TOP_LEVEL_KEYS
)

# Std engine §8.4 / pack §10 — minimum Works opening register (field_code, label, field_type, mandatory, disclosure_status).
DOM_WORKS_REGISTER_BLUEPRINT: tuple[tuple[str, str, str, bool, str], ...] = (
	("bidder_name", "Bidder name", "Text", True, "Disclosed"),
	("submission_timestamp", "Bid submission timestamp", "DateTime", True, "Disclosed"),
	("bid_modification_or_withdrawal", "Bid modification or withdrawal status", "Text", True, "Disclosed"),
	("submitted_total_bid_price", "Submitted total bid price", "Currency", True, "Disclosed"),
	("currency", "Currency", "Text", True, "Disclosed"),
	("tender_security_present", "Tender security present", "Boolean", True, "Disclosed"),
	("addendum_acknowledgement_present", "Addendum acknowledgement present", "Boolean", False, "Disclosed"),
	("opening_committee_attendance", "Opening committee attendance", "List", False, "RecordedOnly"),
	("opening_timestamp", "Opening timestamp", "DateTime", True, "Disclosed"),
	("opening_remarks", "Opening remarks", "Text", False, "RecordedOnly"),
)


def dom_canonical_prohibited_actions() -> list[str]:
	"""Sorted list matching ``DOM_PACK_PROHIBITED_ACTIONS`` (stable JSON)."""
	return sorted(DOM_PACK_PROHIBITED_ACTIONS)


def dom_default_register_fields() -> list[dict[str, Any]]:
	"""Minimal register rows for DERIVED-0400 schema tests (predates richer ``DomGenerator`` traces)."""
	tr_sys: dict[str, str] = {"source_type": "SystemRule"}
	tr_opening: dict[str, str] = {
		"source_type": "Parameter",
		"source_parameter_code": "DATES.OPENING_DATETIME",
	}
	out: list[dict[str, Any]] = []
	for field_code, label, ftype, mandatory, disc in DOM_WORKS_REGISTER_BLUEPRINT:
		trace = tr_opening if field_code == "opening_timestamp" else tr_sys
		out.append(
			{
				"field_code": field_code,
				"label": label,
				"field_type": ftype,
				"mandatory": mandatory,
				"disclosure_status": disc,
				"source_trace": trace,
			},
		)
	return out


def build_dom_stub_payload(inst: Document) -> dict[str, Any]:
	"""Valid DOM ``content_json`` — delegates to ``DomGenerator.generateDOM`` (DERIVED-0410)."""
	from kentender_procurement.tender_management.derived_models.dom.generator import DomGenerator

	return DomGenerator.generateDOM(inst.name)
