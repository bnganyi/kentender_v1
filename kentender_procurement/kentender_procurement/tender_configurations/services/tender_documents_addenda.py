# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""S100 / A3 — Tender Documents & Addenda: DTO, version-bound acknowledgement, invalidation."""

from __future__ import annotations

import hashlib
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
from kentender_procurement.tender_configurations.services.bidder_presentation import (
	BIDDER_DOCUMENTS_DTO_KEYS,
	allowlist_dict,
	project_bidder_addendum_row,
	project_bidder_document_row,
	published_tender_pdf_url,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	ACTION_CLOSED,
	ACTION_UNAVAILABLE,
	ACTION_VIEW_SUBMITTED,
	get_published_tender_overview,
	resolve_published_tender_backend,
	start_or_get_bid_workspace,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	persist_compiled_schema,
)
from kentender_procurement.tender_configurations.services.section_status import (
	STATUS_COMPLETE,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	issue_result,
	to_display_status,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	portal_workspace_url,
)

DOC_ACK_KEYS = frozenset(
	{
		"document_acknowledgement",
		"tender_document_acknowledgement",
		"tender_documents_and_addenda",
	}
)
DOC_ACK_TYPES = frozenset({"document_acknowledgement", "document_ack"})

ACK_STATUS_ACTION_REQUIRED = "Action Required"
ACK_STATUS_COMPLETE = "Complete"
ACK_STATUS_STALE = "Needs Re-acknowledgement"

EMPTY_ADDENDA_MESSAGE = "No official addenda have been issued for this tender."
READINESS_NO_ADDENDA = "No addenda issued."

SECTION_KEY_CANONICAL = "tender_documents_and_addenda"


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


def compute_addenda_set_digest(addenda: list[dict[str, Any]] | None) -> str:
	"""Deterministic digest of the current issued addenda set (id + version)."""
	rows = []
	for row in addenda or []:
		if not isinstance(row, dict):
			continue
		aid = cstr(row.get("id") or "").strip()
		ver = cstr(row.get("version") or row.get("version_or_hash") or "").strip()
		if not aid:
			continue
		rows.append({"id": aid, "version": ver})
	rows.sort(key=lambda r: r["id"])
	blob = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_addendum_row(row: dict[str, Any]) -> dict[str, Any] | None:
	aid = cstr(row.get("id") or row.get("addendum_id") or row.get("ref") or row.get("code") or "").strip()
	title = cstr(row.get("title") or row.get("name") or aid).strip()
	if not aid and not title:
		return None
	requires = bool(
		row.get("requires_acknowledgement")
		if "requires_acknowledgement" in row
		else row.get("requires_ack", True)
	)
	version = cstr(row.get("version") or row.get("version_or_hash") or aid).strip() or aid
	return {
		"id": aid or title,
		"title": title or aid,
		"ref": cstr(row.get("ref") or row.get("code") or aid),
		"summary": cstr(row.get("summary") or row.get("description") or ""),
		"published_at": cstr(row.get("published_at") or row.get("issued_at") or ""),
		"issued_at": cstr(row.get("issued_at") or row.get("published_at") or ""),
		"requires_acknowledgement": 1 if requires else 0,
		"version": version,
		"is_material": 1 if row.get("is_material", True) else 0,
		"attachment_name": cstr(row.get("attachment_name") or row.get("file_name") or ""),
		"attachment_url": cstr(row.get("attachment_url") or row.get("url") or ""),
		"view_url": cstr(row.get("view_url") or row.get("download_url") or ""),
	}


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
		norm = _normalize_addendum_row(row)
		if norm:
			out.append(norm)
	return out


def load_issued_addenda(publication_id: str) -> list[dict[str, Any]]:
	"""Load append-only issued addenda from the publication record."""
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists("IT Tender Publication Record", publication_id):
		return []
	raw = frappe.db.get_value("IT Tender Publication Record", publication_id, "issued_addenda_json")
	rows = _parse_json(raw, [])
	if not isinstance(rows, list):
		return []
	out: list[dict[str, Any]] = []
	for row in rows:
		if isinstance(row, dict):
			norm = _normalize_addendum_row(row)
			if norm:
				out.append(norm)
	return out


def append_issued_addendum(publication_id: str, row: dict[str, Any]) -> dict[str, Any]:
	"""Append one addendum to the publication register (never overwrite prior rows)."""
	if frappe.session.user != "Administrator":
		frappe.throw(
			frappe._("Appending issued addenda is Administrator-only in this slice."),
			frappe.PermissionError,
		)
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists("IT Tender Publication Record", publication_id):
		frappe.throw(frappe._("Publication record not found."), title="PUBLICATION_NOT_FOUND")
	norm = _normalize_addendum_row(row if isinstance(row, dict) else {})
	if not norm:
		frappe.throw(frappe._("Addendum id and title are required."), title="ADDENDUM_INVALID")
	existing = load_issued_addenda(publication_id)
	if any(cstr(r.get("id")) == norm["id"] for r in existing):
		frappe.throw(
			frappe._("Addendum {0} already exists; append a new version id.").format(norm["id"]),
			title="ADDENDUM_DUPLICATE",
		)
	if not norm.get("issued_at"):
		norm["issued_at"] = str(now_datetime())
		norm["published_at"] = norm["issued_at"]
	existing.append(norm)
	pub = frappe.get_doc("IT Tender Publication Record", publication_id)
	pub.flags.ignore_publication_boundary = True
	pub.flags.ignore_publication_lock = True
	pub.issued_addenda_json = json.dumps(existing, ensure_ascii=False)
	pub.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"publication_id": publication_id,
		"addendum": norm,
		"addenda_count": len(existing),
		"addenda_set_digest": compute_addenda_set_digest(existing),
	}


def resolve_addenda_for_publication(
	publication_id: str,
	package: Any = None,
	overview: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
	"""Prefer publication issued_addenda_json; fall back to package/overview lists."""
	issued = load_issued_addenda(publication_id)
	if issued:
		return issued
	return extract_package_addenda(package, overview)


def _acked_addenda_ids(ack_payload: Any) -> set[str]:
	acked: set[str] = set()
	if not isinstance(ack_payload, dict):
		return acked
	for item in ack_payload.get("addenda_acknowledged") or []:
		if isinstance(item, dict):
			acked.add(cstr(item.get("id") or "").strip())
		else:
			acked.add(cstr(item).strip())
	acked.discard("")
	return acked


def is_documents_acknowledged(payload: Any) -> bool:
	if not isinstance(payload, dict):
		return False
	if payload.get("acknowledged") in (True, 1, "1", "true", "True"):
		return True
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
	acked = _acked_addenda_ids(ack_payload)
	for row in rows:
		if not row.get("requires_acknowledgement"):
			continue
		aid = cstr(row.get("id") or "").strip()
		if aid and aid not in acked:
			return True
	return False


def build_package_ack_context(
	*,
	publication_ref: str,
	publication_id: str,
	package: dict[str, Any] | None,
	published_at: str = "",
	addenda: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	pkg = package if isinstance(package, dict) else {}
	addenda = addenda if addenda is not None else []
	return {
		"publication_ref": cstr(publication_ref or "").strip(),
		"publication_id": cstr(publication_id or "").strip(),
		"package_id": cstr(pkg.get("package_id") or pkg.get("name") or "").strip(),
		"package_document_hash": cstr(pkg.get("document_hash") or "").strip(),
		"configuration_version": cstr(pkg.get("configuration_version") or "").strip(),
		"published_at": cstr(published_at or "").strip(),
		"addenda_set_digest": compute_addenda_set_digest(addenda),
	}


def ack_binding_is_current(payload: Any, ctx: dict[str, Any]) -> bool:
	"""True when effective acknowledgement binds the current package/addenda/publication."""
	if not is_documents_acknowledged(payload):
		return False
	if not isinstance(payload, dict):
		return False
	if cstr(payload.get("publication_ref") or "") != cstr(ctx.get("publication_ref") or ""):
		return False
	bound_hash = cstr(payload.get("package_document_hash") or "")
	cur_hash = cstr(ctx.get("package_document_hash") or "")
	if bound_hash and cur_hash and bound_hash != cur_hash:
		return False
	if not bound_hash and cur_hash:
		# Legacy unbound ack — treat as stale when a digest exists.
		return False
	bound_digest = cstr(payload.get("addenda_set_digest") or "")
	cur_digest = cstr(ctx.get("addenda_set_digest") or "")
	if bound_digest != cur_digest:
		return False
	return True


def supersede_stale_acknowledgement(
	payload: dict[str, Any],
	*,
	reason: str,
) -> dict[str, Any]:
	"""Move current ack into history and clear effective current (history retained)."""
	history = list(payload.get("acknowledgement_history") or [])
	snapshot = {
		"acknowledged": payload.get("acknowledged"),
		"acknowledged_at": payload.get("acknowledged_at"),
		"acknowledged_by": payload.get("acknowledged_by"),
		"publication_ref": payload.get("publication_ref"),
		"package_id": payload.get("package_id"),
		"package_document_hash": payload.get("package_document_hash"),
		"configuration_version": payload.get("configuration_version"),
		"addenda_set_digest": payload.get("addenda_set_digest"),
		"addenda_acknowledged": payload.get("addenda_acknowledged") or [],
		"superseded_at": str(now_datetime()),
		"reason": cstr(reason or "invalidated"),
	}
	history.append(snapshot)
	return {
		"acknowledged": False,
		"acknowledge_itt_gcc_tds": False,
		"acknowledged_at": None,
		"acknowledged_by": None,
		"publication_ref": None,
		"package_id": None,
		"package_document_hash": None,
		"configuration_version": None,
		"addenda_set_digest": None,
		"addenda_acknowledged": [],
		"acknowledgement_history": history,
		"stale": True,
		"invalidation_reason": cstr(reason or "invalidated"),
	}


def _docs_response_started(payload: dict[str, Any]) -> bool:
	"""True only after a material ack attempt or retained history (not empty shells)."""
	if not isinstance(payload, dict) or not payload:
		return False
	if payload.get("acknowledgement_history"):
		return True
	if is_documents_acknowledged(payload):
		return True
	if payload.get("stale") in (True, 1, "1", "true", "True"):
		return True
	return False


def derive_docs_section_status(
	section_def: dict[str, Any] | None,
	response: dict[str, Any] | None,
	package_ctx: dict[str, Any] | None,
	*,
	addenda: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""Server-derived status for tender_documents_and_addenda (F0 IssueResult shape)."""
	_ = section_def
	payload = response if isinstance(response, dict) else {}
	ctx = package_ctx if isinstance(package_ctx, dict) else {}
	# Unstarted required sections stay Not Started (A2) — not Needs Attention.
	if not _docs_response_started(payload):
		return issue_result(ok=True, issues=[], section_status=STATUS_NOT_STARTED)

	current = ack_binding_is_current(payload, ctx)
	issues: list[dict[str, Any]] = []
	if is_documents_acknowledged(payload) and not current:
		issues.append(
			{
				"code": "acknowledgement_stale",
				"message": "Prior acknowledgement is not bound to the current package or addenda set.",
			}
		)
	elif not is_documents_acknowledged(payload):
		issues.append(
			{
				"code": "package_acknowledgement_required",
				"message": "Acknowledge the current tender documents for this publication.",
			}
		)

	if required_addenda_block_submission(addenda, payload if current else {}):
		issues.append(
			{
				"code": "required_addendum_unacknowledged",
				"message": "One or more required addenda are unacknowledged for the current version.",
			}
		)

	if issues:
		return issue_result(ok=False, issues=issues, section_status=STATUS_NEEDS_ATTENTION)
	return issue_result(ok=True, issues=[], section_status=STATUS_COMPLETE)


def _load_schema(cfg, bid_doc) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.submission_checklist import (
		_load_published_electronic_schema,
	)

	try:
		return _load_published_electronic_schema(cfg.name)
	except Exception:
		pass
	if bid_doc:
		schema = _parse_json(getattr(bid_doc, "schema_snapshot", None), {})
		if schema.get("sections"):
			return schema
	schema = _parse_json(getattr(cfg, "bidder_submission_schema", None), {})
	if not schema.get("sections"):
		schema = persist_compiled_schema(cfg.name)
	return schema


def _project_documents(
	documents: list[dict[str, Any]],
	*,
	published_tender_ref: str,
	published_at: str = "",
) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for doc in documents or []:
		out.append(
			project_bidder_document_row(
				doc,
				published_tender_ref=published_tender_ref,
				published_at=published_at,
			)
		)
	return out


def _continue_portal_url(schema: dict[str, Any], ack_index: int | None, publication_ref: str) -> str:
	"""Next bidder portal step — never a desk configuration_id bridge."""
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		portal_fot_url,
	)
	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		is_requirement_matrix_section,
		portal_section_url,
	)

	workspace = portal_workspace_url(publication_ref)
	if ack_index is None:
		return workspace
	sections = [s for s in (schema.get("sections") or []) if isinstance(s, dict) and _section_key(s)]
	if ack_index + 1 >= len(sections):
		return workspace
	nxt = sections[ack_index + 1]
	key = _section_key(nxt)
	if key == "form_of_tender":
		return portal_fot_url(publication_ref)
	if is_requirement_matrix_section(nxt):
		return portal_section_url(publication_ref, key)
	return workspace


def _persist_ack_payload(bid_id: str, section_key: str, payload: dict[str, Any]) -> None:
	save_section_responses(bid_id, section_key, payload)


def _resolve_docs_workspace(published_tender_ref: str) -> dict[str, Any]:
	"""Compose overview + server-only binding context for documents/ack."""
	overview = get_published_tender_overview(published_tender_ref)
	backend = resolve_published_tender_backend(published_tender_ref)
	return {"overview": overview, "backend": backend}


def get_tender_documents_addenda(published_tender_ref: str) -> dict[str, Any]:
	"""Screen C / S100 bidder-facing DTO keyed by publication_ref (auth required)."""
	_require_logged_in()
	bundle = _resolve_docs_workspace(published_tender_ref)
	overview = bundle["overview"]
	backend = bundle["backend"]
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)

	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	publication_id = cstr(backend.get("publication_id") or "")
	workspace_path = portal_workspace_url(pub_ref)
	documents_path = portal_documents_url(pub_ref)

	bid_sealed = False
	bid_id = backend.get("bid_id")
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

	cfg = backend.get("configuration") or frappe.get_doc("Tender Configuration", cfg_id)
	schema = _load_schema(cfg, bid_doc)
	responses = _parse_json(getattr(bid_doc, "responses", None), {}) if bid_doc else {}

	ack_sec = resolve_document_acknowledgement_section(schema)
	section_key = (ack_sec or {}).get("key") or SECTION_KEY_CANONICAL
	ack_payload = dict(responses.get(section_key) or {}) if isinstance(responses.get(section_key), dict) else {}

	package = backend.get("confirmed_package") or {}
	if not isinstance(package, dict):
		package = {}
	addenda_raw = resolve_addenda_for_publication(publication_id, package, overview)
	published_at = cstr((overview.get("dates") or {}).get("published_at") or "")
	ctx = build_package_ack_context(
		publication_ref=pub_ref,
		publication_id=publication_id,
		package=package,
		published_at=published_at,
		addenda=addenda_raw,
	)

	# Invalidate stale effective ack on read (persist history). Binding hashes stay server-side.
	if (
		bid_doc
		and not bid_sealed
		and is_documents_acknowledged(ack_payload)
		and not ack_binding_is_current(ack_payload, ctx)
	):
		reason = "package_or_addenda_changed"
		if cstr(ack_payload.get("publication_ref") or "") != ctx["publication_ref"]:
			reason = "publication_ref_mismatch"
		elif cstr(ack_payload.get("package_document_hash") or "") != ctx["package_document_hash"]:
			reason = "package_document_hash_change"
		elif cstr(ack_payload.get("addenda_set_digest") or "") != ctx["addenda_set_digest"]:
			reason = "addenda_set_digest_change"
		ack_payload = supersede_stale_acknowledgement(ack_payload, reason=reason)
		_persist_ack_payload(cstr(bid_doc.name), section_key, ack_payload)
		bid_doc.reload()
		responses = _parse_json(getattr(bid_doc, "responses", None), {})
		ack_payload = dict(responses.get(section_key) or {})

	current = ack_binding_is_current(ack_payload, ctx)
	acknowledged = current or bid_sealed
	block = required_addenda_block_submission(addenda_raw, ack_payload if current else {})
	documents = _project_documents(
		list(overview.get("documents") or []),
		published_tender_ref=pub_ref,
		published_at=published_at,
	)
	primary_pdf_url = published_tender_pdf_url(pub_ref) if documents else ""
	for doc in documents:
		if doc.get("document_key") == "tender_pdf" and doc.get("download_url"):
			primary_pdf_url = cstr(doc.get("download_url"))
			break

	acked_ids = _acked_addenda_ids(ack_payload) if current else set()
	unacked_required = 0
	addenda: list[dict[str, Any]] = []
	for row in addenda_raw:
		aid = cstr(row.get("id") or "")
		is_acked = aid in acked_ids
		projected = project_bidder_addendum_row(
			{
				**row,
				"acknowledged": 1 if is_acked else 0,
				"is_new": 0 if is_acked else 1,
			}
		)
		if projected.get("requires_acknowledgement") and not is_acked:
			unacked_required += 1
		addenda.append(projected)

	deadline_raw = (overview.get("dates") or {}).get("submission_deadline") or ""
	try:
		deadline_display = format_datetime(deadline_raw) if deadline_raw else "—"
	except Exception:
		deadline_display = cstr(deadline_raw) or "—"

	derive = derive_docs_section_status(
		(ack_sec or {}).get("section"),
		ack_payload,
		ctx,
		addenda=addenda_raw,
	)
	display_status = to_display_status(derive["section_status"])
	if bid_sealed and acknowledged:
		display_status = "Complete"
	stale = bool(ack_payload.get("stale") or (is_documents_acknowledged(ack_payload) and not current))
	if stale and not bid_sealed:
		ack_status = ACK_STATUS_STALE
	elif acknowledged and not block:
		ack_status = ACK_STATUS_COMPLETE
	else:
		ack_status = ACK_STATUS_ACTION_REQUIRED

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
	elif stale and not bid_sealed:
		blocker_message = (
			"A material update to the tender documents or addenda invalidated your prior acknowledgement. "
			"Please review the current documents and acknowledge again."
		)

	continue_url = (
		_continue_portal_url(schema, (ack_sec or {}).get("index"), pub_ref)
		if continue_enabled
		else "#"
	)

	dto = {
		"published_tender_ref": pub_ref,
		"section_key": section_key,
		"section_title": (ack_sec or {}).get("title") or "Tender Documents & Addenda",
		"tender_title": overview.get("tender_title") or "",
		"procuring_entity": overview.get("procuring_entity") or "",
		"workspace_url": workspace_path,
		"documents_url": documents_path,
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"submission_deadline": deadline_raw,
		"submission_deadline_display": deadline_display,
		"time_remaining_label": format_time_remaining(deadline_raw),
		"documents": documents,
		"primary_pdf_url": primary_pdf_url,
		"addenda": addenda,
		"addenda_empty": 1 if not addenda else 0,
		"addenda_empty_message": EMPTY_ADDENDA_MESSAGE,
		"acknowledgement_status": ack_status,
		"section_status": display_status,
		"documents_acknowledged": 1 if acknowledged else 0,
		"acknowledgement_stale": 1 if stale and not bid_sealed else 0,
		"addenda_block_submission": 1 if block else 0,
		"readiness": {
			"documents_viewed_label": "Complete" if acknowledged else ("Stale" if stale else "Pending"),
			"addenda_label": readiness_addenda_label,
			"submission_impact": impact,
			"time_remaining_label": format_time_remaining(deadline_raw),
			"blocker_message": blocker_message,
		},
		"acknowledge_label": "Acknowledge Tender Documents",
		"acknowledge_enabled": 1 if ack_enabled else 0,
		"continue_label": "Continue to Next Section",
		"continue_enabled": 1 if continue_enabled else 0,
		"continue_url": continue_url,
		"back_to_checklist_label": "Back to Checklist",
		"back_to_checklist_url": workspace_path,
	}
	return allowlist_dict(dto, BIDDER_DOCUMENTS_DTO_KEYS)


def acknowledge_tender_documents(published_tender_ref: str) -> dict[str, Any]:
	"""Version-bound acknowledgement of current package + required addenda for this bid."""
	_require_logged_in()
	bundle = _resolve_docs_workspace(published_tender_ref)
	overview = bundle["overview"]
	backend = bundle["backend"]
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)

	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	publication_id = cstr(backend.get("publication_id") or "")
	package = backend.get("confirmed_package") or {}
	if not isinstance(package, dict):
		package = {}

	if overview.get("bid_status") == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")

	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	bid_doc = frappe.get_doc("Electronic Bid Submission", bid_id)
	if cstr(bid_doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")

	cfg = backend.get("configuration") or frappe.get_doc("Tender Configuration", cfg_id)
	schema = _load_schema(cfg, bid_doc)
	ack_sec = resolve_document_acknowledgement_section(schema)
	section_key = (ack_sec or {}).get("key") or SECTION_KEY_CANONICAL

	addenda_raw = resolve_addenda_for_publication(publication_id, package, overview)
	published_at = cstr((overview.get("dates") or {}).get("published_at") or "")
	ctx = build_package_ack_context(
		publication_ref=pub_ref,
		publication_id=publication_id,
		package=package,
		published_at=published_at,
		addenda=addenda_raw,
	)

	prior = _parse_json(getattr(bid_doc, "responses", None), {}).get(section_key) or {}
	if isinstance(prior, dict) and ack_binding_is_current(prior, ctx) and is_documents_acknowledged(prior):
		return get_tender_documents_addenda(published_tender_ref)

	history = list(prior.get("acknowledgement_history") or []) if isinstance(prior, dict) else []
	acked_rows = [
		{"id": cstr(a.get("id")), "version_or_hash": cstr(a.get("version") or a.get("id"))}
		for a in addenda_raw
		if a.get("requires_acknowledgement") and cstr(a.get("id"))
	]

	payload = {
		"acknowledged": True,
		"acknowledge_itt_gcc_tds": True,
		"acknowledged_at": str(now_datetime()),
		"acknowledged_by": frappe.session.user,
		"publication_ref": pub_ref,
		"package_id": ctx["package_id"],
		"package_document_hash": ctx["package_document_hash"],
		"configuration_version": ctx["configuration_version"],
		"addenda_set_digest": ctx["addenda_set_digest"],
		"addenda_acknowledged": acked_rows,
		"acknowledgement_history": history,
		"stale": False,
		"invalidation_reason": None,
	}
	save_section_responses(bid_id, section_key, payload)
	return get_tender_documents_addenda(published_tender_ref)
