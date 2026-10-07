# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Requisitions owner's feed to Home (owner key `requisitions`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: no task is opened or closed and no lock is taken.

- **my_work** — the open department-approval and procurement-authorisation tasks the actor
  holds. Who holds one is `my_work_provider`'s own answer (called, not copied); the two
  segregation rules the owner's commands apply (REQ §7.3) are added here, because that
  provider does not check them: the authoriser is not the person who certified the
  requisition (`authorise.py`), and the Head of User Department did not prepare the Version
  in another capacity (`lifecycle.py`). A row is blocked only where the owner's own task
  page says so for the plan item (Planning's authorisation hold).
- **waiting** — the three waits the owner records: the author who sent a requisition for
  department approval, the Head of User Department who certified it to Procurement, and the
  requester of a Planning correction.
- **oversight** — none in v1: Requisitions has no outstanding-matter concept and the
  Accounting Officer reads only what was authorised (OVS), which is never outstanding.
- **coming_up** — none: Requisitions records no scheduled item or deadline.
- **completed** — the actor's own `Requisition Decision` rows of the last 30 days, and the
  sending for department approval from the command journal (it has no decision row).

Returns None where the region does not apply to the actor, [] where it applies and there is
nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services.authorization import descendants_of, is_technical, permitted_ou_scopes
from kentender_procurement.procurement_requisitions.services import eligibility_gateway, my_work_provider, records
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.requisition_roles import (
	DEPARTMENTAL_ROLES,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	SITE_WIDE_ROLES,
)

OWNER = "requisitions"
PAGE = "procurement-requisitions"
ROOT_FIELDS = ["name", "requisition_reference", "lead_org_unit_id", "current_state", "current_version", "plan_item_id"]
VERSION_FIELDS = ["name", "requirement_title", "prepared_by", "prepared_capacity", "sent_for_approval_by", "submitted_by"]
DEPARTMENT_APPROVAL, PROCUREMENT_AUTHORISATION = "requisitions.department_approval", "requisitions.procurement_authorisation"
SEND = "SendForDepartmentApproval"

#: The action phrase on a My work row, one table: the Head of Procurement Function's is the spec's own wording (HOME §10B),
#: the Head of User Department's is the owner's task heading without the reference.
ACTION = {DEPARTMENT_APPROVAL: "Review departmental requisition", PROCUREMENT_AUTHORISATION: "Authorise requisition"}
#: The owner's own words for a plan item on hold (the task page's headline, `read.get_procurement_authorisation_task`).
HOLD_REASON = "Authorisation is on hold while Planning reviews a correction request."
#: The three recorded waits: what the waiting person is told. `{who}` is the holder as a sentence subject.
WAIT_DEPARTMENT = "Waiting for {who} to review the departmental requisition"
WAIT_AUTHORISATION = "Waiting for {who} to authorise the requisition"
WAIT_PLANNING = "Waiting for {who} to resolve the Planning correction request"

#: Recently completed actions: Requisition Decision value → (the action label, what "You …" says). Anything not here is not shown.
COMPLETED: dict[str, tuple[str, str]] = {
	"Submit to Procurement": ("Sent requisition to Procurement", "sent this requisition to Procurement"),
	"Authorise requisition": ("Authorised requisition", "authorised this requisition"),
	"Return for correction": ("Returned requisition for correction", "returned this requisition for correction"),
	"Return to department": ("Returned requisition to department", "returned this requisition to the department"),
	"Change submitting department and return": ("Changed submitting department", "changed the submitting department of this requisition and returned it"),
	"Withdraw requisition": ("Withdrew requisition", "withdrew this requisition"),
	"Request Planning correction": ("Requested Planning correction", "asked Planning to correct the plan behind this requisition"),
	"Revoke authorisation": ("Revoked authorisation", "revoked the authorisation of this requisition"),
}
#: The sending has no decision row; the command journal is the owner's record of it.
SENT = ("Sent requisition for department approval", "sent this requisition for department approval")


# --------------------------------------------------------------------------
# facts read once per Home read
# --------------------------------------------------------------------------


def _people(names: list[str], role: str) -> str:
	"""The holder as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _someone(names: list[str], role: str) -> str:
	"""The holder as a sentence subject: "Amina Hassan", or "a Head of Procurement Function"."""
	if names and len(names) <= 2:
		return " or ".join(names)
	return f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


def _full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user)


def _holders(role: str, unit: str = "") -> list[str]:
	"""Who holds `role` now: for a Site-wide responsibility every enabled assignment with no Organisation Unit (NULL or empty),
	for a unit-scoped one the assignments on the unit or on a unit above it. Period checked as the resolver does (never invented)."""
	at = now_datetime()
	people: list[str] = []
	for row in frappe.get_all(
		"User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"},
		fields=["user", "organisation_unit", "effective_from", "effective_to"], order_by="creation asc", limit_page_length=0,
	):
		if (row.effective_from and get_datetime(row.effective_from) > at) or (row.effective_to and get_datetime(row.effective_to) < at):
			continue
		assigned = cstr(row.organisation_unit)
		if unit:
			if not assigned or not (assigned == unit or unit in descendants_of({assigned})):
				continue
		elif assigned:
			continue
		if row.user not in people:
			people.append(row.user)
	return people


class _Facts:
	"""What one actor's Home read needs more than once: the requisition roots, the versions' titles and people, who holds a
	role, and the read verdict per requisition."""

	def __init__(self, user: str):
		self.user = user
		self._roots: dict[str, Any] = {}
		self._versions: dict[str, Any] = {}
		self._holders: dict[tuple[str, str], list[str]] = {}
		self._readable: dict[str, bool] = {}
		self._holds: dict[str, Any] = {}

	def load(self, roots: set[str], versions: set[str]) -> None:
		"""Batch the roots and versions a read is about to use (two queries, not one per row)."""
		missing = {name for name in roots if name and name not in self._roots}
		if missing:
			for row in frappe.get_all("Procurement Requisition", filters={"name": ("in", sorted(missing))}, fields=ROOT_FIELDS, limit_page_length=0):
				self._roots[row.name] = row
		missing = {name for name in versions if name and name not in self._versions}
		if missing:
			for row in frappe.get_all("Requisition Version", filters={"name": ("in", sorted(missing))}, fields=VERSION_FIELDS, limit_page_length=0):
				self._versions[row.name] = row

	def root(self, name: str):
		self.load({name}, set())
		return self._roots.get(name)

	def version(self, name: str):
		self.load(set(), {name})
		return self._versions.get(name)

	def title(self, root, version_name: str = "") -> str:
		"""The requisition's own title: the officer's `requirement_title` on the Version (the Procurement Requisition has none)."""
		version = self.version(version_name or cstr(root.current_version)) if (version_name or root.current_version) else None
		return cstr((version.requirement_title if version else "") or root.requisition_reference).strip()

	def holders(self, role: str, unit: str = "", *, besides: str = "") -> list[str]:
		key = (role, unit)
		if key not in self._holders:
			self._holders[key] = _holders(role, unit)
		return [user for user in self._holders[key] if user != besides]

	def can_read(self, root_name: str) -> bool:
		"""The actor may still read the requisition (scope revoked since: nothing of it is shown)."""
		if root_name not in self._readable:
			self._readable[root_name] = bool(frappe.has_permission("Procurement Requisition", "read", doc=root_name, user=self.user))
		return self._readable[root_name]

	def hold(self, root) -> bool:
		"""Planning's authorisation hold on the plan item (read-only; the owner's own gateway)."""
		if root.plan_item_id not in self._holds:
			self._holds[root.plan_item_id] = bool((eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id).get("hold") or {}).get("held"))
		return self._holds[root.plan_item_id]


# --------------------------------------------------------------------------
# My work and Waiting
# --------------------------------------------------------------------------


def _applies(user: str) -> bool:
	"""The actor holds a Requisitions responsibility. The Accounting Officer's authorised-only read grant is not one: it gives
	no task, no wait and nothing to complete, so Home does not show them a Requisitions column."""

	def build() -> bool:
		if not user or user == "Guest" or is_technical(user):
			return False
		return any(authz.can_read_site(role, user) for role in SITE_WIDE_ROLES) or any(permitted_ou_scopes(user, role) for role in DEPARTMENTAL_ROLES)

	return home_support.memo("requisitions.applies", build, user=user)


def _tasks(names: list[str]) -> dict[str, Any]:
	return {
		task.name: task
		for task in frappe.get_all(
			"Requisition Task", filters={"name": ("in", names or [""])},
			fields=["name", "requisition", "requisition_version", "business_role", "organisation_unit", "task_token", "creation"], limit_page_length=0,
		)
	}


def _work(facts: _Facts) -> tuple[list[dict[str, Any]], set[str]]:
	"""The tasks the owner offers the actor, less the two the owner's commands would refuse (segregation of duties)."""
	rows = my_work_provider.my_work_rows(user=facts.user)["assigned"]
	tasks = _tasks([cstr(row["task_id"]) for row in rows])
	facts.load({task.requisition for task in tasks.values()}, {task.requisition_version for task in tasks.values()})
	entries: list[dict[str, Any]] = []
	held: set[str] = set()
	for row in rows:
		task = tasks.get(cstr(row["task_id"]))
		root = facts.root(task.requisition) if task else None
		version = facts.version(task.requisition_version) if task else None
		if not task or not root or not version:
			continue
		kind = cstr(row["task_type"])
		if kind == PROCUREMENT_AUTHORISATION and records.authoriser_conflict(version, facts.user):
			continue  # `authorise_requisition`: the authoriser cannot also be the submitting authority or the preparer (REQ_SOD_BLOCKED)
		if kind == DEPARTMENT_APPROVAL and records.certifier_conflict(version, facts.user):
			continue  # `submit_requisition_to_procurement`: an Author cannot complete the HoD decision on a Version they prepared or sent (REQ_SOD_BLOCKED)
		held.add(task.name)
		blocked = kind == PROCUREMENT_AUTHORISATION and facts.hold(root)
		entries.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=root.name, action_id=task.name, title=facts.title(root, task.requisition_version), reference=root.requisition_reference,
			action=ACTION[kind], destination={"route": list(row["route"])}, entered_at=task.creation, entered_verb="Received",
			blocked=blocked, reason=HOLD_REASON if blocked else "", source_revision=cstr(task.task_token),
		))
	return entries, held


def _waits(facts: _Facts, held: set[str]) -> list[dict[str, Any]]:
	"""The three waits the owner records, each only while the requisition is still in that state (so a returned, withdrawn or
	authorised one is not a wait). A task the actor holds themselves is not their wait."""
	entries: list[dict[str, Any]] = []
	user = facts.user
	open_tasks = frappe.get_all(
		"Requisition Task", filters={"status": "Open", "business_role": ("in", [ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_HEAD_OF_PROCUREMENT_FUNCTION])},
		fields=["name", "requisition", "requisition_version", "business_role", "creation"], order_by="creation asc", limit_page_length=0,
	)
	stopped_names = set(frappe.get_all("Procurement Requisition", filters={"current_state": "Upstream correction required"}, pluck="name", limit_page_length=0))
	facts.load({task.requisition for task in open_tasks} | stopped_names, {task.requisition_version for task in open_tasks})
	stopped = [root for root in (facts.root(name) for name in sorted(stopped_names)) if root]
	# who sent each requisition for department approval (the latest sending), and who certified each Version to Procurement
	sent: dict[str, Any] = {}
	for row in frappe.get_all(
		"Requisition Command Journal", filters={"command": SEND, "document_name": ("in", sorted({t.requisition for t in open_tasks}) or [""])},
		fields=["document_name", "actor", "occurred_at"], order_by="occurred_at asc", limit_page_length=0,
	):
		sent[row.document_name] = row
	versions = {task.requisition_version for task in open_tasks if task.business_role == ROLE_HEAD_OF_PROCUREMENT_FUNCTION} | {cstr(root.current_version) for root in stopped}
	decided: dict[tuple[str, str], Any] = {}
	for row in frappe.get_all(
		"Requisition Decision", filters={"requisition_version": ("in", sorted(versions) or [""]), "decision": ("in", ["Submit to Procurement", "Request Planning correction"])},
		fields=["requisition_version", "decision", "actor", "decided_at"], order_by="decided_at asc", limit_page_length=0,
	):
		decided[(row.requisition_version, row.decision)] = row
	for task in open_tasks:
		root = facts.root(task.requisition)
		if not root or task.name in held or not facts.can_read(root.name):
			continue
		if task.business_role == ROLE_HEAD_OF_USER_DEPARTMENT:
			if root.current_state != "Awaiting Department Approval" or not sent.get(root.name) or sent[root.name].actor != user:
				continue
			role, unit, line, since = ROLE_HEAD_OF_USER_DEPARTMENT, cstr(root.lead_org_unit_id), WAIT_DEPARTMENT, task.creation
		else:
			certified = decided.get((task.requisition_version, "Submit to Procurement"))
			if root.current_state != "Submitted to Procurement" or not certified or certified.actor != user:
				continue
			role, unit, line, since = ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "", WAIT_AUTHORISATION, certified.decided_at
		names = [_full_name(person) for person in facts.holders(role, unit, besides=user)]
		entries.append(he.make(
			region=he.WAITING, owner=OWNER, root=root.name, action_id=task.name, title=facts.title(root, task.requisition_version), reference=root.requisition_reference,
			action=line.format(who=_someone(names, role)), destination={"route": [PAGE, root.requisition_reference]}, holder=_people(names, role), since=since,
		))
	for root in stopped:
		request = decided.get((cstr(root.current_version), "Request Planning correction"))
		if not request or request.actor != user or not facts.can_read(root.name):
			continue
		names = [_full_name(person) for person in facts.holders(ROLE_PROCUREMENT_PLANNER, besides=user)]
		entries.append(he.make(
			region=he.WAITING, owner=OWNER, root=root.name, action_id=f"{root.name}:planning-correction", title=facts.title(root), reference=root.requisition_reference,
			action=WAIT_PLANNING.format(who=_someone(names, ROLE_PROCUREMENT_PLANNER)), destination={"route": [PAGE, root.requisition_reference]},
			holder=_people(names, ROLE_PROCUREMENT_PLANNER), since=request.decided_at,
		))
	return entries


def _register(user: str) -> dict[str, Any]:
	"""One scan for one Home read: {"my_work", "waiting"}."""
	facts = _Facts(user)
	my_work, held = _work(facts)
	return {"my_work": my_work, "waiting": _waits(facts, held)}


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _awaiting(facts: _Facts, root, *, role: str, stage: str, unit: str = "") -> str:
	""""It is awaiting authorisation by Charles Mutiso." — only while the requisition is still waiting on that responsibility's own
	open task (FU-HOME-24) and someone other than the actor holds it, named."""
	if not frappe.db.exists("Requisition Task", {"requisition": root.name, "requisition_version": root.current_version, "business_role": role, "status": "Open"}):
		return ""
	names = [_full_name(person) for person in facts.holders(role, unit, besides=facts.user)]
	return home_time.awaiting(stage, _people(names, role)) if names else ""


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	decisions = frappe.get_all(
		"Requisition Decision", filters={"actor": user, "decided_at": (">=", cutoff), "decision": ("in", sorted(COMPLETED))},
		fields=["name", "requisition_version", "decision", "decided_at"], order_by="decided_at desc", limit_page_length=0,
	)
	# a decision with no task is unreadable under the doctype's permission hooks: read with get_all and check the requisition itself
	version_roots = {
		row.name: row.requisition
		for row in frappe.get_all("Requisition Version", filters={"name": ("in", sorted({d.requisition_version for d in decisions}) or [""])}, fields=["name", "requisition"], limit_page_length=0)
	}
	sendings = frappe.get_all(
		"Requisition Command Journal", filters={"command": SEND, "actor": user, "occurred_at": (">=", cutoff)},
		fields=["name", "document_name", "occurred_at"], order_by="occurred_at desc", limit_page_length=0,
	)
	facts.load(set(version_roots.values()) | {row.document_name for row in sendings}, {d.requisition_version for d in decisions})
	last_sent = {}
	for row in frappe.get_all(
		"Requisition Command Journal", filters={"command": SEND, "document_name": ("in", sorted({s.document_name for s in sendings}) or [""])},
		fields=["name", "document_name"], order_by="occurred_at asc", limit_page_length=0,
	):
		last_sent[row.document_name] = row.name
	entries: list[dict[str, Any]] = []
	for row in decisions:
		root = facts.root(version_roots.get(row.requisition_version, ""))
		if not root or not facts.can_read(root.name):
			continue
		label, did = COMPLETED[cstr(row.decision)]
		follow = ""
		if row.decision == "Submit to Procurement" and root.current_state == "Submitted to Procurement" and cstr(root.current_version) == row.requisition_version:
			follow = _awaiting(facts, root, role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, stage="authorisation")
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=root.name, action_id=row.name, title=facts.title(root, row.requisition_version), reference=root.requisition_reference,
			action=label, destination={"route": [PAGE, root.requisition_reference]}, completed_at=row.decided_at, sentence=home_time.completed_sentence(did, row.decided_at, follow=follow),
		))
	for row in sendings:
		root = facts.root(row.document_name)
		if not root or not facts.can_read(root.name):
			continue
		follow = ""
		if root.current_state == "Awaiting Department Approval" and last_sent.get(root.name) == row.name:
			follow = _awaiting(facts, root, role=ROLE_HEAD_OF_USER_DEPARTMENT, stage="department approval", unit=cstr(root.lead_org_unit_id))
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=root.name, action_id=row.name, title=facts.title(root), reference=root.requisition_reference,
			action=SENT[0], destination={"route": [PAGE, root.requisition_reference]}, completed_at=row.occurred_at, sentence=home_time.completed_sentence(SENT[1], row.occurred_at, follow=follow),
		))
	return entries


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region in (he.COMING_UP, he.OVERSIGHT) or not _applies(user):
		return None
	if region == he.COMPLETED:
		return home_support.memo("requisitions.completed", lambda: _completed(user), user=user)
	return home_support.memo("requisitions.register", lambda: _register(user), user=user)[region]
