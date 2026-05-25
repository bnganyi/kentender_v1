# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Package release transitions (P2-009 mark ready; P2-010 release to tender)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from kentender_procurement.procurement_lifecycle.planning_release_handoff import (
	create_planning_release_package,
)
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PLAN_ACTIVE,
	READINESS_PASSED,
	READINESS_PASSED_WARNINGS,
)
from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	get_current_package_readiness_result,
	reconcile_package_readiness_staleness,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageMarkReady,
	PackageReleaseToTender,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope
from kentender_procurement.procurement_planning.services.tendering_handoff import (
	build_release_payload,
	deliver_procurement_package_release,
)
from kentender_procurement.tender_management.services.planning_tender_handoff_xmv import (
	format_xmv_critical_message,
	validate_package_for_release_xmv,
)
from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	package_has_release_tender,
)

_PASSING_READINESS_STATUSES = frozenset((READINESS_PASSED, READINESS_PASSED_WARNINGS))


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _guard_check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _readiness_passes_mark_ready_gate(readiness: dict[str, Any] | None) -> bool:
	if not readiness:
		return False
	if readiness.get("stale"):
		return False
	return (readiness.get("result_status") or "").strip() in _PASSING_READINESS_STATUSES


def can_mark_package_ready_for_release(package_code: str, actor: str) -> dict[str, Any]:
	"""Read-only guard — whether a package may be marked ready for release."""
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
				PackageMarkReady.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	status = (pkg.get("status") or "").strip()
	if status == PKG_READY_FOR_RELEASE:
		reconcile_package_readiness_staleness(package_code)
		readiness = get_current_package_readiness_result(package_code)
		return {
			"allowed": True,
			"blockers": [],
			"checks": checks,
			"idempotent_recall": True,
			"readiness_code": (readiness or {}).get("readiness_code"),
		}

	state_ok = status == PKG_APPROVED
	checks.append(_guard_check("valid_state", _("Package is Approved"), state_ok))
	if not state_ok:
		blockers.append(
			_blocker(
				PackageMarkReady.INVALID_STATE,
				_("Package must be Approved to mark ready for release."),
			)
		)

	locked = bool(cint(pkg.get("locked_after_release")))
	checks.append(_guard_check("not_locked", _("Package is not locked after release"), not locked))
	if locked:
		blockers.append(
			_blocker(
				PackageMarkReady.LOCKED_AFTER_RELEASE,
				_("Package is locked after release and cannot be marked ready."),
			)
		)

	if state_ok and not locked:
		reconcile_package_readiness_staleness(package_code)
		readiness = get_current_package_readiness_result(package_code)
		stale = bool(readiness and readiness.get("stale"))
		passes = _readiness_passes_mark_ready_gate(readiness)
		checks.append(
			_guard_check(
				"readiness_not_stale",
				_("Current readiness result is not stale"),
				not stale,
			)
		)
		checks.append(
			_guard_check(
				"readiness_passed",
				_("Current readiness result passed or passed with warnings"),
				passes,
			)
		)
		if stale:
			blockers.append(
				_blocker(
					PackageMarkReady.READINESS_STALE,
					_("Current readiness result is stale. Rerun readiness checks."),
				)
			)
		elif not passes:
			blockers.append(
				_blocker(
					PackageMarkReady.READINESS_FAILED,
					_("A current passed readiness result is required before marking ready for release."),
				)
			)

	readiness_code = None
	if state_ok and not locked and not blockers:
		readiness_code = (get_current_package_readiness_result(package_code) or {}).get(
			"readiness_code"
		)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"from_state": PKG_APPROVED if state_ok else None,
		"to_state": PKG_READY_FOR_RELEASE if state_ok else None,
		"readiness_code": readiness_code,
	}


def _assert_can_mark_ready_or_throw(package_code: str, actor: str) -> dict[str, Any]:
	guard = can_mark_package_ready_for_release(package_code, actor)
	if guard.get("allowed"):
		return guard
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Package cannot be marked ready for release."),
		title=first.get("code") or PackageMarkReady.PACKAGE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _transition_package_to_ready_for_release(package_code: str) -> None:
	doc = frappe.get_doc("Procurement Package", package_code)
	doc.status = PKG_READY_FOR_RELEASE
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)


def _format_mark_ready_response(
	*,
	action: str,
	package_code: str,
	from_state: str,
	readiness_code: str | None,
) -> dict[str, Any]:
	return {
		"ok": True,
		"action": action,
		"package_code": package_code,
		"from_state": from_state,
		"to_state": PKG_READY_FOR_RELEASE,
		"status": PKG_READY_FOR_RELEASE,
		"readiness_code": readiness_code,
	}


def mark_package_ready_for_release(package_code: str, actor: str) -> dict[str, Any]:
	"""Mark an Approved package ready for release when readiness has passed."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()

	guard = can_mark_package_ready_for_release(package_code, actor_user)
	if guard.get("idempotent_recall"):
		readiness_code = guard.get("readiness_code")
		return _format_mark_ready_response(
			action="recalled",
			package_code=package_code,
			from_state=PKG_APPROVED,
			readiness_code=readiness_code,
		)

	guard = _assert_can_mark_ready_or_throw(package_code, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_mark_package_ready_for_release(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)
	readiness_code = guard.get("readiness_code") or (
		get_current_package_readiness_result(package_code) or {}
	).get("readiness_code")

	_transition_package_to_ready_for_release(package_code)
	journey_code = frappe.db.get_value("Procurement Package", package_code, "journey_code")
	record_planning_audit_event(
		event_type="Package Marked Ready for Release",
		object_type="Procurement Package",
		object_code=package_code,
		from_state=PKG_APPROVED,
		to_state=PKG_READY_FOR_RELEASE,
		evidence_ref=readiness_code,
		journey_code=journey_code,
		actor=actor_user,
	)
	return _format_mark_ready_response(
		action="created",
		package_code=package_code,
		from_state=PKG_APPROVED,
		readiness_code=readiness_code,
	)


def _release_handoff_code(package_code: str) -> str | None:
	journey_code = frappe.db.get_value("Procurement Package", package_code, "journey_code")
	if not journey_code:
		return None
	release_code = (frappe.db.get_value("Procurement Package", package_code, "release_code") or "").strip()
	if release_code:
		return release_code
	return pkgrel_handoff_code_from_journey_code(journey_code) or None


def can_release_package_to_tender_management(package_code: str, actor: str) -> dict[str, Any]:
	"""Read-only guard — whether a package may be released to tender management."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	package_code = (package_code or "").strip()

	pkg = None
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pkg = frappe.db.get_value(
			"Procurement Package",
			package_code,
			("name", "status", "plan_id", "journey_code", "release_code"),
			as_dict=True,
		)
	pkg_ok = bool(pkg)
	checks.append(_guard_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackageReleaseToTender.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	status = (pkg.get("status") or "").strip()
	if status == PKG_RELEASED:
		release_code = _release_handoff_code(package_code)
		return {
			"allowed": True,
			"blockers": [],
			"checks": checks,
			"idempotent_recall": True,
			"release_code": release_code,
		}

	state_ok = status == PKG_READY_FOR_RELEASE
	checks.append(
		_guard_check("valid_state", _("Package is Ready for Release"), state_ok)
	)
	if not state_ok:
		blockers.append(
			_blocker(
				PackageReleaseToTender.INVALID_STATE,
				_("Package must be Ready for Release to release to tender management."),
			)
		)

	journey_code = (pkg.get("journey_code") or "").strip()
	journey_ok = bool(journey_code)
	checks.append(_guard_check("journey_code", _("Procurement journey is linked"), journey_ok))
	if not journey_ok and state_ok:
		blockers.append(
			_blocker(
				PackageReleaseToTender.PACKAGE_NOT_COMPLETE,
				_("Procurement journey code is required to create a Planning Release Package."),
			)
		)

	plan_active = False
	if pkg.get("plan_id"):
		plan_st = frappe.db.get_value("Procurement Plan", pkg.get("plan_id"), "status")
		plan_active = (plan_st or "").strip() == PLAN_ACTIVE
	checks.append(_guard_check("plan_active", _("Procurement plan is Active"), plan_active))
	if state_ok and pkg.get("plan_id") and not plan_active:
		blockers.append(
			_blocker(
				PackageReleaseToTender.PLAN_NOT_ACTIVE,
				_("Procurement Plan must be Active before release to tender."),
			)
		)

	if state_ok and not blockers:
		reconcile_package_readiness_staleness(package_code)
		readiness = get_current_package_readiness_result(package_code)
		stale = bool(readiness and readiness.get("stale"))
		passes = _readiness_passes_mark_ready_gate(readiness)
		checks.append(
			_guard_check(
				"readiness_not_stale",
				_("Current readiness result is not stale"),
				not stale,
			)
		)
		checks.append(
			_guard_check(
				"readiness_passed",
				_("Current readiness result passed or passed with warnings"),
				passes,
			)
		)
		if stale:
			blockers.append(
				_blocker(
					PackageReleaseToTender.READINESS_STALE,
					_("Current readiness result is stale. Rerun readiness checks."),
				)
			)
		elif not passes:
			blockers.append(
				_blocker(
					PackageReleaseToTender.READINESS_FAILED,
					_("A current passed readiness result is required before release."),
				)
			)

		doc = frappe.get_doc("Procurement Package", package_code)
		structural = get_package_completeness_blockers(doc)
		complete_ok = not structural
		checks.append(
			_guard_check("structural_complete", _("Package is structurally complete"), complete_ok)
		)
		if structural:
			blockers.append(
				_blocker(
					PackageReleaseToTender.PACKAGE_NOT_COMPLETE,
					_("Package is not complete: {0}").format("; ".join(structural)),
				)
			)

		xmv = validate_package_for_release_xmv(doc)
		xmv_ok = not xmv.has_critical()
		checks.append(
			_guard_check("xmv_clear", _("Planning-to-tender validation has no critical findings"), xmv_ok)
		)
		if not xmv_ok:
			blockers.append(
				_blocker(
					PackageReleaseToTender.XMV_BLOCKED,
					format_xmv_critical_message(xmv),
				)
			)

	readiness_code = None
	if state_ok and not blockers:
		readiness_code = (get_current_package_readiness_result(package_code) or {}).get(
			"readiness_code"
		)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"from_state": PKG_READY_FOR_RELEASE if state_ok else None,
		"to_state": PKG_RELEASED if state_ok else None,
		"readiness_code": readiness_code,
		"journey_code": journey_code if journey_ok else None,
	}


def _assert_can_release_or_throw(package_code: str, actor: str) -> dict[str, Any]:
	guard = can_release_package_to_tender_management(package_code, actor)
	if guard.get("allowed"):
		return guard
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Package cannot be released to tender management."),
		title=first.get("code") or PackageReleaseToTender.PACKAGE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _transition_package_to_released(
	package_code: str, *, release_code: str
) -> None:
	try:
		frappe.local.pp_allow_package_release_to_tender = True
		doc = frappe.get_doc("Procurement Package", package_code)
		doc.status = PKG_RELEASED
		doc.release_code = release_code
		doc.released_to_tender_at = now_datetime()
		doc.workflow_reason = None
		doc.save(ignore_permissions=True)
	finally:
		if hasattr(frappe.local, "pp_allow_package_release_to_tender"):
			delattr(frappe.local, "pp_allow_package_release_to_tender")


def _format_release_response(
	*,
	action: str,
	package_code: str,
	release_code: str | None,
	readiness_code: str | None,
	handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
	return {
		"ok": True,
		"action": action,
		"package_code": package_code,
		"from_state": PKG_READY_FOR_RELEASE,
		"to_state": PKG_RELEASED,
		"status": PKG_RELEASED,
		"release_code": release_code,
		"readiness_code": readiness_code,
		"handoff": handoff,
	}


def release_package_to_tender_management(package_code: str, actor: str) -> dict[str, Any]:
	"""Release a Ready for Release package to tender management."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()

	guard = can_release_package_to_tender_management(package_code, actor_user)
	if guard.get("idempotent_recall"):
		release_code = guard.get("release_code")
		readiness_code = (get_current_package_readiness_result(package_code) or {}).get(
			"readiness_code"
		)
		return _format_release_response(
			action="recalled",
			package_code=package_code,
			release_code=release_code,
			readiness_code=readiness_code,
		)

	guard = _assert_can_release_or_throw(package_code, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_release_package_to_tender(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)
	journey_code = guard.get("journey_code") or ""
	readiness_code = guard.get("readiness_code")

	doc = frappe.get_doc("Procurement Package", package_code)
	payload = build_release_payload(doc)
	deliver_procurement_package_release(payload)

	if not package_has_release_tender(package_code):
		frappe.throw(
			_(
				"No tender was linked to this package after the release handoff. "
				"Check Error Log for release-to-tender hook messages."
			),
			title=PackageReleaseToTender.HANDOFF_INCOMPLETE,
			exc=frappe.ValidationError,
		)

	release_code = pkgrel_handoff_code_from_journey_code(journey_code)

	_transition_package_to_released(package_code, release_code=release_code or "")

	handoff_out = create_planning_release_package(package_code, journey_code)
	release_code = (handoff_out or {}).get("handoff_code") or release_code

	record_planning_audit_event(
		event_type="Package Released to Tender Management",
		object_type="Planning Release Package",
		object_code=release_code or package_code,
		from_state=PKG_READY_FOR_RELEASE,
		to_state=PKG_RELEASED,
		evidence_ref=release_code,
		journey_code=journey_code,
		actor=actor_user,
	)
	record_planning_audit_event(
		event_type="Package Locked After Release",
		object_type="Procurement Package",
		object_code=package_code,
		from_state=PKG_READY_FOR_RELEASE,
		to_state=PKG_RELEASED,
		evidence_ref=release_code,
		journey_code=journey_code,
		actor=actor_user,
	)

	return _format_release_response(
		action="created",
		package_code=package_code,
		release_code=release_code,
		readiness_code=readiness_code,
		handoff=handoff_out,
	)
