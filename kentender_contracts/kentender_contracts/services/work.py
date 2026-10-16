# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stored obligations (CM-CHG-001 v0.8 sections 5.10, 6.3, 6.4; tracker CM8-312, CM-AC-59).

A `Contract Task` is one obligation of one holder, identified by (case, subject, version, command, holder), so a retry or a replayed event never makes a second one. A command that
hands work on **assigns** it to each required current holder and **finishes** its own; a sender who must wait gets a Waiting item naming the holder. What leads a person's day, and how a
case answers "what is my next step", is `tasks.view` over these rows (`services/tasks.py`) mapped by `services/next_steps.py`. Closing a task keeps its outcome and its attribution; nothing is
deleted, and a reassignment keeps the earlier holder. Whose task it is does not grant authority: every command checks authority itself."""

from __future__ import annotations

from typing import Any, Iterable

import frappe
from frappe.utils import get_datetime

from kentender_contracts.services import clock, notifications, people, records, tasks as rules

TASK = "Contract Task"
STATE = {"Open": rules.ACTIONABLE, "Blocked": rules.BLOCKED, "Waiting": rules.WAITING, "Scheduled": rules.SCHEDULED}
LIVE = ("Open", "Blocked", "Waiting", "Scheduled")
HOP = "Head of Procurement Function"
TECHNICAL = "Technical Operator"


def holders(role: str, unit: str = "") -> list[str]:
	if role == TECHNICAL:  # a technical account holds no business capacity, so the people helper never lists it; the recovery owner is whoever holds the registered technical duty
		return sorted(set(frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user")))
	return people.holders(role, unit)


def identity_of(case: str, subject: str, version: int, command: str, holder: str) -> str:
	"""(case, subject, version, command, holder), shortened to a stable token when it would not fit the 140 characters the key is stored in."""
	whole = f"{case}|{subject}|{version}|{command}|{holder}"
	return whole if len(whole) <= 120 else f"{case}|{records.short(whole)}"


def assign(case: str, command: str, title: str, subject: str, version: int, holder_users: Iterable[str], *, role: str = "", state: str = "Open", due=None, due_verified: bool = False) -> list[str]:
	"""One task for each holder. Returns the identities created; an existing identity is left exactly as it is (so a replay changes nothing)."""
	created = []
	for holder in sorted({h for h in holder_users if h}):
		identity = identity_of(case, subject, version, command, holder)
		existing = frappe.db.get_value(TASK, {"identity": identity}, ["name", "state"], as_dict=True)
		if existing:
			if existing.state in ("Done", "Superseded"):  # the same obligation arising again (a recovery that fails twice) is the same item, reopened with its history kept
				doc = frappe.get_doc(TASK, existing.name)
				records.append_json(doc, "history_json", {"state": "Reopened", "at": str(clock.now())})
				records.update(doc, state=state, title=title, assigned_at=clock.now(), completed_at=None)
				created.append(identity)
				if state == "Open" and notifications.raises_alert(command):
					_notify(case, holder, title, command, subject)
			continue
		records.new(TASK, contract_case=case, identity=identity, command=command, title=title, subject=subject, subject_version=version, holder=holder, holder_role=role, state=state,
			assigned_at=clock.now(), due=due, due_verified=1 if due and due_verified else 0, history_json="[]")
		created.append(identity)
		if state == "Open" and notifications.raises_alert(command):
			_notify(case, holder, title, command, subject)
	return created


def _notify(case: str, holder: str, title: str, command: str, subject: str) -> None:
	"""The bell: one alert for the person whose turn it has just become, linking to the step on its own tab and never a second approval (section 5.10: "a notification links to that item"). Only a task the
	table names alerts (`notifications`); a waiting or scheduled item is not an alert, and an alert that cannot be shown does not undo the task. A supplier's person is sent to the supplier portal, not Desk."""
	from kentender_contracts.boards import chrome
	from kentender_contracts.services import audience

	try:
		doc = frappe.db.get_value("Contract Case", case, ["contract_id", "lifecycle"], as_dict=True)
		root = "/supplier/contracts" if audience.workspace_audiences(holder) == ["supplier"] else "/desk/contracts"
		frappe.get_doc({"doctype": "Notification Log", "for_user": holder, "type": "Alert", "subject": title, "email_content": f"{doc.contract_id}: {title}", "document_type": "Contract Case", "document_name": case,
			"link": f"{root}/{case}/{chrome.tab_of(command, subject, doc.lifecycle).lower()}"}).insert(ignore_permissions=True)
	except Exception:  # noqa: BLE001
		frappe.log_error(title="Contract Management could not notify a task holder")


def alert(case: str, holders: Iterable[str], title: str, command: str, subject: str) -> None:
	"""An alert the table names for a holder who has no task of their own to open (for example the head of procurement when a funding or order update is refused: the table notifies them and gives them a waiting
	item). One alert for each person, linking to the step's tab."""
	for holder in sorted({h for h in holders if h}):
		_notify(case, holder, title, command, subject)


def waiting_command(command: str, qualifier: str) -> str:
	"""The command key of a sender's "waiting" item: distinct from the obligation it waits for, so both keep their own identity and history."""
	return f"{command}:waiting:{qualifier}"


def finish(case: str, *, command: str | None = None, subject: str | None = None, version: int | None = None, state: str = "Done", actor: str = "", holder: str | None = None, exact: bool = False) -> int:
	"""Close the matching live tasks. `state` is Done (the obligation was met) or Superseded (it no longer applies). `holder` limits it to one person's own obligation (each member
	declares for themselves: one member's declaration does not close another's)."""
	filters: dict[str, Any] = {"contract_case": case, "state": ["in", list(LIVE)]}
	if holder is not None:
		filters["holder"] = holder
	if subject is not None:
		filters["subject"] = subject
	if version is not None:
		filters["subject_version"] = version
	if command is None:
		names = frappe.get_all(TASK, filters=filters, pluck="name")
	else:  # the obligation itself, and the sender's "waiting" items that were raised for it (`waiting`), unless `exact`: the obligation alone
		names = frappe.get_all(TASK, filters={**filters, "command": command}, pluck="name")
		if not exact:
			names += frappe.get_all(TASK, filters={**filters, "command": ["like", f"{command}:waiting:%"]}, pluck="name")
	count = 0
	for name in names:
		doc = frappe.get_doc(TASK, name)
		records.append_json(doc, "history_json", {"state": state, "at": str(clock.now()), "by": actor})
		records.update(doc, state=state, completed_at=clock.now())
		count += 1
	return count


def reassign(case: str, command: str, subject: str, version: int, old_holder: str, new_holder: str, *, actor: str = "") -> None:
	"""Move a live task to another holder, keeping the earlier holder and the time it ended."""
	name = frappe.db.get_value(TASK, {"identity": identity_of(case, subject, version, command, old_holder)}, "name")
	if not name:
		return
	doc = frappe.get_doc(TASK, name)
	records.append_json(doc, "history_json", {"holder": old_holder, "from": str(doc.assigned_at), "until": str(clock.now()), "by": actor})
	records.update(doc, holder=new_holder, assigned_at=clock.now(), identity=identity_of(case, subject, version, command, new_holder))


#: The consequence an obligation exercises, so an open hold on it makes the step **blocked** (with the hold's reason and holder) instead of a button that will be refused (section 5.17, 6.3).
CONSEQUENCE = {
	"RequestContractSignatures": "new_signing_attempt", "SignContractVersion": "new_signing_attempt", "SignContractCertification": "certify_invoice", "SignAdvanceCertification": "certify_advance", "RecordFinanceSettlement": "confirm_settlement",
	"VerifyContractRemedy": "close_claim", "SubmitContractChangeForDecision": "vary_contract", "DecideContractChange": "vary_contract", "ActivateContractChange": "vary_contract",
	"IssueCompletionCertificate": "close_contract", "SignContractCloseout": "close_contract", "PrepareContractCloseout": "close_contract", "SignFinalContractAcceptance": "final_accept",
}
#: Finance's payment steps are blocked by a payment hold; the accounting invoice (liability) is not (section 5.8, 5.12).
PAYMENT_STEPS = ("SaveNativeFinanceDraft", "SubmitNativeFinanceForApproval", "ApproveNativeFinanceRecord")


def _consequence(command: str, subject: str) -> str | None:
	if command in PAYMENT_STEPS:
		return "pay" if subject.startswith("payment") else None
	return CONSEQUENCE.get(command)


def live(case: str) -> list[dict[str, Any]]:
	"""The case's live obligations in the shape `tasks.view` orders. An actionable one whose consequence a hold blocks is **blocked**, carrying the hold's reason, its holder and what clears it."""
	from kentender_contracts.services import holds

	rows = frappe.get_all(TASK, filters={"contract_case": case, "state": ["in", list(LIVE)]},
		fields=["name", "creation", "command", "title", "subject", "subject_version", "holder", "holder_role", "state", "assigned_at", "due", "due_verified"], order_by="assigned_at asc, creation asc, name asc")
	out = []
	open_now = None  # the holds are read once for the whole list (fresh for this reading), not once for each obligation
	for r in rows:
		item = {"task_id": r.name, "case": case, "subject": r.subject, "version": r.subject_version, "command": r.command, "title": r.title, "holder": r.holder, "holder_role": r.holder_role,
			"state": STATE[r.state], "due": get_datetime(r.due) if r.due else None, "due_verified": bool(r.due_verified), "assigned_at": get_datetime(r.assigned_at), "created": get_datetime(r.creation)}
		capability = _consequence(r.command, r.subject)
		if capability and item["state"] == rules.ACTIONABLE:
			if open_now is None:
				open_now = holds.open_holds(case)
			blocking = [h for h in open_now if capability in h.blocks and h.covers(r.subject)]
			if blocking:
				first = blocking[0]
				item["state"] = rules.BLOCKED
				item["blocker"] = {"reason_code": "CM_HOLD", "message": first.reason, "fix_label": "View issue", "responsibility": first.owner, "clears_with": first.clearing, "holds": [h.key for h in blocking]}
		out.append(item)
	return out


def view(case: str, actor: str, *, neutral: bool = False, holders: set[str] | None = None) -> dict[str, Any]:
	"""The leading item and Other work for one actor. `holders` limits the work the actor may see to the people named (a supplier sees their own side only, section 6.2)."""
	items = live(case)
	if holders is not None:
		items = [t for t in items if t["holder"].lower() in holders]
	return rules.view(items, actor, clock.now(), neutral=neutral)


def responsible(case: str) -> str:
	"""Who the case is waiting on first: the holder of its leading obligation, whoever that is (the list's "Responsible person")."""
	ordered = rules.order(rules.dedupe(live(case)), clock.now())
	actionable = [t for t in ordered if t["state"] in (rules.ACTIONABLE, rules.BLOCKED)]
	pick = (actionable or ordered or [None])[0]
	return pick["holder"] if pick else ""


def incident(case: str, command: str, title: str, subject: str, version: int) -> None:
	"""Technical recovery work for an operation that did not complete: the original attempt is restored, never repeated with a fresh signature."""
	assign(case, command, title, subject, version, holders(TECHNICAL), role=TECHNICAL)
