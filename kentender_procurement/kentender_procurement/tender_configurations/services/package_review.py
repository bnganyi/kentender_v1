# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Electronic Tender Package Review (v7 A1) — exception-based summary DTO."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.constants import (
	STATUS_AWAITING_PUBLICATION_SETUP,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_SENT_TO_PUBLICATION,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	get_active_package_name,
	get_open_publication_name,
	package_summary_dto,
	publication_summary_dto,
)


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


def _count_rows(blob: dict[str, Any], *keys: str) -> int:
	for key in keys:
		val = blob.get(key)
		if isinstance(val, list):
			return len(val)
	return 0


def _area_status(ok: bool, *, blocker: bool = False) -> str:
	if blocker:
		return "Needs attention"
	return "Ready" if ok else "Incomplete"


def get_package_review_summary(configuration_id: str) -> dict[str, Any]:
	"""A1 DTO: readiness rows, bidder experience, document output, issues/audit."""
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	preview = _parse_blob(getattr(doc, "document_preview", None))
	readiness = _parse_blob(getattr(doc, "readiness_report", None))
	review = _parse_blob(getattr(doc, "review_workspace", None))
	it_req = _parse_blob(getattr(doc, "it_requirements", None))
	impl = _parse_blob(getattr(doc, "implementation_schedule", None))
	inv = _parse_blob(getattr(doc, "system_inventory", None))
	price = _parse_blob(getattr(doc, "price_schedule", None))
	evaluation = _parse_blob(getattr(doc, "evaluation_setup", None))
	forms = _parse_blob(getattr(doc, "forms_and_evidence", None))
	contract = _parse_blob(getattr(doc, "contract_values", None))
	tds = _parse_blob(getattr(doc, "tds_values", None))

	req_count = _count_rows(it_req, "rows", "requirements", "items")
	phase_count = _count_rows(impl, "phases", "rows", "items")
	price_count = _count_rows(price, "rows", "lines", "items")
	forms_count = _count_rows(forms, "rows", "forms", "items")
	preview_status = cstr(preview.get("preview_status") or "Not generated")
	has_preview = preview_status in ("Generated", "Confirmed") and bool(preview.get("preview_html"))
	render_report = preview.get("render_validation_report") or {}
	render_issues = list(render_report.get("issues") or preview.get("render_issues") or [])
	blocker_count = int(readiness.get("blocker_count") or 0)
	approved = bool(review.get("approved_at") or review.get("decision") == "Approved")

	package_areas = [
		{
			"area": "Tender Profile",
			"status": _area_status(bool(doc.tender_title and doc.std_version)),
			"summary": "Core tender identity compiled" if doc.tender_title else "Profile incomplete",
			"route": "it-tender-configuration-tender-profile",
		},
		{
			"area": "Tender Data Sheet",
			"status": _area_status(bool(tds)),
			"summary": "Tender instructions compiled" if tds else "TDS incomplete",
			"route": "it-tender-configuration-tds",
		},
		{
			"area": "IT Requirements",
			"status": _area_status(req_count > 0),
			"summary": f"{req_count} requirements compiled" if req_count else "No requirements",
			"route": "it-tender-configuration-it-requirements",
		},
		{
			"area": "Implementation Schedule",
			"status": _area_status(phase_count > 0 or bool(impl)),
			"summary": f"{phase_count} delivery phases compiled" if phase_count else "Schedule compiled",
			"route": "it-tender-configuration-implementation-schedule",
		},
		{
			"area": "System Inventory & Bidder Background",
			"status": _area_status(bool(inv)),
			"summary": "Bidder background information compiled" if inv else "Inventory incomplete",
			"route": "it-tender-configuration-system-inventory",
		},
		{
			"area": "Price Schedule",
			"status": _area_status(price_count > 0 or bool(price)),
			"summary": f"{price_count} price lines compiled" if price_count else "Price schedule compiled",
			"route": "it-tender-configuration-price-schedule",
		},
		{
			"area": "Evaluation Setup",
			"status": _area_status(bool(evaluation)),
			"summary": "Evaluation method compiled" if evaluation else "Evaluation incomplete",
			"route": "it-tender-configuration-evaluation-setup",
		},
		{
			"area": "Forms & Evidence",
			"status": _area_status(forms_count > 0 or bool(forms)),
			"summary": (
				f"{forms_count} forms and evidence requirements compiled"
				if forms_count
				else "Forms compiled"
			),
			"route": "it-tender-configuration-forms-and-evidence",
		},
		{
			"area": "Contract Values",
			"status": _area_status(bool(contract)),
			"summary": "SCC and contract carry-forward values compiled" if contract else "Contract incomplete",
			"route": "it-tender-configuration-scc",
		},
		{
			"area": "Tender Document",
			"status": _area_status(has_preview, blocker=preview_status == "Exception found"),
			"summary": (
				"Generated tender document available"
				if has_preview
				else "Tender document not generated"
			),
			"route": "it-tender-configuration-render-preview",
		},
	]

	bidder_experience = [
		{
			"area": "Eligibility & Declarations",
			"status": "Ready" if forms else "Pending",
			"summary": "Declarations and eligibility responses",
		},
		{
			"area": "Technical Response",
			"status": "Ready" if req_count else "Pending",
			"summary": f"Respond to {req_count} IT requirements" if req_count else "No requirements",
		},
		{
			"area": "Implementation Proposal",
			"status": "Ready" if impl else "Pending",
			"summary": "Delivery phases and approach",
		},
		{
			"area": "Evidence Uploads",
			"status": "Ready" if forms else "Pending",
			"summary": "Required evidence uploads",
		},
		{
			"area": "Price Schedule",
			"status": "Ready" if price else "Pending",
			"summary": f"{price_count} price lines" if price_count else "Price response",
		},
		{
			"area": "Final Submission",
			"status": "Ready" if has_preview else "Pending",
			"summary": "Electronic bid seal and receipt",
		},
	]

	issues: list[dict[str, Any]] = []
	if blocker_count:
		for finding in readiness.get("findings") or readiness.get("blockers") or []:
			if not isinstance(finding, dict):
				continue
			if cstr(finding.get("severity") or "").lower() not in ("blocker", "high", "error"):
				continue
			issues.append(
				{
					"severity": "Blocker",
					"issue": cstr(finding.get("message") or finding.get("title") or "Readiness blocker"),
					"impact": "Blocks package confirmation",
					"fix_action": cstr(finding.get("cta_label") or "Open Full Configuration"),
					"route": cstr(finding.get("owner_route") or "it-tender-configuration-overview"),
				}
			)
	for issue in render_issues:
		if isinstance(issue, dict):
			issues.append(
				{
					"severity": cstr(issue.get("severity") or "Warning"),
					"issue": cstr(issue.get("message") or issue.get("title") or "Render issue"),
					"impact": "May affect generated tender document",
					"fix_action": "View Render Issues",
					"route": "it-tender-configuration-render-preview",
				}
			)
		elif issue:
			issues.append(
				{
					"severity": "Warning",
					"issue": cstr(issue),
					"impact": "May affect generated tender document",
					"fix_action": "View Render Issues",
					"route": "it-tender-configuration-render-preview",
				}
			)

	pkg_name = cstr(getattr(doc, "confirmed_document_package", None) or "") or get_active_package_name(
		doc.name
	)
	pub_name = cstr(getattr(doc, "it_publication_record", None) or "") or get_open_publication_name(
		doc.name
	)
	confirmed = preview_status == "Confirmed" or bool(pkg_name)
	can_confirm = (
		preview_status == "Generated"
		and approved
		and blocker_count == 0
		and has_preview
		and not confirmed
	)

	context = build_configuration_context(doc)
	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": cstr(context.get("procurement_package_ref") or ""),
		"tender_title": cstr(context.get("procurement_title") or doc.tender_title or ""),
		"procuring_entity": cstr(context.get("procuring_entity_name") or ""),
		"procurement_method": cstr(context.get("procurement_method_label") or ""),
		"standard_tender_document": cstr(
			context.get("standard_tender_document_label") or doc.std_version or ""
		),
		"package_status": (
			"Confirmed"
			if confirmed
			else "Package Review Generated"
			if has_preview
			else "Awaiting Document"
		),
		"configuration_status": cstr(doc.status or ""),
		"context": context,
		"package_readiness": package_areas,
		"bidder_experience": bidder_experience,
		"document_output": {
			"preview_status": preview_status,
			"has_preview": 1 if has_preview else 0,
			"has_confirmed_pdf": 1 if confirmed else 0,
			"document_hash": cstr(preview.get("document_hash") or ""),
			"render_issue_count": len(render_issues),
			"download_label": "Download Confirmed PDF" if confirmed else "Download Preview PDF",
		},
		"issues": issues,
		"has_blockers": 1 if issues and any(i.get("severity") == "Blocker" for i in issues) else 0,
		"audit": {
			"readiness_last_checked_at": readiness.get("last_checked_at") or "",
			"review_approved_at": review.get("approved_at") or "",
			"preview_confirmed_at": preview.get("confirmed_at") or "",
			"confirmed_by": preview.get("confirmed_by") or "",
		},
		"can_confirm_package": 1 if can_confirm else 0,
		"can_return_for_correction": 1 if cstr(doc.status) not in ("Published",) else 0,
		"package_confirmed": 1 if confirmed else 0,
		"publication_id": pub_name or "",
		"publication_route": (
			f"publication-setup/{pub_name}" if pub_name else "publications"
		),
		"confirmed_package": package_summary_dto(pkg_name),
		"publication": publication_summary_dto(pub_name),
		"full_configuration_route": "it-tender-configuration-overview",
		"in_publication_setup": 1
		if cstr(doc.status)
		in (STATUS_AWAITING_PUBLICATION_SETUP, STATUS_SENT_TO_PUBLICATION, STATUS_READY_FOR_PUBLICATION)
		and pub_name
		else 0,
	}
