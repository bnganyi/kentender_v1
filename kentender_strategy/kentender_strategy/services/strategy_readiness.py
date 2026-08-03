# Copyright (c) 2026, KenTender and contributors
"""REQ §13 plan readiness engine."""

from __future__ import annotations

import frappe
from frappe import _


def get_plan_readiness(plan_name: str) -> dict:
	plan = frappe.get_doc("Strategic Plan", plan_name)
	issues: list[dict] = []

	programmes = frappe.get_all(
		"Strategy Programme",
		filters={"plan_version": plan_name},
		fields=["name", "programme_code", "title", "responsible_function"],
		order_by="order_index asc",
	)
	if not programmes:
		issues.append(
			_issue(
				"Structure",
				"blocker",
				plan_name,
				plan.plan_code,
				"No Programme",
				"Add at least one Programme",
				"strategy-plan-structure",
			)
		)

	outcomes = frappe.get_all(
		"Strategic Outcome",
		filters={"plan_version": plan_name},
		fields=["name", "outcome_code", "title", "programme", "responsible_function"],
	)
	indicators = frappe.get_all(
		"Performance Indicator",
		filters={"plan_version": plan_name},
		fields=[
			"name",
			"indicator_code",
			"title",
			"strategic_outcome",
			"definition",
			"measurement_type",
			"unit",
			"data_source",
			"responsible_function",
		],
	)
	targets = frappe.get_all(
		"Performance Target",
		filters={"plan_version": plan_name},
		fields=[
			"name",
			"target_code",
			"title",
			"performance_indicator",
			"baseline_status",
			"baseline_numeric",
			"baseline_text",
			"baseline_as_of",
			"baseline_source",
			"period_start",
			"period_end",
			"benefit_owner",
			"measurement_verifier",
			"target_numeric",
			"target_text",
			"target_date",
		],
	)

	outcomes_by_prog: dict[str, list] = {}
	for o in outcomes:
		outcomes_by_prog.setdefault(o.programme, []).append(o)

	for p in programmes:
		if not outcomes_by_prog.get(p.name):
			issues.append(
				_issue(
					"Structure",
					"blocker",
					p.name,
					p.programme_code,
					"Programme without an Outcome",
					f"{p.title} has no Strategic Outcome",
					"strategy-plan-structure",
				)
			)
		if not p.responsible_function:
			issues.append(
				_issue(
					"Governance",
					"blocker",
					p.name,
					p.programme_code,
					"Missing responsible function",
					f"{p.title} needs a responsible function",
					"strategy-plan-structure",
				)
			)

	inds_by_out = {}
	for i in indicators:
		inds_by_out.setdefault(i.strategic_outcome, []).append(i)
	tgts_by_ind = {}
	for t in targets:
		tgts_by_ind.setdefault(t.performance_indicator, []).append(t)

	for o in outcomes:
		if not inds_by_out.get(o.name):
			issues.append(
				_issue(
					"Structure",
					"blocker",
					o.name,
					o.outcome_code,
					"Outcome without an Indicator",
					f"{o.title} has no Performance Indicator",
					"strategy-plan-structure",
				)
			)

	for i in indicators:
		if not tgts_by_ind.get(i.name):
			issues.append(
				_issue(
					"Targets",
					"blocker",
					i.name,
					i.indicator_code,
					"Indicator without a Target",
					f"{i.title} has no Performance Target",
					"strategy-plan-structure",
				)
			)
		if not i.definition or not i.data_source or not i.responsible_function:
			issues.append(
				_issue(
					"Targets",
					"blocker",
					i.name,
					i.indicator_code,
					"Incomplete indicator definition",
					f"{i.title} is missing required indicator fields",
					"strategy-plan-structure",
				)
			)
		if i.measurement_type not in ("Milestone", "Boolean") and not i.unit:
			issues.append(
				_issue(
					"Targets",
					"blocker",
					i.name,
					i.indicator_code,
					"Incomplete indicator definition",
					f"{i.title} requires a unit",
					"strategy-plan-structure",
				)
			)

	for t in targets:
		incomplete = False
		if t.baseline_status == "Known" and (
			t.baseline_as_of is None
			or not t.baseline_source
			or (t.baseline_numeric is None and not t.baseline_text)
		):
			incomplete = True
		if not t.period_start or not t.period_end or not t.benefit_owner or not t.measurement_verifier:
			incomplete = True
		if (
			t.target_numeric is None
			and not t.target_text
			and t.target_date is None
		):
			incomplete = True
		if incomplete:
			issues.append(
				_issue(
					"Targets",
					"blocker",
					t.name,
					t.target_code,
					"Incomplete target, baseline or period",
					f"{t.title} is incomplete",
					"strategy-plan-structure",
				)
			)

	# code uniqueness within plan
	_check_unique_codes(issues, "Strategy Programme", plan_name, "programme_code")
	_check_unique_codes(issues, "Strategic Outcome", plan_name, "outcome_code")

	commitments = frappe.get_all(
		"Plan Value Commitment",
		filters={"plan_version": plan_name},
		fields=["name", "rationale", "responsible_owner", "public_value_objective_version"],
	)
	for c in commitments:
		links = frappe.get_all("Plan Value Commitment Link", filters={"parent": c.name})
		if not c.rationale or not c.responsible_owner:
			issues.append(
				_issue(
					"Value Commitments",
					"blocker",
					c.name,
					c.name,
					"Plan Value Commitment without rationale, owner or linked outcome/target",
					"Complete commitment rationale and owner",
					"strategy-plan-value-commitments",
				)
			)
		elif not links:
			issues.append(
				_issue(
					"Value Commitments",
					"blocker",
					c.name,
					c.name,
					"Plan Value Commitment without rationale, owner or linked outcome/target",
					"Link the commitment to an outcome or target",
					"strategy-plan-value-commitments",
				)
			)
		pvo_status = frappe.db.get_value(
			"Public Value Objective", c.public_value_objective_version, "status"
		)
		if pvo_status != "Active":
			issues.append(
				_issue(
					"Value Commitments",
					"blocker",
					c.name,
					c.name,
					"Referenced Public Value Objective not Active at time of selection",
					"Select an Active Public Value Objective",
					"strategy-plan-value-commitments",
				)
			)

	if plan.start_date and plan.end_date and plan.start_date > plan.end_date:
		issues.append(
			_issue(
				"Governance",
				"blocker",
				plan.name,
				plan.plan_code,
				"Invalid effective period",
				"Correct the plan effective period",
				"strategy-plan-overview",
			)
		)

	grouped = {"Structure": [], "Targets": [], "Value Commitments": [], "Governance": []}
	for issue in issues:
		grouped.setdefault(issue["group"], []).append(issue)

	blockers = [i for i in issues if i["severity"] == "blocker"]
	return {
		"plan": _ref(plan.name, plan.plan_code, plan.title),
		"status": plan.status,
		"ready": len(blockers) == 0,
		"blocker_count": len(blockers),
		"warning_count": len([i for i in issues if i["severity"] == "warning"]),
		"issues": issues,
		"grouped": grouped,
	}


def assert_plan_ready_for_submit(plan_name: str) -> None:
	result = get_plan_readiness(plan_name)
	if not result["ready"]:
		frappe.throw(
			_("Plan is not ready for submission ({0} blockers)").format(result["blocker_count"])
		)


def _check_unique_codes(issues, doctype, plan_name, code_field):
	rows = frappe.get_all(
		doctype, filters={"plan_version": plan_name}, fields=["name", code_field]
	)
	seen: dict[str, str] = {}
	for r in rows:
		code = r.get(code_field)
		if not code:
			continue
		if code in seen:
			issues.append(
				_issue(
					"Structure",
					"blocker",
					r.name,
					code,
					"Invalid or duplicate code",
					f"Duplicate code {code}",
					"strategy-plan-structure",
				)
			)
		seen[code] = r.name


def _issue(group, severity, record_id, code, title, message, edit_location):
	return {
		"group": group,
		"severity": severity,
		"record_id": record_id,
		"code": code,
		"title": title,
		"message": message,
		"edit_location": edit_location,
	}


def _ref(id_, code, name):
	return {"id": id_, "code": code, "name": name}
