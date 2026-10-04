# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Recovery commands (AWD-CHG-001 v0.4 §5.4, §7 RetryNoticeDelivery; V05, V16).

**Correct contact** (the Head of Procurement): the contact owner corrects the
address through its own form; Award reads the corrected route and retries
the same notice. The signed content and the supplier never change, and every
earlier address and attempt stays recorded. **Retry operation** (the
technical operator): re-runs the failed technical operation — never a
business decision — and records its own outcome."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import clock, eligibility, events, guards, issues, notices, notify, people, records, sources, state
from kentender_procurement.award.services.errors import fail

NOT_CORRECTED = "The contact owner has not corrected the address yet. The supplier has been asked to correct it."


def correct_contact(*, award: str, notice: str, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		if not notice or not frappe.db.exists(state.NOTICE, {"name": notice, "award_case": doc.name}):
			raise frappe.DoesNotExistError("Not found")
		n = frappe.get_doc(state.NOTICE, notice)
		if n.status == "Given":
			return records.summary(doc, notice=n.name, outcome="Given")
		current = sources.for_case(doc).notice_contact(n.bid) if n.bid else {}
		if not current.get("email") or current["email"] == n.contact_email:
			users = [p.get("user") for p in sources.for_case(doc).organisation_users(n.organisation, at=clock.now())]
			notify.tell(doc, users, subject=f"Correct your notice contact for {doc.tender_reference}", message="An award notice could not be delivered to your notice contact.",
				key=f"contact:{n.name}:{n.contact_email}", event_type="Award notice")
			return {**records.summary(doc, notice=n.name), "ok": False, "code": "AWD_NOTICE_FAILED", "message": NOT_CORRECTED}
		outcome = notices.retry(doc, n, actor=user)
		records.bump(state.reload(doc))
		return records.summary(state.reload(doc), notice=n.name, outcome=outcome)

	return records.command("RetryNoticeDelivery", case=award, idempotency_key=idempotency_key, actor=user, payload={"notice": notice, "via": "Correct contact"}, body=body)


def retry_operation(*, award: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""The technical operator's **Retry operation** for this award's failed technical work."""

	def body() -> dict[str, Any]:
		if user not in people.technical_operators():
			raise frappe.DoesNotExistError("Not found")
		doc = records.lock(award)
		done = {"notices": 0, "events": 0, "package": ""}
		for n in (frappe.get_doc(state.NOTICE, x) for x in frappe.get_all(state.NOTICE, filters={"award_case": doc.name, "status": "Failed",
				"failure_reason": "Service unavailable"}, pluck="name")):
			if notices.retry(doc, n, actor=user) == "Delivered":
				done["notices"] += 1
		for e in (frappe.get_doc(state.EVENT, x) for x in frappe.get_all(state.EVENT, filters={"award_case": doc.name, "status": ("in", ("Pending", "Failed"))},
				pluck="name")):
			if events.deliver(doc, e) == "Delivered":
				done["events"] += 1
		doc = state.reload(doc)
		if doc.stage == "Waiting to proceed":
			done["package"] = eligibility.deliver(doc)["status"]
		records.audit(doc.name, "RetryOperation", user, **{k: cstr(v) for k, v in done.items()})
		return {"ok": True, "award": doc.name, **done}

	return records.command("RetryOperation", case=award, idempotency_key=idempotency_key, actor=user, payload={}, body=body)
