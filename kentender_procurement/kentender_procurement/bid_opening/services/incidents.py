# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Opening access support incidents (BOP-CHG-001 v0.10 §8, §10 branches (4)
and (6), §11 Notify support / View problem details; plan D11).

The system opens one incident per problem and case, assigns it to Opening
access support (the Technical Operator holders) and notifies them. When the
notice cannot be delivered, the chair's Notify support resends it for the
same incident; nothing opens a second incident. Support records the
resolution; only then can Start or Retry opening proceed. Support never acts
for the committee (§6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import appointment, clock, errors, notify, people, prc, records
from kentender_procurement.services import sequence

INCIDENT = "Opening Access Incident"
SUBJECTS = {
	"Opening profile unavailable": "Bid opening isn’t available yet",
	"Credential unavailable": "Opening access is not ready yet",
	"Attendance service unavailable": "The public attendance service is unavailable",
	"Package unreadable": "A bid could not be opened",
	"Package mismatch": "A bid does not match the submissions received at the deadline",
}


def open_incidents(case: str) -> list[dict[str, Any]]:
	return frappe.get_all(INCIDENT, filters={"opening_case": case, "status": "Open"}, fields=["name", "incident_id", "incident_type", "envelope_id", "raised_at",
		"holder_user", "notification_state", "notification_attempts", "last_notified_at"], order_by="raised_at asc")


def _deliver(row) -> dict[str, Any]:
	users = [row.holder_user] if row.holder_user else notify.holders()
	result = notify.deliver(incident_id=row.incident_id, subject=SUBJECTS[row.incident_type], message=f"{SUBJECTS[row.incident_type]}. Reference {row.incident_id}.",
		users=users)
	row.notification_attempts = cint(row.notification_attempts) + 1
	if result["delivered"]:
		row.notification_state = "Delivered"
		row.last_notified_at = clock.now()
	elif row.notification_state != "Delivered":
		row.notification_state = "Failed"
	records.save(row)
	return result


def ensure(doc, incident_type: str, *, envelope_id: str = "") -> Any:
	"""The one open incident of this type for this case (and envelope), opened and notified once."""
	name = frappe.db.get_value(INCIDENT, {"opening_case": doc.name, "incident_type": incident_type, "envelope_id": envelope_id, "status": "Open"}, "name")
	if name:
		return frappe.get_doc(INCIDENT, name)
	number = sequence.next_count(INCIDENT, {"opening_case": doc.name})
	holders = notify.holders()
	row = records.insert(frappe.get_doc({
		"doctype": INCIDENT, "incident_id": f"INC-OPEN-{doc.opening_id.removeprefix('BOC-')}-{number:02d}", "opening_case": doc.name, "incident_type": incident_type,
		"envelope_id": envelope_id, "raised_at": clock.now(), "holder_user": holders[0] if holders else None, "status": "Open", "notification_state": "Pending",
		"notification_attempts": 0,
	}))
	_deliver(row)
	return row


def notify_support(*, tender: str, incident: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""§11 Notify support: the chair retries the same incident's notice."""
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		chair = appointment.chair(doc.name)
		if not chair or chair["member_user"] != user:
			raise frappe.DoesNotExistError("Not found")
		row = frappe.get_doc(INCIDENT, {"opening_case": doc.name, "incident_id": incident})
		if row.status != "Open":
			return records.summary(doc, delivered=row.notification_state == "Delivered")
		result = _deliver(row)
		records.bump(doc)
		return records.summary(doc, delivered=result["delivered"], notification_state=row.notification_state)

	return records.command("NotifySupport", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"incident": incident}, body=body)


def record_resolution(*, tender: str, incident: str, resolution_note: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""Opening access support records that the problem is resolved (branch (6):
	"Support records resolution at 11:06:00"). An incident action only; it
	starts nothing and acts for no member."""
	if user not in notify.holders():
		raise frappe.DoesNotExistError("Not found")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		row = frappe.get_doc(INCIDENT, {"opening_case": doc.name, "incident_id": incident})
		if row.status != "Open":
			return records.summary(doc, resolved=False)
		row.update({"status": "Resolved", "resolution_note": cstr(resolution_note).strip(), "resolved_at": clock.now(), "resolved_by": user})
		records.save(row)
		records.bump(doc)
		return records.summary(doc, resolved=True)

	return records.command("RecordIncidentResolution", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"incident": incident, "note": resolution_note},
		body=body)


def record_unresolved(*, tender: str, incident: str, resolution_note: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""Support cannot fix it (board c11c): the paused opening goes to the
	Accounting Officer as "Decide how to proceed with the paused opening"."""
	from kentender_procurement.bid_opening.services import ceremony, not_held

	if user not in notify.holders():
		raise frappe.DoesNotExistError("Not found")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		row = frappe.get_doc(INCIDENT, {"opening_case": doc.name, "incident_id": incident})
		if row.status != "Open":
			return records.summary(doc, escalated=False)
		row.update({"status": "Unresolved", "resolution_note": cstr(resolution_note).strip(), "resolved_by": user})
		records.save(row)
		holders = people.accounting_officers()
		pause = ceremony.open_pause(doc.name)
		if pause:
			pause.outcome = "Escalated"
			pause.holder = holders[0] if holders else None
			records.save(pause)
		if doc.state == "Interrupted" and holders:
			number = sequence.next_count(not_held.DECISION, {"opening_case": doc.name})
			last = ceremony.last_committed(doc.name)
			records.insert(frappe.get_doc({
				"doctype": not_held.DECISION, "decision_item_id": f"{doc.opening_id}-DEC-{number:02d}", "opening_case": doc.name, "kind": "Paused opening",
				"holder_user": holders[0], "reason": SUBJECTS[row.incident_type], "last_committed_event": (last or {}).get("event_id", ""), "incident": row.incident_id,
				"status": "Open", "created_at": clock.now(),
			}))
		records.bump(doc)
		return records.summary(doc, escalated=True)

	return records.command("RecordIncidentUnresolved", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"incident": incident, "note": resolution_note},
		body=body)
