# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Tenders owner's feed to Home (owner key `tenders`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: no task is opened, closed or refreshed, and the one
obligation read is `cancellation.obligation_status`, never
`refresh_obligation_statuses`.

- **my_work** — the open register items the actor holds, the corrected-successor
  and Reopen rows the owner derives, worded by `handoffs.HOME_TEXT`. Who holds an
  item, and the segregation rule that removes it, are `my_work_provider`'s own
  answer (called, not copied). A row is blocked only where the owner's `guidance`
  says so for that exact item.
- **waiting** — the items the actor sent that someone else holds.
- **oversight** — Tenders whose open item is neither the actor's nor sent by the
  actor, for an actor with an oversight-capable responsibility (Accounting Officer,
  Head of Procurement Function, Auditor; a Head of User Department only for a
  Tender their unit contributed to, shown no holder). Each Tender is confirmed with
  the owner's read check first.
- **coming_up** — none in v1: Tenders records the clarification and submission
  deadlines but has no policy on whose Coming up they belong to (owner decision).
- **completed** — the actor's own `Tender Decision` rows of the last 30 days.

Returns None where the region does not apply to the actor, [] where it applies
and there is nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr, getdate, get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import next_step as ns
from kentender_core.services.authorization import is_technical, permitted_ou_scopes
from kentender_procurement.tenders.services import cancellation, guidance, handoffs, my_work_provider, read, serializer
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.tender_roles import ROLE_ACCOUNTING_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_HEAD_OF_USER_DEPARTMENT

OWNER = "tenders"
PAGE = "tenders"
ROOT_FIELDS = ["name", "tender_reference", "requirement_title", "approved_version", "current_version", "lead_org_unit", "contributing_org_unit_ids"]
SUCCESSOR, PERIOD = ":successor", ":period"

#: Recently completed actions: Tender Decision value → (the action label, what "You …" says). Anything not here is not shown
#: (a discarded addendum draft is not a completed action worth a line).
COMPLETED: dict[str, tuple[str, str]] = {
	"Submit for approval": ("Submitted Tender for approval", "submitted this Tender"),
	"Return for correction": ("Returned Tender for correction", "returned this Tender for correction"),
	"Approve Tender package": ("Approved Tender package", "approved this Tender package"),
	"Reopen Tender": ("Reopened Tender", "reopened this Tender for correction"),
	"Authorise publication": ("Authorised publication", "authorised publication of this Tender"),
	"Withdraw publication authorisation": ("Withdrew publication authorisation", "withdrew the publication authorisation for this Tender"),
	"Return approved Tender to Head of Procurement Function": ("Returned approved Tender", "returned this approved Tender to the Head of Procurement Function"),
	"Request requisition correction": ("Requested requisition correction", "asked for the requisition behind this Tender to be corrected"),
	"Recommend cancellation": ("Recommended cancellation", "recommended cancelling this Tender"),
	"Cancel Tender": ("Cancelled Tender", "cancelled this Tender"),
	"Respond to clarification": ("Responded to clarification", "responded to a clarification on this Tender"),
	"Submit addendum for issue": ("Submitted addendum for issue", "submitted an addendum to this Tender for issue"),
	"Issue addendum": ("Issued addendum", "issued an addendum to this Tender"),
	"Return addendum for correction": ("Returned addendum", "returned an addendum to this Tender for correction"),
	"Request cancellation review": ("Requested cancellation review", "asked the Accounting Officer to consider cancelling this Tender"),
	"Close cancellation review": ("Closed cancellation review", "closed the cancellation review for this Tender"),
}
#: The journey stages whose waiting answer reads "It is awaiting {phrase} by …": stage → (the responsibility that must hold it, phrase).
#: A waiting answer on the same stage held by anyone else (a Reopen, a System Manager to assign someone) is not that wait.
AWAITING: dict[str, tuple[str, str]] = {
	guidance.HOPF_APPROVAL: (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "approval"),
	guidance.AO_AUTHORISATION: (ROLE_ACCOUNTING_OFFICER, "publication authorisation"),
	guidance.PUBLICATION: (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "publication confirmation"),
}


# --------------------------------------------------------------------------
# facts read once per Home read
# --------------------------------------------------------------------------


def _people(names: list[str], role: str) -> str:
	"""The holder as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _someone(names: list[str], role: str) -> str:
	"""The holder as a sentence subject: "Amina Hassan", or "an Accounting Officer"."""
	if names and len(names) <= 2:
		return " or ".join(names)
	return f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


class _Facts:
	"""What one actor's Home read needs more than once: the Tender roots, their business titles, the actor's roles and the
	owner's guidance per Tender."""

	def __init__(self, user: str):
		self.user = user
		self.roles = read.actor_roles(user)
		self._roots: dict[str, Any] = {}
		self._titles: dict[str, str] = {}
		self._steps: dict[tuple, dict[str, Any]] = {}
		self._holders: dict[tuple[str, str], list[str]] = {}

	def root(self, name: str):
		if name not in self._roots:
			self._roots[name] = frappe.db.get_value("Tender", name, ROOT_FIELDS, as_dict=True)
		return self._roots[name]

	def title(self, root) -> str:
		"""The Tender's own title: the officer's title on the approved (else current) Version, as Bid Opening, Evaluation and Award
		show it, falling back to the Requisition's. The two differ once the officer retitles the Tender."""
		if root.name not in self._titles:
			version = root.approved_version or root.current_version
			payload = frappe.db.get_value("Tender Version", version, "officer_payload_json") if version else None
			state = serializer.officer_state(frappe._dict(officer_payload_json=payload))
			self._titles[root.name] = cstr(state.get("tender_title") or root.requirement_title or root.tender_reference).strip()
		return self._titles[root.name]

	def holder_names(self, task) -> list[str]:
		"""The people who hold the item now, other than the actor (a holder the segregation rule removed is not their own wait)."""
		key = (cstr(task.get("holder")), cstr(task.task_type))
		if key not in self._holders:
			self._holders[key] = handoffs.holders_of(task)
		return [handoffs.full_name(user) for user in self._holders[key] if user != self.user]

	def step(self, root, *, context: str = "record", subject: dict[str, Any] | None = None) -> dict[str, Any]:
		"""The owner's `next_step` for the actor on this Tender (read-only)."""
		key = (root.name, context, cstr((subject or {}).get("name")))
		if key not in self._steps:
			doc = frappe.get_doc("Tender", root.name)
			self._steps[key] = guidance.guidance(doc, actor=self.user, roles=self.roles, mode="site", context=context, subject=subject)["next_step"]
		return self._steps[key]

	def can_read(self, root) -> bool:
		try:
			authz.reader_mode(self.user, contributing_org_units=authz.contributing_units_of(root))
			return True
		except frappe.DoesNotExistError:
			return False

	def blocked(self, task, root) -> tuple[bool, str]:
		"""Blocked only where the owner's own answer for this exact item is Your turn, blocked; its headline is the reason."""
		kind = cstr(task.task_type)
		if kind == handoffs.CLARIFICATION_RESPONSE:
			subject = frappe.db.get_value("Tender Clarification", task.subject_id, ["name", "status", "received_at", "required_addendum"], as_dict=True) if task.subject_id else None
			if not subject:
				return False, ""
			step = self.step(root, context="clarification", subject=subject)
		elif kind == handoffs.AO_AUTHORISATION:
			step = self.step(root)
		else:
			return False, ""
		headline = cstr(step.get("headline")).strip()
		return (True, headline) if step.get("kind") == ns.KIND_BLOCKED and headline else (False, "")


def _compliance_due(task):
	"""The earliest obligation of the cancellation not yet recorded (a Date), from the owner's read-only status."""
	if cstr(task.task_type) != handoffs.CANCELLATION_COMPLIANCE or not task.subject_id:
		return None
	doc = frappe.get_doc("Tender Cancellation", task.subject_id)
	unmet = [getdate(row.due_by) for row in doc.obligations if row.due_by and cancellation.obligation_status(row, cancellation=doc.name) != "Recorded"]
	if unmet or doc.obligations:
		return min(unmet) if unmet else None
	dates = [getdate(value) for value in (doc.ppra_report_due_by, doc.candidate_notice_due_by) if value]
	return min(dates) if dates else None


# --------------------------------------------------------------------------
# My work, Waiting, Records you oversee
# --------------------------------------------------------------------------


def _record(root) -> dict[str, Any]:
	return {"route": [PAGE, root.tender_reference]}


def _derived_root(row: dict[str, Any]) -> str:
	return cstr(row["task_id"]).rsplit(":", 1)[0]


def _work(facts: _Facts, legacy: list[dict[str, Any]], tasks: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
	entries: list[dict[str, Any]] = []
	held: set[str] = set()
	for row in legacy:
		task_id = cstr(row["task_id"])
		held.add(task_id)
		task = tasks.get(task_id)
		if task:
			root = facts.root(task.tender)
			if not root:
				continue
			blocked, reason = facts.blocked(task, root)
			entries.append(he.make(
				region=he.MY_WORK, owner=OWNER, root=root.name, action_id=task.name, title=facts.title(root), reference=root.tender_reference,
				action=handoffs.home_action_for(root, task), destination={"route": handoffs.route_for(root, task)}, entered_at=task.creation, entered_verb="Received",
				blocked=blocked, reason=reason, due=_compliance_due(task),
			))
			continue
		root = facts.root(_derived_root(row))
		if not root or not task_id.endswith((SUCCESSOR, PERIOD)):
			continue
		if task_id.endswith(SUCCESSOR):
			stopped = frappe.db.get_value("Tender Version", root.current_version, "stopped_at") if root.current_version else None
			action, entered = handoffs.HOME_SUCCESSOR_ACTION, stopped or get_datetime(row["received_at"])
		else:
			action, entered = handoffs.HOME_PERIOD_ACTION, get_datetime(row["received_at"])
		entries.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=root.name, action_id=task_id, title=facts.title(root), reference=root.tender_reference, action=action,
			destination={"route": list(row["route"])}, entered_at=entered, entered_verb="Received",
		))
	return entries, held


def _waiting(facts: _Facts, legacy: list[dict[str, Any]], tasks: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
	entries: list[dict[str, Any]] = []
	sent: set[str] = set()
	for row in legacy:
		task_id = cstr(row["task_id"])
		sent.add(task_id)
		holder = row.get("holder") or {}
		names, role = list(holder.get("people") or []), cstr(holder.get("role"))
		task = tasks.get(task_id)
		if task:
			root = facts.root(task.tender)
			if not root:
				continue
			line = handoffs.home_line_for(root, task, _someone(names, role))
			since, due = task.creation, _compliance_due(task)
		elif task_id.endswith(PERIOD):
			root = facts.root(_derived_root(row))
			if not root:
				continue
			line, since, due = handoffs.HOME_PERIOD_WAITING.format(holder=_someone(names, role)), get_datetime(row["received_at"]), None
		else:
			continue
		entries.append(he.make(
			region=he.WAITING, owner=OWNER, root=root.name, action_id=task_id, title=facts.title(root), reference=root.tender_reference, action=line,
			destination=_record(root), holder=_people(names, role), since=since, due=due,
		))
	return entries, sent


def _oversight(facts: _Facts, tasks: dict[str, Any], *, skip: set[str], full: bool, department: bool) -> list[dict[str, Any]]:
	"""One row per Tender, for the oldest open item that is not the actor's and not theirs to wait on."""
	entries: list[dict[str, Any]] = []
	shown: set[str] = set()
	for task in tasks.values():
		if task.name in skip or cstr(task.sender) == facts.user or task.tender in shown:
			continue
		root = facts.root(task.tender)
		if not root or not facts.can_read(root):
			continue
		if full:
			names = facts.holder_names(task)
			line, holder = handoffs.home_line_for(root, task, _someone(names, cstr(task.business_role))), _people(names, cstr(task.business_role))
		elif department and authz.is_department_head_of(root, facts.user):
			line, holder = handoffs.home_neutral_for(task), ""
		else:
			continue
		if not line:
			continue
		shown.add(task.tender)
		entries.append(he.make(
			region=he.OVERSIGHT, owner=OWNER, root=root.name, action_id=task.name, title=facts.title(root), reference=root.tender_reference, action=line,
			destination=_record(root), holder=holder, since=task.creation, outstanding=True,
		))
	return entries


def _applies(user: str) -> bool:
	return home_support.memo("tenders.applies", lambda: not is_technical(user) and authz.holds_any_tender_responsibility(user), user=user)


def _register(user: str) -> dict[str, Any]:
	"""One scan of the open register for one Home read: {"my_work", "waiting", "oversight"} (oversight None when the actor has none)."""
	facts = _Facts(user)
	legacy = my_work_provider.my_work_rows(user=user)
	tasks = {
		task.name: task
		for task in frappe.get_all("Tender Task", filters={"status": "Open"}, fields=my_work_provider.TASK_FIELDS, order_by="creation asc", limit_page_length=0)
		if task.task_type in handoffs.REGISTER
	}
	my_work, held = _work(facts, legacy["assigned"], tasks)
	waiting, sent = _waiting(facts, legacy["waiting"], tasks)
	full = bool(facts.roles["hopf"] or facts.roles["ao"] or facts.roles["auditor"])
	department = bool(permitted_ou_scopes(user, ROLE_HEAD_OF_USER_DEPARTMENT))
	oversight = _oversight(facts, tasks, skip=held | sent, full=full, department=department) if full or department else None
	return {"my_work": my_work, "waiting": waiting, "oversight": oversight}


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _awaiting(facts: _Facts, root) -> str:
	""""It is awaiting publication authorisation by Amina Hassan." — only while the owner's current answer for the actor is a wait
	on that stage's own holder, named."""
	step = facts.step(root)
	holder = step.get("holder") or {}
	expected = AWAITING.get(cstr(step.get("stage")))
	names = list(holder.get("people") or [])
	if step.get("kind") != ns.KIND_WAITING or not expected or not names or cstr(holder.get("role")) != expected[0]:
		return ""
	return home_time.awaiting(expected[1], _people(names, holder["role"]))


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	entries: list[dict[str, Any]] = []
	rows = frappe.get_all("Tender Decision", filters={"actor": user, "decided_at": (">=", cutoff)}, fields=["name", "tender", "decision", "decided_at"], order_by="decided_at desc", limit_page_length=0)
	for row in rows:
		wording = COMPLETED.get(cstr(row.decision))
		root = facts.root(row.tender) if wording else None
		if not root or not facts.can_read(root):
			continue
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=root.name, action_id=row.name, title=facts.title(root), reference=root.tender_reference, action=wording[0],
			destination=_record(root), completed_at=row.decided_at, sentence=home_time.completed_sentence(wording[1], row.decided_at, follow=_awaiting(facts, root)),
		))
	return entries


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region == he.COMING_UP or not _applies(user):
		return None
	if region == he.COMPLETED:
		return home_support.memo("tenders.completed", lambda: _completed(user), user=user)
	return home_support.memo("tenders.register", lambda: _register(user), user=user)[region]
