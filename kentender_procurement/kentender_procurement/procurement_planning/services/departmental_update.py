# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RequestDepartmentalPlanUpdate — the departmental correction route for an
over-budget line (owner decision 26 Sep 2026).

A purchase's cost is copied from the departments' accepted requirements and
cannot be lowered in the plan (§4.6 "no source/quantity/value override").
When a budget line of a Draft plan is over its approved amount, the Planner
has two recovery paths: ask the Budget Officer to revise the line
(`budget_revision`), or ask a department whose requirements make up the line
to update its accepted departmental plan. The department decides — correct
the estimate, change the requirement, or mark it not proceeding this
financial year — through the existing departmental plan update, certified
by its Head of Department and accepted by Procurement. The Planner then
rebuilds the affected Draft purchase from the new accepted source (the
existing source-correction rule flags it).

A request changes no departmental plan, purchase or Plan state. It is
Answered when Procurement accepts that department's next update, and
Withdrawn when the plan update leaves preparation.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, money
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER
from kentender_procurement.procurement_planning.write_family import planning_command

DOCTYPE = "Departmental Plan Update Request"
OPEN = "Open"
ANSWERED = "Answered"
WITHDRAWN = "Withdrawn"


def _new_reference() -> str:
	return f"DUR-{frappe.generate_hash(length=10).upper()}"


def unit_name(organisation_unit: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", organisation_unit, "unit_name") or organisation_unit)


def line_units(plan_version: str) -> dict[str, list[str]]:
	"""The departments (Organisation Units) whose accepted requirements make up
	each budget line of this Version — where a line's cost comes from."""
	rows = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_version": plan_version, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["budget_line", "organisation_unit"],
		limit_page_length=0,
	)
	units: dict[str, set[str]] = {}
	for row in rows:
		if row.budget_line and row.organisation_unit:
			units.setdefault(row.budget_line, set()).add(row.organisation_unit)
	return {line: sorted(group, key=unit_name) for line, group in units.items()}


def open_requests(plan_version: str) -> dict[tuple[str, str], Any]:
	"""Open requests of this Draft Version, keyed by (budget line, unit)."""
	rows = frappe.get_all(
		DOCTYPE,
		filters={"plan_version": plan_version, "status": OPEN},
		fields=["name", "request_reference", "budget_line", "organisation_unit", "requested_at", "over_amount", "budget_line_title"],
		order_by="requested_at asc",
		limit_page_length=0,
	)
	return {(row.budget_line, row.organisation_unit): row for row in rows}


def open_requests_for_plan(departmental_plan: str) -> list[Any]:
	"""A department's open requests (its plan page and My Work)."""
	return frappe.get_all(
		DOCTYPE,
		filters={"departmental_plan": departmental_plan, "status": OPEN},
		fields=["name", "request_reference", "plan_version", "budget_line", "budget_line_title", "budget_line_reference", "over_amount", "requested_by", "requested_at"],
		order_by="requested_at asc",
		limit_page_length=0,
	)


@planning_command
def request_departmental_plan_update(
	*, plan_version: str, budget_line: str, organisation_unit: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""The Planner asks one department to update its accepted departmental
	plan because `budget_line` is over its approved amount. Line, amounts and
	department are checked against the Draft's own allocations."""
	from kentender_procurement.procurement_planning.services import budget_revision

	actor = authz.actor(user)
	payload = {"plan_version": plan_version, "budget_line": budget_line, "organisation_unit": organisation_unit}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	envelope.check_record_version(version, expected_record_version)
	if version.version_status != "Draft":
		fail("PLN_BASELINE_LOCKED")

	line = budget_revision._line_statement(plan, version, budget_line)
	if not line or not money.exceeds(line.get("planned"), line.get("approved")):
		fail("PLN_DEPARTMENTAL_UPDATE_NOT_REQUIRED")
	if organisation_unit not in (line_units(version.name).get(budget_line) or []):
		fail("PLN_DEPARTMENTAL_UPDATE_NOT_REQUIRED")
	root = frappe.db.get_value(
		"Departmental Plan", {"organisation_unit": organisation_unit, "fiscal_year": plan.fiscal_year},
		["name", "current_accepted_version"], as_dict=True,
	)
	if not root or not root.current_accepted_version:
		fail("PLN_DEPARTMENTAL_UPDATE_NOT_REQUIRED")
	if frappe.db.exists(DOCTYPE, {"plan_version": version.name, "budget_line": budget_line, "organisation_unit": organisation_unit, "status": OPEN}):
		fail("PLN_DEPARTMENTAL_UPDATE_ALREADY_REQUESTED")

	approved, planned = flt(line["approved"]), flt(line["planned"])
	over = float(money.as_decimal(line["planned"]) - money.as_decimal(line["approved"]))  # exact, then stored
	request = frappe.get_doc({
		"doctype": DOCTYPE,
		"request_reference": _new_reference(),
		"plan_version": version.name,
		"departmental_plan": root.name,
		"organisation_unit": organisation_unit,
		"dpp_version_at_request": root.current_accepted_version,
		"budget_line": budget_line,
		"budget_line_reference": cstr(line.get("reference")),
		"budget_line_title": cstr(line.get("title")),
		"approved_amount": approved,
		"planned_amount": planned,
		"over_amount": over,
		"status": OPEN,
		"requested_by": actor,
		"authority_snapshot": authz.authority_snapshot(assignment),
		"requested_at": now_datetime(),
		"idempotency_key": idempotency_key,
		"fixture_namespace": cstr(version.fixture_namespace),
	}).insert(ignore_permissions=True)
	result = {
		"ok": True,
		"action": "requested",
		"request": request.name,
		"plan_reference": plan.plan_reference,
		"idempotent": False,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RequestDepartmentalPlanUpdate", payload=payload, result=result,
		document_type=DOCTYPE, document_name=request.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result


def answer_on_acceptance(departmental_plan: str, accepted_version: str) -> list[str]:
	"""Procurement accepted this department's update: every Open request to it
	is Answered by that version (in the acceptance's own transaction)."""
	answered = []
	for name in frappe.get_all(DOCTYPE, filters={"departmental_plan": departmental_plan, "status": OPEN}, pluck="name"):
		doc = frappe.get_doc(DOCTYPE, name)
		if cstr(doc.dpp_version_at_request) == cstr(accepted_version):
			continue
		doc.status = ANSWERED
		doc.closed_at = now_datetime()
		doc.answered_by_version = accepted_version
		doc.save(ignore_permissions=True)
		answered.append(name)
	return answered


def withdraw_for_version(plan_version: str, *, reason: str) -> list[str]:
	"""The plan update left preparation (sent to Finance, or cancelled): an
	Open request no longer asks anything of the department."""
	withdrawn = []
	for name in frappe.get_all(DOCTYPE, filters={"plan_version": plan_version, "status": OPEN}, pluck="name"):
		frappe.db.set_value(DOCTYPE, name, {"status": WITHDRAWN, "closed_at": now_datetime(), "closed_reason": reason}, update_modified=False)
		withdrawn.append(name)
	return withdrawn
