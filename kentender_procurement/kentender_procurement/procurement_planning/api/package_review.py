# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-010 — Package review read/write API."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates, pp_policy
from kentender_procurement.procurement_planning.pp2_constants import PKG_IN_REVIEW
from kentender_procurement.procurement_planning.services.package_review_api import (
	get_package_review_context,
	record_package_review_for_api,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import PlanningPermission


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _review_fail(
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
		message=_("You do not have access to the Procurement Planning package review."),
		fail=_fail,
		require_planning_read=False,
		require_package_read=False,
	)


def _record_review_gate() -> tuple[str | None, dict[str, Any] | None]:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return None, _review_fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key:
		return None, _review_fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to record package review decisions."),
			role_key=role_key or "auditor",
		)
	try:
		pp_policy.assert_may_record_review_decision(frappe._dict(status=PKG_IN_REVIEW))
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return None, _review_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key or "auditor",
		)
	return role_key, None


def _parse_payload(payload: str | dict | None, kwargs: dict[str, Any]) -> dict[str, Any]:
	data: dict[str, Any] = {}
	if payload:
		if isinstance(payload, str):
			parsed = json.loads(payload)
			if isinstance(parsed, dict):
				data = parsed
		elif isinstance(payload, dict):
			data = dict(payload)
	for key, value in kwargs.items():
		if value is not None and key != "cmd":
			data[key] = value
	return data


@frappe.whitelist()
def get_pp_package_review(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 package review — latest decision and role/state gates."""
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

	return get_package_review_context(code, frappe.session.user)


@frappe.whitelist()
def record_pp_package_review_decision(
	package_code: str | None = None,
	payload: str | dict | None = None,
	**kwargs: Any,
) -> dict[str, Any]:
	"""Whitelisted PP2 write — approve or return package for correction."""
	role_key, gate_err = _record_review_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (package_code or "").strip()
	if not code:
		return _review_fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	data = _parse_payload(payload, kwargs)
	return record_package_review_for_api(code, data, frappe.session.user)
