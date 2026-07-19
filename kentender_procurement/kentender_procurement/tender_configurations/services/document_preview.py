# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-03 Tender Document Preview + Publication Handoff (D1-WG3; WG-04 merged)."""

from __future__ import annotations

import html
import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_COMPLETED,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_RETURNED_FOR_CORRECTION,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.preview_presentation import (
	assert_no_forbidden_preview_markers,
	render_evaluation_section,
	render_forms_section,
	render_information_system_requirements,
	render_inventory_section,
	render_price_section,
	render_schedule_section,
	render_scc_section,
	render_tds_section,
	render_technical_requirements_section,
)

PREVIEW_NOT_GENERATED = "Not generated"
PREVIEW_GENERATED = "Generated"
PREVIEW_EXCEPTION = "Exception found"
PREVIEW_CONFIRMED = "Confirmed"

OUTLINE = (
	("cover_invitation", "Cover and Invitation"),
	("itt", "Instructions to Tenderers"),
	("tds", "Tender Data Sheet"),
	("evaluation", "Evaluation and Qualification Criteria"),
	("forms", "Tendering Forms"),
	("price", "Price Schedules"),
	("requirements_is", "Requirements of the Information System"),
	("technical", "Technical Requirements"),
	("schedule", "Implementation Schedule"),
	("inventory", "System Inventory and Background"),
	("gcc", "General Conditions of Contract"),
	("scc", "Special Conditions of Contract"),
	("contract_forms", "Contract Forms and Appendices"),
)

CONFIRM_CHECKS = (
	("approved_configuration", "Generated from approved configuration"),
	("locked_standard_text", "Locked standard text preserved"),
	("tds_scc", "Tender-specific values included"),
	("requirements_schedules", "Procuring Entity’s Requirements included"),
	("forms_price", "Bidder submission forms included"),
	("no_publication", "This action does not publish the tender"),
)

PACKAGE_ITEMS = (
	"Generated tender document (HTML preview)",
	"Tender configuration reference",
	"Approved STD version",
	"Readiness report",
	"Review approval record",
	"Preview confirmation record",
)

# Outline key → STD Engine section key fragment (matched via render_section_preview).
LOCKED_STD_SECTIONS = {
	"itt": "itt",
	"gcc": "gcc",
}


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


def _esc(val: Any) -> str:
	return html.escape(cstr(val or ""), quote=True)


def _section_html(key: str, title: str, body: str, *, locked: bool = False) -> str:
	# `locked` retained for call-site clarity; do not print internal metadata into PDF.
	_ = locked
	return (
		f'<section class="kt-preview-section" id="sec-{_esc(key)}">'
		f"<h2>{_esc(title)}</h2>{body}</section>"
	)


def _resolve_package_id(doc) -> str:
	return cstr(getattr(doc, "std_version", None) or "").strip()


def _build_parameter_values(doc) -> dict[str, str]:
	"""Best-effort STD placeholder map from TDS / common config fields."""
	values: dict[str, str] = {}
	tds = _parse_blob(getattr(doc, "tds_values", None))
	for key, val in tds.items():
		if isinstance(val, (dict, list)):
			continue
		values[cstr(key)] = cstr(val)
	context = build_configuration_context(doc)
	for alias, source in (
		("tender_title", cstr(doc.tender_title or "")),
		("procuring_entity", cstr(context.get("procuring_entity_name") or "")),
		("procurement_package_ref", cstr(context.get("procurement_package_ref") or "")),
		("configuration_ref", cstr(doc.configuration_ref or doc.name)),
	):
		if source and alias not in values:
			values[alias] = source
	return values


def _render_locked_std_body(
	package_id: str,
	outline_key: str,
	section_suffix: str,
	parameter_values: dict[str, str],
) -> tuple[str, str | None, str | None]:
	"""Return (body_html, render_hash, error_message)."""
	if not package_id:
		return (
			"",
			None,
			frappe._("Bound STD version is required to render locked section {0}.").format(
				outline_key
			),
		)
	try:
		from kentender_procurement.std_engine.services.render_service import (
			render_section_preview,
		)

		result = render_section_preview(
			package_id,
			section_suffix,
			parameter_values=parameter_values,
		)
	except Exception as exc:
		return "", None, cstr(exc)
	if not int(result.get("clauseCount") or 0):
		return (
			"",
			None,
			frappe._("No locked clauses found for section {0} in STD version {1}.").format(
				outline_key, package_id
			),
		)
	return cstr(result.get("html") or ""), cstr(result.get("renderHash") or "") or None, None


def _json_list(doc, field: str, key: str) -> list[dict]:
	raw = getattr(doc, field, None)
	if isinstance(raw, list):
		return [r for r in raw if isinstance(r, dict)]
	if isinstance(raw, str) and raw.strip().startswith("["):
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, list):
				return [r for r in parsed if isinstance(r, dict)]
		except (TypeError, ValueError):
			pass
	blob = _parse_blob(raw)
	rows = blob.get(key) or blob.get("items") or blob.get("requirements") or []
	return [r for r in rows if isinstance(r, dict)]


def assemble_preview_html(
	doc,
) -> tuple[str, list[dict[str, str]], str | None, dict[str, Any]]:
	"""Return (html, outline, exception_message, meta)."""
	context = build_configuration_context(doc)
	outline = [{"key": k, "label": lab} for k, lab in OUTLINE]
	exception: str | None = None
	package_id = _resolve_package_id(doc)
	parameter_values = _build_parameter_values(doc)
	render_hashes: dict[str, str] = {}

	pe_name = cstr(context.get("procuring_entity_name") or "").strip()
	tds = _parse_blob(getattr(doc, "tds_values", None))
	requirements = _json_list(doc, "it_requirements", "requirements")[:50]
	sched = _parse_blob(getattr(doc, "implementation_schedule", None))
	milestones = [m for m in (sched.get("milestones") or []) if isinstance(m, dict)][:40]
	inv = _parse_blob(getattr(doc, "system_inventory", None))
	inv_items = [
		i
		for i in (inv.get("inventory_items") or inv.get("items") or [])
		if isinstance(i, dict)
	][:40]
	inv_na = bool(
		inv.get("not_applicable")
		or inv.get("inventory_not_applicable")
		or cstr(inv.get("status") or "").strip().upper() in ("N/A", "NA", "NOT APPLICABLE")
	)
	price_items = _json_list(doc, "price_schedule", "price_items")[:50]
	criteria = _json_list(doc, "evaluation_setup", "criteria")[:50]
	form_items = _json_list(doc, "forms_and_evidence", "submission_items")[:50]
	contract_values = _json_list(doc, "contract_values", "contract_values")[:50]
	default_currency = cstr(tds.get("tender_currency") or "KES").strip() or "KES"

	tds_html, tds_err = render_tds_section(tds)
	eval_html, eval_err = render_evaluation_section(criteria, requirements)
	price_html, price_err = render_price_section(
		price_items, requirements, default_currency=default_currency
	)
	req_html, req_err = render_information_system_requirements(requirements)
	tech_html, tech_err = render_technical_requirements_section(requirements)
	forms_html, forms_err = render_forms_section(form_items)
	sched_html, sched_err = render_schedule_section(milestones)
	inv_html, inv_err = render_inventory_section(inv_items, not_applicable=inv_na)
	scc_html, scc_err = render_scc_section(contract_values)
	for err in (
		tds_err,
		eval_err,
		price_err,
		req_err,
		tech_err,
		forms_err,
		sched_err,
		inv_err,
		scc_err,
	):
		if err:
			exception = exception or err

	locked_bodies: dict[str, str] = {}
	for outline_key, section_suffix in LOCKED_STD_SECTIONS.items():
		body, render_hash, err = _render_locked_std_body(
			package_id, outline_key, section_suffix, parameter_values
		)
		if err:
			exception = exception or err
			locked_bodies[outline_key] = (
				f'<p class="kt-preview-exception">{_esc(err)}</p>'
			)
		else:
			locked_bodies[outline_key] = body
			if render_hash:
				render_hashes[outline_key] = render_hash
			forbid = assert_no_forbidden_preview_markers(body)
			if forbid:
				exception = exception or forbid

	parts = [
		'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Tender Document Preview</title>',
		"<style>",
		"body{font-family:Georgia,serif;margin:2rem;color:#191c1e;line-height:1.45;}",
		".kt-preview-watermark{position:fixed;top:40%;left:10%;font-size:2.5rem;opacity:.12;",
		"transform:rotate(-24deg);pointer-events:none;font-weight:700;}",
		".kt-preview-section{margin-bottom:2rem;page-break-inside:avoid;}",
		"h1{color:#002244;} h2{color:#002244;border-bottom:1px solid #c4c6cf;padding-bottom:.25rem;}",
		"h3{color:#002244;font-size:1rem;margin:1rem 0 .35rem;}",
		".kt-preview-table{width:100%;border-collapse:collapse;font-size:13px;}",
		".kt-preview-table th,.kt-preview-table td{border:1px solid #c4c6cf;padding:6px 8px;text-align:left;vertical-align:top;}",
		".kt-preview-exception{color:#ba1a1a;font-size:13px;}",
		".kt-preview-criterion,.kt-preview-requirement,.kt-preview-form-item{margin:0 0 1rem;}",
		"</style></head><body>",
		'<div class="kt-preview-watermark">PREVIEW — NOT FOR PUBLICATION</div>',
		f"<h1>{_esc(doc.tender_title)}</h1>",
		f"<p><strong>Procuring Entity:</strong> {_esc(pe_name)}<br>"
		f"<strong>Tender title:</strong> {_esc(doc.tender_title)}<br>"
		f"<strong>Standard tender document:</strong> {_esc(doc.std_document_label)}</p>",
		_section_html(
			"cover_invitation",
			"Cover and Invitation",
			f"<p>The {_esc(pe_name)} invites tenders for {_esc(doc.tender_title)}. "
			f"This invitation and the accompanying tendering documents are issued by "
			f"{_esc(pe_name)}.</p>",
		),
		_section_html(
			"itt",
			"Instructions to Tenderers",
			locked_bodies.get("itt") or "<p></p>",
			locked=True,
		),
		_section_html(
			"tds",
			"Tender Data Sheet",
			tds_html
			or f'<p class="kt-preview-exception">{_esc(tds_err or "Tender Data Sheet unavailable.")}</p>',
		),
		_section_html(
			"evaluation",
			"Evaluation and Qualification Criteria",
			eval_html
			or f'<p class="kt-preview-exception">{_esc(eval_err or "Evaluation criteria unavailable.")}</p>',
		),
		_section_html("forms", "Tendering Forms", forms_html or ""),
		_section_html(
			"price",
			"Price Schedules",
			price_html
			or f'<p class="kt-preview-exception">{_esc(price_err or "Price schedule unavailable.")}</p>',
		),
		_section_html(
			"requirements_is",
			"Requirements of the Information System",
			req_html or "",
		),
		_section_html(
			"technical",
			"Technical Requirements",
			tech_html or "",
		),
		_section_html(
			"schedule",
			"Implementation Schedule",
			sched_html or "",
		),
		_section_html(
			"inventory",
			"System Inventory and Background",
			inv_html
			or f'<p class="kt-preview-exception">{_esc(inv_err or "System inventory unavailable.")}</p>',
		),
		_section_html(
			"gcc",
			"General Conditions of Contract",
			locked_bodies.get("gcc") or "<p></p>",
			locked=True,
		),
		_section_html(
			"scc",
			"Special Conditions of Contract",
			scc_html or "",
		),
		_section_html(
			"contract_forms",
			"Contract Forms and Appendices",
			f"<p>Contract forms and appendices shall be completed in accordance with the "
			f"special conditions and contract values configured for this tender issued by "
			f"{_esc(pe_name)}.</p>",
		),
		"</body></html>",
	]
	html_doc = "".join(parts)
	forbid = assert_no_forbidden_preview_markers(html_doc)
	if forbid:
		exception = exception or forbid
	meta = {
		"std_version": package_id,
		"render_hashes": render_hashes,
	}
	return html_doc, outline, exception, meta


def _status_label(status: str) -> str:
	return {
		PREVIEW_NOT_GENERATED: "Not generated",
		PREVIEW_GENERATED: "Generated",
		PREVIEW_EXCEPTION: "Exception found",
		PREVIEW_CONFIRMED: "Confirmed",
	}.get(status, status)


def _dto(doc, blob: dict[str, Any], package: dict[str, Any] | None = None) -> dict[str, Any]:
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	preview_status = cstr(blob.get("preview_status") or PREVIEW_NOT_GENERATED)
	confirmed = preview_status == PREVIEW_CONFIRMED
	pkg = package if package is not None else _parse_blob(getattr(doc, "publication_package", None))
	sent = bool(pkg.get("sent_at"))

	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"std_family_label": context["std_family_label"],
		"standard_tender_document_label": cstr(doc.std_document_label or ""),
		"review_status_label": _STATUS_LABELS.get(status, status),
		"preview_status": preview_status,
		"preview_status_label": _status_label(preview_status),
		"generated_at": blob.get("generated_at") or "",
		"generated_by": blob.get("generated_by") or "",
		"confirmed_at": blob.get("confirmed_at") or "",
		"outline": blob.get("outline") or [{"key": k, "label": lab} for k, lab in OUTLINE],
		"preview_html": blob.get("preview_html") or "",
		"watermark_label": (
			"PREVIEW CONFIRMED — READY FOR PUBLICATION HANDOFF"
			if confirmed
			else "PREVIEW — NOT FOR PUBLICATION"
		),
		"confirmation_checks": [
			{"id": cid, "label": lab} for cid, lab in CONFIRM_CHECKS
		],
		"user_confirmed": 1 if blob.get("user_confirmed") else 0,
		"can_regenerate_preview": status
		in (STATUS_APPROVED_FOR_PREVIEW, STATUS_READY_FOR_PUBLICATION, STATUS_COMPLETED),
		"can_confirm_preview": preview_status == PREVIEW_GENERATED and status == STATUS_APPROVED_FOR_PREVIEW,
		"can_return_for_correction": preview_status in (PREVIEW_GENERATED, PREVIEW_CONFIRMED)
		and status != STATUS_COMPLETED,
		"show_publication_package": confirmed or sent,
		"publication_package": {
			"items": list(PACKAGE_ITEMS),
			"note": (
				"This action does not publish the tender. "
				"It sends the approved package to the publication workflow."
			),
			"sent_at": pkg.get("sent_at") or "",
			"sent_by": pkg.get("sent_by") or "",
			"can_send": confirmed and not sent and status == STATUS_READY_FOR_PUBLICATION,
			"sent": sent,
		},
		"render_exception": blob.get("render_exception"),
		"std_version": blob.get("std_version") or cstr(getattr(doc, "std_version", None) or ""),
		"render_hashes": blob.get("render_hashes") or {},
		"can_download_preview_pdf": bool(blob.get("preview_html"))
		and preview_status
		in (PREVIEW_GENERATED, PREVIEW_CONFIRMED, PREVIEW_EXCEPTION),
		"download_pdf_method": (
			"kentender_procurement.tender_configurations.download_tender_configuration_document_preview_pdf"
		),
		"home_route": "it-tender-configuration-overview",
		"context": context,
		"entry_allowed": status
		in (
			STATUS_APPROVED_FOR_PREVIEW,
			STATUS_READY_FOR_PUBLICATION,
			STATUS_COMPLETED,
		),
	}


def get_document_preview(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	return _dto(doc, _parse_blob(getattr(doc, "document_preview", None)))


def generate_document_preview(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if cstr(doc.status) not in (
		STATUS_APPROVED_FOR_PREVIEW,
		STATUS_READY_FOR_PUBLICATION,
		STATUS_COMPLETED,
	):
		frappe.throw(
			frappe._("Preview is available only after review approval."),
			title="PREVIEW_NOT_ALLOWED",
		)
	prior = _parse_blob(getattr(doc, "document_preview", None))
	html_doc, outline, exception, meta = assemble_preview_html(doc)
	blob = {
		"preview_status": PREVIEW_EXCEPTION if exception else PREVIEW_GENERATED,
		"preview_html": html_doc,
		"outline": outline,
		"generated_at": str(now_datetime()),
		"generated_by": frappe.session.user,
		"render_exception": exception,
		"user_confirmed": 0,
		"std_version": meta.get("std_version") or "",
		"render_hashes": meta.get("render_hashes") or {},
	}
	# Invalidate prior confirmation / handoff so regenerate cannot skip re-confirm.
	if prior.get("preview_status") == PREVIEW_CONFIRMED or prior.get("user_confirmed"):
		blob.pop("confirmed_at", None)
		blob.pop("confirmed_by", None)
	if cstr(doc.status) in (STATUS_READY_FOR_PUBLICATION, STATUS_COMPLETED):
		doc.status = STATUS_APPROVED_FOR_PREVIEW
	if getattr(doc, "publication_package", None):
		doc.publication_package = None
	doc.document_preview = json.dumps(blob)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return _dto(doc, blob)


def confirm_document_preview(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	blob = _parse_blob(getattr(doc, "document_preview", None))
	if cstr(blob.get("preview_status")) != PREVIEW_GENERATED:
		frappe.throw(frappe._("Generate a preview before confirming."), title="PREVIEW_STATE")
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	if not payload.get("confirm_ready_for_handoff"):
		frappe.throw(
			frappe._("Confirm that you have reviewed the generated tender document."),
			title="PREVIEW_CONFIRM",
		)
	blob["preview_status"] = PREVIEW_CONFIRMED
	blob["user_confirmed"] = 1
	blob["confirmed_at"] = str(now_datetime())
	blob["confirmed_by"] = frappe.session.user
	# Update watermark text in stored HTML
	html_doc = cstr(blob.get("preview_html") or "")
	html_doc = html_doc.replace(
		"PREVIEW — NOT FOR PUBLICATION",
		"PREVIEW CONFIRMED — READY FOR PUBLICATION HANDOFF",
	)
	blob["preview_html"] = html_doc
	doc.document_preview = json.dumps(blob)
	doc.status = STATUS_READY_FOR_PUBLICATION
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return _dto(doc, blob)


def return_preview_for_correction(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	section = cstr(payload.get("affected_section") or "").strip()
	reason = cstr(payload.get("reason") or "").strip()
	if not section or not reason:
		frappe.throw(
			frappe._("Affected section and correction reason are required."),
			title="RETURN_REQUIRED",
		)
	blob = _parse_blob(getattr(doc, "document_preview", None))
	blob["return"] = {
		"section": section,
		"reason": reason,
		"severity": cstr(payload.get("severity") or ""),
		"owning_cfg_step": cstr(payload.get("owning_cfg_step") or ""),
		"at": str(now_datetime()),
		"by": frappe.session.user,
	}
	blob["preview_status"] = PREVIEW_NOT_GENERATED
	blob["user_confirmed"] = 0
	blob["preview_html"] = ""
	blob.pop("confirmed_at", None)
	blob.pop("confirmed_by", None)
	doc.document_preview = json.dumps(blob)
	doc.status = STATUS_RETURNED_FOR_CORRECTION
	if getattr(doc, "publication_package", None):
		doc.publication_package = None
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob)
	out["returned"] = True
	return out


def download_document_preview_pdf(configuration_id: str) -> None:
	"""Stream watermarked preview HTML as PDF (Frappe get_pdf)."""
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	blob = _parse_blob(getattr(doc, "document_preview", None))
	html_doc = cstr(blob.get("preview_html") or "").strip()
	if not html_doc:
		frappe.throw(
			frappe._("Generate a document preview before downloading PDF."),
			title="PREVIEW_PDF_EMPTY",
		)
	pdf_bytes = _html_to_pdf_bytes(html_doc)
	ref = cstr(doc.configuration_ref or doc.name).replace("/", "-")
	frappe.local.response.filename = f"{ref}-preview.pdf"
	frappe.local.response.filecontent = pdf_bytes
	frappe.local.response.type = "download"


def _html_to_pdf_bytes(html_doc: str) -> bytes:
	"""Render preview HTML to PDF via wkhtmltopdf (pdfkit), same engine as frappe.utils.pdf.get_pdf."""
	import pdfkit

	options = {
		"page-size": "A4",
		"encoding": "UTF-8",
		"disable-javascript": "",
		"disable-local-file-access": "",
		"quiet": "",
	}
	return pdfkit.from_string(html_doc, False, options=options)


def send_to_publication_workflow(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	blob = _parse_blob(getattr(doc, "document_preview", None))
	if cstr(blob.get("preview_status")) != PREVIEW_CONFIRMED:
		frappe.throw(
			frappe._("Confirm the preview before sending to publication workflow."),
			title="HANDOFF_STATE",
		)
	if cstr(doc.status) not in (STATUS_READY_FOR_PUBLICATION, STATUS_COMPLETED):
		frappe.throw(
			frappe._("Configuration is not ready for publication handoff."),
			title="HANDOFF_STATE",
		)
	readiness = _parse_blob(getattr(doc, "readiness_report", None))
	review = _parse_blob(getattr(doc, "review_workspace", None))
	package = {
		"items": list(PACKAGE_ITEMS),
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"std_document_label": cstr(doc.std_document_label or ""),
		"readiness_last_checked_at": readiness.get("last_checked_at") or "",
		"review_approved_at": review.get("approved_at") or "",
		"preview_confirmed_at": blob.get("confirmed_at") or "",
		"preview_html_available": 1 if blob.get("preview_html") else 0,
		"sent_at": str(now_datetime()),
		"sent_by": frappe.session.user,
		"note": (
			"This action does not publish the tender. "
			"It sends the approved package to the publication workflow."
		),
	}
	doc.publication_package = json.dumps(package)
	doc.status = STATUS_COMPLETED
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob, package)
	out["sent"] = True
	return out
