# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-015 — Shared role profiles for PP2 whitelisted API read gates."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import (
	_can_read_planning,
	resolve_pp_role_key,
)

PLANNING_QUEUE_READ = "planning_queue_read"
PLANNING_PACKAGE_READ = "planning_package_read"
PLANNING_READINESS_READ = "planning_readiness_read"
RELEASED_TO_TENDER_READ = "released_to_tender_read"
PLANNING_EVIDENCE_READ = "planning_evidence_read"

_PLANNING_INTERNAL_READ_ROLES = frozenset(
	(
		"Procurement Planner",
		"Planning Reviewer",
		"Planning Authority",
		"Auditor",
		"Administrator",
		"System Manager",
	)
)
_PLANNING_INTERNAL_DENIED_ROLES = frozenset(
	(
		"Procurement Officer",
		"Tender Manager",
		"Supplier",
	)
)
_EXTENDED_PLANNING_READ_ROLES = _PLANNING_INTERNAL_READ_ROLES | frozenset(
	(
		"Procurement Officer",
		"Tender Manager",
		"Budget Officer",
	)
)
_EXTENDED_PLANNING_DENIED_ROLES = frozenset(("Supplier",))
_READINESS_READ_ROLES = _PLANNING_INTERNAL_READ_ROLES | frozenset(("Budget Officer",))

_PROFILE_ALLOWED: dict[str, frozenset[str]] = {
	PLANNING_QUEUE_READ: _PLANNING_INTERNAL_READ_ROLES,
	PLANNING_PACKAGE_READ: _PLANNING_INTERNAL_READ_ROLES,
	PLANNING_READINESS_READ: _READINESS_READ_ROLES,
	RELEASED_TO_TENDER_READ: _EXTENDED_PLANNING_READ_ROLES,
	PLANNING_EVIDENCE_READ: _EXTENDED_PLANNING_READ_ROLES,
}
_PROFILE_DENIED: dict[str, frozenset[str]] = {
	PLANNING_QUEUE_READ: _PLANNING_INTERNAL_DENIED_ROLES,
	PLANNING_PACKAGE_READ: _PLANNING_INTERNAL_DENIED_ROLES,
	PLANNING_READINESS_READ: _PLANNING_INTERNAL_DENIED_ROLES,
	RELEASED_TO_TENDER_READ: _EXTENDED_PLANNING_DENIED_ROLES,
	PLANNING_EVIDENCE_READ: _EXTENDED_PLANNING_DENIED_ROLES,
}


def _role_set_allows(
	user: str,
	*,
	allowed: frozenset[str],
	denied: frozenset[str],
) -> bool:
	if user in ("Guest", ""):
		return False
	roles = set(frappe.get_roles(user))
	if roles & denied and not (roles & allowed):
		return False
	return bool(roles & allowed)


def user_may_access(profile: str, user: str | None = None) -> bool:
	"""Return True when the user's roles match the gate profile (role-set only)."""
	user = user or frappe.session.user
	allowed = _PROFILE_ALLOWED.get(profile)
	denied = _PROFILE_DENIED.get(profile)
	if allowed is None or denied is None:
		return False
	return _role_set_allows(user, allowed=allowed, denied=denied)


def _has_doctype_read(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, "read"))
	except Exception:
		return False


def check_profile_access(
	profile: str,
	user: str | None = None,
	*,
	require_planning_read: bool | None = None,
	require_demand_read: bool | None = None,
	require_package_read: bool | None = None,
) -> bool:
	"""Full profile check including DocType read permissions where required."""
	user = user or frappe.session.user
	if not user_may_access(profile, user):
		return False
	if profile == PLANNING_QUEUE_READ:
		need_plan = True if require_planning_read is None else require_planning_read
		need_demand = True if require_demand_read is None else require_demand_read
		if need_plan and not _can_read_planning():
			return False
		if need_demand and not _has_doctype_read("Demand"):
			return False
		return True
	if profile in (PLANNING_PACKAGE_READ, PLANNING_READINESS_READ):
		need_plan = True if require_planning_read is None else require_planning_read
		need_pkg = True if require_package_read is None else require_package_read
		if need_plan and not _can_read_planning():
			return False
		if need_pkg and not _has_doctype_read("Procurement Package"):
			return False
		return True
	return True


def planning_api_read_gate(
	profile: str,
	*,
	message: str,
	fail: Callable[..., dict[str, Any]],
	installed_doctype: str = "Procurement Package",
	require_planning_read: bool | None = None,
	require_demand_read: bool | None = None,
	require_package_read: bool | None = None,
) -> tuple[str | None, dict[str, Any] | None]:
	"""Shared read gate for P4 whitelisted APIs."""
	if not frappe.db.exists("DocType", installed_doctype):
		return None, fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	if not check_profile_access(
		profile,
		require_planning_read=require_planning_read,
		require_demand_read=require_demand_read,
		require_package_read=require_package_read,
	):
		role_key = resolve_pp_role_key()
		return None, fail(
			code="PP_ACCESS_DENIED",
			message=message,
			role_key=role_key or "auditor",
		)
	role_key = resolve_pp_role_key() or "auditor"
	return role_key, None
