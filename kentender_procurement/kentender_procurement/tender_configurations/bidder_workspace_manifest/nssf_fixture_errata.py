# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NSSF golden fixture errata (directive §4.1–4.3) — expectation layer only.

Does not switch live ``schema_compiler`` / Website checklist projection.
"""

from __future__ import annotations

from typing import Iterable, Sequence

# Exact 10 content sections (canonical §4.1). Lots & Alternatives omitted.
NSSF_CANONICAL_CONTENT_SECTION_KEYS: tuple[str, ...] = (
	"tender_documents_and_addenda",
	"form_of_tender",
	"confidential_business_questionnaire",
	"statutory_declarations",
	"tender_security",
	"preliminary_requirements_and_evidence",
	"qualification_and_capability",
	"technical_proposal_and_implementation_plan",
	"requirements_compliance",
	"price_schedule",
)

NSSF_FORBIDDEN_LEGACY_CONTENT_SECTION_KEYS: frozenset[str] = frozenset(
	{
		"contract_terms_acknowledgement",
		"final_declaration_and_submit",
		# Display / pack-10 aliases that must not appear as content rows
		"contract_conditions_acknowledgement",
		"final_declaration_and_submission",
	}
)

NSSF_SECURITY_DECISION_ID = "NSSF-DEC-SEC-001"

NSSF_LOT_MODEL: dict[str, object] = {
	"mode": "single_scope",
	"bidder_selectable_lots": False,
	"alternatives_permitted": False,
}

NSSF_DEADLINE = "2026-06-30T11:00:00+03:00"

NSSF_EXPECTED_CONTENT_SECTION_COUNT = 10


def assert_nssf_content_sections(keys: Sequence[str] | Iterable[str]) -> list[str]:
	"""Validate a section-key list against NSSF golden errata.

	Raises ValueError on count mismatch, missing required keys, or forbidden legacy keys.
	"""
	ordered = list(keys)
	if len(ordered) != NSSF_EXPECTED_CONTENT_SECTION_COUNT:
		raise ValueError(
			f"NSSF content sections must be exactly {NSSF_EXPECTED_CONTENT_SECTION_COUNT}; "
			f"got {len(ordered)}"
		)
	if tuple(ordered) != NSSF_CANONICAL_CONTENT_SECTION_KEYS:
		missing = [k for k in NSSF_CANONICAL_CONTENT_SECTION_KEYS if k not in ordered]
		extra = [k for k in ordered if k not in NSSF_CANONICAL_CONTENT_SECTION_KEYS]
		raise ValueError(
			"NSSF content section keys do not match canonical errata; "
			f"missing={missing!r} extra={extra!r} order_mismatch={ordered != list(NSSF_CANONICAL_CONTENT_SECTION_KEYS)}"
		)
	forbidden = [k for k in ordered if k in NSSF_FORBIDDEN_LEGACY_CONTENT_SECTION_KEYS]
	if forbidden:
		raise ValueError(f"forbidden legacy content section keys present: {forbidden!r}")
	return ordered


def publication_readiness_requires_security_decision(bound_decision_id: str | None) -> bool:
	"""BWMF-T054 corrected: readiness passes only when NSSF-DEC-SEC-001 is bound."""
	return (bound_decision_id or "").strip() == NSSF_SECURITY_DECISION_ID


def lots_and_alternatives_omitted(lot_model: dict[str, object] | None) -> bool:
	if not isinstance(lot_model, dict):
		return False
	return (
		lot_model.get("mode") == NSSF_LOT_MODEL["mode"]
		and lot_model.get("bidder_selectable_lots") is False
		and lot_model.get("alternatives_permitted") is False
	)
