# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase E1 / PP2 — Authoritative role checks for whitelisted workflow and PP APIs."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_EDITABLE_STATUSES,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_RETURNED,
	PLAN_ACTIVE,
	PLAN_DRAFT,
	POST_RELEASE_LOCK_MESSAGE,
)
from kentender_procurement.procurement_planning.services.package_post_release_lock import (
	is_post_release_locked,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackagePostReleaseLock,
	PlanningPermission,
)

# Business roles (Roles Matrix §3 / §6)
_ROLE_PLANNER = frozenset(("Procurement Planner",))
_ROLE_REVIEWER = frozenset(("Planning Reviewer",))
_ROLE_AUTHORITY = frozenset(("Planning Authority",))
_ROLE_OFFICER = frozenset(("Procurement Officer",))
_ROLE_TENDER_MANAGER = frozenset(("Tender Manager",))
_ROLE_AUDITOR = frozenset(("Auditor",))
_ROLE_BREAK_GLASS = frozenset(("Administrator",))

_ALL_PP_BUSINESS_ROLES = frozenset(
	(
		"Procurement Planner",
		"Planning Reviewer",
		"Planning Authority",
		"Procurement Officer",
		"Tender Manager",
		"Auditor",
		"Finance Reviewer",
		"Budget Officer",
	)
)

_INTERNAL_PLANNING_ROLES = _ALL_PP_BUSINESS_ROLES | _ROLE_BREAK_GLASS | frozenset(("System Manager",))

# Composite allowed sets (Administrator break-glass; System Manager-only denied via _assert_business_roles)
_ROLE_PLANNER_OR_AUTHORITY = _ROLE_PLANNER | _ROLE_AUTHORITY | _ROLE_BREAK_GLASS
_ROLE_REVIEWER_OR_AUTHORITY = _ROLE_REVIEWER | _ROLE_AUTHORITY | _ROLE_BREAK_GLASS
_ROLE_MARK_READY = _ROLE_REVIEWER | _ROLE_AUTHORITY | _ROLE_OFFICER | _ROLE_BREAK_GLASS
_ROLE_RELEASE = _ROLE_AUTHORITY | _ROLE_OFFICER | _ROLE_BREAK_GLASS
_ROLE_READINESS = _ROLE_PLANNER | _ROLE_REVIEWER | _ROLE_AUTHORITY | _ROLE_BREAK_GLASS
_ROLE_CONSUMPTION = _ROLE_OFFICER | _ROLE_TENDER_MANAGER | _ROLE_AUTHORITY | _ROLE_BREAK_GLASS
_ROLE_PLAN_AUTHORITY = _ROLE_AUTHORITY | _ROLE_BREAK_GLASS

# Back-compat aliases used by workflow helpers
_ROLE_PLANNER_ADMIN = _ROLE_PLANNER_OR_AUTHORITY
_ROLE_AUTHORITY_ADMIN = _ROLE_REVIEWER_OR_AUTHORITY
_ROLE_OFFICER_OR_AUTHORITY_ADMIN = _ROLE_MARK_READY


def _session_roles() -> frozenset[str]:
	return frozenset(frappe.get_roles(frappe.session.user))


def _deny_not_permitted() -> None:
	frappe.throw(
		_("{0}: Not permitted.").format(PlanningPermission.NOT_PERMITTED),
		frappe.PermissionError,
	)


def _assert_internal_planning_actor() -> None:
	"""Deny Guest and users with no internal Planning role."""
	user = (frappe.session.user or "").strip()
	if not user or user == "Guest":
		_deny_not_permitted()
	roles = _session_roles()
	if roles & _INTERNAL_PLANNING_ROLES:
		return
	_deny_not_permitted()


def _assert_not_auditor_write() -> None:
	roles = _session_roles()
	if roles & _ROLE_AUDITOR and not (roles & (_ALL_PP_BUSINESS_ROLES - _ROLE_AUDITOR)):
		_deny_not_permitted()


def _assert_business_roles(allowed: frozenset[str]) -> None:
	"""Allow business roles in *allowed*; Administrator break-glass; deny System-Manager-only."""
	_assert_internal_planning_actor()
	roles = _session_roles()
	if roles & _ROLE_BREAK_GLASS:
		return
	if roles & allowed:
		return
	_assert_not_auditor_write()
	_deny_not_permitted()


def assert_may_include_demand_in_plan() -> None:
	"""Planner or Planning Authority may include approved demand in a plan."""
	_assert_business_roles(_ROLE_PLANNER_OR_AUTHORITY)


def assert_may_create_package_from_inclusion() -> None:
	"""Planner or Planning Authority may create a package from inclusion."""
	_assert_business_roles(_ROLE_PLANNER_OR_AUTHORITY)


def assert_may_record_method_decision(doc) -> None:
	"""Planner or Planning Authority may record method decisions on editable packages."""
	_assert_business_roles(_ROLE_PLANNER_OR_AUTHORITY)


def assert_may_run_readiness_checks(doc) -> None:
	"""Planner, Reviewer, or Authority may run readiness checks."""
	_assert_business_roles(_ROLE_READINESS)


def assert_may_submit_package_for_review(doc) -> None:
	"""Planner or Authority may submit Draft/Returned packages for review."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	if st not in (PKG_DRAFT, PKG_RETURNED):
		frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
	_assert_business_roles(_ROLE_PLANNER_OR_AUTHORITY)


def assert_may_record_review_decision(doc) -> None:
	"""Reviewer or Authority may approve/return/cancel while In Review."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	if st != PKG_IN_REVIEW:
		frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
	_assert_business_roles(_ROLE_REVIEWER_OR_AUTHORITY)


def assert_may_mark_package_ready_for_release(doc) -> None:
	"""Reviewer, Authority, or Officer may mark Approved packages ready for release."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	if st != PKG_APPROVED:
		frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
	_assert_business_roles(_ROLE_MARK_READY)


def assert_may_release_package_to_tender(doc) -> None:
	"""Authority or Officer may release Ready for Release packages."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	if st != PKG_READY_FOR_RELEASE:
		frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
	_assert_business_roles(_ROLE_RELEASE)


def assert_may_run_plan_workflow(action: str, doc) -> None:
	"""Raise if the current user may not run this plan workflow action (server-side)."""
	st = (doc.status or "").strip()
	if action == "activate_plan":
		if st != PLAN_DRAFT:
			frappe.throw(_("Invalid plan state for this action."), title=_("Not permitted"))
		_assert_business_roles(_ROLE_PLAN_AUTHORITY)
	elif action in ("close_plan", "supersede_plan"):
		if st != PLAN_ACTIVE:
			frappe.throw(_("Invalid plan state for this action."), title=_("Not permitted"))
		_assert_business_roles(_ROLE_PLAN_AUTHORITY)
	elif action == "cancel_plan":
		if st not in (PLAN_DRAFT, PLAN_ACTIVE):
			frappe.throw(_("Invalid plan state for this action."), title=_("Not permitted"))
		_assert_business_roles(_ROLE_PLAN_AUTHORITY)
	else:
		frappe.throw(_("Unknown workflow action."), title=_("Not permitted"))


def assert_may_run_package_workflow(action: str, doc) -> None:
	"""Raise if the current user may not run this package workflow action (server-side)."""
	if action == "submit_package":
		assert_may_submit_package_for_review(doc)
	elif action in ("approve_package", "return_package", "cancel_package"):
		assert_may_record_review_decision(doc)
	elif action == "mark_ready_for_release":
		assert_may_mark_package_ready_for_release(doc)
	elif action == "release_package_to_tender":
		assert_may_release_package_to_tender(doc)
	else:
		frappe.throw(_("Unknown workflow action."), title=_("Not permitted"))


def assert_may_mark_planning_release_consumed(doc) -> None:
	"""Officer, Tender Manager, or Authority may consume a planning release."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	if st not in (PKG_RELEASED, PKG_CONSUMED):
		frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
	_assert_business_roles(_ROLE_CONSUMPTION)


def assert_may_consume_planning_release() -> None:
	"""Role-only guard when release package doc is not yet resolved."""
	_assert_business_roles(_ROLE_CONSUMPTION)


def assert_may_apply_template_to_demands() -> None:
	"""C2 / D5 — only planners (and authority/admins) may apply templates to demands."""
	_assert_business_roles(_ROLE_PLANNER_OR_AUTHORITY)


def assert_may_create_planning_correction(doc) -> None:
	"""P2-013 — Planning Authority may apply post-release correction or supersession."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	if st not in (PKG_RELEASED, PKG_CONSUMED):
		frappe.throw(_("Invalid package state for this action."), title=_("Not permitted"))
	_assert_business_roles(_ROLE_PLAN_AUTHORITY)


def assert_may_edit_package_lines(doc) -> None:
	"""Planner/Authority on Draft/Returned; Reviewer denied during In Review (PP2-PERM-NEG-004)."""
	st = (getattr(doc, "status", None) or doc.get("status") or "").strip()
	roles = _session_roles()
	if st == PKG_IN_REVIEW and (roles & _ROLE_REVIEWER) and not (
		roles & (_ROLE_PLANNER | _ROLE_AUTHORITY | _ROLE_BREAK_GLASS)
	):
		_deny_not_permitted()
	_assert_business_roles(_ROLE_PLANNER_OR_AUTHORITY)
	if is_post_release_locked(doc):
		frappe.throw(
			POST_RELEASE_LOCK_MESSAGE,
			title=PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
		)
	if st not in PKG_EDITABLE_STATUSES:
		frappe.throw(_("Package lines cannot be edited in this state."), title=_("Not permitted"))
