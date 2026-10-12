# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation work items (EVL-CHG-001 v0.4 §7.3 hand-off register; plan D11;
`reconciliation/handoff_register.md`).

Every row is derived from the current state, so an item appears when its
event happens and clears only when the recorded action it names is
committed; opening or reading never clears anything. Items are keyed by
(evaluation, source event, responsibility), so concurrent items never
collide. A system job is never "waiting on a person" (§7.1). Registered on
`kt_my_work_providers`. Rows grow with each phase's commands."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import people, records, roster

PAGE = "tenders"
OPEN_STATES = ("Preparing", "Reviewing", "Signing", "Report sent")


def _row(doc, *, key: str, title: str, action_label: str, role: str, sub: str = "", since=None, status: str = "Assigned") -> dict[str, Any]:
	route = [PAGE, doc.tender_reference, "evaluation", *([sub] if sub else [])]
	return {
		"task_id": f"{doc.name}:{key}", "task_type": f"bid_evaluation.{key.split(':')[0]}", "title": title, "reference": doc.tender_reference,
		"module": "Bid Evaluation", "stage": "Bid evaluation", "fiscal_year": "", "organisation_unit": "", "assignment": role, "status": status,
		"received_at": cstr(since or ""), "due_at": "", "action_label": action_label, "route": route, "route_options": {}, "concurrency_token": "",
		"can_claim": False, "can_open": True, "comment": "",
	}


def _preparation(doc, user: str, ao: bool, hop: bool, out: dict[str, list]) -> None:
	ref = doc.tender_reference
	appointment = roster.current_appointment(doc.name)
	if doc.state not in ("Preparing", "Reviewing"):
		return
	# the Head is secretary by office when the committee is appointed: no secretary task or waiting item exists (EVL-CHG-001 v0.8 §3, EVL-A20)
	if not appointment:
		if ao:
			out["assigned"].append(_row(doc, key="appoint", title=f"Appoint evaluation committee for {ref}", action_label="Appoint committee",
				role=people.ACCOUNTING_OFFICER, sub="appoint", since=doc.prepared_at))
		return
	members = roster.member_users(doc.name)
	undeclared = [u for u in members if not roster.declaration(doc.name, u)]
	if user in undeclared:
		out["assigned"].append(_row(doc, key=f"declare:{appointment.name}:{user}", title=f"Declare interests for {ref}", action_label="Complete declaration",
			role="Appointed member", sub="declaration", since=appointment.appointed_at))
	if ao and undeclared:
		out["waiting"].append(_row(doc, key=f"declare:waiting:{appointment.name}", title="Waiting for committee declarations", action_label="View",
			role=people.ACCOUNTING_OFFICER, status="Waiting", since=appointment.appointed_at))
	blocked = [u for u in members if roster.status(doc.name, u)["conflict"] or roster.status(doc.name, u)["unavailable"]]
	if blocked:
		if ao:
			out["assigned"].append(_row(doc, key=f"resolve-appointment:{appointment.name}", title=f"Resolve committee appointment for {ref}",
				action_label="Replace member", role=people.ACCOUNTING_OFFICER, sub="replace"))
		chair = roster.chair(doc.name)
		if chair == user and user not in blocked:
			out["waiting"].append(_row(doc, key=f"resolve-appointment:waiting:{appointment.name}", title="Waiting for committee appointment", action_label="View",
				role="Chair", status="Waiting"))


def _review(doc, user: str, out: dict[str, list]) -> None:
	if doc.state == "Reviewing" and doc.source_intake and roster.status(doc.name, user)["eligible"]:
		out["assigned"].append(_row(doc, key=f"review:{doc.source_intake}:{user}", title=f"Review bids for {doc.tender_reference}", action_label="Open evaluation",
			role="Appointed member"))


def _concerns(doc, user: str, out: dict[str, list]) -> None:
	if doc.state != "Reviewing":
		return
	chair = roster.chair(doc.name)
	for item in frappe.get_all("Evaluation Discussion Item", filters={"evaluation_case": doc.name, "status": "Open"}, fields=["name", "opened_at", "opened_by",
			"subject"], order_by="opened_at asc"):
		if user == chair:
			out["assigned"].append(_row(doc, key=f"concern:{item.name}", title=f"Resolve evaluation concern for {doc.tender_reference}", action_label="Start discussion",
				role="Chair", since=item.opened_at))
		if user == item.opened_by and user != chair:
			out["waiting"].append(_row(doc, key=f"concern:waiting:{item.name}", title="Waiting for committee response", action_label="View", role="Appointed member",
				status="Waiting", since=item.opened_at))


def _clarifications(doc, user: str, out: dict[str, list]) -> None:
	from kentender_procurement.bid_evaluation.services import clarification

	if doc.state != "Reviewing":
		return
	chair, secretary = roster.chair(doc.name), roster.secretary(doc.name)
	for request in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": doc.name, "status": ("in", ("Authorised", "Sent"))},
			fields=["name", "status", "evaluation_bid", "authorised_at", "sent_at"]):
		bidder = frappe.db.get_value("Evaluation Bid", request.evaluation_bid, "tenderer_name")
		if request.status == "Authorised":
			if user == secretary:
				out["assigned"].append(_row(doc, key=f"send:{request.name}", title=f"Send clarification for {bidder}", action_label="Send clarification",
					role="Secretary", sub=f"clarifications/{request.name}", since=request.authorised_at))
			if user == chair:
				out["waiting"].append(_row(doc, key=f"send:waiting:{request.name}", title="Waiting for clarification to be sent", action_label="View", role="Chair",
					status="Waiting", since=request.authorised_at))
			continue
		answered = frappe.db.exists("Evaluation Clarification Reply", {"clarification": request.name, "state": "Sent"})
		if answered or clarification.overdue(frappe.get_doc("Evaluation Clarification", request.name)):
			if user == chair:
				out["assigned"].append(_row(doc, key=f"outcome:{request.name}", title=f"Review clarification outcome for {bidder}", action_label="Review outcome",
					role="Chair", sub=f"clarifications/{request.name}", since=request.sent_at))
		elif user in (chair, secretary) or user in roster.member_users(doc.name):
			out["waiting"].append(_row(doc, key=f"reply:waiting:{request.name}", title=f"Waiting for {bidder}'s reply", action_label="View", role="Committee",
				status="Waiting", since=request.sent_at))


def _verification(doc, user: str, out: dict[str, list]) -> None:
	from kentender_procurement.bid_evaluation.services import diligence

	plan = diligence.current_plan(doc.name)
	if doc.state != "Reviewing" or not plan or plan.status != "Current":
		return
	ref, chair = doc.tender_reference, roster.chair(doc.name)
	participants = diligence.participants(plan)
	observed = {o.participant_user for o in diligence.observations(plan)}
	if plan.report_state == "Draft":
		if user in participants and user not in observed:
			out["assigned"].append(_row(doc, key=f"observe:{plan.name}:{user}", title=f"Record verification findings for {ref}", action_label="Record findings",
				role="Verification participant", sub="verification", since=plan.recorded_at))
		if user == plan.lead_user:
			out["assigned"].append(_row(doc, key=f"prepare-verification:{plan.name}", title=f"Prepare verification report for {ref}", action_label="Prepare report",
				role="Verification lead", sub="verification", since=plan.recorded_at))
		if user == chair and user != plan.lead_user:
			out["waiting"].append(_row(doc, key=f"verify:waiting:{plan.name}", title="Waiting for verification findings", action_label="View", role="Chair",
				status="Waiting", since=plan.recorded_at))
	elif plan.report_state == "Frozen":
		if user in participants and diligence.my_targets(doc, plan, user):
			out["assigned"].append(_row(doc, key=f"sign-verification:{plan.report_version}:{user}", title=f"Review and sign verification report for {ref}",
				action_label="Sign verification report", role="Verification participant", sub="verification", since=plan.frozen_at))
		elif user == plan.lead_user:
			out["waiting"].append(_row(doc, key=f"sign-verification:waiting:{plan.report_version}", title="Waiting for verification signatures", action_label="View",
				role="Verification lead", status="Waiting", since=plan.frozen_at))
	elif plan.report_state == "Signed":
		if user == chair:
			out["assigned"].append(_row(doc, key=f"verification-outcome:{plan.name}", title=f"Review verification outcome for {ref}", action_label="Start discussion",
				role="Chair", since=plan.frozen_at))
		elif user == plan.lead_user:
			out["waiting"].append(_row(doc, key=f"verification-outcome:waiting:{plan.name}", title="Waiting for committee conclusion", action_label="View",
				role="Verification lead", status="Waiting", since=plan.frozen_at))


def _report(doc, user: str, out: dict[str, list]) -> None:
	from kentender_procurement.bid_evaluation.services import signing

	ref, chair, secretary = doc.tender_reference, roster.chair(doc.name), roster.secretary(doc.name)
	if doc.state == "Signing":
		version = signing.signing_version(doc)
		pending = [s["member"] for s in signing.signatures(version) if not s["signed_at"]]
		if user in pending:
			out["assigned"].append(_row(doc, key=f"sign:{version.name}:{user}", title=f"Review and sign report for {ref}", action_label="Review and sign",
				role="Appointed member", sub="report", since=version.frozen_at))
		if user == secretary and pending:
			out["waiting"].append(_row(doc, key=f"sign:waiting:{version.name}", title="Waiting for committee signatures", action_label="View", role="Secretary",
				status="Waiting", since=version.frozen_at))
	if doc.state == "Reviewing":
		latest = frappe.db.get_value("Evaluation Report Version", {"evaluation_case": doc.name, "state": ("!=", "Draft")}, ["name", "state", "supersession_kind",
			"supersession_reason", "superseded_at"], as_dict=True, order_by="version_number desc")
		if latest and latest.state == "Superseded" and latest.supersession_kind == "Concern" and user in (chair, secretary):
			out["assigned"].append(_row(doc, key=f"report-concern:{latest.name}", title=f"Resolve report concern for {ref}", action_label="Open report",
				role="Chair" if user == chair else "Secretary", sub="report", since=latest.superseded_at))
		returned = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name, "review_state": "Returned"}, ["name", "return_comment",
			"returned_at", "recipient_user"], as_dict=True, order_by="returned_at desc")
		if returned and latest and latest.state == "Returned":
			if user in (chair, secretary):
				out["assigned"].append(_row(doc, key=f"correct:{returned.name}", title=f"Correct evaluation report for {ref}: {returned.return_comment}",
					action_label="Open report", role="Chair" if user == chair else "Secretary", sub="report", since=returned.returned_at))
			if user == returned.recipient_user:
				out["waiting"].append(_row(doc, key=f"correct:waiting:{returned.name}", title="Waiting for corrected report", action_label="View",
					role=people.HEAD_OF_PROCUREMENT, status="Waiting", since=returned.returned_at))
	delivery = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name, "status": "Delivered"}, ["name", "recipient_user", "delivered_at",
		"review_state"], as_dict=True, order_by="delivered_at desc")
	if doc.state == "Report sent" and delivery and user == delivery.recipient_user and delivery.review_state == "Open":
		out["assigned"].append(_row(doc, key=f"review-report:{delivery.name}", title=f"Review evaluation report for {ref}", action_label="Open report",
			role=people.HEAD_OF_PROCUREMENT, sub="report", since=delivery.delivered_at))
	for event in frappe.get_all("Evaluation Source Event", filters={"evaluation_case": doc.name, "kind": "Opening supplement"}, fields=["name", "impact",
			"head_review_state", "delivered_context", "received_at"]):
		pending = event.impact in ("", "Pending")
		if pending and event.delivered_context == "Before delivery" and roster.status(doc.name, user)["eligible"]:
			out["assigned"].append(_row(doc, key=f"supplement:{event.name}", title=f"Review opening update for {ref}", action_label="Record impact",
				role="Chair" if user == chair else "Appointed member", sub="updates", since=event.received_at))
		if event.delivered_context == "After delivery":
			if pending and user == chair:
				out["assigned"].append(_row(doc, key=f"supplement:{event.name}:chair", title=f"Review opening update for {ref}", action_label="Record impact",
					role="Chair", sub="updates", since=event.received_at))
			if delivery and user == delivery.recipient_user and event.head_review_state == "Open":
				out["assigned"].append(_row(doc, key=f"supplement:{event.name}:head", title=f"Review opening update for {ref}", action_label="Open new evidence",
					role=people.HEAD_OF_PROCUREMENT, sub="updates", since=event.received_at))
	for notice in frappe.get_all("Evaluation Correction Notice", filters={"evaluation_case": doc.name, "head_review_state": "Open"}, fields=["name", "recorded_at"]):
		if delivery and user == delivery.recipient_user:
			out["assigned"].append(_row(doc, key=f"correction:{notice.name}", title=f"Review report correction for {ref}", action_label="Open new evidence",
				role=people.HEAD_OF_PROCUREMENT, sub="updates", since=notice.recorded_at))
		if user == chair:
			out["waiting"].append(_row(doc, key=f"correction:waiting:{notice.name}", title="Waiting for correction review", action_label="View", role="Chair",
				status="Waiting", since=notice.recorded_at))


def my_work_rows(user: str) -> dict[str, list[dict[str, Any]]]:
	out: dict[str, list[dict[str, Any]]] = {"assigned": [], "claimable": [], "waiting": []}
	if not user or people.technical(user):
		return out
	ao = people.holds(user, people.ACCOUNTING_OFFICER)
	hop = people.holds(user, people.HEAD_OF_PROCUREMENT)
	for name in frappe.get_all(records.CASE, filters={"state": ("in", OPEN_STATES)}, pluck="name", order_by="creation asc"):
		doc = frappe.get_doc(records.CASE, name)
		involved = ao or hop or user in roster.member_users(doc.name) or user == roster.secretary(doc.name) or bool(frappe.db.exists(
			"Evaluation Report Delivery", {"evaluation_case": doc.name, "recipient_user": user}))
		if not involved:
			continue
		_preparation(doc, user, ao, hop, out)
		_review(doc, user, out)
		_concerns(doc, user, out)
		_clarifications(doc, user, out)
		_verification(doc, user, out)
		_report(doc, user, out)
	return out
