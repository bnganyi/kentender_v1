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
from kentender_procurement.procurement_planning.services import budget_gateway, needs_intake, references
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.dpp_lifecycle import ATTESTATION, entry_is_complete
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
				"entry_id", "source_origin", "need", "need_version", "title", "description",
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
			if not_proceeding:
				status, kind = "Not proceeding", "muted"
			elif funded:
				status, kind = "Ready", "live"
			else:
				status, kind = "Funding incomplete", "attention"
			entries.append(
				{
					"entry_id": row.entry_id,
					"source_origin": row.source_origin,
					"title": row.title,
					"source_label": f"Accepted Need · {row.need}" if need_origin else "Direct requirement",
					"quantity_display": _quantity_display(row.quantity, row.unit),
					"required_by_display": _date(row.required_by_date),
					"budget_line_display": (line.get("reference") or cstr(row.budget_line)) if row.budget_line else ("—" if not_proceeding else "Not selected"),
					"amount_display": _money(row.indicative_amount) if funded else "—",
					"status": status,
					"status_kind": kind,
					"not_proceeding_reason": cstr(row.not_proceeding_reason),
					"action": (
						"" if version.version_status != "Draft" or access in ("planner", "oversight")
						else ("Edit" if not need_origin else "Complete")
					),
					"issues": issues_by_entry.get(row.entry_id, []),
				}
			)
	mutable = bool(version) and version.version_status == "Draft" and access in ("author", "hod")
	ready = bool(entries) and incomplete == 0
	if mutable and ready:
		for row in entries:
			if row["action"]:
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
	attestation = ATTESTATION.format(department=labels["department_name"], financial_year=labels["financial_year"])
	return {
		"outcome": "OK",
		"access": access,
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"current_state": root.current_state,
		"fiscal_year": root.fiscal_year,
		"version": {
			"name": version.name if version else "",
			"version_reference": cstr(version.version_reference) if version else "",
			"version_number": version.version_number if version else None,
			"status": version.version_status if version else "",
		},
		"header": {
			"title": f"{labels['department_name']} departmental plan",
			"reference_line": f"{root.dpp_reference} · Version {version.version_number}" if version else root.dpp_reference,
			"badge": badge,
			"badge_kind": badge_kind,
		},
		"context": {
			"department": labels["department"],
			"financial_year": labels["financial_year"],
			"window": _window_display(root.fiscal_year),
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
	if access not in ("author", "hod"):
		authz.not_found()
	labels = _labels(root)
	version = frappe.get_doc("Departmental Plan Version", root.current_version)
	payload: dict[str, Any] = {
		"outcome": "OK",
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"dpp_version": version.name,
		"mutable": version.version_status == "Draft",
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
				f"{entry.need} · Version {needs_intake.need_version_number(entry.need_version)}" if entry.need else ""
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
			"required_by_display": _date(row.get("required_by_date")),
			"budget_line_display": line_labels.get(cstr(row.get("budget_line")), {}).get("reference") or cstr(row.get("budget_line")) or "—",
			"amount_display": _money(row.get("indicative_amount")) if not cstr(row.get("not_proceeding_reason")).strip() else "—",
			"description": row.get("description"),
			"expected_operational_result": row.get("expected_operational_result"),
			"not_proceeding": bool(cstr(row.get("not_proceeding_reason")).strip()),
			"not_proceeding_reason": cstr(row.get("not_proceeding_reason")),
		}
		for row in snapshots
	]
	requirement_types = frappe.get_all("Requirement Type", filters={"status": "Active"}, order_by="title asc", pluck="name")
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
			"reference_line": f"{root.dpp_reference} · Submitted Version {version.version_number}",
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
