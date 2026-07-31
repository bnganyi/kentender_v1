# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Officer Desk Bid Submissions — sealed confidentiality, opening, register, read-only review."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

PUBLICATION_DOCTYPE = "IT Tender Publication Record"
BID_DOCTYPE = "Electronic Bid Submission"
OPENING_DOCTYPE = "IT Bid Opening Record"
CFG_DOCTYPE = "Tender Configuration"

STAGE_RECEIVING = "Receiving submissions"
STAGE_SEALED = "Closed and sealed"
STAGE_OPENING = "Opening in progress"
STAGE_OPENED = "Opened"
STAGE_RELEASED = "Released to evaluation"

OPENING_ROLES = frozenset(
	{
		"System Manager",
		"Purchase Manager",
		"Procurement Manager",
		"Tender Manager",
	}
)
VIEW_METADATA_ROLES = frozenset(
	OPENING_ROLES
	| {
		"Purchase User",
		"Accounts Manager",
		"Auditor",
	}
)


def _throw(msg: str, *, title: str) -> None:
	frappe.throw(frappe._(msg), title=title)


def _require_login() -> None:
	if frappe.session.user in (None, "Guest"):
		frappe.throw(frappe._("Login required."), frappe.AuthenticationError)


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(cstr(raw))
	except (TypeError, ValueError):
		return default if default is not None else {}


def _user_roles() -> set[str]:
	return set(frappe.get_roles())


def can_view_submission_metadata() -> bool:
	roles = _user_roles()
	return bool(roles & VIEW_METADATA_ROLES) or "Administrator" in roles or frappe.session.user == "Administrator"


def can_open_bids() -> bool:
	roles = _user_roles()
	return bool(roles & OPENING_ROLES) or frappe.session.user == "Administrator"


def can_view_opened_register() -> bool:
	return can_view_submission_metadata()


def can_view_opened_bid() -> bool:
	return can_view_submission_metadata()


def can_download_evidence() -> bool:
	return can_open_bids() or "Auditor" in _user_roles()


def can_view_version_history() -> bool:
	return can_open_bids() or "Auditor" in _user_roles()


def _as_dt(value: Any):
	if not value:
		return None
	try:
		return get_datetime(value)
	except Exception:
		return None


def _get_publication(publication_id: str):
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists(PUBLICATION_DOCTYPE, publication_id):
		_throw("Publication not found.", title="PUBLICATION_NOT_FOUND")
	return frappe.get_doc(PUBLICATION_DOCTYPE, publication_id)


def _get_completed_opening(publication_id: str):
	name = frappe.db.get_value(
		OPENING_DOCTYPE,
		{"publication": publication_id, "status": "Completed"},
		"name",
	)
	if not name:
		return None
	return frappe.get_doc(OPENING_DOCTYPE, name)


def _get_any_opening(publication_id: str):
	name = frappe.db.get_value(OPENING_DOCTYPE, {"publication": publication_id}, "name")
	if not name:
		return None
	return frappe.get_doc(OPENING_DOCTYPE, name)


def derive_submission_stage(pub, opening=None) -> str:
	"""Derive tender-level submission stage. Time alone never opens bids."""
	status = cstr(getattr(pub, "status", None) or "")
	if status != "Published":
		return STAGE_RECEIVING
	opening = opening if opening is not None else _get_any_opening(pub.name)
	if opening and cstr(opening.status) == "Completed":
		# Released reserved for future evaluation handoff flag — not fabricated here.
		return STAGE_OPENED
	if opening and cstr(opening.status) == "In Progress":
		return STAGE_OPENING
	deadline = _as_dt(getattr(pub, "submission_deadline", None))
	now = now_datetime()
	if deadline and now >= deadline:
		return STAGE_SEALED
	return STAGE_RECEIVING


def _tender_title(cfg) -> str:
	return cstr(getattr(cfg, "tender_title", None) or getattr(cfg, "configuration_ref", None) or cfg.name)


def _procuring_entity(cfg) -> str:
	return cstr(
		getattr(cfg, "procuring_entity_name", None)
		or getattr(cfg, "procuring_entity", None)
		or ""
	)


def _action_for_stage(stage: str) -> dict[str, str]:
	if stage == STAGE_RECEIVING:
		return {"key": "view_tender", "label": "View tender"}
	if stage == STAGE_SEALED:
		return {"key": "view_sealed", "label": "View sealed status"}
	if stage == STAGE_OPENING:
		return {"key": "view_opening", "label": "View opening status"}
	return {"key": "view_register", "label": "Open register"}


def list_bid_submission_tenders(
	*,
	search: str | None = None,
	stage: str | None = None,
	page: int | str | None = 1,
	page_size: int | str | None = 20,
) -> dict[str, Any]:
	"""List published tenders with derived stage. Never returns submission counts/names before open."""
	_require_login()
	if not can_view_submission_metadata():
		_throw("Not permitted to view Bid Submissions.", title="BID_SUBMISSIONS_DENIED")

	try:
		page_i = max(1, int(page or 1))
		size_i = min(100, max(1, int(page_size or 20)))
	except (TypeError, ValueError):
		page_i, size_i = 1, 20

	pubs = frappe.get_all(
		PUBLICATION_DOCTYPE,
		filters={"status": "Published"},
		fields=[
			"name",
			"publication_ref",
			"configuration",
			"configuration_ref",
			"submission_deadline",
			"opening_datetime",
			"status",
		],
		order_by="submission_deadline desc",
		limit=500,
	)
	search_q = cstr(search or "").strip().lower()
	stage_filter = cstr(stage or "").strip()
	rows: list[dict[str, Any]] = []
	for pub_row in pubs:
		cfg = frappe.get_doc(CFG_DOCTYPE, pub_row.configuration) if pub_row.configuration else None
		if not cfg:
			continue
		title = _tender_title(cfg)
		pe = _procuring_entity(cfg)
		ref = cstr(pub_row.publication_ref or pub_row.configuration_ref or "")
		if search_q and search_q not in title.lower() and search_q not in ref.lower() and search_q not in pe.lower():
			continue
		opening = _get_any_opening(pub_row.name)
		derived = derive_submission_stage(pub_row, opening)
		if stage_filter and derived != stage_filter:
			continue
		action = _action_for_stage(derived)
		row: dict[str, Any] = {
			"publication_id": pub_row.name,
			"publication_ref": ref,
			"configuration_id": cfg.name,
			"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
			"tender_title": title,
			"procuring_entity": pe,
			"submission_deadline": cstr(pub_row.submission_deadline or ""),
			"opening_datetime": cstr(pub_row.opening_datetime or ""),
			"submission_stage": derived,
			"action": action,
		}
		# Post-open only: active bid count from immutable register.
		if derived in (STAGE_OPENED, STAGE_RELEASED) and opening and cstr(opening.status) == "Completed":
			row["active_bids_opened"] = int(opening.active_bid_count or 0)
		rows.append(row)

	total = len(rows)
	start = (page_i - 1) * size_i
	page_rows = rows[start : start + size_i]
	return {
		"rows": page_rows,
		"total": total,
		"page": page_i,
		"page_size": size_i,
		"stages": [
			STAGE_RECEIVING,
			STAGE_SEALED,
			STAGE_OPENING,
			STAGE_OPENED,
			STAGE_RELEASED,
		],
		"can_open_bids": 1 if can_open_bids() else 0,
	}


def get_bid_submission_sealed_status(publication_id: str) -> dict[str, Any]:
	"""Sealed tender status — no submission metadata."""
	_require_login()
	if not can_view_submission_metadata():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	cfg = frappe.get_doc(CFG_DOCTYPE, pub.configuration)
	opening = _get_any_opening(pub.name)
	stage = derive_submission_stage(pub, opening)
	deadline = _as_dt(pub.submission_deadline)
	scheduled = _as_dt(pub.opening_datetime)
	now = now_datetime()
	deadline_passed = bool(deadline and now >= deadline)
	opening_time_arrived = bool(scheduled and now >= scheduled)
	already_opened = bool(opening and cstr(opening.status) == "Completed")
	can_open = bool(
		can_open_bids()
		and deadline_passed
		and opening_time_arrived
		and not already_opened
		and stage in (STAGE_SEALED, STAGE_OPENING)
	)
	return {
		"publication_id": pub.name,
		"publication_ref": cstr(pub.publication_ref or ""),
		"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
		"tender_title": _tender_title(cfg),
		"procuring_entity": _procuring_entity(cfg),
		"submission_deadline": cstr(pub.submission_deadline or ""),
		"opening_datetime": cstr(pub.opening_datetime or ""),
		"submission_stage": stage,
		"status_label": STAGE_SEALED if stage == STAGE_SEALED else stage,
		"can_open_submitted_bids": 1 if can_open else 0,
		"waiting_for_authorised_opening": 0 if can_open else 1,
		"already_opened": 1 if already_opened else 0,
		# Explicit: never include counts, bidder names, or activity.
	}


def resolve_active_submissions(publication_id: str, *, as_of=None) -> list[dict[str, Any]]:
	"""Latest valid sealed submission per bidder+offer before deadline; exclude withdrawn/superseded."""
	pub = _get_publication(publication_id)
	deadline = _as_dt(pub.submission_deadline) or as_of or now_datetime()
	rows = frappe.get_all(
		BID_DOCTYPE,
		filters={
			"publication": publication_id,
			"status": "Sealed",
		},
		fields=[
			"name",
			"bidder_label",
			"bidder_legal_name",
			"offer_type",
			"lots_json",
			"receipt_code",
			"sealed_at",
			"sealed_by",
			"superseded_by",
			"withdrawn_at",
			"owner",
		],
		order_by="sealed_at desc",
	)
	# Also match by configuration when publication not stamped (legacy seals).
	if not rows:
		rows = frappe.get_all(
			BID_DOCTYPE,
			filters={"configuration": pub.configuration, "status": "Sealed"},
			fields=[
				"name",
				"bidder_label",
				"bidder_legal_name",
				"offer_type",
				"lots_json",
				"receipt_code",
				"sealed_at",
				"sealed_by",
				"superseded_by",
				"withdrawn_at",
				"owner",
			],
			order_by="sealed_at desc",
		)
	active: list[dict[str, Any]] = []
	seen: set[str] = set()
	for row in rows:
		if cstr(row.superseded_by or "").strip():
			continue
		if row.withdrawn_at:
			continue
		sealed_at = _as_dt(row.sealed_at)
		if sealed_at and sealed_at > deadline:
			continue
		key = f"{cstr(row.owner)}|{cstr(row.offer_type or 'Main')}"
		if key in seen:
			continue
		seen.add(key)
		lots = _parse_json(row.lots_json, [])
		active.append(
			{
				"bid_id": row.name,
				"bidder_legal_name": cstr(row.bidder_legal_name or row.bidder_label or "Tenderer"),
				"receipt_code": cstr(row.receipt_code or ""),
				"submitted_at": cstr(row.sealed_at or ""),
				"lots": lots if isinstance(lots, list) else [],
				"offer_type": cstr(row.offer_type or "Main"),
				"status": "Opened",
			}
		)
	return active


def _append_opening_audit(doc, action: str, detail: dict[str, Any] | None = None) -> None:
	events = _parse_json(getattr(doc, "audit_json", None), [])
	if not isinstance(events, list):
		events = []
	events.append(
		{
			"action": action,
			"at": str(now_datetime()),
			"by": frappe.session.user,
			"detail": detail or {},
		}
	)
	doc.audit_json = json.dumps(events)


def open_submitted_bids(publication_id: str) -> dict[str, Any]:
	"""Authorised opening — transactional; never reveals data before completion."""
	_require_login()
	if not can_open_bids():
		_append_failed_open_attempt(publication_id, "permission")
		_throw("Not permitted to open submitted bids.", title="BID_OPENING_DENIED")

	pub = _get_publication(publication_id)
	if cstr(pub.status) != "Published":
		_throw("Tender is not published.", title="BID_OPENING_DENIED")

	deadline = _as_dt(pub.submission_deadline)
	scheduled = _as_dt(pub.opening_datetime)
	now = now_datetime()
	if not deadline or now < deadline:
		_append_failed_open_attempt(publication_id, "deadline")
		_throw("Submission deadline has not passed.", title="BID_OPENING_DENIED")
	if not scheduled or now < scheduled:
		_append_failed_open_attempt(publication_id, "scheduled_opening")
		_throw("Scheduled opening time has not arrived.", title="BID_OPENING_DENIED")

	# Lock against duplicate opening.
	frappe.db.sql("SELECT name FROM `tabIT Tender Publication Record` WHERE name=%s FOR UPDATE", pub.name)
	existing = _get_completed_opening(pub.name)
	if existing:
		_throw("This tender has already been opened.", title="BID_OPENING_DENIED")

	active = resolve_active_submissions(pub.name)
	register_payload = [
		{
			"bid_id": a["bid_id"],
			"receipt_code": a["receipt_code"],
			"bidder_legal_name": a["bidder_legal_name"],
			"submitted_at": a["submitted_at"],
			"lots": a["lots"],
			"offer_type": a["offer_type"],
		}
		for a in active
	]

	prior = _get_any_opening(pub.name)
	if prior and cstr(prior.status) != "Completed":
		doc = prior
		doc.flags.ignore_opening_immutability = True
	else:
		doc = frappe.get_doc(
			{
				"doctype": OPENING_DOCTYPE,
				"publication": pub.name,
				"configuration": pub.configuration,
				"configuration_ref": cstr(pub.configuration_ref or ""),
				"publication_ref": cstr(pub.publication_ref or ""),
				"status": "In Progress",
				"scheduled_opening_datetime": pub.opening_datetime,
			}
		)
		doc.insert(ignore_permissions=True)

	doc.status = "Completed"
	doc.opened_at = now
	doc.opened_by = frappe.session.user
	doc.register_completed_at = now
	doc.scheduled_opening_datetime = pub.opening_datetime
	doc.active_submission_ids = json.dumps(register_payload)
	doc.active_bid_count = len(register_payload)
	_append_opening_audit(
		doc,
		"opening_completed",
		{"active_bid_count": len(register_payload)},
	)
	doc.flags.ignore_opening_immutability = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return get_opening_register(pub.name)


def _append_failed_open_attempt(publication_id: str, reason: str) -> None:
	try:
		pub_id = cstr(publication_id or "").strip()
		if not pub_id or not frappe.db.exists(PUBLICATION_DOCTYPE, pub_id):
			return
		doc = _get_any_opening(pub_id)
		if not doc:
			pub = frappe.get_doc(PUBLICATION_DOCTYPE, pub_id)
			doc = frappe.get_doc(
				{
					"doctype": OPENING_DOCTYPE,
					"publication": pub.name,
					"configuration": pub.configuration,
					"configuration_ref": cstr(pub.configuration_ref or ""),
					"publication_ref": cstr(pub.publication_ref or ""),
					"status": "Draft",
					"scheduled_opening_datetime": pub.opening_datetime,
					"active_submission_ids": "[]",
					"active_bid_count": 0,
				}
			)
			doc.insert(ignore_permissions=True)
		_append_opening_audit(doc, "opening_attempt_rejected", {"reason": reason})
		doc.flags.ignore_opening_immutability = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="bid_opening_audit_failed")


def _require_opened(publication_id: str):
	opening = _get_completed_opening(publication_id)
	if not opening:
		_throw("Submitted bids remain sealed.", title="BID_SEALED")
	return opening


def get_opening_register(publication_id: str) -> dict[str, Any]:
	_require_login()
	if not can_view_opened_register():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	opening = _require_opened(pub.name)
	cfg = frappe.get_doc(CFG_DOCTYPE, pub.configuration)
	entries = _parse_json(opening.active_submission_ids, [])
	if not isinstance(entries, list):
		entries = []
	rows = []
	for e in entries:
		if not isinstance(e, dict):
			continue
		rows.append(
			{
				"bid_id": cstr(e.get("bid_id") or ""),
				"tenderer": cstr(e.get("bidder_legal_name") or ""),
				"receipt_code": cstr(e.get("receipt_code") or ""),
				"submitted_at": cstr(e.get("submitted_at") or ""),
				"lots": e.get("lots") if isinstance(e.get("lots"), list) else [],
				"offer_type": cstr(e.get("offer_type") or "Main"),
				"status": "Opened",
			}
		)
	_append_opening_audit(opening, "register_viewed", {})
	opening.flags.ignore_opening_immutability = True
	# Avoid rewriting immutable completed fields — only audit_json.
	frappe.db.set_value(OPENING_DOCTYPE, opening.name, "audit_json", opening.audit_json, update_modified=False)
	return {
		"publication_id": pub.name,
		"publication_ref": cstr(pub.publication_ref or ""),
		"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
		"tender_title": _tender_title(cfg),
		"procuring_entity": _procuring_entity(cfg),
		"submission_stage": STAGE_OPENED,
		"opened_at": cstr(opening.opened_at or ""),
		"active_bids_opened": int(opening.active_bid_count or 0),
		"opening_ref": cstr(opening.opening_ref or ""),
		"rows": rows,
		"empty": 1 if not rows else 0,
		"empty_title": "No bids were received" if not rows else "",
		"empty_message": (
			"No active bid submissions were recorded for this tender." if not rows else ""
		),
	}


def get_opening_record_view(publication_id: str) -> dict[str, Any]:
	_require_login()
	if not can_view_opened_register():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	cfg = frappe.get_doc(CFG_DOCTYPE, pub.configuration)
	opening = _get_any_opening(pub.name)
	stage = derive_submission_stage(pub, opening)
	base = {
		"publication_id": pub.name,
		"publication_ref": cstr(pub.publication_ref or ""),
		"tender_title": _tender_title(cfg),
		"scheduled_opening_datetime": cstr(pub.opening_datetime or ""),
		"submission_stage": stage,
	}
	if not opening or cstr(opening.status) != "Completed":
		base.update(
			{
				"opening_status": cstr(opening.status) if opening else "Not started",
				"opened_at": "",
				"opened_by": "",
				"active_bids_opened": None,
				"receipt_refs": [],
			}
		)
		return base
	entries = _parse_json(opening.active_submission_ids, [])
	receipts = [cstr(e.get("receipt_code")) for e in entries if isinstance(e, dict) and e.get("receipt_code")]
	base.update(
		{
			"opening_status": "Completed",
			"opened_at": cstr(opening.opened_at or ""),
			"opened_by": cstr(opening.opened_by or ""),
			"active_bids_opened": int(opening.active_bid_count or 0),
			"receipt_refs": receipts,
			"opening_ref": cstr(opening.opening_ref or ""),
		}
	)
	return base


def _bid_in_register(opening, bid_id: str) -> dict[str, Any] | None:
	entries = _parse_json(opening.active_submission_ids, [])
	for e in entries:
		if isinstance(e, dict) and cstr(e.get("bid_id")) == cstr(bid_id):
			return e
	return None


def get_submitted_bid_overview(publication_id: str, bid_id: str) -> dict[str, Any]:
	_require_login()
	if not can_view_opened_bid():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	opening = _require_opened(pub.name)
	entry = _bid_in_register(opening, bid_id)
	if not entry:
		_throw("Bid is not on the opening register.", title="BID_NOT_IN_REGISTER")
	bid = frappe.get_doc(BID_DOCTYPE, bid_id)
	if cstr(bid.status) not in ("Sealed", "Withdrawn"):
		_throw("Bid is not available.", title="BID_NOT_AVAILABLE")
	cfg = frappe.get_doc(CFG_DOCTYPE, pub.configuration)
	sections = _manifest_sections(pub, bid)
	_append_opening_audit(opening, "bid_viewed", {"bid_ref": cstr(bid.receipt_code or "")})
	frappe.db.set_value(OPENING_DOCTYPE, opening.name, "audit_json", opening.audit_json, update_modified=False)
	return {
		"publication_id": pub.name,
		"publication_ref": cstr(pub.publication_ref or ""),
		"tender_title": _tender_title(cfg),
		"bid_id": bid.name,
		"tenderer": cstr(entry.get("bidder_legal_name") or bid.bidder_legal_name or bid.bidder_label),
		"receipt_code": cstr(bid.receipt_code or ""),
		"submitted_at": cstr(bid.sealed_at or ""),
		"lots": entry.get("lots") if isinstance(entry.get("lots"), list) else [],
		"offer_type": cstr(entry.get("offer_type") or "Main"),
		"status": "Opened",
		"read_only_label": "Read-only submitted bid",
		"sections": sections,
	}


def _manifest_sections(pub, bid) -> list[dict[str, Any]]:
	snap = _parse_json(getattr(pub, "electronic_template_snapshot", None), {})
	sections = snap.get("sections") if isinstance(snap, dict) else None
	if not sections:
		schema = _parse_json(getattr(bid, "schema_snapshot", None), {})
		sections = schema.get("sections") if isinstance(schema, dict) else []
	out = []
	for sec in sections or []:
		if not isinstance(sec, dict):
			continue
		key = cstr(sec.get("section_key") or sec.get("key") or "")
		label = cstr(sec.get("label") or sec.get("title") or key)
		if not key:
			continue
		out.append(
			{
				"section_key": key,
				"label": label,
				"submission_status": "Submitted",
				"action": "Review",
			}
		)
	return out


def get_submitted_section_response(publication_id: str, bid_id: str, section_key: str) -> dict[str, Any]:
	_require_login()
	if not can_view_opened_bid():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	opening = _require_opened(pub.name)
	entry = _bid_in_register(opening, bid_id)
	if not entry:
		_throw("Bid is not on the opening register.", title="BID_NOT_IN_REGISTER")
	bid = frappe.get_doc(BID_DOCTYPE, bid_id)
	section_key = cstr(section_key or "").strip()
	responses = _parse_json(bid.responses, {})
	payload = responses.get(section_key) if isinstance(responses, dict) else None
	if payload is None:
		payload = {}
	sections = _manifest_sections(pub, bid)
	keys = [s["section_key"] for s in sections]
	idx = keys.index(section_key) if section_key in keys else -1
	label = sections[idx]["label"] if idx >= 0 else section_key
	return {
		"publication_id": pub.name,
		"publication_ref": cstr(pub.publication_ref or ""),
		"bid_id": bid.name,
		"tenderer": cstr(entry.get("bidder_legal_name") or ""),
		"receipt_code": cstr(bid.receipt_code or ""),
		"section_key": section_key,
		"section_label": label,
		"payload": payload,
		"read_only": 1,
		"previous_section_key": keys[idx - 1] if idx > 0 else "",
		"next_section_key": keys[idx + 1] if idx >= 0 and idx + 1 < len(keys) else "",
	}


def get_submission_receipt_view(publication_id: str, bid_id: str) -> dict[str, Any]:
	_require_login()
	if not can_view_opened_bid():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	opening = _require_opened(pub.name)
	entry = _bid_in_register(opening, bid_id)
	if not entry:
		_throw("Bid is not on the opening register.", title="BID_NOT_IN_REGISTER")
	bid = frappe.get_doc(BID_DOCTYPE, bid_id)
	cfg = frappe.get_doc(CFG_DOCTYPE, pub.configuration)
	return {
		"publication_ref": cstr(pub.publication_ref or ""),
		"tender_title": _tender_title(cfg),
		"tenderer": cstr(entry.get("bidder_legal_name") or bid.bidder_legal_name or ""),
		"receipt_code": cstr(bid.receipt_code or ""),
		"submitted_at": cstr(bid.sealed_at or ""),
		"lots": entry.get("lots") if isinstance(entry.get("lots"), list) else [],
		"offer_type": cstr(entry.get("offer_type") or "Main"),
		"status": "Opened",
	}


def download_submitted_evidence(
	publication_id: str, bid_id: str, evidence_key: str
) -> dict[str, Any]:
	_require_login()
	if not can_download_evidence():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	opening = _require_opened(pub.name)
	if not _bid_in_register(opening, bid_id):
		_throw("Bid is not on the opening register.", title="BID_NOT_IN_REGISTER")
	bid = frappe.get_doc(BID_DOCTYPE, bid_id)
	snap = _parse_json(bid.evidence_seal_snapshot_json, {})
	versions = snap.get("versions") if isinstance(snap, dict) else []
	evidence_key = cstr(evidence_key or "").strip()
	match = None
	for v in versions or []:
		if isinstance(v, dict) and cstr(v.get("key") or v.get("evidence_key") or "") == evidence_key:
			match = v
			break
	if not match:
		_throw("Evidence not found on the sealed submission.", title="EVIDENCE_NOT_FOUND")
	_append_opening_audit(
		opening, "evidence_downloaded", {"receipt": cstr(bid.receipt_code or ""), "key": evidence_key}
	)
	frappe.db.set_value(OPENING_DOCTYPE, opening.name, "audit_json", opening.audit_json, update_modified=False)
	# Return sealed file metadata only — never live profile paths.
	return {
		"evidence_key": evidence_key,
		"file_name": cstr(match.get("file_name") or match.get("filename") or ""),
		"file_url": cstr(match.get("file_url") or match.get("url") or ""),
		"content_type": cstr(match.get("content_type") or ""),
		"sealed": 1,
	}


def get_submission_version_history(publication_id: str) -> dict[str, Any]:
	_require_login()
	if not can_view_version_history():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	pub = _get_publication(publication_id)
	_require_opened(pub.name)
	rows = frappe.get_all(
		BID_DOCTYPE,
		filters={"publication": publication_id},
		or_filters={"configuration": pub.configuration},
		fields=[
			"name",
			"bidder_legal_name",
			"bidder_label",
			"offer_type",
			"receipt_code",
			"sealed_at",
			"status",
			"supersedes",
			"superseded_by",
			"withdrawn_at",
		],
		order_by="sealed_at desc",
	)
	# frappe or_filters with filters may be wrong — query both and merge
	if not rows:
		rows = frappe.get_all(
			BID_DOCTYPE,
			filters={"configuration": pub.configuration},
			fields=[
				"name",
				"bidder_legal_name",
				"bidder_label",
				"offer_type",
				"receipt_code",
				"sealed_at",
				"status",
				"supersedes",
				"superseded_by",
				"withdrawn_at",
			],
			order_by="sealed_at desc",
		)
	history = []
	for r in rows:
		history.append(
			{
				"bid_id": r.name,
				"tenderer": cstr(r.bidder_legal_name or r.bidder_label or ""),
				"offer_type": cstr(r.offer_type or "Main"),
				"receipt_code": cstr(r.receipt_code or ""),
				"sealed_at": cstr(r.sealed_at or ""),
				"status": cstr(r.status or ""),
				"supersedes": cstr(r.supersedes or ""),
				"superseded_by": cstr(r.superseded_by or ""),
				"withdrawn": 1 if r.withdrawn_at else 0,
			}
		)
	return {"publication_id": pub.name, "versions": history}


# --- Officer tooling for fixtures (Administrator) ---


def officer_withdraw_sealed_bid(bid_id: str) -> dict[str, Any]:
	"""Mark a sealed bid withdrawn (fixture / authorised pre-deadline tooling)."""
	_require_login()
	if frappe.session.user != "Administrator" and not can_open_bids():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	doc = frappe.get_doc(BID_DOCTYPE, bid_id)
	if cstr(doc.status) != "Sealed":
		_throw("Only sealed bids can be withdrawn.", title="BID_STATE")
	doc.flags.ignore_sealed_meta_update = True
	doc.status = "Withdrawn"
	doc.withdrawn_at = now_datetime()
	doc.withdrawn_by = frappe.session.user
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"bid_id": doc.name, "status": "Withdrawn"}


def officer_link_supersession(old_bid_id: str, new_bid_id: str) -> dict[str, Any]:
	_require_login()
	if frappe.session.user != "Administrator" and not can_open_bids():
		_throw("Not permitted.", title="BID_SUBMISSIONS_DENIED")
	old = frappe.get_doc(BID_DOCTYPE, old_bid_id)
	new = frappe.get_doc(BID_DOCTYPE, new_bid_id)
	old.flags.ignore_sealed_meta_update = True
	new.flags.ignore_sealed_meta_update = True
	old.superseded_by = new.name
	new.supersedes = old.name
	old.save(ignore_permissions=True)
	new.save(ignore_permissions=True)
	frappe.db.commit()
	return {"old_bid_id": old.name, "new_bid_id": new.name}
