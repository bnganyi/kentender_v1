# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The bidder-safe public projection of published Tenders (BDS-CHG-001 v0.8
§7.1 `GetAvailableTenders` / `GetPublishedTenderForBidder` inputs; plan D3,
Tenders tracker TND12-B01).

Tenders owns the facts; Bid Submission renders them. Everything here is an
allowlist built from the published Tender Version with the Issued addenda
applied, so a supplier sees the current delivery location, deadline and
title — never an internal record name, digest, file path, release identity,
candidate identity or officer-only value. A frozen addendum awaiting channel
confirmation is not public yet (TPR §5.6).

- `available_tenders(at)` — every published Tender (open, ended or
  cancelled) with its availability at the trusted instant `at`: `open`
  strictly before the current submission deadline, `closed` from it (even
  before the close job runs), `cancelled` once cancelled.
- `published_tender(reference, at)` — the detail: facts, official
  documents, effective addenda, public answers and any cancellation.
- `stream_public_document(reference, key)` — the file bytes of one public
  document by its public key (`invitation`, `complete-tender`, an Issued
  addendum reference, `cancellation-notice`); PDF when rendered, else HTML.
- `public_answers(tender)` — answers sent to all registered candidates,
  anonymous, each with an opaque `key`.
- `candidate_view(tender, candidate_registration_id)` — that candidate's own
  questions and the notices addressed to it (Tenders-owned delivery states).
- `resolve_published(reference)` — the internal Tender name, for Bid
  Submission's server-side binding only; never rendered.

Machine values only: ISO datetimes with the site offset and decimal text.
Reads create nothing and need no permission (Guest reads the same result).
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.tenders.services import bid_definition, candidate_gateway, clock
from kentender_procurement.tenders.services.bid_definition import decimal_text, iso_datetime
from kentender_procurement.tenders.services.publication_read import _change_summary

PUBLIC_STATUSES = ("Published — open", "Submission period ended", "Cancelled")
OPEN_STATUS = "Published — open"
#: public key → (Tender Document kind, visible label)
DOCUMENT_KEYS: dict[str, tuple[str, str]] = {
	"invitation": ("Invitation", "Invitation to Tender"),
	"complete-tender": ("Complete Tender", "Complete Tender"),
}
CANCELLATION_KEY = "cancellation-notice"
CANCELLATION_LABEL = "Cancellation notice"
#: Tenders notice type → the subject kind a supplier sees
NOTICE_KINDS = {"Clarification response": "answer", "Addendum issued": "addendum", "Deadline changed": "addendum", "Tender cancelled": "cancellation"}
_ROOT_FIELDS = ["name", "tender_reference", "overall_status", "published_at", "publication", "submission_deadline", "clarification_deadline", "cancellation"]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _published_root(reference: str):
	ref = cstr(reference).strip()
	if not ref:
		return None
	row = frappe.db.get_value("Tender", {"tender_reference": ref}, _ROOT_FIELDS, as_dict=True)
	if not row or not row.published_at or not row.publication or row.overall_status not in PUBLIC_STATUSES:
		return None
	return row


def _instant(at):
	return get_datetime(at) if at else clock.now()


def _availability(row, at) -> str:
	if row.overall_status == "Cancelled":
		return "cancelled"
	if row.overall_status != OPEN_STATUS or not row.submission_deadline or _instant(at) >= get_datetime(row.submission_deadline):
		return "closed"
	return "open"


def _issued_addenda(tender: str) -> list[dict[str, Any]]:
	return frappe.get_all(
		"Tender Addendum", filters={"tender": tender, "status": "Issued"},
		fields=["name", "addendum_reference", "change_class", "affected_area", "affected_reference", "affected_reference_key", "revised_value", "deadline_extension_required", "revised_submission_deadline", "issued_at"],
		order_by="addendum_number asc", limit_page_length=0,
	)


def _published_version(row) -> str:
	return cstr(frappe.db.get_value("Tender Publication", row.publication, "tender_version"))


def _effective(row, addenda: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
	"""(published projection, the same with the Issued addenda applied)."""
	root = frappe.get_doc("Tender", row.name)
	version = frappe.get_doc("Tender Version", _published_version(row))
	base = bid_definition.projection(root, version, publication_id=row.publication)
	return base, bid_definition.apply_addenda(base, addenda)


def answer_key(tender: str, clarification: str) -> str:
	"""An opaque, stable public handle for one clarification answer."""
	return hashlib.sha256(f"{tender}:{clarification}".encode()).hexdigest()[:16]


def _document(filters: dict[str, Any]):
	rows = frappe.get_all("Tender Document", filters=filters, fields=["name", "file", "html_file"], order_by="generated_at desc, creation desc", limit=1)
	return rows[0] if rows else None


def _official_document(row, key: str):
	kind, _label = DOCUMENT_KEYS[key]
	return _document({"tender": row.name, "kind": kind, "tender_version": _published_version(row)})


def _cancellation_document(row):
	if row.overall_status != "Cancelled" or not row.cancellation:
		return None
	return _document({"cancellation": row.cancellation, "kind": "Cancellation notice"})


# --------------------------------------------------------------------------
# public reads
# --------------------------------------------------------------------------


def resolve_published(reference: str) -> str | None:
	row = _published_root(reference)
	return row.name if row else None


def availability(reference: str, *, at=None) -> str | None:
	"""`open`, `closed` or `cancelled` for a published Tender at `at`, or None
	when no published Tender has that reference (BDS-CHG-001 v0.8 §7.2
	`StartBid` rechecks the open state)."""
	row = _published_root(reference)
	return _availability(row, at) if row else None


def available_tenders(*, at=None) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Tender", filters={"published_at": ("is", "set"), "overall_status": ("in", PUBLIC_STATUSES), "publication": ("is", "set")},
		fields=_ROOT_FIELDS, order_by="submission_deadline asc, tender_reference asc", limit_page_length=0,
	)
	out = []
	for row in rows:
		_base, effective = _effective(row, _issued_addenda(row.name))
		out.append(
			{
				"reference": cstr(row.tender_reference), "title": cstr(effective["tender"]["title"]), "procuring_entity": cstr(effective["procuring_entity"]["name"]),
				"method": cstr(effective["tender"]["procurement_method"]), "reservation": cstr(effective["reservation"]["category"]),
				"submission_deadline": iso_datetime(row.submission_deadline), "published_at": iso_datetime(row.published_at), "availability": _availability(row, at),
			}
		)
	return out


def published_tender(reference: str, *, at=None) -> dict[str, Any] | None:
	row = _published_root(reference)
	if not row:
		return None
	addenda = _issued_addenda(row.name)
	base, effective = _effective(row, addenda)
	items = [
		{"description": cstr(i["item_name"]), "quantity": cstr(i["quantity"]), "unit": cstr(i["unit"]), "delivery_location": cstr(i["delivery_location"]), "latest_delivery": cstr(i["latest_delivery_date"])}
		for i in effective["items"]
	]
	units = {i["unit"] for i in items}
	locations = {i["delivery_location"] for i in items}
	availability = _availability(row, at)
	published_at = iso_datetime(row.published_at)
	documents = []
	for key, (_kind, label) in DOCUMENT_KEYS.items():
		doc = _official_document(row, key)
		if doc:
			documents.append({"key": key, "label": label, "published_at": published_at, "format": "pdf" if doc.file else "html"})
	cancellation = None
	if row.overall_status == "Cancelled" and row.cancellation:
		cancellation = {
			"cancelled_at": iso_datetime(frappe.db.get_value("Tender Cancellation", row.cancellation, "decided_at")),
			"notice_key": CANCELLATION_KEY if _cancellation_document(row) else "",
		}
	return {
		"reference": cstr(row.tender_reference),
		"title": cstr(effective["tender"]["title"]),
		"procuring_entity": cstr(effective["procuring_entity"]["name"]),
		"method": cstr(effective["tender"]["procurement_method"]),
		"reservation": cstr(effective["reservation"]["category"]),
		"items": items,
		"total_quantity": {"quantity": decimal_text(sum((Decimal(i["quantity"] or "0") for i in items), Decimal(0))), "unit": next(iter(units))} if items and len(units) == 1 else None,
		"delivery_location": next(iter(locations)) if len(locations) == 1 else "",
		"latest_delivery": max((i["latest_delivery"] for i in items if i["latest_delivery"]), default=""),
		"currency": cstr(effective["tender"]["currency"]),
		"tender_security_amount": cstr(effective["tender"]["tender_security"]["amount"]),
		"validity_days": int(effective["tender"]["validity_days"] or 0),
		"published_at": published_at,
		"clarification_deadline": iso_datetime(row.clarification_deadline) or cstr(base["tender"]["clarification_deadline"]),
		"original_submission_deadline": cstr(base["tender"]["submission_deadline"]),
		"submission_deadline": iso_datetime(row.submission_deadline),
		"availability": availability,
		"clarifications_open": availability == "open" and bool(row.clarification_deadline) and _instant(at) < get_datetime(row.clarification_deadline),
		"documents": documents,
		"addenda": [
			{
				"reference": cstr(a.addendum_reference), "summary": _change_summary(a), "issued_at": iso_datetime(a.issued_at),
				"revised_submission_deadline": iso_datetime(a.revised_submission_deadline) if a.deadline_extension_required else "",
				"document_key": cstr(a.addendum_reference) if _document({"addendum": a.name, "kind": "Addendum notice"}) else "",
			}
			for a in addenda
		],
		"answers": public_answers(row.name),
		"cancellation": cancellation,
	}


def stream_public_document(reference: str, key: str) -> dict[str, Any] | None:
	row = _published_root(reference)
	key = cstr(key).strip()
	if not row or not key:
		return None
	if key in DOCUMENT_KEYS:
		doc, name = _official_document(row, key), DOCUMENT_KEYS[key][1]
	elif key == CANCELLATION_KEY:
		doc, name = _cancellation_document(row), CANCELLATION_LABEL
	else:
		addendum = frappe.db.get_value("Tender Addendum", {"tender": row.name, "addendum_reference": key, "status": "Issued"}, "name")
		if not addendum:
			return None
		doc, name = _document({"addendum": addendum, "kind": "Addendum notice"}), key
	if not doc or not (doc.file or doc.html_file):
		return None
	from kentender_core.services.file_integrity import read_bytes

	content = read_bytes(doc.file or doc.html_file)  # exact bytes: a decoded-and-re-encoded PDF is corrupt
	return {
		"file_name": f"{name}.{'pdf' if doc.file else 'html'}",
		"content_type": "application/pdf" if doc.file else "text/html; charset=utf-8",
		"content": content,
	}


def public_answers(tender: str) -> list[dict[str, Any]]:
	"""Answers sent to all registered candidates, without the asker. An
	answer that changed the Tender is public only once its addendum is
	Issued (Tenders already holds it back until then; checked again here)."""
	rows = frappe.get_all(
		"Tender Clarification", filters={"tender": tender, "status": "Answered", "response_audience": "All registered candidates"},
		fields=["name", "question", "response", "responded_at", "affects_published_tender", "required_addendum"], order_by="responded_at asc, received_at asc", limit_page_length=0,
	)
	out = []
	for r in rows:
		if r.affects_published_tender and (not r.required_addendum or frappe.db.get_value("Tender Addendum", r.required_addendum, "status") != "Issued"):
			continue
		out.append({"key": answer_key(tender, r.name), "question": cstr(r.question), "answer": cstr(r.response), "answered_at": iso_datetime(r.responded_at)})
	return out


def _question_status(status: str) -> str:
	# "Awaiting addendum" and "Awaiting response" are officer states; the
	# supplier sees only that the question was received until it is answered.
	return status if status in ("Answered", "Closed") else "Received"


def candidate_view(tender: str, candidate_registration_id: str) -> dict[str, Any] | None:
	"""One registered candidate's own questions and the Tenders notices
	addressed to it; None when it is not a registered candidate of `tender`."""
	cid = cstr(candidate_registration_id).strip()
	if not cid or not candidate_gateway.candidate_registration(tender=tender, candidate_registration_id=cid):
		return None
	questions = []
	for q in frappe.get_all(
		"Tender Clarification", filters={"tender": tender, "candidate_registration_id": cid},
		fields=["name", "question", "received_at", "status", "response", "response_audience", "responded_at"], order_by="received_at asc", limit_page_length=0,
	):
		answered = q.status == "Answered"
		questions.append(
			{
				"key": answer_key(tender, q.name), "question": cstr(q.question), "received_at": iso_datetime(q.received_at), "status": _question_status(q.status),
				"audience": cstr(q.response_audience) if answered else "", "answer": cstr(q.response) if answered else "", "answered_at": iso_datetime(q.responded_at) if answered else "",
			}
		)
	notices = []
	for n in frappe.get_all(
		"Tender Candidate Notice", filters={"tender": tender, "candidate_registration_id": cid},
		fields=["notice_type", "subject_id", "status", "attempt_count", "last_attempt_at", "delivered_at"], order_by="creation asc", limit_page_length=0,
	):
		kind = NOTICE_KINDS.get(n.notice_type, "")
		if kind == "answer":
			subject_key = answer_key(tender, n.subject_id)
		elif kind == "addendum":
			subject_key = cstr(frappe.db.get_value("Tender Addendum", n.subject_id, "addendum_reference"))
		else:
			subject_key = CANCELLATION_KEY
		notices.append(
			{"kind": kind, "subject_key": subject_key, "status": cstr(n.status), "attempt_count": int(n.attempt_count or 0), "last_attempt_at": iso_datetime(n.last_attempt_at), "delivered_at": iso_datetime(n.delivered_at)}
		)
	return {"questions": questions, "notices": notices}
