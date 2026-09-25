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
from kentender_procurement.procurement_planning.services import budget_gateway, dpp_classification, missing_setting, needs_intake, references
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


def _returned_issues(version) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
	"""§4.4/§12.2 — a returned submission's issues, keyed by entry, plus any
	whole-submission issue (`entry_id` null) separately. A decision is
	immutable, so an older row still carries the retired `{problem,
	correction}` shape rather than the single `correction_required` comment —
	both facts are distinct information and neither is discarded or rewritten
	to fit the current shape."""
	if not version.returned_from_submission:
		return {}, []
	decision = frappe.db.get_value(
		"Departmental Plan Validation Decision",
		{"submission": version.returned_from_submission, "decision": "Return to department"},
		"issues",
	)
	if not decision:
		return {}, []
	by_entry: dict[str, list[dict[str, str]]] = {}
	whole_plan: list[dict[str, str]] = []
	for row in json.loads(decision):
		entry_id = cstr(row.get("entry_id")).strip()
		if "correction_required" in row:
			item = {"correction_required": cstr(row.get("correction_required"))}
		else:
			item = {"problem": cstr(row.get("problem")), "correction": cstr(row.get("correction"))}
		if entry_id:
			by_entry.setdefault(entry_id, []).append(item)
		else:
			whole_plan.append(item)
	return by_entry, whole_plan


def _entry_action(
	*, not_proceeding: bool, need_origin: bool, mutable: bool, funded: bool, has_issue: bool, can_open: bool,
) -> str:
	"""§10.4 — the row's action names what the department will actually do
	there, in the artboard's own words.

	An excluded requirement's only action is to bring it back, and a direct
	requirement is never "excluded" in the first place, so it is never
	restorable. A read-only plan still opens its requirements — it just does
	not change them. A reader the entry read would refuse (a Planner looking
	at someone else's departmental plan) gets no action rather than a link
	into a masked denial (§12.1's own rule about dead-end links).

	U05-CORRECTION — a Need-origin row Procurement returned a comment against
	still routes to funding details, even though it is already funded: that
	is exactly what the department is being asked to revisit."""
	if not mutable:
		return "View details" if can_open else ""
	if not_proceeding:
		return "Include in this year's departmental plan" if need_origin else ""
	if need_origin and (not funded or has_issue):
		return "Enter funding details"
	return "Review details"


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
	if version:
		# §5.1 — the coverage boundary is established at command time, not by
		# a browser timestamp: `open_departmental_plan`'s own "reused" branch
		# already re-syncs a mutable Draft against the Need register on every
		# re-open, and `submit_departmental_plan` re-syncs again just before
		# it checks coverage. This read was the one caller left out — an
		# Author or Head of Department who only ever *views* the record (the
		# workspace's own "Continue"/"Review" cards route straight here, never
		# through `open_departmental_plan` again) saw the entries as they
		# stood when the Draft was first opened, with no visible sign that a
		# Need accepted afterwards was missing (found live 22 Sep 2026).
		# `refresh_draft_entries` is idempotent and a no-op on anything but a
		# Draft, so calling it from a read is safe.
		needs_intake.refresh_draft_entries(version)
	entries = []
	incomplete = 0
	total_specified = 0.0
	issues_by_entry, plan_issues = _returned_issues(version) if version else ({}, [])
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
			has_issue = bool(issues_by_entry.get(row.entry_id))
			# §10.4's own wording: what the row *is* to the department, not an
			# internal readiness label. U05-CORRECTION — a funded row is not
			# simply "Included" while Procurement's comment against it is
			# still open.
			if not_proceeding:
				status, kind = "Not included this year", "muted"
			elif has_issue:
				status, kind = "Correction requested", "attention"
			elif funded:
				status, kind = "Included", "live"
			else:
				status, kind = "Funding details needed", "attention"
			entries.append(
				{
					"entry_id": row.entry_id,
					"source_origin": row.source_origin,
					"title": row.title,
					# Never shown as raw text (the artboards never print a Need's
					# bare id) — only navigation ("Correct the source requirement")
					# reads this, and only for a Need-origin entry.
					"need": cstr(row.need) if need_origin else "",
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
						not_proceeding=not_proceeding, need_origin=need_origin, funded=funded, has_issue=has_issue,
						mutable=version.version_status == "Draft" and access in ("author", "hod"),
						can_open=access in ("author", "hod", "oversight"),
					),
					# §10.4 U03-FUNDING — the funding panel opens beneath the
					# row it belongs to; nothing else navigates away from U02.
					"opens_funding_panel": bool(
						need_origin and not not_proceeding
						and version.version_status == "Draft" and access in ("author", "hod")
					),
					"issues": issues_by_entry.get(row.entry_id, []),
				}
			)
	mutable = bool(version) and version.version_status == "Draft" and access in ("author", "hod")
	ready = bool(entries) and incomplete == 0
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
	is_correction = bool(version and cstr(version.returned_from_submission))
	# U05-CORRECTION's own context row: which submission Procurement returned,
	# a distinct fact from whichever submission is currently Accepted — a
	# plan need never have been accepted at all for a correction cycle to
	# exist (found live 23 Sep 2026: this and `candidate_submission_number`
	# below only ever populated for the accepted-update path, so the
	# artboard's "Returned submission"/"Correction submission" pair never
	# rendered for a plain first-cycle correction).
	returned_submission_number = (
		int(frappe.db.get_value("Departmental Plan Submission", version.returned_from_submission, "submission_number") or 0)
		if is_correction else None
	)
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
			pronoun = "it" if len(gaps) == 1 else "them"
			update_notice = {
				"title": f"{len(gaps)} accepted {plural} not in this plan",
				"text": (
					f"{', '.join(gaps)} accepted after this plan was accepted. "
					f"Create an update to carry {pronoun} into a new draft version, fund {pronoun} and resubmit."
				),
			}
	attestation = ATTESTATION.format(department=labels["department_name"], financial_year=labels["financial_year"])
	# §5.1 — the window gates only a first submission; a plan that has been
	# submitted before may still send corrections and updates after close.
	window = _window_display(root.fiscal_year)
	if window["state"] == "Closed" and _has_any_submission(root):
		window = {**window, "display": "Closed · corrections and updates may still be submitted"}
	# U02-AUTHOR-DRAFT/U03-FUNDING/U03-EXCLUDED-ROW — this is fixed, invariant
	# copy: it tells the Author who submits next, in every mutable state
	# they can be in, not only once the plan happens to be ready (found live
	# 23 Sep 2026: gating this on `ready` meant an in-progress Draft showed no
	# footer note at all, contradicting every Author artboard).
	submit_hint = ""
	if mutable and access != "hod":
		submit_hint = "Your Head of User Department must review and submit this plan."
	# FU-14 — the record route never strands the actor who holds the open task
	open_task = None
	if access == "planner" and version and version.version_status == "Submitted":
		task = frappe.db.get_value(
			"Departmental Plan Validation Task", {"dpp_version": version.name, "status": "Open"}, ["name", "submission"], as_dict=True,
		)
		if task and not authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task.submission):
			open_task = {"label": "Review submission", "route": ["procurement-planning", "dpp-review", task.name]}
	# PLN v1.27 §5.7 second table / §10.1A.2 — the next step and journey
	# for this viewer. On the Author's own Draft the tracker is reduced to one
	# line, because the summary strip and table already fill the first view.
	from kentender_procurement.procurement_planning.services import next_step as plan_next_step

	guidance = plan_next_step.dpp_guidance(
		root, version, actor=actor, access=access, ready=ready, incomplete=incomplete,
		entry_count=len(entries), window_closed=window["state"] == "Closed" and not _has_any_submission(root),
		is_correction=is_correction, update_in_progress=update_in_progress,
		reduced=access == "author" and bool(version) and version.version_status == "Draft",
	)
	return {
		"outcome": "OK",
		"next_step": guidance["next_step"],
		"journey": guidance["journey"],
		"access": access,
		"dpp_reference": root.dpp_reference,
		"record_version": int(root.record_version or 0),
		"current_state": root.current_state,
		"display_state": display_state,
		"accepted_submission_number": accepted_number,
		"returned_submission_number": returned_submission_number,
		"candidate_submission_number": version.version_number if version and (is_correction or update_in_progress) else None,
		"is_correction": is_correction,
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
		# §10.16 C02-DPP-CLOSED — the closed submission window named as the
		# setting it is, above the submit action it blocks. Draft saving and
		# returned-correction work are untouched and stay where they are.
		"missing_setting": missing_setting.dpp_submissions(fiscal_year=root.fiscal_year, user=actor),
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
		"has_returned_issues": bool(issues_by_entry) or bool(plan_issues),
		# §4.4 — an issue against the whole submission rather than one entry.
		"plan_issues": plan_issues,
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
	# Same read-path gap as `get_departmental_plan` (found live 22 Sep 2026):
	# without this, an Author deep-linking straight to this editor to fund a
	# Need accepted after the Draft was last opened gets a false "not found"
	# below — idempotent and a no-op on anything but a Draft.
	needs_intake.refresh_draft_entries(version)
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
			# Never shown as raw text — only navigation ("Correct the source
			# requirement") reads this, and only for a Need-origin entry.
			"need": cstr(entry.need) if entry.source_origin == needs_intake.NEED_ORIGIN else "",
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


def _snapshot_role(snapshot: str) -> str:
	"""The business role recorded in a frozen assignment snapshot. A snapshot
	that cannot be read yields nothing rather than a guess."""
	try:
		return cstr(json.loads(snapshot or "{}").get("business_role"))
	except (ValueError, TypeError):
		return ""


def _json_map(value) -> dict[str, str]:
	"""A decision's JSON column reads back as text or already decoded."""
	if isinstance(value, dict):
		return {cstr(k): cstr(v) for k, v in value.items()}
	try:
		parsed = json.loads(cstr(value) or "{}")
	except ValueError:
		return {}
	return {cstr(k): cstr(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}


def _validation_guidance(root, version, task_doc, actor: str) -> dict[str, Any]:
	from kentender_core.services import next_step as ns
	from kentender_procurement.procurement_planning.services import next_step as plan_next_step

	if task_doc.status == "Open":
		# The review task is the Planner's screen: a Planner who is also the
		# department's certifier reads it as a Planner, so segregation (not
		# the department's "waiting for Procurement") is what they are told.
		access = "planner" if authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor) else (
			authz.dpp_read_profile(root.organisation_unit, actor) or "oversight"
		)
		return plan_next_step.dpp_guidance(
			root, version, actor=actor, access=access, ready=True, incomplete=0, entry_count=1,
			window_closed=False, is_correction=False, update_in_progress=False,
		)
	decision = frappe.db.get_value("Departmental Plan Validation Decision", task_doc.decision, ["decision", "actor", "decided_at"], as_dict=True) if task_doc.decision else None
	if not decision:
		return {"next_step": ns.not_involved(), "journey": None}
	who = cstr(frappe.db.get_value("User", decision.actor, "full_name") or decision.actor)
	accepted = decision.decision == "Accept departmental plan"
	verb = "Accepted" if accepted else "Returned to the department"
	done = ns.answer(ns.KIND_DONE, headline=f"{verb} by {who} on {_eat(decision.decided_at)}", stage=plan_next_step.DPP_ACCEPTED if accepted else plan_next_step.DPP_PREPARATION)
	journey = (
		ns.journey(plan_next_step.DPP_STAGES, complete=True) if accepted
		# §10.1A.1 return rule applied to §10.1A.2: the correction restarts
		# at Preparation; the return itself stays in the history.
		else ns.journey(plan_next_step.DPP_STAGES, current=plan_next_step.DPP_PREPARATION)
	)
	return {"next_step": done, "journey": journey}


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

	def _budget_line_display(budget_line: str) -> str:
		# U06's own artboard reads "Digital health infrastructure programme ·
		# MOH-BL-DHI-2027" — the name first, since that is what tells the
		# Planner what the money is for, with the code after it. This used
		# to show only `.get("reference")`, the bare code alone with no
		# name at all (found live 22 Sep 2026).
		line = line_labels.get(cstr(budget_line), {})
		reference = cstr(line.get("reference")) or cstr(budget_line)
		if not reference:
			return "—"
		return f"{line.get('title')} · {reference}" if line.get("title") else reference

	# A decided review shows what the decision recorded, per requirement —
	# not empty disabled selects (found live 25 Sep 2026). Read before the
	# rows so each can carry its own recorded pair.
	decision_ref = cstr(task_doc.decision)
	decided = None
	recorded_types: dict[str, str] = {}
	recorded_categories: dict[str, str] = {}
	if decision_ref:
		decided = frappe.db.get_value(
			"Departmental Plan Validation Decision", decision_ref,
			["decision", "decided_at", "actor", "classifications", "derived_categories"], as_dict=True,
		)
		recorded_types = _json_map(decided.pop("classifications", None))
		recorded_categories = _json_map(decided.pop("derived_categories", None))
		decided["decided_at_display"] = _eat(decided.get("decided_at"))
		decided["actor_name"] = cstr(frappe.db.get_value("User", decided.get("actor"), "full_name") or decided.get("actor"))

	rows = [
		{
			"entry_id": row.get("entry_id"),
			"title": row.get("title"),
			"recorded_requirement_type": recorded_types.get(cstr(row.get("entry_id")), ""),
			"recorded_category": recorded_categories.get(cstr(row.get("entry_id")), ""),
			"source_label": f"Accepted Need · {row.get('need')}" if row.get("need") else "Direct requirement",
			"quantity_display": _quantity_display(row.get("quantity"), cstr(row.get("unit"))),
			"quantity_number": _quantity_number(row.get("quantity")),
			"unit_label": cstr(row.get("unit")),
			"required_by_display": _date(row.get("required_by_date")),
			"budget_line_display": _budget_line_display(row.get("budget_line")),
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
	maker_checker_blocked = authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=submission.name)
	# PLN v1.27 §10.5 — U06's next step and DPP journey. An open review is
	# the Planner's turn (or Waiting under segregation); a decided one states
	# the recorded decision, whatever the plan has done since, never
	# "Decision required" over disabled controls (found live 25 Sep 2026).
	guidance = _validation_guidance(root, version, task_doc, actor)
	return {
		"outcome": "OK",
		"next_step": guidance["next_step"],
		"journey": guidance["journey"],
		# §10.5 U06-CLASSIFICATION-MISSING — the count is the Planner's unsaved
		# choices, which only the screen holds; the words stay the server's.
		"classification_prompt": {
			"one": "Select the requirement type for 1 requirement, then accept",
			"many": "Select the requirement type for {count} requirements, then accept",
		},
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
			# §10.5 — the capacity the person certified in. A certification by
			# someone with no authority to give it is a different fact from one
			# given by the Head of Department, and the Planner deciding on it
			# needs to see which. Taken from the assignment snapshot the
			# submission froze, so a later change cannot rewrite it (§13).
			"submitted_capacity": _snapshot_role(submission.get("authority_snapshot")),
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
