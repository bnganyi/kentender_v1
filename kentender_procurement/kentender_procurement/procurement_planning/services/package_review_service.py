# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Package review transitions (P2-007 submit; P2-008 approve/return)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_RETURNED,
)
from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	get_current_package_method_decision,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	get_current_package_readiness_result,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReviewDecision,
	PackageSubmitReview,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

_SUBMIT_ALLOWED_STATUSES = frozenset((PKG_DRAFT, PKG_RETURNED))
_DECISION_SUBMITTED = "Submitted for Review"
_DECISION_APPROVED = "Approved"
_DECISION_RETURNED = "Returned for Correction"
_REVIEW_DECISION_TYPES = frozenset((_DECISION_APPROVED, _DECISION_RETURNED))
_VALUE_TOLERANCE = 0.01


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _guard_check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _active_line_count(package_code: str) -> int:
	return frappe.db.count(
		"Procurement Package Line",
		{"package_id": package_code, "is_active": 1},
	)


def _load_active_lines(package_code: str) -> list[dict[str, Any]]:
	return frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code, "is_active": 1},
		fields=["name", "amount", "budget_line_id"],
		limit_page_length=500,
	)


def _review_decision_code(package_code: str) -> str:
	count = frappe.db.count("Package Review Decision", {"package_code": package_code})
	return f"PKGREV-{package_code}-{count + 1:03d}"


def _format_review_row(row: dict[str, Any]) -> dict[str, Any]:
	return {
		"review_decision_code": row.get("review_decision_code"),
		"package_code": row.get("package_code"),
		"decision_type": row.get("decision_type"),
		"decided_by": row.get("decided_by"),
		"decided_at": row.get("decided_at"),
		"from_state": row.get("from_state"),
		"to_state": row.get("to_state"),
		"decision_reason": row.get("decision_reason"),
		"required_correction": row.get("required_correction"),
		"readiness_code": row.get("readiness_code"),
		"method_decision_code": row.get("method_decision_code"),
	}


def _get_review_decision(review_decision_code: str) -> dict[str, Any] | None:
	if not review_decision_code or not frappe.db.exists(
		"Package Review Decision", review_decision_code
	):
		return None
	row = frappe.db.get_value(
		"Package Review Decision",
		review_decision_code,
		[
			"review_decision_code",
			"package_code",
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
	return _format_review_row(row) if row else None


def _latest_submitted_review(package_code: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Package Review Decision",
		filters={"package_code": package_code, "decision_type": _DECISION_SUBMITTED},
		fields=[
			"review_decision_code",
			"package_code",
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
		order_by="decided_at desc",
		limit=1,
	)
	return _format_review_row(rows[0]) if rows else None


def _latest_decision_by_type(package_code: str, decision_type: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Package Review Decision",
		filters={"package_code": package_code, "decision_type": decision_type},
		fields=[
			"review_decision_code",
			"package_code",
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
		order_by="decided_at desc",
		limit=1,
	)
	return _format_review_row(rows[0]) if rows else None


def _normalize_decision_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
	raw = dict(payload or {})
	decision = (raw.get("decision") or raw.get("decision_type") or "").strip()
	if decision == "Returned":
		decision = _DECISION_RETURNED
	reason = (raw.get("decision_reason") or raw.get("reason") or "").strip()
	correction = (raw.get("required_correction") or "").strip()
	return {
		"decision_type": decision,
		"decision_reason": reason,
		"required_correction": correction,
	}


def _is_self_approval_blocked(package_code: str, actor: str) -> bool:
	roles = set(frappe.get_roles(actor or frappe.session.user))
	if "Administrator" in roles or "System Manager" in roles:
		return False
	created_by = frappe.db.get_value("Procurement Package", package_code, "created_by") or ""
	return bool(created_by) and created_by == (actor or frappe.session.user)


def _structural_completeness_blockers(doc) -> list[str]:
	blockers: list[str] = []
	blockers.extend(get_package_completeness_blockers(doc))

	method_decision = get_current_package_method_decision(doc.name)
	category = (
		(method_decision or {}).get("procurement_category")
		or (doc.get("procurement_category") or "")
	).strip()
	method = (
		(method_decision or {}).get("procurement_method")
		or (doc.get("procurement_method") or "")
	).strip()

	if not (doc.get("package_name") or "").strip():
		blockers.append(_("Package title is required."))
	if not category:
		blockers.append(_("Procurement category is required."))
	if not method:
		blockers.append(_("Procurement method is required."))
	if flt(doc.get("estimated_value")) <= 0:
		blockers.append(_("Estimated value must be greater than zero."))
	if not (doc.get("currency") or "").strip():
		blockers.append(_("Currency is required."))

	budget_on_pkg = bool((doc.get("budget_line_id") or "").strip())
	lines = _load_active_lines(doc.name)
	if not budget_on_pkg and lines and not all(l.get("budget_line_id") for l in lines):
		blockers.append(_("Budget line link is required on the package or every active line."))

	if lines:
		line_sum = sum(flt(l.get("amount")) for l in lines)
		if abs(flt(doc.get("estimated_value")) - line_sum) > _VALUE_TOLERANCE:
			blockers.append(_("Package estimated value must equal the sum of active line amounts."))

	if not method_decision:
		blockers.append(_("A current package method decision is required."))
	else:
		if not (method_decision.get("method_basis") or "").strip():
			blockers.append(_("Method basis must be recorded on the method decision."))
		if method_decision.get("override_flag") and not (
			method_decision.get("override_reason") or ""
		).strip():
			blockers.append(_("Override reason is required when method is overridden."))

	return blockers


def can_submit_package_for_review(package_code: str, actor: str) -> dict[str, Any]:
	"""Read-only guard — whether a package may be submitted for review."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	package_code = (package_code or "").strip()

	pkg = None
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pkg = frappe.db.get_value(
			"Procurement Package",
			package_code,
			("name", "status", "locked_after_release"),
			as_dict=True,
		)
	pkg_ok = bool(pkg)
	checks.append(_guard_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackageSubmitReview.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	status = (pkg.get("status") or "").strip()
	state_ok = status in _SUBMIT_ALLOWED_STATUSES
	checks.append(
		_guard_check(
			"valid_state",
			_("Package is Draft or Returned for Correction"),
			state_ok,
		)
	)
	if not state_ok:
		if status == PKG_IN_REVIEW:
			latest = _latest_submitted_review(package_code)
			if latest and latest.get("to_state") == PKG_IN_REVIEW:
				return {
					"allowed": True,
					"blockers": [],
					"checks": checks,
					"idempotent_recall": True,
					"review_decision_code": latest.get("review_decision_code"),
				}
		blockers.append(
			_blocker(
				PackageSubmitReview.INVALID_STATE,
				_("Package must be Draft or Returned for Correction to submit for review."),
			)
		)

	locked = bool(cint(pkg.get("locked_after_release")))
	checks.append(_guard_check("not_locked", _("Package is not locked after release"), not locked))
	if locked:
		blockers.append(
			_blocker(
				PackageSubmitReview.LOCKED_AFTER_RELEASE,
				_("Package is locked after release and cannot be submitted for review."),
			)
		)

	line_count = _active_line_count(package_code)
	lines_ok = line_count > 0
	checks.append(_guard_check("package_lines", _("At least one active package line"), lines_ok))
	if not lines_ok:
		blockers.append(
			_blocker(
				PackageSubmitReview.NO_PACKAGE_LINE,
				_("The package must have at least one active package line."),
			)
		)

	doc = frappe.get_doc("Procurement Package", package_code)
	structural = _structural_completeness_blockers(doc)
	complete_ok = not structural
	checks.append(_guard_check("structural_complete", _("Package is structurally complete"), complete_ok))
	if structural:
		blockers.append(
			_blocker(
				PackageSubmitReview.PACKAGE_NOT_COMPLETE,
				_("Package is not complete: {0}").format("; ".join(structural)),
			)
		)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"from_state": status if state_ok else None,
	}


def _assert_can_submit_or_throw(package_code: str, actor: str) -> dict[str, Any]:
	guard = can_submit_package_for_review(package_code, actor)
	if guard.get("allowed"):
		return guard
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Package cannot be submitted for review."),
		title=first.get("code") or PackageSubmitReview.PACKAGE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _create_submitted_review_decision(
	*,
	package_code: str,
	from_state: str,
	actor: str,
) -> str:
	method_decision = get_current_package_method_decision(package_code)
	review_code = _review_decision_code(package_code)
	doc = frappe.get_doc(
		{
			"doctype": "Package Review Decision",
			"review_decision_code": review_code,
			"package_code": package_code,
			"decision_type": _DECISION_SUBMITTED,
			"decided_by": actor,
			"decided_at": now_datetime(),
			"from_state": from_state,
			"to_state": PKG_IN_REVIEW,
			"method_decision_code": (method_decision or {}).get("method_decision_code"),
			"is_master_seed": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return review_code


def _transition_package_to_in_review(
	package_code: str, *, review_decision_code: str, from_state: str
) -> None:
	doc = frappe.get_doc("Procurement Package", package_code)
	doc.status = PKG_IN_REVIEW
	doc.latest_review_code = review_decision_code
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)


def _format_submit_response(
	*,
	action: str,
	review_decision_code: str,
	package_code: str,
	from_state: str,
) -> dict[str, Any]:
	review = _get_review_decision(review_decision_code)
	return {
		"ok": True,
		"action": action,
		"review_decision_code": review_decision_code,
		"package_code": package_code,
		"from_state": from_state,
		"to_state": PKG_IN_REVIEW,
		"status": PKG_IN_REVIEW,
		"review": review,
	}


def submit_package_for_review(package_code: str, actor: str) -> dict[str, Any]:
	"""Submit a Draft or Returned package for review."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()

	guard = can_submit_package_for_review(package_code, actor_user)
	if guard.get("idempotent_recall"):
		code = guard.get("review_decision_code") or ""
		from_state = (
			(_get_review_decision(code) or {}).get("from_state")
			or frappe.db.get_value("Procurement Package", package_code, "status")
			or PKG_DRAFT
		)
		return _format_submit_response(
			action="recalled",
			review_decision_code=code,
			package_code=package_code,
			from_state=from_state,
		)

	guard = _assert_can_submit_or_throw(package_code, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_submit_package_for_review(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)
	from_state = guard.get("from_state") or PKG_DRAFT

	review_code = _create_submitted_review_decision(
		package_code=package_code,
		from_state=from_state,
		actor=actor_user,
	)
	_transition_package_to_in_review(
		package_code,
		review_decision_code=review_code,
		from_state=from_state,
	)
	journey_code = frappe.db.get_value("Procurement Package", package_code, "journey_code")
	record_planning_audit_event(
		event_type="Package Submitted for Review",
		object_type="Procurement Package",
		object_code=package_code,
		from_state=from_state,
		to_state=PKG_IN_REVIEW,
		evidence_ref=review_code,
		journey_code=journey_code,
		actor=actor_user,
	)
	return _format_submit_response(
		action="created",
		review_decision_code=review_code,
		package_code=package_code,
		from_state=from_state,
	)


def can_record_package_review_decision(
	package_code: str, decision_payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	"""Read-only guard — whether a review decision may be recorded."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	package_code = (package_code or "").strip()
	normalized = _normalize_decision_payload(decision_payload)
	decision_type = normalized.get("decision_type") or ""

	if decision_type not in _REVIEW_DECISION_TYPES:
		blockers.append(
			_blocker(
				PackageReviewDecision.INVALID_DECISION,
				_("Review decision must be Approved or Returned for Correction."),
			)
		)
		return {
			"allowed": False,
			"blockers": blockers,
			"checks": checks,
			"decision_type": decision_type,
		}

	pkg = None
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pkg = frappe.db.get_value(
			"Procurement Package",
			package_code,
			("name", "status", "locked_after_release", "created_by"),
			as_dict=True,
		)
	pkg_ok = bool(pkg)
	checks.append(_guard_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackageReviewDecision.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {
			"allowed": False,
			"blockers": blockers,
			"checks": checks,
			"decision_type": decision_type,
		}

	status = (pkg.get("status") or "").strip()
	target_state = PKG_APPROVED if decision_type == _DECISION_APPROVED else PKG_RETURNED

	if status == target_state:
		latest = _latest_decision_by_type(package_code, decision_type)
		if latest and latest.get("to_state") == target_state:
			if decision_type == _DECISION_APPROVED:
				return {
					"allowed": True,
					"blockers": [],
					"checks": checks,
					"decision_type": decision_type,
					"idempotent_recall": True,
					"review_decision_code": latest.get("review_decision_code"),
				}
			if (
				(latest.get("decision_reason") or "").strip() == normalized.get("decision_reason")
				and (latest.get("required_correction") or "").strip()
				== normalized.get("required_correction")
			):
				return {
					"allowed": True,
					"blockers": [],
					"checks": checks,
					"decision_type": decision_type,
					"idempotent_recall": True,
					"review_decision_code": latest.get("review_decision_code"),
				}

	state_ok = status == PKG_IN_REVIEW
	checks.append(_guard_check("valid_state", _("Package is In Review"), state_ok))
	if not state_ok:
		blockers.append(
			_blocker(
				PackageReviewDecision.INVALID_STATE,
				_("Package must be In Review to record this review decision."),
			)
		)

	locked = bool(cint(pkg.get("locked_after_release")))
	checks.append(_guard_check("not_locked", _("Package is not locked after release"), not locked))
	if locked:
		blockers.append(
			_blocker(
				PackageReviewDecision.LOCKED_AFTER_RELEASE,
				_("Package is locked after release and cannot be reviewed."),
			)
		)

	if decision_type == _DECISION_APPROVED:
		doc = frappe.get_doc("Procurement Package", package_code)
		structural = _structural_completeness_blockers(doc)
		complete_ok = not structural
		checks.append(
			_guard_check("structural_complete", _("Package is structurally complete"), complete_ok)
		)
		if structural:
			blockers.append(
				_blocker(
					PackageReviewDecision.PACKAGE_NOT_COMPLETE,
					_("Package is not complete: {0}").format("; ".join(structural)),
				)
			)

		self_ok = not _is_self_approval_blocked(package_code, actor)
		checks.append(
			_guard_check(
				"no_self_approval",
				_("Reviewer is not the package creator"),
				self_ok,
			)
		)
		if not self_ok:
			blockers.append(
				_blocker(
					PackageReviewDecision.SELF_APPROVAL_NOT_ALLOWED,
					_(
						"You cannot approve a procurement package you created (separation of duties)."
					),
				)
			)
	else:
		reason_ok = bool(normalized.get("decision_reason"))
		correction_ok = bool(normalized.get("required_correction"))
		checks.append(
			_guard_check("return_reason", _("Return reason is provided"), reason_ok)
		)
		checks.append(
			_guard_check(
				"required_correction",
				_("Required correction is provided"),
				correction_ok,
			)
		)
		if not reason_ok:
			blockers.append(
				_blocker(
					PackageReviewDecision.RETURN_REASON_REQUIRED,
					_("Decision reason is required when returning a package."),
				)
			)
		if not correction_ok:
			blockers.append(
				_blocker(
					PackageReviewDecision.RETURN_CORRECTION_REQUIRED,
					_("Required correction is required when returning a package."),
				)
			)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"decision_type": decision_type,
		"from_state": PKG_IN_REVIEW if state_ok else None,
		"to_state": target_state if state_ok else None,
	}


def _assert_can_record_or_throw(
	package_code: str, decision_payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	guard = can_record_package_review_decision(package_code, decision_payload, actor)
	if guard.get("allowed"):
		return guard
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Review decision cannot be recorded."),
		title=first.get("code") or PackageReviewDecision.PACKAGE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _create_review_decision(
	*,
	package_code: str,
	decision_type: str,
	from_state: str,
	to_state: str,
	actor: str,
	decision_reason: str | None = None,
	required_correction: str | None = None,
) -> str:
	method_decision = get_current_package_method_decision(package_code)
	readiness = get_current_package_readiness_result(package_code)
	review_code = _review_decision_code(package_code)
	doc = frappe.get_doc(
		{
			"doctype": "Package Review Decision",
			"review_decision_code": review_code,
			"package_code": package_code,
			"decision_type": decision_type,
			"decided_by": actor,
			"decided_at": now_datetime(),
			"from_state": from_state,
			"to_state": to_state,
			"decision_reason": decision_reason,
			"required_correction": required_correction,
			"readiness_code": (readiness or {}).get("readiness_code"),
			"method_decision_code": (method_decision or {}).get("method_decision_code"),
			"is_master_seed": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return review_code


def _transition_package_after_review(
	package_code: str,
	*,
	review_decision_code: str,
	to_state: str,
	workflow_reason: str | None = None,
) -> None:
	doc = frappe.get_doc("Procurement Package", package_code)
	doc.status = to_state
	doc.latest_review_code = review_decision_code
	doc.workflow_reason = workflow_reason
	doc.save(ignore_permissions=True)


def _format_decision_response(
	*,
	action: str,
	review_decision_code: str,
	package_code: str,
	from_state: str,
	to_state: str,
) -> dict[str, Any]:
	review = _get_review_decision(review_decision_code)
	return {
		"ok": True,
		"action": action,
		"review_decision_code": review_decision_code,
		"package_code": package_code,
		"from_state": from_state,
		"to_state": to_state,
		"status": to_state,
		"review": review,
	}


def record_package_review_decision(
	package_code: str, decision_payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	"""Record an Approved or Returned-for-Correction review decision."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()
	normalized = _normalize_decision_payload(decision_payload)
	decision_type = normalized.get("decision_type") or ""

	guard = can_record_package_review_decision(package_code, normalized, actor_user)
	if guard.get("idempotent_recall"):
		code = guard.get("review_decision_code") or ""
		review = _get_review_decision(code) or {}
		return _format_decision_response(
			action="recalled",
			review_decision_code=code,
			package_code=package_code,
			from_state=review.get("from_state") or PKG_IN_REVIEW,
			to_state=review.get("to_state")
			or (PKG_APPROVED if decision_type == _DECISION_APPROVED else PKG_RETURNED),
		)

	guard = _assert_can_record_or_throw(package_code, normalized, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_record_review_decision(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)
	from_state = guard.get("from_state") or PKG_IN_REVIEW
	to_state = guard.get("to_state") or (
		PKG_APPROVED if decision_type == _DECISION_APPROVED else PKG_RETURNED
	)

	review_code = _create_review_decision(
		package_code=package_code,
		decision_type=decision_type,
		from_state=from_state,
		to_state=to_state,
		actor=actor_user,
		decision_reason=normalized.get("decision_reason") or None,
		required_correction=normalized.get("required_correction") or None,
	)
	workflow_reason = None
	if decision_type == _DECISION_RETURNED:
		workflow_reason = normalized.get("decision_reason")

	_transition_package_after_review(
		package_code,
		review_decision_code=review_code,
		to_state=to_state,
		workflow_reason=workflow_reason,
	)
	journey_code = frappe.db.get_value("Procurement Package", package_code, "journey_code")
	event_type = (
		"Package Approved"
		if decision_type == _DECISION_APPROVED
		else "Package Returned for Correction"
	)
	record_planning_audit_event(
		event_type=event_type,
		object_type="Procurement Package",
		object_code=package_code,
		from_state=from_state,
		to_state=to_state,
		reason=normalized.get("decision_reason") or None,
		evidence_ref=review_code,
		journey_code=journey_code,
		actor=actor_user,
	)
	return _format_decision_response(
		action="created",
		review_decision_code=review_code,
		package_code=package_code,
		from_state=from_state,
		to_state=to_state,
	)
