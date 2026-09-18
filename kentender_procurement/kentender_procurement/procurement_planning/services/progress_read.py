# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §10.13 / §10.15 — procurement progress (U14) and Planning
correction requests (U16).

Both reads exist to say only what an owning module has actually supplied.

For progress that means: what the current plan planned, how much of it an
authorised Requisition covers, and what procurement stage the owning module
reports. There is no completion column unless an owning module supplies
completion evidence, and no placeholder in its place — an empty column that
says "not yet available" on every row is worse than no column (§10.13,
PLN22-AC-009). Different units are never summed, and publication is never
rendered as delivery.

Operational dates are owner-supplied actuals only, held per procurement
proceeding (§5.5.1A): the approved baseline, the actual, and the days between
them. Forecast comparison is absent from the MVP (§10.13, PLN23-CHG-001), so
no forecast column is offered here or anywhere downstream of here.

For corrections that means leading with the change that is required and the
work it holds, not with request identifiers and orchestration states. Multiple
requests share one effective hold on the item, and it lifts only when every one
of them reaches a permitted terminal outcome (§5.4.5, PLN-RI-029).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

#: §10.15 — what the Planner is being asked for, and what it is doing to their
#: work. Request ids, versions and timestamps stay in the detail.
_REQUEST_STATUS = {
	"Open": ("Needs review", "pending"),
	"In progress": ("Correction in progress", "attention"),
	"Resolved": ("Correction recorded", "live"),
	"Closed without change": ("Closed without a plan change", "muted"),
}

_REQUEST_ACTION = {
	"Open": "Review issue",
	"In progress": "Continue correction",
	"Resolved": "View outcome",
	"Closed without change": "View outcome",
}

#: §10.13 — a supported milestone an owner has not yet reported. An
#: *unsupported* milestone is omitted entirely rather than given this text.
NO_DATE_RECORDED = "No date recorded"


# --------------------------------------------------------------------------
# U14 — procurement progress
# --------------------------------------------------------------------------


def get_procurement_progress(*, plan_reference: str = "", user: str | None = None) -> dict[str, Any]:
	"""§10.13 U14 — planned scope, authorised coverage and procurement stage
	for the current plan, purchase by purchase."""
	from kentender_procurement.procurement_planning.services import plan_read, references

	actor = authz.actor(user)
	authz.require_site_read(plan_read.PLAN_READERS, actor)

	plan = _current_plan(plan_reference)
	if not plan:
		return {"outcome": "NO_ACTIVE_PLAN"}
	version = frappe.get_doc("Annual Plan Version", plan.active_version)

	items = [
		_purchase_row(item)
		for item in frappe.get_all(
			"Annual Plan Item",
			filters={"plan_version": version.name, "item_state": "Active"},
			fields=["name", "plan_item_id", "title", "schedule_profile_version"],
			order_by="creation asc",
			limit_page_length=0,
		)
	]

	return {
		"outcome": "OK",
		"plan_reference": cstr(plan.plan_reference),
		"plan_title": cstr(plan.title),
		"version_number": version.version_number,
		# §10.13 header — this read is only ever about the plan in force.
		"status": "Current plan",
		"financial_year_label": references.fy_label(cstr(plan.fiscal_year)),
		"items": items,
	}


def _current_plan(plan_reference: str):
	"""The Active plan — named, or the one in force. A plan with no Active
	Version has no procurement to report, which is a state, not an error."""
	filters = {"plan_reference": cstr(plan_reference)} if cstr(plan_reference).strip() else {"active_version": ("is", "set")}
	plan = frappe.db.get_value(
		"Annual Plan", filters, ["name", "plan_reference", "title", "fiscal_year", "active_version"], as_dict=True
	)
	return plan if plan and plan.active_version else None


def _purchase_row(item) -> dict[str, Any]:
	"""One purchase: what was planned, what authorised requisitions cover,
	what has started, and the proceedings behind it."""
	from kentender_procurement.procurement_planning.services import plan_read, scope_lock

	planned_qty, planned_value, unit = _planned(item.name)
	covered_qty, covered_value = _authorised_coverage(item.plan_item_id)
	proceedings = _proceedings(item.plan_item_id, item)
	lock = scope_lock.status(item.plan_item_id)

	return {
		"plan_item_id": cstr(item.plan_item_id),
		"title": cstr(item.title),
		# Quantity and value together, never a bare "remaining" number that
		# hides which of the two is short (§10.13).
		"planned_display": _scope_display(planned_qty, unit, planned_value),
		"covered_display": _scope_display(covered_qty, unit, covered_value),
		"not_covered_display": _scope_display(planned_qty - covered_qty, unit, planned_value - covered_value),
		"fully_covered": bool(planned_qty) and covered_qty >= planned_qty,
		"procurement_stage": _stage(proceedings),
		"proceedings": proceedings,
		"hold": _hold_for(lock),
		"scope_locked": bool(lock["locked"]),
		"route": ["procurement-plan-item", cstr(item.plan_item_id)],
	}


def _planned(plan_item: str) -> tuple[float, float, str]:
	"""This Version's own approved scope. Released allocations are not
	planned scope any more and are not counted back in."""
	rows = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": plan_item, "allocation_state": ("!=", "Released")},
		fields=["quantity", "unit", "indicative_amount"],
		limit_page_length=0,
	)
	return (
		sum(flt(r.quantity) for r in rows),
		sum(flt(r.indicative_amount) for r in rows),
		cstr(rows[0].unit) if rows else "",
	)


def _scope_display(quantity: float, unit: str, value: float) -> str:
	"""`250 Each / KES 50,000,000` — the two facts side by side, in the
	purchase's own unit. Units from different purchases are never summed."""
	from kentender_procurement.procurement_planning.services import plan_read

	label = plan_read._unit_label(unit) if unit else ""
	return f"{flt(quantity):g} {label} / {plan_read._money(value)}".replace("  ", " ").strip()


def _authorised_coverage(plan_item_id: str) -> tuple[float, float]:
	"""Only what an authorised Requisition actually drew down — never
	inferred from a shared stable item id or a published Tender
	(§5.4.6, PLN-RI-069). A reversed drawdown covers nothing."""
	rows = frappe.get_all(
		"Plan Drawdown Reference",
		filters={"plan_item_id": plan_item_id, "drawdown_state": "Active"},
		fields=["quantity", "amount"],
		limit_page_length=0,
	)
	return sum(flt(r.quantity) for r in rows), sum(flt(r.amount) for r in rows)


def _proceedings(plan_item_id: str, item) -> list[dict[str, Any]]:
	"""Each procurement proceeding this item's sources are covered by, with
	the stage its owning module reports and that proceeding's own owner-
	supplied dates. Two proceedings keep two sets of dates (§5.5.1A); one is
	never collapsed onto the other."""
	from kentender_procurement.procurement_planning.services import plan_read

	out = []
	for row in frappe.get_all(
		"Proceeding Coverage",
		filters={"plan_item_id": plan_item_id},
		fields=[
			"proceeding_type", "proceeding_id", "requisition_reference", "covered_quantity",
			"covered_value", "authorisation_state", "publication_state",
		],
		order_by="creation asc",
		limit_page_length=0,
	):
		schedule_rows, durations = _operational_dates(plan_item_id, cstr(row.proceeding_id), item)
		out.append(
			{
				"proceeding_type": cstr(row.proceeding_type),
				"proceeding_id": cstr(row.proceeding_id),
				"requisition_reference": cstr(row.requisition_reference),
				"covered_display": f"{flt(row.covered_quantity):g} / {plan_read._money(row.covered_value)}",
				# The owning module's own words for where this has got to.
				# Publication is never presented as delivery or completion.
				"stage": cstr(row.publication_state) or cstr(row.authorisation_state) or "Authorised",
				"milestones": schedule_rows,
				"durations": durations,
			}
		)
	return out


def _operational_dates(plan_item_id: str, proceeding_id: str, item) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""§10.13 U14-ACTUALS — Milestone; Approved date; Actual date; Days after
	approved date, for one proceeding, and beneath it the stage durations
	that both endpoints actually support.

	Returns two empty lists when no owner has supplied a single actual for
	this proceeding: the whole table is omitted rather than rendered as rows
	of placeholders (PLN22-AC-009)."""
	from kentender_procurement.procurement_planning.services import actuals, plan_read, schedule

	variance = actuals.proceeding_variance(plan_item_id, proceeding_id)
	applicable = [row for row in variance if row["applicable"]]
	if not any(row["actual"] for row in applicable):
		return [], []

	milestones = [
		{
			"milestone": row["milestone"],
			"label": schedule.MILESTONE_LABELS[row["milestone"]],
			"approved_display": plan_read._date(row["baseline"]),
			"actual_display": plan_read._date(row["actual"]) if row["actual"] else NO_DATE_RECORDED,
			"days_after_approved": _measure(row["baseline_lateness_days"]),
		}
		for row in applicable
	]

	durations = []
	previous = None
	for row in applicable:
		if previous is not None and previous["actual"] and row["actual"]:
			durations.append(
				{
					"from_label": schedule.MILESTONE_LABELS[previous["milestone"]],
					"to_label": schedule.MILESTONE_LABELS[row["milestone"]],
					"planned_elapsed_days": _measure(actuals.elapsed_days(previous["baseline"], row["baseline"])),
					"actual_elapsed_days": _measure(row["elapsed_since_previous_days"]),
					"difference_days": _measure(row["duration_variance_since_previous_days"]),
				}
			)
		previous = row
	return milestones, durations


def _measure(value) -> str:
	"""A measure the owner's evidence supports, or the plain statement that
	it does not. `Not applicable` is only ever the applicable owner's own
	explicit state, never our stand-in for a missing number."""
	from kentender_procurement.procurement_planning.services.actuals import NOT_APPLICABLE, NOT_AVAILABLE

	if value == NOT_APPLICABLE:
		return "Not applicable"
	if value == NOT_AVAILABLE or value is None:
		return "—"
	return str(int(value))


def _stage(proceedings: list[dict[str, Any]]) -> str:
	"""What has started, in the owners' words. Nothing started is a fact, not
	an omission."""
	if not proceedings:
		return "Not started"
	return " · ".join(sorted({p["stage"] for p in proceedings}))


def _hold_for(lock: dict[str, Any]) -> dict[str, Any] | None:
	"""§5.4.5 / PLN-RI-029 — one effective hold derived from every unresolved
	request, shown against the purchase it actually affects."""
	if not lock["held"]:
		return None
	count = int(lock["open_requests"] or 0)
	return {
		"open_requests": count,
		"text": "New requisitions are on hold while these requests remain unresolved.",
		"link_text": "View correction requests",
	}


# --------------------------------------------------------------------------
# U16 — plan correction requests
# --------------------------------------------------------------------------


def get_plan_correction_requests(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	"""§10.15 U16 — what must change, what is held, and the lawful next
	action, before any request mechanics."""
	from kentender_procurement.procurement_planning.services import plan_read, scope_lock

	actor = authz.actor(user)
	authz.require_site_read(plan_read.PLAN_READERS, actor)

	item = frappe.db.get_value(
		"Annual Plan Item",
		{"plan_item_id": cstr(plan_item_id), "item_state": "Active"},
		["name", "plan_item_id", "title", "plan_version"],
		as_dict=True,
	)
	if not item:
		authz.not_found()
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	lock = scope_lock.status(item.plan_item_id)

	correcting_plan = _correcting_plan(cstr(item.plan_version))
	requests = [_request_row(row, correcting_plan) for row in frappe.get_all(
		"Plan Item Correction Request",
		filters={"plan_item_id": cstr(plan_item_id)},
		fields=[
			"name", "reason", "status", "requisition_reference", "requisition_version",
			"requested_by", "requested_role", "requested_at", "plan_version",
			"resolved_by", "resolved_at", "resolution_note", "record_version",
		],
		order_by="requested_at asc",
		limit_page_length=0,
	)]
	unresolved = [r for r in requests if not r["terminal"]]

	return {
		"outcome": "OK",
		"plan_item_id": cstr(item.plan_item_id),
		"title": cstr(item.title),
		"version_number": version.version_number,
		"hold": _request_hold(unresolved),
		# §5.4.6 — the permanent restriction is a separate fact from the
		# temporary hold, and it survives every request outcome.
		"scope_lock": (
			{
				"locked": True,
				"text": (
					"A requisition has already been authorised. Extra requirements must be added as a "
					"separate purchase in a plan update."
				),
				"first_requisition": lock["first_requisition"],
			}
			if lock["locked"] else {"locked": False}
		),
		"requests": requests,
		"correcting_plan": correcting_plan,
		"additional_requirement": _additional_requirement(cstr(item.plan_item_id), cstr(item.plan_version)),
		"can_act": authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor),
	}


def _correcting_plan(plan_version: str) -> dict[str, Any]:
	"""§10.15 U16-COMPLETE — the plan version a correction would be recorded
	against, and whether it is actually Active yet.

	`ResolvePlanItemCorrectionRequest` refuses a version that is not Active
	(`PLN_CORRECTION_NOT_ACTIVE`), so the screen names the version and says
	plainly when it is still being prepared rather than offering a control
	the command would reject."""
	from kentender_procurement.procurement_planning.services import plan_read

	plan_name = frappe.db.get_value("Annual Plan Version", plan_version, "annual_plan")
	plan = frappe.db.get_value(
		"Annual Plan", plan_name, ["plan_reference", "active_version", "open_successor_version"], as_dict=True
	)
	if not plan:
		return {"available": False}

	candidate = cstr(plan.active_version)
	version = frappe.db.get_value(
		"Annual Plan Version", candidate, ["version_number", "version_status", "activated_at"], as_dict=True
	) if candidate else None
	if not version:
		return {"available": False}

	return {
		"available": True,
		"plan_reference": cstr(plan.plan_reference),
		"correcting_plan_version": candidate,
		"version_number": version.version_number,
		"activated_display": plan_read._eat(version.activated_at),
		"update_in_preparation": bool(plan.open_successor_version),
	}


def _request_row(row, correcting_plan: dict[str, Any]) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	status, kind = _REQUEST_STATUS.get(cstr(row.status), (cstr(row.status), "pending"))
	terminal = cstr(row.status) in ("Resolved", "Closed without change")
	# §10.15 U16-COMPLETE — completion is offered only once a *later* plan
	# version is actually Active. The version the request was raised against
	# is not a correction of itself, and a Draft successor is not yet one
	# either (`ResolvePlanItemCorrectionRequest` refuses both).
	correction_active = bool(
		correcting_plan.get("available")
		and correcting_plan.get("correcting_plan_version") != cstr(row.plan_version)
	)
	return {
		"request": row.name,
		# The change itself leads. The request id, the exact versions and the
		# timestamps are detail (PLN22-AC-011).
		"change_required": cstr(row.reason),
		"status": status,
		"status_kind": kind,
		# §10.15 — "the exact Requisition/Tender owner". The person who
		# actually raised it, in the capacity they raised it in. No department
		# is inferred: one person may hold the role for several, and naming
		# the wrong one would be worse than naming none (§6.5).
		"requested_from": _requester(row),
		"action": _REQUEST_ACTION.get(cstr(row.status), ""),
		"terminal": terminal,
		"record_version": row.record_version,
		"can_start": cstr(row.status) == "Open",
		"can_record_completed": not terminal and correction_active,
		"can_close_without_change": not terminal,
		# Why the completion control is absent, said plainly rather than shown
		# as a disabled button with no explanation (§11 labels).
		"completion_blocked_reason": (
			""
			if terminal or correction_active
			else (
				"A plan update is being prepared. Record the correction once that version is active."
				if correcting_plan.get("update_in_preparation")
				else "Prepare and activate a plan correction before recording it here."
			)
		),
		"detail": {
			"request": row.name,
			"requisition_reference": cstr(row.requisition_reference),
			"requisition_version": cstr(row.requisition_version),
			"requested_by": _person(row.requested_by),
			"requested_display": plan_read._eat(row.requested_at),
			"plan_version": cstr(row.plan_version),
			"resolved_by": _person(row.resolved_by),
			"resolved_display": plan_read._eat(row.resolved_at),
			"resolution_note": cstr(row.resolution_note),
		},
	}


def _person(user) -> str:
	"""A real person's name, never an invented one — the sign-in address is
	the fallback, and blank stays blank (§6.5)."""
	user = cstr(user).strip()
	if not user:
		return ""
	return cstr(frappe.db.get_value("User", user, "full_name")) or user


def _requester(row) -> str:
	who = _person(row.requested_by)
	role = cstr(row.requested_role)
	return f"{who} · {role}" if (who and role) else (who or role)


def _request_hold(unresolved: list[dict[str, Any]]) -> dict[str, Any]:
	"""§10.15 U16-MULTIPLE — one disposition never clears another's hold, so
	the count of what is still outstanding is stated rather than implied. A
	lifted hold offers no "resume requisitions" action: nothing downstream is
	restarted by Planning."""
	if not unresolved:
		return {"active": False}
	count = len(unresolved)
	return {
		"active": True,
		"text": "New requisitions for this purchase are on hold until the planning issue is resolved.",
		"remaining": f"{count} issue{'s' if count != 1 else ''} still need{'' if count != 1 else 's'} attention",
	}


def _additional_requirement(plan_item_id: str, plan_version: str) -> dict[str, Any] | None:
	"""§10.15 U16-ADDITIONAL-REQUIREMENT / PLN-RI-068 — accepted departmental
	requirements that are not in the current annual plan.

	A later accepted requirement is never absorbed into a purchase whose scope
	is locked (§5.4.6), so it is named here with the lawful route instead:
	a separate item in a plan update. Naming it creates nothing — the action
	only opens the eligible pending work (PLN19-UX-021).

	Its three results are stated separately, because none of them implies
	another: being planned is not procurement, and procurement is not
	completion (PLN-RI-069).
	"""
	from kentender_procurement.procurement_planning.services import plan_read

	plan_name = frappe.db.get_value("Annual Plan Version", plan_version, "annual_plan")
	plan = frappe.db.get_value("Annual Plan", plan_name, ["fiscal_year", "active_version", "open_successor_version"], as_dict=True)
	if not plan or not plan.active_version:
		return None

	allocated = plan_read._allocated_dpp_entries(plan.active_version)
	in_open_update = plan_read._allocated_dpp_entries(plan.open_successor_version) if plan.open_successor_version else set()
	pending = [row for row in plan_read._accepted_entry_rows(plan.fiscal_year) if row["dpp_entry"] not in allocated]
	if not pending:
		return None

	return {
		"heading": "Requirement not yet in the current plan",
		"sources": [
			{
				"dpp_entry": row["dpp_entry"],
				"entry_id": row["entry_id"],
				"title": row["title"],
				"department": row["department"],
				"quantity_display": f"{flt(row['quantity']):g} {row['unit_label']}".strip(),
				"amount_display": row["amount_display"],
				"source_label": row["source_label"],
				# Three labelled results, each from its own evidence.
				"annual_plan_result": (
					"Already in a plan update being prepared"
					if row["dpp_entry"] in in_open_update
					else "Not yet in the current annual plan"
				),
				"procurement_result": "No procurement recorded",
				"completion_result": "No completion evidence",
			}
			for row in pending
		],
		"action": "Add as a separate item in a plan update",
		# Where the action goes. It opens the eligible pending work; it does
		# not start an update on navigation.
		"route": ["annual-procurement-plan", cstr(frappe.db.get_value("Annual Plan", plan_name, "plan_reference"))],
	}
