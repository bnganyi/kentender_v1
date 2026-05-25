# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure PLANINCL-MOH-2026-001 exists (spec §8)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_procurement.procurement_lifecycle.handoff_card_service import create_or_update_handoff_card
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	CURRENCY,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	INCLUSION_CODE,
	INCLUSION_FISCAL_YEAR,
	INCLUSION_INCLUDED_AT,
	INCLUSION_NOTE,
	INCLUSION_PROCUREMENT_CATEGORY,
	INCLUSION_STATUS_INCLUDED,
	JOURNEY_CODE,
	PE_CODE,
	PKG_CODE,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	SEED_ACTOR,
	SOURCE_BUDGET_STATUS_AT_INCLUSION,
	SOURCE_DEMAND_STATUS_AT_INCLUSION,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)

_PLANNING_INCLUSION_TITLE = "Planning Inclusion Record"
_HANDOFF_STATUS_INCLUDED = "Handed Off"
_INCLUSION_BUSINESS_STATUS = "Included"
_NEXT_ACTION = "Prepare a procurement package for the approved demand."


def _plan_evidence_link(plan_code: str) -> dict[str, str]:
	return {
		"label": "Procurement Plan",
		"object_type": "Procurement Plan",
		"object_code": plan_code,
		"module": "Procurement Planning",
		"route": f"/desk#Form/Procurement Plan/{plan_code}",
		"visibility": "Internal",
	}


def _strict_inclusion_payload(*, included_by: str) -> dict[str, Any]:
	return {
		"handoff_code": INCLUSION_CODE,
		"handoff_title": _PLANNING_INCLUSION_TITLE,
		"journey_code": JOURNEY_CODE,
		"source_module": "Procurement Planning",
		"target_module": "Procurement Planning",
		"source_object_type": "Demand",
		"source_object_code": DEMAND_CODE,
		"target_object_type": "Procurement Plan",
		"target_object_code": PLAN_CODE,
		"status": _HANDOFF_STATUS_INCLUDED,
		"generated_by": included_by,
		"generated_at": INCLUSION_INCLUDED_AT,
		"next_action": _NEXT_ACTION,
		"locked_summary": {
			"procurement_plan": PLAN_CODE,
			"included_demand": DEMAND_CODE,
			"budget_line": BUDGET_LINE_CODE,
			"demand_item_codes": [DEMAND_ITEM_CODE],
			"inclusion_note": INCLUSION_NOTE,
			"inclusion_status": INCLUSION_STATUS_INCLUDED,
			"procuring_entity_code": PE_CODE,
			"fiscal_year": INCLUSION_FISCAL_YEAR,
			"procurement_category": INCLUSION_PROCUREMENT_CATEGORY,
			"source_demand_status_at_inclusion": SOURCE_DEMAND_STATUS_AT_INCLUSION,
			"source_budget_status_at_inclusion": SOURCE_BUDGET_STATUS_AT_INCLUSION,
		},
		"passed_forward_summary": {
			"package_candidate": PKG_TITLE,
			"category": INCLUSION_PROCUREMENT_CATEGORY,
			"estimated_value": flt(ESTIMATED_VALUE),
			"currency": CURRENCY,
		},
		"evidence_links": [_plan_evidence_link(PLAN_CODE)],
		"technical_refs": {
			"inclusion_code": INCLUSION_CODE,
			"demand_item_codes": [DEMAND_ITEM_CODE],
			"budget_line_code": BUDGET_LINE_CODE,
		},
		"is_master_seed": True,
	}


def _guard_inclusion_package_link_consistency() -> None:
	if not frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE):
		return
	doc = frappe.get_doc("Procurement Handoff Card", INCLUSION_CODE)
	locked = frappe.parse_json(doc.locked_summary or "{}")
	if not isinstance(locked, dict):
		return
	linked = (locked.get("created_package_code") or "").strip()
	if linked and linked != PKG_CODE and frappe.db.exists("Procurement Package", linked):
		frappe.throw(
			f"Inconsistent master seed: inclusion links to {linked}, expected {PKG_CODE}. "
			"Use force_reset=True.",
			title="SEED_INCONSISTENT",
		)


def ensure_planning_inclusion(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	_guard_inclusion_package_link_consistency()
	included_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)
	existed = bool(frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE))
	payload = _strict_inclusion_payload(included_by=included_by)
	result = create_or_update_handoff_card(payload)
	action = "repaired" if existed else result.get("action", "created")
	return {
		"action": action,
		"inclusion_code": INCLUSION_CODE,
	}
