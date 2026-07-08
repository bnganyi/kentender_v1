# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0600 — DCM schema constants (Cursor pack §12 / std engine §10).

Runtime validation: ``dcm.validator.validate_dcm_source_traces``.
"""

from __future__ import annotations

from typing import Any

from frappe.model.document import Document

# Stable title for structural / prohibited-content validation (tracker §4).
DCM_SCHEMA_INVALID = "DCM_SCHEMA_INVALID"

DCM_GENERATION_FAILED = "DCM_GENERATION_FAILED"

# Works BOQ — contract price source must follow DEM/Award; no manual override (std engine §10.5).
DCM_MANUAL_PRICE_OVERRIDE_DENIED = "DCM_MANUAL_PRICE_OVERRIDE_DENIED"

DCM_PRICE_SOURCE_TYPES: frozenset[str] = frozenset(
	{
		"CorrectedEvaluatedBOQTotal",
		"AwardPrice",
		"LumpSum",
		"System",
	},
)

DCM_CONTRACT_DOCUMENT_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"document_code",
		"label",
		"description",
		"source_trace",
	},
)

DCM_CONTRACT_TERM_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"term_code",
		"label",
		"value",
		"editable_in_contract",
		"description",
		"source_trace",
	},
)

DCM_PRICE_SOURCE_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"source_type",
		"source_output_code",
		"source_evaluation_result_code",
		"manual_override_allowed",
	},
)

DCM_SECURITIES_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"performance_security",
		"retention",
		"advance_payment_security",
	},
)

DCM_WORKS_SCOPE_ALLOWED_KEYS: frozenset[str] = frozenset(
	{
		"specifications",
		"drawings",
		"boq",
	},
)

# Smuggled contract-formation shortcuts (std engine §10.6 / pack §12).
DCM_PROHIBITED_KEYS: frozenset[str] = frozenset(
	{
		"opening_submitted_total_as_contract_price",
		"use_opening_price_as_contract",
		"silent_scc_override",
		"silent_gcc_override",
		"gcc_free_text_edit",
		"manual_boq_price_override",
		"override_boq_quantities_post_award",
	},
)

DCM_LEGACY_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
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

DCM_OPTIONAL_PACK_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"output_code",
		"tender_code",
		"instance_code",
		"version_number",
		"securities",
		# Pack §19 / DERIVED-1200 — Works BOQ DCM commercial summary (top-level scalars).
		"completion_period_days",
		"defects_liability_period_days",
		"performance_security_percent",
		"retention_percent",
	},
)

DCM_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"contract_documents",
		"contract_terms",
		"price_source",
		"works_scope_references",
	},
)

DCM_KNOWN_TOP_LEVEL_KEYS: frozenset[str] = (
	DCM_REQUIRED_TOP_LEVEL_KEYS | DCM_LEGACY_TOP_LEVEL_KEYS | DCM_OPTIONAL_PACK_TOP_LEVEL_KEYS
)


def build_dcm_stub_payload(inst: Document) -> dict[str, Any]:
	"""Valid DCM ``content_json`` — delegates to ``DcmGenerator.generateDCM`` (DERIVED-0610)."""
	from kentender_procurement.tender_management.derived_models.dcm.generator import DcmGenerator

	return DcmGenerator.generateDCM(inst.name)
