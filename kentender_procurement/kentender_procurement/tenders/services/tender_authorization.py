# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §6 / §8 — Tenders authorisation on the shared
AUTH-ADR-001 v1.8 resolver (plan D12).

One vocabulary for every Tenders list, count, detail and command: a
role-bound `User Responsibility Assignment` resolved by
`kentender_core.services.authorization`. Procurement Officer, Head of
Procurement Function, Accounting Officer and Auditor are Site-wide readers;
Departmental Author and Head of User Department read the neutral projection
only for a Tender whose source Requisition their Organisation Unit
contributed to (`Tender.lead_org_unit` / `contributing_org_unit_ids`). A
Frappe Role, a framework permission row, a task or a browser value grants
nothing.

Every Tender-family doctype without an Organisation Unit column of its own
delegates to the owning `Tender` (`_CHILD_LINK`), exactly as the Requisition
family delegates to its root. Resolver codes never reach a client:
record-addressed reads and commands mask to not-found (§8), and every
remaining condition maps onto the closed §8 set. Administrator and System
Manager read everything and decide nothing (KT-STD-001 §3A.6).
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
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import (
	DEPARTMENTAL_ROLES,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PROCUREMENT_OFFICER,
	SITE_WIDE_ROLES,
)

# AUTH-ADR-001 v1.8 §10 → TPR-CHG-001 v0.8 §8 (unmasked paths only).
_AUTH_TO_TND: dict[str, str] = {
	"AUTH_RESPONSIBILITY_REQUIRED": "TND_RESPONSIBILITY_REQUIRED",
	"AUTH_SCOPE_REQUIRED": "TND_RESPONSIBILITY_REQUIRED",
	"AUTH_ASSIGNMENT_INACTIVE": "TND_RESPONSIBILITY_REQUIRED",
	"AUTH_SEGREGATION_BLOCKED": "TND_SOD_BLOCKED",
	"AUTH_TASK_REQUIRED": "TND_STALE_VERSION",
	"AUTH_STATE_CHANGED": "TND_STALE_VERSION",
	"AUTH_PERIOD_UNAVAILABLE": "TND_RESPONSIBILITY_REQUIRED",
	"AUTH_CONFIGURATION_INVALID": "TND_RESPONSIBILITY_REQUIRED",
}

ROOT = "Tender"


def not_found() -> None:
	"""§8: unauthorised detail/task reads look exactly like a missing record."""
	raise frappe.DoesNotExistError("Not found")


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		fail("TND_RESPONSIBILITY_REQUIRED", "Sign in to access Tenders.")
	return value


def _deny(decision, *, masked: bool, role: str = "") -> None:
	if masked:
		not_found()
	code = _AUTH_TO_TND.get(decision.reason_code, "TND_RESPONSIBILITY_REQUIRED")
	if code == "TND_RESPONSIBILITY_REQUIRED" and role:
		fail(code, f"This action requires {role}.")
	fail(code)


def require_site_role(role: str, user: str | None = None, *, masked: bool = True) -> Assignment:
	principal = actor(user)
	decision = authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
	if not decision.allowed:
		_deny(decision, masked=masked, role=role)
	return decision.assignment


def require_officer(user: str | None = None, *, masked: bool = True) -> Assignment:
	return require_site_role(ROLE_PROCUREMENT_OFFICER, user, masked=masked)


def require_hopf(user: str | None = None, *, masked: bool = True) -> Assignment:
	return require_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, user, masked=masked)


def require_ao(user: str | None = None, *, masked: bool = True) -> Assignment:
	return require_site_role(ROLE_ACCOUNTING_OFFICER, user, masked=masked)


def require_any_site_role(roles: tuple[str, ...], user: str | None = None, *, masked: bool = True) -> tuple[Assignment, str]:
	"""The first of `roles` the actor holds (command purpose), e.g. an
	addendum drafted by a Procurement Officer or the HoPF (§6)."""
	principal = actor(user)
	last = None
	for role in roles:
		decision = authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
		if decision.allowed:
			return decision.assignment, role
		last = decision
	_deny(last, masked=masked, role=" or ".join(roles))
	return None, ""  # unreachable


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


def site_roles_held(user: str | None = None) -> tuple[str, ...]:
	principal = cstr(user or frappe.session.user)
	return tuple(role for role in SITE_WIDE_ROLES if can_read_site(role, principal))


def departmental_units(user: str | None = None) -> set[str]:
	principal = cstr(user or frappe.session.user)
	units: set[str] = set()
	for role in DEPARTMENTAL_ROLES:
		scope = permitted_ou_scopes(principal, role)
		if scope:
			units |= scope
	return units


def reader_mode(actor_name: str, *, contributing_org_units: set[str]) -> str:
	"""`site` for a Site-wide reader, `department` for an OU-scoped neutral
	reader whose unit contributed, `technical` for Administrator/System
	Manager; masked not-found otherwise (§6, §8)."""
	if is_technical(actor_name):
		return "technical"
	for role in SITE_WIDE_ROLES:
		if can_read_site(role, actor_name):
			return "site"
	if departmental_units(actor_name) & contributing_org_units:
		return "department"
	not_found()
	return ""  # unreachable


def require_tender_reader(actor_name: str, *, contributing_org_units: set[str]) -> str:
	return reader_mode(actor_name, contributing_org_units=contributing_org_units)


def holds_any_tender_responsibility(user: str | None = None) -> bool:
	"""Page-level verdict resolved before anything renders (KT-STD §3A.1)."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	if is_technical(principal):
		return True
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return True
	return bool(departmental_units(principal))


def authority_snapshot(assignment: Assignment | None) -> str:
	"""The exact assignment exercised, copied so later changes never rewrite
	decision evidence, plus the site PE code."""
	payload = json.loads(assignment_snapshot(assignment))
	payload["site_pe_code"] = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	return json.dumps(payload, sort_keys=True)


def contributing_units_of(root) -> set[str]:
	units: set[str] = set()
	if getattr(root, "lead_org_unit", None):
		units.add(cstr(root.lead_org_unit))
	raw = getattr(root, "contributing_org_unit_ids", None) or "[]"
	try:
		units |= {cstr(u) for u in json.loads(raw) if u}
	except (TypeError, ValueError):
		pass
	return units


# --------------------------------------------------------------------------
# Frappe permission hooks — the Tender family
# --------------------------------------------------------------------------

_CHILD_LINK: dict[str, tuple[str, str]] = {
	"Tender Version": ("tender", ROOT),
	"Tender Task": ("tender", ROOT),
	"Tender Decision": ("tender", ROOT),
	"Tender Publication": ("tender", ROOT),
	"Tender Channel Confirmation": ("tender", ROOT),
	"Tender Addendum": ("tender", ROOT),
	"Tender Addendum Inquiry": ("tender", ROOT),
	"Tender Cancellation": ("tender", ROOT),
	"Tender Document": ("tender", ROOT),
	"Tender Event": ("tender", ROOT),
	"Tender Submission Handoff": ("tender", ROOT),
}
FAMILY: tuple[str, ...] = (ROOT, *_CHILD_LINK.keys())


def _site_wide_condition(principal: str) -> str | None:
	if is_technical(principal):
		return ""
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return ""
	return None


def _tender_scope_condition(principal: str) -> str:
	unrestricted = _site_wide_condition(principal)
	if unrestricted is not None:
		return unrestricted
	units = departmental_units(principal)
	if not units:
		return "1=0"
	quoted = ", ".join(frappe.db.escape(u) for u in sorted(units))
	return f"`tab{ROOT}`.`lead_org_unit` in ({quoted})"


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	principal = cstr(user or frappe.session.user)
	if is_technical(principal):
		return ""
	root_condition = _tender_scope_condition(principal)
	if root_condition in ("", "1=0"):
		return root_condition
	if doctype in (None, ROOT):
		return root_condition
	link = _CHILD_LINK.get(doctype)
	if not link:
		return "1=0"
	field, _parent = link
	return f"`tab{doctype}`.`{field}` in (select name from `tab{ROOT}` where {root_condition})"


def template_permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""`Supported Tender Template`: readable by every Site-wide Tenders role
	and technical readers; nobody else lists it."""
	principal = cstr(user or frappe.session.user)
	return "" if _site_wide_condition(principal) is not None else "1=0"


def template_has_permission(doc=None, ptype: str = "read", user: str | None = None):
	principal = cstr(user or frappe.session.user)
	return _site_wide_condition(principal) is not None


def _root_of(doctype: str, name: str) -> str:
	if doctype == ROOT:
		return name
	link = _CHILD_LINK.get(doctype)
	if not link:
		return ""
	field, _parent = link
	return cstr(frappe.db.get_value(doctype, name, field))


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
	root_name = _root_of(doctype, name)
	if not root_name:
		return False
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed:
			return True
	root = frappe.db.get_value(ROOT, root_name, ["lead_org_unit", "contributing_org_unit_ids"], as_dict=True)
	if not root:
		return False
	return bool(departmental_units(principal) & contributing_units_of(root))
