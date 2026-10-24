# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Issues and correspondence (CM-CHG-001 v0.8 sections 5.7, 5.20, 7; plan Phase 8; boards D13, D13-S, D13-C).

An issue is a matter the parties must settle: the inspection findings that call for a replacement, a warranty claim, anything else. It holds the facts, the remedy asked for, the date a reply is wanted and the
thread of messages. A message to the supplier is dispatched through the operation-intent model and is **Unsent** until there is evidence it was delivered: a failed dispatch keeps the same message and retries it,
and nothing claims the supplier received what they did not. The supplier replies on the same issue and proposes a remedy; they never close it. The contract owner (or the head of procurement) resolves it with a
reasoned disposition, which closes that thread; later evidence starts a linked issue. A hold an issue causes names its scope and is lifted only by the issue's own disposition, never by a comment."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, getdate

from kentender_contracts.services import authority, clock, dispatch, events, intents, parties, people, preflight, records, segregation, work
from kentender_contracts.services.errors import fail, invalid

ISSUE = "Contract Issue"
CASE = "Contract Case"
KINDS = ("Delivery issue", "Warranty claim", "Other")


def owner_of(case: str) -> str:
	"""The person who owns the contract's matters: its responsible person, else the head of procurement."""
	doc = frappe.get_doc(CASE, case)
	return doc.responsible_user or next(iter(work.holders(work.HOP)), "")


def get(case: str, number: int):
	name = frappe.db.get_value(ISSUE, {"contract_case": case, "issue_no": number}, "name")
	return frappe.get_doc(ISSUE, name) if name else None


def thread(row) -> list[dict[str, Any]]:
	return records.loads(row.messages_json, [])


def _may_manage(case: str, actor: str) -> None:
	"""The issue's owner, the head of procurement, or a person who prepares contracts for the managing unit."""
	if actor.lower() == cstr(owner_of(case)).lower():
		return
	unit = frappe.db.get_value(CASE, case, "managing_unit") or ""
	if people.holds(actor, "Contract coordination", unit):  # the contract coordinator is the owner's side too (section 6.2)
		return
	preflight.acts_as_preparer(actor, unit)


def _supplier_side(case: str) -> list[str]:
	organisation = frappe.db.get_value(CASE, case, "supplier_organisation")
	return sorted(set(parties.representatives(organisation, clock.now())))


def open_issue(case: str, *, kind: str, title: str, facts: dict[str, Any], requested_remedy: str = "", reply_by: str = "", units: list[str] | None = None, links: dict[str, Any] | None = None,
		draft: str = "", actor: str, linked_issue: str = "", first_task: str = "") -> Any:
	"""Create an issue and ask its owner to send the first message. Service-level: commands call it after their own authority and version checks."""
	number = records.next_number(ISSUE, {"contract_case": case}, "issue_no")
	row = records.new(ISSUE, contract_case=case, issue_no=number, kind=kind, title=title, state="Open", facts_json=records.dumps(facts), requested_remedy=requested_remedy, reply_by=getdate(reply_by) if reply_by else None,
		owner_user=owner_of(case), messages_json=records.dumps([]), units_json=records.dumps(units or []), links_json=records.dumps({**(links or {}), "draft": draft}), linked_issue=linked_issue or None, record_version=1)
	subject = f"issue {number}"
	work.assign(case, "SendContractCorrespondence", first_task or ("Send the inspection findings to the supplier." if kind == "Delivery issue" else "Send the message to the supplier."), subject, 1, [row.owner_user], role="Contract owner")
	events.record(case, "Issue recorded", actor, f"Issue {number} recorded: {title}.", issue=row.name, kind=kind)
	return row


def record_issue(case: str, *, expected_version: int, idempotency_key: str, actor: str, kind: str, title: str, description: str, requested_remedy: str = "", reply_by: str = "") -> dict[str, Any]:
	"""`RecordContractIssue`: the supplier's representative or the contract's owner reports a matter. The facts are the reporter's own words; evidence comes with the messages."""
	preflight.exists(case)

	def authorise() -> None:
		from kentender_contracts.services import payment

		try:
			payment._claim_authority(case, actor)  # a supplier's representative
		except Exception:  # noqa: BLE001 - not the supplier: the owner's side may report too
			_may_manage(case, actor)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Awaiting signatures")
		invalid({"kind": "" if kind in KINDS else "Choose the kind of issue.", "title": "" if cstr(title).strip() else "Enter a short title.", "description": "" if cstr(description).strip() else "Describe the matter."})
		row = open_issue(case, kind=kind, title=cstr(title).strip(), facts={"description": cstr(description).strip(), "reported_by": actor}, requested_remedy=requested_remedy, reply_by=reply_by, actor=actor)
		records.bump(doc)
		return records.summary(doc, issue=row.name, issue_no=row.issue_no)

	return records.command("RecordContractIssue", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "kind": kind, "title": title, "description": description,
		"remedy": requested_remedy, "reply_by": reply_by}, body=body, authorise=authorise)


# -- correspondence -------------------------------------------------------------------------------------------------------------------
def _identity_subject(row, message_id: int) -> str:
	return f"issue {row.issue_no} message {message_id}"


def send_correspondence(case: str, *, issue: str, text: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SendContractCorrespondence`: a message from the owner to the supplier on the issue. It is dispatched once; the supplier is told only when there is evidence of delivery, and a message that could
	not be dispatched stays Unsent with its text and is retried."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ISSUE, issue)
		if row.contract_case != case or row.state == "Closed":
			fail("CM_CHANGED", issue=issue, state=row.state)
		invalid({"text": "" if cstr(text).strip() else "Write the message."})
		messages = thread(row)
		message = {"id": len(messages) + 1, "direction": "to supplier", "by": actor, "at": str(clock.now()), "text": cstr(text).strip(), "dispatch": {"state": "Unsent", "channel": "Supplier portal", "evidence": "", "at": ""}}
		messages.append(message)
		records.update(row, messages_json=records.dumps(messages), state="Awaiting reply", record_version=cint(row.record_version) + 1)
		subject = f"issue {row.issue_no}"
		work.finish(case, command="SendContractCorrespondence", subject=subject, actor=actor)
		intents.record(case, _identity_subject(row, message["id"]), 1, "Notice dispatch", "send", recovery_owner="Technical operator")
		records.bump(doc)
		return records.summary(doc, issue=row.name, message=message["id"])

	recorded = records.command("SendContractCorrespondence", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "text": text}, body=body,
		authorise=lambda: _may_manage(case, actor))
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	return dispatch_message(case, recorded["issue"], recorded["message"], actor)


def dispatch_message(case: str, issue: str, message_id: int, actor: str) -> dict[str, Any]:
	"""Carry the message to the supplier through the dispatch operation. Delivery is recorded with its evidence; a failure leaves the message Unsent and opens technical recovery."""
	row = frappe.get_doc(ISSUE, issue)
	message = next(m for m in thread(row) if m["id"] == message_id)
	identity_subject = _identity_subject(row, message_id)
	name = frappe.db.get_value(intents.INTENT, {"operation_identity": intents.identity(case, identity_subject, 1, "Notice dispatch", "send")}, "name")

	def executor(identity: str):
		try:
			return dispatch.deliver(identity, case=case, recipients=_supplier_side(case), subject=row.title, text=message["text"]), "Notice delivery"
		except dispatch.Failed as exc:
			raise intents.OwnerRefused(str(exc)) from exc

	result = intents.execute(name, executor, lambda identity: dispatch.find(identity), native_doctype="Notice delivery")
	with records.atomic():
		doc = records.lock(case)
		row = frappe.get_doc(ISSUE, issue)
		messages = thread(row)
		target = next(m for m in messages if m["id"] == message_id)
		if result["state"] in intents.SETTLED:
			target["dispatch"] = {"state": "Delivered", "channel": "Supplier portal", "evidence": result["reference"], "at": str(clock.now())}
			records.update(row, messages_json=records.dumps(messages), record_version=cint(row.record_version) + 1)
			subject = f"issue {row.issue_no}"
			work.finish(case, command="RestoreContractOperation", subject=_identity_subject(row, message_id), actor=actor)
			work.assign(case, "ReplyContractCorrespondence", "Reply to the replacement request." if row.kind == "Delivery issue" else "Reply to the message.", subject, len(messages), _supplier_side(case), role="Supplier Representative")
			work.assign(case, work.waiting_command("ReplyContractCorrespondence", "supplier"), "Waiting for the supplier's reply.", subject, len(messages), [row.owner_user], role="Contract owner", state="Waiting")
			events.record(case, "Message delivered", actor, f"Message {message_id} on issue {row.issue_no} reached the supplier.", issue=row.name, evidence=result["reference"])
			if row.kind == "Warranty claim":
				from kentender_contracts.services import warranty

				warranty.on_notice_delivered(case, row.name, actor)
		else:
			work.incident(case, "RestoreContractOperation", "Restore the message dispatch", _identity_subject(row, message_id), 1)
			events.record(case, "Message not delivered", actor, f"Message {message_id} on issue {row.issue_no} could not be delivered ({result['state'].lower()}); it stays unsent.", issue=row.name)
		records.bump(doc)
	frappe.db.commit()
	return {"ok": True, "issue": issue, "message": message_id, "delivered": result["state"] in intents.SETTLED}


def retry_dispatches(case: str, actor: str = "") -> int:
	"""Retry every message that is still Unsent (technical recovery). The same message and the same operation: nothing is sent twice."""
	count = 0
	for name in frappe.get_all(ISSUE, filters={"contract_case": case, "state": ["!=", "Closed"]}, pluck="name"):
		for message in thread(frappe.get_doc(ISSUE, name)):
			if message["direction"] == "to supplier" and message["dispatch"]["state"] != "Delivered":
				dispatch_message(case, name, message["id"], actor)
				count += 1
	return count


def reply_correspondence(case: str, *, issue: str, text: str, expected_version: int, idempotency_key: str, actor: str, proposed_remedy: str = "") -> dict[str, Any]:
	"""`ReplyContractCorrespondence` / `RespondToContractIssue`: the supplier's representative answers on the issue, and may propose a remedy. They never close it or accept their own remedy."""
	preflight.exists(case)

	def authorise() -> None:
		from kentender_contracts.services import payment

		payment._claim_authority(case, actor)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ISSUE, issue)
		if row.contract_case != case or row.state == "Closed":
			fail("CM_CHANGED", issue=issue, state=row.state)
		invalid({"text": "" if cstr(text).strip() else "Write your reply."})
		messages = thread(row)
		messages.append({"id": len(messages) + 1, "direction": "from supplier", "by": actor, "at": str(clock.now()), "text": cstr(text).strip(), "dispatch": {"state": "Received", "channel": "Supplier portal", "evidence": "", "at": str(clock.now())},
			**({"proposed_remedy": cstr(proposed_remedy).strip()} if cstr(proposed_remedy).strip() else {})})
		records.update(row, messages_json=records.dumps(messages), state="Remedy proposed" if cstr(proposed_remedy).strip() else "Replied", record_version=cint(row.record_version) + 1)
		subject = f"issue {row.issue_no}"
		work.finish(case, command="ReplyContractCorrespondence", subject=subject, actor=actor)
		work.assign(case, "ResolveContractIssue", "Review the supplier's reply." if row.kind == "Delivery issue" else "Review the supplier's reply and the remedy.", subject, len(messages), [row.owner_user], role="Contract owner")
		events.record(case, "Supplier replied", actor, f"The supplier replied on issue {row.issue_no}.", issue=row.name)
		records.bump(doc)
		return records.summary(doc, issue=row.name, message=len(messages))

	return records.command("ReplyContractCorrespondence", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "text": text, "remedy": proposed_remedy},
		body=body, authorise=authorise)


def resolve_issue(case: str, *, issue: str, disposition: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ResolveContractIssue`: the owner records the reasoned disposition and the thread closes. A warranty claim also needs its remedy verified first (see `warranty`), which closes it by itself."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ISSUE, issue)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		if row.state == "Closed":
			return records.summary(doc, issue=row.name, already=True)
		invalid({"disposition": "" if cstr(disposition).strip() else "Enter the disposition."})
		if row.kind == "Warranty claim":
			fail("CM_RECONCILE", issue=issue, reason="A warranty claim is closed when its remedy is verified, not by a note.")
		close(case, row, cstr(disposition).strip(), actor)
		from kentender_contracts.services import closeout

		closeout.offer_completion(case)
		records.bump(doc)
		return records.summary(doc, issue=row.name, state="Closed")

	return records.command("ResolveContractIssue", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "disposition": disposition}, body=body,
		authorise=lambda: _may_manage(case, actor))


def close(case: str, row, resolution: str, actor: str) -> None:
	"""Close the thread: nothing about it stays waiting, and a later matter starts a linked issue."""
	records.update(row, state="Closed", resolution=resolution, resolved_by=actor, closed_at=clock.now(), record_version=cint(row.record_version) + 1)
	subject = f"issue {row.issue_no}"
	for command in ("SendContractCorrespondence", "ReplyContractCorrespondence", "ResolveContractIssue"):
		work.finish(case, command=command, subject=subject, actor=actor)
	events.record(case, "Issue closed", actor, f"Issue {row.issue_no} closed: {resolution}", issue=row.name)


def close_when_replaced(case: str, accepted_units: dict[str, str], acceptance_number: int, actor: str) -> None:
	"""When replacement units are accepted, the issue that asked for them is closed with the fact. `accepted_units` maps a replacement unit to the rejected unit it replaces."""
	replaced = set(accepted_units.values())
	for name in frappe.get_all(ISSUE, filters={"contract_case": case, "kind": "Delivery issue", "state": ["!=", "Closed"]}, pluck="name"):
		row = frappe.get_doc(ISSUE, name)
		units = set(records.loads(row.units_json, []))
		if units and units <= replaced:
			made = ", ".join(sorted(u for u, old in accepted_units.items() if old in units))
			close(case, row, f"Replacement units {made} were accepted on {clock.now().strftime('%-d %B %Y')}.", actor)
