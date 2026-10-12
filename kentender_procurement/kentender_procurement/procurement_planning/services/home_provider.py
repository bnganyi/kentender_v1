# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Planning owner's feed to Home (owner key `planning`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: no plan is refreshed, no draft entry is rebuilt (so
`dpp_read.get_departmental_plan` is never called) and no task is opened or closed.

- **my_work** — the open Planning items the actor holds: the validation, funding,
  governance and correction tasks, the department's update prompts and the plan and
  departmental-plan hand-offs. Who holds an item and the segregation rule that
  removes it are `my_work_provider`'s own answer (its builders are called, not
  copied); this provider only gives each row its business title (the plan's title, or
  the department's name — a departmental plan has no title), a true event instant and
  the owner's own blocked reason.
- **waiting** — the items the actor sent that someone else holds, worded by the
  owner's waiting titles, with the holder and the instant the hand-off began.
- **oversight** — none in v1: Planning has no owner API for outstanding matters, no
  oversight read is built for it, the Head of User Department's downstream position
  does not exist, and deriving it would run the heavy plan guidance for every plan.
- **coming_up** — none in v1: PLN v1.29 §5.5.1B creates no schedule-driven Planning
  item (the CFG-owned departmental-plan intake closing time is an owner decision).
- **completed** — the actor's own decision rows of the last 30 days.

Returns None where the region does not apply to the actor, [] where it applies and
there is nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import next_step as ns
from kentender_core.services.authorization import is_technical
from kentender_procurement.procurement_planning.services import my_work_provider as work
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services import plan_read
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

OWNER = "planning"
PLAN_PAGE = "annual-procurement-plan"
DPP_PAGE = "departmental-procurement-plan"
PLANNING_PAGE = "procurement-planning"
#: More than this many people hold a responsibility: name the responsibility, never a list (the owner's guidance names them all).
MAX_NAMED = 2

#: The action each work row reads, without the title (`my_work_provider`'s wording with the plan or department removed). The
#: governance row is told apart by the task's stage.
ACTION: dict[str, str] = {
	"planning.dpp_validation": "Validate departmental plan",
	"planning.finance": "Confirm plan funding",
	"planning.plan_item_correction": "Review correction request",
	"planning.dpp_update_required": "Update departmental plan",
	"planning.dpp_update_requested": "Update departmental plan",
	"planning.finance_return": "Correct the plan returned by Finance",
	"planning.budget_outcome": "Continue plan update",
	"planning.governance_return": "Correct the returned plan",
	"planning.add_requirements": "Add accepted requirements to the annual plan",
	"planning.sign": "Sign and submit the annual plan",
	"planning.publication": "Confirm plan publication",
	"planning.withdrawal_request": "Request withdrawal for correction",
	"planning.withdrawal_decision": "Decide the withdrawal request",
	"planning.continue_correction": "Continue the correction",
	"planning.corrected_plan": "Prepare a corrected plan",
	"planning.dpp_return": "Correct and resubmit departmental plan",
}
GOVERNANCE_ACTION: dict[str, str] = {
	"Accounting Officer adoption": "Adopt Annual Procurement Plan",
	"Statutory approval": "Approve Annual Procurement Plan",
}
#: Completed actions: decision value → (the action label, what "You …" says). Anything not here is not shown.
FINANCE_DECISIONS: dict[str, tuple[str, str]] = {
	"Confirm plan funding": ("Confirmed plan funding", "confirmed funding for this plan"),
	"Return to planner": ("Returned plan to the Planner", "returned this plan to the Procurement Planner"),
}
GOVERNANCE_DECISIONS: dict[str, tuple[str, str]] = {
	"Adopt and submit": ("Adopted Annual Procurement Plan", "adopted this Annual Procurement Plan and submitted it for approval"),
	"Approve Annual Procurement Plan": ("Approved Annual Procurement Plan", "approved this Annual Procurement Plan"),
	"Return for correction": ("Returned plan for correction", "returned this Annual Procurement Plan for correction"),
	"Withdraw for correction": ("Withdrew plan for correction", "withdrew this Annual Procurement Plan for correction"),
}
VALIDATION_DECISIONS: dict[str, tuple[str, str]] = {
	"Accept departmental plan": ("Accepted departmental plan", "accepted this departmental plan"),
	"Return to department": ("Returned departmental plan", "returned this departmental plan to the department"),
}
DISPOSITIONS: dict[str, tuple[str, str]] = {
	"Start": ("Started correction request", "started work on this plan item correction request"),
	"Resolve": ("Resolved correction request", "resolved this plan item correction request"),
	"Close without change": ("Closed correction request", "closed this plan item correction request without change"),
}
SIGNED = ("Signed and submitted annual plan", "signed and submitted this annual plan")
SUBMITTED = ("Submitted departmental plan", "certified and submitted this departmental plan to Procurement")
PUBLICATION = ("Confirmed plan publication", "confirmed the Treasury submission and website publication of this Annual Procurement Plan")

#: The wait an actor is in, as the "It is awaiting {phrase} by …" clause: the stage of a plan wait, or "review" for a departmental
#: plan under Procurement's review. Any other wait (preparation, planning) is not a clause.
AWAITING: dict[str, str] = {
	"funding": "funding confirmation",
	"signature": "signature",
	"ao": "adoption",
	"statutory": "approval",
	"publication": "publication",
	"review": "Procurement review",
}

#: Who may still read the plan record behind a decision (the roles the owner's own task and plan reads accept).
FINANCE_READERS = (ROLE_FINANCE_CONFIRMATION_OFFICER, ROLE_PROCUREMENT_PLANNER, ROLE_ACCOUNTING_OFFICER, ROLE_AUDITOR)


# --------------------------------------------------------------------------
# facts read once per Home read
# --------------------------------------------------------------------------


def _people(holder: Any) -> tuple[str, list[str]]:
	"""(display, names) of a next-step holder: up to two names, otherwise the responsibility (never an invented person)."""
	holder = holder or {}
	names = [cstr(name) for name in holder.get("people") or [] if cstr(name)]
	role = cstr(holder.get("role"))
	return (" or ".join(names) if names and len(names) <= MAX_NAMED else role or " or ".join(names)), names


def _instant(value: Any):
	return get_datetime(value) if value else None


def _latest(doctype: str, filters: dict[str, Any], field: str):
	return frappe.db.get_value(doctype, filters, field, order_by=f"{field} desc")


class _Facts:
	"""What one actor's Home read needs more than once: plan and department titles and the owner's guidance per Version."""

	def __init__(self, user: str):
		self.user = user
		self._plans: dict[str, Any] = {}
		self._units: dict[str, str] = {}
		self._versions: dict[str, Any] = {}
		self.guidance: dict[str, dict[str, Any]] = {}

	def version(self, name: str):
		if name not in self._versions:
			self._versions[name] = frappe.db.get_value("Annual Plan Version", name, ["name", "annual_plan", "version_number", "version_status", "modified"], as_dict=True)
		return self._versions[name]

	def plan(self, annual_plan: str):
		if annual_plan not in self._plans:
			self._plans[annual_plan] = frappe.db.get_value("Annual Plan", annual_plan, ["name", "plan_reference", "title"], as_dict=True)
		return self._plans[annual_plan]

	def plan_title(self, plan) -> str:
		return cstr(plan.title or plan.plan_reference).strip()

	def unit(self, organisation_unit: str) -> str:
		"""The department's name: a departmental plan has no title of its own."""
		if organisation_unit not in self._units:
			self._units[organisation_unit] = cstr(frappe.db.get_value("Organisation Unit", organisation_unit, "unit_name") or organisation_unit)
		return self._units[organisation_unit]

	def plan_reference(self, version) -> str:
		return f"{self.plan(version.annual_plan).plan_reference} · Version {version.version_number}"

	def guidance_for(self, version_name: str) -> dict[str, Any]:
		"""The owner's answer for the actor on this Version, read once (the hand-off scan has already read every open one)."""
		if version_name not in self.guidance:
			doc = frappe.get_doc("Annual Plan Version", version_name)
			self.guidance[version_name] = plan_read._guidance_for(doc, frappe.get_doc("Annual Plan", doc.annual_plan), self.user)
		return self.guidance[version_name]


def _blocking(guidance: dict[str, Any], *, governance: bool = False) -> tuple[bool, str]:
	"""Blocked only where the owner's own answer for this item is Your turn, blocked; its headline is the reason (the one blocker's
	headline when the step names a single blocker). A governance turn the owner marks blocked on its journey — the positive decision
	cannot be taken until the plan has a new funding check — is blocked too."""
	step = guidance["next_step"]
	headline = cstr(step.get("headline")).strip()
	if step.get("kind") == ns.KIND_BLOCKED:
		blockers = step.get("blockers") or []
		reason = cstr(blockers[0].get("headline")).strip() if len(blockers) == 1 else headline
		return (True, reason or headline) if (reason or headline) else (False, "")
	if governance and step.get("kind") == ns.KIND_YOUR_TURN and headline:
		stages = (guidance.get("journey") or {}).get("stages") or []
		if any(row.get("marker") == ns.MARKER_BLOCKED and row.get("code") == step.get("stage") for row in stages):
			return True, headline
	return False, ""


# --------------------------------------------------------------------------
# My work
# --------------------------------------------------------------------------


def _route(row: dict[str, Any]) -> dict[str, Any]:
	return {"route": list(row["route"]), "route_options": dict(row.get("route_options") or {})}


def _hand_off_instant(kind: str, doc):
	"""When the actor's turn at this hand-off began: the event that created it where one is recorded (the Finance decision, the
	Budget outcome, the governance decision, the hold), otherwise None and the caller falls back to the Version's `modified`, the
	owner's own approximation. `add_requirements` always falls back: nothing records when a requirement became unallocated."""
	from kentender_procurement.procurement_planning.services import plan_finance

	version = doc.name
	if kind == "finance_return":
		tasks = frappe.get_all("Plan Finance Task", filters={"plan_version": version}, pluck="name")
		return _latest("Plan Finance Decision", {"task": ("in", tasks or [""]), "decision": "Return to planner"}, "decided_at")
	if kind == "budget_outcome":
		return _latest("Plan Budget Revision Request", {"plan_version": version, "status": ("in", ("Revised", "Declined"))}, "outcome_at")
	if kind == "governance_return":
		return _latest("Plan Governance Decision", {"plan_version": doc.correction_of_plan_version or "", "decision": ("in", ("Return for correction", "Withdraw for correction"))}, "decided_at")
	if kind == "sign":
		confirmed = plan_finance._confirmed_decision(version)
		return confirmed.decided_at if confirmed else None
	if kind == "publication":
		return _latest("Plan Governance Decision", {"plan_version": version, "decision": "Approve Annual Procurement Plan"}, "decided_at")
	if kind == "withdrawal_request":
		return _latest("Plan Publication Hold", {"plan_version": version, "hold_state": "Active"}, "raised_at")
	if kind == "withdrawal_decision":
		return frappe.db.get_value("Plan Governance Task", {"plan_version": version, "task_reference": f"SAT-WD-{version}", "status": "Open"}, "creation")
	if kind == "continue_correction":
		return _latest("Plan Governance Decision", {"plan_version": version, "decision": "Withdraw for correction"}, "decided_at")
	if kind == "corrected_plan":
		return _latest("Plan Publication Confirmation", {"plan_version": version, "confirmation_state": "Current"}, "recorded_at")
	return None  # add_requirements: nothing records when a requirement became unallocated


def _dpp_root(dpp_version: str):
	return frappe.db.get_value("Departmental Plan Version", dpp_version, "departmental_plan")


def _task_entry(row: dict[str, Any], facts: _Facts) -> dict[str, Any] | None:
	"""(root, title, action, entered_at, blocked, reason) for a task-backed or derived row; None when its record is gone."""
	kind, name = row["task_type"], row["task_id"]
	blocked, reason = False, ""
	if kind == "planning.dpp_validation":
		task = frappe.db.get_value("Departmental Plan Validation Task", name, ["dpp_version", "organisation_unit", "creation"], as_dict=True)
		if not task:
			return None
		return {"root": _dpp_root(task.dpp_version) or name, "title": facts.unit(task.organisation_unit), "action": ACTION[kind], "entered_at": task.creation}
	if kind in ("planning.finance", "planning.governance"):
		doctype = "Plan Finance Task" if kind == "planning.finance" else "Plan Governance Task"
		task = frappe.db.get_value(doctype, name, ["plan_version", "creation"] + (["stage"] if kind == "planning.governance" else []), as_dict=True)
		version = facts.version(task.plan_version) if task else None
		if not version:
			return None
		blocked, reason = _blocking(facts.guidance_for(version.name), governance=kind == "planning.governance")
		action = GOVERNANCE_ACTION.get(cstr(task.get("stage")), "Decide Annual Procurement Plan") if kind == "planning.governance" else ACTION[kind]
		plan = facts.plan(version.annual_plan)
		return {"root": plan.name, "title": facts.plan_title(plan), "action": action, "entered_at": task.creation, "blocked": blocked, "reason": reason}
	if kind == "planning.plan_item_correction":
		request = frappe.db.get_value("Plan Item Correction Request", name, ["plan_item", "plan_version", "requested_at", "creation"], as_dict=True)
		version = facts.version(request.plan_version) if request and request.plan_version else None
		if not version:
			return None
		plan = facts.plan(version.annual_plan)
		item = cstr(frappe.db.get_value("Annual Plan Item", request.plan_item, "title")) if request.plan_item else ""
		return {"root": plan.name, "title": item.strip() or facts.plan_title(plan), "action": ACTION[kind], "entered_at": request.requested_at or request.creation}
	if kind == "planning.dpp_update_required":
		root = frappe.db.get_value("Departmental Plan", name.split(":", 1)[0], ["name", "organisation_unit", "current_state", "current_version", "current_accepted_version", "modified"], as_dict=True)
		if not root:
			return None
		from kentender_procurement.procurement_planning.services import needs_intake

		since = needs_intake.late_needs_since(needs_intake.late_needs(root))  # when the plan started missing a Need: a recorded acceptance
		return {"root": root.name, "title": facts.unit(root.organisation_unit), "action": ACTION[kind], "entered_at": since or root.modified}
	if kind == "planning.dpp_update_requested":
		request = frappe.db.get_value("Departmental Plan Update Request", name, ["departmental_plan", "organisation_unit", "requested_at", "creation"], as_dict=True)
		if not request:
			return None
		return {"root": request.departmental_plan, "title": facts.unit(request.organisation_unit), "action": ACTION[kind], "entered_at": request.requested_at or request.creation}
	return None


def _hand_off_entry(row: dict[str, Any], doc, plan, guidance: dict[str, Any], facts: _Facts) -> dict[str, Any]:
	kind = row["task_type"].split(".", 1)[1]
	blocked, reason = _blocking(guidance)
	return {
		"root": plan.name, "title": facts.plan_title(plan), "action": ACTION[row["task_type"]], "blocked": blocked, "reason": reason,
		"entered_at": _hand_off_instant(kind, doc) or doc.modified,
	}


def _dpp_return_entry(row: dict[str, Any], facts: _Facts) -> dict[str, Any] | None:
	root = frappe.db.get_value("Departmental Plan", row["task_id"].split(":", 1)[0], ["name", "organisation_unit", "current_version"], as_dict=True)
	version = frappe.db.get_value("Departmental Plan Version", root.current_version, ["returned_from_submission", "modified"], as_dict=True) if root and root.current_version else None
	if not version:
		return None
	task = frappe.db.get_value("Departmental Plan Validation Task", {"submission": version.returned_from_submission}, "decision") if version.returned_from_submission else None
	returned = frappe.db.get_value("Departmental Plan Validation Decision", task, "decided_at") if task else None
	return {"root": root.name, "title": facts.unit(root.organisation_unit), "action": ACTION["planning.dpp_return"], "entered_at": returned or version.modified}


# --------------------------------------------------------------------------
# Waiting
# --------------------------------------------------------------------------


def _dpp_planning_since(root_name: str):
	"""The owner's "Waiting for planning" row carries no instant: when the department's plan was accepted is when the
	requirements were handed to Planning."""
	version = frappe.db.get_value("Departmental Plan", root_name, "current_accepted_version")
	submission = frappe.db.get_value("Departmental Plan Submission", {"dpp_version": version}, "name") if version else None
	task = frappe.db.get_value("Departmental Plan Validation Task", {"submission": submission}, "decision") if submission else None
	return frappe.db.get_value("Departmental Plan Validation Decision", task, "decided_at") if task else None


# --------------------------------------------------------------------------
# One scan per Home read
# --------------------------------------------------------------------------


def _register(user: str) -> dict[str, Any]:
	"""{"my_work": […], "waiting": […], "waits": {version or departmental plan: (clause phrase, holder)}} for one Home read."""
	facts = _Facts(user)
	my_work: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	waits: dict[str, tuple[str, str]] = {}

	def add_work(row: dict[str, Any], fact: dict[str, Any] | None) -> None:
		if not fact:
			return
		my_work.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=fact["root"], action_id=row["task_id"], title=fact["title"], reference=row["reference"], action=fact["action"],
			destination=_route(row), entered_at=fact["entered_at"], entered_verb="Received", blocked=fact.get("blocked", False), reason=fact.get("reason", ""),
		))

	def add_wait(row: dict[str, Any], *, root: str, title: str, since: Any, key: str, phrase: str) -> None:
		display, names = _people(row.get("holder"))
		if not since or not display:
			frappe.logger("kentender.home").info("planning wait skipped, no recorded since or holder | %s", row["task_id"])
			return
		waiting.append(he.make(
			region=he.WAITING, owner=OWNER, root=root, action_id=row["task_id"], title=title, reference=row["reference"], action=row["title"],
			destination=_route(row), holder=display, since=_instant(since),
		))
		if names and phrase and key not in waits:
			waits[key] = (phrase, display)

	# the plan hand-offs first: they read the owner's guidance for every open Version, and the task rows below reuse it
	for bucket, row, doc, plan, guidance in work.plan_handoff_items(user):
		facts.guidance[doc.name] = guidance
		if bucket == "assigned":
			add_work(row, _hand_off_entry(row, doc, plan, guidance, facts))
		else:
			stage = row["task_id"].rsplit(":", 1)[1]
			add_wait(row, root=plan.name, title=facts.plan_title(plan), since=(row.get("since") or {}).get("at"), key=doc.name, phrase=AWAITING.get(stage, ""))
	for builder in (work._validation_rows, work._finance_rows, work._governance_rows, work._correction_request_rows, work._update_required_rows, work._update_request_rows):
		for row in builder(user):
			add_work(row, _task_entry(row, facts))
	dpp_assigned, dpp_waiting = work._dpp_handoff_rows(user)
	for row in dpp_assigned:
		add_work(row, _dpp_return_entry(row, facts))
	for row in dpp_waiting:
		root_name = row["task_id"].split(":", 1)[0]
		root = frappe.db.get_value("Departmental Plan", root_name, ["name", "organisation_unit"], as_dict=True)
		if not root:
			continue
		review = row["task_id"].endswith(":waiting:review")
		since = (row.get("since") or {}).get("at") if review else _dpp_planning_since(root.name)
		add_wait(row, root=root.name, title=facts.unit(root.organisation_unit), since=since, key=root.name, phrase=AWAITING["review"] if review else "")
	return {"my_work": my_work, "waiting": waiting, "waits": waits}


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _can_read_plan(user: str, roles: tuple[str, ...]) -> bool:
	return any(authz.can_read_site(role, user) for role in roles)


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	waits = home_support.memo("planning.register", lambda: _register(user), user=user)["waits"]
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	out: list[dict[str, Any]] = []

	def add(*, name: str, root: str, title: str, reference: str, route: list[str], wording: tuple[str, str], when: Any, wait: str = "") -> None:
		follow = ""
		if wait in waits:
			follow = home_time.awaiting(waits[wait][0], waits[wait][1])
		out.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=root, action_id=name, title=title, reference=reference, action=wording[0],
			destination={"route": route}, completed_at=when, sentence=home_time.completed_sentence(wording[1], when, follow=follow),
		))

	def plan_view(version_name: str):
		version = facts.version(version_name) if version_name else None
		plan = facts.plan(version.annual_plan) if version else None
		return (version, plan) if plan else (None, None)

	def add_plan(row, version_name: str, wording: tuple[str, str], when: Any, roles: tuple[str, ...]) -> None:
		version, plan = plan_view(version_name)
		if not plan or not _can_read_plan(user, roles):
			return
		add(name=row.name, root=plan.name, title=facts.plan_title(plan), reference=facts.plan_reference(version), route=[PLAN_PAGE, plan.plan_reference], wording=wording, when=when, wait=version.name)

	for row in frappe.get_all("Plan Finance Decision", filters={"actor": user, "decided_at": (">=", cutoff)}, fields=["name", "task", "decision", "decided_at"], limit_page_length=0):
		wording = FINANCE_DECISIONS.get(cstr(row.decision))
		if wording:
			add_plan(row, frappe.db.get_value("Plan Finance Task", row.task, "plan_version"), wording, row.decided_at, FINANCE_READERS)
	for row in frappe.get_all("Plan Governance Decision", filters={"actor": user, "decided_at": (">=", cutoff)}, fields=["name", "plan_version", "stage", "decision", "decided_at"], limit_page_length=0):
		wording = GOVERNANCE_DECISIONS.get(cstr(row.decision))
		stage_role = ROLE_ACCOUNTING_OFFICER if cstr(row.stage) == "Accounting Officer adoption" else ROLE_PLAN_STATUTORY_APPROVER
		if wording:
			add_plan(row, row.plan_version, wording, row.decided_at, (stage_role, ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR))
	for row in frappe.get_all("Plan Preparation Signature", filters={"actor": user, "signed_at": (">=", cutoff)}, fields=["name", "plan_version", "signed_at"], limit_page_length=0):
		add_plan(row, row.plan_version, SIGNED, row.signed_at, plan_read.PLAN_READERS)
	for row in frappe.get_all("Plan Publication Confirmation", filters={"actor": user, "recorded_at": (">=", cutoff), "confirmation_state": ("in", ("Current", "Superseded"))}, fields=["name", "plan_version", "recorded_at"], limit_page_length=0):
		add_plan(row, row.plan_version, PUBLICATION, row.recorded_at, plan_read.PLAN_READERS)

	def add_dpp(row, root_name: str, unit: str, wording: tuple[str, str], when: Any) -> None:
		root = frappe.db.get_value("Departmental Plan", root_name, ["name", "dpp_reference", "organisation_unit"], as_dict=True) if root_name else None
		if not root or not authz.dpp_read_profile(unit or root.organisation_unit, user):
			return
		add(name=row.name, root=root.name, title=facts.unit(unit or root.organisation_unit), reference=cstr(root.dpp_reference), route=[DPP_PAGE, cstr(root.dpp_reference)], wording=wording, when=when, wait=root.name)

	for row in frappe.get_all("Departmental Plan Validation Decision", filters={"actor": user, "decided_at": (">=", cutoff)}, fields=["name", "task", "decision", "decided_at"], limit_page_length=0):
		wording = VALIDATION_DECISIONS.get(cstr(row.decision))
		task = frappe.db.get_value("Departmental Plan Validation Task", row.task, ["dpp_version", "organisation_unit"], as_dict=True) if wording else None
		if task:
			add_dpp(row, _dpp_root(task.dpp_version), task.organisation_unit, wording, row.decided_at)
	for row in frappe.get_all("Departmental Plan Submission", filters={"submitted_by_user": user, "submitted_at": (">=", cutoff)}, fields=["name", "dpp_version", "submitted_at"], limit_page_length=0):
		add_dpp(row, _dpp_root(row.dpp_version), "", SUBMITTED, row.submitted_at)
	for row in frappe.get_all("Plan Item Correction Disposition", filters={"actor": user, "disposed_at": (">=", cutoff)}, fields=["name", "correction_request", "action", "disposed_at"], limit_page_length=0):
		wording = DISPOSITIONS.get(cstr(row.action))
		request = frappe.db.get_value("Plan Item Correction Request", row.correction_request, ["name", "plan_item", "plan_version"], as_dict=True) if wording else None
		version, plan = plan_view(request.plan_version) if request else (None, None)
		if not plan or not _can_read_plan(user, (ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR)):
			continue
		item = cstr(frappe.db.get_value("Annual Plan Item", request.plan_item, "title")).strip() if request.plan_item else ""
		add(name=row.name, root=plan.name, title=item or facts.plan_title(plan), reference=cstr(frappe.db.get_value("Plan Item Correction Request", request.name, "requisition_reference")),
			route=[PLANNING_PAGE, "correction-request", request.name], wording=wording, when=row.disposed_at)
	return out


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def _applies(user: str) -> bool:
	return home_support.memo("planning.applies", lambda: not is_technical(user) and authz.holds_any_planning_responsibility(user), user=user)


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region in (he.COMING_UP, he.OVERSIGHT) or not _applies(user):
		return None
	if region == he.COMPLETED:
		return home_support.memo("planning.completed", lambda: _completed(user), user=user)
	return home_support.memo("planning.register", lambda: _register(user), user=user)[region]
