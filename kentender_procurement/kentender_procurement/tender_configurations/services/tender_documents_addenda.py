# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A3 — Tender Documents & Addenda (Screen C) DTO + acknowledgement."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_datetime, now_datetime

from kentender_procurement.tender_configurations.services.available_tenders import (
	format_time_remaining,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	create_or_get_draft,
	save_section_responses,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	ACTION_CLOSED,
	ACTION_UNAVAILABLE,
	ACTION_VIEW_SUBMITTED,
	get_published_tender_overview,
	start_or_get_bid_workspace,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	persist_compiled_schema,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	portal_workspace_url,
)

DOC_ACK_KEYS = frozenset({"document_acknowledgement", "tender_document_acknowledgement"})
DOC_ACK_TYPES = frozenset({"document_acknowledgement"})

ACK_STATUS_ACTION_REQUIRED = "Action Required"
ACK_STATUS_COMPLETE = "Complete"

EMPTY_ADDENDA_MESSAGE = "No official addenda have been issued for this tender."
READINESS_NO_ADDENDA = "No addenda issued."


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to open tender documents."), frappe.PermissionError)


def portal_documents_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/documents"


def _section_key(sec: dict[str, Any]) -> str:
	return cstr(sec.get("key") or sec.get("section_key") or sec.get("id") or "").strip()


def _section_title(sec: dict[str, Any], key: str) -> str:
	return cstr(sec.get("title") or sec.get("label") or key).strip() or key


def is_document_acknowledgement_section(sec: dict[str, Any]) -> bool:
	key = _section_key(sec)
	stype = cstr(sec.get("section_type") or sec.get("type") or "").strip().lower()
	return stype in DOC_ACK_TYPES or key in DOC_ACK_KEYS


def resolve_document_acknowledgement_section(schema: dict[str, Any] | None) -> dict[str, Any] | None:
	"""Return {key, title, required, index} for the schema document_acknowledgement section."""
	sections = (schema or {}).get("sections") or []
	for idx, sec in enumerate(sections):
		if not isinstance(sec, dict):
			continue
		key = _section_key(sec)
		if not key or not is_document_acknowledgement_section(sec):
			continue
		required = True
		if "required" in sec:
			required = bool(sec.get("required"))
		elif "blocks_submission" in sec:
			required = bool(sec.get("blocks_submission"))
		return {
			"key": key,
			"title": _section_title(sec, key),
			"required": required,
			"index": idx,
			"section": sec,
		}
	return None


def extract_package_addenda(package: Any, overview: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""Return real addenda rows only — never invent. Empty when package has none."""
	candidates: list[Any] = []
	if isinstance(package, dict):
		for key in ("addenda", "official_addenda", "addendum_list"):
			raw = package.get(key)
			if isinstance(raw, list):
				candidates = raw
				break
	if not candidates and isinstance(overview, dict):
		raw = overview.get("addenda")
		if isinstance(raw, list):
			candidates = raw
	out: list[dict[str, Any]] = []
	for row in candidates:
		if not isinstance(row, dict):
			continue
		aid = cstr(row.get("id") or row.get("addendum_id") or row.get("ref") or row.get("code") or "").strip()
		title = cstr(row.get("title") or row.get("name") or aid).strip()
		if not aid and not title:
			continue
		requires = bool(
			row.get("requires_acknowledgement")
			if "requires_acknowledgement" in row
			else row.get("requires_ack", True)
		)
		out.append(
			{
				"id": aid or title,
				"title": title or aid,
				"ref": cstr(row.get("ref") or row.get("code") or aid),
				"summary": cstr(row.get("summary") or row.get("description") or ""),
				"published_at": cstr(row.get("published_at") or row.get("issued_at") or ""),
				"requires_acknowledgement": 1 if requires else 0,
				"attachment_name": cstr(row.get("attachment_name") or row.get("file_name") or ""),
				"attachment_url": cstr(row.get("attachment_url") or row.get("url") or ""),
				"view_url": cstr(row.get("view_url") or row.get("download_url") or ""),
			}
		)
	return out


def is_documents_acknowledged(payload: Any) -> bool:
	if not isinstance(payload, dict):
		return False
	if payload.get("acknowledged") in (True, 1, "1", "true", "True"):
		return True
	# Compat with E1 validate field on tender_document_acknowledgement
	if payload.get("acknowledge_itt_gcc_tds") in (True, 1, "1", "true", "True"):
		return True
	return False


def required_addenda_block_submission(
	addenda: list[dict[str, Any]] | None,
	ack_payload: Any,
) -> bool:
	"""True only when a required addendum is unacknowledged. Empty addenda → False."""
	rows = addenda or []
	if not rows:
		return False
	acked: set[str] = set()
	if isinstance(ack_payload, dict):
		for item in ack_payload.get("addenda_acknowledged") or []:
			acked.add(cstr(item).strip())
	for row in rows:
		if not row.get("requires_acknowledgement"):
			continue
		aid = cstr(row.get("id") or "").strip()
		if aid and aid not in acked:
			return True
	return False


def _desk_section_bridge(configuration_id: str) -> str:
	return f"/app/it-electronic-bidder-workspace/{quote(configuration_id, safe='')}"


def _load_schema(cfg, bid_doc) -> dict[str, Any]:
	if bid_doc:
		schema = _parse_json(getattr(bid_doc, "schema_snapshot", None), {})
		if schema.get("sections"):
			return schema
	schema = _parse_json(getattr(cfg, "bidder_submission_schema", None), {})
	if not schema.get("sections"):
		schema = persist_compiled_schema(cfg.name)
	return schema


def _enrich_documents(documents: list[dict[str, Any]], configuration_id: str) -> list[dict[str, Any]]:
	pdf_url = (
		"/api/method/kentender_procurement.tender_configurations"
		".download_tender_configuration_document_preview_pdf"
		f"?configuration_id={quote(configuration_id, safe='')}"
	)
	out: list[dict[str, Any]] = []
	for doc in documents or []:
		row = dict(doc)
		if row.get("document_key") == "tender_pdf" or (
			row.get("can_download") and cstr(row.get("type")).upper() == "PDF"
		):
			row["view_url"] = pdf_url
			row["download_url"] = pdf_url
		else:
			row.setdefault("view_url", "")
			row.setdefault("download_url", "")
		out.append(row)
	return out


def _next_section_bridge(schema: dict[str, Any], ack_index: int | None, configuration_id: str) -> str:
	bridge = _desk_section_bridge(configuration_id)
	if ack_index is None:
		return bridge
	sections = [s for s in (schema.get("sections") or []) if isinstance(s, dict) and _section_key(s)]
	if ack_index + 1 < len(sections):
		return bridge
	return bridge


def get_tender_documents_addenda(published_tender_ref: str) -> dict[str, Any]:
	"""Screen C DTO keyed by publication_ref (auth required)."""
	_require_logged_in()
	overview = get_published_tender_overview(published_tender_ref)
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)

	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(overview.get("configuration_id") or "")
	workspace_path = portal_workspace_url(pub_ref)
	documents_path = portal_documents_url(pub_ref)

	bid_sealed = False
	bid_id = overview.get("bid_id")
	if action == ACTION_VIEW_SUBMITTED or overview.get("bid_status") == STATUS_SEALED:
		bid_sealed = True
		started = start_or_get_bid_workspace(pub_ref)
		bid_id = started.get("bid_id") or bid_id
	else:
		draft = create_or_get_draft(cfg_id)
		bid_id = draft.get("bid_id")

	bid_doc = frappe.get_doc("Electronic Bid Submission", bid_id) if bid_id else None
	if bid_doc and cstr(bid_doc.status) == STATUS_SEALED:
		bid_sealed = True

	cfg = frappe.get_doc("Tender Configuration", cfg_id)
	schema = _load_schema(cfg, bid_doc)
	responses = _parse_json(getattr(bid_doc, "responses", None), {}) if bid_doc else {}

	ack_sec = resolve_document_acknowledgement_section(schema)
	section_key = (ack_sec or {}).get("key") or "document_acknowledgement"
	ack_payload = responses.get(section_key) or {}
	acknowledged = is_documents_acknowledged(ack_payload) or bid_sealed

	package = overview.get("confirmed_package") or {}
	addenda = extract_package_addenda(package, overview)
	block = required_addenda_block_submission(addenda, ack_payload)
	documents = _enrich_documents(list(overview.get("documents") or []), cfg_id)
	primary_pdf_url = ""
	for doc in documents:
		if doc.get("document_key") == "tender_pdf" and doc.get("download_url"):
			primary_pdf_url = cstr(doc.get("download_url"))
			break

	unacked_required = 0
	if addenda:
		acked_ids = {
			cstr(x).strip()
			for x in ((ack_payload.get("addenda_acknowledged") or []) if isinstance(ack_payload, dict) else [])
		}
		for row in addenda:
			if row.get("requires_acknowledgement") and cstr(row.get("id")) not in acked_ids:
				unacked_required += 1
			row["acknowledged"] = 1 if cstr(row.get("id")) in acked_ids else 0

	deadline_raw = (overview.get("dates") or {}).get("submission_deadline") or ""
	try:
		deadline_display = format_datetime(deadline_raw) if deadline_raw else "—"
	except Exception:
		deadline_display = cstr(deadline_raw) or "—"

	ack_status = ACK_STATUS_COMPLETE if acknowledged and not block else ACK_STATUS_ACTION_REQUIRED
	continue_enabled = bool(acknowledged and not block and not bid_sealed)
	ack_enabled = bool(not acknowledged and not bid_sealed)

	readiness_addenda_label = READINESS_NO_ADDENDA
	if addenda:
		if unacked_required:
			readiness_addenda_label = f"{unacked_required} pending"
		else:
			readiness_addenda_label = "Complete"

	impact = "Blocks final submission" if block else ("Ready" if acknowledged else "Acknowledgement required")
	blocker_message = ""
	if block:
		blocker_message = (
			"You must acknowledge all required addenda before submitting your bid. "
			"Submission will remain blocked until required acknowledgements are complete."
		)

	return {
		"published_tender_ref": pub_ref,
		"publication_id": overview.get("publication_id"),
		"configuration_id": cfg_id,
		"configuration_ref": overview.get("configuration_ref"),
		"bid_id": bid_id,
		"bid_status": cstr(bid_doc.status) if bid_doc else None,
		"section_key": section_key,
		"section_title": (ack_sec or {}).get("title") or "Tender Documents & Addenda",
		"tender_title": overview.get("tender_title") or "",
		"procuring_entity": overview.get("procuring_entity") or "",
		"workspace_url": workspace_path,
		"documents_url": documents_path,
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"desk_bridge_next_url": _next_section_bridge(
			schema, (ack_sec or {}).get("index"), cfg_id
		),
		"submission_deadline": deadline_raw,
		"submission_deadline_display": deadline_display,
		"time_remaining_label": format_time_remaining(deadline_raw),
		"documents": documents,
		"primary_pdf_url": primary_pdf_url,
		"package_summary": package,
		"addenda": addenda,
		"addenda_empty": 1 if not addenda else 0,
		"addenda_empty_message": EMPTY_ADDENDA_MESSAGE,
		"acknowledgement_status": ack_status,
		"documents_acknowledged": 1 if acknowledged else 0,
		"addenda_block_submission": 1 if block else 0,
		"readiness": {
			"documents_viewed_label": "Complete" if acknowledged else "Pending",
			"addenda_label": readiness_addenda_label,
			"submission_impact": impact,
			"time_remaining_label": format_time_remaining(deadline_raw),
			"blocker_message": blocker_message,
		},
		"acknowledge_label": "Acknowledge Tender Documents",
		"acknowledge_enabled": 1 if ack_enabled else 0,
		"continue_label": "Continue to Next Section",
		"continue_enabled": 1 if continue_enabled else 0,
		"continue_url": _next_section_bridge(schema, (ack_sec or {}).get("index"), cfg_id)
		if continue_enabled
		else "#",
		"back_to_checklist_label": "Back to Checklist",
		"back_to_checklist_url": workspace_path,
	}


def acknowledge_tender_documents(published_tender_ref: str) -> dict[str, Any]:
	"""Complete the schema document_acknowledgement section for this bid."""
	_require_logged_in()
	dto = get_tender_documents_addenda(published_tender_ref)
	if dto.get("documents_acknowledged"):
		return dto
	if dto.get("bid_status") == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")

	bid_id = cstr(dto.get("bid_id") or "")
	section_key = cstr(dto.get("section_key") or "document_acknowledgement")
	addenda = dto.get("addenda") or []
	# When no required addenda, bulk-ack empty list; future required rows stay unacked until per-addendum API.
	acked_ids = [
		cstr(a.get("id"))
		for a in addenda
		if a.get("requires_acknowledgement") and cstr(a.get("id"))
	]
	# Only auto-include when none require ack (empty or all optional) — Option-1: empty → no per-addendum blockers.
	if any(a.get("requires_acknowledgement") for a in addenda):
		# Future: do not silently complete required addenda via bulk screen ack alone.
		# Screen ack still marks document review; blocker helper keeps submission blocked.
		acked_ids = []

	payload = {
		"acknowledged": True,
		"acknowledge_itt_gcc_tds": True,
		"acknowledged_at": str(now_datetime()),
		"acknowledged_by": frappe.session.user,
		"addenda_acknowledged": acked_ids,
	}
	save_section_responses(bid_id, section_key, payload)
	return get_tender_documents_addenda(published_tender_ref)
