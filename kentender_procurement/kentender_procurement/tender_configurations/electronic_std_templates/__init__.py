# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Manually curated PPRA IT STD electronic submission templates."""

from __future__ import annotations

from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent
PPRA_IT_STD_V1_PATH = TEMPLATE_DIR / "ppra_it_std_v1.json"
PPRA_IT_STD_V1_APPROVAL_PATH = TEMPLATE_DIR / "ppra_it_std_v1.approval.json"

# Full registry order (F0). Conditional sections may be omitted from a tender snapshot.
# FoT after Price Schedule (electronic workflow); Final Declaration ships later.
CANONICAL_SECTION_KEYS = (
	"tender_documents_and_addenda",
	"lot_and_alternative_selection",
	"confidential_business_questionnaire",
	"statutory_declarations",
	"tender_security",
	"preliminary_requirements_and_evidence",
	"qualification_and_capability",
	"technical_proposal_and_implementation_plan",
	"requirements_compliance",
	"price_schedule",
	"form_of_tender",
)

CONDITIONAL_SECTION_KEYS = frozenset(
	{
		"lot_and_alternative_selection",
		"tender_security",
	}
)

ALLOWED_RENDERERS = frozenset(
	{
		"document_acknowledgement",
		"lot_selection",
		"declaration_form",
		"structured_form",
		"questionnaire",
		"evidence_and_declaration",
		"evidence_matrix",
		"structured_response",
		"requirement_matrix",
		"price_schedule",
		"placeholder",
	}
)

LIFECYCLE_STATUSES = ("Draft", "Reviewed", "Approved", "Retired")

TEMPLATE_ID_PPRA_IT_STD = "PPRA-IT-STD"
TEMPLATE_VERSION_V1 = "1.0"
