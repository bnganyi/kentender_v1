# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The public opening page (BOP-CHG-001 v0.10 §10.5; boards p0–p6; plan D10).

Anyone may read it for a published Tender: when and how to attend, then each
bid's facts only after the recorder has confirmed what was read aloud (the
live readout), and after completion the register request for a verified
submitting supplier. Before Start nothing here states or implies the bid
count or a bidder identity. A signed-in visitor joins through the published
attendance channel; saying whom they represent is not proof of a bid.
Reading creates no event."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_opening.services import (
	arrangements, availability, ceremony, clock, errors, finish, labels, prc, records, register_copy,
)

REQUEST = register_copy.REQUEST
LIVE = ("Opening", "Interrupted")
DONE = ("Readout complete", "Awaiting attestations", "Opening complete")


def _tender(tender_reference: str) -> tuple[str, dict[str, Any]]:
	from kentender_procurement.tenders.services import opening_seam

	name = frappe.db.get_value("Tender", {"tender_reference": cstr(tender_reference).strip()}, "name")
	facts = opening_seam.tender_facts(name) if name else None
	if not facts or not facts["published"]:
		raise frappe.DoesNotExistError("Not found")
	return name, facts


def _entity() -> str:
	return cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name"))


def _organisation(user: str) -> str:
	"""The legal name of the supplier organisation a signed-in visitor acts for,
	through kentender_core's Supplier Accounts contract."""
	from kentender_core.services import supplier_account_contract as contract

	provider = contract.provider()
	if provider is None:
		return ""
	for row in provider.active_assignments(user=user):
		org = provider.organisation(organisation_id=row["organisation_id"]) if row.get("active") else None
		if org:
			return cstr(org["legal_name"])
	return ""


def _joined(case: str, proceeding: str, user: str) -> str:
	if not proceeding or not user or user == "Guest":
		return ""
	from kentender_procurement.proceedings.services import attendance

	row = next((r for r in attendance.present(proceeding) if r["user"] == user), None)
	return labels.time(row["occurred_at"]) if row else ""


def phase(doc, now) -> str:
	"""Which public board applies: p0 (no details yet), p1a (before join opens),
	p1 (join open), p2 (in session), p3–p6 (after the readout), or the two
	terminal outcomes."""
	published = arrangements.current(doc.name)
	if doc.state == "Not held":
		return "not-held"
	if doc.state == "Cancelled after start":
		return "cancelled"
	if doc.state in LIVE:
		return "in-session"
	if doc.state in DONE:
		return "complete" if doc.state == "Opening complete" else "ended"
	if not published:
		return "details-coming"
	return "join" if now >= get_datetime(published.join_opens_at) else "before-join"


def get_public_opening(*, tender_reference: str, user: str) -> dict[str, Any]:
	tender, facts = _tender(tender_reference)
	case = records.case_for(tender)
	now = clock.now()
	out: dict[str, Any] = {
		"tender": {"reference": facts["tender_reference"], "title": facts["title"], "entity": _entity(), "opening_label": labels.when(facts["opening_datetime"])},
		"phase": "details-coming", "status": "", "arrangements": {"published": False, "message": arrangements.COMING_SOON}, "joined_label": "", "can_join": False,
		"readout": [], "repeats": [], "register": {"state": "unavailable", "message": ""}, "signed_in": bool(user and user != "Guest"),
	}
	if not case:
		return out
	doc = frappe.get_doc(records.CASE, case)
	out["phase"] = phase(doc, now)
	out["status"] = {"in-session": "In session", "ended": "Opening ended", "complete": "Opening complete", "not-held": "Did not take place",
		"cancelled": "Ended — Tender cancelled"}.get(out["phase"], "")
	out["arrangements"] = arrangements.public_projection(case)
	out["joined_label"] = _joined(case, doc.proceeding, user)
	out["can_join"] = out["phase"] in ("join", "in-session") and out["signed_in"] and not out["joined_label"] and availability.attendance_channel_available()
	# the live readout: only bids whose readout the recorder has confirmed
	out["readout"] = [{"number": r["number"], "tenderer": r["tenderer"], "submitted_total": r["submitted_total"], "security_given": r["security_given"],
		"recorded_label": labels.time_seconds(r["recorded_at"])} for r in finish.register_rows(doc.name)]
	out["repeats"] = [f"At {labels.time(at)} a figure was repeated at an attendee’s request. The bid is unchanged."
		for at in frappe.get_all(ceremony.EXCEPTION, filters={"opening_case": doc.name, "exception_class": "Repeat request"}, pluck="recorded_at",
			order_by="recorded_at asc")] if out["readout"] else []
	out["register"] = _register(doc, user)
	return out


def _register(doc, user: str) -> dict[str, Any]:
	"""Boards p2–p6: the register request, for a verified submitting supplier only."""
	if doc.state != "Opening complete":
		return {"state": "after-completion", "message": "After the opening record is complete, a supplier who submitted a bid can request the opening register."}
	if not user or user == "Guest" or not register_copy.submitter_receipt(doc, user):
		return {"state": "not-a-submitter", "message": "Only a supplier who submitted a bid for this Tender can request the opening register. The facts read aloud are shown above."}
	row = frappe.db.get_value(REQUEST, {"opening_case": doc.name, "requester_user": user, "status": ("in", ("Pending", "Ready", "Delivered"))},
		["request_id", "status", "requested_at"], as_dict=True)
	if not row:
		return {"state": "can-request", "message": "The opening record is complete. As the representative of a supplier who submitted a bid, you can request a copy of the opening register."}
	if row.status == "Pending":
		return {"state": "preparing", "requested_label": labels.time(row.requested_at),
			"message": f"You requested it at {labels.time(row.requested_at)}. We will notify you when it is ready to download."}
	count = len(finish.register_rows(doc.name))
	return {"state": "ready", "message": f"Your copy of the opening register is ready. It lists {'the one bid' if count == 1 else f'the {count} bids'} opened, as read aloud."}


def join_public_opening(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""Board p1 "Join public opening": the signed-in visitor's arrival through
	the published attendance channel, recorded in the Proceedings attendance."""
	from kentender_procurement.proceedings.services import attendance

	if not user or user == "Guest":
		raise frappe.PermissionError("Sign in to join the opening.")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		now = clock.now()
		if phase(doc, now) not in ("join", "in-session"):
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "join_not_open"})
		if not availability.attendance_channel_available():
			return {"ok": False, "code": "BOP_ATTENDANCE_SERVICE_UNAVAILABLE", "message": "The public attendance service is unavailable."}
		if _joined(doc.name, doc.proceeding, user):
			return records.summary(doc, joined=False)
		organisation = _organisation(user)
		attendance.record_attendance(**prc.ref(doc.name), person_name=cstr(frappe.db.get_value("User", user, "full_name") or user), user=user,
			capacity="Tenderer representative" if organisation else "Public observer", movement="Arrival", represented_tenderer=organisation,
			idempotency_key=prc.key(idempotency_key, "public-join"), actor=user)
		records.bump(doc)
		return records.summary(doc, joined=True)

	return records.command("JoinPublicOpening", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)
