# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0500 — DEM schema constants (Cursor pack §11 / std engine §9).

Runtime validation: ``dem.validator.validate_dem_source_traces``.
"""

from __future__ import annotations

from typing import Any

from frappe.model.document import Document

from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)

# Stable title for structural / traceability / prohibited-content validation (tracker §4).
DEM_SCHEMA_INVALID = "DEM_SCHEMA_INVALID"

# Stable title for generation preconditions / unexpected failures (DERIVED-0510).
DEM_GENERATION_FAILED = "DEM_GENERATION_FAILED"

# Pack §11 / §15 — deny manual or hidden evaluation criteria during DEM generation.
MANUAL_EVALUATION_CRITERIA_DENIED = DenialCode.MANUAL_EVALUATION_CRITERIA_DENIED

DEM_STAGE_TYPES: frozenset[str] = frozenset(
	{
		"Responsiveness",
		"Eligibility",
		"Qualification",
		"Technical",
		"Financial",
		"BOQArithmetic",
		"Ranking",
	},
)

DEM_RULE_TYPES: frozenset[str] = frozenset(
	{
		"PresenceCheck",
		"Threshold",
		"PassFail",
		"ArithmeticCorrection",
		"Comparison",
		"Ranking",
		"System",
	},
)

DEM_FAILURE_EFFECTS: frozenset[str] = frozenset(
	{
		"Reject",
		"Clarify",
		"Adjust",
		"RecordOnly",
	},
)

DEM_RANKING_METHODS: frozenset[str] = frozenset(
	{
		"LowestEvaluatedCost",
		"HighestScore",
		"QualityCostBased",
		"Other",
	},
)

# Keys allowed on each evaluation stage row (pack §11).
DEM_STAGE_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"stage_code",
		"stage_name",
		"sequence",
		"stage_type",
		"mandatory",
		"rules",
	},
)

# Keys allowed on each rule row.
DEM_RULE_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"rule_code",
		"rule_type",
		"label",
		"description",
		"data_source",
		"operator",
		"threshold_value",
		"failure_effect",
		"source_trace",
	},
)

DEM_BOQ_ARITHMETIC_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"enabled",
		"stage_code",
		"correction_rules",
	},
)

DEM_CORRECTION_RULE_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"rule_code",
		"label",
		"description",
		"rule_type",
		"source_trace",
	},
)

DEM_RANKING_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"method",
		"source_trace",
	},
)

# Smuggled outcomes / manual criteria — must not appear anywhere in DEM JSON (§9.6).
DEM_PROHIBITED_KEYS: frozenset[str] = frozenset(
	{
		"manual_evaluation_criteria",
		"committee_criteria",
		"hidden_rules",
		"free_form_criteria",
		"award_decision",
		"contract_award",
		"evaluation_score",
		"evaluation_scores",
		"evaluated_price",
		"responsive",
		"non_responsive",
		"responsiveness_outcome",
		"ranking_outcome",
	},
)

DEM_LEGACY_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
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

DEM_OPTIONAL_PACK_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"output_code",
		"tender_code",
		"instance_code",
		"version_number",
	},
)

DEM_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"evaluation_method",
		"stages",
		"boq_arithmetic_correction",
		"ranking",
	},
)

DEM_KNOWN_TOP_LEVEL_KEYS: frozenset[str] = (
	DEM_REQUIRED_TOP_LEVEL_KEYS | DEM_LEGACY_TOP_LEVEL_KEYS | DEM_OPTIONAL_PACK_TOP_LEVEL_KEYS
)

# Trace must tie a rule to STD (§9 / pack §11) — parameter, section, BOQ item, etc., or a named SystemRule.
DEM_STD_TRACE_ANCHOR_KEYS: frozenset[str] = frozenset(
	{
		"source_section_code",
		"source_clause_code",
		"source_parameter_code",
		"source_form_code",
		"source_boq_item_code",
		"source_component_code",
		"source_addendum_code",
	},
)


def build_dem_stub_payload(inst: Document) -> dict[str, Any]:
	"""Valid DEM ``content_json`` — delegates to ``DemGenerator.generateDEM`` (DERIVED-0510)."""
	from kentender_procurement.tender_management.derived_models.dem.generator import DemGenerator

	return DemGenerator.generateDEM(inst.name)
