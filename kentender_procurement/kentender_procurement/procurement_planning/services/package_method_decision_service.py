# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Record Package Method Decision (P2-005)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	COMPETITIVE_METHODS,
	VALID_CONTRACT_TYPES,
	VALID_METHODS,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_EDITABLE_STATUSES,
	PKG_LOCKED_STATUSES,
	POST_RELEASE_LOCK_MESSAGE,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageMethodDecision,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

_CATEGORY_VALUES = frozenset(("Works", "Goods", "Services", "Consultancy"))
_METHOD_BASIS_VALUES = frozenset(("Template", "Threshold", "Manual Confirmation", "Rule Profile"))
_THRESHOLD_VALUES = frozenset(("PASS", "FAIL", "NOT APPLICABLE"))
_DECISION_STATUS = "Current"


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _method_decision_code(package_code: str) -> str:
	return f"METHDEC-{(package_code or '').strip()}"


def _normalize_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
	raw = dict(payload or {})
	std_type = (raw.get("required_std_type") or "").strip()
	if not std_type:
		version_code = (raw.get("required_std_template_version_code") or "").strip()
		if version_code:
			std_type = version_code
	override_flag = raw.get("override_flag")
	if isinstance(override_flag, str):
		override_flag = override_flag.strip().lower() in ("1", "true", "yes")
	else:
		override_flag = bool(override_flag)
	return {
		"procurement_category": (raw.get("procurement_category") or "").strip(),
		"procurement_method": (raw.get("procurement_method") or "").strip(),
		"required_std_category": (raw.get("required_std_category") or "").strip(),
		"required_std_type": std_type,
		"contract_type_expectation": (raw.get("contract_type_expectation") or "").strip(),
		"method_basis": (raw.get("method_basis") or "Template").strip(),
		"threshold_check_result": (raw.get("threshold_check_result") or "NOT APPLICABLE").strip(),
		"template_code": (raw.get("template_code") or "").strip(),
		"rule_profile_code": (raw.get("rule_profile_code") or "").strip(),
		"override_flag": override_flag,
		"override_reason": (raw.get("override_reason") or "").strip(),
		"approved_by": (raw.get("approved_by") or "").strip(),
		"approved_at": raw.get("approved_at"),
	}


def _decision_fingerprint(normalized: dict[str, Any]) -> tuple[Any, ...]:
	return (
		normalized.get("procurement_category"),
		normalized.get("procurement_method"),
		normalized.get("required_std_category"),
		normalized.get("required_std_type"),
		normalized.get("contract_type_expectation"),
		normalized.get("method_basis"),
		normalized.get("threshold_check_result"),
		normalized.get("template_code"),
		normalized.get("rule_profile_code"),
		bool(normalized.get("override_flag")),
		normalized.get("override_reason"),
	)


def _row_fingerprint(row: dict[str, Any]) -> tuple[Any, ...]:
	return (
		(row.get("procurement_category") or "").strip(),
		(row.get("procurement_method") or "").strip(),
		(row.get("required_std_category") or "").strip(),
		(row.get("required_std_type") or "").strip(),
		(row.get("contract_type_expectation") or "").strip(),
		(row.get("method_basis") or "").strip(),
		(row.get("threshold_check_result") or "").strip(),
		(row.get("template_code") or "").strip(),
		(row.get("rule_profile_code") or "").strip(),
		bool(cint(row.get("override_flag"))),
		(row.get("override_reason") or "").strip(),
	)


def _format_method_decision(row: dict[str, Any]) -> dict[str, Any]:
	return {
		"method_decision_code": row.get("method_decision_code"),
		"package_code": row.get("package_code"),
		"procurement_category": row.get("procurement_category"),
		"procurement_method": row.get("procurement_method"),
		"required_std_category": row.get("required_std_category"),
		"required_std_type": row.get("required_std_type"),
		"contract_type_expectation": row.get("contract_type_expectation"),
		"method_basis": row.get("method_basis"),
		"threshold_check_result": row.get("threshold_check_result"),
		"template_code": row.get("template_code"),
		"rule_profile_code": row.get("rule_profile_code"),
		"override_flag": bool(cint(row.get("override_flag"))),
		"override_reason": row.get("override_reason"),
		"decided_by": row.get("decided_by"),
		"decided_at": row.get("decided_at"),
		"approved_by": row.get("approved_by"),
		"approved_at": row.get("approved_at"),
		"is_current": bool(cint(row.get("is_current"))),
		"status": _DECISION_STATUS if cint(row.get("is_current")) else "Superseded",
	}


def get_current_package_method_decision(package_code: str) -> dict[str, Any] | None:
	package_code = (package_code or "").strip()
	if not package_code:
		return None
	row = frappe.db.get_value(
		"Package Method Decision",
		{"package_code": package_code, "is_current": 1},
		[
			"method_decision_code",
			"package_code",
			"procurement_category",
			"procurement_method",
			"required_std_category",
			"required_std_type",
			"contract_type_expectation",
			"method_basis",
			"threshold_check_result",
			"template_code",
			"rule_profile_code",
			"override_flag",
			"override_reason",
			"decided_by",
			"decided_at",
			"approved_by",
			"approved_at",
			"is_current",
		],
		as_dict=True,
		order_by="modified desc",
	)
	if not row:
		return None
	return _format_method_decision(row)


def _find_matching_current_decision(
	package_code: str, normalized: dict[str, Any]
) -> dict[str, Any] | None:
	current = get_current_package_method_decision(package_code)
	if not current:
		return None
	row = frappe.db.get_value(
		"Package Method Decision",
		current["method_decision_code"],
		[
			"method_decision_code",
			"package_code",
			"procurement_category",
			"procurement_method",
			"required_std_category",
			"required_std_type",
			"contract_type_expectation",
			"method_basis",
			"threshold_check_result",
			"template_code",
			"rule_profile_code",
			"override_flag",
			"override_reason",
			"decided_by",
			"decided_at",
			"approved_by",
			"approved_at",
			"is_current",
		],
		as_dict=True,
	)
	if row and _row_fingerprint(row) == _decision_fingerprint(normalized):
		return _format_method_decision(row)
	return None


def _active_line_count(package_code: str) -> int:
	return frappe.db.count(
		"Procurement Package Line",
		{"package_id": package_code, "is_active": 1},
	)


def can_record_package_method_decision(
	package_code: str, payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	"""Read-only guard — whether a method decision may be recorded for a package."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	normalized = _normalize_payload(payload)
	package_code = (package_code or "").strip()

	pkg = None
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pkg = frappe.db.get_value(
			"Procurement Package",
			package_code,
			("name", "status", "journey_code"),
			as_dict=True,
		)
	pkg_ok = bool(pkg)
	checks.append(_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackageMethodDecision.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	status = (pkg.get("status") or "").strip()
	if status in PKG_LOCKED_STATUSES:
		checks.append(_check("package_editable", _("Package is editable"), False))
		blockers.append(
			_blocker(
				PackageMethodDecision.LOCKED_AFTER_RELEASE,
				_(POST_RELEASE_LOCK_MESSAGE),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	editable = status in PKG_EDITABLE_STATUSES
	checks.append(_check("package_editable", _("Package is editable"), editable))
	if not editable:
		blockers.append(
			_blocker(
				PackageMethodDecision.LOCKED_AFTER_RELEASE,
				_("Method decisions can only be recorded while the package is Draft or Returned for Correction."),
			)
		)

	line_count = _active_line_count(package_code)
	lines_ok = line_count > 0
	checks.append(_check("package_has_lines", _("Package has active lines"), lines_ok))
	if not lines_ok:
		blockers.append(
			_blocker(
				PackageMethodDecision.NO_PACKAGE_LINE,
				_("The package must have at least one active package line."),
			)
		)

	category = normalized.get("procurement_category") or ""
	method = normalized.get("procurement_method") or ""
	std_category = normalized.get("required_std_category") or ""
	category_ok = category in _CATEGORY_VALUES
	method_ok = method in VALID_METHODS
	std_ok = bool(std_category)
	checks.append(_check("category_valid", _("Procurement category is valid"), category_ok))
	checks.append(_check("method_valid", _("Procurement method is valid"), method_ok))
	checks.append(_check("std_category_present", _("Required STD category is present"), std_ok))
	if not category_ok or not category:
		blockers.append(
			_blocker(
				PackageMethodDecision.STD_CATEGORY_MISSING,
				_("Procurement category and required STD category must be provided."),
			)
		)
	elif not std_ok:
		blockers.append(
			_blocker(
				PackageMethodDecision.STD_CATEGORY_MISSING,
				_("Required STD category must be provided."),
			)
		)
	if category_ok and not method_ok:
		blockers.append(
			_blocker(
				PackageMethodDecision.METHOD_MISSING,
				_("A valid procurement method must be provided."),
			)
		)

	basis = normalized.get("method_basis") or ""
	basis_ok = basis in _METHOD_BASIS_VALUES
	checks.append(_check("method_basis_valid", _("Method basis is valid"), basis_ok))
	if not basis_ok:
		blockers.append(
			_blocker(
				PackageMethodDecision.METHOD_MISSING,
				_("Method basis must be Template, Threshold, Manual Confirmation, or Rule Profile."),
			)
		)

	threshold = normalized.get("threshold_check_result") or ""
	if threshold and threshold not in _THRESHOLD_VALUES:
		blockers.append(
			_blocker(
				PackageMethodDecision.METHOD_MISSING,
				_("Threshold check result must be PASS, FAIL, or NOT APPLICABLE."),
			)
		)

	override_ok = not normalized.get("override_flag") or bool(normalized.get("override_reason"))
	checks.append(_check("override_reason", _("Override reason provided when required"), override_ok))
	if not override_ok:
		blockers.append(
			_blocker(
				PackageMethodDecision.METHOD_OVERRIDE_REASON,
				_("Override reason is required when method is overridden."),
			)
		)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"normalized_payload": normalized,
	}


def _assert_can_record_or_throw(
	package_code: str, payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	guard = can_record_package_method_decision(package_code, payload, actor)
	if guard.get("allowed"):
		return guard["normalized_payload"]
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Method decision cannot be recorded for this package."),
		title=first.get("code") or PackageMethodDecision.PACKAGE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _sync_package_from_decision(package_code: str, normalized: dict[str, Any]) -> None:
	contract_type = normalized.get("contract_type_expectation") or ""
	if contract_type and contract_type not in VALID_CONTRACT_TYPES:
		contract_type = ""
	patch: dict[str, Any] = {
		"procurement_category": normalized.get("procurement_category"),
		"procurement_method": normalized.get("procurement_method"),
		"required_std_category": normalized.get("required_std_category"),
		"required_std_type": normalized.get("required_std_type") or None,
		"method_override_flag": 1 if normalized.get("override_flag") else 0,
		"method_override_reason": normalized.get("override_reason") or None,
	}
	if contract_type:
		patch["contract_type"] = contract_type
	elif normalized.get("procurement_method") in COMPETITIVE_METHODS:
		existing = frappe.db.get_value("Procurement Package", package_code, "contract_type")
		if not existing:
			patch["contract_type"] = "Fixed Price"
	frappe.db.set_value("Procurement Package", package_code, patch, update_modified=False)


def _format_response(*, action: str, method_decision_code: str, package_code: str) -> dict[str, Any]:
	decision = get_current_package_method_decision(package_code)
	return {
		"ok": True,
		"action": action,
		"method_decision_code": method_decision_code,
		"package_code": package_code,
		"status": _DECISION_STATUS,
		"method_decision": decision,
	}


def _create_or_update_method_decision(
	*,
	package_code: str,
	normalized: dict[str, Any],
	actor: str,
	had_different_current: bool,
) -> tuple[str, str]:
	decision_code = _method_decision_code(package_code)
	now = now_datetime()
	doc_fields = {
		"doctype": "Package Method Decision",
		"method_decision_code": decision_code,
		"package_code": package_code,
		"procurement_category": normalized["procurement_category"],
		"procurement_method": normalized["procurement_method"],
		"required_std_category": normalized["required_std_category"],
		"required_std_type": normalized.get("required_std_type") or None,
		"contract_type_expectation": normalized.get("contract_type_expectation") or None,
		"method_basis": normalized["method_basis"],
		"threshold_check_result": normalized.get("threshold_check_result") or "NOT APPLICABLE",
		"template_code": normalized.get("template_code") or None,
		"rule_profile_code": normalized.get("rule_profile_code") or None,
		"override_flag": 1 if normalized.get("override_flag") else 0,
		"override_reason": normalized.get("override_reason") or None,
		"decided_by": actor,
		"decided_at": now,
		"approved_by": normalized.get("approved_by") or None,
		"approved_at": normalized.get("approved_at") or None,
		"is_current": 1,
	}

	frappe.db.sql(
		"""
		UPDATE `tabPackage Method Decision`
		SET is_current = 0
		WHERE package_code = %s AND is_current = 1 AND method_decision_code != %s
		""",
		(package_code, decision_code),
	)

	if frappe.db.exists("Package Method Decision", decision_code):
		frappe.db.set_value("Package Method Decision", decision_code, doc_fields, update_modified=True)
		action = "superseded" if had_different_current else "created"
	else:
		doc = frappe.get_doc(doc_fields)
		doc.insert(ignore_permissions=True)
		action = "created"

	_sync_package_from_decision(package_code, normalized)
	journey_code = frappe.db.get_value("Procurement Package", package_code, "journey_code")
	record_planning_audit_event(
		event_type="Method Decision Recorded",
		object_type="Package Method Decision",
		object_code=decision_code,
		to_state=_DECISION_STATUS,
		evidence_ref=package_code,
		journey_code=journey_code,
		actor=actor,
	)
	return decision_code, action


def record_package_method_decision(
	package_code: str, payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	"""Create or return the current Package Method Decision for a Draft package."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "").strip() or frappe.session.user
	normalized = _normalize_payload(payload)

	existing = _find_matching_current_decision(package_code, normalized)
	if existing:
		return _format_response(
			action="existing",
			method_decision_code=existing["method_decision_code"],
			package_code=package_code,
		)

	had_different_current = bool(get_current_package_method_decision(package_code))
	normalized = _assert_can_record_or_throw(package_code, normalized, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_record_method_decision(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)

	decision_code, action = _create_or_update_method_decision(
		package_code=package_code,
		normalized=normalized,
		actor=actor_user,
		had_different_current=had_different_current,
	)
	return _format_response(
		action=action,
		method_decision_code=decision_code,
		package_code=package_code,
	)
