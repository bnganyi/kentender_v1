# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-004 — Planning inclusion write APIs (create package from inclusion)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import (
	_can_read_planning,
	resolve_pp_role_key,
)
from kentender_procurement.procurement_planning.permissions import pp_policy
from kentender_procurement.procurement_planning.services.pp_governance_codes import PlanningPermission


def _package_fail(
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


def _create_package_gate() -> tuple[str | None, dict[str, Any] | None]:
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return None, _package_fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return None, _package_fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to create packages from planning inclusions."),
			role_key=role_key or "auditor",
		)
	try:
		pp_policy.assert_may_create_package_from_inclusion()
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return None, _package_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key or "auditor",
		)
	return role_key, None


@frappe.whitelist()
def create_pp_package_from_planning_inclusion(
	inclusion_code: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted Planning write — create Draft package from Planning Inclusion."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	inclusion_code = (inclusion_code or "").strip()
	if not inclusion_code:
		return _package_fail(
			code="MISSING_PARAMS",
			message=_("Planning inclusion code is required."),
			role_key=role_key,
		)

	from kentender_procurement.procurement_planning.services.package_creation_service import (
		can_create_package_from_inclusion,
		create_package_from_planning_inclusion,
	)

	try:
		out = create_package_from_planning_inclusion(inclusion_code, frappe.session.user)
	except frappe.ValidationError as exc:
		guard = can_create_package_from_inclusion(inclusion_code, frappe.session.user)
		blockers = (guard.get("blockers") or []) if isinstance(guard, dict) else []
		error_code = (
			(blockers[0].get("code") if blockers else None)
			or getattr(exc, "title", None)
			or "VALIDATION_ERROR"
		)
		return _package_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key,
			blockers=blockers or None,
		)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return _package_fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key,
		)

	return {
		"ok": True,
		"role_key": role_key,
		**out,
	}


@frappe.whitelist()
def get_pp_create_package_modal_drawer(
	demand_code: str | None = None,
	plan_code: str | None = None,
	inclusion_code: str | None = None,
	demand_item_codes: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted read — Create Package modal business context."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.create_package_modal_drawer import (
		get_create_package_modal_drawer,
	)

	item_codes: list[str] | None = None
	raw_items = (demand_item_codes or "").strip()
	if raw_items:
		try:
			import json

			parsed = json.loads(raw_items)
			if isinstance(parsed, list):
				item_codes = [str(x).strip() for x in parsed if str(x).strip()]
		except json.JSONDecodeError:
			item_codes = [raw_items]

	out = get_create_package_modal_drawer(
		demand_code=(demand_code or "").strip() or None,
		plan_code=(plan_code or "").strip() or None,
		inclusion_code=(inclusion_code or "").strip() or None,
		demand_item_codes=item_codes,
		actor=frappe.session.user,
	)
	if not out.get("ok"):
		return out
	out["role_key"] = role_key
	return out
