# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PublishOpeningArrangements and the public attendance projection
(BOP-CHG-001 v0.10 §3, §7, §10.2 ARRANGEMENTS, §10.5; BOP-A11).

The Accounting Officer publishes the actual attendance method and
instructions to the public Tender before the event, with a versioned record
and time. The opening time is the effective deadline; the join window opens
the operating profile's lead time before it. No box metadata, supplier
identity or committee credential is exposed. No Proceedings consumer."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.bid_opening.services import clock, errors, labels, people, records, settings

ARRANGEMENT = "Opening Arrangement"
COMING_SOON = "Details on how to attend the opening are coming soon"


def current(case: str) -> Any | None:
	name = frappe.db.get_value(ARRANGEMENT, {"opening_case": case, "status": "Published"}, "name")
	return frappe.get_doc(ARRANGEMENT, name) if name else None


def join_opens_at(scheduled_at) -> Any | None:
	lead = settings.get()["public_join_lead_minutes"]
	return get_datetime(scheduled_at) - timedelta(minutes=cint(lead)) if scheduled_at is not None and lead is not None else None


def publish_opening_arrangements(*, tender: str, attendance_method: str, access_instructions: str, expected_version: int, idempotency_key: str,
		user: str) -> dict[str, Any]:
	if not people.holds(user, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		records.check_version(doc, expected_version)
		if doc.state not in ("Awaiting deadline", "Ready to open"):
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if not cstr(attendance_method).strip():
			return {"ok": False, "code": "BOP_ATTENDANCE_NOT_PUBLISHED", "errors": {"attendance_method": "Say how people can attend."}}
		opens = join_opens_at(doc.effective_deadline)
		if opens is None:
			errors.fail("BOP_OPENING_PROFILE_UNAVAILABLE", {"reason": "operating_profile_incomplete"})
		previous = current(doc.name)
		number = frappe.db.count(ARRANGEMENT, {"opening_case": doc.name}) + 1
		at = clock.now()
		arrangement = records.insert(frappe.get_doc({
			"doctype": ARRANGEMENT, "arrangement_id": f"{doc.opening_id}-ARR-{number:02d}", "opening_case": doc.name, "version_number": number,
			"attendance_method": cstr(attendance_method).strip(), "access_instructions": cstr(access_instructions).strip(), "scheduled_at": doc.effective_deadline,
			"join_opens_at": opens, "published_by": user, "published_at": at, "status": "Published",
		}))
		if previous:
			previous.status = "Superseded"
			records.save(previous)
		records.bump(doc, current_arrangement=arrangement.name)
		return records.summary(doc, arrangement=arrangement.name, published_at=str(at))

	return records.command("PublishOpeningArrangements", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"attendance_method": attendance_method, "access_instructions": access_instructions, "expected_version": expected_version}, body=body)


def public_projection(case: str) -> dict[str, Any]:
	"""What the public Tender page may show (§10.5): the method and times only."""
	row = current(case)
	if not row:
		return {"published": False, "message": COMING_SOON}
	return {
		"published": True, "attendance_method": row.attendance_method, "access_instructions": row.access_instructions, "scheduled_at": str(row.scheduled_at),
		"scheduled_label": labels.when(row.scheduled_at), "join_opens_at": str(row.join_opens_at), "join_opens_label": labels.when(row.join_opens_at),
		"published_at": str(row.published_at), "published_label": labels.when(row.published_at), "version": row.version_number,
	}
