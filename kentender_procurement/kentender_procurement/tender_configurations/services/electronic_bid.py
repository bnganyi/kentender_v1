# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Host-agnostic electronic bid APIs (Desk PoC now; /supplier later)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_configurations.services.schema_compiler import (
	compile_schema_for_configuration,
	persist_compiled_schema,
)

STATUS_DRAFT = "Draft"
STATUS_SEALED = "Sealed"

MOCK_UPLOAD = {
	"file_name": "evidence-mock.pdf",
	"content_type": "application/pdf",
	"byte_size": 1024,
	"mock": True,
}


def _require_admin_poc() -> None:
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Electronic bidder PoC is Administrator-only."), frappe.PermissionError)


def _require_logged_in() -> None:
	"""Portal + Desk draft access — any signed-in user (not Guest)."""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to continue."), frappe.PermissionError)


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _canonical_hash(payload: Any) -> str:
	blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _section_map(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
	return {
		cstr(s.get("key") or ""): s
		for s in (schema.get("sections") or [])
		if isinstance(s, dict) and s.get("key")
	}


def _append_audit(doc, event: str, detail: dict[str, Any] | None = None) -> None:
	doc.append(
		"audit_events",
		{
			"event": event,
			"actor": frappe.session.user,
			"event_at": now_datetime(),
			"detail_json": json.dumps(detail or {}),
		},
	)


def _get_bid(bid_id: str):
	bid_id = cstr(bid_id or "").strip()
	if not bid_id or not frappe.db.exists("Electronic Bid Submission", bid_id):
		frappe.throw(frappe._("Electronic bid not found."), title="BID_NOT_FOUND")
	return frappe.get_doc("Electronic Bid Submission", bid_id)


def _progress(schema: dict[str, Any], responses: dict[str, Any]) -> list[dict[str, Any]]:
	out = []
	for sec in schema.get("sections") or []:
		key = cstr(sec.get("key") or "")
		payload = responses.get(key) or {}
		out.append(
			{
				"key": key,
				"label": cstr(sec.get("label") or key),
				"has_responses": bool(payload),
			}
		)
	return out


def get_bidder_workspace(configuration_id: str) -> dict[str, Any]:
	_require_logged_in()
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	schema = _parse_json(getattr(doc, "bidder_submission_schema", None), {})
	if not schema.get("sections"):
		schema = persist_compiled_schema(configuration_id)
	draft_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_DRAFT},
		"name",
	)
	sealed_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_SEALED},
		"name",
		order_by="sealed_at desc",
	)
	open_bid = None
	if draft_name:
		open_bid = frappe.get_doc("Electronic Bid Submission", draft_name)
	elif sealed_name:
		open_bid = frappe.get_doc("Electronic Bid Submission", sealed_name)
	responses = _parse_json(getattr(open_bid, "responses", None), {}) if open_bid else {}
	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"std_version": cstr(doc.std_version or ""),
		"tender_title": cstr(doc.tender_title or ""),
		"submission_policy": schema.get("submission_policy"),
		"schema": schema,
		"schema_hash": schema.get("schema_hash"),
		"bid_id": open_bid.name if open_bid else None,
		"bid_status": cstr(open_bid.status) if open_bid else None,
		"responses": responses,
		"section_progress": _progress(schema, responses),
		"receipt_code": cstr(open_bid.receipt_code) if open_bid else None,
		"read_only": bool(open_bid and open_bid.status == STATUS_SEALED),
		"host_hint": "desk_poc",
	}


def create_or_get_draft(configuration_id: str, bidder_label: str | None = None) -> dict[str, Any]:
	_require_logged_in()
	configuration_id = cstr(configuration_id or "").strip()
	existing = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_DRAFT},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Electronic Bid Submission", existing)
		return _bid_dto(doc)
	cfg = frappe.get_doc("Tender Configuration", configuration_id)
	schema = persist_compiled_schema(configuration_id)
	doc = frappe.get_doc(
		{
			"doctype": "Electronic Bid Submission",
			"configuration": cfg.name,
			"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
			"std_version": cstr(cfg.std_version or ""),
			"bidder_label": cstr(bidder_label or "PoC Demo Bidder").strip() or "PoC Demo Bidder",
			"status": STATUS_DRAFT,
			"schema_hash": schema.get("schema_hash"),
			"schema_snapshot": json.dumps(schema),
			"responses": json.dumps({}),
		}
	)
	_append_audit(doc, "draft_created", {"configuration_id": configuration_id})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return _bid_dto(doc)


def save_section_responses(bid_id: str, section_key: str, payload: dict[str, Any] | str | None) -> dict[str, Any]:
	_require_logged_in()
	doc = _get_bid(bid_id)
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	section_key = cstr(section_key or "").strip()
	if not section_key:
		frappe.throw(frappe._("section_key is required."), title="BID_SECTION")
	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = payload or {}
	responses = _parse_json(doc.responses, {})
	responses[section_key] = payload
	doc.responses = json.dumps(responses)
	_append_audit(doc, "section_saved", {"section_key": section_key})
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _bid_dto(doc)


def _is_filled(val: Any) -> bool:
	if val is None:
		return False
	if isinstance(val, bool):
		return val
	if isinstance(val, (int, float)):
		return True
	if isinstance(val, dict):
		return bool(val.get("file_name") or val.get("mock") or val.get("uploaded_at"))
	if isinstance(val, list):
		return len(val) > 0
	return bool(cstr(val).strip())


def _money(val: Any) -> float | None:
	text = cstr(val).strip().replace(",", "")
	if not text:
		return None
	try:
		return float(text)
	except ValueError:
		return None


def validate_submission(bid_id: str) -> dict[str, Any]:
	_require_admin_poc()
	doc = _get_bid(bid_id)
	schema = _parse_json(doc.schema_snapshot, {})
	if not schema.get("sections"):
		schema = compile_schema_for_configuration(doc.configuration)
	responses = _parse_json(doc.responses, {})
	errors: list[dict[str, str]] = []
	by_key = _section_map(schema)

	# 1 Preliminary
	prelim = by_key.get("preliminary_documents") or {}
	for req in prelim.get("requirements") or []:
		rid = cstr(req.get("id") or "").strip()
		row = (responses.get("preliminary_documents") or {}).get(rid) or {}
		if not (_is_filled(row.get("upload")) or _is_filled(row.get("e_declaration")) or _is_filled(row)):
			errors.append(
				{
					"rule": "1",
					"code": "prelim_incomplete",
					"message": f"Preliminary requirement {rid} is incomplete.",
					"section_key": "preliminary_documents",
					"item_id": rid,
				}
			)

	# 2 Section VIII matrix
	matrix = by_key.get("technical_compliance_matrix") or {}
	matrix_resp = responses.get("technical_compliance_matrix") or {}
	for req in matrix.get("requirements") or []:
		rid = cstr(req.get("requirement_id") or req.get("id") or "").strip()
		row = matrix_resp.get(rid) or {}
		if not (_is_filled(row.get("compliant_yes_no")) and _is_filled(row.get("compliance_statement"))):
			errors.append(
				{
					"rule": "2",
					"code": "matrix_incomplete",
					"message": f"Requirement {rid} needs Yes/No and compliance statement.",
					"section_key": "technical_compliance_matrix",
					"item_id": rid,
				}
			)

	# 3 Price lines
	price_sec = by_key.get("price_schedule") or {}
	price_resp = responses.get("price_schedule") or {}
	lines_resp = price_resp.get("lines") or price_resp
	for line in price_sec.get("price_lines") or []:
		lid = cstr(line.get("line_id") or "").strip()
		row = lines_resp.get(lid) or {}
		need_unit = bool(line.get("unit_cost_required"))
		ok = _is_filled(row.get("total_cost"))
		if need_unit:
			ok = ok and _is_filled(row.get("unit_cost"))
		if not ok:
			errors.append(
				{
					"rule": "3",
					"code": "price_incomplete",
					"message": f"Price line {lid} is incomplete.",
					"section_key": "price_schedule",
					"item_id": lid,
				}
			)

	# 4 Grand total reconciliation
	summary = price_resp.get("summary") or {}
	fot = responses.get("form_of_tender") or {}
	subtotal = _money(summary.get("subtotal_excluding_vat"))
	vat = _money(summary.get("vat_16_percent"))
	grand = _money(summary.get("grand_total_inclusive_vat"))
	fot_grand = _money(fot.get("grand_total_inclusive_vat"))
	if None in (subtotal, vat, grand, fot_grand):
		errors.append(
			{
				"rule": "4",
				"code": "totals_missing",
				"message": "Price summary and Form of Tender totals are required.",
				"section_key": "price_schedule",
				"item_id": "summary",
			}
		)
	else:
		expected_vat = round(subtotal * 0.16, 2)
		expected_grand = round(subtotal + vat, 2)
		if abs(vat - expected_vat) > 0.05 or abs(grand - expected_grand) > 0.05:
			errors.append(
				{
					"rule": "4",
					"code": "totals_mismatch_internal",
					"message": "VAT/grand total do not reconcile with subtotal.",
					"section_key": "price_schedule",
					"item_id": "summary",
				}
			)
		if abs(grand - fot_grand) > 0.05:
			errors.append(
				{
					"rule": "4",
					"code": "totals_mismatch_fot",
					"message": "Form of Tender grand total must match price schedule grand total.",
					"section_key": "form_of_tender",
					"item_id": "grand_total_inclusive_vat",
				}
			)

	# 5 Professional indemnity evidence (PRELIM-05 or criterion text match)
	prelim_resp = responses.get("preliminary_documents") or {}
	indem = prelim_resp.get("PRELIM-05") or {}
	if not indem:
		for req in (by_key.get("preliminary_documents") or {}).get("requirements") or []:
			if "indemnity" in cstr(req.get("criterion") or "").lower():
				indem = prelim_resp.get(cstr(req.get("id") or "")) or {}
				break
	indem_alt = responses.get("professional_indemnity_evidence") or {}
	indem_ok = (
		_is_filled(indem.get("upload"))
		or _is_filled(indem.get("e_declaration"))
		or _is_filled(indem)
		or _is_filled(indem_alt)
	)
	if not indem_ok:
		errors.append(
			{
				"rule": "5",
				"code": "indemnity_missing",
				"message": "Professional indemnity evidence is required.",
				"section_key": "preliminary_documents",
				"item_id": "PRELIM-05",
			}
		)

	# 6 Deadline
	tds = _parse_json(
		frappe.db.get_value("Tender Configuration", doc.configuration, "tds_values"),
		{},
	)
	deadline_raw = cstr(tds.get("tender_submission_deadline") or "").strip()
	if deadline_raw:
		try:
			deadline = get_datetime(deadline_raw)
			if now_datetime() > deadline:
				errors.append(
					{
						"rule": "6",
						"code": "past_deadline",
						"message": "Submission deadline has passed.",
						"section_key": "final_declaration_and_submit",
						"item_id": "deadline",
					}
				)
		except Exception:
			pass

	# Final declarations + acknowledgements
	ack = responses.get("tender_document_acknowledgement") or {}
	if not _is_filled(ack.get("acknowledge_itt_gcc_tds")):
		errors.append(
			{
				"rule": "1",
				"code": "ack_missing",
				"message": "Tender document acknowledgement is required.",
				"section_key": "tender_document_acknowledgement",
				"item_id": "acknowledge_itt_gcc_tds",
			}
		)
	final = responses.get("final_declaration_and_submit") or {}
	for key in (
		"independent_tender_declaration",
		"fraud_and_corruption_declaration",
	):
		if not _is_filled(final.get(key)):
			errors.append(
				{
					"rule": "7",
					"code": "declaration_missing",
					"message": f"Final declaration field {key} is required.",
					"section_key": "final_declaration_and_submit",
					"item_id": key,
				}
			)

	# Tech qual
	techq = by_key.get("technical_qualification") or {}
	tq_resp = responses.get("technical_qualification") or {}
	for req in techq.get("requirements") or []:
		rid = cstr(req.get("id") or "").strip()
		row = tq_resp.get(rid) or {}
		if not (_is_filled(row.get("structured_response")) or _is_filled(row.get("upload")) or _is_filled(row)):
			errors.append(
				{
					"rule": "1",
					"code": "techqual_incomplete",
					"message": f"Technical qualification {rid} is incomplete.",
					"section_key": "technical_qualification",
					"item_id": rid,
				}
			)

	ok = len(errors) == 0
	_append_audit(
		doc,
		"validated" if ok else "submit_blocked",
		{"error_count": len(errors)},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"bid_id": doc.name,
		"ok": ok,
		"errors": errors,
		"error_count": len(errors),
	}


def _complete_responses_for_tests(schema: dict[str, Any]) -> dict[str, Any]:
	"""Build a minimal valid response payload for PoC/tests (mock uploads)."""
	by_key = _section_map(schema)
	responses: dict[str, Any] = {
		"tender_document_acknowledgement": {"acknowledge_itt_gcc_tds": True},
		"form_of_tender": {
			"total_excluding_vat": "1000000",
			"vat_16_percent": "160000",
			"grand_total_inclusive_vat": "1160000",
			"authorized_signatory_name": "Demo Signatory",
			"authorized_signatory_position": "Director",
			"company_name": "Demo Bidder Ltd",
			"signatory_declaration": True,
		},
		"confidential_business_questionnaire": {},
		"contract_terms_acknowledgement": {"acknowledge_contract_conditions": True},
		"final_declaration_and_submit": {
			"independent_tender_declaration": True,
			"fraud_and_corruption_declaration": True,
		},
		"implementation_plan": {"work_plan": "Phased delivery plan for PoC."},
	}
	cbq = by_key.get("confidential_business_questionnaire") or {}
	for field in cbq.get("fields") or []:
		fk = cstr(field.get("field_key") or "")
		if fk:
			responses["confidential_business_questionnaire"][fk] = f"PoC value for {fk}"

	prelim: dict[str, Any] = {}
	for req in (by_key.get("preliminary_documents") or {}).get("requirements") or []:
		rid = cstr(req.get("id") or "")
		prelim[rid] = {"upload": {**MOCK_UPLOAD, "uploaded_at": str(now_datetime()), "file_name": f"{rid}.pdf"}}
	responses["preliminary_documents"] = prelim

	tq: dict[str, Any] = {}
	for req in (by_key.get("technical_qualification") or {}).get("requirements") or []:
		rid = cstr(req.get("id") or "")
		tq[rid] = {
			"structured_response": f"Response for {rid}",
			"upload": {**MOCK_UPLOAD, "uploaded_at": str(now_datetime()), "file_name": f"{rid}.pdf"},
		}
	responses["technical_qualification"] = tq

	matrix: dict[str, Any] = {}
	for req in (by_key.get("technical_compliance_matrix") or {}).get("requirements") or []:
		rid = cstr(req.get("requirement_id") or req.get("id") or "")
		matrix[rid] = {
			"compliant_yes_no": "Yes",
			"compliance_statement": f"Compliant with {rid}",
			"reference_pages": "22",
			"evidence_uploads": {**MOCK_UPLOAD, "uploaded_at": str(now_datetime())},
			"deviation_note_if_any": "",
		}
	responses["technical_compliance_matrix"] = matrix

	lines: dict[str, Any] = {}
	subtotal = 0.0
	for i, line in enumerate((by_key.get("price_schedule") or {}).get("price_lines") or []):
		lid = cstr(line.get("line_id") or "")
		unit = 10000.0 + i
		qty_raw = cstr(line.get("quantity") or "1").strip()
		try:
			qty = float(qty_raw) if qty_raw else 1.0
		except ValueError:
			qty = 1.0
		total = unit * qty
		if line.get("unit_cost_required"):
			lines[lid] = {"unit_cost": str(unit), "total_cost": str(total)}
		else:
			lines[lid] = {"total_cost": str(total)}
		subtotal += total
	vat = round(subtotal * 0.16, 2)
	grand = round(subtotal + vat, 2)
	responses["price_schedule"] = {
		"lines": lines,
		"summary": {
			"subtotal_excluding_vat": str(subtotal),
			"vat_16_percent": str(vat),
			"grand_total_inclusive_vat": str(grand),
		},
	}
	responses["form_of_tender"]["total_excluding_vat"] = str(subtotal)
	responses["form_of_tender"]["vat_16_percent"] = str(vat)
	responses["form_of_tender"]["grand_total_inclusive_vat"] = str(grand)
	return responses


def fill_draft_for_tests(bid_id: str) -> dict[str, Any]:
	"""Administrator helper: fill a valid PoC payload (used by tests/Playwright)."""
	_require_admin_poc()
	doc = _get_bid(bid_id)
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	schema = _parse_json(doc.schema_snapshot, {})
	doc.responses = json.dumps(_complete_responses_for_tests(schema))
	_append_audit(doc, "section_saved", {"section_key": "*", "source": "fill_draft_for_tests"})
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _bid_dto(doc)


def submit_and_seal(bid_id: str) -> dict[str, Any]:
	_require_admin_poc()
	doc = _get_bid(bid_id)
	if cstr(doc.status) == STATUS_SEALED:
		return get_receipt(bid_id)
	result = validate_submission(bid_id)
	if not result.get("ok"):
		frappe.throw(
			frappe._("Submission validation failed ({0} errors).").format(result.get("error_count")),
			title="BID_VALIDATION_FAILED",
		)
	doc = _get_bid(bid_id)
	responses = _parse_json(doc.responses, {})
	seal_hash = _canonical_hash(
		{
			"responses": responses,
			"schema_hash": doc.schema_hash,
			"configuration_id": doc.configuration,
			"std_version": doc.std_version,
		}
	)
	receipt = f"EBD-{cstr(doc.configuration_ref or doc.configuration)}-{frappe.generate_hash(length=8).upper()}"
	now = now_datetime()
	doc.status = STATUS_SEALED
	doc.sealed_at = now
	doc.sealed_by = frappe.session.user
	doc.seal_hash = seal_hash
	doc.receipt_code = receipt
	doc.receipt_issued_at = now
	_append_audit(doc, "sealed", {"seal_hash": seal_hash})
	_append_audit(doc, "receipt_issued", {"receipt_code": receipt})
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return get_receipt(bid_id)


def get_receipt(bid_id: str) -> dict[str, Any]:
	_require_admin_poc()
	doc = _get_bid(bid_id)
	if cstr(doc.status) != STATUS_SEALED:
		frappe.throw(frappe._("Receipt is available only after seal."), title="BID_NOT_SEALED")
	return {
		"bid_id": doc.name,
		"receipt_code": doc.receipt_code,
		"sealed_at": str(doc.sealed_at) if doc.sealed_at else None,
		"receipt_issued_at": str(doc.receipt_issued_at) if doc.receipt_issued_at else None,
		"seal_hash": doc.seal_hash,
		"configuration_id": doc.configuration,
		"configuration_ref": doc.configuration_ref,
		"std_version": doc.std_version,
		"bidder_label": doc.bidder_label,
		"status": doc.status,
	}


def _bid_dto(doc) -> dict[str, Any]:
	responses = _parse_json(doc.responses, {})
	schema = _parse_json(doc.schema_snapshot, {})
	return {
		"bid_id": doc.name,
		"configuration_id": doc.configuration,
		"configuration_ref": doc.configuration_ref,
		"std_version": doc.std_version,
		"bidder_label": doc.bidder_label,
		"status": doc.status,
		"schema_hash": doc.schema_hash,
		"responses": responses,
		"section_progress": _progress(schema, responses),
		"receipt_code": doc.receipt_code,
		"read_only": doc.status == STATUS_SEALED,
	}
