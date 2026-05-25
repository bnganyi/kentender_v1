# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-011 — Package release read/write API service (PP2 UI §18)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.package_planning_release_display import (
	summarize_planning_release_handoff_for_package_detail,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_READY_FOR_RELEASE,
)
from kentender_procurement.procurement_planning.services.package_lines import (
	_resolve_package_name,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	can_mark_package_ready_for_release,
	can_release_package_to_tender_management,
	mark_package_ready_for_release,
	release_package_to_tender_management,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageMarkReady,
	PackageReleaseToTender,
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


def format_package_release_tab(doc, package_code: str) -> dict[str, Any]:
	"""Return release tab fields for workspace / dedicated API."""
	business_code = (package_code or doc.name or "").strip()
	release = (
		summarize_planning_release_handoff_for_package_detail(business_code)
		if business_code
		else None
	)
	return {"release": release}


def _may_mark_ready(doc, actor: str, package_code: str) -> dict[str, Any]:
	guard = can_mark_package_ready_for_release(package_code, actor)
	if not guard.get("allowed"):
		blockers = guard.get("blockers") or []
		first = blockers[0] if blockers else {}
		return {
			"allowed": False,
			"error_code": first.get("code") or PackageMarkReady.PACKAGE_NOT_FOUND,
			"message": first.get("message") or "Package cannot be marked ready for release.",
		}
	try:
		pp_policy.assert_may_mark_package_ready_for_release(doc)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return {
			"allowed": False,
			"error_code": str(error_code),
			"message": str(exc),
		}
	return {"allowed": True, "error_code": None, "message": None}


def _may_release(doc) -> dict[str, Any]:
	if bool(cint(doc.locked_after_release)):
		return {
			"allowed": False,
			"error_code": PackageMarkReady.LOCKED_AFTER_RELEASE,
			"message": "Package is locked after release and cannot be released again.",
		}
	status = (doc.status or "").strip()
	if status != PKG_READY_FOR_RELEASE:
		return {
			"allowed": False,
			"error_code": PackageReleaseToTender.INVALID_STATE,
			"message": "Package must be Ready for Release to release to tender management.",
		}
	try:
		pp_policy.assert_may_release_package_to_tender(doc)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return {
			"allowed": False,
			"error_code": str(error_code),
			"message": str(exc),
		}
	return {"allowed": True, "error_code": None, "message": None}


def get_package_release_context(package_code: str, actor: str) -> dict[str, Any]:
	"""Return release context for a procurement package."""
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
		"package_status": (doc.status or "").strip(),
		"locked_after_release": bool(cint(doc.locked_after_release)),
		**format_package_release_tab(doc, business_code),
		"may_mark_ready": _may_mark_ready(doc, actor, business_code),
		"may_release": _may_release(doc),
	}


def mark_package_ready_for_api(package_code: str, actor: str) -> dict[str, Any]:
	"""Mark package ready for release via P2-009 service with structured API errors."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	package_code = (package_code or "").strip()

	if not package_code:
		return _fail(
			code="NOT_FOUND",
			message="Package not found.",
			role_key=role_key,
		)

	try:
		out = mark_package_ready_for_release(package_code, actor)
	except frappe.ValidationError as exc:
		guard = can_mark_package_ready_for_release(package_code, actor)
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


def release_package_to_tender_for_api(package_code: str, actor: str) -> dict[str, Any]:
	"""Release package to tender via P2-010 service with structured API errors."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	package_code = (package_code or "").strip()

	if not package_code:
		return _fail(
			code="NOT_FOUND",
			message="Package not found.",
			role_key=role_key,
		)

	try:
		out = release_package_to_tender_management(package_code, actor)
	except frappe.ValidationError as exc:
		guard = can_release_package_to_tender_management(package_code, actor)
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
