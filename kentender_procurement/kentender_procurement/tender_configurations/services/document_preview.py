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
	STATUS_AWAITING_PUBLICATION_SETUP,
	STATUS_COMPLETED,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_RETURNED_FOR_CORRECTION,
	STATUS_SENT_TO_PUBLICATION,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.preview_presentation import (
	assert_no_forbidden_preview_markers,
	assert_price_units_normalized,
	assert_scc_values_complete,
	build_render_validation_report,
	generation_block,
	render_evaluation_section,
	render_forms_section,
	render_information_system_requirements,
	render_inventory_section,
	render_price_section,
	render_schedule_section,
	render_scc_section,
	render_tds_section,
	render_technical_requirements_section,
	strip_pe_only_contract_form_notes,
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
	"Generated tender PDF",
	"Tender configuration reference",
	"Procurement package reference",
	"STD version",
	"Configuration version",
	"Bidder submission schema",
	"Evaluation schema",
	"Price schedule schema",
	"Forms/evidence schema",
	"Contract carry-forward values",
	"Readiness report",
	"Review approval record",
	"Preview confirmation record",
	"Document hash",
)

# Outline key → STD Engine section key fragment (matched via render_section_preview).
LOCKED_STD_SECTIONS = {
	"itt": "itt",
	"gcc": "gcc",
	"forms": "forms",
	"contract_forms": "contract_forms",
}

LOCKED_STD_SECTION_LABELS = {
	"itt": "Instructions to Tenderers",
	"gcc": "General Conditions of Contract",
	"forms": "Tendering Forms",
	"contract_forms": "Contract Forms",
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


def _locked_unavailable_block(outline_key: str, *, detail: str = "") -> dict[str, str]:
	from kentender_procurement.tender_configurations.services.preview_presentation import (
		LOCKED_STD_UNAVAILABLE_MSG,
	)

	section = LOCKED_STD_SECTION_LABELS.get(outline_key, outline_key)
	message = LOCKED_STD_UNAVAILABLE_MSG.format(section=section)
	if detail:
		message = f"{message} ({detail})"
	return generation_block(
		blocking_area=f"STD Engine — {section}",
		message=message,
		action="Load approved STD Engine text before generating preview.",
	)


def _assert_active_std_package(package_id: str) -> dict[str, str] | None:
	if not package_id:
		return _locked_unavailable_block("itt", detail="no STD version bound")
	if not frappe.db.exists("STD Version", package_id):
		return _locked_unavailable_block("itt", detail=f"{package_id} not found")
	lifecycle = cstr(frappe.db.get_value("STD Version", package_id, "lifecycle_state"))
	if lifecycle != "ACTIVE":
		return _locked_unavailable_block(
			"itt",
			detail=f"{package_id} lifecycle is {lifecycle or 'unknown'}, required ACTIVE",
		)
	# Fixture sample packages are never sufficient for legal preview.
	if package_id.upper().startswith("TCFG-FIXTURE") or "FIXTURE" in package_id.upper():
		return _locked_unavailable_block(
			"itt",
			detail="fixture STD sample text is not permitted for tender preview",
		)
	try:
		from kentender_procurement.std_engine.services.form_locked_text import (
			assert_form_locked_text_complete,
		)

		if package_id == "KE-PPRA-IT-2022-04" or package_id.startswith("KE-PPRA-IT"):
			assert_form_locked_text_complete(package_id)
	except Exception as exc:
		return _locked_unavailable_block("forms", detail=cstr(exc))
	return None


def _render_locked_std_body(
	package_id: str,
	outline_key: str,
	section_suffix: str,
	parameter_values: dict[str, str],
) -> tuple[str, str | None, dict[str, str] | None]:
	"""Return (body_html, render_hash, generation_block). LOCKED_STD_TEXT only."""
	if not package_id:
		return "", None, _locked_unavailable_block(outline_key)
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
		return "", None, _locked_unavailable_block(outline_key, detail=cstr(exc))
	if not int(result.get("clauseCount") or 0):
		return "", None, _locked_unavailable_block(outline_key)
	body = cstr(result.get("html") or "")
	# Reject known fixture sample fragments if they ever leak into official package.
	if outline_key in ("itt", "gcc") and "tenderer shall prepare the tender in accordance" in body.lower():
		return "", None, _locked_unavailable_block(
			outline_key,
			detail="fixture sample clause detected",
		)
	return body, cstr(result.get("renderHash") or "") or None, None


def _format_block_message(block: dict[str, Any] | str | None) -> str:
	if not block:
		return ""
	if isinstance(block, str):
		return block
	area = cstr(block.get("blocking_area") or "").strip()
	message = cstr(block.get("message") or "").strip()
	action = cstr(block.get("action") or "").strip()
	parts = [p for p in (area, message, action) if p]
	return " ".join(parts) if parts else message


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
	"""Return (html, outline, exception_message, meta).

	On blocking readiness/generation errors: return empty HTML (never embed diagnostics
	in the tender artifact). Structured block lives in meta["generation_block"].
	"""
	context = build_configuration_context(doc)
	outline = [{"key": k, "label": lab} for k, lab in OUTLINE]
	package_id = _resolve_package_id(doc)
	parameter_values = _build_parameter_values(doc)
	render_hashes: dict[str, str] = {}

	pe_name = cstr(context.get("procuring_entity_name") or "").strip()
	tds = _parse_blob(getattr(doc, "tds_values", None))
	# No hard 50-row cap — E1 NSSF PoC and full IT tenders need honest matrices.
	requirements = _json_list(doc, "it_requirements", "requirements")
	sched = _parse_blob(getattr(doc, "implementation_schedule", None))
	milestones = [m for m in (sched.get("milestones") or []) if isinstance(m, dict)]
	single_delivery = (
		sched.get("single_delivery") if isinstance(sched.get("single_delivery"), dict) else {}
	)
	delivery_approach = cstr(sched.get("delivery_approach") or "")
	inv = _parse_blob(getattr(doc, "system_inventory", None))
	inv_items = [
		i
		for i in (inv.get("inventory_items") or inv.get("items") or [])
		if isinstance(i, dict)
	]
	inv_na = bool(
		inv.get("not_applicable")
		or inv.get("inventory_not_applicable")
		or cstr(inv.get("status") or "").strip().upper() in ("N/A", "NA", "NOT APPLICABLE")
	)
	price_items = _json_list(doc, "price_schedule", "price_items")
	criteria = _json_list(doc, "evaluation_setup", "criteria")
	form_items = _json_list(doc, "forms_and_evidence", "submission_items")
	contract_values = _json_list(doc, "contract_values", "contract_values")
	default_currency = cstr(tds.get("tender_currency") or "KES").strip() or "KES"
	poc_audit_notes = _extract_poc_audit_notes(doc)

	from kentender_procurement.tender_configurations.services.preview_presentation import (
		electronic_schema_reference_html,
	)

	block: dict[str, str] | None = _assert_active_std_package(package_id)
	if not block:
		block = assert_price_units_normalized(price_items)
	if not block:
		block = assert_scc_values_complete(
			contract_values,
			std_version=cstr(getattr(doc, "std_version", None) or package_id or ""),
			tds=tds,
			requirements=requirements,
			milestones=milestones,
			single_delivery=single_delivery,
			delivery_approach=delivery_approach,
		)

	tds_html, tds_err = render_tds_section(tds)
	eval_html, eval_err = render_evaluation_section(criteria, requirements)
	price_html, price_err = render_price_section(
		price_items, requirements, default_currency=default_currency
	)
	req_html, req_err = render_information_system_requirements(requirements)
	tech_html, tech_err = render_technical_requirements_section(requirements)
	evidence_html, evidence_err = render_forms_section(form_items)
	sched_html, sched_err = render_schedule_section(milestones)
	inv_html, inv_err = render_inventory_section(inv_items, not_applicable=inv_na)
	scc_html, scc_err = render_scc_section(
		contract_values,
		std_version=cstr(getattr(doc, "std_version", None) or package_id or ""),
		tds=tds,
		requirements=requirements,
		milestones=milestones,
		single_delivery=single_delivery,
		delivery_approach=delivery_approach,
	)

	if not block:
		for err in (
			tds_err,
			eval_err,
			price_err,
			req_err,
			tech_err,
			evidence_err,
			sched_err,
			inv_err,
			scc_err,
		):
			if err:
				block = err if isinstance(err, dict) else generation_block(
					blocking_area="Document Preview",
					message=cstr(err),
					action="Resolve the readiness issue, then regenerate.",
				)
				break

	locked_bodies: dict[str, str] = {}
	if not block:
		for outline_key, section_suffix in LOCKED_STD_SECTIONS.items():
			body, render_hash, err = _render_locked_std_body(
				package_id, outline_key, section_suffix, parameter_values
			)
			if err:
				block = err
				break
			# PE preparation notes may appear in forms and/or contract_forms locked text.
			if outline_key in ("forms", "contract_forms"):
				body = strip_pe_only_contract_form_notes(body)
			locked_bodies[outline_key] = body
			if render_hash:
				render_hashes[outline_key] = render_hash
			forbid = assert_no_forbidden_preview_markers(body)
			if forbid:
				block = forbid
				break

	audit_report = build_render_validation_report(
		doc=doc,
		tds=tds,
		contract_values=contract_values,
		price_items=price_items,
		poc_audit_notes=poc_audit_notes,
		generation_block=block,
		std_version=package_id,
	)
	meta: dict[str, Any] = {
		"std_version": package_id,
		"render_hashes": render_hashes,
		"generation_block": block,
		"render_validation_report": audit_report,
		"render_block_types": {
			"itt": "LOCKED_STD_TEXT",
			"gcc": "LOCKED_STD_TEXT",
			"forms": "LOCKED_STD_TEXT",
			"contract_forms": "LOCKED_STD_TEXT",
			"tds": "CONFIGURED_TABLE",
			"evaluation": "CONFIGURED_TABLE",
			"requirements_is": "CONFIGURED_TABLE",
			"technical": "CONFIGURED_TABLE",
			"price": "CONFIGURED_TABLE",
			"schedule": "CONFIGURED_TABLE",
			"inventory": "CONFIGURED_TABLE",
			"scc": "CONFIGURED_TABLE",
			"electronic_ref": "ELECTRONIC_SCHEMA_REFERENCE",
		},
	}
	if block:
		# Option 1: do not generate a tender PDF/HTML artifact with diagnostics.
		return "", outline, _format_block_message(block), meta

	forms_body = (
		(locked_bodies.get("forms") or "")
		+ electronic_schema_reference_html()
		+ (evidence_html or "")
	)
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
		".kt-preview-electronic-ref{font-style:italic;margin:0.75rem 0;}",
		"</style></head><body>",
		'<div class="kt-preview-watermark">PREVIEW — NOT FOR PUBLICATION</div>',
		f"<h1>{_esc(doc.tender_title)}</h1>",
		f"<p><strong>Procuring Entity:</strong> {_esc(pe_name)}<br>"
		f"<strong>Tender title:</strong> {_esc(doc.tender_title)}<br>"
		f"<strong>Standard tender document:</strong> {_esc(doc.std_document_label)}</p>",
		_section_html(
			"cover_invitation",
			"Cover and Invitation",
			"<p data-render-block=\"PARAMETERIZED_STD_TEXT\">"
			f"This tender document is issued by {_esc(pe_name)} for {_esc(doc.tender_title)}. "
			"The Instructions to Tenderers and General Conditions of Contract are the locked "
			"standard text of the bound Official Standard Tender Document.</p>"
			+ electronic_schema_reference_html(),
		),
		_section_html(
			"itt",
			"Instructions to Tenderers",
			locked_bodies.get("itt") or "<p></p>",
			locked=True,
		),
		_section_html("tds", "Tender Data Sheet", tds_html or ""),
		_section_html(
			"evaluation",
			"Evaluation and Qualification Criteria",
			eval_html or "",
		),
		_section_html("forms", "Tendering Forms", forms_body, locked=True),
		_section_html("price", "Price Schedules", price_html or ""),
		_section_html(
			"requirements_is",
			"Requirements of the Information System",
			req_html or "",
		),
		_section_html("technical", "Technical Requirements", tech_html or ""),
		_section_html("schedule", "Implementation Schedule", sched_html or ""),
		_section_html("inventory", "System Inventory and Background", inv_html or ""),
		_section_html(
			"gcc",
			"General Conditions of Contract",
			locked_bodies.get("gcc") or "<p></p>",
			locked=True,
		),
		_section_html("scc", "Special Conditions of Contract", scc_html or ""),
		_section_html(
			"contract_forms",
			"Contract Forms and Appendices",
			locked_bodies.get("contract_forms") or "<p></p>",
			locked=True,
		),
		"</body></html>",
	]
	html_doc = "".join(parts)
	forbid = assert_no_forbidden_preview_markers(html_doc)
	if forbid:
		meta["generation_block"] = forbid
		meta["render_validation_report"] = build_render_validation_report(
			doc=doc,
			tds=tds,
			contract_values=contract_values,
			price_items=price_items,
			poc_audit_notes=poc_audit_notes,
			generation_block=forbid,
			std_version=package_id,
		)
		return "", outline, _format_block_message(forbid), meta
	return html_doc, outline, None, meta


def _extract_poc_audit_notes(doc) -> dict[str, Any]:
	"""AUDIT_ONLY notes stamped on bidder schema / configuration artifact."""
	schema = _parse_blob(getattr(doc, "bidder_submission_schema", None))
	art = schema.get("_kentender_artifact") if isinstance(schema, dict) else None
	if isinstance(art, dict):
		notes = art.get("poc_audit_notes")
		if isinstance(notes, dict):
			return notes
	return {}


def _status_label(status: str) -> str:
	return {
		PREVIEW_NOT_GENERATED: "Not generated",
		PREVIEW_GENERATED: "Generated",
		PREVIEW_EXCEPTION: "Exception found",
		PREVIEW_CONFIRMED: "Preview Confirmed",
	}.get(status, status)


def _dto(doc, blob: dict[str, Any], package: dict[str, Any] | None = None) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		package_summary_dto,
		publication_summary_dto,
	)

	context = dict(build_configuration_context(doc))
	status = cstr(doc.status or "")
	preview_status = cstr(blob.get("preview_status") or PREVIEW_NOT_GENERATED)
	confirmed = preview_status == PREVIEW_CONFIRMED
	pkg = package if package is not None else _parse_blob(getattr(doc, "publication_package", None))
	sent = bool(pkg.get("sent_at")) or status in (
		STATUS_AWAITING_PUBLICATION_SETUP,
		STATUS_SENT_TO_PUBLICATION,
	)
	block = blob.get("generation_block") if isinstance(blob.get("generation_block"), dict) else None
	# Preview generation blocks are distinct from WG-01 readiness findings — surface them
	# in the shared Issues cell so "None" does not contradict the exception banner.
	if preview_status == PREVIEW_EXCEPTION and block:
		step = cstr(block.get("owner_step") or "").strip()
		context["issues_label"] = (
			f"Preview blocked · {step}" if step else "Preview blocked"
		)
		context["issues_alert"] = 1

	confirmed_pkg_name = cstr(getattr(doc, "confirmed_document_package", None) or "")
	publication_name = cstr(getattr(doc, "it_publication_record", None) or "")
	confirmed_pkg = package_summary_dto(confirmed_pkg_name)
	publication = publication_summary_dto(publication_name)
	download_label = (
		"Download Confirmed PDF" if confirmed else "Download Preview PDF"
	)

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
			"PACKAGE CONFIRMED — READY FOR PUBLICATION SETUP"
			if confirmed
			else "PREVIEW — NOT FOR PUBLICATION"
		),
		"confirmation_checks": [
			{"id": cid, "label": lab} for cid, lab in CONFIRM_CHECKS
		],
		"user_confirmed": 1 if blob.get("user_confirmed") else 0,
		# F1 §4: regenerate disabled after Confirm Tender Package.
		"can_regenerate_preview": (
			status == STATUS_APPROVED_FOR_PREVIEW
			and preview_status in (PREVIEW_NOT_GENERATED, PREVIEW_GENERATED, PREVIEW_EXCEPTION)
			and not confirmed
		),
		"can_confirm_preview": preview_status == PREVIEW_GENERATED
		and status
		in (STATUS_APPROVED_FOR_PREVIEW, STATUS_READY_FOR_PUBLICATION)
		and not confirmed,
		# Return remains available until published.
		"can_return_for_correction": (
			preview_status in (PREVIEW_GENERATED, PREVIEW_CONFIRMED)
			and status
			in (
				STATUS_APPROVED_FOR_PREVIEW,
				STATUS_READY_FOR_PUBLICATION,
				STATUS_AWAITING_PUBLICATION_SETUP,
				STATUS_SENT_TO_PUBLICATION,
			)
		),
		"show_publication_package": confirmed or sent,
		"publication_package": {
			"items": confirmed_pkg.get("items") or list(PACKAGE_ITEMS),
			"note": (
				"This action does not publish the tender. "
				"The confirmed package is ready for publication setup."
			),
			"sent_at": pkg.get("sent_at") or "",
			"sent_by": pkg.get("sent_by") or "",
			# v7: no separate Send step — can_send always false; continue to setup instead.
			"can_send": False,
			"sent": sent,
			"continue_to_setup": 1 if (confirmed or sent) and publication.get("publication_id") else 0,
			"publication_setup_route": (
				f"publication-setup/{publication.get('publication_id')}"
				if publication.get("publication_id")
				else "publications"
			),
			"document_hash": confirmed_pkg.get("document_hash") or blob.get("document_hash") or "",
			"package_id": confirmed_pkg.get("package_id") or "",
			"package_status": confirmed_pkg.get("package_status") or "",
			"publication_id": publication.get("publication_id") or "",
			"publication_status": publication.get("status") or "",
		},
		"confirmed_document_package": confirmed_pkg,
		"it_publication_record": publication,
		"render_exception": blob.get("render_exception"),
		"generation_block": blob.get("generation_block"),
		"render_validation_report": blob.get("render_validation_report") or {},
		"std_version": blob.get("std_version") or cstr(getattr(doc, "std_version", None) or ""),
		"render_hashes": blob.get("render_hashes") or {},
		"document_hash": blob.get("document_hash")
		or confirmed_pkg.get("document_hash")
		or "",
		# Tender PDF only when clean Generated/Confirmed — never on Exception found.
		"can_download_preview_pdf": bool(blob.get("preview_html"))
		and preview_status in (PREVIEW_GENERATED, PREVIEW_CONFIRMED),
		"download_pdf_label": download_label,
		"download_pdf_method": (
			"kentender_procurement.tender_configurations.download_tender_configuration_document_preview_pdf"
		),
		"home_route": "it-tender-configuration-overview",
		"context": context,
		"entry_allowed": status
		in (
			STATUS_APPROVED_FOR_PREVIEW,
			STATUS_READY_FOR_PUBLICATION,
			STATUS_SENT_TO_PUBLICATION,
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
		STATUS_SENT_TO_PUBLICATION,
		STATUS_COMPLETED,
	):
		frappe.throw(
			frappe._("Preview is available only after review approval."),
			title="PREVIEW_NOT_ALLOWED",
		)
	prior = _parse_blob(getattr(doc, "document_preview", None))
	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		configuration_is_locked_for_edit,
	)

	# F1 §4: regenerate is disabled after Confirm Preview (confirmed state / active package).
	# Note: STATUS_READY_FOR_PUBLICATION alone is not enough — UI-00 also uses that status
	# for configs that have not yet confirmed a preview.
	if (
		cstr(prior.get("preview_status")) == PREVIEW_CONFIRMED
		or prior.get("user_confirmed")
		or configuration_is_locked_for_edit(doc.name)
		or cstr(doc.status)
		in (STATUS_AWAITING_PUBLICATION_SETUP, STATUS_SENT_TO_PUBLICATION, STATUS_COMPLETED)
	):
		frappe.throw(
			frappe._(
				"Preview regeneration is disabled after Confirm Tender Package. "
				"Return for Correction before regenerating."
			),
			title="PREVIEW_LOCKED",
		)
	html_doc, outline, exception, meta = assemble_preview_html(doc)
	blocked = bool(exception) or bool(meta.get("generation_block"))
	blob = {
		"preview_status": PREVIEW_EXCEPTION if blocked else PREVIEW_GENERATED,
		# Never persist diagnostic HTML into the tender artifact.
		"preview_html": "" if blocked else html_doc,
		"outline": outline,
		"generated_at": str(now_datetime()),
		"generated_by": frappe.session.user,
		"render_exception": exception,
		"generation_block": meta.get("generation_block"),
		"render_validation_report": meta.get("render_validation_report") or {},
		"user_confirmed": 0,
		"std_version": meta.get("std_version") or "",
		"render_hashes": meta.get("render_hashes") or {},
	}
	if getattr(doc, "publication_package", None):
		doc.publication_package = None
	doc.document_preview = json.dumps(blob)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_f1_publication_lock = True
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
		"PACKAGE CONFIRMED — READY FOR PUBLICATION SETUP",
	)
	html_doc = html_doc.replace(
		"PREVIEW CONFIRMED — READY FOR PUBLICATION HANDOFF",
		"PACKAGE CONFIRMED — READY FOR PUBLICATION SETUP",
	)
	blob["preview_html"] = html_doc

	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		create_confirmed_package,
		create_publication_record,
	)

	pkg = create_confirmed_package(doc, preview_blob=blob)
	blob["document_hash"] = cstr(pkg.document_hash or "")
	blob["confirmed_package_id"] = pkg.name

	# v7 §17: Confirm Tender Package auto-creates/opens Publication Setup.
	pub = create_publication_record(doc, pkg)
	package = {
		"items": list(PACKAGE_ITEMS),
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"std_document_label": cstr(doc.std_document_label or ""),
		"std_version": cstr(pkg.std_version or ""),
		"configuration_version": cstr(pkg.configuration_version or ""),
		"document_hash": cstr(pkg.document_hash or ""),
		"confirmed_package_id": pkg.name,
		"publication_id": pub.name,
		"publication_status": cstr(pub.status or ""),
		"sent_at": str(now_datetime()),
		"sent_by": frappe.session.user,
		"note": (
			"This action does not publish the tender. "
			"The confirmed package is ready for publication setup."
		),
	}
	doc.document_preview = json.dumps(blob)
	doc.publication_package = json.dumps(package)
	doc.status = STATUS_AWAITING_PUBLICATION_SETUP
	doc.confirmed_document_package = pkg.name
	doc.it_publication_record = pub.name
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_f1_publication_lock = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob, package)
	out["publication_id"] = pub.name
	out["publication_setup_route"] = f"publication-setup/{pub.name}"
	out["package_confirmed"] = True
	return out


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
	blob.pop("document_hash", None)
	blob.pop("confirmed_package_id", None)

	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		cancel_publication_for_configuration,
		get_active_package_name,
		invalidate_package,
	)

	pkg_name = cstr(getattr(doc, "confirmed_document_package", None) or "") or get_active_package_name(
		doc.name
	)
	if pkg_name:
		invalidate_package(pkg_name, reason=reason)
	cancel_publication_for_configuration(doc.name, reason=reason)

	doc.document_preview = json.dumps(blob)
	doc.status = STATUS_RETURNED_FOR_CORRECTION
	doc.publication_package = None
	doc.confirmed_document_package = None
	doc.it_publication_record = None
	# Force re-path through readiness / review / preview (F1 §9).
	doc.readiness_report = None
	doc.review_workspace = None
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_f1_publication_lock = True
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
	preview_status = cstr(blob.get("preview_status") or "")
	if preview_status == PREVIEW_EXCEPTION or blob.get("generation_block"):
		frappe.throw(
			frappe._(
				"Preview PDF is unavailable while generation is blocked. "
				"Resolve the readiness issue and regenerate a clean preview."
			),
			title="PREVIEW_PDF_BLOCKED",
		)
	if preview_status not in (PREVIEW_GENERATED, PREVIEW_CONFIRMED):
		frappe.throw(
			frappe._("Generate a document preview before downloading PDF."),
			title="PREVIEW_PDF_EMPTY",
		)
	html_doc = cstr(blob.get("preview_html") or "").strip()
	if not html_doc:
		frappe.throw(
			frappe._("Generate a document preview before downloading PDF."),
			title="PREVIEW_PDF_EMPTY",
		)
	pdf_bytes = _html_to_pdf_bytes(html_doc)
	ref = cstr(doc.configuration_ref or doc.name).replace("/", "-")
	suffix = "confirmed" if preview_status == PREVIEW_CONFIRMED else "preview"
	frappe.local.response.filename = f"{ref}-{suffix}.pdf"
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
	"""Thin shim: v7 Confirm already opens Publication Setup. Idempotent return."""
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	blob = _parse_blob(getattr(doc, "document_preview", None))
	if cstr(blob.get("preview_status")) != PREVIEW_CONFIRMED:
		# Prefer canonical confirm path (creates package + publication).
		return confirm_document_preview(
			configuration_id, {"confirm_ready_for_handoff": 1}
		)

	from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
		PACKAGE_DOCTYPE,
		create_publication_record,
		get_active_package_name,
		get_open_publication_name,
	)

	pkg_name = cstr(getattr(doc, "confirmed_document_package", None) or "") or get_active_package_name(
		doc.name
	)
	if not pkg_name or not frappe.db.exists(PACKAGE_DOCTYPE, pkg_name):
		frappe.throw(
			frappe._("Confirmed tender document package is missing. Confirm the package again."),
			title="HANDOFF_STATE",
		)
	pkg_doc = frappe.get_doc(PACKAGE_DOCTYPE, pkg_name)
	pub_name = cstr(getattr(doc, "it_publication_record", None) or "") or get_open_publication_name(
		doc.name
	)
	if pub_name and frappe.db.exists("IT Tender Publication Record", pub_name):
		pub = frappe.get_doc("IT Tender Publication Record", pub_name)
	else:
		pub = create_publication_record(doc, pkg_doc)

	package = _parse_blob(getattr(doc, "publication_package", None)) or {
		"items": list(PACKAGE_ITEMS),
		"document_hash": cstr(pkg_doc.document_hash or ""),
		"confirmed_package_id": pkg_doc.name,
	}
	package["publication_id"] = pub.name
	package["publication_status"] = cstr(pub.status or "")
	package["sent_at"] = package.get("sent_at") or str(now_datetime())
	package["sent_by"] = package.get("sent_by") or frappe.session.user
	package["note"] = (
		"This action does not publish the tender. "
		"The confirmed package is ready for publication setup."
	)
	doc.publication_package = json.dumps(package)
	doc.it_publication_record = pub.name
	if cstr(doc.status) not in (STATUS_AWAITING_PUBLICATION_SETUP, STATUS_SENT_TO_PUBLICATION):
		doc.status = STATUS_AWAITING_PUBLICATION_SETUP
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_f1_publication_lock = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob, package)
	out["sent"] = True
	out["publication_id"] = pub.name
	out["publication_setup_route"] = f"publication-setup/{pub.name}"
	return out


def confirm_tender_package(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	"""v7 canonical Confirm Tender Package (alias of confirm_document_preview)."""
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = dict(payload or {})
	payload.setdefault("confirm_ready_for_handoff", 1)
	return confirm_document_preview(configuration_id, payload)
