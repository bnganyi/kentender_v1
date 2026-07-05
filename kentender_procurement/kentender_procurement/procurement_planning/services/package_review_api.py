# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-010 — Package review read/write API service (PP2 UI §17)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PKG_IN_REVIEW
from kentender_procurement.procurement_planning.services.package_lines import (
	_resolve_package_name,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	can_record_package_review_decision,
	record_package_review_decision,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReviewDecision,
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


def _format_review_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
	if not row:
		return None
	return {
		"review_decision_code": (row.get("review_decision_code") or "").strip(),
		"decision_type": (row.get("decision_type") or "").strip(),
		"decided_by": (row.get("decided_by") or "").strip(),
		"decided_at": row.get("decided_at"),
		"from_state": (row.get("from_state") or "").strip(),
		"to_state": (row.get("to_state") or "").strip(),
		"decision_reason": (row.get("decision_reason") or "").strip(),
		"required_correction": (row.get("required_correction") or "").strip(),
		"readiness_code": (row.get("readiness_code") or "").strip(),
		"method_decision_code": (row.get("method_decision_code") or "").strip(),
	}


def _latest_review(package_code: str, latest_review_code: str | None) -> dict[str, Any] | None:
	code = (latest_review_code or "").strip()
	if code and frappe.db.exists("Package Review Decision", code):
		row = frappe.db.get_value(
			"Package Review Decision",
			code,
			[
				"review_decision_code",
				"decision_type",
				"decided_by",
				"decided_at",
				"from_state",
				"to_state",
				"decision_reason",
				"required_correction",
				"readiness_code",
				"method_decision_code",
			],
			as_dict=True,
		)
		return _format_review_row(row)

	rows = frappe.get_all(
		"Package Review Decision",
		filters={"package_code": package_code},
		fields=[
			"review_decision_code",
			"decision_type",
			"decided_by",
			"decided_at",
			"from_state",
			"to_state",
			"decision_reason",
			"required_correction",
			"readiness_code",
			"method_decision_code",
		],
		order_by="decided_at desc, modified desc",
		limit=1,
	)
	return _format_review_row(rows[0]) if rows else None


def format_package_review_tab(doc, package_code: str) -> dict[str, Any]:
	"""Return review tab fields for workspace / dedicated API."""
	business_code = (package_code or doc.name or "").strip()
	return {
		"latest_review": _latest_review(business_code, doc.latest_review_code),
	}


def _may_approve(doc, actor: str, package_code: str) -> dict[str, Any]:
	status = (doc.status or "").strip()
	if status != PKG_IN_REVIEW:
		return {
			"allowed": False,
			"error_code": PackageReviewDecision.INVALID_STATE,
			"message": "Package must be In Review to approve.",
		}
	guard = can_record_package_review_decision(
		package_code, {"decision": "Approved"}, actor
	)
	if not guard.get("allowed"):
		blockers = guard.get("blockers") or []
		first = blockers[0] if blockers else {}
		return {
			"allowed": False,
			"error_code": first.get("code") or PackageReviewDecision.PACKAGE_NOT_FOUND,
			"message": first.get("message") or "Review approval cannot be recorded for this package.",
		}
	try:
		pp_policy.assert_may_record_review_decision(doc)
	except (frappe.PermissionError, frappe.ValidationError) as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return {
			"allowed": False,
			"error_code": str(error_code),
			"message": str(exc),
		}
	return {"allowed": True, "error_code": None, "message": None}


def _may_return(doc, actor: str) -> dict[str, Any]:
	status = (doc.status or "").strip()
	if status != PKG_IN_REVIEW:
		return {
			"allowed": False,
			"error_code": PackageReviewDecision.INVALID_STATE,
			"message": "Package must be In Review to return for correction.",
		}
	if bool(cint(doc.locked_after_release)):
		return {
			"allowed": False,
			"error_code": PackageReviewDecision.LOCKED_AFTER_RELEASE,
			"message": "Package is locked after release and cannot be reviewed.",
		}
	try:
		pp_policy.assert_may_record_review_decision(doc)
	except frappe.PermissionError as exc:
		error_code = getattr(exc, "title", None) or PlanningPermission.NOT_PERMITTED
		return {
			"allowed": False,
			"error_code": str(error_code),
			"message": str(exc),
		}
	return {"allowed": True, "error_code": None, "message": None}


def get_package_review_context(package_code: str, actor: str) -> dict[str, Any]:
	"""Return review context for a procurement package."""
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
		**format_package_review_tab(doc, business_code),
		"may_approve": _may_approve(doc, actor, business_code),
		"may_return": _may_return(doc, actor),
	}


def record_package_review_for_api(
	package_code: str, payload: dict[str, Any] | None, actor: str
) -> dict[str, Any]:
	"""Record review decision via P2-008 service with structured API errors."""
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
		out = record_package_review_decision(package_code, data, actor)
	except frappe.ValidationError as exc:
		guard = can_record_package_review_decision(package_code, data, actor)
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
