# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-011 — Package release read/write API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates, pp_policy
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
)
from kentender_procurement.procurement_planning.services.package_release_api import (
	get_package_release_context,
	mark_package_ready_for_api,
	release_package_to_tender_for_api,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import PlanningPermission


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _release_fail(
	*,
	code: str,
	message: str,
	role_key: str = "auditor",
	blockers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}
	if blockers:
		out["blockers"] = blockers
	return out


def _planning_read_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_PACKAGE_READ,
		message=_("You do not have access to the Procurement Planning package release."),
		fail=_fail,
		require_planning_read=False,
		require_package_read=False,
	)


def _mark_ready_gate() -> tuple[str | None, dict[str, Any] | None]:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return None, _release_fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key:
		return None, _release_fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to mark packages ready for release."),
			role_key=role_key or "auditor",
		)
	try:
		pp_policy.assert_may_mark_package_ready_for_release(frappe._dict(status=PKG_APPROVED))
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return None, _release_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key or "auditor",
		)
	return role_key, None


def _release_to_tender_gate() -> tuple[str | None, dict[str, Any] | None]:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return None, _release_fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key:
		return None, _release_fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to release packages to tender management."),
			role_key=role_key or "auditor",
		)
	try:
		pp_policy.assert_may_release_package_to_tender(frappe._dict(status=PKG_READY_FOR_RELEASE))
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return None, _release_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key or "auditor",
		)
	return role_key, None


@frappe.whitelist()
def get_pp_package_release(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 package release — handoff summary and role/state gates."""
	role_key, gate_err = _planning_read_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (package_code or "").strip()
	if not code:
		return _fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	return get_package_release_context(code, frappe.session.user)


@frappe.whitelist()
def mark_pp_package_ready_for_release(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 write — mark an approved package ready for release."""
	role_key, gate_err = _mark_ready_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (package_code or "").strip()
	if not code:
		return _release_fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	return mark_package_ready_for_api(code, frappe.session.user)


@frappe.whitelist()
def release_pp_package_to_tender(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 write — release a ready package to tender management."""
	role_key, gate_err = _release_to_tender_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (package_code or "").strip()
	if not code:
		return _release_fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	return release_package_to_tender_for_api(code, frappe.session.user)
