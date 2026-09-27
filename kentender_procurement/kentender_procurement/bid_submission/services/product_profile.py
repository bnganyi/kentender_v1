# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`ResolveBidProductProfile` (BDS-CHG-001 v0.8 §4.4.3, §4.4.7): the exact
template family, renderer profile and renderer version this Bid Submission
build can render. There is no fallback: an unknown combination is
`BDS_DEFINITION_UNSUPPORTED` before any bid record exists."""

from __future__ import annotations

from typing import Any

from kentender_procurement.bid_submission.services.errors import fail

#: (template family, renderer profile, renderer version) -> supplier tasks.
SUPPORTED: dict[tuple[str, str, str], int] = {
	("IT-EQUIPMENT-OPEN-V1", "BDS-GOODS-IT-V1", "1.0.0"): 5,
	("IT-EQUIPMENT-OPEN-V1", "BDS-GOODS-IT-V1", "1.1.0"): 5,
}


def resolve(definition: dict[str, Any]) -> dict[str, Any]:
	key = (definition.get("template_family"), definition.get("renderer_profile_id"), definition.get("supported_renderer_version"))
	tasks = SUPPORTED.get(key)
	if tasks is None or len(definition.get("sections") or []) != tasks:
		fail("BDS_DEFINITION_UNSUPPORTED")
	return {"template_family": key[0], "renderer_profile_id": key[1], "supported_renderer_version": key[2], "tasks": tasks}


#: The renderer's headings for the released compositions of BDS-GOODS-IT-V1
#: (STD-TPL-001 §8.2): code-owned presentation, never shown as identities.
#: The official forms a locked declaration composition carries, by the
#: definition's own form id (the PPRA Goods STD Section IV forms this family
#: renders; BDS-CHG-001 v0.8 §10.9 names them for the bidder).
FORM_HEADINGS: dict[str, str] = {
	"FORM-TENDER": "Form of Tender",
	"FORM-CITD": "Independent tender determination",
	"FORM-SD1": "Self-declaration — not debarred",
	"FORM-SD2": "Self-declaration — no corrupt or fraudulent practice",
	"FORM-COE": "Code of ethics commitment",
	"FORM-CBQ": "Confidential business questionnaire",
}

COMPOSITION_HEADINGS: dict[str, str] = {
	"COMP-DOC-ACK": "Addendum acknowledgement",
	"COMP-SUPPLIER-DETAILS": "Tenderer information",
	"COMP-JV-MEMBER": "Joint-venture member",
	"COMP-LOCKED-DECLARATION": "Declaration",
	"COMP-RESERVATION-ELIGIBILITY": "Reservation eligibility",
	"COMP-TENDER-SECURITY": "Tender security",
	"COMP-GOODS-OFFER": "Offered goods",
	"COMP-TECHNICAL-COMPLIANCE": "Technical requirement",
	"COMP-WARRANTY-SUPPORT": "Warranty and support",
	"COMP-EXPERIENCE": "Comparable experience",
	"COMP-RELATED-SERVICES": "Related services",
	"COMP-ACCEPTANCE": "Acceptance",
	"COMP-EVIDENCE-LIST": "Supporting evidence",
	"COMP-GOODS-PRICE": "Goods price",
	"COMP-REVIEW-SIGNATURE": "Signature and confirmation",
}
