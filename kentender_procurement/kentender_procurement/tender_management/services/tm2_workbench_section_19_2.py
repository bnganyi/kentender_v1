# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §19.2 — canonical tender detail surface for integrations (P9-24).

Maps :func:`~kentender_procurement.tender_management.services.tm2_workbench_tender_detail.get_workbench_tender_detail`
output into the pack's **GET /api/tm2/tenders/{tender_code}** contract (implemented as a desk whitelist method).

Tests: ``tender_management.tests.test_p9_24_workbench_tender_detail_section_19_2``.
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	get_workbench_tender_detail as get_workbench_tender_detail_service,
)


def _readiness_summary(std_readiness: dict[str, Any]) -> dict[str, Any]:
	bind = std_readiness.get("binding") or {}
	meta = std_readiness.get("readiness_meta") or {}
	dem = std_readiness.get("dem_missing_block")
	return {
		"binding_code": bind.get("binding_code") or "",
		"binding_status": bind.get("binding_status") or "",
		"std_readiness_status": meta.get("std_readiness_status") or "",
		"readiness_code": meta.get("readiness_code") or "",
		"readiness_status": meta.get("readiness_status") or "",
		"publication_snapshot_code": bind.get("publication_snapshot_code") or "",
		"dem_missing_block": dem if dem else None,
	}


def _opening_handoff_brief(tab: dict[str, Any]) -> dict[str, Any]:
	return {
		"readiness_status": tab.get("readiness_status") or "",
		"opening_readiness_code": tab.get("opening_readiness_code") or "",
		"closing_record_code": tab.get("closing_record_code") or "",
		"closing_record_status": tab.get("closing_record_status") or "",
		"dom_output_code": tab.get("dom_output_code") or "",
		"valid_sealed_submissions_count": tab.get("valid_sealed_submissions_count"),
		"opening_record_code": tab.get("opening_record_code") or "",
	}


def _evaluation_handoff_brief(tab: dict[str, Any]) -> dict[str, Any]:
	return {
		"handoff_status": tab.get("handoff_status") or "",
		"evaluation_handoff_code": tab.get("evaluation_handoff_code") or "",
		"opening_record_code": tab.get("opening_record_code") or "",
		"dem_output_code": tab.get("dem_output_code") or "",
		"dsm_output_code": tab.get("dsm_output_code") or "",
	}


def _contract_handoff_brief(tab: dict[str, Any]) -> dict[str, Any]:
	return {
		"handoff_status": tab.get("handoff_status") or "",
		"contract_handoff_code": tab.get("contract_handoff_code") or "",
		"award_decision_code": tab.get("award_decision_code") or "",
		"dcm_output_code": tab.get("dcm_output_code") or "",
		"final_evaluated_price_display": tab.get("final_evaluated_price_display") or "",
	}


def build_section_19_2_from_detail(full: dict[str, Any]) -> dict[str, Any]:
	"""Shape ``full`` (``ok`` tender detail dict) into §19.2 keys; caller must ensure ``full['ok']``."""
	ov = full.get("overview") or {}
	ts = ov.get("tender_summary") or {}
	std_readiness = full.get("std_readiness") or {}
	or_tab = full.get("opening_readiness_tab") or {}
	eh_tab = full.get("evaluation_handoff_tab") or {}
	ch_tab = full.get("contract_handoff_tab") or {}

	return {
		"tender_code": full.get("tender_code") or "",
		"tender_title": full.get("tender_title") or "",
		"tender_status": full.get("tender_status") or "",
		"tender_summary": {
			**dict(ts),
			"package_lineage": ov.get("package_lineage") or {},
			"current_state": ov.get("current_state") or {},
			"current_required_action": ov.get("current_required_action") or {},
		},
		"timeline": ov.get("timeline") or {},
		"std_binding": ov.get("std_binding") or {},
		"output_refs": ov.get("output_refs") or {},
		"publication_snapshot": {
			"publication_snapshot_code": ov.get("publication_snapshot_code") or "",
		},
		"blockers": {
			"summary": full.get("blocker_summary") or "",
			"overview_blockers_summary": ov.get("blockers_summary") or "",
		},
		"tab_counts": ov.get("tab_counts") or {},
		"action_availability": full.get("actions") or [],
		"recent_audit_events": ov.get("recent_audit_events") or [],
		"readiness_summary": _readiness_summary(std_readiness),
		"handoff_summaries": {
			"opening_readiness": _opening_handoff_brief(or_tab),
			"evaluation_handoff": _evaluation_handoff_brief(eh_tab),
			"contract_handoff": _contract_handoff_brief(ch_tab),
		},
	}


def get_section_19_2_tender_detail(actor: str, tender_code: str) -> dict[str, Any]:
	"""Return doc 9 §19.2 payload, or the same error dict as workbench detail when not found."""
	full = get_workbench_tender_detail_service(actor, tender_code)
	if not full.get("ok"):
		return full
	return {"ok": True, **build_section_19_2_from_detail(full)}
