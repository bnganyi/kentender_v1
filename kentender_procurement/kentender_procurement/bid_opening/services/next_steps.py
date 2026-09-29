# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The actor-specific next step and journey before Start (BOP-CHG-001 v0.10
§5 hand-off table, §8, §10.2, §10.3 WAIT and READY, §10.7; KT-STD-001 v1.10
§2.9, §3B). Wording is the boards' own (a1, a3, a5, c1–c3, c2b–c2d, n1, n2).
Computed on the server only; a technical reader never gets a turn or a fix."""

from __future__ import annotations

from typing import Any

from frappe.utils import get_datetime

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import (
	appointment, arrangements, availability, clock, guards, incidents, labels, not_held, people, presence,
)

STAGES = (("prepare", "Prepare opening"), ("open", "Open bids"), ("record", "Record opening"))
SUPPORT = guards.SUPPORT
SYSTEM = "System"
UNAVAILABLE_DECISION = "A Tender decision is needed. Cancellation after submissions close is not available in this version."
_COUNT = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def _ao_names() -> list[str]:
	return [people.full_name(u) for u in people.accounting_officers()]


def _timed_close(doc) -> dict[str, Any]:
	return ns.answer(ns.KIND_SCHEDULED, headline=f"Submissions close automatically at {labels.when(doc.effective_deadline)}.", holder=ns.holder(SYSTEM), stage="open")


def _join_answer(doc, now) -> dict[str, Any]:
	opens = arrangements.join_opens_at(doc.effective_deadline)
	if opens is not None and now < opens:
		return ns.answer(ns.KIND_SCHEDULED, headline=f"You can join from {labels.when(opens)}.", holder=ns.holder(SYSTEM), stage="open")
	return ns.answer(ns.KIND_YOUR_TURN, headline=f"Join opening for {doc.tender_reference}", stage="open", primary_action="join")


def _decision_item(doc):
	import frappe

	name = frappe.db.get_value(not_held.DECISION, {"opening_case": doc.name, "status": "Open"}, "name")
	return frappe.get_doc(not_held.DECISION, name) if name else None


def _chair_before_start(doc, member, now) -> dict[str, Any]:
	present = presence.present_members(doc.name)
	if member["member_user"] not in present:
		return _join_answer(doc, now)
	if now < get_datetime(doc.effective_deadline):
		return _timed_close(doc)
	refused = guards.start_guards(doc)
	closed = f"Submissions closed at {labels.time(doc.effective_deadline)} EAT."
	if not refused:
		count = len(appointment.roster(doc.name))
		return ns.answer(ns.KIND_YOUR_TURN, headline="Ready to start", sentence=f"All {_COUNT.get(count, count)} members have joined and submissions closed at "
			f"{labels.time(doc.effective_deadline)} EAT.", stage="open", primary_action="start")
	failed = [row for row in incidents.open_incidents(doc.name) if row.notification_state == "Failed"]
	if failed:
		blocker = ns.guard(False, reason_code="BOP_OPENING_PROFILE_UNAVAILABLE", headline="Bid opening isn’t available yet.",
			message="Support could not be notified. Try again.", figures={"incident": failed[0].incident_id},
			fixes=[ns.fix("Notify support", responsibility="Chair", kind=ns.FIX_COMMAND, fix_id="notify_support", target=failed[0].incident_id, primary=True),
				ns.fix("View problem details", responsibility=SUPPORT, kind=ns.FIX_FOCUS, fix_id="view_problem_details", target=failed[0].incident_id)])
		return ns.answer(ns.KIND_BLOCKED, headline="Bid opening isn’t available yet.", stage="open", blockers=[ns.blocker(blocker)])
	absent = [g for g in refused if g["reason_code"] == "BOP_MEMBER_ABSENT"]
	service = [g for g in refused if g["reason_code"] in ("BOP_OPENING_PROFILE_UNAVAILABLE", "BOP_CREDENTIAL_UNAVAILABLE", "BOP_ATTENDANCE_SERVICE_UNAVAILABLE",
		"BOP_CLOSE_MANIFEST_UNAVAILABLE")]
	if service:
		first = service[0]
		told = any(r.notification_state == "Delivered" for r in incidents.open_incidents(doc.name))
		sentence = "Opening access support has been told." if (told and first["reason_code"] == "BOP_OPENING_PROFILE_UNAVAILABLE") else "You can start once they have fixed it."
		return ns.answer(ns.KIND_WAITING, headline=first["message"], sentence=sentence, stage="open", holder=ns.holder(SUPPORT), blockers=[ns.blocker(g) for g in refused])
	if absent:
		names = [g["message"] for g in absent]
		member_names = [m["full_name"] for m in appointment.roster(doc.name) if m["member_user"] not in present]
		return ns.answer(ns.KIND_WAITING, headline=names[0], sentence=f"{closed} You can start once every appointed member has joined.", stage="open",
			holder=ns.holder("", member_names), blockers=[ns.blocker(g) for g in refused])
	return ns.answer(ns.KIND_WAITING, headline=refused[0]["message"], stage="open", holder=ns.holder(people.ACCOUNTING_OFFICER, _ao_names()),
		blockers=[ns.blocker(g) for g in refused])


def _member_before_start(doc, member, now) -> dict[str, Any]:
	if member["member_user"] not in presence.present_members(doc.name):
		return _join_answer(doc, now)
	if now < get_datetime(doc.effective_deadline):
		return _timed_close(doc)
	chair = appointment.chair(doc.name)
	return ns.answer(ns.KIND_WAITING, headline=f"Waiting for {chair['full_name']} to start the opening", stage="open", holder=ns.holder("Chair", [chair["full_name"]]))


def _ao_before_start(doc, now) -> dict[str, Any] | None:
	current_appointment = appointment.current(doc.name)
	if not current_appointment:
		return ns.answer(ns.KIND_YOUR_TURN, headline="Appoint opening committee", stage="prepare", primary_action="appoint")
	published = arrangements.current(doc.name)
	if not published:
		return ns.answer(ns.KIND_YOUR_TURN, headline="Publish how to attend", sentence=f"You appointed the committee on {labels.when(current_appointment.appointed_at)}. "
			"The opening cannot start until attendance details are published.", stage="prepare", primary_action="publish")
	if now >= get_datetime(doc.effective_deadline) and (incidents.open_incidents(doc.name) or not availability.attendance_channel_available()):
		return ns.answer(ns.KIND_YOUR_TURN, headline="The opening has not started; record what happened", stage="open", primary_action="record_not_held")
	return ns.answer(ns.KIND_DONE, headline=f"You published how to attend on {labels.when(published.published_at)}.", stage="prepare")


def answer_for(doc, user: str) -> dict[str, Any]:
	now = clock.now()
	technical = people.technical(user)
	member = appointment.member(doc.name, user)
	ao = people.holds(user, people.ACCOUNTING_OFFICER)
	candidates: list[dict[str, Any] | None] = []
	if doc.state == "Not held":
		item = _decision_item(doc)
		if item and ao:
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Decide what happens next", sentence="The opening did not take place.", stage="open",
				primary_action="tender_decision"))
		elif item:
			candidates.append(ns.answer(ns.KIND_WAITING, headline="The opening did not take place. Waiting for "
				f"{people.full_name(item.holder_user)} to decide what happens next.", stage="open", holder=ns.holder(people.ACCOUNTING_OFFICER, [people.full_name(item.holder_user)])))
		else:
			candidates.append(ns.answer(ns.KIND_DONE, headline="The opening did not take place.", sentence="The Tender was cancelled before the opening.", stage="open"))
	elif doc.state in ("Awaiting deadline", "Ready to open"):
		if ao:
			candidates.append(_ao_before_start(doc, now))
		if member and member["is_chair"]:
			candidates.append(_chair_before_start(doc, member, now))
		elif member:
			candidates.append(_member_before_start(doc, member, now))
		if not appointment.current(doc.name) and not ao and (people.holds(user, people.HEAD_OF_PROCUREMENT) or technical):
			names = _ao_names()
			candidates.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {', '.join(names) or 'the Accounting Officer'} to appoint the opening committee",
				stage="prepare", holder=ns.holder(people.ACCOUNTING_OFFICER, names)))
	result = ns.choose(*candidates)
	reader = ns.not_involved(result.get("stage", ""))
	return ns.for_viewer(result, technical=technical, reader=reader)


def journey_for(doc) -> dict[str, Any]:
	prepared = bool(appointment.current(doc.name) and arrangements.current(doc.name))
	if doc.state == "Not held":
		return ns.journey(STAGES, current="open", blocked=True, holder_display=", ".join(_ao_names()))
	if not prepared:
		return ns.journey(STAGES, current="prepare", holder_display=", ".join(_ao_names()))
	now = clock.now()
	if now < get_datetime(doc.effective_deadline):
		return ns.journey(STAGES, current="open", holder_display=f"Opens {labels.when(doc.effective_deadline)}")
	chair = appointment.chair(doc.name)
	return ns.journey(STAGES, current="open", holder_display=chair["full_name"] if chair else "")
