# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The next step and the Prepare · Review · Report tracker for each viewer
(EVL-CHG-001 v0.4 §7.1, §9.1–§9.13; KT-STD-001 §3B; plan D10).

Actionable work takes precedence over waiting; every genuine blocker is shown
with its named fix; a system job is never "waiting on a person". The tracker
describes the viewer's own human journey: Preparing is Prepare current;
Reviewing is Review current, except for a viewer who must still appoint,
assign the secretary or declare (Prepare current); Signing is Report
current; Report sent completes all three. A suspension marks the current
stage blocked; a cancellation keeps the stages done before it, marks the
interrupted stage blocked and ends with "Evaluation ended". No evaluation
required has no tracker. The headlines are the boards' exact words."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import next_step as ns
from kentender_procurement.bid_evaluation.services import people, roster

STAGES = (("prepare", "Prepare"), ("review", "Review"), ("report", "Report"))
STATE_STAGE = {"Preparing": "prepare", "Reviewing": "review", "Signing": "report"}


def when(value) -> str:
	return get_datetime(value).strftime("%-d %b %Y, %H:%M") + " EAT" if value else ""


def in_sentence(label: str) -> str:
	"""A requirement name inside a sentence: "Service location" reads
	"service location", while a code keeps its capitals ("not debarred (SD1)")."""
	first = label.split(" ", 1)[0]
	return label if first.isupper() and len(first) > 1 else label[:1].lower() + label[1:]


def names(users: list[str]) -> str:
	shown = [people.full_name(u) for u in users]
	return shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1] if shown else ""


def viewer(doc, user: str) -> dict[str, Any]:
	members = roster.member_users(doc.name)
	standing = roster.status(doc.name, user) if user in members else None
	return {
		"user": user, "technical": people.technical(user), "ao": people.holds(user, people.ACCOUNTING_OFFICER),
		"hop": people.holds(user, people.HEAD_OF_PROCUREMENT), "auditor": people.holds(user, people.AUDITOR),
		"member": user in members, "chair": roster.chair(doc.name) == user, "secretary": roster.secretary(doc.name) == user,
		"eligible": bool(standing and standing["eligible"]), "undeclared": bool(standing and not standing["declared"] and not standing["conflict"]),
		"conflicted": bool(standing and standing["conflict"]), "unavailable": bool(standing and standing["unavailable"]),
	}


def tracker(doc, v: dict[str, Any], holder_display: str = "") -> dict[str, Any] | None:
	if doc.state == "No evaluation required":
		return None
	setup_owed = (v["ao"] and not roster.current_appointment(doc.name)) or (v["hop"] and not roster.secretary(doc.name)) or v["undeclared"]
	if doc.state == "Report sent":
		return ns.journey(STAGES, complete=True)
	if doc.state == "Cancelled":
		# A cancellation after delivery leaves the case at Report sent (above).
		return ns.journey(STAGES, current=STATE_STAGE[_state_before_cancel(doc)], blocked=True)
	current = "prepare" if setup_owed else STATE_STAGE.get(doc.state, "prepare")
	return ns.journey(STAGES, current=current, blocked=bool(doc.suspended), holder_display=holder_display)


def _state_before_cancel(doc) -> str:
	"""The lifecycle stage the cancellation interrupted, from the case history."""
	if frappe.db.exists("Evaluation Report Version", {"evaluation_case": doc.name, "supersession_kind": "Cancellation"}):
		return "Signing"
	return "Reviewing" if doc.source_intake else "Preparing"


def _source_issue(doc) -> dict[str, Any] | None:
	return frappe.db.get_value("Support Issue", {"module": "Bid Evaluation", "reference_name": doc.name, "operation": "ReceiveOpeningPackage", "status": "Open"},
		["issue_id", "holder_users_json", "opened_at", "holder_role"], as_dict=True)


def answer(doc, user: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	"""The one guidance answer for this viewer on the evaluation record."""
	import json

	from kentender_procurement.bid_evaluation.services import clarification, correction, diligence, discussion, lifecycle, signing

	v = viewer(doc, user)
	ref = doc.tender_reference
	chair, secretary = roster.chair(doc.name), roster.secretary(doc.name)
	if doc.state == "No evaluation required":
		return ns.answer(ns.KIND_DONE, headline="No bids were received. No evaluation is required.")
	if doc.state == "Cancelled":
		return ns.answer(ns.KIND_DONE, headline="Evaluation ended")
	reader = ns.not_involved()
	candidates: list[dict[str, Any]] = []
	if doc.suspended:
		event = frappe.db.get_value("Evaluation Source Event", doc.suspension_event, ["authority", "instruction_reference", "received_at", "permitted_actions_json"],
			as_dict=True) or {}
		permitted = json.loads(event.get("permitted_actions_json") or "[]")
		if v["ao"] and "appointments" in permitted and not roster.current_appointment(doc.name):
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Appoint the members who will evaluate this tender.", primary_action="appoint_committee"))
		else:
			authority = cstr(event.get("authority"))
			return ns.for_viewer(ns.answer(ns.KIND_WAITING, headline="Evaluation is paused by the recorded instruction.",
				holder=ns.holder(people.ACCOUNTING_OFFICER, [people.full_name(authority)] if authority else []), since=ns.since(event.get("received_at"),
				when(event.get("received_at")))), technical=v["technical"])
	# Preparation work (any state before delivery).
	if doc.state in ("Preparing", "Reviewing"):
		if v["ao"] and not roster.current_appointment(doc.name):
			headline = "Appoint the evaluation committee." if doc.source_intake else "Appoint the members who will evaluate this tender."
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline=headline, primary_action="appoint_committee",
				sentence="Opening is complete. The evaluation committee has not been appointed." if doc.source_intake else ""))
		if v["hop"] and not secretary:
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Assign the person who will organise the evaluation record.", primary_action="assign_secretary"))
		if v["undeclared"]:
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Complete your declaration before viewing bids.", primary_action="complete_declaration"))
		blocked = [u for u in roster.member_users(doc.name) if roster.status(doc.name, u)["conflict"] or roster.status(doc.name, u)["unavailable"]]
		if v["ao"] and blocked:
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Resolve {people.full_name(blocked[0])}'s declared conflict." if roster.status(doc.name,
				blocked[0])["conflict"] else f"Resolve {people.full_name(blocked[0])}'s inability to serve.", primary_action="replace_member"))
	if doc.state == "Preparing":
		issue = _source_issue(doc)
		if issue:
			holders = json.loads(issue.holder_users_json or "[]")
			candidates.append(ns.answer(ns.KIND_WAITING, headline=f"{names(holders) or 'Technical support'} is resolving the opening-package issue.",
				holder=ns.holder(issue.holder_role, [people.full_name(h) for h in holders]), since=ns.since(issue.opened_at, when(issue.opened_at))))
		elif v["member"] or v["secretary"] or v["ao"] or v["hop"]:
			from kentender_procurement.tenders.services import evaluation_seam as tenders

			fact = tenders.publication_fact(doc.tender) or {}
			candidates.append(ns.answer(ns.KIND_SCHEDULED, headline=f"Opening is scheduled for {when(fact.get('submission_deadline'))}.",
				holder=ns.holder("System")))
	if doc.state == "Reviewing":
		candidates += _reviewing(doc, v, ref, chair, secretary, clarification, diligence, discussion, signing, correction)
	if doc.state == "Signing":
		version = signing.signing_version(doc)
		sigs = signing.signatures(version)
		pending = [s["member"] for s in sigs if not s["signed_at"]]
		delivery = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name, "report_version": version.name if version else ""}, "status")
		if v["secretary"] and delivery == "Failed":
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="The signed report could not be delivered.", primary_action="retry_delivery"))
		if v["eligible"] and user in pending:
			candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review and sign the evaluation report.", primary_action="sign_report"))
		elif (v["member"] or v["secretary"]) and pending:
			mine = next((s for s in sigs if s["member"] == user and s["signed_at"]), None)
			since_at = mine["signed_at"] if mine else (version.frozen_at if version else None)
			candidates.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {names(pending)} to sign report {version.version_number}.",
				holder=ns.holder("Appointed member", [people.full_name(u) for u in pending]), since=ns.since(since_at, when(since_at))))
	if doc.state == "Report sent":
		delivery = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name, "status": "Delivered"}, ["recipient_user", "delivered_at",
			"review_state"], as_dict=True, order_by="delivered_at desc")
		for event in frappe.get_all("Evaluation Source Event", filters={"evaluation_case": doc.name, "kind": "Opening supplement", "delivered_context": "After delivery"},
				fields=["name", "impact", "head_review_state"]):
			if v["chair"] and event.impact in ("", "Pending"):
				candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the opening update.", primary_action="record_impact"))
			if delivery and user == delivery.recipient_user and event.head_review_state == "Open":
				candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the opening update alongside the delivered report.", primary_action="open_new_evidence"))
		if delivery and user == delivery.recipient_user:
			if frappe.db.exists("Evaluation Correction Notice", {"evaluation_case": doc.name, "head_review_state": "Open"}):
				candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the report correction.", primary_action="open_new_evidence"))
			if delivery.review_state == "Open":
				candidates.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the committee's report.", primary_action="open_report"))
		if delivery and (v["member"] or v["secretary"] or v["auditor"]):
			candidates.append(ns.answer(ns.KIND_DONE, headline=f"The committee report was sent to {people.full_name(delivery.recipient_user)} on {when(delivery.delivered_at)}."))
	chosen = ns.choose(*candidates) if candidates else reader
	return ns.for_viewer(chosen, technical=v["technical"], reader=ns.not_involved())


def _reviewing(doc, v, ref, chair, secretary, clarification, diligence, discussion, signing, correction) -> list[dict[str, Any]]:
	from kentender_procurement.bid_evaluation.services import comparison, report, timers

	out: list[dict[str, Any]] = []
	user = v["user"]
	session = discussion.active_session(doc)
	present = discussion.present(doc) if session else []
	items = frappe.get_all("Evaluation Discussion Item", filters={"evaluation_case": doc.name, "status": "Open"}, fields=["subject", "opened_at"], order_by="opened_at asc")
	returned = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name, "review_state": "Returned"}, ["returned_by", "return_comment"], as_dict=True,
		order_by="returned_at desc")
	if session:
		missing = [u for u in roster.member_users(doc.name) if u not in present]
		if v["member"] and v["eligible"] and user not in present:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Join the committee discussion.", primary_action="join_discussion"))
		if v["secretary"] and user in present and missing:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Record notes while the committee waits for {names(missing)}.", primary_action="save_note"))
		elif v["secretary"] and user in present:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record the discussion for the chair.", primary_action="save_note"))
		if v["secretary"] and user not in present:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Join the committee discussion.", primary_action="join_discussion"))
		if v["chair"] and missing:
			out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {names(missing)} to join the discussion.",
				holder=ns.holder("Appointed member", [people.full_name(u) for u in missing])))
		elif v["chair"]:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record the committee's conclusion.", primary_action="record_conclusion"))
		if v["member"] and user in present and not v["chair"]:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the recorded conclusion and add any disagreement.", primary_action="record_disagreement"))
	if v["chair"] and items and not session:
		label = in_sentence(cstr(items[0].subject).split(" — ")[0])
		out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Discuss the {label} finding with the committee.", primary_action="start_discussion"))
	for request in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": doc.name, "status": ("in", ("Authorised", "Sent"))},
			fields=["name", "status", "evaluation_bid", "notice_state", "requirement_key", "sent_at", "reply_deadline"]):
		bidder = frappe.db.get_value("Evaluation Bid", request.evaluation_bid, "tenderer_name")
		reply = frappe.db.exists("Evaluation Clarification Reply", {"clarification": request.name, "state": "Sent"})
		if v["secretary"] and request.status == "Authorised":
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Send the committee's question to {bidder}.", primary_action="send_clarification"))
		if v["secretary"] and request.status == "Sent" and request.notice_state == "Delivery problem":
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Retry the clarification notice.", primary_action="retry_notice"))
		if request.status == "Sent" and (reply or clarification.overdue(frappe.get_doc("Evaluation Clarification", request.name))):
			if v["chair"] and not session:
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record how the reply affects the finding.", primary_action="start_discussion"))
		elif request.status == "Sent" and (v["chair"] or v["secretary"] or v["member"]):
			out.append(ns.answer(ns.KIND_WAITING, headline=f"Waiting for {bidder}'s reply.", holder=ns.holder("Supplier", [bidder]),
				since=ns.since(request.sent_at, when(request.sent_at))))
	plan = diligence.current_plan(doc.name)
	if plan and plan.status == "Current":
		mine = user in diligence.participants(plan)
		observed = {o.participant_user for o in diligence.observations(plan)}
		if mine and plan.report_state == "Draft" and user not in observed:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record the supplier verification findings.", primary_action="record_observation"))
		if user == plan.lead_user and plan.report_state == "Draft" and set(diligence.participants(plan)) <= observed:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Send the verification report to its participants for signing.", primary_action="send_verification"))
		if mine and plan.report_state == "Frozen" and diligence.my_targets(doc, plan, user):
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review and sign verification report", primary_action="sign_verification"))
		if v["chair"] and plan.report_state == "Signed" and not session:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record how verification affects the evaluation.", primary_action="start_discussion"))
	for event in frappe.get_all("Evaluation Source Event", filters={"evaluation_case": doc.name, "kind": "Opening supplement", "impact": ("in", ("", "Pending"))},
			fields=["name"]):
		if v["eligible"]:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the correction added to the opening record.", primary_action="record_impact"))
	dated = timers.dated(doc)
	if v["secretary"]:
		if returned:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Correct the report returned by {people.full_name(returned.returned_by)}.", primary_action="send_for_signing"))
		ready = signing.readiness(doc)
		if ready:
			issues = (ready.reasons[0]["detail"].get("issues") or []) if ready.reasons else []
			if issues and ready.reasons[0]["code"] == "EVL_REPORT_INCOMPLETE":
				out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Open the unresolved issue before sending the report for signing.", primary_action="open_issue"))
		elif dated["validity_expired"]:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Record the expired tender validity in the report.", primary_action="send_for_signing"))
		else:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Check the report and send it to members for signing.", primary_action="send_for_signing"))
	# the member's own review work, except while they sit in a live discussion
	# (the discussion's own step is theirs then: boards D05-START, D05-MEMBER)
	if v["eligible"] and not v["secretary"] and not (session and user in present):
		pending = _evidence_for(doc, user)
		if pending:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline=f"Review the evidence for the {in_sentence(pending)}.", primary_action="review_bid"))
		elif dated["overdue"] and v["chair"]:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the overdue evaluation and complete its report.", primary_action="view_report"))
		else:
			out.append(ns.answer(ns.KIND_YOUR_TURN, headline="Review the results and raise a concern if needed.", primary_action="review_bid"))
	return out


def _evidence_for(doc, user: str) -> str:
	"""The first requirement still waiting for a member's evidence finding."""
	from kentender_procurement.bid_evaluation.services import aggregate, checks

	run = checks.current_run(doc.name)
	if not run:
		return ""
	human = aggregate.human_record(doc.name)
	for bid in frappe.get_all("Evaluation Bid", filters={"evaluation_case": doc.name}, pluck="name", order_by="entry_number asc"):
		for r in aggregate.bid_results(doc.name, run, bid, human)["requirements"]:
			if r["evidence_pending"] and not r["open_item"]:
				return cstr(r["label"])
	return ""
