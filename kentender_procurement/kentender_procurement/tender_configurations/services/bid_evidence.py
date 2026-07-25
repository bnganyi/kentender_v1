# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X100 — Lean Evidence Register (File + bid-scoped metadata). Not BWMF."""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	_append_audit,
	_get_bid,
	_parse_json,
	_require_logged_in,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	portal_workspace_url,
)

EVIDENCE_STATUS_CURRENT = "Current"
EVIDENCE_STATUS_MISSING_METADATA = "Missing Metadata"
EVIDENCE_STATUS_SUPERSEDED = "Superseded"
EVIDENCE_STATUS_INVALID_FILE = "Invalid File"

ALLOWED_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"})
ALLOWED_CONTENT_TYPES = frozenset(
	{
		"application/pdf",
		"image/png",
		"image/jpeg",
		"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		"application/octet-stream",  # allowed only with safe extension
	}
)
MAX_BYTES = 5 * 1024 * 1024

# Types that require issuer / reference / issue / expiry for Current status.
METADATA_REQUIRED_TYPES = frozenset({"certificate", "licence", "license", "tax_clearance"})

BIDDER_ITEM_KEYS = frozenset(
	{
		"evidence_id",
		"title",
		"evidence_type",
		"file_name",
		"file_url",
		"version",
		"issuer",
		"reference_number",
		"issue_date",
		"expiry_or_validity",
		"language",
		"translation_ref",
		"party_scope",
		"links",
		"status",
		"superseded_by",
	}
)


def portal_evidence_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/evidence"


def _require_draft_bid(published_tender_ref: str):
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	return backend, doc


def _load_register(doc) -> dict[str, Any]:
	raw = _parse_json(getattr(doc, "evidence_register_json", None), {"items": []})
	if not isinstance(raw, dict):
		raw = {"items": []}
	items = raw.get("items")
	if not isinstance(items, list):
		items = []
	raw["items"] = items
	return raw


def _save_register(doc, register: dict[str, Any], *, event: str, detail: dict[str, Any] | None = None) -> None:
	doc.evidence_register_json = json.dumps(register, ensure_ascii=False)
	_append_audit(doc, event, detail or {})
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def _project_item(row: dict[str, Any]) -> dict[str, Any]:
	out = {k: row.get(k) for k in BIDDER_ITEM_KEYS if k in row}
	out.setdefault("links", list(row.get("links") or []))
	out.setdefault("superseded_by", cstr(row.get("superseded_by") or ""))
	# Never expose storage identifiers.
	out.pop("file_id", None)
	return out


def _derive_status(row: dict[str, Any]) -> str:
	if cstr(row.get("status")) == EVIDENCE_STATUS_SUPERSEDED:
		return EVIDENCE_STATUS_SUPERSEDED
	etype = cstr(row.get("evidence_type") or "").strip().lower()
	if etype in METADATA_REQUIRED_TYPES:
		for key in ("issuer", "reference_number", "issue_date", "expiry_or_validity"):
			if not cstr(row.get(key) or "").strip():
				return EVIDENCE_STATUS_MISSING_METADATA
	if not cstr(row.get("file_name") or "").strip():
		return EVIDENCE_STATUS_INVALID_FILE
	return EVIDENCE_STATUS_CURRENT


def _validate_upload(*, filename: str, content: bytes, content_type: str) -> None:
	name = cstr(filename or "").strip()
	if not name or "/" in name or "\\" in name or ".." in name:
		frappe.throw(frappe._("Invalid file name."), title="EVIDENCE_FILE_INVALID")
	ext = os.path.splitext(name)[1].lower()
	if ext not in ALLOWED_EXTENSIONS:
		frappe.throw(
			frappe._("File type {0} is not allowed.").format(ext or "(none)"),
			title="EVIDENCE_FILE_TYPE",
		)
	ctype = cstr(content_type or "").strip().lower() or "application/octet-stream"
	if ctype not in ALLOWED_CONTENT_TYPES:
		frappe.throw(frappe._("Content type is not allowed."), title="EVIDENCE_CONTENT_TYPE")
	if ctype == "application/octet-stream" and ext not in ALLOWED_EXTENSIONS:
		frappe.throw(frappe._("Content type is not allowed."), title="EVIDENCE_CONTENT_TYPE")
	if not content:
		frappe.throw(frappe._("Empty files cannot be uploaded as evidence."), title="EVIDENCE_FILE_EMPTY")
	if len(content) > MAX_BYTES:
		frappe.throw(
			frappe._("File exceeds the maximum allowed size."),
			title="EVIDENCE_FILE_TOO_LARGE",
		)
	# Basic safety: reject Windows PE / shell script markers for non-text types.
	if content.startswith(b"MZ") or content.startswith(b"#!"):
		frappe.throw(frappe._("File failed safety validation."), title="EVIDENCE_FILE_UNSAFE")


def _decode_content(content_b64: str | None, content: bytes | None) -> bytes:
	if content is not None:
		return content
	raw = cstr(content_b64 or "").strip()
	if not raw:
		return b""
	try:
		return base64.b64decode(raw)
	except Exception:
		frappe.throw(frappe._("File content could not be decoded."), title="EVIDENCE_FILE_INVALID")
		return b""


def _attach_file(doc, *, filename: str, content: bytes, content_type: str) -> Any:
	from frappe.utils.file_manager import save_file

	_ = content_type
	return save_file(
		fname=filename,
		content=content,
		dt="Electronic Bid Submission",
		dn=doc.name,
		is_private=1,
	)


def _new_evidence_id() -> str:
	return f"EVD-{frappe.generate_hash(length=10).upper()}"


def get_evidence_register(published_tender_ref: str) -> dict[str, Any]:
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	register = _load_register(doc)
	items = []
	for row in register.get("items") or []:
		if not isinstance(row, dict):
			continue
		row = dict(row)
		row["status"] = _derive_status(row)
		items.append(_project_item(row))
	return {
		"published_tender_ref": pub_ref,
		"workspace_url": portal_workspace_url(pub_ref),
		"evidence_url": portal_evidence_url(pub_ref),
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"documents_url": f"/tenders/{quote(pub_ref, safe='')}/documents",
		"tender_title": cstr(
			frappe.db.get_value("Tender Configuration", cfg_id, "tender_title") or ""
		),
		"items": items,
		"empty": 1 if not items else 0,
		"empty_message": "No evidence has been uploaded for this bid yet.",
	}


def upload_evidence(
	published_tender_ref: str,
	*,
	title: str,
	evidence_type: str,
	filename: str,
	content_b64: str | None = None,
	content: bytes | None = None,
	content_type: str = "application/pdf",
	metadata: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	backend, doc = _require_draft_bid(published_tender_ref)
	if isinstance(metadata, str):
		metadata = _parse_json(metadata, {})
	metadata = metadata if isinstance(metadata, dict) else {}
	blob = _decode_content(content_b64, content)
	_validate_upload(filename=filename, content=blob, content_type=content_type)
	file_doc = _attach_file(doc, filename=filename, content=blob, content_type=content_type)
	eid = _new_evidence_id()
	row = {
		"evidence_id": eid,
		"title": cstr(title or filename).strip() or filename,
		"evidence_type": cstr(evidence_type or "supporting_document").strip() or "supporting_document",
		"file_id": file_doc.name,
		"file_name": cstr(file_doc.file_name or filename),
		"file_url": cstr(file_doc.file_url or ""),
		"version": 1,
		"issuer": cstr(metadata.get("issuer") or ""),
		"reference_number": cstr(metadata.get("reference_number") or ""),
		"issue_date": cstr(metadata.get("issue_date") or ""),
		"expiry_or_validity": cstr(metadata.get("expiry_or_validity") or ""),
		"language": cstr(metadata.get("language") or "en"),
		"translation_ref": cstr(metadata.get("translation_ref") or ""),
		"party_scope": cstr(metadata.get("party_scope") or "bidder"),
		"links": [],
		"status": EVIDENCE_STATUS_CURRENT,
		"superseded_by": "",
		"created_at": str(now_datetime()),
	}
	row["status"] = _derive_status(row)
	register = _load_register(doc)
	register["items"].append(row)
	_save_register(
		doc,
		register,
		event="evidence_uploaded",
		detail={"evidence_id": eid, "version": 1},
	)
	return {"published_tender_ref": backend["published_tender_ref"], "item": _project_item(row)}


def replace_evidence(
	published_tender_ref: str,
	*,
	evidence_id: str,
	filename: str,
	content_b64: str | None = None,
	content: bytes | None = None,
	content_type: str = "application/pdf",
) -> dict[str, Any]:
	backend, doc = _require_draft_bid(published_tender_ref)
	eid = cstr(evidence_id or "").strip()
	register = _load_register(doc)
	current = next(
		(
			r
			for r in register["items"]
			if isinstance(r, dict)
			and cstr(r.get("evidence_id")) == eid
			and cstr(r.get("status")) != EVIDENCE_STATUS_SUPERSEDED
		),
		None,
	)
	if not current:
		frappe.throw(frappe._("Evidence item not found."), frappe.PermissionError)
	blob = _decode_content(content_b64, content)
	_validate_upload(filename=filename, content=blob, content_type=content_type)
	file_doc = _attach_file(doc, filename=filename, content=blob, content_type=content_type)
	prev_version = int(current.get("version") or 1)
	current["status"] = EVIDENCE_STATUS_SUPERSEDED
	current["superseded_by"] = eid
	new_row = dict(current)
	new_row.update(
		{
			"file_id": file_doc.name,
			"file_name": cstr(file_doc.file_name or filename),
			"file_url": cstr(file_doc.file_url or ""),
			"version": prev_version + 1,
			"status": EVIDENCE_STATUS_CURRENT,
			"superseded_by": "",
			"created_at": str(now_datetime()),
		}
	)
	new_row["status"] = _derive_status(new_row)
	# Keep superseded current in place; append new current version row.
	register["items"].append(new_row)
	_save_register(
		doc,
		register,
		event="evidence_replaced",
		detail={"evidence_id": eid, "version": new_row["version"]},
	)
	return {"published_tender_ref": backend["published_tender_ref"], "item": _project_item(new_row)}


def link_evidence(
	published_tender_ref: str,
	*,
	evidence_id: str,
	target_kind: str,
	target_key: str,
) -> dict[str, Any]:
	backend, doc = _require_draft_bid(published_tender_ref)
	eid = cstr(evidence_id or "").strip()
	kind = cstr(target_kind or "obligation").strip() or "obligation"
	key = cstr(target_key or "").strip()
	if not key:
		frappe.throw(frappe._("Link target key is required."), title="EVIDENCE_LINK_INVALID")
	register = _load_register(doc)
	current = next(
		(
			r
			for r in register["items"]
			if isinstance(r, dict)
			and cstr(r.get("evidence_id")) == eid
			and cstr(r.get("status")) != EVIDENCE_STATUS_SUPERSEDED
		),
		None,
	)
	if not current:
		frappe.throw(frappe._("Evidence item not found."), frappe.PermissionError)
	links = list(current.get("links") or [])
	if not any(
		cstr(l.get("target_kind")) == kind and cstr(l.get("target_key")) == key
		for l in links
		if isinstance(l, dict)
	):
		links.append({"target_kind": kind, "target_key": key})
	current["links"] = links
	_save_register(
		doc,
		register,
		event="evidence_linked",
		detail={"evidence_id": eid, "target_kind": kind, "target_key": key},
	)
	return {"published_tender_ref": backend["published_tender_ref"], "item": _project_item(current)}


def unlink_evidence(
	published_tender_ref: str,
	*,
	evidence_id: str,
	target_kind: str,
	target_key: str,
) -> dict[str, Any]:
	backend, doc = _require_draft_bid(published_tender_ref)
	eid = cstr(evidence_id or "").strip()
	kind = cstr(target_kind or "obligation").strip() or "obligation"
	key = cstr(target_key or "").strip()
	register = _load_register(doc)
	current = next(
		(
			r
			for r in register["items"]
			if isinstance(r, dict)
			and cstr(r.get("evidence_id")) == eid
			and cstr(r.get("status")) != EVIDENCE_STATUS_SUPERSEDED
		),
		None,
	)
	if not current:
		frappe.throw(frappe._("Evidence item not found."), frappe.PermissionError)
	current["links"] = [
		l
		for l in (current.get("links") or [])
		if isinstance(l, dict)
		and not (cstr(l.get("target_kind")) == kind and cstr(l.get("target_key")) == key)
	]
	_save_register(
		doc,
		register,
		event="evidence_unlinked",
		detail={"evidence_id": eid, "target_kind": kind, "target_key": key},
	)
	return {"published_tender_ref": backend["published_tender_ref"], "item": _project_item(current)}


def freeze_evidence_for_seal(bid_id: str) -> dict[str, Any]:
	"""Immutable snapshot of current evidence versions for submission binding."""
	doc = frappe.get_doc("Electronic Bid Submission", bid_id)
	register = _load_register(doc)
	versions = []
	for row in register.get("items") or []:
		if not isinstance(row, dict):
			continue
		status = _derive_status(row)
		if status == EVIDENCE_STATUS_SUPERSEDED:
			continue
		versions.append(
			{
				"evidence_id": cstr(row.get("evidence_id")),
				"version": int(row.get("version") or 1),
				"file_id": cstr(row.get("file_id") or ""),
				"file_name": cstr(row.get("file_name") or ""),
				"title": cstr(row.get("title") or ""),
				"links": list(row.get("links") or []),
			}
		)
	snapshot = {"frozen_at": str(now_datetime()), "versions": versions}
	doc.evidence_seal_snapshot_json = json.dumps(snapshot, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return snapshot


def list_missing_metadata_items(published_tender_ref: str) -> list[dict[str, Any]]:
	reg = get_evidence_register(published_tender_ref)
	return [i for i in (reg.get("items") or []) if i.get("status") == EVIDENCE_STATUS_MISSING_METADATA]
