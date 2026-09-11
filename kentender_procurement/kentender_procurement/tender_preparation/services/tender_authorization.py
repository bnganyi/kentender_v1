# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §5 — Tender Preparation authorisation on the shared
AUTH-ADR-001 v1.6 resolver.

One vocabulary for every Tender list, count, detail, preview, file and
command: a role-bound `User Responsibility Assignment` resolved by
`kentender_core.services.authorization`. Procurement Officer, Head of
Procurement Function and Auditor are Site-wide; there is no Procuring Entity
or Fiscal Year scope check anywhere (§5). A Frappe Role, a framework
permission row, a task or a browser value grants nothing.

Tender doctypes carry no Organisation Unit column, so the module registers
its own `permission_query_conditions` / `has_permission` for the whole
family rather than a `kentender_scope_map` entry (plan D11; C8): a Site-wide
reader sees everything, anyone else sees nothing, and every family child
delegates to the root through the same predicate.

Resolver codes never reach a client: record-addressed reads and commands
mask to not-found (§11.3), and every remaining condition maps onto the
closed §11.3 set (see `errors.py`). Administrator and System Manager read
everything and decide nothing (AUTH §8; TPR-SMOKE-19).
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import (
	PURPOSE_COMMAND,
	PURPOSE_READ,
	Assignment,
	assignment_snapshot,
	authorise_record,
	is_technical,
)
from kentender_procurement.tender_preparation.services.errors import fail
from kentender_procurement.tender_preparation.services.tender_roles import (
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PROCUREMENT_OFFICER,
	SITE_WIDE_ROLES,
)

# AUTH-ADR-001 v1.6 §10 → TPR-CHG-001 v0.6 §11.3 (unmasked paths only).
_AUTH_TO_TPR: dict[str, str] = {
	"AUTH_RESPONSIBILITY_REQUIRED": "TPR_RESPONSIBILITY_REQUIRED",
	"AUTH_SCOPE_REQUIRED": "TPR_RESPONSIBILITY_REQUIRED",
	"AUTH_ASSIGNMENT_INACTIVE": "TPR_RESPONSIBILITY_REQUIRED",
	"AUTH_SEGREGATION_BLOCKED": "TPR_SOD_BLOCKED",
	"AUTH_TASK_REQUIRED": "TPR_STALE_VERSION",
	"AUTH_STATE_CHANGED": "TPR_STALE_VERSION",
	"AUTH_PERIOD_UNAVAILABLE": "TPR_RESPONSIBILITY_REQUIRED",
	"AUTH_CONFIGURATION_INVALID": "TPR_RESPONSIBILITY_REQUIRED",
}

# Every doctype the family predicate covers (root first).
FAMILY_DOCTYPES: tuple[str, ...] = (
	"Prepared Tender",
	"Tender Preparation Version",
	"Tender Preparation Task",
	"Tender Preparation Decision",
	"Tender Publication Handoff",
	"Tender Preparation Event",
	"Tender Preparation Command Journal",
	"Supported Tender Template",
)


def not_found() -> None:
	"""§11.3: unauthorised detail/task reads look exactly like a missing record."""
	raise frappe.DoesNotExistError("Not found")


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		fail("TPR_RESPONSIBILITY_REQUIRED", "Sign in to access Tender Preparation.")
	return value


def _deny(decision, *, masked: bool) -> None:
	if masked:
		not_found()
	fail(_AUTH_TO_TPR.get(decision.reason_code, "TPR_RESPONSIBILITY_REQUIRED"))


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


def require_officer(user: str | None = None, *, masked: bool = True) -> Assignment:
	"""§5 — start, edit, run readiness, submit and correct: Procurement Officer."""
	return require_site_role(ROLE_PROCUREMENT_OFFICER, user, masked=masked)


def require_hopf(user: str | None = None, *, masked: bool = True) -> Assignment:
	"""§5/§10.3 — return, approve, reopen: the Head of Procurement Function."""
	return require_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, user, masked=masked)


def require_officer_or_hopf(user: str | None = None, *, masked: bool = True) -> Assignment:
	"""§10.4 — request upstream correction is an officer action; the same
	gate also serves commands either office may run."""
	principal = actor(user)
	last = None
	for role in (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION):
		decision = authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
		if decision.allowed:
			return decision.assignment
		last = decision
	_deny(last, masked=masked)
	return None  # unreachable


def require_tender_reader(user: str | None = None) -> str:
	"""§5 — any Site-wide reader, or a technical role; anyone else is masked."""
	principal = actor(user)
	if is_technical(principal):
		return principal
	for role in SITE_WIDE_ROLES:
		if can_read_site(role, principal):
			return principal
	not_found()
	return principal  # unreachable


def holds_any_tender_responsibility(user: str | None = None) -> bool:
	"""Page-level verdict resolved before anything renders (KT-STD-001 §3A.1)."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	if is_technical(principal):
		return True
	return any(can_read_site(role, principal) for role in SITE_WIDE_ROLES)


def authority_snapshot(assignment: Assignment | None) -> str:
	"""The exact assignment exercised, copied so later changes never rewrite
	decision evidence, plus the site PE code (never a scope — §15)."""
	payload = json.loads(assignment_snapshot(assignment))
	payload["site_pe_code"] = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	return json.dumps(payload, sort_keys=True)


# --------------------------------------------------------------------------
# Frappe permission hooks — the whole Tender family is Site-wide
# --------------------------------------------------------------------------


def _reads_site(principal: str) -> bool:
	if is_technical(principal):
		return True
	return any(
		authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed
		for role in SITE_WIDE_ROLES
	)


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""List/count predicate for every Tender-family doctype: unrestricted for
	a Site-wide reader or a technical role, nothing for anyone else."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return "1=0"
	return "" if _reads_site(principal) else "1=0"


def has_permission(doc=None, ptype: str = "read", user: str | None = None):
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	if is_technical(principal):
		return True
	return _reads_site(principal)
