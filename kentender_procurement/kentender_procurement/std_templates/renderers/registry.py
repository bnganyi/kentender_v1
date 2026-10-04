# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The renderer-adapter registry (STD-TPL-IMP-001 v1.0 §8), keyed by
`renderer_profile_id + supported_renderer_version`.

Each registered version declares one document adapter (Invitation and issued
Tender) and the Bid-Workspace capability set the compiler checks every
released control, composition, validation and named rule against. A release
binds an exact key; a missing, incompatible or unhealthy adapter is
`STD_RENDERER_UNSUPPORTED` and there is no generic fallback.
Pure Python: no Frappe import.
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.renderers.document import DocumentAdapter

BDS_GOODS_IT_V1 = "BDS-GOODS-IT-V1"

_BDS_GOODS_IT_V1_1_0_0_CAPABILITIES: dict[str, Any] = {
	"renderer_profile_id": BDS_GOODS_IT_V1,
	"supported_renderer_version": "1.0.0",
	"controls": [
		"CTL-CONFIRMATION", "CTL-YES-NO", "CTL-SINGLE-CHOICE", "CTL-MULTI-SELECT", "CTL-SHORT-TEXT", "CTL-LONG-TEXT",
		"CTL-INTEGER", "CTL-DECIMAL", "CTL-MONEY", "CTL-DATE", "CTL-EVIDENCE-REFERENCE", "CTL-PORTS-LIST",
	],
	"compositions": [
		"COMP-DOC-ACK", "COMP-SUPPLIER-DETAILS", "COMP-LOCKED-DECLARATION", "COMP-RESERVATION-ELIGIBILITY",
		"COMP-TENDER-SECURITY", "COMP-GOODS-OFFER", "COMP-TECHNICAL-COMPLIANCE", "COMP-WARRANTY-SUPPORT",
		"COMP-EXPERIENCE", "COMP-RELATED-SERVICES", "COMP-ACCEPTANCE", "COMP-EVIDENCE-LIST", "COMP-GOODS-PRICE",
		"COMP-REVIEW-SIGNATURE",
	],
	"validations": [
		"VAL-NONE", "VAL-CONFIRMED", "VAL-TEXT-LENGTH", "VAL-INTEGER-RANGE", "VAL-DECIMAL-RANGE", "VAL-MONEY",
		"VAL-DATE-RANGE", "VAL-OPTION-IN-LIST", "VAL-OPTIONS-SUBSET", "VAL-PORTS", "VAL-EVIDENCE-COUNT",
	],
	"required_rules": ["RQ-ALWAYS", "RQ-NEVER", "RQ-WHEN-FIELD-EQUALS", "RQ-WHEN-ANY-FIELD-EQUALS", "RQ-WHEN-SOURCE-FLAG"],
	"visibility_rules": ["VS-ALWAYS", "VS-WHEN-FIELD-EQUALS", "VS-WHEN-ANY-FIELD-EQUALS"],
	"supplied_value_sources": [],
	"label_parameters": [],
	"repetitions": [],
}

#: 1.1.0 (template release 1.2; BDS-CHG-001 v0.8 OD-E/OD-I): 1.0.0 plus the
#: joint-venture member composition repeated per arrangement member, values
#: Bid Submission supplies read-only, and label parameters it fills at bid time.
_BDS_GOODS_IT_V1_1_1_0_CAPABILITIES: dict[str, Any] = {
	**_BDS_GOODS_IT_V1_1_0_0_CAPABILITIES,
	"supported_renderer_version": "1.1.0",
	"compositions": _BDS_GOODS_IT_V1_1_0_0_CAPABILITIES["compositions"] + ["COMP-JV-MEMBER"],
	"supplied_value_sources": ["SV-ORGANISATION", "SV-ARRANGEMENT", "SV-ARRANGEMENT-MEMBER", "SV-SIGNATORY"],
	"label_parameters": ["bidder_name", "addendum_reference"],
	"repetitions": ["per_arrangement_member"],
}

#: 1.2.0 (template release 1.4; the supplier business profile and bounded
#: tables): 1.1.0 plus the row-group control, the entity-profile composition
#: repeated per entity (the lead organisation and each joint-venture member),
#: and the source of each entity's standing business facts.
_BDS_GOODS_IT_V1_1_2_0_CAPABILITIES: dict[str, Any] = {
	**_BDS_GOODS_IT_V1_1_1_0_CAPABILITIES,
	"supported_renderer_version": "1.2.0",
	"controls": _BDS_GOODS_IT_V1_1_1_0_CAPABILITIES["controls"] + ["CTL-ROW-GROUP"],
	"compositions": _BDS_GOODS_IT_V1_1_1_0_CAPABILITIES["compositions"] + ["COMP-ENTITY-PROFILE"],
	"validations": _BDS_GOODS_IT_V1_1_1_0_CAPABILITIES["validations"] + ["VAL-ROW-GROUP"],
	"supplied_value_sources": _BDS_GOODS_IT_V1_1_1_0_CAPABILITIES["supplied_value_sources"] + ["SV-ENTITY-PROFILE"],
	"repetitions": _BDS_GOODS_IT_V1_1_1_0_CAPABILITIES["repetitions"] + ["per_entity"],
}


def _document(version: str) -> DocumentAdapter:
	return DocumentAdapter(
		renderer_profile_id=BDS_GOODS_IT_V1,
		supported_renderer_version=version,
		engine="wkhtmltopdf",
		engine_version="wkhtmltopdf 0.12.6.1 (with patched qt)",
		page_options=(("page-size", "A4"), ("margin-top", "25mm"), ("margin-bottom", "25mm"), ("margin-left", "20mm"), ("margin-right", "20mm")),
	)

REGISTRY: dict[tuple[str, str], dict[str, Any]] = {
	(BDS_GOODS_IT_V1, "1.0.0"): {"document": _document("1.0.0"), "bid_workspace": _BDS_GOODS_IT_V1_1_0_0_CAPABILITIES},
	(BDS_GOODS_IT_V1, "1.1.0"): {"document": _document("1.1.0"), "bid_workspace": _BDS_GOODS_IT_V1_1_1_0_CAPABILITIES},
	(BDS_GOODS_IT_V1, "1.2.0"): {"document": _document("1.2.0"), "bid_workspace": _BDS_GOODS_IT_V1_1_2_0_CAPABILITIES},
}


def _entry(renderer_profile_id: str, supported_renderer_version: str) -> dict[str, Any]:
	entry = REGISTRY.get((renderer_profile_id, supported_renderer_version))
	if not entry:
		fail(
			"STD_RENDERER_UNSUPPORTED",
			"No renderer adapter is registered for this exact profile and version.",
			identity=f"{renderer_profile_id}@{supported_renderer_version}",
		)
	return entry


def document_adapter(renderer_profile_id: str, supported_renderer_version: str) -> DocumentAdapter:
	return _entry(renderer_profile_id, supported_renderer_version)["document"]


def bid_workspace_capabilities(renderer_profile_id: str, supported_renderer_version: str) -> dict[str, Any]:
	caps = _entry(renderer_profile_id, supported_renderer_version)["bid_workspace"]
	return {k: (list(v) if isinstance(v, list) else v) for k, v in caps.items()}


def is_registered(renderer_profile_id: str, supported_renderer_version: str) -> bool:
	return (renderer_profile_id, supported_renderer_version) in REGISTRY


def health(renderer_profile_id: str, supported_renderer_version: str) -> dict[str, Any]:
	"""Runtime health for one registered key: every adapter kind must be ready."""
	if not is_registered(renderer_profile_id, supported_renderer_version):
		return {"ok": False, "registered": False, "document": None, "bid_workspace": None}
	document = document_adapter(renderer_profile_id, supported_renderer_version).health()
	return {"ok": bool(document["ok"]), "registered": True, "document": document, "bid_workspace": {"ok": True, "declared": True}}
