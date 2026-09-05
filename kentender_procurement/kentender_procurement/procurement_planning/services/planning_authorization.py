# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §6 / §16.4 — Planning authorisation on the shared
AUTH-ADR-001 v1.6 resolver (tracker D2–D5).

One vocabulary for every Planning list, count, detail and command: a
role-bound `User Responsibility Assignment` resolved by
`kentender_core.services.authorization`. Departmental Author and Head of User
Department are Organisation-Unit scoped (the DPP's unit must fall inside an
assigned subtree); Procurement Planner, Finance Confirmation Officer,
Accounting Officer, Plan Statutory Approver and Auditor are Site-wide. A
Frappe Role, a framework permission row, a task or a browser value grants nothing.
Fiscal Year is never a user grant (§6).

Resolver codes never reach a client: record-addressed reads and commands mask
to not-found (§9), context and creation resolve to `PLN_NO_CONTEXT`, and the
remaining codes map onto the closed §9 set below (D4). Administrator and
System Manager read everything and decide nothing (AUTH §8).

§6.1 maker-checker is evaluated from the evidence itself (D5): the Plan
Version chain linked through `correction_of_plan_version`, the actors named
on submissions, decisions and the Planning Command Journal. No extra field.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import (
	PURPOSE_COMMAND,
	PURPOSE_READ,
	Assignment,
	assignment_snapshot,
	authorise_record,
	is_technical,
	permitted_ou_scopes,
)
from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services.planning_roles import (
	ALL_PLANNING_ROLES,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

# AUTH-ADR-001 v1.6 §10 → PLN-CHG-001 v1.12 §9 (unmasked paths only).
_AUTH_TO_PLN: dict[str, str] = {
	"AUTH_RESPONSIBILITY_REQUIRED": "PLN_NO_CONTEXT",
	"AUTH_SCOPE_REQUIRED": "PLN_NO_CONTEXT",
	"AUTH_ASSIGNMENT_INACTIVE": "PLN_NO_CONTEXT",
	"AUTH_SEGREGATION_BLOCKED": "PLN_SEGREGATION_CONFLICT",
	"AUTH_TASK_REQUIRED": "PLN_REVIEW_STALE",
	"AUTH_STATE_CHANGED": "PLN_REVIEW_STALE",
	"AUTH_PERIOD_UNAVAILABLE": "PLN_WINDOW_CLOSED",
	"AUTH_CONFIGURATION_INVALID": "PLN_NO_CONTEXT",
}

# Planner commands that put an actor on a Plan Version's evidence chain (§6.1).
PLANNER_CHAIN_COMMANDS = (
	"FormPlanItems",
	"DissolvePlanItem",
	"SavePlanItem",
	"ConfirmSplittingAdvisory",
	"RequestPlanFundingConfirmation",
	"SubmitConsolidatedPlan",
	"SubmitCorrectedPlan",
	"RemovePlanItemInSuccessor",
	"BeginPlanUpdate",
)

ACTION_FINANCE_DECIDE = "finance_decide"
ACTION_AO_DECIDE = "ao_decide"
ACTION_STATUTORY_DECIDE = "statutory_decide"
ACTION_DPP_VALIDATE = "dpp_validate"


def not_found() -> None:
	"""§9: unauthorised detail/task reads look exactly like a missing record."""
	raise frappe.DoesNotExistError("Not found")


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		fail("PLN_NO_CONTEXT", "Sign in to access Procurement Planning.")
	return value


def _deny(decision, *, masked: bool) -> None:
	if masked:
		not_found()
	fail(_AUTH_TO_PLN.get(decision.reason_code, "PLN_NO_CONTEXT"))


# --------------------------------------------------------------------------
# Departmental (Organisation Unit scoped) responsibilities
# --------------------------------------------------------------------------


def _first_allowed(user: str, roles: tuple[str, ...], organisation_unit: str, purpose: str):
	last = None
	for role in roles:
		decision = authorise_record(
			user=user, business_role=role, organisation_unit=cstr(organisation_unit), purpose=purpose
		)
		if decision.allowed:
			return decision
		last = decision
	return last


def require_dpp_author(organisation_unit: str, user: str | None = None, *, masked: bool = True) -> Assignment:
	"""§5.1 — Departmental Author or Head of User Department, active for the
	DPP's unit (or an ancestor). Returns the exact assignment exercised."""
	principal = actor(user)
	decision = _first_allowed(
		principal, (ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_DEPARTMENTAL_AUTHOR), organisation_unit, PURPOSE_COMMAND
	)
	if not decision.allowed:
		_deny(decision, masked=masked)
	return decision.assignment


def require_dpp_hod(organisation_unit: str, user: str | None = None, *, masked: bool = True) -> Assignment:
	"""§5.1 / §12.5 — certify, submit, resubmit or withdraw: an active Head of
	User Department assignment (substantive or Acting) covering the unit."""
	principal = actor(user)
	decision = authorise_record(
		user=principal,
		business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
		organisation_unit=cstr(organisation_unit),
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		_deny(decision, masked=masked)
	return decision.assignment


def dpp_read_profile(organisation_unit: str, user: str | None = None) -> str:
	"""One scope predicate for every DPP read path: `hod`, `author`,
	`planner`, `oversight` or "" (the caller masks)."""
	principal = actor(user)
	if is_technical(principal):
		return "oversight"
	ou = cstr(organisation_unit)
	if authorise_record(user=principal, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=ou, purpose=PURPOSE_READ).allowed:
		return "hod"
	if authorise_record(user=principal, business_role=ROLE_DEPARTMENTAL_AUTHOR, organisation_unit=ou, purpose=PURPOSE_READ).allowed:
		return "author"
	if authorise_record(user=principal, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="", purpose=PURPOSE_READ).allowed:
		return "planner"
	if authorise_record(user=principal, business_role=ROLE_AUDITOR, organisation_unit="", purpose=PURPOSE_READ).allowed:
		return "oversight"
	return ""


def require_dpp_read(organisation_unit: str, user: str | None = None) -> str:
	profile = dpp_read_profile(organisation_unit, user)
	if not profile:
		not_found()
	return profile


def creation_units(user: str | None = None) -> list[dict[str, str]]:
	"""§12.1 — the units a departmental user may open a DPP for (Author ∪ HoD
	subtrees). Technical users get none: setup authority is not business
	authority (AUTH §8)."""
	principal = actor(user)
	if is_technical(principal):
		return []
	units: set[str] = set()
	for role in (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT):
		scope = permitted_ou_scopes(principal, role)
		if scope:
			units |= scope
	if not units:
		return []
	rows = frappe.get_all(
		"Organisation Unit",
		filters={"name": ("in", sorted(units)), "status": "Active"},
		fields=["name", "unit_name", "unit_code"],
		order_by="unit_name asc",
		limit_page_length=0,
	)
	return [{"id": r.name, "name": r.unit_name, "code": r.unit_code} for r in rows]


def workspace_units(user: str | None = None) -> set[str] | None:
	"""§12.1 — the DPP rows a workspace may list: `None` = every unit (a
	Site-wide Planning responsibility or a technical reader), else the
	departmental subtrees."""
	principal = actor(user)
	if is_technical(principal):
		return None
	for role in (ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR, ROLE_FINANCE_CONFIRMATION_OFFICER, ROLE_ACCOUNTING_OFFICER, ROLE_PLAN_STATUTORY_APPROVER):
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return None
	units: set[str] = set()
	for role in (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT):
		scope = permitted_ou_scopes(principal, role)
		if scope:
			units |= scope
	return units


# --------------------------------------------------------------------------
# Site-wide responsibilities
# --------------------------------------------------------------------------


def require_site_role(role: str, user: str | None = None, *, masked: bool = True) -> Assignment:
	principal = actor(user)
	decision = authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
	if not decision.allowed:
		_deny(decision, masked=masked)
	return decision.assignment


def has_site_role(role: str, user: str | None = None) -> bool:
	"""Command-purpose check for read-offer parity: a control is offered only
	to an actor the command would accept (technical users get no offer)."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	return authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed


def can_read_site(role: str, user: str | None = None) -> bool:
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	return authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed


def require_site_read(roles: tuple[str, ...], user: str | None = None) -> str:
	"""Masked read gate for Site-wide surfaces: the first role that admits the
	actor (technical readers pass as `oversight`)."""
	principal = actor(user)
	if is_technical(principal):
		return "oversight"
	for role in roles:
		if can_read_site(role, principal):
			return role
	not_found()
	return ""


def holds_any_planning_responsibility(user: str | None = None) -> bool:
	"""PLN-AC-111 — the page-level verdict resolved before anything renders."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	if is_technical(principal):
		return True
	for role in ALL_PLANNING_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return True
		if role in (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT) and permitted_ou_scopes(principal, role):
			return True
	return False


def require_technical(user: str | None = None) -> str:
	principal = actor(user)
	if not is_technical(principal):
		not_found()
	return principal


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------


def authority_snapshot(assignment: Assignment | None) -> str:
	"""§4.5/§4.6/§4.11/§4.12 — the exact assignment exercised, copied (never
	linked alone) so later changes never rewrite decision evidence (§13),
	plus the site PE code so the stored text literally carries role/PE/OU/
	effective period."""
	payload = json.loads(assignment_snapshot(assignment))
	payload["site_pe_code"] = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	return json.dumps(payload, sort_keys=True)


# --------------------------------------------------------------------------
# §6.1 maker-checker
# --------------------------------------------------------------------------


def evidence_chain(plan_version: str) -> list[str]:
	"""The Version plus every correction linked through
	`correction_of_plan_version`, walked in both directions within one Annual
	Plan. A successor reached only through `based_on_version` starts a new
	chain; a correction never resets segregation history (§6.1)."""
	start = frappe.db.get_value("Annual Plan Version", plan_version, ["name", "annual_plan"], as_dict=True)
	if not start:
		return []
	rows = frappe.get_all(
		"Annual Plan Version",
		filters={"annual_plan": start.annual_plan},
		fields=["name", "correction_of_plan_version"],
		limit_page_length=0,
	)
	parent = {r.name: cstr(r.correction_of_plan_version) for r in rows}
	children: dict[str, list[str]] = {}
	for name, corrected in parent.items():
		if corrected:
			children.setdefault(corrected, []).append(name)
	seen, stack = set(), [start.name]
	while stack:
		node = stack.pop()
		if node in seen:
			continue
		seen.add(node)
		if parent.get(node):
			stack.append(parent[node])
		stack.extend(children.get(node, []))
	return sorted(seen)


def prior_actors(chain: list[str]) -> dict[str, set[str]]:
	if not chain:
		return {"planner": set(), "finance": set(), "ao": set()}
	versions = frappe.get_all(
		"Annual Plan Version",
		filters={"name": ("in", chain)},
		fields=["name", "owner", "submitted_by_user", "correction_of_plan_version"],
		limit_page_length=0,
	)
	planner: set[str] = set()
	for v in versions:
		if v.submitted_by_user:
			planner.add(cstr(v.submitted_by_user))
		# V1 (created inside AcceptDepartmentalPlan by the Planner) and a
		# BeginPlanUpdate successor are Planner-created; a correction Draft is
		# created by a governance return and its owner is not a Planner action.
		if not v.correction_of_plan_version and v.owner and v.owner != "Administrator":
			planner.add(cstr(v.owner))
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": ("in", chain)}, pluck="name")
	tasks = frappe.get_all("Plan Finance Task", filters={"plan_version": ("in", chain)}, pluck="name")
	journal_targets = set(chain) | set(items) | set(tasks)
	if journal_targets:
		for row in frappe.get_all(
			"Planning Command Journal",
			filters={
				"command": ("in", PLANNER_CHAIN_COMMANDS),
				"document_name": ("in", sorted(journal_targets)),
			},
			fields=["actor"],
			limit_page_length=0,
		):
			planner.add(cstr(row.actor))
	finance = set()
	if tasks:
		finance = {
			cstr(r.actor)
			for r in frappe.get_all("Plan Finance Decision", filters={"task": ("in", tasks)}, fields=["actor"])
		}
	ao = {
		cstr(r.actor)
		for r in frappe.get_all(
			"Plan Governance Decision",
			filters={"plan_version": ("in", chain), "stage": "Accounting Officer adoption"},
			fields=["actor"],
		)
	}
	planner.discard("Administrator")
	return {"planner": planner, "finance": finance, "ao": ao}


def is_segregated(user: str, later_action: str, *, plan_version: str = "", submission: str = "") -> bool:
	if later_action == ACTION_DPP_VALIDATE:
		submitted_by = cstr(frappe.db.get_value("Departmental Plan Submission", submission, "submitted_by_user"))
		return bool(submitted_by) and submitted_by == user
	actors = prior_actors(evidence_chain(plan_version))
	if later_action == ACTION_FINANCE_DECIDE:
		return user in actors["planner"]
	if later_action == ACTION_AO_DECIDE:
		return user in actors["planner"] or user in actors["finance"]
	if later_action == ACTION_STATUTORY_DECIDE:
		return user in actors["planner"] or user in actors["finance"] or user in actors["ao"]
	return False


def require_not_segregated(user: str, later_action: str, *, plan_version: str = "", submission: str = "") -> None:
	if is_segregated(user, later_action, plan_version=plan_version, submission=submission):
		fail("PLN_SEGREGATION_CONFLICT")


# --------------------------------------------------------------------------
# Frappe permission hooks for the DPP family without an OU column (D3)
# --------------------------------------------------------------------------

_PARENT_PATH = {
	"Departmental Plan Version": ("departmental_plan", "Departmental Plan"),
	"Departmental Plan Entry": ("dpp_version", "Departmental Plan Version"),
	"Departmental Plan Submission": ("dpp_version", "Departmental Plan Version"),
	"Departmental Plan Validation Decision": ("task", "Departmental Plan Validation Task"),
}


def _root_unit_of(doctype: str, name: str) -> str:
	current_doctype, current_name = doctype, name
	for _ in range(4):
		if current_doctype == "Departmental Plan":
			return cstr(frappe.db.get_value("Departmental Plan", current_name, "organisation_unit"))
		if current_doctype == "Departmental Plan Validation Task":
			return cstr(frappe.db.get_value("Departmental Plan Validation Task", current_name, "organisation_unit"))
		link, parent_doctype = _PARENT_PATH[current_doctype]
		current_name = cstr(frappe.db.get_value(current_doctype, current_name, link))
		current_doctype = parent_doctype
		if not current_name:
			return ""
	return ""


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""List/count predicate for a DPP-family DocType: delegate to the root's
	own registered condition through the parent chain."""
	from kentender_core.services.authorization import scope_condition

	principal = cstr(user or frappe.session.user)
	if is_technical(principal):
		return ""
	root_condition = scope_condition("Departmental Plan", principal)
	if root_condition == "":
		return ""
	if root_condition.strip() in ("1=0", "(1=0)"):
		return "1=0"
	if doctype == "Departmental Plan Version":
		return f"`tabDepartmental Plan Version`.`departmental_plan` in (select name from `tabDepartmental Plan` where {root_condition})"
	if doctype in ("Departmental Plan Entry", "Departmental Plan Submission"):
		return (
			f"`tab{doctype}`.`dpp_version` in (select name from `tabDepartmental Plan Version` where "
			f"`departmental_plan` in (select name from `tabDepartmental Plan` where {root_condition}))"
		)
	if doctype == "Departmental Plan Validation Decision":
		task_condition = scope_condition("Departmental Plan Validation Task", principal)
		if task_condition == "":
			return ""
		return f"`tabDepartmental Plan Validation Decision`.`task` in (select name from `tabDepartmental Plan Validation Task` where {task_condition})"
	return "1=0"


def has_permission(doc=None, ptype: str = "read", user: str | None = None):
	from kentender_core.services.authorization import has_permission as core_has_permission

	principal = cstr(user or frappe.session.user)
	if doc is None:
		return True
	doctype = getattr(doc, "doctype", None) or (doc.get("doctype") if isinstance(doc, dict) else "")
	name = getattr(doc, "name", None) or (doc.get("name") if isinstance(doc, dict) else "")
	unit = _root_unit_of(doctype, name) if name else ""
	proxy = frappe._dict({"doctype": "Departmental Plan", "name": name, "organisation_unit": unit})
	return core_has_permission(proxy, ptype, principal)
