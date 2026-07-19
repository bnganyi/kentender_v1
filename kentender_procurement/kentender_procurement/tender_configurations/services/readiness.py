# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-01 Readiness Check & Report (D1-WG1).

Aggregates CFG-01…CFG-09 blockers/warnings. Does not edit configuration values.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.constants import (
	STATUS_READY_FOR_REVIEW,
	STATUS_RETURNED_FOR_CORRECTION,
	STATUS_UNDER_REVIEW,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_NEEDS_ATTENTION,
	STEP_NOT_STARTED,
	STEP_ROUTES,
)

CFG_AREAS = (
	("CFG-01", "Tender Profile", "tender_profile"),
	("CFG-02", "Tender Data Sheet", "tds"),
	("CFG-03", "IT Requirements", "it_requirements"),
	("CFG-04", "Implementation Schedule", "implementation_schedule"),
	("CFG-05", "System Inventory & Bidder Background", "system_inventory"),
	("CFG-06", "Price Schedule", "price_schedule"),
	("CFG-07", "Evaluation Setup", "evaluation_setup"),
	("CFG-08", "Forms & Evidence", "forms_and_evidence"),
	("CFG-09", "Contract Values", "contract_values"),
)

OVERALL_READY = "Ready for Review"
OVERALL_WARNINGS = "Ready with Warnings"
OVERALL_NOT_READY = "Not Ready for Review"
OVERALL_NOT_RUN = "Check Not Run"

WHY_BLOCKER = "This must be fixed before the configuration can be submitted for review."
WHY_WARNING = "Reviewers will see this warning if you submit without resolving it."


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except (TypeError, ValueError):
			return {}
	return {}


def _load_cfg_probe(step_id: str, configuration_id: str) -> dict[str, Any]:
	loaders: dict[str, Callable[[str], dict[str, Any]]] = {
		"CFG-01": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.profile",
			fromlist=["get_configuration_profile"],
		).get_configuration_profile(cid),
		"CFG-02": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.tds",
			fromlist=["get_configuration_tds"],
		).get_configuration_tds(cid),
		"CFG-03": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.it_requirements",
			fromlist=["get_configuration_requirements"],
		).get_configuration_requirements(cid),
		"CFG-04": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.implementation_schedule",
			fromlist=["get_configuration_implementation_schedule"],
		).get_configuration_implementation_schedule(cid),
		"CFG-05": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.system_inventory",
			fromlist=["get_configuration_system_inventory"],
		).get_configuration_system_inventory(cid),
		"CFG-06": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.price_schedule",
			fromlist=["get_configuration_price_schedule"],
		).get_configuration_price_schedule(cid),
		"CFG-07": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.evaluation_setup",
			fromlist=["get_configuration_evaluation_setup"],
		).get_configuration_evaluation_setup(cid),
		"CFG-08": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.forms_and_evidence",
			fromlist=["get_configuration_forms_and_evidence"],
		).get_configuration_forms_and_evidence(cid),
		"CFG-09": lambda cid: __import__(
			"kentender_procurement.tender_configurations.services.contract_values",
			fromlist=["get_configuration_contract_values"],
		).get_configuration_contract_values(cid),
	}
	fn = loaders.get(step_id)
	if not fn:
		return {}
	try:
		return fn(configuration_id) or {}
	except Exception:
		frappe.log_error(title=f"Readiness probe failed for {step_id}")
		return {
			"can_continue": False,
			"blockers": [{"code": "probe_failed", "message": f"{step_id} could not be checked."}],
			"warnings": [],
		}


def _finding(
	*,
	severity: str,
	area: str,
	issue: str,
	owner_screen: str,
	owner_route: str,
	required_action: str,
	why: str,
	action_label: str,
) -> dict[str, str]:
	return {
		"severity": severity,
		"area": area,
		"issue": issue,
		"why_it_matters": why,
		"required_action": required_action,
		"owner_screen": owner_screen,
		"owner_route": owner_route,
		"action_label": action_label,
	}


def _build_findings_and_checklist(configuration_id: str) -> tuple[list[dict], list[dict], int, int]:
	findings: list[dict[str, str]] = []
	checklist: list[dict[str, Any]] = []
	blocker_count = 0
	warning_count = 0

	for step_id, title, _key in CFG_AREAS:
		probe = _load_cfg_probe(step_id, configuration_id)
		route = STEP_ROUTES.get(step_id, "")
		blockers = list(probe.get("blockers") or [])
		warnings = list(probe.get("warnings") or [])
		can = bool(probe.get("can_continue"))
		# Some CFG get APIs use blocker_count without can_continue
		if "can_continue" not in probe and "blocker_count" in probe:
			can = int(probe.get("blocker_count") or 0) == 0

		step_warning_findings = 0
		for b in blockers:
			msg = cstr(b.get("message") if isinstance(b, dict) else b).strip()
			if not msg:
				continue
			blocker_count += 1
			findings.append(
				_finding(
					severity="Blocker",
					area=title,
					issue=msg,
					owner_screen=title,
					owner_route=route,
					required_action=msg,
					why=WHY_BLOCKER,
					action_label="Fix",
				)
			)
		for w in warnings:
			msg = cstr(w.get("message") if isinstance(w, dict) else w).strip()
			if not msg:
				continue
			# Skip upstream advisory noise that is always present
			if "may change after" in msg.lower():
				continue
			warning_count += 1
			step_warning_findings += 1
			findings.append(
				_finding(
					severity="Warning",
					area=title,
					issue=msg,
					owner_screen=title,
					owner_route=route,
					required_action=msg,
					why=WHY_WARNING,
					action_label="Review",
				)
			)

		if blockers or not can:
			result = STEP_NEEDS_ATTENTION
			action = "Fix"
		elif step_warning_findings:
			result = "Warnings"
			action = "Review"
		elif can:
			result = STEP_COMPLETE
			action = "Review"
		else:
			result = STEP_NOT_STARTED
			action = "Start"

		checklist.append(
			{
				"step_id": step_id,
				"area": title,
				"check_result": result,
				"action_label": action,
				"owner_route": route,
			}
		)

	return findings, checklist, blocker_count, warning_count


def _overall(blocker_count: int, warning_count: int, checked: bool) -> str:
	if not checked:
		return OVERALL_NOT_RUN
	if blocker_count > 0:
		return OVERALL_NOT_READY
	if warning_count > 0:
		return OVERALL_WARNINGS
	return OVERALL_READY


def _guidance(overall: str, *, open_correction_count: int = 0) -> str:
	if open_correction_count > 0:
		return (
			"This configuration was returned for correction. "
			"Mark all reviewer corrections as fixed, then re-run readiness before submitting for review."
		)
	if overall == OVERALL_NOT_READY:
		return (
			"This configuration cannot be submitted for review yet. "
			"Fix the blockers listed below, then re-run the readiness check."
		)
	if overall == OVERALL_WARNINGS:
		return "This configuration has no blockers. Review the warnings before submitting for review."
	if overall == OVERALL_READY:
		return "This configuration is ready to submit for review."
	return "Run the readiness check to see whether this configuration can be submitted for review."


def _review_corrections_payload(doc) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.review_workspace import (
		get_review_corrections_for_readiness,
	)

	return get_review_corrections_for_readiness(doc)


def _dto(doc, blob: dict[str, Any], *, just_ran: bool = False) -> dict[str, Any]:
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	findings = list(blob.get("findings") or [])
	checklist = list(blob.get("checklist") or [])
	blocker_count = int(blob.get("blocker_count") or 0)
	warning_count = int(blob.get("warning_count") or 0)
	checked = bool(blob.get("last_checked_at")) or just_ran
	overall = cstr(blob.get("overall_result") or "") or _overall(blocker_count, warning_count, checked)
	corr = _review_corrections_payload(doc)
	open_correction_count = int(corr.get("open_correction_count") or 0)
	can_submit = (
		checked
		and blocker_count == 0
		and open_correction_count == 0
		and status not in (STATUS_UNDER_REVIEW,)
	)
	if blocker_count > 0:
		primary = "Fix Blockers"
	elif open_correction_count > 0:
		primary = "Fix Corrections"
	elif can_submit:
		primary = "Submit for Review"
	else:
		primary = "Run Readiness Check"

	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"std_family_label": context["std_family_label"],
		"standard_tender_document_label": cstr(doc.std_document_label or ""),
		"procuring_entity_name": context["procuring_entity_name"],
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"wizard_state_label": context.get("wizard_state_label") or _STATUS_LABELS.get(status, status),
		"overall_result": overall,
		"blocker_count": blocker_count,
		"warning_count": warning_count,
		"last_checked_at": blob.get("last_checked_at") or "",
		"last_checked_by": blob.get("last_checked_by") or "",
		"guidance": _guidance(overall, open_correction_count=open_correction_count),
		"findings": findings,
		"checklist": checklist,
		"review_corrections": corr.get("review_corrections") or [],
		"open_correction_count": open_correction_count,
		"can_submit_for_review": can_submit,
		"primary_action": primary,
		"review_route": "it-tender-configuration-review-and-approval",
		"home_route": "it-tender-configuration-overview",
		"context": context,
		"has_run": checked,
	}


def get_readiness_report(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	return _dto(doc, _parse_blob(getattr(doc, "readiness_report", None)))


def run_readiness_check(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	findings, checklist, blocker_count, warning_count = _build_findings_and_checklist(configuration_id)
	overall = _overall(blocker_count, warning_count, True)
	blob = {
		"findings": findings,
		"checklist": checklist,
		"blocker_count": blocker_count,
		"warning_count": warning_count,
		"overall_result": overall,
		"last_checked_at": str(now_datetime()),
		"last_checked_by": frappe.session.user,
	}
	doc.readiness_report = json.dumps(blob)
	doc.blocker_count = blocker_count
	doc.warning_count = warning_count
	from kentender_procurement.tender_configurations.services.review_workspace import (
		count_open_corrections_for_doc,
	)

	open_corr = count_open_corrections_for_doc(doc)
	status_now = cstr(doc.status or "")
	# Do not promote Returned → Ready while reviewer Correction Required findings remain Open.
	if (
		blocker_count == 0
		and open_corr == 0
		and status_now
		in (
			"",
			"In Progress",
			"Needs Attention",
			STATUS_RETURNED_FOR_CORRECTION,
			STATUS_READY_FOR_REVIEW,
		)
	):
		doc.status = STATUS_READY_FOR_REVIEW
	elif blocker_count > 0 and status_now not in (
		STATUS_UNDER_REVIEW,
		"Approved for Preview",
		"Ready for Publication",
		"Completed",
	):
		doc.status = "Needs Attention"
	# else: keep Returned for Correction (or other status) when open corrections remain
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return _dto(doc, blob, just_ran=True)


def submit_for_review(configuration_id: str, payload: dict[str, Any] | str | None = None) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	# Ensure a fresh check exists
	report = get_readiness_report(configuration_id)
	if not report.get("has_run"):
		report = run_readiness_check(configuration_id)
		doc = frappe.get_doc("Tender Configuration", configuration_id)
	if int(report.get("blocker_count") or 0) > 0:
		frappe.throw(
			frappe._("Fix all blockers before submitting for review."),
			title="READINESS_BLOCKERS",
		)

	from kentender_procurement.tender_configurations.services.review_workspace import (
		count_open_corrections_for_doc,
	)

	doc = frappe.get_doc("Tender Configuration", configuration_id)
	open_corr = count_open_corrections_for_doc(doc)
	if open_corr > 0:
		frappe.throw(
			frappe._(
				"Mark all reviewer corrections as fixed before submitting for review. "
				"{0} open correction(s) remain."
			).format(open_corr),
			title="REVIEW_CORRECTIONS_OPEN",
		)

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}

	blob = _parse_blob(getattr(doc, "readiness_report", None))
	blob["submitted_at"] = str(now_datetime())
	blob["submitted_by"] = frappe.session.user
	blob["warnings_acknowledged"] = 1 if payload.get("acknowledge_warnings") else 0
	doc.readiness_report = json.dumps(blob)
	doc.status = STATUS_UNDER_REVIEW
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob, just_ran=True)
	out["submitted"] = True
	out["review_route"] = "it-tender-configuration-review-and-approval"
	return out
