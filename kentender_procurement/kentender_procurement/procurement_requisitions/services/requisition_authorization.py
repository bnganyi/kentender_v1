# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §8 — Requisitions authorisation on the shared
AUTH-ADR-001 v1.6 resolver.

One vocabulary for every Requisitions list, count, detail and command: a
role-bound `User Responsibility Assignment` resolved by
`kentender_core.services.authorization`. Departmental Author and Head of
User Department are Organisation-Unit scoped; Head of Procurement Function,
Procurement Planner and Auditor are Site-wide. A Frappe Role, a framework
permission row, a task or a browser value grants nothing.

A `Procurement Requisition` has no single `organisation_unit` column — it
may have more than one contributing department (§2.1's narrow cross-
department relaxation), recorded as a child table
(`Requisition Contributing Unit`). This is why the module cannot simply
register a `kentender_scope_map` entry the way a single-OU doctype would
(Planning's own `Departmental Plan` precedent): the query condition and the
record-level check both need an EXISTS subquery over that child table
instead of a denormalised column comparison. Version/Task/Decision/Package/
PackageVersion/Handoff carry no Organisation Unit of their own; their own
`permission_query_conditions`/`has_permission` registrations delegate to the
owning Requisition's own condition, exactly as Planning's DPP family
delegates to `Departmental Plan` (see `_PARENT_PATH`/`_root_requisition_of`
below).

Resolver codes never reach a client: record-addressed reads and commands
mask to not-found (§11), and every remaining condition maps onto the closed
§11 set (see `errors.py`). Administrator and System Manager read everything
and decide nothing (AUTH §8).
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
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import (
	DEPARTMENTAL_ROLES,
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	SITE_WIDE_ROLES,
)

# AUTH-ADR-001 v1.6 §10 → REQ-CHG-001 v1.6 §11 (unmasked paths only).
_AUTH_TO_REQ: dict[str, str] = {
	"AUTH_RESPONSIBILITY_REQUIRED": "REQ_RESPONSIBILITY_REQUIRED",
	"AUTH_SCOPE_REQUIRED": "REQ_RESPONSIBILITY_REQUIRED",
	"AUTH_ASSIGNMENT_INACTIVE": "REQ_RESPONSIBILITY_REQUIRED",
	"AUTH_SEGREGATION_BLOCKED": "REQ_SOD_BLOCKED",
	"AUTH_TASK_REQUIRED": "REQ_STALE_VERSION",
	"AUTH_STATE_CHANGED": "REQ_STALE_VERSION",
	"AUTH_PERIOD_UNAVAILABLE": "REQ_RESPONSIBILITY_REQUIRED",
	"AUTH_CONFIGURATION_INVALID": "REQ_RESPONSIBILITY_REQUIRED",
}


def not_found() -> None:
	"""§11: unauthorised detail/task reads look exactly like a missing record."""
	raise frappe.DoesNotExistError("Not found")


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		fail("REQ_RESPONSIBILITY_REQUIRED", "Sign in to access Procurement Requisitions.")
	return value


def _deny(decision, *, masked: bool) -> None:
	if masked:
		not_found()
	fail(_AUTH_TO_REQ.get(decision.reason_code, "REQ_RESPONSIBILITY_REQUIRED"))


def require_site_role(role: str, user: str | None = None, *, masked: bool = True) -> Assignment:
	principal = actor(user)
	decision = authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
	if not decision.allowed:
		_deny(decision, masked=masked)
	return decision.assignment


def can_read_site(role: str, user: str | None = None) -> bool:
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	return authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed


def has_site_role(role: str, user: str | None = None) -> bool:
	"""Command-purpose check for read-offer parity: a control is offered
	only to an actor the command layer would accept."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	return authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed


def require_requisition_reader(actor_name: str, *, contributing_org_units: set[str]) -> None:
	"""§5A/§8 — the Site-wide roles read unconditionally; the two
	Organisation-Unit-scoped roles only for a Requisition whose contributing
	departments they hold (never one a department did not contribute to)."""
	if is_technical(actor_name):
		return
	for role in SITE_WIDE_ROLES:
		if can_read_site(role, actor_name):
			return
	for role in DEPARTMENTAL_ROLES:
		scope = permitted_ou_scopes(actor_name, role)
		if scope and scope & contributing_org_units:
			return
	not_found()


def require_departmental_author(organisation_unit: str, user: str | None = None, *, masked: bool = True) -> Assignment:
	"""Prepare/save a Draft directly: Departmental Author or Head of User
	Department, active for the given Organisation Unit."""
	principal = actor(user)
	last = None
	for role in (ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_DEPARTMENTAL_AUTHOR):
		decision = authorise_record(user=principal, business_role=role, organisation_unit=cstr(organisation_unit), purpose=PURPOSE_COMMAND)
		if decision.allowed:
			return decision.assignment
		last = decision
	_deny(last, masked=masked)
	return None  # unreachable


def require_hod_for_any(contributing_org_units: set[str], user: str | None = None, *, masked: bool = True) -> tuple[Assignment, str]:
	"""§7.3 — Head of User Department for at least one of the Requisition's
	contributing departments (the lead department certifies on behalf of
	every contributing department in one submission — §7.3)."""
	principal = actor(user)
	last = None
	for unit in sorted(contributing_org_units):
		decision = authorise_record(user=principal, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=unit, purpose=PURPOSE_COMMAND)
		if decision.allowed:
			return decision.assignment, unit
		last = decision
	if last is None:
		not_found() if masked else fail("REQ_RESPONSIBILITY_REQUIRED")
	_deny(last, masked=masked)
	return None, ""  # unreachable


def require_draft_author_for_any(contributing_org_units: set[str], user: str | None = None, *, masked: bool = True) -> Assignment:
	"""Prepare/edit a Draft: Departmental Author or Head of User Department
	for *any* of the Requisition's contributing departments — §2.1 does not
	restrict Draft editing to a single 'owning' department once Planning
	has combined more than one; §7.3's certification restriction applies
	only to the HoD *decision*, never to drafting."""
	principal = actor(user)
	last = None
	for role in (ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_DEPARTMENTAL_AUTHOR):
		for unit in sorted(contributing_org_units):
			decision = authorise_record(user=principal, business_role=role, organisation_unit=cstr(unit), purpose=PURPOSE_COMMAND)
			if decision.allowed:
				return decision.assignment
			last = decision
	if last is None:
		not_found() if masked else fail("REQ_RESPONSIBILITY_REQUIRED")
	_deny(last, masked=masked)
	return None  # unreachable


def require_hopf(user: str | None = None, *, masked: bool = True) -> Assignment:
	"""§9.1/§9.1A — Head of Procurement Function is the sole authoriser."""
	return require_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, user, masked=masked)


def require_department_task_access(
	contributing_org_units: set[str], user: str | None = None, *, masked: bool = True
) -> tuple[str, Assignment | None, str]:
	"""KT-STD-001 §3A.6/AUTH-ADR-001 §8 — Department Approval task read
	access. Administrator/System Manager (`is_technical`) and the site-wide
	Auditor read in "oversight" mode — no assignment, every decision
	capability False — never masked, and never attributed a certifying
	HoD's own name. Granting Auditor oversight here matches how this module
	already treats Auditor everywhere else it reads (`require_requisition_reader`'s
	own `SITE_WIDE_ROLES` loop, `TENDER_SEAM_READER_ROLES`): a task read is
	not a different kind of artifact from the Requisition it belongs to.
	A Head of User Department covering one of the Requisition's contributing
	departments reads as the "decider" who may certify or return it (§7.3);
	anyone else is masked as not found exactly as `require_hod_for_any`
	denies the command itself."""
	principal = actor(user)
	if is_technical(principal) or can_read_site(ROLE_AUDITOR, principal):
		return "oversight", None, ""
	assignment, matched_unit = require_hod_for_any(contributing_org_units, principal, masked=masked)
	return "decider", assignment, matched_unit


def require_procurement_task_access(user: str | None = None, *, masked: bool = True) -> tuple[str, Assignment | None]:
	"""Procurement Authorisation task read access — the same oversight/
	decider split as `require_department_task_access`, gated on the sole
	authoriser `require_hopf` (§9.1/§9.1A) for the decider path."""
	principal = actor(user)
	if is_technical(principal) or can_read_site(ROLE_AUDITOR, principal):
		return "oversight", None
	assignment = require_hopf(principal, masked=masked)
	return "decider", assignment


def holds_any_requisition_responsibility(user: str | None = None) -> bool:
	"""Page-level verdict resolved before anything renders (§3A.1)."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	if is_technical(principal):
		return True
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return True
	for role in DEPARTMENTAL_ROLES:
		if permitted_ou_scopes(principal, role):
			return True
	return False


def authority_snapshot(assignment: Assignment | None) -> str:
	"""The exact assignment exercised, copied so later changes never rewrite
	decision evidence, plus the site PE code."""
	payload = json.loads(assignment_snapshot(assignment))
	payload["site_pe_code"] = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	return json.dumps(payload, sort_keys=True)


# --------------------------------------------------------------------------
# Frappe permission hooks — Procurement Requisition (multi-OU child table)
# --------------------------------------------------------------------------


def _site_wide_condition(principal: str) -> str | None:
	"""Returns "" (unrestricted) if the actor holds any Site-wide reader
	role or is technical; None otherwise (caller falls through to the
	OU-scoped subquery)."""
	if is_technical(principal):
		return ""
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return ""
	return None


def _requisition_scope_condition(principal: str) -> str:
	unrestricted = _site_wide_condition(principal)
	if unrestricted is not None:
		return unrestricted
	units: set[str] = set()
	for role in DEPARTMENTAL_ROLES:
		scope = permitted_ou_scopes(principal, role)
		if scope:
			units |= scope
	if not units:
		return "1=0"
	quoted = ", ".join(frappe.db.escape(u) for u in sorted(units))
	return (
		"exists (select 1 from `tabRequisition Contributing Unit` rcu "
		"where rcu.parent = `tabProcurement Requisition`.name and rcu.organisation_unit in (" + quoted + "))"
	)


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""List/count predicate for `Procurement Requisition` and, via delegation
	through `_root_requisition_of`, every requisition-family child DocType
	with no Organisation Unit column of its own."""
	principal = cstr(user or frappe.session.user)
	if is_technical(principal):
		return ""
	root_condition = _requisition_scope_condition(principal)
	if root_condition == "":
		return ""
	if root_condition == "1=0":
		return "1=0"
	if doctype in (None, "Procurement Requisition"):
		return root_condition
	link = _CHILD_LINK.get(doctype)
	if not link:
		return "1=0"
	field, parent_doctype = link
	if parent_doctype == "Procurement Requisition":
		return f"`tab{doctype}`.`{field}` in (select name from `tabProcurement Requisition` where {root_condition})"
	# Version/Task-scoped children (e.g. Requisition Decision -> Task -> Requisition)
	parent_condition = permission_query_conditions(principal, parent_doctype)
	if parent_condition == "":
		return ""
	if parent_condition == "1=0":
		return "1=0"
	return f"`tab{doctype}`.`{field}` in (select name from `tab{parent_doctype}` where {parent_condition})"


_CHILD_LINK: dict[str, tuple[str, str]] = {
	"Requisition Version": ("requisition", "Procurement Requisition"),
	"Requisition Task": ("requisition", "Procurement Requisition"),
	"Authorised Requisition Handoff": ("requisition", "Procurement Requisition"),
	"Requisition Decision": ("task", "Requisition Task"),
}


def _root_requisition_of(doctype: str, name: str) -> str:
	"""Walk a requisition-family record back to its owning
	`Procurement Requisition`, for the record-level `has_permission` check."""
	current_doctype, current_name = doctype, name
	for _ in range(4):
		if current_doctype == "Procurement Requisition":
			return current_name
		link = _CHILD_LINK.get(current_doctype)
		if not link:
			return ""
		field, parent_doctype = link
		current_name = cstr(frappe.db.get_value(current_doctype, current_name, field))
		current_doctype = parent_doctype
		if not current_name:
			return ""
	return ""


def has_permission(doc=None, ptype: str = "read", user: str | None = None):
	principal = cstr(user or frappe.session.user)
	if is_technical(principal):
		return True
	if doc is None:
		return True
	doctype = getattr(doc, "doctype", None) or (doc.get("doctype") if isinstance(doc, dict) else "")
	name = getattr(doc, "name", None) or (doc.get("name") if isinstance(doc, dict) else "")
	if not name:
		return True
	root_name = name if doctype == "Procurement Requisition" else _root_requisition_of(doctype, name)
	if not root_name:
		return False
	units = {
		r.organisation_unit
		for r in frappe.get_all("Requisition Contributing Unit", filters={"parent": root_name}, fields=["organisation_unit"])
	}
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return True
	for role in DEPARTMENTAL_ROLES:
		scope = permitted_ou_scopes(principal, role)
		if scope and scope & units:
			return True
	return False
