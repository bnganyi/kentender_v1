# Copyright (c) 2026, KenTender and contributors
"""Idempotent Review (STR-UI-13) fixtures — incomplete Draft + transition Draft.

Does not mutate MOH-SP-2026-2030 Active master.
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_strategy.seeds.works_master_strategy_hierarchy import resolve_procuring_entity_moh
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles

REVIEW_BLOCKERS_PLAN_CODE: Final[str] = "MOH-SP-REVIEW-BLOCK"
REVIEW_TX_PLAN_CODE: Final[str] = "MOH-SP-REVIEW-TX"


def ensure_review_blockers_draft(procuring_entity: str | None = None) -> dict[str, Any]:
	"""Draft plan with no hierarchy → Structure blocker (No Programme)."""
	ensure_strategy_roles()
	pe = procuring_entity or resolve_procuring_entity_moh()
	if not pe:
		return {"ok": False, "reason": "no-procuring-entity", "plan": None, "plan_code": REVIEW_BLOCKERS_PLAN_CODE}

	name = frappe.db.get_value(
		"Strategic Plan",
		{"plan_code": REVIEW_BLOCKERS_PLAN_CODE, "version_number": 1},
		"name",
	)
	if name:
		frappe.db.set_value(
			"Strategic Plan",
			name,
			{"status": "Draft", "return_reason": ""},
			update_modified=False,
		)
		# Ensure no leftover hierarchy from prior experiments
		for dt in (
			"Performance Target",
			"Performance Indicator",
			"Strategic Outcome",
			"Strategy Sub Programme",
			"Strategy Programme",
			"Plan Value Commitment",
		):
			for row in frappe.get_all(dt, filters={"plan_version": name}, pluck="name"):
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": REVIEW_BLOCKERS_PLAN_CODE,
				"version_number": 1,
				"title": "MOH Review Blockers Fixture",
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"status": "Draft",
				"start_date": "2026-07-01",
				"end_date": "2027-06-30",
				"description": "STR-UI-13 blockers canvas fixture (empty structure).",
			}
		)
		doc.insert(ignore_permissions=True)
		name = doc.name

	frappe.db.commit()
	return {
		"ok": True,
		"plan": name,
		"plan_code": REVIEW_BLOCKERS_PLAN_CODE,
		"procuring_entity": pe,
		"status": "Draft",
	}


def ensure_review_transition_draft(procuring_entity: str | None = None) -> dict[str, Any]:
	"""Isolated Draft with minimal ready hierarchy for Submit→…→Activate tests."""
	ensure_strategy_roles()
	pe = procuring_entity or resolve_procuring_entity_moh()
	if not pe:
		return {"ok": False, "reason": "no-procuring-entity", "plan": None, "plan_code": REVIEW_TX_PLAN_CODE}

	name = frappe.db.get_value(
		"Strategic Plan",
		{"plan_code": REVIEW_TX_PLAN_CODE, "version_number": 1},
		"name",
	)
	if name:
		# Wipe and rebuild so status/hierarchy are deterministic
		for dt in (
			"Performance Measurement",
			"Strategy Corrective Action",
			"Plan Value Commitment",
			"Performance Target",
			"Performance Indicator",
			"Strategic Outcome",
			"Strategy Sub Programme",
			"Strategy Programme",
		):
			if not frappe.db.exists("DocType", dt):
				continue
			for row in frappe.get_all(dt, filters={"plan_version": name}, pluck="name"):
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
		frappe.delete_doc("Strategic Plan", name, force=True, ignore_permissions=True)

	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"plan_code": REVIEW_TX_PLAN_CODE,
			"version_number": 1,
			"title": "MOH Review Transition Fixture",
			"procuring_entity": pe,
			"plan_type": "Entity Strategic Plan",
			"status": "Draft",
			"start_date": "2026-07-01",
			"end_date": "2027-06-30",
			"description": "STR-UI-13 transition matrix fixture.",
		}
	)
	plan.insert(ignore_permissions=True)
	name = plan.name

	prog = frappe.get_doc(
		{
			"doctype": "Strategy Programme",
			"programme_code": "REV-PROG-01",
			"title": "Review Transition Programme",
			"plan_version": name,
			"responsible_function": "Digital Health Directorate",
			"order_index": 1,
		}
	).insert(ignore_permissions=True)

	outcome = frappe.get_doc(
		{
			"doctype": "Strategic Outcome",
			"outcome_code": "REV-OUT-01",
			"title": "Review Transition Outcome",
			"plan_version": name,
			"programme": prog.name,
			"responsible_function": "Digital Health Directorate",
			"order_index": 1,
		}
	).insert(ignore_permissions=True)

	ind = frappe.get_doc(
		{
			"doctype": "Performance Indicator",
			"indicator_code": "REV-IND-01",
			"title": "Review Transition Indicator",
			"plan_version": name,
			"strategic_outcome": outcome.name,
			"definition": "Fixture indicator definition",
			"measurement_type": "Percentage",
			"unit": "%",
			"data_source": "Fixture source",
			"responsible_function": "Digital Health Directorate",
			"order_index": 1,
		}
	).insert(ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": "Performance Target",
			"target_code": "REV-TGT-01",
			"title": "Review Transition Target",
			"plan_version": name,
			"performance_indicator": ind.name,
			"baseline_status": "Known",
			"baseline_numeric": 90,
			"baseline_as_of": "2026-01-01",
			"baseline_source": "Fixture baseline",
			"period_start": "2026-07-01",
			"period_end": "2027-06-30",
			"benefit_owner": "Director, Digital Health",
			"measurement_verifier": "Administrator",
			"target_numeric": 95,
			"comparison_direction": "At least",
			"order_index": 1,
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	return {
		"ok": True,
		"plan": name,
		"plan_code": REVIEW_TX_PLAN_CODE,
		"procuring_entity": pe,
		"status": "Draft",
	}
