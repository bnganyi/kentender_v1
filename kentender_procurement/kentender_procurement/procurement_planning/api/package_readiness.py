# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-009 — Package readiness read/run API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates, pp_policy
from kentender_procurement.procurement_planning.services.package_readiness_api import (
	get_package_readiness_context,
	run_package_readiness_for_api,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import PlanningPermission


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _readiness_fail(
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
		pp_api_gates.PLANNING_READINESS_READ,
		message=_("You do not have access to the Procurement Planning package readiness."),
		fail=_fail,
		require_planning_read=False,
		require_package_read=False,
	)


def _run_readiness_gate() -> tuple[str | None, dict[str, Any] | None]:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return None, _readiness_fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key or not pp_api_gates.check_profile_access(
		pp_api_gates.PLANNING_PACKAGE_READ,
		require_package_read=False,
	):
		return None, _readiness_fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to run package readiness checks."),
			role_key=role_key or "auditor",
		)
	try:
		pp_policy.assert_may_run_readiness_checks(None)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return None, _readiness_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key or "auditor",
		)
	return role_key, None


@frappe.whitelist()
def get_pp_package_readiness(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 package readiness — server-backed check context."""
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

	return get_package_readiness_context(code, frappe.session.user)


@frappe.whitelist()
def run_pp_package_readiness_checks(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 write — run and persist package readiness checks."""
	role_key, gate_err = _run_readiness_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (package_code or "").strip()
	if not code:
		return _readiness_fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	return run_package_readiness_for_api(code, frappe.session.user)
