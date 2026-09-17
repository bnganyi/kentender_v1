# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 GetDepartmentalPlan / GetDPPValidationTask — the
PLN-UI-02..06 read models.

Direct record routes derive the Fiscal Year from the record and reauthorise
through the shared resolver (§10, §12.1); unauthorised reads return the same
not-found as a nonexistent record. Dates display in Africa/Nairobi (§12.13).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, format_datetime, formatdate

from kentender_core.services import site_configuration
from kentender_procurement.procurement_planning.services import budget_gateway, dpp_classification, needs_intake, references
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.dpp_lifecycle import ATTESTATION, _has_any_submission, entry_is_complete
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_AUDITOR, ROLE_PROCUREMENT_PLANNER

NAIROBI = "Africa/Nairobi"


def _money(amount: float) -> str:
	return f"KES {fmt_money(flt(amount), precision=0, currency=None).strip()}"


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def _eat(value) -> str:
	"""A UTC instant rendered as EAT (§12.13)."""
	if not value:
		return ""
	from frappe.utils import convert_utc_to_timezone, get_datetime

	local = convert_utc_to_timezone(get_datetime(value), NAIROBI)
	return f"{format_datetime(local, 'd MMM yyyy, HH:mm')} EAT"


def _labels(root) -> dict[str, str]:
	unit = frappe.db.get_value("Organisation Unit", root.organisation_unit, ["unit_name", "unit_code"], as_dict=True) or {}
	ou_label = cstr(unit.get("unit_name") or root.organisation_unit)
	return {
		"department": f"{cstr(unit.get('unit_code') or root.organisation_unit)} — {ou_label}",
		"department_name": ou_label,
		"financial_year": references.fy_label(root.fiscal_year),
	}


def _root(dpp_reference: str):
	name = frappe.db.get_value("Departmental Plan", {"dpp_reference": cstr(dpp_reference)})
	if not name:
		authz.not_found()
	return frappe.get_doc("Departmental Plan", name)


def _unit_label(unit: str) -> str:
	return cstr(frappe.db.get_value("UOM", unit, "uom_name") or unit)


def _quantity_display(quantity, unit: str) -> str:
	value = flt(quantity)
	return f"{value:g} {_unit_label(unit).lower()}".strip()


def _quantity_number(quantity) -> str:
	"""§10.1 — Quantity and Unit are separate columns, so the number is
	rendered on its own without the unit appended."""
	return f"{flt(quantity):g}"


def _revision_number(need_revision: str) -> int:
	return needs_intake.need_revision_number(need_revision)


def _window_display(fiscal_year: str) -> dict[str, str]:
	state = site_configuration.get_dpp_submission_state(fiscal_year)
	if state.get("open"):
		if state.get("closes_at"):
			return {"state": "Open", "display": f"Open until {_eat(state['closes_at'])}"}
		return {"state": "Open", "display": "Open"}
	return {"state": "Closed", "display": "Closed"}


def _returned_issues(version) -> dict[str, list[dict[str, str]]]:
	"""§12.2 — a returned submission's structured issues, keyed by entry."""
	if not version.returned_from_submission:
		return {}
	decision = frappe.db.get_value(
		"Departmental Plan Validation Decision",
		{"submission": version.returned_from_submission, "decision": "Return to department"},
		"issues",
	)
	if not decision:
		return {}
	issues: dict[str, list[dict[str, str]]] = {}
	for row in json.loads(decision):
		issues.setdefault(cstr(row.get("entry_id")), []).append(
			{"problem": cstr(row.get("problem")), "correction": cstr(row.get("correction"))}
		)
	return issues


def _entry_action(*, not_proceeding: bool, need_origin: bool, mutable: bool) -> str:
	"""U02-A/U03-notproceeding — a not-proceeding entry's only Draft action is
	Restore, never Complete/View; a direct entry's own row is never restorable."""
	if not mutable:
		return ""
	if not_proceeding:
		return "Restore to planned requirements" if need_origin else ""
	return "Edit" if not need_origin else "Complete"


BADGES = {
	"Draft": ("Draft", "attention"),
	"Submitted": ("Awaiting validation", "attention"),
	"Returned": ("Returned", "critical"),
	"Accepted": ("Accepted", "live"),
	"Withdrawn": ("Withdrawn", "muted"),
}


def get_departmental_plan(*, dpp_reference: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	root = _root(dpp_reference)
	access = authz.require_dpp_read(root.organisation_unit, actor)
	labels = _labels(root)
	line_labels = budget_gateway.line_labels(root.fiscal_year)
	version_name = root.current_version or root.current_accepted_version
	version = frappe.get_doc("Departmental Plan Version", version_name) if version_name else None
	entries = []
	incomplete = 0
	total_specified = 0.0
	issues_by_entry = _returned_issues(version) if version else {}
	if version:
		rows = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version.name},
			fields=[
				"entry_id", "source_origin", "need", "need_revision", "title", "description",
				"expected_operational_result", "quantity", "unit", "required_by_date",
				"budget_line", "indicative_amount", "not_proceeding_reason",
			],
			order_by="creation asc",
			limit_page_length=0,
		)
		for row in rows:
			not_proceeding = bool(cstr(row.not_proceeding_reason).strip())
			funded = bool(row.budget_line) and flt(row.indicative_amount) > 0
			complete = not_proceeding or funded
			if not complete:
				incomplete += 1
			elif funded:
				total_specified += flt(row.indicative_amount)
			need_origin = row.source_origin == needs_intake.NEED_ORIGIN
			line = line_labels.get(cstr(row.budget_line), {})
			# §10.4's own wording: what the row *is* to the department, not an
			# internal readiness label.
			if not_proceeding:
				status, kind = "Not included this year", "muted"
			elif funded:
				status, kind = "Included", "live"
			else:
				status, kind = "Funding details needed", "attention"
			entries.append(
				{
					"entry_id": row.entry_id,
					"source_origin": row.source_origin,
					"title": row.title,
					"source_label": f"Accepted Need · {row.need}" if need_origin else "Direct requirement",
					# §10.4 — the requirement cell is the title on its own line
					# with its source reference and revision beneath, in muted
					# text. Direct requirements have no Need revision to show.
					"reference_line": (
						f"{row.need} · Revision {_revision_number(row.need_revision)}"
						if need_origin and row.need else "Direct requirement"
					),
					"quantity_number": _quantity_number(row.quantity),
					"unit_label": cstr(row.unit),
					"quantity_display": _quantity_display(row.quantity, row.unit),
					"required_by_display": _date(row.required_by_date),
					"budget_line_display": (line.get("reference") or cstr(row.budget_line)) if row.budget_line else ("—" if not_proceeding else "Not selected"),
					"amount_display": (
						_money(row.indicative_amount) if funded
						else ("Not applicable" if not_proceeding else "Not entered")
					),
					"status": status,
					"status_kind": kind,
					"not_proceeding_reason": cstr(row.not_proceeding_reason),
					"disposition": "Not proceeding" if not_proceeding else "Proceeding",
					"can_set_disposition": need_origin and version.version_status == "Draft" and access in ("author", "hod"),
					"action": _entry_action(
						not_proceeding=not_proceeding, need_origin=need_origin,
						mutable=version.version_status == "Draft" and access in ("author", "hod"),
					),
					"issues": issues_by_entry.get(row.entry_id, []),
				}
			)
	mutable = bool(version) and version.version_status == "Draft" and access in ("author", "hod")
	ready = bool(entries) and incomplete == 0
	if mutable and ready:
		for row in entries:
			if row["action"] and row["disposition"] != "Not proceeding":
				row["action"] = "View"
	count_label = f"{len(entries)} requirement{'s' if len(entries) != 1 else ''}"
	if incomplete:
		plural = "requirement needs" if incomplete == 1 else "requirements need"
		totals_caption = f"{count_label} · {_money(total_specified)} specified"
		readiness = {
			"title": f"{incomplete} {plural} funding details",
			"text": (
				"Select a Procurement Budget Line and enter the indicative amount for every "
				"requirement before the plan can be submitted."
			),
		}
	else:
		totals_caption = f"{count_label} · {_money(total_specified)}"
		readiness = None
	badge, badge_kind = BADGES.get(version.version_status if version else root.current_state, ("Draft", "attention"))
	if mutable and ready:
		badge, badge_kind = "Ready to submit", "live"
	# §5.1.1 — acceptance is never replaced by the candidate's state
	accepted_number = int(frappe.db.get_value("Departmental Plan Version", root.current_accepted_version, "version_number") or 0) if root.current_accepted_version else None
	update_in_progress = bool(root.current_accepted_version) and bool(version) and cstr(version.name) != cstr(root.current_accepted_version) and version.version_status in ("Draft", "Submitted", "Returned")
	display_state = "Accepted — update in progress" if update_in_progress else root.current_state
	if update_in_progress:
		badge, badge_kind = display_state, "live"
	# §5.1 "Accepted; change required → Create update": the department's own
	# actors, on an accepted plan with no open successor. An accepted plan never
	# re-projects Needs itself (§5.3 inv. 1), so name the ones it is missing.
	can_create_update = (
		access in ("author", "hod")
		and root.current_state == "Accepted"
		and cstr(root.current_version) == cstr(root.current_accepted_version)
	)
	update_notice = None
	if can_create_update:
		gaps = needs_intake.coverage_gaps(version)
		if gaps:
			plural = "need is" if len(gaps) == 1 else "needs are"
			update_notice = {
				"title": f"{len(gaps)} accepted {plural} not in this plan",
				"text": (
					f"{', '.join(gaps)} accepted after this plan was accepted. "
					"Create an update to carry it into a new draft version, fund it and resubmit."
				),
			}
	attestation = ATTESTATION.format(department=labels["department_name"], financial_year=labels["financial_year"])
	# §5.1 — the window gates only a first submission; a plan that has been
	# submitted before may still send corrections and updates after close.
	window = _window_display(root.fiscal_year)
	if window["state"] == "Closed" and _has_any_submission(root):
		window = {**window, "display": "Closed · corrections and updates may still be submitted"}
	submit_hint = ""
	if mutable and ready and access != "hod":
		submit_hint = "Only the Head of User Department, or an acting head, can submit this plan."
	# FU-14 — the record route never strands the actor who holds the open task
	open_task = None
	if access == "planner" and version and version.version_status == "Submitted":
		task = frappe.db.get_value(
			"Departmental Plan Validation Task", {"dpp_version": version.name, "status": "Open"}, ["name", "submission"], as_dict=True,
		)
		if task and not authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task.submission):
			open_task = {"label": "Review submission", "route": ["procurement-planning", "dpp-review", task.name]}
	return {
		"outcome": "OK",
		"access": access,
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"current_state": root.current_state,
		"display_state": display_state,
		"accepted_submission_number": accepted_number,
		"candidate_submission_number": version.version_number if (version and update_in_progress) else None,
		"is_correction": bool(version and cstr(version.returned_from_submission)),
		"fiscal_year": root.fiscal_year,
		"version": {
			"name": version.name if version else "",
			"version_reference": cstr(version.version_reference) if version else "",
			"version_number": version.version_number if version else None,
			"status": version.version_status if version else "",
		},
		"header": {
			"title": f"{labels['department_name']} departmental plan",
			"reference_line": f"{root.dpp_reference} · Submission {version.version_number}" if version else root.dpp_reference,
			"badge": badge,
			"badge_kind": badge_kind,
		},
		"context": {
			"department": labels["department"],
			"department_name": labels["department_name"],
			"financial_year": labels["financial_year"],
			"window": window,
		},
		"readiness": readiness,
		"submit_hint": submit_hint,
		"open_task": open_task,
		"entries": entries,
		"totals_caption": totals_caption if entries else "",
		# §10.4 — the summary strip's own value. For the Author this is "cost
		# entered so far"; for the HoD it is the included cost. Same number,
		# different claim, so the label is decided by the screen.
		"included_cost_display": _money(total_specified),
		"certification": {
			"heading": "Departmental certification",
			"text": attestation,
			"checkbox_label": "I confirm this certification",
			"show": mutable and ready and access == "hod",
		},
		"mutable": mutable,
		"can_submit": mutable and ready and access == "hod",
		"can_create_update": can_create_update,
		"update_notice": update_notice,
		"has_returned_issues": bool(issues_by_entry),
	}


def _eligible_lines(root) -> list[dict[str, Any]]:
	rows = budget_gateway.list_eligible_budget_lines(fiscal_year=root.fiscal_year, source_org_unit=root.organisation_unit)
	out = []
	for row in rows:
		reference = cstr(row.get("reference")) or cstr(row.get("id"))
		out.append(
			{
				"id": cstr(row.get("id")),
				"reference": reference,
				"label": f"{reference} — {row.get('title')}" if row.get("title") else reference,
				"title": cstr(row.get("title")),
				"approved_display": _money(row.get("approved") or 0),
				"currency": "KES",
			}
		)
	return out


def get_dpp_entry_editor(*, dpp_reference: str, entry_id: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""PLN-UI-03 (Need funding) / PLN-UI-04 (direct requirement) editor read."""
	actor = authz.actor(user)
	root = _root(dpp_reference)
	access = authz.require_dpp_read(root.organisation_unit, actor)
	# KT-STD-001 v1.5 §3A.6 / AUTH-ADR-001 §8 — a technical reader or Auditor
	# (`access == "oversight"`) reads this editor read-only; every other
	# non-author/hod profile (e.g. a Planner) keeps the existing masked
	# denial — this never widens who may reach the editor at all.
	if access not in ("author", "hod", "oversight"):
		authz.not_found()
	labels = _labels(root)
	version = frappe.get_doc("Departmental Plan Version", root.current_version)
	payload: dict[str, Any] = {
		"outcome": "OK",
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"dpp_version": version.name,
		"mutable": version.version_status == "Draft",
		"can_edit": access in ("author", "hod"),
		"context": {"department": labels["department"], "financial_year": labels["financial_year"]},
		"budget_lines": _eligible_lines(root),
		"currency": "KES",
	}
	if entry_id:
		name = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": version.name, "entry_id": cstr(entry_id)}, "name")
		if not name:
			authz.not_found()
		entry = frappe.get_doc("Departmental Plan Entry", name)
		payload["entry"] = {
			"entry_id": entry.entry_id,
			"source_origin": entry.source_origin,
			"title": entry.title,
			"description": entry.description,
			"expected_operational_result": entry.expected_operational_result,
			"quantity": flt(entry.quantity),
			"quantity_display": _quantity_display(entry.quantity, entry.unit),
			"unit": entry.unit,
			"unit_label": _unit_label(entry.unit),
			"required_by_date": cstr(entry.required_by_date),
			"required_by_display": _date(entry.required_by_date),
			"budget_line": cstr(entry.budget_line),
			"indicative_amount": flt(entry.indicative_amount) or None,
			"not_proceeding_reason": cstr(entry.not_proceeding_reason),
			"need_reference_line": (
				f"{entry.need} · Revision {needs_intake.need_revision_number(entry.need_revision)}" if entry.need else ""
			),
		}
	units = frappe.get_all("UOM", filters={"enabled": 1}, fields=["name", "uom_name"], order_by="uom_name asc", limit_page_length=200)
	payload["units"] = [{"id": row.name, "label": row.uom_name} for row in units]
	return payload


def get_dpp_validation_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""§8.1 GetDPPValidationTask / PLN-UI-06 — the exact immutable submission,
	all entry details and the current decision controls (PLN-DES-06)."""
	actor = authz.actor(user)
	if not task or not frappe.db.exists("Departmental Plan Validation Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Departmental Plan Validation Task", task)
	authz.require_site_read((ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR), actor)
	can_decide = authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	submission = frappe.get_doc("Departmental Plan Submission", task_doc.submission)
	version = frappe.get_doc("Departmental Plan Version", task_doc.dpp_version)
	root = frappe.get_doc("Departmental Plan", version.departmental_plan)
	labels = _labels(root)
	line_labels = budget_gateway.line_labels(root.fiscal_year)
	snapshots = json.loads(submission.entry_snapshots)

	submitted_by = cstr(frappe.db.get_value("User", submission.submitted_by_user, "full_name") or submission.submitted_by_user)
	total = sum(flt(row.get("indicative_amount")) for row in snapshots if not cstr(row.get("not_proceeding_reason")).strip())
	rows = [
		{
			"entry_id": row.get("entry_id"),
			"title": row.get("title"),
			"source_label": f"Accepted Need · {row.get('need')}" if row.get("need") else "Direct requirement",
			"quantity_display": _quantity_display(row.get("quantity"), cstr(row.get("unit"))),
			"quantity_number": _quantity_number(row.get("quantity")),
			"unit_label": cstr(row.get("unit")),
			"required_by_display": _date(row.get("required_by_date")),
			"budget_line_display": line_labels.get(cstr(row.get("budget_line")), {}).get("reference") or cstr(row.get("budget_line")) or "—",
			# §10.5 — an excluded row shows Not applicable for cost and type;
			# it needs neither, and an em dash would not say why.
			"amount_display": (
				"Not applicable" if cstr(row.get("not_proceeding_reason")).strip()
				else _money(row.get("indicative_amount"))
			),
			"description": row.get("description"),
			"expected_operational_result": row.get("expected_operational_result"),
			"not_proceeding": bool(cstr(row.get("not_proceeding_reason")).strip()),
			"not_proceeding_reason": cstr(row.get("not_proceeding_reason")),
		}
		for row in snapshots
	]
	# §4.4 — the Planner picks a type; the category comes with it so the screen
	# can show the derived value beside the selector without a round trip.
	requirement_types = dpp_classification.active_requirement_types()
	decision_ref = cstr(task_doc.decision)
	decided = None
	if decision_ref:
		decided = frappe.db.get_value("Departmental Plan Validation Decision", decision_ref, ["decision", "decided_at"], as_dict=True)
	maker_checker_blocked = authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=submission.name)
	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"can_decide": can_decide and task_doc.status == "Open" and not maker_checker_blocked,
		"maker_checker_blocked": maker_checker_blocked,
		"header": {
			"eyebrow": "DEPARTMENTAL PLAN REVIEW",
			"title": f"Validate {labels['department_name']} departmental plan",
			"reference_line": f"{root.dpp_reference} · Submission {version.version_number}",
			"badge": "Awaiting validation" if task_doc.status == "Open" else "Completed",
			"badge_kind": "pending" if task_doc.status == "Open" else "live",
		},
		"context": {
			"department": labels["department_name"],
			"financial_year": labels["financial_year"],
			"submitted_by": submitted_by,
			"submitted_at": _eat(submission.submitted_at),
			"requirements": len(rows),
			"total_display": _money(total),
			# §10.5 summary strip: included count, included cost, excluded count.
			"included_requirements": len([r for r in rows if not r["not_proceeding"]]),
			"included_cost_display": _money(
				sum(flt(r.get("indicative_amount")) for r in snapshots if not cstr(r.get("not_proceeding_reason")).strip())
			),
			"excluded_requirements": len([r for r in rows if r["not_proceeding"]]),
		},
		"entries": rows,
		"requirement_types": requirement_types,
		"certification": {
			"heading": "Departmental certification",
			"text": submission.attestation_text,
			"signed_line": f"Certified by {submitted_by} · {_eat(submission.submitted_at)}",
		},
		"decided": decided,
	}
