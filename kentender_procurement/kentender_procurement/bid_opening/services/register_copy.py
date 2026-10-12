# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RequestOpeningRegister and GetOpeningRegisterCopy (BOP-CHG-001 v0.10 §5 hand-off
table, §7, §10.5; BOP-A08, BOP-N09).

Only a verified submitting tenderer, a person with an active supplier-account
assignment in an organisation whose bid was opened, may request the final
register. Saying whom one represents proves nothing. Before completion the
request waits and the bidder is told when it is ready. When the operating
profile allows self-service the exact final register is available to them;
otherwise the Accounting Officer receives "Provide opening register for …"
and provides or declines it with a reason. Every request, delivery and
download is recorded with the register digest. The copy is the register
only: never a full bid, a competing bid or the opening record."""

from __future__ import annotations

import io
from typing import Any

import frappe
from frappe.utils import cstr, escape_html

from kentender_procurement.bid_opening.services import ceremony, clock, errors, finish, labels, people, records, settings
from kentender_procurement.bid_submission.services import opening_gateway
from kentender_procurement.services import sequence

REQUEST = "Opening Register Request"


def submitter_receipt(doc, user: str) -> str:
	opened = {e.receipt_reference for e in ceremony.entries(doc.name) if e.status == "Read out"}
	return next((r for r in opening_gateway.submitting_receipts(tender=doc.tender, user=user) if r in opened), "")


def _notify(user: str, doc, subject: str) -> None:
	from kentender_core.services.notification_service import emit_notification_log

	emit_notification_log(for_user=user, subject=subject, message=subject, document_type=records.CASE, document_name=doc.name, event_type="Opening register",
		entity_scope="Bid Opening", route=f"/tenders/{doc.tender_reference}/opening", correlation_key=f"bop-register:{doc.name}:{user}:{subject}")


def request_opening_register(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		receipt = submitter_receipt(doc, user)
		if not receipt:
			raise frappe.DoesNotExistError("Not found")
		existing = frappe.db.get_value(REQUEST, {"opening_case": doc.name, "requester_user": user, "status": ("in", ("Pending", "Ready", "Delivered"))}, "request_id")
		if existing:
			return records.summary(doc, request=existing, status=frappe.db.get_value(REQUEST, {"request_id": existing}, "status"))
		number = sequence.next_count(REQUEST, {"opening_case": doc.name})
		row = records.insert(frappe.get_doc({
			"doctype": REQUEST, "request_id": f"{doc.opening_id}-RRQ-{number:02d}", "opening_case": doc.name, "requester_user": user, "receipt_reference": receipt,
			"requested_at": clock.now(), "status": "Pending",
			"delivery_mode": "Self-service" if settings.get()["register_self_service"] else "Accounting Officer",
		}))
		if doc.state == "Opening complete":
			_release(doc, row)
		records.bump(doc)
		return records.summary(doc, request=row.request_id, status=row.status)

	return records.command("RequestOpeningRegister", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def _release(doc, row) -> None:
	if row.delivery_mode == "Self-service":
		row.update({"status": "Ready", "register_digest": frappe.db.get_value(finish.REGISTER, doc.register, "register_digest")})
		records.save(row)
		_notify(row.requester_user, doc, f"The opening register for {doc.tender_reference} is ready")


def release_pending(doc) -> None:
	"""At completion: self-service requests become ready; the others wait for the Accounting Officer."""
	for name in frappe.get_all(REQUEST, filters={"opening_case": doc.name, "status": "Pending"}, pluck="name"):
		_release(doc, frappe.get_doc(REQUEST, name))


def provide_register_copy(*, tender: str, request: str, idempotency_key: str, user: str, decline_reason: str = "") -> dict[str, Any]:
	"""The Accounting Officer's "Provide opening register for …": provide, or decline with a reason."""
	if not people.holds(user, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		row = frappe.get_doc(REQUEST, {"opening_case": doc.name, "request_id": request})
		if doc.state != "Opening complete" or row.status != "Pending":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state"})
		if decline_reason:
			row.update({"status": "Declined", "decline_reason": cstr(decline_reason).strip(), "delivered_by": user, "delivered_at": clock.now()})
			records.save(row)
			_notify(row.requester_user, doc, f"Your request for the opening register for {doc.tender_reference} was declined")
		else:
			row.update({"status": "Ready", "register_digest": frappe.db.get_value(finish.REGISTER, doc.register, "register_digest"), "delivered_by": user})
			records.save(row)
			_notify(row.requester_user, doc, f"The opening register for {doc.tender_reference} is ready")
		records.bump(doc)
		return records.summary(doc, request=request, status=row.status)

	return records.command("ProvideOpeningRegister", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"request": request, "decline": decline_reason},
		body=body)


def register_html(doc) -> str:
	e = escape_html
	register = frappe.get_doc(finish.REGISTER, doc.register)
	rows = finish.register_rows(doc.name)
	body = "".join(f"<tr><td>{r['number']}</td><td>{e(r['tenderer'])}</td><td>{e(r['submitted_total'])}</td><td>{e(r['security_given'])}</td>"
		f"<td>{e(labels.time_seconds(r['recorded_at']))}</td></tr>" for r in rows) or "<tr><td colspan='5'>Empty register. There were no current bids.</td></tr>"
	return (f"<html><head><meta charset='utf-8'></head><body><h1>Opening register</h1><p>{e(doc.tender_reference)} · {e(doc.tender_title or '')}</p>"
		f"<p>Opening completed {e(labels.when_seconds(doc.completed_at))}.</p><table border='1' cellpadding='4' style='border-collapse:collapse;width:100%'>"
		f"<tr><th>No.</th><th>Tenderer</th><th>Submitted total</th><th>Security given</th><th>Recorded at</th></tr>{body}</table>"
		f"<p>Register version {register.version_number}. Digest {e(register.register_digest)}.</p></body></html>")


def get_register_copy(*, tender: str, user: str) -> dict[str, Any]:
	"""The exact final register for a requester whose copy is ready; the first
	download is recorded as the delivery, and every download is audited."""
	from frappe.utils.pdf import get_pdf

	from kentender_core.services.audit_event_service import log_audit_event

	case = records.case_for(tender)
	name = frappe.db.get_value(REQUEST, {"opening_case": case, "requester_user": user, "status": ("in", ("Ready", "Delivered"))}, "name") if case else None
	if not name:
		raise frappe.DoesNotExistError("Not found")
	doc = frappe.get_doc(records.CASE, case)
	row = frappe.get_doc(REQUEST, name)
	pdf = get_pdf(register_html(doc))
	if row.status == "Ready":
		row.update({"status": "Delivered", "delivered_at": clock.now()})
		records.save(row)
	log_audit_event(event_type="Opening register downloaded", document_type=REQUEST, document_name=row.name, action="download", performed_by=user,
		timestamp=clock.now(), metadata={"register_digest": row.register_digest})
	return {"filename": f"Opening register {doc.tender_reference}.pdf", "content": pdf, "register_digest": row.register_digest}
