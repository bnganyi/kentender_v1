# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-009 — Package readiness read/run API service (PP2 UI §16)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope
from kentender_procurement.procurement_planning.pp2_constants import READINESS_NOT_RUN
from kentender_procurement.procurement_planning.pp_package_business_readiness import (
	summarize_pp_package_business_readiness,
)
from kentender_procurement.procurement_planning.services.package_lines import (
	_resolve_package_name,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	can_run_package_readiness_checks,
	get_current_package_readiness_result,
	reconcile_package_readiness_staleness,
	run_package_readiness_checks,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReadiness,
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


def format_package_readiness_tab(doc, package_code: str) -> dict[str, Any]:
	"""Return readiness tab fields for workspace / dedicated API."""
	code = (package_code or "").strip()
	if code:
		reconcile_package_readiness_staleness(code)
	readiness_status = (doc.readiness_status or "").strip() or READINESS_NOT_RUN
	current = get_current_package_readiness_result(code) if code else None
	business = summarize_pp_package_business_readiness(doc)
	return {
		"readiness_status": readiness_status,
		"latest_readiness_code": (doc.latest_readiness_code or "").strip(),
		"current_result": current,
		"business_readiness": business,
	}


def _may_run_readiness(doc, actor: str, package_code: str) -> dict[str, Any]:
	guard = can_run_package_readiness_checks(package_code, actor)
	if not guard.get("allowed"):
		blockers = guard.get("blockers") or []
		first = blockers[0] if blockers else {}
		return {
			"allowed": False,
			"error_code": first.get("code") or PackageReadiness.PACKAGE_NOT_FOUND,
			"message": first.get("message") or "Readiness checks cannot be run for this package.",
		}
	try:
		pp_policy.assert_may_run_readiness_checks(doc)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return {
			"allowed": False,
			"error_code": str(error_code),
			"message": str(exc),
		}
	return {"allowed": True, "error_code": None, "message": None}


def get_package_readiness_context(package_code: str, actor: str) -> dict[str, Any]:
	"""Return readiness context for a procurement package."""
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
		doc = frappe.get_doc("Procurement Package", pkg_name)
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
		**format_package_readiness_tab(doc, business_code),
		"may_run": _may_run_readiness(doc, actor, business_code),
	}


def run_package_readiness_for_api(package_code: str, actor: str) -> dict[str, Any]:
	"""Run readiness checks via P2-006 service with structured API errors."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	package_code = (package_code or "").strip()

	if not package_code:
		return _fail(
			code="NOT_FOUND",
			message="Package not found.",
			role_key=role_key,
		)

	pkg_name = _resolve_package_name(package_code)
	if not pkg_name:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)

	business_code = (
		frappe.db.get_value("Procurement Package", pkg_name, "package_code") or pkg_name or ""
	).strip()

	try:
		out = run_package_readiness_checks(business_code, actor)
	except frappe.ValidationError as exc:
		guard = can_run_package_readiness_checks(business_code, actor)
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
