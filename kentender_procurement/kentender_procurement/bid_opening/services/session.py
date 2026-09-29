# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The ceremony as its readers see it (BOP-CHG-001 v0.10 §10.3; boards c4–c13b,
c10, c12): the bids opened so far, the register preview, the chronology,
requests and comments, and why a paused opening stopped.

Only after Start, and only to ceremony and oversight readers: a technical
reader sees no bid facts (§6). The register's "Recorded at" is the trusted
recorder confirmation; a reported speech time is shown separately and
attributed to the recorder (§10.3)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_opening.services import appointment, ceremony, finish, incidents, labels, people, presence, records

WHAT = {
	"ProceedingStarted": "Started the opening", "PackageRevealed": None, "ReadoutConfirmed": None, "Intervention": None, "MemberAccount": "Recorded their own differing account",
	"CommentForEvaluation": None, "OpeningPaused": None, "OpeningResumed": "The opening continued from the last recorded step", "AttendanceDeparture": "Left the opening",
	"AttendanceArrival": "Joined the opening", "ProceedingEnded": "Ended the opening", "NoBidsOutcome": "Recorded that there were no bids to open",
}


def _entry_facts(e) -> dict[str, Any]:
	return {"entry": e.entry_id, "number": e.entry_number, "receipt": e.receipt_reference, "tenderer": e.bidder_name,
		"submitted_total": labels.money(e.submitted_total, e.currency), "security_given": e.security_given or "", "page_count": cint(e.page_count),
		"price_page": cint(e.price_page), "designated_pages": e.designated_pages or "", "read_aloud": labels.read_aloud(e), "status": e.status,
		"opened_label": labels.time_seconds(e.revealed_at), "recorded_label": labels.time_seconds(e.readout_confirmed_at),
		"speaker": people.full_name(e.readout_speaker) if e.readout_speaker else "",
		"reported_speech": f"Reported speech time: {labels.time_seconds(e.reported_speech_at)} — recorded by {people.full_name(e.readout_confirmed_by)}"
			if e.reported_speech_at else ""}


def chronology(case: str) -> list[dict[str, str]]:
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	rows = frappe.get_all("Proceeding Event", filters={"proceeding": proceeding, "pre_session": 0}, fields=["event_type", "recorded_at", "actor", "note",
		"reported_at", "reported_by"], order_by="sequence asc")
	out = []
	for r in rows:
		if r.event_type in ("ProceedingCreated", "CustodyParticipation", "ClosedManifestReference"):
			continue
		who = people.full_name(r.actor) if r.actor else "System"
		what = WHAT.get(r.event_type) or r.note or r.event_type
		out.append({"time": labels.time_seconds(r.reported_at or r.recorded_at), "who": who, "what": what,
			"reported": f"reported time, recorded by {people.full_name(r.reported_by)}" if r.reported_at and r.reported_by else ""})
	return out


def accounts(case: str) -> list[dict[str, Any]]:
	"""Members' own differing accounts (board c8), each with whether the
	recorder has responded to it (board c8b)."""
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	if not proceeding:
		return []
	rows = frappe.get_all("Proceeding Event", filters={"proceeding": proceeding, "event_type": "MemberAccount"}, fields=["event_id", "actor", "note", "recorded_at"],
		order_by="sequence asc")
	answered = set(frappe.get_all("Proceeding Event", filters={"proceeding": proceeding, "event_type": "Intervention", "linked_event": ("in", [r.event_id for r in rows])},
		pluck="linked_event")) if rows else set()
	return [{"event_id": r.event_id, "member_user": r.actor, "member": people.full_name(r.actor), "account": r.note, "time_label": labels.time_seconds(r.recorded_at),
		"responded": r.event_id in answered} for r in rows]


def view(doc, user: str) -> dict[str, Any] | None:
	if doc.state in ("Awaiting deadline", "Ready to open", "Not held") or people.technical(user):
		return None
	opened = ceremony.entries(doc.name)
	pause = ceremony.open_pause(doc.name)
	pause_view = None
	if pause:
		incident = frappe.db.get_value(incidents.INCIDENT, {"opening_case": doc.name, "incident_id": pause.incident}, ["incident_id", "status", "resolved_at", "raised_at"],
			as_dict=True) if pause.incident else None
		last = ceremony.last_committed(doc.name)
		pause_view = {"class": pause.exception_class, "message": pause.observed_fact, "member": pause.speaker_name, "since_label": labels.time(pause.recorded_at),
			"receipt": next((e.receipt_reference for e in opened if e.envelope_id == pause.envelope_id), "") or pause.envelope_id,
			"incident": dict(incident) if incident else None, "last_step": {"what": (last or {}).get("note") or "", "at_label": labels.time_seconds((last or {}).get("recorded_at"))}}
	requests = frappe.get_all(ceremony.EXCEPTION, filters={"opening_case": doc.name, "exception_class": ("in", ("Repeat request", "Procedural comment", "Comment for Evaluation"))},
		fields=["exception_id", "exception_class", "entry", "speaker_name", "observed_fact", "response", "outcome", "recorded_at", "recorded_by"], order_by="recorded_at asc")
	return {
		"accounts": accounts(doc.name),
		"current_bids": len(ceremony.envelopes(doc)),
		"opened": [_entry_facts(e) for e in opened],
		"awaiting_readout": next((_entry_facts(e) for e in opened if e.status == "Opened"), None),
		"register": [{**r, "recorded_label": labels.time_seconds(r["recorded_at"])} for r in finish.register_rows(doc.name)],
		"requests": [{**r, "recorded_label": labels.time_seconds(r["recorded_at"]), "recorded_by": people.full_name(r["recorded_by"]) if r["recorded_by"] else ""} for r in requests],
		"chronology": chronology(doc.name),
		"pause": pause_view,
		"present": {m["member_user"]: labels.time(t) for m in appointment.roster(doc.name) for u, t in presence.present_members(doc.name).items() if u == m["member_user"]},
	}
