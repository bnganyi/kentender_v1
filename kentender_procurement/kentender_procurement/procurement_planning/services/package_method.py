# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-008 — Package method & category read/write service (PP2 UI §15)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PKG_EDITABLE_STATUSES
from kentender_procurement.procurement_planning.services.package_lines import (
	_resolve_package_name,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	can_record_package_method_decision,
	get_current_package_method_decision,
	record_package_method_decision,
)
from kentender_procurement.procurement_planning.services.package_post_release_lock import (
	is_post_release_locked,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageMethodDecision,
	PlanningPermission,
)


def _fail(
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


def format_package_method_tab(doc, package_code: str) -> dict[str, Any]:
	"""Return method tab fields — current decision or package-field fallback."""
	decision = get_current_package_method_decision(package_code)
	if decision:
		return {
			"source": "method_decision",
			**decision,
		}
	return {
		"source": "package",
		"procurement_category": (doc.procurement_category or "").strip(),
		"procurement_method": (doc.procurement_method or "").strip(),
		"required_std_category": (doc.required_std_category or "").strip(),
		"required_std_type": (doc.required_std_type or "").strip(),
		"contract_type_expectation": (doc.contract_type or "").strip(),
		"method_decision_code": None,
	}


def _may_edit_method(doc, actor: str) -> dict[str, Any]:
	status = (doc.status or "").strip()
	if is_post_release_locked(doc):
		return {
			"allowed": False,
			"error_code": PackageMethodDecision.LOCKED_AFTER_RELEASE,
			"message": "Package method cannot be edited after release.",
		}
	if status not in PKG_EDITABLE_STATUSES:
		return {
			"allowed": False,
			"error_code": PackageMethodDecision.LOCKED_AFTER_RELEASE,
			"message": "Method decisions can only be recorded while the package is Draft or Returned for Correction.",
		}
	try:
		pp_policy.assert_may_record_method_decision(doc)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return {
			"allowed": False,
			"error_code": str(error_code),
			"message": str(exc),
		}
	return {"allowed": True, "error_code": None, "message": None}


def get_package_method_context(package_code: str, actor: str) -> dict[str, Any]:
	"""Return method/category context for a procurement package."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	pkg_name = _resolve_package_name(package_code)
	if not pkg_name:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)

	try:
		if not frappe.has_permission("Procurement Package", "read", pkg_name):
			return _fail(
				code="NO_PACKAGE_PERMISSION",
				message="You do not have permission to view this package.",
				role_key=role_key,
			)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this package.",
			role_key=role_key,
		)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		doc.check_permission("read")
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.DoesNotExistError:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this package.",
			role_key=role_key,
		)

	business_code = (doc.package_code or doc.name or "").strip()
	return {
		"ok": True,
		"role_key": role_key,
		"package": {
			"id": doc.name,
			"code": business_code,
			"name": (doc.package_name or business_code).strip(),
		},
		**format_package_method_tab(doc, business_code),
		"may_edit": _may_edit_method(doc, actor),
	}


def record_package_method_for_api(
	package_code: str, payload: dict[str, Any] | None, actor: str
) -> dict[str, Any]:
	"""Record method decision via P2-005 service with structured API errors."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	package_code = (package_code or "").strip()
	data = dict(payload or {})

	if not package_code:
		return _fail(
			code="NOT_FOUND",
			message="Package not found.",
			role_key=role_key,
		)

	try:
		out = record_package_method_decision(package_code, data, actor)
	except frappe.ValidationError as exc:
		guard = can_record_package_method_decision(package_code, data, actor)
		blockers = (guard.get("blockers") or []) if isinstance(guard, dict) else []
		error_code = (
			(blockers[0].get("code") if blockers else None)
			or getattr(exc, "title", None)
			or "VALIDATION_ERROR"
		)
		return _fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key,
			blockers=blockers or None,
		)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return _fail(
			code=str(error_code),
			message=str(exc),
			role_key=role_key,
		)

	return {
		"ok": True,
		"role_key": role_key,
		**out,
	}
