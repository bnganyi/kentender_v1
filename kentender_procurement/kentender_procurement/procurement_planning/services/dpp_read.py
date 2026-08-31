# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §8.1 GetDepartmentalPlan — the PLN-UI-02..05 read models.

Direct record routes derive PE/FY from the record and reauthorise (§10);
unauthorised reads return the same not-found as a nonexistent record. Dates
display in Africa/Nairobi (§12.13)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, format_datetime, formatdate

from kentender_procurement.procurement_planning.services import (
	authority,
	budget_gateway,
	needs_intake,
)
from kentender_procurement.procurement_planning.services.dpp_lifecycle import (
	ATTESTATION,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PLANNING_AUDITOR,
	ROLE_PROCUREMENT_PLANNER,
)

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
	pe_label = cstr(
		frappe.db.get_value("Procuring Entity", root.procuring_entity, "legal_name")
		or root.procuring_entity
	)
	ou_label = cstr(
		frappe.db.get_value("Organisation Unit", root.organisation_unit, "unit_name")
		or root.organisation_unit
	)
	fy_label = cstr(
		frappe.db.get_value("Financial Year", root.financial_year, "label")
		or root.financial_year
	)
	if fy_label and not fy_label.upper().startswith("FY"):
		fy_label = f"FY {fy_label}"
	return {
		"procuring_entity": f"{root.procuring_entity} — {pe_label}",
		"department": f"{root.organisation_unit} — {ou_label}",
		"department_name": ou_label,
		"financial_year": fy_label,
	}


def _access(actor: str, root) -> str:
	"""One scope predicate for every DPP read path; masked not-found outside it."""
	roles = set(frappe.get_roles(actor))
	pes = authority.permitted_pes(actor)
	ous = authority.permitted_org_units(actor)
	if root.procuring_entity in pes:
		if ROLE_HEAD_OF_USER_DEPARTMENT in roles and root.organisation_unit in ous:
			return "hod"
		if ROLE_DEPARTMENTAL_AUTHOR in roles and root.organisation_unit in ous:
			return "author"
		if ROLE_PROCUREMENT_PLANNER in roles and (not ous or root.organisation_unit in ous):
			return "planner"
		if ROLE_PLANNING_AUDITOR in roles:
			return "auditor"
	authority.not_found()


def _root(dpp_reference: str):
	name = frappe.db.get_value("Departmental Plan", {"dpp_reference": cstr(dpp_reference)})
	if not name:
		authority.not_found()
	return frappe.get_doc("Departmental Plan", name)


def _unit_label(unit: str) -> str:
	return cstr(frappe.db.get_value("Unit Of Measure", unit, "unit_label") or unit)


def _quantity_display(quantity, unit: str) -> str:
	value = flt(quantity)
	shown = f"{value:g}"
	return f"{shown} {_unit_label(unit).lower()}".strip()


def _window_display(root) -> dict[str, str]:
	row = frappe.db.get_value(
		"Departmental Plan Submission Window",
		{"pe_fy_context": root.pe_fy_context},
		["opens_at", "closes_at"],
		as_dict=True,
	)
	if not row:
		return {"state": "None", "display": "Not configured"}
	from frappe.utils import get_datetime, now_datetime

	now = now_datetime()
	if now < get_datetime(row.opens_at):
		return {"state": "Scheduled", "display": f"Opens {_eat(row.opens_at)}"}
	if now > get_datetime(row.closes_at):
		return {"state": "Closed", "display": f"Closed {_eat(row.closes_at)}"}
	return {"state": "Open", "display": f"Open until {_eat(row.closes_at)}"}


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


BADGES = {
	"Draft": ("Draft", "attention"),
	"Submitted": ("Awaiting validation", "attention"),
	"Returned": ("Returned", "critical"),
	"Accepted": ("Accepted", "live"),
	"Withdrawn": ("Withdrawn", "muted"),
}


def get_departmental_plan(*, dpp_reference: str, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	root = _root(dpp_reference)
	access = _access(actor, root)
	labels = _labels(root)
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
				"entry_id", "source_origin", "need", "need_version", "title",
				"description", "expected_operational_result", "quantity", "unit",
				"required_by_date", "budget_line", "indicative_amount",
			],
			order_by="creation asc",
			limit_page_length=0,
		)
		for row in rows:
			funded = bool(row.budget_line) and flt(row.indicative_amount) > 0
			if not funded:
				incomplete += 1
			else:
				total_specified += flt(row.indicative_amount)
			need_origin = row.source_origin == needs_intake.NEED_ORIGIN
			entries.append(
				{
					"entry_id": row.entry_id,
					"source_origin": row.source_origin,
					"title": row.title,
					"source_label": (
						f"Accepted Need · {row.need}" if need_origin else "Direct requirement"
					),
					"quantity_display": _quantity_display(row.quantity, row.unit),
					"required_by_display": _date(row.required_by_date),
					"budget_line_display": cstr(row.budget_line) or "Not selected",
					"amount_display": _money(row.indicative_amount) if funded else "—",
					"status": "Ready" if funded else "Funding incomplete",
					"status_kind": "live" if funded else "attention",
					"action": (
						"" if version.version_status != "Draft" or access in ("planner", "auditor")
						else ("Edit" if not need_origin else "Complete")
					),
					"issues": issues_by_entry.get(row.entry_id, []),
				}
			)
	mutable = bool(version) and version.version_status == "Draft" and access in ("author", "hod")
	ready = bool(entries) and incomplete == 0
	if mutable and ready:
		# PLN-DES-05: once every row is Ready the per-row action reads "View"
		# (the editor stays reachable; DES-02's Complete/Edit belong to the
		# incomplete state).
		for row in entries:
			if row["action"]:
				row["action"] = "View"
	if incomplete:
		plural = "requirement needs" if incomplete == 1 else "requirements need"
		totals_caption = (
			f"{len(entries)} requirement{'s' if len(entries) != 1 else ''} · "
			f"{_money(total_specified)} specified"
		)
		readiness = {
			"title": f"{incomplete} {plural} funding details",
			"text": (
				"Select a Budget Line and enter the indicative amount for every "
				"requirement before the plan can be submitted."
			),
		}
	else:
		totals_caption = (
			f"{len(entries)} requirement{'s' if len(entries) != 1 else ''} · "
			f"{_money(total_specified)}"
		)
		readiness = None
	badge, badge_kind = BADGES.get(
		version.version_status if version else root.current_state, ("Draft", "attention")
	)
	if mutable and ready:
		badge, badge_kind = "Ready to submit", "live"
	attestation = ATTESTATION.format(
		department=labels["department_name"], financial_year=labels["financial_year"]
	)
	return {
		"outcome": "OK",
		"access": access,
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"current_state": root.current_state,
		"version": {
			"name": version.name if version else "",
			"version_reference": cstr(version.version_reference) if version else "",
			"version_number": version.version_number if version else None,
			"status": version.version_status if version else "",
		},
		"header": {
			"title": f"{labels['department_name']} departmental plan",
			"reference_line": (
				f"{root.dpp_reference} · Version {version.version_number}"
				if version
				else root.dpp_reference
			),
			"badge": badge,
			"badge_kind": badge_kind,
		},
		"context": {
			"procuring_entity": labels["procuring_entity"],
			"department": labels["department"],
			"financial_year": labels["financial_year"],
			"window": _window_display(root),
		},
		"readiness": readiness,
		"entries": entries,
		"totals_caption": totals_caption if entries else "",
		"certification": {
			"heading": "Departmental certification",
			"text": attestation,
			"checkbox_label": "I confirm this certification",
			"show": mutable and ready and access == "hod",
		},
		"mutable": mutable,
		"can_submit": mutable and ready and access == "hod",
		"has_returned_issues": bool(issues_by_entry),
	}


def _eligible_lines(root) -> list[dict[str, Any]]:
	rows = budget_gateway.list_eligible_budget_lines(
		procuring_entity=root.procuring_entity,
		financial_year=root.financial_year,
		source_org_unit=root.organisation_unit,
	)
	return [
		{
			"id": cstr(row.get("id")),
			"label": f"{row.get('id')} — {row.get('title')}" if row.get("title") else cstr(row.get("id")),
			"title": cstr(row.get("title")),
			"approved_display": _money(row.get("approved") or 0),
			"currency": "KES",
		}
		for row in rows
	]


def get_dpp_entry_editor(
	*, dpp_reference: str, entry_id: str | None = None, user: str | None = None
) -> dict[str, Any]:
	"""PLN-UI-03 (Need funding) / PLN-UI-04 (direct requirement) editor read."""
	actor = cstr(user or frappe.session.user)
	root = _root(dpp_reference)
	access = _access(actor, root)
	if access not in ("author", "hod"):
		authority.not_found()
	labels = _labels(root)
	version = frappe.get_doc("Departmental Plan Version", root.current_version)
	payload: dict[str, Any] = {
		"outcome": "OK",
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"dpp_version": version.name,
		"mutable": version.version_status == "Draft",
		"context": {
			"procuring_entity": labels["procuring_entity"],
			"department": labels["department"],
			"financial_year": labels["financial_year"],
		},
		"budget_lines": _eligible_lines(root),
		"currency": "KES",
	}
	if entry_id:
		name = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": version.name, "entry_id": cstr(entry_id)},
			"name",
		)
		if not name:
			authority.not_found()
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
			"need_reference_line": (
				f"{entry.need} · Version {needs_intake.need_version_number(entry.need_version)}"
				if entry.need
				else ""
			),
		}
	units = frappe.get_all(
		"Unit Of Measure",
		filters={"status": "Active"},
		fields=["name", "unit_label"],
		order_by="unit_label asc",
		limit_page_length=200,
	)
	payload["units"] = [{"id": row.name, "label": row.unit_label} for row in units]
	return payload


def get_dpp_validation_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""§8.1 GetDPPValidationTask / PLN-UI-06 — the exact immutable submission,
	all entry details and the current decision controls (PLN-DES-06)."""
	from kentender_procurement.procurement_planning.services.dpp_validation import (
		_authorise_planner,
	)

	actor = cstr(user or frappe.session.user)
	if not task or not frappe.db.exists("Departmental Plan Validation Task", task):
		authority.not_found()
	task_doc = frappe.get_doc("Departmental Plan Validation Task", task)
	_authorise_planner(actor, task_doc)
	submission = frappe.get_doc("Departmental Plan Submission", task_doc.submission)
	version = frappe.get_doc("Departmental Plan Version", task_doc.dpp_version)
	root = frappe.get_doc("Departmental Plan", version.departmental_plan)
	labels = _labels(root)
	snapshots = json.loads(submission.entry_snapshots)

	submitted_by = cstr(
		frappe.db.get_value("User", submission.submitted_by_user, "full_name")
		or submission.submitted_by_user
	)
	total = sum(flt(row.get("indicative_amount")) for row in snapshots)
	rows = [
		{
			"entry_id": row.get("entry_id"),
			"title": row.get("title"),
			"source_label": (
				f"Accepted Need · {row.get('need')}"
				if row.get("need")
				else "Direct requirement"
			),
			"quantity_display": _quantity_display(row.get("quantity"), cstr(row.get("unit"))),
			"required_by_display": _date(row.get("required_by_date")),
			"budget_line_display": cstr(row.get("budget_line")),
			"amount_display": _money(row.get("indicative_amount")),
			"description": row.get("description"),
			"expected_operational_result": row.get("expected_operational_result"),
		}
		for row in snapshots
	]
	requirement_types = frappe.get_all(
		"Requirement Type", filters={"status": "Active"}, order_by="title asc", pluck="name"
	)
	decision_ref = cstr(task_doc.decision)
	decided = None
	if decision_ref:
		decided = frappe.db.get_value(
			"Departmental Plan Validation Decision",
			decision_ref,
			["decision", "decided_at"],
			as_dict=True,
		)
	# §6.1 — the certifier never validates their own submission.
	maker_checker_blocked = cstr(submission.submitted_by_user) == actor
	return {
		"outcome": "OK",
		"task": task_doc.name,
		"task_reference": task_doc.task_reference,
		"task_token": task_doc.task_token,
		"status": task_doc.status,
		"maker_checker_blocked": maker_checker_blocked,
		"header": {
			"eyebrow": "DEPARTMENTAL PLAN REVIEW",
			"title": f"Validate {labels['department_name']} departmental plan",
			"reference_line": (
				f"{root.dpp_reference} · Submitted Version {version.version_number}"
			),
			"badge": "Awaiting validation" if task_doc.status == "Open" else "Completed",
			"badge_kind": "pending" if task_doc.status == "Open" else "live",
		},
		"context": {
			"procuring_entity": cstr(
				frappe.db.get_value("Procuring Entity", root.procuring_entity, "legal_name")
				or root.procuring_entity
			),
			"department": labels["department_name"],
			"financial_year": labels["financial_year"],
			"submitted_by": submitted_by,
			"submitted_at": _eat(submission.submitted_at),
			"requirements": len(rows),
			"total_display": _money(total),
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
