# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Planning correction and supersession (P2-013)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.data import parse_json

from kentender_procurement.procurement_planning.pp2_constants import (
	CORRECTION_DECISION_APPLIED,
	CORRECTION_REPLACEMENT_VALID_STATUSES,
	CORRECTION_TYPE_POST_RELEASE,
	CORRECTION_TYPE_SUPERSESSION,
	CORRECTION_VALID_TYPES,
	PKG_CONSUMED,
	PKG_RELEASED,
	PKG_RETURNED,
	PKG_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackagePlanningCorrection,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

_POST_RELEASE_CORRECTION_STATUSES = frozenset((PKG_RELEASED, PKG_CONSUMED))


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _guard_check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _correction_code(package_code: str) -> str:
	count = frappe.db.count(
		"Planning Correction Supersession Record", {"package_code": package_code}
	)
	return f"PKGCORR-{package_code}-{count + 1:03d}"


def _normalize_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
	raw = payload or {}
	correction_type = (raw.get("correction_type") or CORRECTION_TYPE_POST_RELEASE).strip()
	reason = (raw.get("reason") or "").strip()
	release_code = (raw.get("release_code") or "").strip()
	replacement = (raw.get("replacement_package_code") or "").strip()
	affected_raw = raw.get("affected_fields_json")
	if affected_raw in (None, ""):
		affected_raw = raw.get("affected_fields")
	if isinstance(affected_raw, str):
		try:
			affected = parse_json(affected_raw)
		except Exception:
			affected = affected_raw
	else:
		affected = affected_raw
	if isinstance(affected, (dict, list)) and affected:
		affected_json = json.dumps(affected)
	else:
		affected_json = ""
	return {
		"correction_type": correction_type,
		"reason": reason,
		"release_code": release_code,
		"replacement_package_code": replacement,
		"affected_fields_json": affected_json,
		"affected_fields": affected,
	}


def _affected_fields_ok(affected: Any) -> bool:
	if isinstance(affected, dict):
		return bool(affected)
	if isinstance(affected, list):
		return bool(affected)
	return bool(affected)


def _load_release_handoff(release_code: str) -> dict[str, Any] | None:
	rc = (release_code or "").strip()
	if not rc:
		return None
	if frappe.db.exists("Procurement Handoff Card", rc):
		return frappe.db.get_value(
			"Procurement Handoff Card",
			rc,
			("name", "handoff_code", "status"),
			as_dict=True,
		)
	return frappe.db.get_value(
		"Procurement Handoff Card",
		{"handoff_code": rc},
		("name", "handoff_code", "status"),
		as_dict=True,
	)


def can_create_planning_correction_or_supersession(
	package_code: str, payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	"""Read-only guard — whether a correction/supersession may be recorded."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	normalized = _normalize_payload(payload)
	package_code = (package_code or "").strip()

	pkg = None
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pkg = frappe.db.get_value(
			"Procurement Package",
			package_code,
			("name", "status", "release_code", "journey_code"),
			as_dict=True,
		)
	pkg_ok = bool(pkg)
	checks.append(_guard_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackagePlanningCorrection.PACKAGE_NOT_FOUND,
				_("Procurement package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	status = (pkg.get("status") or "").strip()
	state_ok = status in _POST_RELEASE_CORRECTION_STATUSES
	checks.append(
		_guard_check(
			"package_post_release_state",
			_("Package is released or consumed"),
			state_ok,
		)
	)
	if not state_ok:
		blockers.append(
			_blocker(
				PackagePlanningCorrection.INVALID_STATE,
				_("Correction or supersession is only allowed for released or consumed packages."),
			)
		)

	correction_type = normalized.get("correction_type") or ""
	type_ok = correction_type in CORRECTION_VALID_TYPES
	checks.append(_guard_check("correction_type_valid", _("Correction type is valid"), type_ok))
	if not type_ok:
		blockers.append(
			_blocker(
				PackagePlanningCorrection.INVALID_CORRECTION_TYPE,
				_("Correction type must be Post-Release Correction or Supersession."),
			)
		)

	reason_ok = bool(normalized.get("reason"))
	checks.append(_guard_check("reason_present", _("Reason is provided"), reason_ok))
	if not reason_ok:
		blockers.append(
			_blocker(
				PackagePlanningCorrection.REASON_REQUIRED,
				_("A business reason is required for this correction or supersession."),
			)
		)

	affected_ok = _affected_fields_ok(normalized.get("affected_fields"))
	checks.append(
		_guard_check("affected_fields_present", _("Affected fields are provided"), affected_ok)
	)
	if not affected_ok:
		blockers.append(
			_blocker(
				PackagePlanningCorrection.AFFECTED_FIELDS_REQUIRED,
				_("Affected fields must describe at least one impacted baseline field."),
			)
		)

	release_code = normalized.get("release_code") or (pkg.get("release_code") or "").strip()
	release_ok = bool(release_code)
	checks.append(_guard_check("release_code_present", _("Release code is present"), release_ok))
	if not release_ok:
		blockers.append(
			_blocker(
				PackagePlanningCorrection.RELEASE_CODE_REQUIRED,
				_("Release code is required for post-release corrections."),
			)
		)

	if correction_type == CORRECTION_TYPE_SUPERSESSION:
		replacement = normalized.get("replacement_package_code") or ""
		replacement_ok = bool(replacement) and replacement != package_code
		checks.append(
			_guard_check(
				"replacement_package_present",
				_("Replacement package code is provided"),
				replacement_ok,
			)
		)
		if not replacement_ok:
			blockers.append(
				_blocker(
					PackagePlanningCorrection.REPLACEMENT_REQUIRED,
					_("Supersession requires a distinct replacement package code."),
				)
			)
		elif not frappe.db.exists("Procurement Package", replacement):
			blockers.append(
				_blocker(
					PackagePlanningCorrection.REPLACEMENT_INVALID,
					_("Replacement package was not found."),
				)
			)
		else:
			repl_status = frappe.db.get_value("Procurement Package", replacement, "status")
			repl_ok = (repl_status or "").strip() in CORRECTION_REPLACEMENT_VALID_STATUSES
			checks.append(
				_guard_check(
					"replacement_package_state",
					_("Replacement package is in a valid pre-release state"),
					repl_ok,
				)
			)
			if not repl_ok:
				blockers.append(
					_blocker(
						PackagePlanningCorrection.REPLACEMENT_INVALID,
						_(
							"Replacement package must be Draft, Returned for Correction, "
							"In Review, or Approved."
						),
					)
				)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"normalized_payload": normalized,
		"package_code": package_code,
		"from_state": status,
		"release_code": release_code,
		"journey_code": pkg.get("journey_code") if pkg else "",
	}


def _assert_can_create_or_throw(
	package_code: str, payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	guard = can_create_planning_correction_or_supersession(package_code, payload, actor)
	if guard.get("allowed"):
		return guard
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	code = first.get("code") or PackagePlanningCorrection.PACKAGE_NOT_FOUND
	message = first.get("message") or _("Correction or supersession cannot be recorded.")
	frappe.throw(f"{code}: {message}", title=code, exc=frappe.ValidationError)


def _update_release_handoff_returned(handoff_name: str, *, reason: str) -> None:
	frappe.db.set_value(
		"Procurement Handoff Card",
		handoff_name,
		{
			"status": "Returned",
			"next_action": reason[:500] if reason else _("Returned for governed correction."),
		},
		update_modified=True,
	)


def _transition_package_post_release_correction(
	package_code: str, *, reason: str
) -> None:
	try:
		frappe.local.pp_allow_package_post_release_correction = True
		doc = frappe.get_doc("Procurement Package", package_code)
		doc.status = PKG_RETURNED
		doc.workflow_reason = reason
		doc.save(ignore_permissions=True)
	finally:
		if hasattr(frappe.local, "pp_allow_package_post_release_correction"):
			delattr(frappe.local, "pp_allow_package_post_release_correction")


def _transition_package_superseded(package_code: str, *, reason: str) -> None:
	try:
		frappe.local.pp_allow_package_supersede = True
		doc = frappe.get_doc("Procurement Package", package_code)
		doc.status = PKG_SUPERSEDED
		doc.workflow_reason = reason
		doc.save(ignore_permissions=True)
	finally:
		if hasattr(frappe.local, "pp_allow_package_supersede"):
			delattr(frappe.local, "pp_allow_package_supersede")


def _format_response(
	*,
	action: str,
	correction_code: str,
	package_code: str,
	correction_type: str,
	from_state: str,
	to_state: str,
) -> dict[str, Any]:
	return {
		"ok": True,
		"action": action,
		"correction_code": correction_code,
		"package_code": package_code,
		"correction_type": correction_type,
		"from_state": from_state,
		"to_state": to_state,
		"status": to_state,
	}


def create_planning_correction_or_supersession(
	package_code: str, payload: dict[str, Any], actor: str
) -> dict[str, Any]:
	"""Create a governed correction or supersession record and apply the package transition."""
	package_code = (package_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()

	guard = _assert_can_create_or_throw(package_code, payload, actor_user)
	if frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_create_planning_correction(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)
	normalized = guard.get("normalized_payload") or _normalize_payload(payload)
	correction_type = normalized.get("correction_type") or CORRECTION_TYPE_POST_RELEASE
	from_state = guard.get("from_state") or ""
	release_code = guard.get("release_code") or ""
	journey_code = guard.get("journey_code") or ""
	reason = normalized.get("reason") or ""

	if correction_type == CORRECTION_TYPE_POST_RELEASE:
		to_state = PKG_RETURNED
	elif correction_type == CORRECTION_TYPE_SUPERSESSION:
		to_state = PKG_SUPERSEDED
	else:
		frappe.throw(
			_("Correction type must be Post-Release Correction or Supersession."),
			title=PackagePlanningCorrection.INVALID_CORRECTION_TYPE,
			exc=frappe.ValidationError,
		)

	code = _correction_code(package_code)
	corr_doc = frappe.get_doc(
		{
			"doctype": "Planning Correction Supersession Record",
			"correction_code": code,
			"package_code": package_code,
			"release_code": release_code,
			"correction_type": correction_type,
			"requested_by": actor_user,
			"requested_at": now_datetime(),
			"reason": reason,
			"affected_fields_json": normalized.get("affected_fields_json"),
			"from_state": from_state,
			"proposed_next_state": to_state,
			"requires_re_readiness": 1,
			"requires_re_release": 1,
			"decision_status": CORRECTION_DECISION_APPLIED,
			"decided_by": actor_user,
			"decided_at": now_datetime(),
		}
	)
	if correction_type == CORRECTION_TYPE_SUPERSESSION:
		replacement = normalized.get("replacement_package_code") or ""
		corr_doc.supersedes_package_code = package_code
		corr_doc.superseded_by_package_code = replacement
	corr_doc.insert(ignore_permissions=True)

	if correction_type == CORRECTION_TYPE_POST_RELEASE:
		_transition_package_post_release_correction(package_code, reason=reason)
		handoff = _load_release_handoff(release_code)
		if handoff and handoff.get("name"):
			_update_release_handoff_returned(handoff["name"], reason=reason)
		event_type = "Returned for Correction"
	elif correction_type == CORRECTION_TYPE_SUPERSESSION:
		_transition_package_superseded(package_code, reason=reason)
		event_type = "Package Superseded"
	else:
		event_type = "Planning Correction Recorded"

	audit_code = record_planning_audit_event(
		event_type=event_type,
		object_type="Planning Correction Supersession Record",
		object_code=code,
		from_state=from_state,
		to_state=to_state,
		reason=reason,
		evidence_ref=release_code or package_code,
		journey_code=journey_code or None,
		actor=actor_user,
	)
	if audit_code:
		frappe.db.set_value(
			"Planning Correction Supersession Record",
			code,
			"audit_event_ref",
			audit_code,
			update_modified=False,
		)

	return _format_response(
		action="created",
		correction_code=code,
		package_code=package_code,
		correction_type=correction_type,
		from_state=from_state,
		to_state=to_state,
	)
