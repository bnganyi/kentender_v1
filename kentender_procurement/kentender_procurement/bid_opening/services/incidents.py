# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Opening access support incidents and their support findings (BOP-CHG-001 v0.16 §5.2, §7.2, §10.8; TRUST-OPS-001 v0.2 §5, §9, §10; plan D11).

The system opens one incident per problem and case, assigns it to Opening access support (the Technical Operator holders) and notifies them. When the notice
cannot be delivered, the chair's Notify support resends it for the same incident; nothing opens a second incident.

**Support records a finding** — Unresolved, Recovered or Cannot recover — with a reason, opaque evidence references, the exact incident revision it is made
against, the opening revision and the last committed ceremony step (`record_finding`). The record is append-only: a changed technical finding is a new row and
the earlier failed attempt stays. A finding changes no ceremony state; it only changes what the next holder may do:

- **Recovered**: the appointed chair may retry or resume (or, before Start, begin), still under the full roster and custody checks. The incident stays open
  until that committed act, which closes it ("Recovered and the opening continued");
- **Cannot recover**: every chair route stays closed and the Accounting Officer holds the one open decision item for this escalation (`not_held.ensure_item`),
  whose route is the existing Tender decision. Support never selects a ground, marks a bid non-responsive or resumes for the chair;
- a lawful cancellation closes the incident "Closed after tender cancellation", keeping its findings and the service defect as a separately owned follow-up
  (`close_for_cancellation`); a later finding on such an incident settles only that follow-up."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import appointment, clock, errors, notify, people, records
from kentender_procurement.services import sequence

INCIDENT = "Opening Access Incident"
FINDING = "Opening Incident Finding"
SUBJECTS = {
	"Opening profile unavailable": "Bid opening isn’t available yet",
	"Credential unavailable": "Opening access is not ready yet",
	"Attendance service unavailable": "The public attendance service is unavailable",
	"Package unreadable": "A bid could not be opened",
	"Package mismatch": "A bid does not match the submissions received at the deadline",
}
UNRESOLVED, RECOVERED, CANNOT_RECOVER = "Unresolved", "Recovered", "Cannot recover"
FINDINGS = (UNRESOLVED, RECOVERED, CANNOT_RECOVER)
CLOSED_RECOVERED = "Recovered and the opening continued"
CLOSED_CANCELLED = "Closed after tender cancellation"
#: BOP-CHG-001 v0.16 §10.8: what Cannot recover says to the chair and the Accounting Officer.
NOT_RECOVERED = "Opening could not be recovered. The Accounting Officer must review the next step."


def open_incidents(case: str) -> list[dict[str, Any]]:
	return frappe.get_all(INCIDENT, filters={"opening_case": case, "status": "Open"}, fields=["name", "incident_id", "incident_type", "envelope_id", "raised_at",
		"holder_user", "notification_state", "notification_attempts", "last_notified_at", "current_finding", "incident_revision"], order_by="raised_at asc")


def blocking_incidents(case: str) -> list[dict[str, Any]]:
	"""Open incidents the chair cannot proceed past: every open one whose latest finding is not Recovered."""
	return [r for r in open_incidents(case) if r.current_finding != RECOVERED]


def cannot_recover(case: str) -> bool:
	return any(r.current_finding == CANNOT_RECOVER for r in open_incidents(case))


def findings(incident_id: str) -> list[dict[str, Any]]:
	return frappe.get_all(FINDING, filters={"incident": incident_id}, fields=["finding_id", "finding_no", "finding", "reason", "evidence_refs", "recorded_by", "recorded_at",
		"incident_revision", "opening_revision", "last_committed_event"], order_by="finding_no asc")


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
		"envelope_id": envelope_id, "raised_at": clock.now(), "holder_user": holders[0] if holders else None, "status": "Open", "current_finding": UNRESOLVED,
		"incident_revision": 0, "notification_state": "Pending", "notification_attempts": 0,
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


def record_finding(*, tender: str, incident: str, finding: str, reason: str, evidence_refs: str = "", expected_revision=None, idempotency_key: str, user: str,
		command: str = "RecordIncidentFinding") -> dict[str, Any]:
	"""RecordIncidentFinding (TRUST-OPS-001 v0.2 §9.2): an Opening access support holder appends one finding.

	It needs the incident's exact revision when the caller gives one (a stale revision is a conflict that writes nothing), a reason, an active Opening access
	support assignment, and a retry key (a duplicate accepted write returns the original; the same key with another fact conflicts). It never writes Bid Opening,
	Tenders or Proceedings state, and records no bid content, count or identity."""
	if finding not in FINDINGS:
		return {"ok": False, "message": "Choose what you found.", "errors": {"finding": "Choose Unresolved, Recovered or Cannot recover."}}
	if user not in notify.holders():
		raise frappe.DoesNotExistError("Not found")
	if not cstr(reason).strip():
		return {"ok": False, "message": "Record what you found.", "errors": {"reason": "Record what you found."}}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if not frappe.db.exists(INCIDENT, {"opening_case": doc.name, "incident_id": incident}):
			raise frappe.DoesNotExistError("Not found")
		row = frappe.get_doc(INCIDENT, {"opening_case": doc.name, "incident_id": incident}, for_update=True)
		if expected_revision is not None and cint(expected_revision) != cint(row.incident_revision):
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "incident_revision", "incident_revision": cint(row.incident_revision)})
		if row.status == "Closed":
			return _settle_service_followup(doc, row, finding=finding, reason=reason, evidence_refs=evidence_refs, user=user, key=idempotency_key)
		last = _last_step(doc)
		number = cint(row.incident_revision) + 1
		records.insert(frappe.get_doc({
			"doctype": FINDING, "finding_id": f"{row.incident_id}-F{number:02d}", "incident": row.incident_id, "opening_case": doc.name, "finding_no": number, "finding": finding,
			"reason": cstr(reason).strip(), "evidence_refs": cstr(evidence_refs).strip(), "recorded_by": user, "recorded_at": clock.now(), "incident_revision": number,
			"opening_revision": cint(doc.record_version), "last_committed_event": last, "request_key": idempotency_key,
		}))
		values = {"current_finding": finding, "incident_revision": number, "resolution_note": cstr(reason).strip(), "resolved_by": user, "resolved_at": clock.now()}
		row.update(values)
		records.save(row)
		escalated = None
		if finding == CANNOT_RECOVER:
			escalated = _escalate(doc, row, last)
		return {**records.summary(doc), "incident": row.incident_id, "finding": finding, "incident_revision": number, "item": escalated}

	return records.command(command, tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"incident": incident, "finding": finding, "reason": reason, "evidence_refs": evidence_refs, "expected_revision": cstr(expected_revision)}, body=body)


def _last_step(doc) -> str:
	from kentender_procurement.bid_opening.services import ceremony

	last = ceremony.last_committed(doc.name)
	return cstr((last or {}).get("event_id")) or cstr(doc.last_committed_event)


def _escalate(doc, row, last: str) -> str:
	"""Cannot recover: the Accounting Officer holds one open decision item for this escalation, whatever state the opening is in; a pause is marked escalated."""
	from kentender_procurement.bid_opening.services import ceremony, not_held

	pause = ceremony.open_pause(doc.name)
	holders = people.accounting_officers()
	if pause:
		pause.outcome = "Escalated"
		pause.holder = holders[0] if holders else None
		records.save(pause)
	if not holders or doc.state in ("Not held", "Cancelled after start", "Opening complete"):
		return ""
	kind = "Paused opening" if doc.state == "Interrupted" else "Opening cannot proceed"
	item = not_held.ensure_item(doc, kind=kind, reason=SUBJECTS[row.incident_type], holder=holders[0], incident=row.incident_id, last_event=last)
	return item.decision_item_id


def _settle_service_followup(doc, row, *, finding: str, reason: str, evidence_refs: str, user: str, key: str) -> dict[str, Any]:
	"""A finding on an incident that was closed after a cancellation: it appends its evidence and settles only the separately owned service defect — never
	the proceeding, which has ended."""
	if row.closure != CLOSED_CANCELLED:
		errors.fail("BOP_VERSION_CONFLICT", {"reason": "incident_closed", "closure": cstr(row.closure)})
	number = cint(row.incident_revision) + 1
	records.insert(frappe.get_doc({
		"doctype": FINDING, "finding_id": f"{row.incident_id}-F{number:02d}", "incident": row.incident_id, "opening_case": doc.name, "finding_no": number, "finding": finding,
		"reason": cstr(reason).strip(), "evidence_refs": cstr(evidence_refs).strip(), "recorded_by": user, "recorded_at": clock.now(), "incident_revision": number,
		"opening_revision": cint(doc.record_version), "last_committed_event": cstr(doc.last_committed_event), "request_key": key,
	}))
	row.update({"current_finding": finding, "incident_revision": number, "service_followup": "Resolved" if finding == RECOVERED else "Open"})
	records.save(row)
	return {**records.summary(doc), "incident": row.incident_id, "finding": finding, "incident_revision": number, "service_followup": row.service_followup}


def close_recovered(doc, event_id: str) -> int:
	"""The chair's committed Begin / Resume / Retry closes every open incident whose latest finding is Recovered (TRUST-OPS-001 v0.2 §10 (a))."""
	count = 0
	for r in open_incidents(doc.name):
		if r.current_finding == RECOVERED:
			row = frappe.get_doc(INCIDENT, r.name)
			row.update({"status": "Closed", "closure": CLOSED_RECOVERED, "closure_ref": event_id, "closed_at": clock.now(), "service_followup": "Resolved"})
			records.save(row)
			count += 1
	return count


def close_for_cancellation(doc, *, reference: str, event_id: str) -> int:
	"""A lawful cancellation ended the proceeding: its open incidents close with the reason "Closed after tender cancellation" (TRUST-OPS-001 v0.2 §9.3, §10 (b)).
	The incident keeps its findings. The service defect is a separately owned follow-up and is not claimed repaired unless the latest finding says Recovered."""
	count = 0
	for r in open_incidents(doc.name):
		row = frappe.get_doc(INCIDENT, r.name)
		row.update({"status": "Closed", "closure": CLOSED_CANCELLED, "closure_ref": reference or event_id, "closed_at": clock.now(),
			"service_followup": "Resolved" if row.current_finding == RECOVERED else "Open"})
		records.save(row)
		count += 1
	return count


def record_resolution(*, tender: str, incident: str, resolution_note: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""Support records that the problem is Recovered (branch (6): "Support records resolution at 11:06:00"). A finding only: it starts nothing and acts for
	no member. Kept as the plain-words entry point; it is `record_finding` with the Recovered finding."""
	return record_finding(tender=tender, incident=incident, finding=RECOVERED, reason=resolution_note, idempotency_key=idempotency_key, user=user, command="RecordIncidentResolution")


def record_unresolved(*, tender: str, incident: str, resolution_note: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""Support cannot fix it (board c11c): the Cannot recover finding, which gives the Accounting Officer the opening's decision item."""
	return record_finding(tender=tender, incident=incident, finding=CANNOT_RECOVER, reason=resolution_note, idempotency_key=idempotency_key, user=user, command="RecordIncidentUnresolved")
