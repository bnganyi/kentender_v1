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
			holder=ns.holder("Committee member", member_names), blockers=[ns.blocker(g) for g in refused])
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


def _ceremony(doc, user: str, member, ao: bool) -> list[dict[str, Any] | None]:
	"""Boards c4–c13b, c10–c11e, z1 (BOP-CHG-001 v0.10 §10.3)."""
	import frappe

	from kentender_procurement.bid_opening.services import ceremony

	out: list[dict[str, Any] | None] = []
	chair = appointment.chair(doc.name)
	recorder = appointment.recorder(doc.name)
	ao_names = _ao_names()
	ao_display = ", ".join(ao_names) or "the Accounting Officer"
	if doc.state == "Opening":
		from kentender_procurement.bid_opening.services import session

		entries = ceremony.entries(doc.name)
		awaiting = next((e for e in entries if e.status == "Opened"), None)
		remaining = len(ceremony.envelopes(doc)) - len(entries)
		unanswered = next((a for a in session.accounts(doc.name) if not a["responded"]), None)
		if member and member["is_recorder"] and unanswered and not awaiting:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Record the response to {unanswered['member']}’s account", stage="open",
				primary_action="respond_account"))
		if member and member["is_chair"]:
			if doc.outcome == "No bids":
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="No bids to open", sentence=f"Submissions closed at {labels.time(doc.effective_deadline)} EAT "
					"with no current bids.", stage="open", primary_action="end_no_bids"))
			elif awaiting and not member["is_recorder"]:
				out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {recorder['full_name']} to record what was read aloud", stage="open",
					holder=ns.holder("Recorder", [recorder["full_name"]])))
			elif not awaiting and remaining > 0:
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Open the first bid" if not entries else "Open the next bid", stage="open", primary_action="open_next"))
			elif not awaiting:
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="End the opening", sentence="Every bid has been read aloud and recorded, and the pages for signing "
					"are chosen.", stage="open", primary_action="end"))
		if member and member["is_recorder"] and awaiting:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record what was read aloud", stage="open", primary_action="record_readout"))
		if member and not member["is_chair"] and not member["is_recorder"]:
			if awaiting:
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Read these details aloud", sentence=f"{recorder['full_name']} will record what you read. "
					"You do not need to confirm it.", stage="open", primary_action="read_aloud"))
			else:
				out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {chair['full_name']} to continue the opening", stage="open",
					holder=ns.holder("Chair", [chair["full_name"]])))
	elif doc.state == "Interrupted":
		pause = ceremony.open_pause(doc.name)
		if pause and pause.exception_class == "Member absent":
			absent = [m for m in ceremony.absent_members(doc)]
			name = absent[0]["full_name"] if absent else pause.speaker_name
			if member and absent and member["member_user"] == absent[0]["member_user"]:
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Join opening for {doc.tender_reference}", sentence="The opening is paused until you rejoin.",
					stage="open", primary_action="join"))
			elif member:
				out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {name} to rejoin or for {ao_display} to appoint a replacement",
					sentence=f"Opening is paused because {name} is not present. {name} left at {labels.time(pause.recorded_at)}.", stage="open",
					holder=ns.holder("Committee member", [name, *ao_names])))
			if ao:
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Appoint replacement for {doc.tender_reference}", sentence=f"Opening is paused because {name} is not "
					"present. Appoint a replacement only if they cannot return.", stage="open", primary_action="appoint_replacement"))
		elif pause:
			incident = frappe.db.get_value(incidents.INCIDENT, {"opening_case": doc.name, "incident_id": pause.incident}, ["status", "resolved_at"], as_dict=True) \
				if pause.incident else None
			status = (incident or {}).get("status")
			problem = ns.fix("View problem details", responsibility=SUPPORT, kind=ns.FIX_FOCUS, fix_id="view_problem_details", target=pause.incident)
			if member and member["is_chair"]:
				if status == "Resolved":
					out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Retry opening", sentence=f"Opening access support resolved the problem at "
						f"{labels.time(incident.resolved_at)}. The same bid will be opened again.", stage="open", primary_action="retry"))
				elif status == "Unresolved":
					out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {ao_display} to resolve the paused opening",
						sentence=f"Opening access support could not fix the problem. {ao_display} will decide how to proceed.", stage="open",
						holder=ns.holder(people.ACCOUNTING_OFFICER, ao_names)))
				else:
					blocker = ns.guard(False, reason_code={"Package unreadable": "BOP_PACKAGE_UNREADABLE", "Package mismatch": "BOP_PACKAGE_MISMATCH"}.get(
						pause.exception_class, "BOP_CREDENTIAL_UNAVAILABLE"), message=pause.observed_fact, fixes=[problem])
					out.append(ns.answer(ns.KIND_BLOCKED, headline=pause.observed_fact, stage="open", blockers=[ns.blocker(blocker)]))
			elif member:
				out.append(ns.answer(ns.KIND_WAITING, headline=pause.observed_fact, stage="open", holder=ns.holder(SUPPORT)))
			if ao and status == "Unresolved":
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Decide how to proceed with the paused opening", sentence="Opening access support could not fix the "
					"problem. This stays in your work until the opening resumes or a Tender decision is recorded.", stage="open", primary_action="tender_decision"))
	elif doc.state == "Readout complete":
		if member and member["is_recorder"]:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Prepare opening record", sentence=f"The opening ended at {labels.time(doc.ended_at)}. The draft is "
				"built from the register, attendance and what happened in the session.", stage="record", primary_action="prepare_record"))
		elif member:
			out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {recorder['full_name']} to prepare the opening record", stage="record",
				holder=ns.holder("Recorder", [recorder["full_name"]])))
	elif doc.state == "Awaiting attestations":
		out.append(_signing_answer(doc, user))
	elif doc.state == "Opening complete":
		out.append(_completed_answer(doc, user, member, ao))
	return out


def _signing_answer(doc, user: str) -> dict[str, Any] | None:
	"""Boards r3, r4, r5."""
	import frappe

	from kentender_procurement.bid_opening.services import signing

	version, mine = signing.my_targets(doc, user)
	if not mine:
		return None
	number = frappe.db.get_value("Proceeding Minutes Version", version, "version_number")
	unsigned = [t for t in mine if not t["signed"]]
	if unsigned:
		older = frappe.db.exists("Proceeding Attestation", {"proceeding": doc.proceeding, "member_user": user, "minutes_version": ("!=", version)})
		if older:
			return ns.answer(ns.KIND_YOUR_TURN, headline="The opening record changed. Review the latest version before signing", stage="record", primary_action="sign")
		last = frappe.get_all("Proceeding Attestation", filters={"minutes_version": version, "satisfies_current": 1, "member_user": ("!=", user)},
			fields=["member_user", "recorded_at"], order_by="recorded_at desc", limit=1)
		sentence = f"{people.full_name(last[0].member_user)} signed at {labels.time(last[0].recorded_at)}." if last else ""
		return ns.answer(ns.KIND_YOUR_TURN, headline="Review and sign opening record", sentence=sentence, stage="record", primary_action="sign")
	from kentender_procurement.proceedings.services import finalize

	waiting = sorted({people.full_name(m["required_member"]) for m in finalize.missing_proofs(frappe.get_doc("Proceeding", doc.proceeding))})
	names = " and ".join([", ".join(waiting[:-1]), waiting[-1]] if len(waiting) > 1 else waiting)
	signed_at = max(t["signed_at"] for t in mine)
	return ns.answer(ns.KIND_WAITING, headline=f"Waiting for {names} to sign the opening record", sentence=f"You signed version {number} at {labels.time(signed_at)}.",
		stage="record", holder=ns.holder("Committee member", waiting))


def _completed_answer(doc, user: str, member, ao: bool) -> dict[str, Any] | None:
	"""Boards r6, h2, h5."""
	import frappe

	if not (member or ao):
		return None
	if doc.outcome == "No bids":
		return ns.answer(ns.KIND_DONE, headline="Opening complete — no bids to evaluate", sentence=f"Completed {labels.when(doc.completed_at)}. Nothing was passed "
			"to Evaluation.", stage="record")
	latest = frappe.get_all("Proceeding Supplement", filters={"proceeding": doc.proceeding}, fields=["recorded_at"], order_by="recorded_at desc", limit=1)
	if latest and member and member["is_recorder"]:
		return ns.answer(ns.KIND_DONE, headline=f"Correction added at {labels.when(latest[0].recorded_at)}. The original opening record is unchanged.",
			sentence="People who can read this record see the correction with it.", stage="record")
	count = frappe.db.count("Opening Entry", {"opening_case": doc.name})
	return ns.answer(ns.KIND_DONE, headline=f"The opening was completed at {labels.when(doc.completed_at)}, after the last signature.",
		sentence=f"The opened {'bid is' if count == 1 else 'bids are'} now available to the Evaluation Committee.", stage="record")


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
	elif doc.state in ("Opening", "Interrupted", "Readout complete", "Awaiting attestations", "Opening complete"):
		candidates += _ceremony(doc, user, member, ao)
	result = ns.choose(*candidates)
	reader = ns.not_involved(result.get("stage", ""))
	return ns.for_viewer(result, technical=technical, reader=reader)


def journey_for(doc) -> dict[str, Any]:
	prepared = bool(appointment.current(doc.name) and arrangements.current(doc.name))
	if doc.state == "Not held":
		return ns.journey(STAGES, current="open", blocked=True, holder_display=", ".join(_ao_names()))
	if not prepared:
		return ns.journey(STAGES, current="prepare", holder_display=", ".join(_ao_names()))
	if doc.state == "Cancelled after start":
		return ns.journey(STAGES, current="open", holder_display="Ended")
	if doc.state == "Interrupted":
		from kentender_procurement.bid_opening.services import ceremony

		pause = ceremony.open_pause(doc.name)
		absent = ceremony.absent_members(doc)
		holder = absent[0]["full_name"] if absent else (SUPPORT if pause and pause.outcome == "Open" else ", ".join(_ao_names()))
		return ns.journey(STAGES, current="open", blocked=True, holder_display=holder)
	if doc.state == "Opening complete":
		return ns.journey(STAGES, complete=True)
	if doc.state == "Awaiting attestations":
		import frappe

		from kentender_procurement.proceedings.services import finalize

		waiting = sorted({people.full_name(m["required_member"]) for m in finalize.missing_proofs(frappe.get_doc("Proceeding", doc.proceeding))})
		return ns.journey(STAGES, current="record", holder_display=", ".join(waiting))
	if doc.state == "Readout complete":
		recorder = appointment.recorder(doc.name)
		return ns.journey(STAGES, current="record", holder_display=recorder["full_name"] if recorder else "")
	now = clock.now()
	if now < get_datetime(doc.effective_deadline):
		return ns.journey(STAGES, current="open", holder_display=f"Opens {labels.when(doc.effective_deadline)}")
	chair = appointment.chair(doc.name)
	return ns.journey(STAGES, current="open", holder_display=chair["full_name"] if chair else "")
