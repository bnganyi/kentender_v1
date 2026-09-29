# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening rows for the shared My Work queue (BOP-CHG-001 v0.10 §5 hand-off
table; KT-STD-001 §3B.4; plan D11). Registered on `kt_my_work_providers`.

Every row is derived from the case's actual state, so it clears exactly on
its business transition and never on reading:

- Accounting Officer: "Appoint opening committee for …" until the appointment
  commits; "Publish how to attend for …" until publication; "Decide what
  happens next for …" while the Not held decision item is open;
- each appointed member: "Join opening for …" until their own join;
- the chair: "Start opening for … at …", upcoming until the box closes;
- waiting: the Head of Procurement Function's "Waiting for … to appoint the
  opening committee".

Opening access support incidents are never My Work (they are in-app
notifications). Technical readers get nothing (core skips them)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import appointment, arrangements, clock, labels, not_held, people, presence, records

PAGE = "tenders"


def _row(doc, *, key: str, title: str, status: str, action_label: str, role: str, since=None, holder: dict[str, Any] | None = None) -> dict[str, Any]:
	row = {
		"task_id": f"{doc.name}:{key}", "task_type": f"bid_opening.{key}", "title": title, "reference": doc.tender_reference, "module": "Bid Opening",
		"stage": "Bid opening", "fiscal_year": "", "organisation_unit": "", "assignment": role, "status": status, "received_at": cstr(since or ""), "due_at": "",
		"action_label": action_label, "route": [PAGE, doc.tender_reference, "opening"], "route_options": {}, "concurrency_token": "", "can_claim": False,
		"can_open": True, "comment": "", "since": ns.since(since, labels.when(since)) if since else None,
	}
	if holder:
		row["holder"] = holder
	return row


def my_work_rows(user: str) -> dict[str, list[dict[str, Any]]]:
	out: dict[str, list[dict[str, Any]]] = {"assigned": [], "claimable": [], "waiting": []}
	ao = people.holds(user, people.ACCOUNTING_OFFICER)
	hopf = people.holds(user, people.HEAD_OF_PROCUREMENT)
	now = clock.now()
	for row in frappe.get_all(records.CASE, filters={"state": ("in", ("Awaiting deadline", "Ready to open", "Not held", "Interrupted", "Readout complete"))},
			fields=["name"], limit_page_length=0):
		doc = frappe.get_doc(records.CASE, row.name)
		ref = doc.tender_reference
		current_appointment = appointment.current(doc.name)
		if doc.state in ("Interrupted", "Readout complete"):
			out["assigned"] += _ceremony_rows(doc, user, ao)
			continue
		if doc.state == "Not held":
			item = frappe.db.get_value(not_held.DECISION, {"opening_case": doc.name, "status": "Open", "holder_user": user}, ["name", "created_at"], as_dict=True)
			if item and ao:
				out["assigned"].append(_row(doc, key="decide", title=f"Decide what happens next for {ref}", status="Assigned", action_label="Decide what happens next",
					role=people.ACCOUNTING_OFFICER, since=item.created_at))
			continue
		if ao and not current_appointment:
			out["assigned"].append(_row(doc, key="appoint", title=f"Appoint opening committee for {ref}", status="Assigned", action_label="Appoint committee",
				role=people.ACCOUNTING_OFFICER, since=doc.creation))
		elif ao and not arrangements.current(doc.name):
			out["assigned"].append(_row(doc, key="publish", title=f"Publish how to attend for {ref}", status="Assigned", action_label="Publish how to attend",
				role=people.ACCOUNTING_OFFICER, since=current_appointment.appointed_at))
		if not current_appointment and hopf and not ao:
			names = [people.full_name(u) for u in people.accounting_officers()]
			out["waiting"].append(_row(doc, key="await-appointment", title=f"Waiting for {', '.join(names) or 'the Accounting Officer'} to appoint the opening committee",
				status="Waiting", action_label="View", role=people.HEAD_OF_PROCUREMENT, since=doc.creation, holder=ns.holder(people.ACCOUNTING_OFFICER, names)))
		member = appointment.member(doc.name, user) if current_appointment else None
		if not member:
			continue
		if user not in presence.present_members(doc.name):
			out["assigned"].append(_row(doc, key="join", title=f"Join opening for {ref}", status="Assigned", action_label="Join opening", role=member["committee_role"],
				since=current_appointment.appointed_at))
		if member["is_chair"]:
			upcoming = now < get_datetime(doc.effective_deadline)
			out["assigned"].append(_row(doc, key="start", title=f"Start opening for {ref} at {labels.when(doc.effective_deadline)}",
				status="Upcoming" if upcoming else "Assigned", action_label="Start opening", role=member["committee_role"], since=current_appointment.appointed_at))
	return out


def _ceremony_rows(doc, user: str, ao: bool) -> list[dict[str, Any]]:
	"""§5: the paused-opening decision, a replacement, and the recorder's opening record."""
	from kentender_procurement.bid_opening.services import ceremony

	ref = doc.tender_reference
	rows = []
	if doc.state == "Interrupted" and ao:
		# Any current Accounting Officer may take the paused-opening decision (§5: "AO Amina Hassan").
		item = frappe.db.get_value(not_held.DECISION, {"opening_case": doc.name, "kind": "Paused opening", "status": "Open"}, ["created_at"], as_dict=True)
		if item:
			rows.append(_row(doc, key="paused", title=f"Decide how to proceed with the paused opening for {ref}", status="Assigned",
				action_label="Decide how to proceed", role=people.ACCOUNTING_OFFICER, since=item.created_at))
		pause = ceremony.open_pause(doc.name)
		if pause and pause.exception_class == "Member absent":
			rows.append(_row(doc, key="replacement", title=f"Appoint replacement for {ref}", status="Assigned", action_label="Appoint replacement",
				role=people.ACCOUNTING_OFFICER, since=pause.recorded_at))
	member = appointment.member(doc.name, user)
	if doc.state == "Interrupted" and member and user not in presence.present_members(doc.name):
		rows.append(_row(doc, key="join", title=f"Join opening for {ref}", status="Assigned", action_label="Join opening", role=member["committee_role"],
			since=doc.started_at))
	if doc.state == "Readout complete" and member and member["is_recorder"]:
		rows.append(_row(doc, key="prepare-record", title=f"Prepare opening record for {ref}", status="Assigned", action_label="Prepare opening record",
			role=member["committee_role"], since=doc.ended_at))
	return rows
