# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §5.9 / §5.10 / §10.17 — the server-derived next step and
Tender journey for the signed-in actor (plan D26; KT-STD-001 v1.8 §3B).

One function, `guidance()`, answers "whose turn is it and what happens next"
for one Tender, one actor and one screen context. The browser draws the
answer with the shared core components and never infers it from a badge or
a disabled control (§11.1(4)).

The five formal stages (§5.9) are the journey; the three preparation tasks
are sections of PREPARE, channel confirmations are work inside PUBLICATION,
and addenda, clarifications and cancellation are work inside
OPEN_MANAGEMENT. The marker tuple and the next-step stage always agree
(§10.17): a Your-turn-blocked answer, a segregation wait on a System Manager
and a stopped Version mark the current stage Blocked.

Headlines follow §10.17. Where a §10.17 headline quotes fixture facts the
server cannot know generically, the server states the same fact from the
record (the departures are registered in the fidelity guidance table).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import next_step as ns
from kentender_procurement.tenders.services import handoffs, serializer
from kentender_procurement.tenders.services.tender_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PROCUREMENT_OFFICER,
)

PREPARE = "PREPARE"
HOPF_APPROVAL = "HOPF_APPROVAL"
AO_AUTHORISATION = "AO_AUTHORISATION"
PUBLICATION = "PUBLICATION"
OPEN_MANAGEMENT = "OPEN_MANAGEMENT"
STAGES = (
	(PREPARE, "Prepare Tender"),
	(HOPF_APPROVAL, "HOPF approval"),
	(AO_AUTHORISATION, "AO publication authorisation"),
	(PUBLICATION, "Confirm publication"),
	(OPEN_MANAGEMENT, "Manage open Tender"),
)
SYSTEM_MANAGER = "System Manager"
CONTEXTS = ("record", "editor", "review", "publication", "addendum", "clarification", "cancellation")


# --------------------------------------------------------------------------
# people
# --------------------------------------------------------------------------


def _name(user: str) -> str:
	return handoffs.full_name(user)


def _holders(role: str, *, exclude: tuple[str, ...] = ()) -> list[str]:
	return [u for u in handoffs.users_with_site_role(role) if u not in exclude]


def _names(users: list[str]) -> str:
	return ", ".join(_name(u) for u in users)


def _since(value) -> dict[str, Any] | None:
	return ns.since(value, serializer.fmt_datetime_short(value)) if value else None


def _since_text(value) -> str:
	return f" since {serializer.fmt_datetime_short(value)}" if value else ""


def _subject(users: list[str], role: str, *, role_first: bool = False) -> str:
	"""The holder as a sentence subject (§10.17): "Charles Mutiso, Head of
	Procurement Function," — or, role first, "Accounting Officer Amina
	Hassan". Two eligible people are both named; more than two, or none,
	name the responsibility without inventing a person (§5.9)."""
	names = [_name(u) for u in users]
	if names and len(names) <= 2:
		joined = " or ".join(names)
		return f"{role} {joined}" if role_first else f"{joined}, {role},"
	return f"{'An' if role[:1] in 'AEIOU' else 'A'} {role}"


def _display(users: list[str], role: str) -> str:
	"""The tracker's holder: up to two names, otherwise the responsibility."""
	return " or ".join(_name(u) for u in users) if users and len(users) <= 2 else role


# --------------------------------------------------------------------------
# answers
# --------------------------------------------------------------------------


def _turn(stage: str, headline: str, *, holder_users: list[str], role: str, primary: str = "", sentence: str = "", since=None) -> dict[str, Any]:
	return ns.answer(ns.KIND_YOUR_TURN, headline=headline, sentence=sentence, stage=stage, holder=ns.holder(role, [_name(u) for u in holder_users]), since=_since(since), primary_action=primary)


def _blocked(stage: str, headline: str, *, holder_users: list[str], role: str, blockers: list[dict[str, Any]], sentence: str = "", since=None) -> dict[str, Any]:
	return ns.answer(ns.KIND_BLOCKED, headline=headline, sentence=sentence, stage=stage, holder=ns.holder(role, [_name(u) for u in holder_users]), since=_since(since), blockers=blockers)


def _waiting(stage: str, headline: str, *, holder_users: list[str], role: str, since=None) -> dict[str, Any]:
	return ns.answer(ns.KIND_WAITING, headline=headline, stage=stage, holder=ns.holder(role, [_name(u) for u in holder_users]), since=_since(since))


def _done(stage: str, headline: str) -> dict[str, Any]:
	return ns.answer(ns.KIND_DONE, headline=headline, stage=stage)


def _refusal(reason_code: str, message: str, *, fixes: list[dict[str, Any]], figures: dict[str, Any] | None = None, headline: str = "") -> dict[str, Any]:
	return ns.guard(False, reason_code=reason_code, message=message, headline=headline or message, figures=figures or {}, fixes=fixes)


def _journey(stage: str, *, blocked: bool = False, holder_display: str = "", complete: bool = False) -> dict[str, Any]:
	return ns.journey(STAGES, current="" if complete else stage, blocked=blocked, holder_display=holder_display, complete=complete, reduced_style=ns.REDUCED_POSITION)


# --------------------------------------------------------------------------
# context
# --------------------------------------------------------------------------


def _version(root, name: str = ""):
	name = name or cstr(root.current_version)
	return frappe.get_doc("Tender Version", name) if name else None


def _open_tasks(root, task_type: str = "", subject_id: str = "") -> list[Any]:
	filters: dict[str, Any] = {"tender": root.name, "status": "Open"}
	if task_type:
		filters["task_type"] = task_type
	if subject_id:
		filters["subject_id"] = subject_id
	return frappe.get_all("Tender Task", filters=filters, fields=["name", "task_type", "business_role", "holder", "sender", "comment", "subject_type", "subject_id", "creation", "tender_version"], order_by="creation asc")


def _eligible(role: str, version, blocked_columns: tuple[str, ...]) -> list[str]:
	exclude = tuple(cstr(version.get(c)) for c in blocked_columns if version is not None and version.get(c))
	return _holders(role, exclude=exclude)


# --------------------------------------------------------------------------
# PREPARE
# --------------------------------------------------------------------------


def _preparer(version) -> list[str]:
	user = cstr(version.prepared_by) if version is not None else ""
	return [user] if user else _holders(ROLE_PROCUREMENT_OFFICER)


def _returned_by(version) -> tuple[str, str, Any]:
	"""(returned_by, affected task, returned_at) when this Draft copies a
	returned Version."""
	if version is None or not version.predecessor_version:
		return "", "", None
	row = frappe.db.get_value("Tender Version", version.predecessor_version, ["status", "returned_by", "return_affected_task", "returned_at"], as_dict=True)
	if not row or row.status != "Returned":
		return "", "", None
	return cstr(row.returned_by), cstr(row.return_affected_task), row.returned_at


def _prepare(root, version, *, actor: str, roles: dict[str, bool], context: str, task: str, review_summary: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
	preparers = _preparer(version)
	returned_by, affected, returned_at = _returned_by(version)
	# §5.9: since the Draft or return event
	since = returned_at or (version.prepared_at if version is not None else None) or root.creation
	holder_display = _display(preparers, ROLE_PROCUREMENT_OFFICER)
	if roles.get("officer"):
		if context == "review" and review_summary is not None:
			must_fix = review_summary.get("must_fix") or []
			if must_fix:
				blockers = [
					ns.blocker(_refusal(
						"TND_MUST_FIX", f["message"], figures={"finding": f.get("finding_code"), "field": f.get("field")},
						fixes=[ns.fix(f.get("link_label") or "Review the Tender", responsibility=ROLE_PROCUREMENT_OFFICER, kind=ns.FIX_ROUTE, fix_id=f"finding:{f.get('field') or f.get('task')}", target={"task": f.get("task"), "field": f.get("field")}, primary=i == 0)],
					))
					for i, f in enumerate(must_fix)
				]
				headline = must_fix[0]["message"] if len(must_fix) == 1 else f"Fix the {len(must_fix)} listed items before submitting."
				answer = _blocked(PREPARE, headline, holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, blockers=blockers)
				return answer, _journey(PREPARE, blocked=True, holder_display=holder_display)
			answer = _turn(PREPARE, "Submit this Tender for approval.", holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, primary="submit_for_approval")
			return answer, _journey(PREPARE, holder_display=holder_display)
		if returned_by:
			topic = (affected or "Supplier and contract requirements").lower()
			answer = _turn(PREPARE, f"Address {_name(returned_by)}'s return comment about {topic}.", holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, primary="review_tender")
		elif task == "requirements":
			answer = _turn(PREPARE, "Set supplier evidence and contract terms.", holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, primary="review_tender")
		else:
			answer = _turn(PREPARE, "Set the Tender dates, security and meeting details.", holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, primary="continue")
		return answer, _journey(PREPARE, holder_display=holder_display)
	answer = _waiting(PREPARE, f"{_subject(preparers, ROLE_PROCUREMENT_OFFICER)} is preparing this Tender{_since_text(since)}.", holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, since=since)
	return answer, _journey(PREPARE, holder_display=holder_display)


def _correction(root, version, *, actor: str, roles: dict[str, bool]) -> tuple[dict[str, Any], dict[str, Any]]:
	from kentender_procurement.tenders.services import correction, handoff_gateway

	author = correction.requisition_author(root)
	authors = [author] if author else []
	successor = handoff_gateway.successors(plan_item_id=cstr(root.plan_item_id), user=actor) if roles.get("officer") else []
	if successor:
		preparers = _preparer(version)
		number = cstr(successor[0].get("requisition_version_number") or "")
		label = f"authorised Requisition Version {number}" if number else f"the authorised corrected requisition {cstr(successor[0].get('requisition_reference'))}"
		answer = _turn(PREPARE, f"Start a corrected Tender Version from {label}.", holder_users=preparers, role=ROLE_PROCUREMENT_OFFICER, primary="start_corrected_tender_version")
		return answer, _journey(PREPARE, holder_display=_display(preparers, ROLE_PROCUREMENT_OFFICER))
	since = version.stopped_at if version is not None else None
	answer = _waiting(PREPARE, f"{_subject(authors, ROLE_DEPARTMENTAL_AUTHOR)} is correcting the requisition{_since_text(since)}.", holder_users=authors, role=ROLE_DEPARTMENTAL_AUTHOR, since=since)
	return answer, _journey(PREPARE, blocked=True, holder_display=_display(authors, ROLE_DEPARTMENTAL_AUTHOR))


# --------------------------------------------------------------------------
# HOPF_APPROVAL / AO_AUTHORISATION
# --------------------------------------------------------------------------


SEGREGATION_SENTENCES = {
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION: "You cannot approve a Tender Version you prepared or submitted.",
	ROLE_ACCOUNTING_OFFICER: "You cannot authorise publication of a Tender Version you prepared, submitted or approved as Head of Procurement Function.",
}


def _decision(root, version, *, actor: str, roles: dict[str, bool], stage: str, role: str, role_key: str, columns: tuple[str, ...], headline_turn: str, primary: str, since, doing: str) -> tuple[dict[str, Any], dict[str, Any]]:
	eligible = _eligible(role, version, columns)
	conflicted = roles.get(role_key) and actor not in eligible
	if roles.get(role_key) and not conflicted:
		answer = _turn(stage, headline_turn, holder_users=[actor], role=role, primary=primary)
		return answer, _journey(stage, holder_display=_name(actor))
	# §10.7 / §10.8 segregation text travels in the one guidance line (§10.17
	# replaces the separate segregation warning), as its sentence
	sentence = SEGREGATION_SENTENCES[role] if conflicted else ""
	if not eligible:
		# §5.10 TND_SOD_BLOCKED / §10.17: a System Manager must assign an eligible holder.
		title = "Head of Procurement Function" if role == ROLE_HEAD_OF_PROCUREMENT_FUNCTION else "Accounting Officer"
		answer = ns.answer(
			ns.KIND_WAITING, headline=f"A System Manager must assign an eligible {title} to decide this Version.", sentence=sentence, stage=stage,
			holder=ns.holder(SYSTEM_MANAGER, []),
		)
		return answer, _journey(stage, blocked=True, holder_display=SYSTEM_MANAGER)
	answer = _waiting(stage, f"{_subject(eligible, role)} is {doing}{_since_text(since)}.", holder_users=eligible, role=role, since=since)
	answer["sentence"] = sentence
	return answer, _journey(stage, holder_display=_display(eligible, role))


# --------------------------------------------------------------------------
# PUBLICATION
# --------------------------------------------------------------------------


def _publication(root, version, *, actor: str, roles: dict[str, bool]) -> tuple[dict[str, Any], dict[str, Any]]:
	hopfs = _holders(ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	rows = frappe.get_all("Tender Channel Confirmation", filters={"subject_type": "Tender package", "subject_id": cstr(root.publication)}, fields=["channel_label", "status"], order_by="creation asc")
	outstanding = [r.channel_label for r in rows if r.status != "Confirmed"]
	confirmed = len(rows) - len(outstanding)
	authorised_at = frappe.db.get_value("Tender Publication", root.publication, "authorised_at") if root.publication else None
	if roles.get("hopf"):
		channels = " and ".join(outstanding) if len(outstanding) <= 2 else ", ".join(outstanding[:-1]) + " and " + outstanding[-1]
		answer = _turn(PUBLICATION, f"Confirm publication through {channels}; {confirmed} of {len(rows)} channels are confirmed.", holder_users=[actor], role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, primary="confirm_publication_channel")
		return answer, _journey(PUBLICATION, holder_display=_name(actor))
	answer = _waiting(PUBLICATION, f"{_subject(hopfs, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)} is confirming publication{_since_text(authorised_at)}.", holder_users=hopfs, role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, since=authorised_at)
	return answer, _journey(PUBLICATION, holder_display=_display(hopfs, ROLE_HEAD_OF_PROCUREMENT_FUNCTION))


def evidence_rejected(channel_label: str, *, stage: str = PUBLICATION) -> dict[str, Any]:
	"""§10.17 DES-08 invalid evidence — the blocked answer a failed
	confirmation returns in its error detail (the entered values stay)."""
	return ns.answer(
		ns.KIND_BLOCKED, headline=f"{channel_label} evidence could not be accepted.", stage=stage,
		blockers=[ns.blocker(_refusal("TND_PUBLICATION_EVIDENCE_INVALID", f"{channel_label} evidence could not be accepted.", fixes=[
			ns.fix("Choose evidence file", responsibility=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, kind=ns.FIX_FOCUS, fix_id="choose_evidence_file", target="evidence_file", primary=True),
			ns.fix("Confirm publication", responsibility=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, kind=ns.FIX_COMMAND, fix_id="confirm_publication_channel"),
		]))],
	)


def confirmation_conflict(channel_label: str = "", *, stage: str = PUBLICATION) -> dict[str, Any]:
	"""§10.17 DES-08 conflicting confirmation: View confirmation for the
	confirmed channel, then Confirm publication on the outstanding ones."""
	answer = ns.answer(ns.KIND_YOUR_TURN, headline="Continue with the channels still awaiting confirmation.", stage=stage, primary_action="confirm_publication_channel")
	if channel_label:
		answer["fixes"] = [ns.fix(f"View confirmation for {channel_label}", responsibility=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, kind=ns.FIX_COMMAND, fix_id="view_confirmation", target={"channel_label": channel_label})]
	return answer


# --------------------------------------------------------------------------
# OPEN_MANAGEMENT
# --------------------------------------------------------------------------


def _failed_notice_blocker(root) -> dict[str, Any] | None:
	failed = frappe.db.count("Tender Candidate Notice", {"tender": root.name, "status": "Failed"})
	if not failed:
		return None
	return _refusal(
		"TND_NOTICE_DELIVERY_FAILED", f"{failed} candidate notice{'s' if failed != 1 else ''} failed delivery; the Tender remains open.", figures={"failed": failed},
		fixes=[ns.fix("Retry notice", responsibility=f"{ROLE_HEAD_OF_PROCUREMENT_FUNCTION} or {ROLE_PROCUREMENT_OFFICER}", kind=ns.FIX_COMMAND, fix_id="retry_notice", primary=True)],
	)


def _change(reference: dict[str, Any], revised: str) -> str:
	"""§10.17 DES-10 material headline subject: "Increasing the business
	laptops quantity from 250 to 300" or "Changing {reference} from … to …"."""
	current = cstr(reference.get("value"))
	if cstr(reference.get("key")).startswith("goods:"):
		before, after = _number(current), _number(revised)
		if before is not None and after is not None and before != after:
			item = reference["label"].split(" — ")[0].lower()
			verb = "Increasing" if after > before else "Reducing"
			return f"{verb} the {item} quantity from {_plain(before)} to {_plain(after)}"
	return f"Changing {reference['label'].split(' — ')[-1].lower()} from {current} to {revised}"


def _short_change(reference: dict[str, Any], revised: str) -> str:
	""""The 250-to-300 Each addendum" (§10.17 DES-10 after the review closes)."""
	current = cstr(reference.get("value"))
	unit = current.split(" ", 1)[1] if " " in current and _number(current) is not None else ""
	if unit and revised.endswith(f" {unit}"):
		current = current[: -len(unit) - 1]
	return f"The {current}-to-{revised} addendum"


def _proposal(reference: dict[str, Any], revised: str) -> str:
	""""the proposed quantity increase" (§10.17 DES-12 review request)."""
	if cstr(reference.get("key")).startswith("goods:"):
		before, after = _number(cstr(reference.get("value"))), _number(revised)
		if before is not None and after is not None and before != after:
			return f"the proposed quantity {'increase' if after > before else 'reduction'}"
	return f"the proposed change to {reference['label'].split(' — ')[-1].lower()}"


def _number(text: str):
	head = cstr(text).split(" ", 1)[0].replace(",", "")
	try:
		return float(head)
	except ValueError:
		return None


def _plain(value: float) -> str:
	return f"{int(value):,}" if float(value).is_integer() else f"{value:,}"


def _answer_holder(answer: dict[str, Any]) -> str:
	holder = answer.get("holder") or {}
	people = holder.get("people") or []
	return " or ".join(people) if people and len(people) <= 2 else cstr(holder.get("role"))


def _material_draft(root, addendum: dict[str, Any]) -> bool:
	from kentender_procurement.tenders.services import addenda

	if cstr(addendum.get("status")) != "Draft":
		return False
	ref = {r["key"]: r for r in addenda.affected_references(root)}.get(cstr(addendum.get("affected_reference_key")))
	return bool(ref and ref["material"])


def _review_requested_at(root, addendum_name: str):
	return frappe.db.get_value("Tender Decision", {"tender": root.name, "decision": "Request cancellation review", "subject_id": addendum_name}, "decided_at", order_by="decided_at desc")


def _addendum_answer(root, addendum: dict[str, Any], *, actor: str, roles: dict[str, bool]) -> dict[str, Any] | None:
	"""§10.17 DES-10 rows for one addendum. The drafter (Procurement Officer
	or HOPF) and the issuing HOPF get their turn on it; any other reader gets
	the truthful waiting or done answer for the item (§5.9)."""
	from kentender_procurement.tenders.services import addenda

	status = cstr(addendum.get("status"))
	drafter = roles.get("officer") or roles.get("hopf")
	hopfs = _holders(ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	aos = _holders(ROLE_ACCOUNTING_OFFICER)
	reference = cstr(addendum.get("addendum_reference"))
	drafted_by = [cstr(addendum.get("drafted_by"))] if addendum.get("drafted_by") else _holders(ROLE_PROCUREMENT_OFFICER)
	if status == "Draft":
		catalogue = {r["key"]: r for r in addenda.affected_references(root)}
		ref = catalogue.get(cstr(addendum.get("affected_reference_key")))
		review = cstr(addendum.get("cancellation_review_status"))
		if ref and ref["material"]:
			revised = cstr(addendum.get("revised_value"))
			if review == "Requested":
				since = _review_requested_at(root, addendum["name"])
				if roles.get("ao"):
					return None  # the AO's turn is the review itself (_open)
				return _waiting(OPEN_MANAGEMENT, f"{_subject(aos, ROLE_ACCOUNTING_OFFICER, role_first=True)} is considering cancellation of {root.tender_reference}{_since_text(since)}.", holder_users=aos, role=ROLE_ACCOUNTING_OFFICER, since=since)
			if not drafter:
				return _waiting(OPEN_MANAGEMENT, f"{_subject(drafted_by, ROLE_PROCUREMENT_OFFICER)} is deciding what to do with a material addendum proposal.", holder_users=drafted_by, role=ROLE_PROCUREMENT_OFFICER)
			discard = ns.fix("Discard addendum draft", responsibility=ROLE_PROCUREMENT_OFFICER, kind=ns.FIX_COMMAND, fix_id="discard_addendum_draft")
			figures = {"affected_reference": ref["label"], "current": ref["value"], "proposed": revised}
			ao = _names(aos) if len(aos) <= 2 else ""
			if review == "Closed":
				closer = frappe.db.get_value("Tender Decision", {"tender": root.name, "decision": "Close cancellation review", "subject_id": addendum["name"]}, "actor", order_by="decided_at desc")
				headline = f"{_short_change(ref, revised)} remains unissuable; {_name(closer) if closer else 'the Accounting Officer'} closed the cancellation review with a recorded reason."
				blockers = [ns.blocker(_refusal("TND_ADDENDUM_MATERIAL", headline, figures=figures, fixes=[{**discard, "primary": True}]))]
			else:
				headline = f"{_change(ref, revised)} cannot be issued as an addendum."
				label = f"Ask {ao} (Accounting Officer) to consider cancellation" if ao else "Ask the Accounting Officer to consider cancellation"
				ask = ns.fix(label, responsibility=ROLE_ACCOUNTING_OFFICER, person=ao, kind=ns.FIX_COMMAND, fix_id="request_cancellation_review", primary=True)
				blockers = [ns.blocker(_refusal("TND_ADDENDUM_MATERIAL", headline, figures=figures, fixes=[ask, discard]))]
			return _blocked(OPEN_MANAGEMENT, headline, holder_users=[actor], role=ROLE_PROCUREMENT_OFFICER, blockers=blockers)
		if drafter:
			return _turn(OPEN_MANAGEMENT, "Submit the non-material addendum for issue.", holder_users=[actor], role=ROLE_PROCUREMENT_OFFICER, primary="submit_addendum_for_issue")
		since = addendum.get("drafted_at")
		return _waiting(OPEN_MANAGEMENT, f"{_subject(drafted_by, ROLE_PROCUREMENT_OFFICER)} is preparing addendum {reference}{_since_text(since)}.", holder_users=drafted_by, role=ROLE_PROCUREMENT_OFFICER, since=since)
	if status == "Awaiting issue":
		if roles.get("hopf"):
			return _turn(OPEN_MANAGEMENT, "Decide whether to issue this addendum.", holder_users=[actor], role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, primary="issue_addendum")
		submitted = addendum.get("submitted_at")
		return _waiting(OPEN_MANAGEMENT, f"{_subject(hopfs, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)} is deciding addendum {reference}{_since_text(submitted)}.", holder_users=hopfs, role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, since=submitted)
	if status == "Awaiting publication confirmation":
		if roles.get("hopf"):
			return _turn(OPEN_MANAGEMENT, f"Confirm publication of {reference} through the remaining original channels.", holder_users=[actor], role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, primary="confirm_addendum_channel")
		decided = addendum.get("issue_decided_at")
		return _waiting(OPEN_MANAGEMENT, f"{_subject(hopfs, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)} is confirming publication of {reference}{_since_text(decided)}.", holder_users=hopfs, role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, since=decided)
	if status == "Issued":
		rows = frappe.get_all("Tender Channel Confirmation", filters={"subject_type": "Addendum", "subject_id": addendum["name"], "status": "Confirmed"}, fields=["attested_by", "attested_at"], order_by="attested_at desc", limit=1)
		if rows:
			return _done(OPEN_MANAGEMENT, f"{_name(rows[0].attested_by)} completed addendum publication on {serializer.fmt_datetime_short(rows[0].attested_at)}.")
	if status in ("Discarded", "Returned"):
		return _done(OPEN_MANAGEMENT, f"Addendum {reference} was {status.lower()}; the published Tender is unchanged.")
	return None


def _clarification_answer(root, clarification: dict[str, Any], *, actor: str, roles: dict[str, bool]) -> dict[str, Any] | None:
	"""§10.17 DES-11 rows for one clarification; any reader who does not
	answer clarifications gets the truthful waiting or done answer (§5.9)."""
	status = cstr(clarification.get("status"))
	holder = roles.get("officer") or roles.get("hopf")
	role = ROLE_PROCUREMENT_OFFICER if roles.get("officer") else ROLE_HEAD_OF_PROCUREMENT_FUNCTION
	answerers = _holders(ROLE_PROCUREMENT_OFFICER)
	if status == "Awaiting response":
		if holder:
			return _turn(OPEN_MANAGEMENT, "Send the answer to all registered candidates.", holder_users=[actor], role=role, primary="send_response")
		since = clarification.get("received_at")
		return _waiting(OPEN_MANAGEMENT, f"{_subject(answerers, ROLE_PROCUREMENT_OFFICER)} is answering this clarification{_since_text(since)}.", holder_users=answerers, role=ROLE_PROCUREMENT_OFFICER, since=since)
	if status == "Awaiting addendum":
		if holder:
			headline = "Issue an addendum before sending this answer."
			prepare = ns.fix("Prepare addendum", responsibility=f"{ROLE_PROCUREMENT_OFFICER} or {ROLE_HEAD_OF_PROCUREMENT_FUNCTION}", kind=ns.FIX_COMMAND, fix_id="prepare_addendum", primary=True)
			return _blocked(OPEN_MANAGEMENT, headline, holder_users=[actor], role=role, blockers=[ns.blocker(_refusal("TND_CLARIFICATION_ADDENDUM_REQUIRED", headline, figures={"clarification": clarification["name"]}, fixes=[prepare]))])
		return _waiting(OPEN_MANAGEMENT, f"{_subject(answerers, ROLE_PROCUREMENT_OFFICER)} is preparing the addendum this answer needs.", holder_users=answerers, role=ROLE_PROCUREMENT_OFFICER)
	if status == "Answered":
		failed = frappe.db.count("Tender Candidate Notice", {"subject_id": clarification["name"], "status": "Failed"})
		if failed and holder:
			headline = f"{failed} candidate notice{'s' if failed != 1 else ''} failed delivery; the Tender remains open."
			retry = ns.fix("Retry notice", responsibility=f"{ROLE_HEAD_OF_PROCUREMENT_FUNCTION} or {ROLE_PROCUREMENT_OFFICER}", kind=ns.FIX_COMMAND, fix_id="retry_notice", primary=True)
			return _blocked(OPEN_MANAGEMENT, headline, holder_users=[actor], role=role, blockers=[ns.blocker(_refusal("TND_NOTICE_DELIVERY_FAILED", headline, figures={"failed": failed}, fixes=[retry]))])
		return _done(OPEN_MANAGEMENT, f"{_name(cstr(clarification.get('responded_by')))} answered this clarification on {serializer.fmt_datetime_short(clarification.get('responded_at'))}.")
	if status == "Closed with reason":
		return _done(OPEN_MANAGEMENT, "This clarification was closed with a recorded reason.")
	return None


def _open(root, version, *, actor: str, roles: dict[str, bool], context: str, subject: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
	holder_display = ""
	if context == "addendum" and subject:
		answer = _addendum_answer(root, subject, actor=actor, roles=roles)
		if answer:
			# §10.17 DES-10: a material proposal keeps O blocked for every reader
			return answer, _journey(OPEN_MANAGEMENT, blocked=answer["kind"] == ns.KIND_BLOCKED or _material_draft(root, subject), holder_display=_answer_holder(answer))
	if context == "clarification" and subject:
		answer = _clarification_answer(root, subject, actor=actor, roles=roles)
		if answer:
			return answer, _journey(OPEN_MANAGEMENT, blocked=answer["kind"] == ns.KIND_BLOCKED, holder_display=_answer_holder(answer))
	# the AO's cancellation review (§5.11) comes before the optional actions
	reviews = _open_tasks(root, handoffs.CANCELLATION_REVIEW)
	if roles.get("ao") and reviews and context in ("record", "cancellation", "addendum"):
		from kentender_procurement.tenders.services import addenda

		proposal = frappe.db.get_value("Tender Addendum", reviews[0].subject_id, ["name", "affected_reference_key", "revised_value"], as_dict=True)
		ref = {r["key"]: r for r in addenda.affected_references(root)}.get(cstr(proposal.affected_reference_key)) if proposal else None
		what = _proposal(ref, cstr(proposal.revised_value)) if ref else "the proposed change"
		answer = _turn(OPEN_MANAGEMENT, f"Consider the request to cancel {root.tender_reference} because {what} cannot be issued by addendum.", holder_users=[actor], role=ROLE_ACCOUNTING_OFFICER, primary="cancel_tender", since=_review_requested_at(root, cstr(reviews[0].subject_id)))
		answer["fixes"] = [
			ns.fix("Cancel Tender", responsibility=ROLE_ACCOUNTING_OFFICER, kind=ns.FIX_COMMAND, fix_id="cancel_tender", primary=True),
			ns.fix("Close cancellation review", responsibility=ROLE_ACCOUNTING_OFFICER, kind=ns.FIX_COMMAND, fix_id="close_cancellation_review", target={"addendum": cstr(reviews[0].subject_id)}),
		]
		return answer, _journey(OPEN_MANAGEMENT, holder_display=_name(actor))
	if context in ("addendum", "clarification") and subject:
		# a reader who holds nothing on this item (§5.9): the item's done line
		return ns.not_involved(OPEN_MANAGEMENT), _journey(OPEN_MANAGEMENT)
	# the actor's own pending items (§5.9: Your turn on that exact item)
	candidates: list[dict[str, Any]] = []
	if roles.get("officer") or roles.get("hopf"):
		blocker = _failed_notice_blocker(root)
		if blocker:
			role = ROLE_HEAD_OF_PROCUREMENT_FUNCTION if roles.get("hopf") else ROLE_PROCUREMENT_OFFICER
			candidates.append(_blocked(OPEN_MANAGEMENT, blocker["headline"], holder_users=[actor], role=role, blockers=[ns.blocker(blocker)]))
		for row in frappe.get_all("Tender Clarification", filters={"tender": root.name, "status": ("in", ("Awaiting response", "Awaiting addendum"))}, fields=["name", "status", "received_at"], order_by="received_at asc", limit=1):
			if row.status == "Awaiting response":
				candidates.append(_turn(OPEN_MANAGEMENT, f"Respond to the supplier clarification received {serializer.fmt_datetime_short(row.received_at)}.", holder_users=[actor], role=ROLE_PROCUREMENT_OFFICER, primary="respond_clarification"))
		for row in frappe.get_all("Tender Addendum", filters={"tender": root.name, "status": ("in", ("Awaiting issue", "Awaiting publication confirmation"))}, fields=["name", "status", "addendum_reference"], limit=1):
			if roles.get("hopf"):
				candidates.append(_addendum_answer(root, {**row}, actor=actor, roles=roles))
	candidates = [c for c in candidates if c]
	if candidates:
		answer = ns.choose(*candidates)
		return answer, _journey(OPEN_MANAGEMENT, blocked=answer["kind"] == ns.KIND_BLOCKED, holder_display=_name(actor))
	if reviews and not roles.get("ao") and (roles.get("officer") or roles.get("hopf")):
		# §5.9: while the AO considers cancellation, the procurement side waits
		aos = _holders(ROLE_ACCOUNTING_OFFICER)
		since = _review_requested_at(root, cstr(reviews[0].subject_id))
		answer = _waiting(OPEN_MANAGEMENT, f"{_subject(aos, ROLE_ACCOUNTING_OFFICER, role_first=True)} is considering cancellation of {root.tender_reference}{_since_text(since)}.", holder_users=aos, role=ROLE_ACCOUNTING_OFFICER, since=since)
		return answer, _journey(OPEN_MANAGEMENT, blocked=True, holder_display=_display(aos, ROLE_ACCOUNTING_OFFICER))
	# the available options (§10.17 DES-09): stated as options, never obligations
	if roles.get("hopf"):
		answer = _turn(OPEN_MANAGEMENT, "Prepare an addendum or recommend cancellation if the open Tender needs it.", holder_users=[actor], role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, primary="prepare_addendum", sentence="These are available options, not overdue work.")
	elif roles.get("officer"):
		answer = _turn(OPEN_MANAGEMENT, "Prepare an addendum if the published Tender needs a non-material correction.", holder_users=[actor], role=ROLE_PROCUREMENT_OFFICER, primary="prepare_addendum", sentence="This is an available option, not assigned work.")
	elif roles.get("ao"):
		if context == "cancellation":
			from kentender_procurement.tenders.services import cancellation

			recommendation = cancellation.latest_recommendation(root)
			ground = cstr(frappe.db.get_value("Tender Decision", recommendation, "affected_task")) if recommendation else ""
			label = cancellation.GROUND_LABELS.get(ground, "")
			headline = f"Decide whether to cancel this Tender for {label[0].lower() + label[1:]}." if label else "Decide whether to cancel this Tender on an applicable ground."
			answer = _turn(OPEN_MANAGEMENT, headline, holder_users=[actor], role=ROLE_ACCOUNTING_OFFICER, primary="cancel_tender")
		else:
			answer = _turn(OPEN_MANAGEMENT, "You can cancel this open Tender on an applicable ground.", holder_users=[actor], role=ROLE_ACCOUNTING_OFFICER, primary="cancel_tender", sentence="This is an available option, not an assigned cancellation review.")
	else:
		answer = ns.not_involved(OPEN_MANAGEMENT)
	return answer, _journey(OPEN_MANAGEMENT, holder_display=holder_display)


def _cancelled(root, *, actor: str, roles: dict[str, bool]) -> tuple[dict[str, Any], dict[str, Any]]:
	doc = frappe.db.get_value("Tender Cancellation", root.cancellation, ["name", "decided_by", "decided_at", "ppra_report_due_by", "candidate_notice_due_by"], as_dict=True) if root.cancellation else None
	compliance = _open_tasks(root, handoffs.CANCELLATION_COMPLIANCE)
	holders = [cstr(t.holder) for t in compliance if t.holder]
	if compliance and (actor in holders or (not holders and roles.get("officer"))):
		due = max((d for d in (doc.ppra_report_due_by, doc.candidate_notice_due_by) if d), default=None) if doc else None
		answer = _turn(OPEN_MANAGEMENT, f"Record the outstanding cancellation notices and PPRA report by {serializer.fmt_date_short(due)}." if due else "Record the outstanding cancellation notices and PPRA report.", holder_users=[actor], role=ROLE_PROCUREMENT_OFFICER, primary="record_cancellation_evidence")
		answer["fixes"] = [
			ns.fix("Record cancellation notice evidence", responsibility=ROLE_PROCUREMENT_OFFICER, kind=ns.FIX_COMMAND, fix_id="record_cancellation_notice_evidence"),
			ns.fix("Record PPRA report evidence", responsibility=ROLE_PROCUREMENT_OFFICER, kind=ns.FIX_COMMAND, fix_id="record_ppra_report_evidence"),
		]
		return answer, _journey(OPEN_MANAGEMENT, holder_display=_name(actor))
	if doc:
		return _done(OPEN_MANAGEMENT, f"{_name(doc.decided_by)} cancelled this Tender on {serializer.fmt_datetime_short(doc.decided_at)}."), _journey(OPEN_MANAGEMENT, complete=True)
	return _done(OPEN_MANAGEMENT, "This Tender was cancelled."), _journey(OPEN_MANAGEMENT, complete=True)


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def guidance(root, *, actor: str, roles: dict[str, bool], mode: str, context: str = "record", task: str = "", subject: dict[str, Any] | None = None, review_summary: dict[str, Any] | None = None) -> dict[str, Any]:
	"""`{"next_step", "journey"}` for this actor on this screen (§5.9)."""
	if context not in CONTEXTS:
		raise ValueError(context)
	status = cstr(root.overall_status)
	version = _version(root)
	business = {k: bool(roles.get(k)) for k in ("officer", "hopf", "ao")} if mode != "technical" else {"officer": False, "hopf": False, "ao": False}
	if status == "Draft":
		answer, journey = _prepare(root, version, actor=actor, roles=business, context=context, task=task, review_summary=review_summary)
	elif status == "Requisition correction requested":
		answer, journey = _correction(root, version, actor=actor, roles=business)
	elif status == "Awaiting procurement approval":
		answer, journey = _decision(
			root, version, actor=actor, roles=business, stage=HOPF_APPROVAL, role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, role_key="hopf", columns=("prepared_by", "submitted_by"),
			headline_turn="Decide whether to approve this Tender package.", primary="approve_tender_package", since=version.submitted_at if version is not None else None, doing="reviewing this Tender",
		)
	elif status == "Approved":
		approved = _version(root, cstr(root.approved_version)) or version
		withdrawn = _open_tasks(root, handoffs.REVIEW_WITHDRAWN)
		if withdrawn and business.get("hopf"):
			answer = _turn(AO_AUTHORISATION, "Review the withdrawn publication authorisation and reopen the Tender if it needs correction.", holder_users=[actor], role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, primary="reopen_tender", since=withdrawn[0].creation)
			journey = _journey(AO_AUTHORISATION, holder_display=_name(actor))
		else:
			answer, journey = _decision(
				root, approved, actor=actor, roles=business, stage=AO_AUTHORISATION, role=ROLE_ACCOUNTING_OFFICER, role_key="ao", columns=("prepared_by", "submitted_by", "approved_by"),
				headline_turn="Authorise publication of the approved Tender package.", primary="authorise_publication", since=approved.approved_at if approved is not None else None, doing="deciding publication of this Tender",
			)
	elif status == "Publication authorised":
		answer, journey = _publication(root, version, actor=actor, roles=business)
	elif status == "Published — open":
		answer, journey = _open(root, version, actor=actor, roles=business, context=context, subject=subject)
	elif status == "Submission period ended":
		answer = _done(OPEN_MANAGEMENT, f"The system closed supplier submission at {serializer.fmt_datetime_short(root.submission_deadline)}.")
		journey = _journey(OPEN_MANAGEMENT, complete=True)
	elif status == "Cancelled":
		answer, journey = _cancelled(root, actor=actor, roles=business)
	else:
		answer, journey = ns.not_involved(), _journey(PREPARE)
	if mode == "technical":
		reader = answer if answer["kind"] not in ns.TURN_KINDS else ns.not_involved(answer["stage"])
		answer = ns.for_viewer(answer, technical=True, reader=reader)
	# the journey marker and the next-step stage always agree (§10.17)
	if answer.get("stage") and journey.get("current") and answer["stage"] != journey["current"]:
		raise ValueError(f"next step stage {answer['stage']} disagrees with journey {journey['current']}")
	return {"next_step": answer, "journey": journey}


def task_steps(root, *, actor: str, roles: dict[str, bool], mode: str) -> dict[str, Any]:
	"""The editor's per-task answers (§10.17 DES-03 / DES-04): the Vue shows
	the one for the task on screen; it never composes the wording."""
	return {task: guidance(root, actor=actor, roles=roles, mode=mode, context="editor", task=task)["next_step"] for task in ("details", "requirements")}
