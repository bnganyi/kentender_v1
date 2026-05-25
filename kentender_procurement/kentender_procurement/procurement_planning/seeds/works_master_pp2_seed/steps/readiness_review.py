# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Review, readiness, and ready-for-release transitions (spec §12–§13)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import frappe
from frappe.utils import add_days, today

from kentender_procurement.procurement_lifecycle.handoff_card_service import create_or_update_handoff_card
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	READINESS_PASSED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDCONF_CODE,
	BUDGET_LINE_CODE,
	DEMAPP_CODE,
	DEMAND_CODE,
	JOURNEY_CODE,
	PKG_CODE,
	SEED_ACTOR,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	get_current_package_readiness_result,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness import (
	ensure_master_readiness_result,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	mark_package_ready_for_release,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.method_decision import (
	sync_master_method_decision_approval,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.review import (
	ensure_master_review_decision,
)


def _ensure_upstream_handoffs() -> None:
	for handoff_code, title, source_mod, target_mod, src_type, src_code in (
		(
			DEMAPP_CODE,
			"Demand Approval Certificate",
			"Demand Intake and Approval",
			"Procurement Planning",
			"Demand",
			DEMAND_CODE,
		),
		(
			BUDCONF_CODE,
			"Budget Funding Confirmation",
			"Budget",
			"Demand Intake and Approval",
			"Budget Line",
			BUDGET_LINE_CODE,
		),
	):
		create_or_update_handoff_card(
			{
				"handoff_code": handoff_code,
				"handoff_title": title,
				"journey_code": JOURNEY_CODE,
				"source_module": source_mod,
				"target_module": target_mod,
				"status": "Consumed",
				"next_action": "Proceed to procurement planning.",
				"source_object_type": src_type,
				"source_object_code": src_code,
				"is_master_seed": 1,
			}
		)


def _ensure_schedule() -> None:
	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{"schedule_start": today(), "schedule_end": add_days(today(), 30)},
		update_modified=False,
	)


_POST_READY_PACKAGE_STATUSES = frozenset((PKG_READY_FOR_RELEASE, PKG_RELEASED, PKG_CONSUMED))


def ensure_review_readiness_and_ready(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	status = frappe.db.get_value("Procurement Package", PKG_CODE, "status") or ""
	readiness = get_current_package_readiness_result(PKG_CODE) or {}
	if status in _POST_READY_PACKAGE_STATUSES:
		if status == PKG_READY_FOR_RELEASE and readiness.get("result_status") == READINESS_PASSED:
			sync_master_method_decision_approval()
		return {
			"action": "existing",
			"readiness_code": readiness.get("readiness_code"),
			"status": status,
		}

	_ensure_upstream_handoffs()
	_ensure_schedule()

	if status in ("Draft", "Returned for Correction", "In Review", "Approved"):
		ensure_master_review_decision(actor=actor)

	sync_master_method_decision_approval()

	readiness_out = ensure_master_readiness_result(actor=actor)
	if readiness_out.get("action") == "existing":
		current = get_current_package_readiness_result(PKG_CODE) or {}
		if (current.get("result_status") or "").strip() != READINESS_PASSED:
			frappe.throw(
				"Package readiness checks did not pass.",
				title="READINESS_FAILED",
			)

	mark_package_ready_for_release(PKG_CODE, actor)
	readiness = get_current_package_readiness_result(PKG_CODE) or {}
	return {
		"action": "created",
		"readiness_code": readiness.get("readiness_code"),
		"status": PKG_READY_FOR_RELEASE,
	}
