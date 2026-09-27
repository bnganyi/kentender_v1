# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid next step, journey and the Submit guard (BDS-CHG-001 v0.8 §5.12, §5.13,
§10.19; KT-STD-001 v1.8 §3B; plan Phase 10).

One answer per viewer, computed on the server from the same facts the
commands check: the bid's recorded status, readiness, the addendum state,
the latest submission attempt, the deadline on the trusted clock, the
submission availability, the supplier-portal information and the
signatory's certificate. The wording is §5.12's, with the fixture's names
replaced by the current holders: the bid's Authorised Signatory, the
Technical Operator and the Release Operator responsibilities (owner decision
27 Sep 2026). `since` is given only where an instant is recorded.

The bid record has three stages — Prepare bid, Sign and submit, Receipt —
with §5.12's markers; the reduced line reads "Stage {label} of 3"
(§10.19). The five tasks stay a checklist inside preparation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import next_step as ns

from kentender_procurement.bid_submission.services import addendum, availability, bid_authorization as authz, labels, readiness, supplier_gateway
from kentender_procurement.bid_submission.services.errors import MESSAGES

STAGES = (("BID_PREPARATION", "Prepare bid"), ("SIGN_AND_SUBMIT", "Sign and submit"), ("RECEIPT", "Receipt"))
MARKERS = {"D": ns.MARKER_DONE, "C": ns.MARKER_CURRENT, "B": ns.MARKER_BLOCKED, "N": ns.MARKER_NOT_STARTED}
TECHNICAL, RELEASE = "Technical Operator", "Release Operator"
SUPPLIER = "Supplier Representative / Authorised Signatory"


# -- holders -------------------------------------------------------------------


def _name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user)


def responsibility_holders(business_role: str) -> list[str]:
	"""Current holders of a Site-wide responsibility, resolved now."""
	from kentender_core.services.authorization import PURPOSE_READ, authorise_record

	users = frappe.get_all("User Responsibility Assignment", filters={"business_role": business_role, "status": "Enabled"}, pluck="user", order_by="creation asc", limit_page_length=0)
	out: list[str] = []
	for user in users:
		if user not in out and authorise_record(user=user, business_role=business_role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			out.append(user)
	return [_name(u) for u in out]


def signatory_names(ctx, at=None) -> list[str]:
	named = cstr(ctx.arrangement.authorised_signatory_assignment)
	if named:
		row = supplier_gateway.assignment(assignment_id=named, at=at)
		return [_name(row["user"])] if row else []
	return [_name(a["user"]) for a in supplier_gateway.organisation_signatories(organisation_id=ctx.workspace.lead_organisation, at=at)]


def _holder_line(role_label: str, people: list[str]) -> str:
	return f"{role_label} {', '.join(people)}" if people else role_label


# -- journey ---------------------------------------------------------------------


def journey(markers: str, holder_display: str = "") -> dict[str, Any]:
	"""The bid tracker with §5.12's explicit markers (e.g. "DBN")."""
	rows, current = [], None
	for (code, label), letter in zip(STAGES, markers):
		marker = MARKERS[letter]
		active = letter in ("C", "B")
		rows.append({"code": code, "label": label, "marker": marker, "marker_label": ns.MARKER_LABELS[marker], "holder": holder_display if active else ""})
		if active and current is None:
			current = rows[-1]
	parts = {"prefix": "Stage ", "label": current["label"], "suffix": " of 3"} if current else None
	return {
		"stages": rows, "current": current["code"] if current else "", "reduced_style": "stage_label_of", "reduced": False,
		"reduced_text": (parts["prefix"] + parts["label"] + parts["suffix"]) if parts else "", "reduced_parts": parts, "upstream": None, "downstream": None,
	}


# -- the Submit guard (§5.13) ------------------------------------------------------


def _text_fix(label: str, responsibility: str, people: list[str] | None = None) -> dict[str, Any]:
	return ns.fix(label, responsibility=responsibility, kind=ns.FIX_TEXT, person=", ".join(people or []))


def submit_guard(ctx, *, actor: str, at, tasks=None) -> dict[str, Any]:
	"""Every reason Submit is not available to this person now, each with
	its figures and real fix (all together, never one at a time)."""
	from kentender_procurement.bid_submission.services import signature

	ws = ctx.workspace
	guards: list[dict[str, Any]] = []
	deadline = frappe.db.get_value("Tender", ws.tender, "submission_deadline")
	deadline_label = labels.datetime_label(deadline)
	if deadline and get_datetime(at) >= get_datetime(deadline):
		return ns.guard(False, reason_code="BDS_DEADLINE_PASSED", message=MESSAGES["BDS_DEADLINE_PASSED"], figures={"deadline": deadline_label, "server_time": labels.datetime_label(at)})
	assignment = ctx.assignment
	if assignment.get("responsibility") != authz.SIGNATORY or not assignment.get("signatory_ready") or (ctx.arrangement.authorised_signatory_assignment and assignment.get("assignment_id") != ctx.arrangement.authorised_signatory_assignment):
		people = signatory_names(ctx, at)
		guards.append(ns.guard(False, reason_code="BDS_SIGNATORY_REQUIRED", message=MESSAGES["BDS_SIGNATORY_REQUIRED"], figures={"signatory": ", ".join(people)}, fixes=[_text_fix("The Authorised Signatory submits this bid.", authz.SIGNATORY, people)]))
	if addendum.pending(ctx) is not None or addendum.attention(ctx):
		guards.append(ns.guard(False, reason_code="BDS_ADDENDUM_REVIEW_REQUIRED", message=MESSAGES["BDS_ADDENDUM_REVIEW_REQUIRED"], figures={"tasks": addendum.attention(ctx) or ["documents"]},
			fixes=[ns.fix("Review addendum", responsibility=SUPPLIER, kind=ns.FIX_ROUTE, fix_id="review_addendum", target={"task": "documents"}, primary=True)]))
	tasks = tasks or readiness.evaluate(ctx, attention=addendum.attention(ctx))
	must_fix = [(key, s) for key, t in tasks.items() if key != readiness.REVIEW_TASK for s in t.fields if s.issue and s.issue["severity"] == readiness.MUST_FIX]
	if must_fix:
		task_keys = list(dict.fromkeys(key for key, _s in must_fix))
		guards.append(ns.guard(False, reason_code="BDS_MUST_FIX", message=MESSAGES["BDS_MUST_FIX"], figures={"count": len(must_fix), "tasks": task_keys},
			fixes=[ns.fix(f"Fix item: {ctx.model.task(k).label}", responsibility=SUPPLIER, kind=ns.FIX_ROUTE, fix_id=f"fix_item:{k}", target={"task": k}, primary=i == 0) for i, k in enumerate(task_keys)]))
	gate = availability.get_submission_availability()
	if not gate["available"]:
		if gate["code"] == "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED":
			people = responsibility_holders(RELEASE)
			guards.append(ns.guard(False, reason_code=gate["code"], message=gate["message"], figures={"deadline": deadline_label}, fixes=[_text_fix("The Release Operator holds the verified production-submission release.", RELEASE, people)]))
		else:
			people = responsibility_holders(TECHNICAL)
			what = "digital signing" if gate["code"] == "BDS_SIGNATURE_UNAVAILABLE" else "electronic submission"
			guards.append(ns.guard(False, reason_code=gate["code"], message=gate["message"], figures={"deadline": deadline_label}, fixes=[_text_fix(f"The Technical Operator restores {what}.", TECHNICAL, people)]))
	from kentender_core.services import public_portal

	if (public_portal.get_public_portal_information() or {}).get("status") != "Complete":
		guards.append(ns.guard(False, reason_code="BDS_PORTAL_INFORMATION_UNAVAILABLE", message=MESSAGES["BDS_PORTAL_INFORMATION_UNAVAILABLE"], fixes=[_text_fix("The CFG System Manager restores supplier portal information in System setup.", "CFG System Manager", _cfg_holders())]))
	correlation = signature.pending_attempt(ws.name)
	if correlation:
		guards.append(ns.guard(False, reason_code="BDS_SUBMISSION_UNCERTAIN", message=MESSAGES["BDS_SUBMISSION_UNCERTAIN"], figures={"correlation_id": correlation},
			fixes=[ns.fix("View status", responsibility=SUPPLIER, kind=ns.FIX_ROUTE, fix_id="view_status", target={"screen": "status"})]))
	if assignment.get("responsibility") == authz.SIGNATORY and gate["code"] not in ("BDS_PRODUCTION_SUBMISSION_NOT_ENABLED", "BDS_SIGNATURE_UNAVAILABLE"):
		from kentender_procurement.bid_submission.services import gateways

		found = gateways.trust().certificate(user=actor, organisation=ws.lead_organisation, at=at) if gateways.trust_healthy() else {"status": "None"}
		if found.get("status") != "Ready":
			guards.append(ns.guard(False, reason_code="BDS_SIGNATORY_CERTIFICATE_REQUIRED", message=MESSAGES["BDS_SIGNATORY_CERTIFICATE_REQUIRED"], figures={"certificate": found.get("status"), "deadline": deadline_label},
				fixes=[ns.fix("Check certificate", responsibility=authz.SIGNATORY, kind=ns.FIX_COMMAND, fix_id="check_certificate", person=_name(actor), primary=True)]))
	return ns.combine(*guards) if guards else ns.allowed()


def _cfg_holders() -> list[str]:
	"""The CFG System Manager: a Technical Operator who holds System Manager."""
	names = []
	for user in frappe.get_all("User Responsibility Assignment", filters={"business_role": TECHNICAL, "status": "Enabled"}, pluck="user"):
		if "System Manager" in frappe.get_roles(user) and _name(user) not in names:
			names.append(_name(user))
	return names


# -- the next step (§5.12) ----------------------------------------------------------


def _latest_attempt(workspace: str):
	name = frappe.db.get_value("Bid Submission Attempt", {"bid_workspace": workspace}, "name", order_by="creation desc")
	return frappe.get_doc("Bid Submission Attempt", name) if name else None


def _current_version(ws):
	if not ws.current_submission_version:
		return None
	return frappe.db.get_value("Bid Submission Version", ws.current_submission_version, ["version_number", "accepted_at", "receipt", "status_since"], as_dict=True)


def _change_label(tender: str) -> str:
	"""What the latest issued addendum changed, in words (§5.12: "the changed
	delivery location")."""
	ref = frappe.db.get_value("Tender Addendum", {"tender": tender, "status": "Issued"}, "affected_reference", order_by="issued_at desc")
	text = cstr(ref).split(" — ")[-1].strip()
	return text[:1].lower() + text[1:] if text else "Tender details"


def for_bid(ctx, *, actor: str, at, tasks=None) -> dict[str, Any]:
	"""{"next_step", "journey", "submit_guard"} for this viewer."""
	ws = ctx.workspace
	tasks = tasks or readiness.evaluate(ctx, attention=addendum.attention(ctx) + (["documents"] if addendum.pending(ctx) is not None else []))
	deadline = frappe.db.get_value("Tender", ws.tender, "submission_deadline")
	deadline_label = labels.datetime_label(deadline)
	closed = bool(deadline) and get_datetime(at) >= get_datetime(deadline)
	signatory = ctx.assignment.get("responsibility") == authz.SIGNATORY
	viewer = _name(actor)
	current = _current_version(ws)
	guard = submit_guard(ctx, actor=actor, at=at, tasks=tasks)
	codes = [b["reason_code"] for b in ns.blockers_of(guard)]

	def result(answer, markers, holder_display=""):
		return {"next_step": answer, "journey": journey(markers, holder_display), "submit_guard": guard}

	# -- after the deadline: facts only ------------------------------------------
	if closed or ws.status == "Closed without submission":
		if current:
			return result(ns.answer(ns.KIND_DONE, headline=f"Bid Version {int(current.version_number)} remains submitted; submission changes closed at {deadline_label}.", stage="RECEIPT", primary_action="view_receipt"), "DDD")
		if ws.status == "Withdrawn":
			return result(ns.answer(ns.KIND_DONE, headline=f"This bid was withdrawn; submission closed at {deadline_label}.", stage="RECEIPT"), "DDD")
		return result(ns.answer(ns.KIND_DONE, headline=f"Submission closed at {deadline_label}; this Draft was not submitted.", stage="BID_PREPARATION", primary_action="back_to_my_bids"), "DNN")

	# -- a submitted or withdrawn bid, before the deadline --------------------------
	if ws.status == "Submitted" and current:
		if signatory:
			fixes = [ns.fix("Prepare replacement", responsibility=authz.SIGNATORY, kind=ns.FIX_COMMAND, fix_id="prepare_replacement"), ns.fix("Withdraw bid", responsibility=authz.SIGNATORY, kind=ns.FIX_COMMAND, fix_id="withdraw_bid")]
			return result(ns.answer(ns.KIND_YOUR_TURN, headline=f"You may prepare a replacement or withdraw before {deadline_label}. Version {int(current.version_number)} remains submitted.", sentence="These are options, not assigned overdue work.", stage="RECEIPT", fixes=fixes), "DDD")
		return result(ns.answer(ns.KIND_DONE, headline=f"Bid Version {int(current.version_number)} was accepted on {labels.datetime_seconds_label(current.accepted_at)}.", stage="RECEIPT", primary_action="view_receipt"), "DDD")
	if ws.status == "Withdrawn":
		if signatory:
			return result(ns.answer(ns.KIND_YOUR_TURN, headline="You may start a new bid before the deadline. This bid was withdrawn; no bid is currently submitted.", sentence="This is an available option, not overdue work.", stage="RECEIPT",
				fixes=[ns.fix("Start replacement", responsibility=authz.SIGNATORY, kind=ns.FIX_COMMAND, fix_id="start_replacement", primary=True)], primary_action="start_replacement"), "DDD")
		return result(ns.answer(ns.KIND_DONE, headline="This bid was withdrawn; no bid is currently submitted.", stage="RECEIPT"), "DDD")

	# -- an open Draft (a replacement Draft when a Version is current) -------------------
	replacement = current is not None
	still_preparing = readiness.bid_status(tasks) != "Ready to submit"
	if "BDS_SUBMISSION_UNCERTAIN" in codes:
		attempt = _latest_attempt(ws.name)
		people = responsibility_holders(TECHNICAL)
		return result(ns.answer(ns.KIND_WAITING, headline=f"{_holder_line('Technical operator', people)} is checking the same submission attempt.", sentence="No new Submit or retry action.", stage="SIGN_AND_SUBMIT",
			holder=ns.holder(TECHNICAL, people), since=ns.since(attempt.received_at, labels.datetime_label(attempt.received_at)) if attempt else None, primary_action="view_status"), "DBN", ns.holder(TECHNICAL, people)["display"])
	if "BDS_ADDENDUM_REVIEW_REQUIRED" in codes:
		blockers = [b for b in ns.blockers_of(guard) if b["reason_code"] == "BDS_ADDENDUM_REVIEW_REQUIRED"]
		return result(ns.answer(ns.KIND_BLOCKED, headline=f"Review the changed {_change_label(ws.tender)} and acknowledge the current addendum before submitting.", stage="BID_PREPARATION", blockers=blockers, primary_action="review_addendum"), "BNN", viewer)
	if still_preparing:
		if "BDS_PORTAL_INFORMATION_UNAVAILABLE" in codes:
			return result(ns.answer(ns.KIND_YOUR_TURN, headline="Continue your saved bid. Submission is blocked until supplier portal information is restored.", stage="BID_PREPARATION", primary_action="continue_bid",
				fixes=[ns.fix("Continue saved bid", responsibility=SUPPLIER, kind=ns.FIX_ROUTE, fix_id="continue_bid", primary=True)]), "CNN", viewer)
		task = next(key for key, t in tasks.items() if key != readiness.REVIEW_TASK and t.status != "Complete")
		label = ctx.model.task(task).label
		if replacement and signatory:
			headline = f"Finish and submit the replacement before the deadline. Version {int(current.version_number)} remains submitted."
		else:
			headline = f"Continue the {label[:1].lower() + label[1:]} task."
		return result(ns.answer(ns.KIND_YOUR_TURN, headline=headline, sentence=f"Deadline {deadline_label}.", stage="BID_PREPARATION", primary_action="continue_bid",
			fixes=[ns.fix("Continue bid", responsibility=SUPPLIER, kind=ns.FIX_ROUTE, fix_id=f"continue_bid:{task}", target={"task": task}, primary=True)]), "CNN", viewer)
	# ready to submit
	if "BDS_SIGNATORY_REQUIRED" in codes:
		people = signatory_names(ctx, at)
		return result(ns.answer(ns.KIND_WAITING, headline=f"{_holder_line('Authorised Signatory', people)} must submit this bid.", stage="SIGN_AND_SUBMIT", holder=ns.holder(authz.SIGNATORY, people), primary_action="review_bid"), "DCN", ns.holder(authz.SIGNATORY, people)["display"])
	if "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED" in codes:
		people = responsibility_holders(RELEASE)
		return result(ns.answer(ns.KIND_WAITING, headline=f"{_holder_line('Release operator', people)} holds the verified production-submission release.", sentence="Your bid remains saved and no receipt exists.", stage="SIGN_AND_SUBMIT", holder=ns.holder(RELEASE, people)), "DBN", ns.holder(RELEASE, people)["display"])
	if "BDS_SIGNATURE_UNAVAILABLE" in codes or "BDS_SUBMISSION_SERVICE_UNAVAILABLE" in codes:
		people = responsibility_holders(TECHNICAL)
		what = "digital signing" if "BDS_SIGNATURE_UNAVAILABLE" in codes else "electronic submission"
		return result(ns.answer(ns.KIND_WAITING, headline=f"{_holder_line('Technical operator', people)} is restoring {what}.", sentence="Your bid remains saved.", stage="SIGN_AND_SUBMIT", holder=ns.holder(TECHNICAL, people)), "DBN", ns.holder(TECHNICAL, people)["display"])
	if "BDS_PORTAL_INFORMATION_UNAVAILABLE" in codes:
		people = _cfg_holders()
		return result(ns.answer(ns.KIND_WAITING, headline=f"{_holder_line('CFG System Manager', people)} is restoring supplier portal information.", sentence="Your ready Draft remains saved.", stage="SIGN_AND_SUBMIT", holder=ns.holder("CFG System Manager", people)), "DBN", ns.holder("CFG System Manager", people)["display"])
	if "BDS_SIGNATORY_CERTIFICATE_REQUIRED" in codes:
		blockers = [b for b in ns.blockers_of(guard) if b["reason_code"] == "BDS_SIGNATORY_CERTIFICATE_REQUIRED"]
		return result(ns.answer(ns.KIND_BLOCKED, headline="Obtain a valid digital signature certificate from an approved licensed certifying agency before submitting.", sentence="Your bid remains saved.", stage="SIGN_AND_SUBMIT", blockers=blockers, primary_action="check_certificate"), "DBN", viewer)
	attempt = _latest_attempt(ws.name)
	if attempt and attempt.status == "Rejected" and (not current or attempt.creation > frappe.db.get_value("Bid Submission Version", ws.current_submission_version, "creation")):
		fixes = [ns.fix("Try confirmation again", responsibility=authz.SIGNATORY, kind=ns.FIX_COMMAND, fix_id="submit_bid", primary=True), ns.fix("Contact support", responsibility="Supplier support", kind=ns.FIX_ROUTE, fix_id="contact_support")]
		blocker = ns.blocker(ns.guard(False, reason_code="BDS_CUSTODY_REJECTED", message=MESSAGES["BDS_CUSTODY_REJECTED"], figures={"rejection_reference": cstr(attempt.rejection_reference)}, fixes=fixes))
		return result(ns.answer(ns.KIND_BLOCKED, headline="The tender box rejected this attempt; no bid was submitted.", stage="SIGN_AND_SUBMIT", blockers=[blocker], primary_action="submit_bid"), "DBN", viewer)
	if replacement:
		return result(ns.answer(ns.KIND_YOUR_TURN, headline=f"Finish and submit the replacement before the deadline. Version {int(current.version_number)} remains submitted.", stage="BID_PREPARATION", primary_action="review_bid",
			fixes=[ns.fix("Review bid", responsibility=authz.SIGNATORY, kind=ns.FIX_ROUTE, fix_id="review_bid", primary=True)]), "CNN", viewer)
	return result(ns.answer(ns.KIND_YOUR_TURN, headline=f"Review, sign and submit this bid before {deadline_label}.", stage="SIGN_AND_SUBMIT", primary_action="review_bid",
		fixes=[ns.fix("Review bid", responsibility=authz.SIGNATORY, kind=ns.FIX_ROUTE, fix_id="review_bid", primary=True)]), "DCN", viewer)

