# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The live ceremony (BOP-CHG-001 v0.10 §5 Opening and Interrupted, §7
BeginOpening, OpenNextTender, RecordInterruption, ResumeOpening; binding
rows → PRC `StartProceeding`, `AppendProceedingEvent`; BOP-A02, A04, A05,
A09, N02, N05, N06, N16).

- Begin needs every Start guard to pass, then starts the Proceeding with the
  actual roster; only now may a ceremony user learn whether there are bids.
- Open next bid takes the next current timely envelope once, through the
  joint release, renders it and numbers it. Nothing is read aloud yet.
- An absent member, lost secure access, an unreadable package or a package
  that does not match the closed record pauses the opening before the next
  material act, with the exact cause and the last committed step. The
  Proceeding stays In session; a pause is an event, not a reset.
- A pause for an absent member ends when every member is present again and
  the release is renewed; a package problem needs support's recorded
  resolution and the chair's Retry opening, which opens the same bid again.

Every material command rechecks the whole roster on the server; the chair
cannot act for anyone."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import (
	appointment, clock, custody, custody_participation, errors, guards, incidents, labels, prc, presence, records, renderer, renders,
)

ENTRY = "Opening Entry"
EXCEPTION = "Opening Exception"
PAUSE_CLASSES = ("Member absent", "Credential unavailable", "Package unreadable", "Package mismatch")
CEREMONY_STATES = ("Opening", "Interrupted")


def require_chair(doc, user: str) -> dict[str, Any]:
	chair = appointment.chair(doc.name)
	if not chair or chair["member_user"] != user:
		raise frappe.DoesNotExistError("Not found")
	return chair


def require_recorder(doc, user: str) -> dict[str, Any]:
	recorder = appointment.recorder(doc.name)
	if not recorder or recorder["member_user"] != user:
		raise frappe.DoesNotExistError("Not found")
	return recorder


def envelopes(doc) -> list[dict[str, Any]]:
	manifest = custody.closed_manifest(doc.tender)
	return custody.current_envelopes(manifest) if manifest else []


def entries(case: str) -> list[Any]:
	return [frappe.get_doc(ENTRY, n) for n in frappe.get_all(ENTRY, filters={"opening_case": case}, order_by="entry_number asc", pluck="name")]


def open_pause(case: str) -> Any | None:
	name = frappe.db.get_value(EXCEPTION, {"opening_case": case, "exception_class": ("in", PAUSE_CLASSES), "outcome": ("in", ("Open", "Escalated"))}, "name",
		order_by="recorded_at desc")
	return frappe.get_doc(EXCEPTION, name) if name else None


def last_committed(case: str) -> dict[str, Any] | None:
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	row = frappe.db.get_value("Proceeding Event", {"proceeding": proceeding, "source": ("in", ("Owner", "Recorder", "Member")),
		"event_type": ("not in", ("OpeningPaused", "OpeningResumed", "AttendanceArrival", "AttendanceDeparture", "CustodyParticipation", "ClosedManifestReference"))},
		["event_id", "event_type", "note", "recorded_at"], as_dict=True, order_by="sequence desc")
	return dict(row) if row else None


def absent_members(doc) -> list[dict[str, Any]]:
	present = presence.present_members(doc.name)
	return [m for m in appointment.roster(doc.name) if m["member_user"] not in present]


def _exception(doc, exception_class: str, *, fact: str, user: str, entry: str = "", envelope_id: str = "", incident: str = "", outcome: str = "Open",
		speaker: str = "", response: str = "", event_id: str = "") -> Any:
	number = frappe.db.count(EXCEPTION, {"opening_case": doc.name}) + 1
	return records.insert(frappe.get_doc({
		"doctype": EXCEPTION, "exception_id": f"{doc.opening_id}-EXC-{number:03d}", "opening_case": doc.name, "exception_class": exception_class, "entry": entry,
		"envelope_id": envelope_id, "observed_fact": fact, "speaker_name": speaker, "response": response, "recorded_by": user if frappe.db.exists("User", user) else None,
		"recorded_at": clock.now(), "outcome": outcome, "incident": incident, "proceeding_event": event_id,
	}))


def pause(doc, exception_class: str, *, fact: str, key: str, member: str = "", envelope_id: str = "", incident: str = "") -> Any:
	"""RecordInterruption: the opening pauses before the next material act."""
	from kentender_procurement.proceedings.services import events

	last = last_committed(doc.name)
	event = events.append_event(**prc.ref(doc.name), event_type="OpeningPaused", source="Owner", owner_event_id=f"pause:{key}",
		payload={"cause": exception_class, "member": member, "envelope": envelope_id, "incident": incident, "last_event": (last or {}).get("event_id", "")},
		note=fact, idempotency_key=prc.key(key, "pause"), actor=prc.SYSTEM_ACTOR)
	row = _exception(doc, exception_class, fact=fact, user=prc.SYSTEM_ACTOR, envelope_id=envelope_id, incident=incident, event_id=event["event_id"],
		speaker=appointment.member(doc.name, member)["full_name"] if member and appointment.member(doc.name, member) else "")
	doc.state = "Interrupted"
	return row


def resume(doc, key: str, *, actor: str) -> str:
	from kentender_procurement.proceedings.services import events

	row = open_pause(doc.name)
	if row:
		row.outcome = "Resolved"
		records.save(row)
	event = events.append_event(**prc.ref(doc.name), event_type="OpeningResumed", source="Owner", owner_event_id=f"resume:{key}",
		payload={"pause": row.exception_id if row else ""}, note="The opening continues from the last recorded step.", idempotency_key=prc.key(key, "resume"),
		actor=actor)
	from kentender_procurement.bid_opening.services import not_held

	for name in frappe.get_all(not_held.DECISION, filters={"opening_case": doc.name, "kind": "Paused opening", "status": "Open"}, pluck="name"):
		item = frappe.get_doc(not_held.DECISION, name)
		item.update({"status": "Cleared", "cleared_at": clock.now(), "clearing_event": event["event_id"]})
		records.save(item)
	doc.state = "Opening"
	return event["event_id"]


def ceremony_ready(doc) -> tuple[bool, str]:
	"""The whole roster present, the joint release valid, no package or access problem open."""
	absent = absent_members(doc)
	if absent:
		return False, "member_absent"
	if not custody_participation.valid(doc):
		return False, "release_not_valid"
	if incidents.open_incidents(doc.name):
		return False, "incident_open"
	return True, ""


def try_resume_after_rejoin(doc, key: str) -> bool:
	"""Board c10b: when the absent member has rejoined and signed in again, the
	opening continues from the last recorded step without another click."""
	row = open_pause(doc.name)
	if doc.state != "Interrupted" or not row or row.exception_class != "Member absent":
		return False
	ready, _reason = ceremony_ready(doc)
	if not ready:
		return False
	resume(doc, key, actor=prc.SYSTEM_ACTOR)
	return True


def begin_opening(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_chair(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Ready to open" or prc.state(doc.name) != "Pending":
			if doc.state in ("Not held", "Cancelled after start") or prc.state(doc.name) in ("Not held", "Aborted after start"):
				errors.fail("BOP_VERSION_CONFLICT", {"reason": "terminal", "state": doc.state})
			guard = guards.start_guard(doc)
			if not guard["allowed"]:
				return {"ok": False, "code": guard["reason_code"], "message": guard["message"], "guard": guard}
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		guard = guards.start_guard(doc)
		if not guard["allowed"]:
			return {"ok": False, "code": guard["reason_code"], "message": guard["message"], "guard": guard}
		roster = [{"member_user": m["member_user"], "full_name": m["full_name"], "designation": m["designation"], "committee_capacity": m["committee_role"],
			"appointment_reference": doc.current_appointment} for m in appointment.roster(doc.name)]
		started = lifecycle.start_proceeding(**prc.ref(doc.name), roster=roster, custody_reference=cstr(doc.manifest_handoff), owner_event_id=f"begin:{doc.name}",
			idempotency_key=prc.key(idempotency_key, "start"), actor=user)
		count = len(envelopes(doc))
		records.bump(doc, state="Opening", started_at=clock.now(), last_committed_event=started["event_id"], outcome="" if count else "No bids")
		return records.summary(doc, bids=count)

	return records.command("BeginOpening", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)


def _next_envelope(doc) -> dict[str, Any] | None:
	opened = {e.envelope_id for e in entries(doc.name)}
	return next((e for e in envelopes(doc) if e["envelope_id"] not in opened), None)


def _open(doc, envelope: dict[str, Any], key: str, user: str) -> dict[str, Any]:
	"""Reveal, render and number one envelope; or pause with the exact cause."""
	from kentender_procurement.proceedings.services import events

	revealed = custody.reveal(tender=doc.tender, envelope_id=envelope["envelope_id"], manifest_digest=doc.manifest_digest,
		roster_digest=appointment.roster_digest(doc.name), correlation_id=f"{doc.opening_id}-REV-{envelope['envelope_id']}")
	if revealed["outcome"] != custody.VERIFIED:
		if revealed.get("reason") == "package_mismatch":
			incident = incidents.ensure(doc, "Package mismatch", envelope_id=envelope["envelope_id"])
			pause(doc, "Package mismatch", fact=errors.message("BOP_PACKAGE_MISMATCH"), key=key, envelope_id=envelope["envelope_id"], incident=incident.incident_id)
			return {"ok": False, "code": "BOP_PACKAGE_MISMATCH", "message": errors.message("BOP_PACKAGE_MISMATCH"), "incident": incident.incident_id}
		incident = incidents.ensure(doc, "Credential unavailable", envelope_id=envelope["envelope_id"])
		message = errors.message("BOP_CREDENTIAL_UNAVAILABLE", started=True)
		pause(doc, "Credential unavailable", fact=message, key=key, envelope_id=envelope["envelope_id"], incident=incident.incident_id)
		return {"ok": False, "code": "BOP_CREDENTIAL_UNAVAILABLE", "message": message, "incident": incident.incident_id}
	number = len(entries(doc.name)) + 1
	entry_id = f"{doc.opening_id}-BID-{number:02d}"
	rendered = renderer.render_package(package=revealed["package"], envelope_id=envelope["envelope_id"], receipt_reference=envelope["receipt_reference"],
		correlation_id=entry_id)
	if rendered["outcome"] != renderer.VERIFIED:
		incident = incidents.ensure(doc, "Package unreadable", envelope_id=envelope["envelope_id"])
		pause(doc, "Package unreadable", fact=errors.message("BOP_PACKAGE_UNREADABLE"), key=key, envelope_id=envelope["envelope_id"], incident=incident.incident_id)
		return {"ok": False, "code": "BOP_PACKAGE_UNREADABLE", "message": errors.message("BOP_PACKAGE_UNREADABLE"), "incident": incident.incident_id}
	renders.save(entry_id, rendered["pdf"])
	facts = rendered["facts"]
	event = events.append_event(**prc.ref(doc.name), event_type="PackageRevealed", source="Owner", owner_event_id=f"reveal:{entry_id}",
		payload={"entry": entry_id, "receipt": envelope["receipt_reference"], "pages": rendered["page_count"], "render_digest": rendered["render_digest"]},
		note=f"Bid {number} opened", idempotency_key=prc.key(key, f"reveal:{entry_id}"), actor=user)
	records.insert(frappe.get_doc({
		"doctype": ENTRY, "entry_id": entry_id, "opening_case": doc.name, "entry_number": number, "envelope_id": envelope["envelope_id"],
		"receipt_reference": envelope["receipt_reference"], "submission_version": envelope["submission_version"], "package_digest": envelope["package_digest"],
		"render_digest": rendered["render_digest"], "page_count": rendered["page_count"], "price_page": rendered["price_page"],
		"change_pages": ",".join(str(p) for p in rendered["change_pages"]), "bidder_name": facts["tenderer_name"], "submitted_total": facts["submitted_total"],
		"currency": facts["currency"], "security_given": labels.security(facts["security_given"]), "revealed_at": clock.now(), "revealed_by": user,
		"status": "Opened", "proceeding_event": event["event_id"],
	}))
	doc.last_committed_event = event["event_id"]
	return {"ok": True, "entry": entry_id}


def _material_check(doc) -> dict[str, Any] | None:
	"""Before any material act: a missing member pauses the opening now."""
	absent = absent_members(doc)
	if not absent:
		return None
	return {"ok": False, "code": "BOP_MEMBER_ABSENT", "message": errors.message("BOP_MEMBER_ABSENT", started=True, name=absent[0]["full_name"])}


def open_next_tender(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_chair(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = _material_check(doc)
		if refused:
			return refused
		if any(e.status == "Opened" for e in entries(doc.name)):
			errors.fail("BOP_READOUT_INCOMPLETE")
		envelope = _next_envelope(doc)
		if envelope is None:
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "no_more_bids"})
		outcome = _open(doc, envelope, idempotency_key, user)
		records.bump(doc)
		return {**records.summary(doc), **outcome} if outcome["ok"] else {**outcome, "opening": doc.name, "state": doc.state, "record_version": cint(doc.record_version)}

	return records.command("OpenNextTender", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)


def retry_opening(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	"""§11 Retry opening: only after support records resolution; the same bid is opened again."""
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_chair(doc, user)
		records.check_version(doc, expected_version)
		row = open_pause(doc.name)
		if doc.state != "Interrupted" or not row or row.exception_class not in ("Package unreadable", "Package mismatch", "Credential unavailable"):
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		status = frappe.db.get_value(incidents.INCIDENT, {"opening_case": doc.name, "incident_id": row.incident}, "status")
		if status != "Resolved":
			return {"ok": False, "code": "BOP_OPENING_PROFILE_UNAVAILABLE", "message": "Retry opening is available when support marks the problem resolved.",
				"reason": "incident_not_resolved"}
		refused = _material_check(doc)
		if refused:
			return refused
		if not custody_participation.valid(doc):
			return {"ok": False, "code": "BOP_CREDENTIAL_UNAVAILABLE", "message": errors.message("BOP_CREDENTIAL_UNAVAILABLE", started=True)}
		resume(doc, idempotency_key, actor=user)
		envelope = next(e for e in envelopes(doc) if e["envelope_id"] == row.envelope_id)
		outcome = _open(doc, envelope, f"{idempotency_key}:retry", user)
		records.bump(doc)
		return {**records.summary(doc), **outcome} if outcome["ok"] else {**outcome, "opening": doc.name, "state": doc.state, "record_version": cint(doc.record_version)}

	return records.command("RetryOpening", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)


def resume_opening(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	"""§7 ResumeOpening from a pause without a package to retry (secure access
	restored, or a successor member now present)."""
	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_chair(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Interrupted":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		ready, reason = ceremony_ready(doc)
		if not ready:
			absent = absent_members(doc)
			code = "BOP_MEMBER_ABSENT" if absent else "BOP_CREDENTIAL_UNAVAILABLE"
			return {"ok": False, "code": code, "reason": reason,
				"message": errors.message(code, started=True, **({"name": absent[0]["full_name"]} if absent else {}))}
		resume(doc, idempotency_key, actor=user)
		records.bump(doc)
		return records.summary(doc)

	return records.command("ResumeOpening", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)
