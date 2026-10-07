# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Debrief correspondence (AWD-CHG-001 v0.4 §5.6; AWD-AC-015).

`SaveAwardExplanation` keeps HOP's draft reply. `SendAwardExplanation` —
**Send and close** — freezes the exact reply for every delivery attempt and
closes the request only once the dispatch evidence is recorded; a failed or
uncertain dispatch leaves the request open ("The reply has not been sent.
This request remains open.") and retries the same reply without another
approval. Sent content is never edited; a later request is a new linked
record. A request is not a Review Board filing and changes no clock under
the test profile's debrief rule."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import clock, guards, notices, records, simulation, sources, state
from kentender_procurement.award.services.errors import fail, invalid

NOT_SENT = "The reply has not been sent. This request remains open."
CLOSED = "This request is closed."


def _load(doc, request: str):
	if not request or not frappe.db.exists(state.CORRESPONDENCE, {"name": request, "award_case": doc.name}):
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(state.CORRESPONDENCE, request)


def save(*, award: str, request: str, reply: str, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		c = _load(doc, request)
		if c.state == "Closed" or c.reply_state in ("Sending", "Sent"):
			fail("AWD_RECORD_CHANGED", {"reason": "reply_frozen"})
		records.update(c, reply_draft=cstr(reply), reply_state="Draft")
		records.bump(doc)
		return records.summary(state.reload(doc), request=c.name)

	return records.command("SaveAwardExplanation", case=award, idempotency_key=idempotency_key, actor=user, payload={"request": request, "reply": reply}, body=body,
		authorise=lambda: guards.require_hop(user))


def _dispatch(doc, c) -> bool:
	attempt = {"at": str(clock.now())}
	if simulation.flag("email_service_down"):
		attempt.update(outcome="Service unavailable")
		records.append_json(c, "attempts_json", attempt)
		records.save(c)
		return False
	email = cstr(frappe.db.get_value("User", c.requested_by, "email"))
	result = notices._transport({"to": email, "subject": f"Explanation of the award result for {doc.tender_reference}", "body": c.reply_text,
		"link": f"/supplier/awards/{c.notice}"})
	attempt.update(outcome="Delivered" if result else "Service unavailable", detail=cstr((result or {}).get("result")))
	records.append_json(c, "attempts_json", attempt)
	records.save(c)
	return bool(result)


def send(*, award: str, request: str, reply: str = "", idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		c = _load(doc, request)
		if c.state == "Closed":
			return records.summary(doc, request=c.name, closed=True, message=CLOSED)
		if c.reply_state != "Sending":
			text = cstr(reply).strip() or cstr(c.reply_draft).strip()
			invalid({"reply": "Enter the response." if not text else ""})
			records.update(c, reply_text=text, reply_state="Sending")
		if not _dispatch(doc, c):
			records.bump(doc)
			return {**records.summary(state.reload(doc), request=c.name), "ok": False, "code": "AWD_NOTICE_FAILED", "message": NOT_SENT}
		now = clock.now()
		records.update(c, reply_state="Sent", sent_at=now, state="Closed", closed_at=now, closed_by=user)
		records.bump(doc)
		records.audit(doc.name, "SendAwardExplanation", user, request=c.name)
		return records.summary(state.reload(doc), request=c.name, closed=True, message=CLOSED)

	return records.command("SendAwardExplanation", case=award, idempotency_key=idempotency_key, actor=user, payload={"request": request, "reply": reply}, body=body,
		authorise=lambda: guards.require_hop(user))


def retry_pending() -> int:
	count = 0
	for name in frappe.get_all(state.CORRESPONDENCE, filters={"reply_state": "Sending", "state": "Open"}, pluck="name"):
		c = frappe.get_doc(state.CORRESPONDENCE, name)
		doc = frappe.get_doc(records.CASE, c.award_case)
		if _dispatch(doc, c):
			now = clock.now()
			records.update(c, reply_state="Sent", sent_at=now, state="Closed", closed_at=now)
			count += 1
	return count


def open_requests(doc) -> list:
	return [frappe.get_doc(state.CORRESPONDENCE, n) for n in frappe.get_all(state.CORRESPONDENCE, filters={"award_case": doc.name, "state": "Open"},
		pluck="name", order_by="requested_at asc")]


def _provider(doc):
	return sources.for_case(doc)
