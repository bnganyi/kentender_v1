# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""GetOpening (BOP-CHG-001 v0.10 §6, §7 GetOpening; binding row: role-filtered
read, no Proceedings mutation; BOP-N01, BOP-A01, BOP-A13).

Readers: the Accounting Officer, the Head of Procurement Function, the
Procurement Officer, the Auditor, the appointed members and technical
readers (health only, KT-STD-001 §3A.6). Anyone else gets Not found, and a
guessed route confers nothing. Before Start nothing here states or implies
the bid count or a bidder identity: the closed box appears only as
"received", identically for an empty and a nonempty box. Reading creates no
event."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, get_datetime

from kentender_procurement.bid_opening.services import (
	appointment, arrangements, clock, guards, incidents, labels, next_steps, not_held, people, prc_owner, presence, records, session,
)

READER_ROLES = (people.ACCOUNTING_OFFICER, people.HEAD_OF_PROCUREMENT, people.PROCUREMENT_OFFICER, people.AUDITOR)


def can_read(case: str, user: str) -> bool:
	return people.technical(user) or bool(appointment.member(case, user)) or any(people.holds(user, r) for r in READER_ROLES)


def _attendees(case: str) -> list[dict[str, Any]]:
	from kentender_procurement.proceedings.services import attendance

	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	if not proceeding:
		return []
	members = {m["member_user"] for m in appointment.roster(case)}
	return [{"person_name": r["person_name"], "represents": r["represented_tenderer"] or "", "capacity": r["capacity"], "joined_label": labels.time(r["occurred_at"])}
		for r in attendance.present(proceeding) if r["user"] not in members]


def status_line(doc, answer: dict[str, Any]) -> dict[str, str]:
	"""The page head's second line (boards a1–h5): the words before the status,
	the status itself and its tone. Before Start it never implies a count."""
	from kentender_procurement.bid_opening.services import ceremony

	closed = clock.now() >= get_datetime(doc.effective_deadline)
	if doc.state in ("Awaiting deadline", "Ready to open"):
		if answer.get("primary_action") == "record_not_held":
			return {"text": f"Scheduled {labels.when(doc.effective_deadline)}", "label": "Not started", "tone": "is-attention", "since": ""}
		return {"text": f"Submissions {'closed' if closed else 'close'} {labels.when(doc.effective_deadline)}", "label": "", "tone": "", "since": ""}
	if doc.state == "Opening":
		return {"text": "", "label": "In session", "tone": "is-live", "since": f"since {labels.time_seconds(doc.started_at)} EAT"}
	if doc.state == "Interrupted":
		pause = ceremony.open_pause(doc.name)
		return {"text": "", "label": "Paused", "tone": "is-attention", "since": f"since {labels.time(pause.recorded_at)} EAT" if pause else ""}
	if doc.state == "Cancelled after start":
		return {"text": "", "label": "Ended — Tender cancelled", "tone": "is-critical", "since": ""}
	if doc.state == "Not held":
		return {"text": "", "label": "Did not take place", "tone": "is-critical", "since": ""}
	if doc.state == "Readout complete":
		return {"text": "", "label": f"Opening ended {labels.time(doc.ended_at)} EAT", "tone": "is-live", "since": ""}
	if doc.state == "Awaiting attestations":
		number = cint(frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.proceeding, "state": ("in", ("Frozen", "Finalized"))}, "version_number",
			order_by="version_number desc"))
		return {"text": "" if number > 1 else f"Version {number}", "label": f"Version {number}" if number > 1 else "", "tone": "is-attention", "since": ""}
	return {"text": "", "label": "Complete", "tone": "is-live", "since": ""}


def get_opening(*, tender: str, user: str) -> dict[str, Any]:
	case = records.case_for(tender)
	if not case or not can_read(case, user):
		raise frappe.DoesNotExistError("Not found")
	doc = frappe.get_doc(records.CASE, case)
	technical = people.technical(user)
	member = appointment.member(case, user)
	ao = people.holds(user, people.ACCOUNTING_OFFICER)
	current_appointment = appointment.current(case)
	present = presence.present_members(case)
	published = arrangements.public_projection(case)
	guard = guards.start_guard(doc) if doc.state == "Ready to open" or (doc.state == "Awaiting deadline" and clock.now() >= get_datetime(doc.effective_deadline)) else None
	item = next_steps._decision_item(doc)
	answer = next_steps.answer_for(doc, user)
	out: dict[str, Any] = {
		"opening": {"opening_id": doc.opening_id, "state": doc.state, "record_version": cint(doc.record_version), "tender": doc.tender,
			"tender_reference": doc.tender_reference, "title": doc.tender_title, "deadline": str(doc.effective_deadline), "deadline_label": labels.when(doc.effective_deadline),
			"closed": clock.now() >= get_datetime(doc.effective_deadline), "box_received": bool(doc.manifest_digest), "status": status_line(doc, answer)},
		"next_step": answer,
		"journey": next_steps.journey_for(doc),
		"committee": {
			"appointed": bool(current_appointment),
			"appointed_label": labels.when(current_appointment.appointed_at) if current_appointment else "",
			"appointed_by": people.full_name(current_appointment.appointed_by) if current_appointment else "",
			"members": [{**m, "present": m["member_user"] in present, "joined_label": labels.time(present.get(m["member_user"]))} for m in appointment.roster(case)],
			"history": [{"version": a.version_number, "appointed_label": labels.when(a.appointed_at), "appointed_by": people.full_name(a.appointed_by), "status": a.status}
				for a in frappe.get_all(appointment.APPOINTMENT, filters={"opening_case": case}, fields=["version_number", "appointed_at", "appointed_by", "status"],
					order_by="version_number asc")],
		},
		"arrangements": published,
		"candidates": appointment.candidates(doc.tender) if ao and doc.state in ("Awaiting deadline", "Ready to open", "Interrupted") else [],
		"attendees": [] if technical else _attendees(case),
		"start_guard": guard,
		"incidents": [{"incident_id": r.incident_id, "type": r.incident_type, "holder": guards.SUPPORT, "notification_state": r.notification_state,
			"notified_label": labels.time_seconds(r.last_notified_at)} for r in incidents.open_incidents(case)],
		"decision": {"kind": item.kind, "reason": item.reason, "holder": people.full_name(item.holder_user), "unavailable_text": next_steps.UNAVAILABLE_DECISION,
			"recorded_label": labels.when(item.created_at)}
			if item and (ao or technical) else None,
		"ceremony": session.view(doc, user),
		"record": record_view(doc, user),
		"technical_status": {"message": "You can see technical status for this opening. Bids, the register and the opening record are not shown to administrators.",
			"state": doc.state, "completed_label": labels.when(doc.completed_at), "incidents": frappe.db.count(incidents.INCIDENT, {"opening_case": case})} if technical else None,
		"cancellation": {"message": "Opening ended by Tender cancellation", "note": "What happened up to the cancellation is kept as a partial record. There is no opening "
			"record to sign and nothing is passed to Evaluation."} if doc.state == "Cancelled after start" else None,
		"viewer": {"is_member": bool(member), "is_chair": bool(member and member["is_chair"]), "is_recorder": bool(member and member["is_recorder"]),
			"is_accounting_officer": ao, "technical": technical},
	}
	return out


def record_view(doc, user: str) -> dict[str, Any] | None:
	"""Boards r1–r6, h1, h2, h4, h5: the draft (recorder only, before freezing),
	the versions, this member's targets, everyone's signature status, the
	completion and the corrections. Never for a technical reader."""
	from kentender_procurement.bid_opening.services import record, signing

	if doc.state not in ("Readout complete", "Awaiting attestations", "Opening complete") or people.technical(user):
		return None
	member = appointment.member(doc.name, user)
	out: dict[str, Any] = {"draft": None, "versions": [], "mine": [], "signatures": [], "completion": None, "corrections": []}
	if doc.state == "Readout complete":
		if member and member["is_recorder"]:
			out["draft"] = record.draft(doc)
		return out
	versions = frappe.get_all("Proceeding Minutes Version", filters={"proceeding": doc.proceeding}, fields=["minutes_version_id", "version_number", "state",
		"page_count", "frozen_at", "frozen_by", "supersede_reason"], order_by="version_number asc")
	out["versions"] = [{**v, "frozen_label": labels.when(v.frozen_at), "frozen_by": people.full_name(v.frozen_by) if v.frozen_by else ""} for v in versions]
	version, mine = signing.my_targets(doc, user)
	out["mine"] = mine
	for m in record.participants(doc.name):
		proofs = frappe.get_all("Proceeding Attestation", filters={"minutes_version": version, "member_user": m["member_user"], "satisfies_current": 1},
			fields=["recorded_at"], order_by="recorded_at desc")
		required = frappe.db.count("Proceeding Minutes Target", {"parent": version, "required_member": m["member_user"]})
		out["signatures"].append({"member": m["full_name"], "role": m["committee_capacity"], "signed": bool(required) and len(proofs) >= required,
			"signed_label": labels.time(proofs[0].recorded_at) if proofs and len(proofs) >= required else ""})
	if doc.state == "Opening complete":
		out["completion"] = {"completed_label": labels.when(doc.completed_at), "bids_opened": frappe.db.count("Opening Entry", {"opening_case": doc.name}),
			"evaluation_reference": doc.evaluation_handoff or "", "no_bids": doc.outcome == "No bids"}
		out["corrections"] = [{**s, "added_label": labels.time(s.recorded_at), "author": people.full_name(s.author)} for s in frappe.get_all("Proceeding Supplement",
			filters={"proceeding": doc.proceeding}, fields=["supplement_id", "kind", "correct_information", "reason", "author", "recorded_at"], order_by="recorded_at asc")]
	return out
