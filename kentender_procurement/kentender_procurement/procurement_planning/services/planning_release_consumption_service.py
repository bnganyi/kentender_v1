# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Planning release consumption by Tender Management (P2-011)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from kentender_procurement.procurement_lifecycle.demand_module_gate import demand_consumers_live
from frappe import _
from frappe.utils import flt, now_datetime

from kentender_procurement.procurement_lifecycle.handoff_freshness import (
	validate_handoff_card_freshness,
)
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgconsume_code_from_release_code,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_CONSUMED, PKG_RELEASED
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReleaseConsumed,
)
from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope

_BASELINE_FIELDS = (
	"procurement_method",
	"procurement_category",
	"budget_line",
	"estimated_value",
	"currency",
)


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _guard_check(check_id: str, label: str, ok: bool) -> dict[str, Any]:
	return {"id": check_id, "label": label, "ok": bool(ok)}


def _safe_dict(raw: Any) -> dict[str, Any]:
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except json.JSONDecodeError:
			pass
	return {}


def _load_release_handoff(release_code: str) -> dict[str, Any] | None:
	rc = (release_code or "").strip()
	if not rc:
		return None
	if frappe.db.exists("Procurement Handoff Card", rc):
		return frappe.db.get_value(
			"Procurement Handoff Card",
			rc,
			(
				"name",
				"handoff_code",
				"journey_code",
				"source_object_type",
				"source_object_code",
				"locked_summary",
				"target_object_type",
				"target_object_code",
			),
			as_dict=True,
		)
	row = frappe.db.get_value(
		"Procurement Handoff Card",
		{"handoff_code": rc},
		(
			"name",
			"handoff_code",
			"journey_code",
			"source_object_type",
			"source_object_code",
			"locked_summary",
			"target_object_type",
			"target_object_code",
		),
		as_dict=True,
	)
	return row or None


def _package_business_code(pkg_row: dict[str, Any] | None) -> str:
	if not pkg_row:
		return ""
	return (pkg_row.get("package_code") or pkg_row.get("name") or "").strip()


def _find_existing_consumption(release_code: str, tender_code: str) -> str | None:
	code = frappe.db.get_value(
		"Planning Release Consumption Record",
		{
			"release_code": release_code,
			"target_object_code": tender_code,
			"consumption_status": "Consumed",
		},
		"consumption_code",
	)
	return (code or "").strip() or None


def _get_budget_line_code(budget_line_frappe_name: str) -> str:
	if not budget_line_frappe_name:
		return ""
	val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "generated_reference")
	if not val:
		try:
			val = frappe.db.get_value("Budget Line", budget_line_frappe_name, "budget_line_code")
		except Exception:
			val = None
	return str(val or budget_line_frappe_name or "").strip()


def _get_demand_category(demand_frappe_name: str) -> str:
	if not demand_frappe_name or not demand_consumers_live():
		return ""
	val = frappe.db.get_value("Demand", demand_frappe_name, "requisition_type")
	return str(val or "").strip()


def _live_package_baseline(package_code: str) -> dict[str, Any]:
	pkg = frappe.db.get_value(
		"Procurement Package",
		package_code,
		("name", "package_code", "procurement_method", "currency", "estimated_value", "template_id"),
		as_dict=True,
	)
	if not pkg:
		return {}

	procurement_category = ""
	line = frappe.db.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code},
		fields=["demand_id"],
		limit=1,
		order_by="creation asc",
	)
	if line:
		procurement_category = _get_demand_category(str(line[0].get("demand_id") or ""))

	budget_line = ""
	line = frappe.db.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code},
		fields=["budget_line_id"],
		limit=1,
		order_by="creation asc",
	)
	if line:
		budget_line = _get_budget_line_code(str(line[0].get("budget_line_id") or ""))

	return {
		"procurement_method": str(pkg.get("procurement_method") or "").strip(),
		"procurement_category": procurement_category,
		"budget_line": budget_line,
		"estimated_value": flt(pkg.get("estimated_value")),
		"currency": str(pkg.get("currency") or "").strip(),
	}


def _baseline_drift(locked_summary: dict[str, Any], live: dict[str, Any]) -> list[str]:
	changed: list[str] = []
	for field in _BASELINE_FIELDS:
		locked_val = locked_summary.get(field)
		live_val = live.get(field)
		if field == "estimated_value":
			if flt(locked_val) != flt(live_val):
				changed.append(field)
			continue
		if str(locked_val or "").strip() != str(live_val or "").strip():
			if locked_val is not None and str(locked_val).strip():
				changed.append(field)
			elif live_val is not None and str(live_val).strip():
				changed.append(field)
	return changed


def _tender_matches_package(tender_row: dict[str, Any], package_code: str, pkg_row: dict[str, Any]) -> bool:
	business_code = _package_business_code(pkg_row)
	frappe_name = (pkg_row.get("name") or package_code or "").strip()
	tender_pkg_link = str(tender_row.get("procurement_package") or "").strip()
	tender_pkg_code = str(tender_row.get("procurement_package_code") or "").strip()
	source_pkg_code = str(tender_row.get("source_package_code") or "").strip()
	candidates = {c for c in (business_code, frappe_name, package_code) if c}
	if tender_pkg_link and tender_pkg_link in candidates:
		return True
	if tender_pkg_code and tender_pkg_code in candidates:
		return True
	if source_pkg_code and source_pkg_code in candidates:
		return True
	return False


def can_mark_planning_release_consumed(
	release_code: str, tender_code: str, actor: str
) -> dict[str, Any]:
	"""Read-only guard — whether a planning release may be consumed by TM2."""
	blockers: list[dict[str, str]] = []
	checks: list[dict[str, Any]] = []
	release_code = (release_code or "").strip()
	tender_code = (tender_code or "").strip()

	handoff = _load_release_handoff(release_code)
	release_ok = bool(handoff)
	checks.append(_guard_check("release_exists", _("Planning release package exists"), release_ok))
	if not release_ok:
		blockers.append(
			_blocker(
				PackageReleaseConsumed.RELEASE_NOT_FOUND,
				_("Planning release package was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	package_code = str(handoff.get("source_object_code") or "").strip()
	pkg = None
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pkg = frappe.db.get_value(
			"Procurement Package",
			package_code,
			("name", "package_code", "status", "journey_code", "release_code"),
			as_dict=True,
		)
	pkg_ok = bool(pkg)
	checks.append(_guard_check("package_exists", _("Procurement package exists"), pkg_ok))
	if not pkg_ok:
		blockers.append(
			_blocker(
				PackageReleaseConsumed.PACKAGE_NOT_FOUND,
				_("Procurement package for this release was not found."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	status = (pkg.get("status") or "").strip()
	journey_code = str(pkg.get("journey_code") or handoff.get("journey_code") or "").strip()

	if status == PKG_CONSUMED:
		existing = _find_existing_consumption(release_code, tender_code)
		if existing:
			return {
				"allowed": True,
				"blockers": [],
				"checks": checks,
				"idempotent_recall": True,
				"consumption_code": existing,
				"package_code": package_code,
				"release_code": release_code,
				"tender_code": tender_code,
				"journey_code": journey_code,
			}

	state_ok = status == PKG_RELEASED
	checks.append(
		_guard_check("valid_state", _("Package is Released to Tender"), state_ok)
	)
	if not state_ok:
		blockers.append(
			_blocker(
				PackageReleaseConsumed.INVALID_STATE,
				_("Package must be Released to Tender before consumption."),
			)
		)
		return {"allowed": False, "blockers": blockers, "checks": checks}

	freshness: dict[str, Any] = {}
	try:
		freshness = validate_handoff_card_freshness(release_code)
	except ValueError:
		freshness = {"fresh": False, "stale_reason": _("Release handoff card is invalid.")}
	fresh_ok = bool(freshness.get("fresh"))
	checks.append(_guard_check("release_fresh", _("Planning release is not stale"), fresh_ok))
	if not fresh_ok:
		reason = freshness.get("stale_reason") or _("Planning release is stale.")
		blockers.append(
			_blocker(
				PackageReleaseConsumed.RELEASE_STALE,
				str(reason),
			)
		)

	tender_row = None
	if tender_code:
		tender_row = frappe.db.get_value(
			"TM2 Tender",
			{"tender_code": tender_code},
			(
				"name",
				"tender_code",
				"tender_title",
				"procurement_package",
				"procurement_package_code",
				"source_package_code",
			),
			as_dict=True,
		)
	tender_ok = bool(tender_row)
	checks.append(_guard_check("tender_exists", _("TM2 tender exists"), tender_ok))
	if not tender_ok:
		blockers.append(
			_blocker(
				PackageReleaseConsumed.TENDER_NOT_FOUND,
				_("TM2 tender was not found."),
			)
		)

	if tender_row:
		link_ok = _tender_matches_package(tender_row, package_code, pkg)
		checks.append(
			_guard_check(
				"tender_package_link",
				_("TM2 tender is linked to the release package"),
				link_ok,
			)
		)
		if not link_ok:
			blockers.append(
				_blocker(
					PackageReleaseConsumed.TENDER_PACKAGE_MISMATCH,
					_("TM2 tender is not linked to this procurement package."),
				)
			)

	if not blockers:
		locked = _safe_dict(handoff.get("locked_summary"))
		live = _live_package_baseline(package_code)
		drift = _baseline_drift(locked, live)
		baseline_ok = not drift
		checks.append(
			_guard_check(
				"baseline_preserved",
				_("Planning baseline matches locked release summary"),
				baseline_ok,
			)
		)
		if not baseline_ok:
			blockers.append(
				_blocker(
					PackageReleaseConsumed.BASELINE_MISMATCH,
					_("Planning baseline changed since release: {0}.").format(
						", ".join(drift)
					),
				)
			)

	return {
		"allowed": not blockers,
		"blockers": blockers,
		"checks": checks,
		"from_state": PKG_RELEASED,
		"to_state": PKG_CONSUMED,
		"release_code": release_code,
		"tender_code": tender_code,
		"package_code": package_code,
		"journey_code": journey_code,
	}


def _assert_can_consume_or_throw(release_code: str, tender_code: str, actor: str) -> dict[str, Any]:
	guard = can_mark_planning_release_consumed(release_code, tender_code, actor)
	if guard.get("allowed"):
		return guard
	blockers = guard.get("blockers") or []
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or _("Planning release cannot be consumed."),
		title=first.get("code") or PackageReleaseConsumed.RELEASE_NOT_FOUND,
		exc=frappe.ValidationError,
	)


def _transition_package_to_consumed(package_code: str, *, tender_code: str) -> None:
	try:
		frappe.local.pp_allow_package_consumed = True
		doc = frappe.get_doc("Procurement Package", package_code)
		doc.status = PKG_CONSUMED
		doc.tender_code = tender_code
		doc.save(ignore_permissions=True)
	finally:
		if hasattr(frappe.local, "pp_allow_package_consumed"):
			delattr(frappe.local, "pp_allow_package_consumed")


def _update_release_handoff_consumed(
	handoff_name: str, *, tender_code: str, actor_user: str
) -> None:
	now = now_datetime()
	frappe.db.set_value(
		"Procurement Handoff Card",
		handoff_name,
		{
			"target_object_type": "TM2 Tender",
			"target_object_code": tender_code,
			"consumed_by": actor_user,
			"consumed_at": now,
		},
		update_modified=True,
	)


def _format_consume_response(
	*,
	action: str,
	release_code: str,
	tender_code: str,
	package_code: str,
	consumption_code: str | None,
) -> dict[str, Any]:
	return {
		"ok": True,
		"action": action,
		"release_code": release_code,
		"tender_code": tender_code,
		"package_code": package_code,
		"consumption_code": consumption_code,
		"from_state": PKG_RELEASED,
		"to_state": PKG_CONSUMED,
		"status": PKG_CONSUMED,
	}


def mark_planning_release_consumed(
	release_code: str, tender_code: str, actor: str
) -> dict[str, Any]:
	"""Record Tender Management consumption of a planning release package."""
	release_code = (release_code or "").strip()
	tender_code = (tender_code or "").strip()
	actor_user = (actor or frappe.session.user or "Administrator").strip()

	guard = can_mark_planning_release_consumed(release_code, tender_code, actor_user)
	if guard.get("idempotent_recall"):
		return _format_consume_response(
			action="recalled",
			release_code=release_code,
			tender_code=tender_code,
			package_code=guard.get("package_code") or "",
			consumption_code=guard.get("consumption_code"),
		)

	guard = _assert_can_consume_or_throw(release_code, tender_code, actor_user)
	package_code = guard.get("package_code") or ""
	if package_code and frappe.db.exists("Procurement Package", package_code):
		pp_policy.assert_may_mark_planning_release_consumed(
			frappe.get_doc("Procurement Package", package_code)
		)
		pp_scope.assert_may_act_on_procurement_package(package_code)
	else:
		pp_policy.assert_may_consume_planning_release()
	journey_code = guard.get("journey_code") or ""

	handoff = _load_release_handoff(release_code) or {}
	handoff_name = handoff.get("name") or release_code
	tender_row = frappe.db.get_value(
		"TM2 Tender",
		{"tender_code": tender_code},
		("tender_title",),
		as_dict=True,
	) or {}

	consumption_code = pkgconsume_code_from_release_code(release_code)
	if frappe.db.exists("Planning Release Consumption Record", consumption_code):
		consumption_code = f"{consumption_code}-{frappe.generate_hash(length=4).upper()}"

	consumption_result = {
		"tender_code": tender_code,
		"tender_title": str(tender_row.get("tender_title") or "").strip(),
		"created_from_release": release_code,
		"planning_baseline_preserved": True,
		"changed_values": [],
	}

	consumed_at = now_datetime()
	cons_doc = frappe.get_doc(
		{
			"doctype": "Planning Release Consumption Record",
			"consumption_code": consumption_code,
			"release_code": release_code,
			"package_code": package_code,
			"consumed_by_module": "Tender Management",
			"consumed_by": actor_user,
			"consumed_at": consumed_at,
			"target_object_type": "TM2 Tender",
			"target_object_code": tender_code,
			"consumption_status": "Consumed",
			"consumption_result_json": json.dumps(consumption_result),
		}
	)
	cons_doc.insert(ignore_permissions=True)

	_update_release_handoff_consumed(
		handoff_name, tender_code=tender_code, actor_user=actor_user
	)
	_transition_package_to_consumed(package_code, tender_code=tender_code)

	audit_code = record_planning_audit_event(
		event_type="Release Consumed by Tender Management",
		object_type="Planning Release Consumption Record",
		object_code=consumption_code,
		from_state=PKG_RELEASED,
		to_state=PKG_CONSUMED,
		evidence_ref=tender_code,
		journey_code=journey_code,
		actor=actor_user,
	)
	if audit_code:
		frappe.db.set_value(
			"Planning Release Consumption Record",
			consumption_code,
			"audit_event_ref",
			audit_code,
			update_modified=False,
		)

	return _format_consume_response(
		action="created",
		release_code=release_code,
		tender_code=tender_code,
		package_code=package_code,
		consumption_code=consumption_code,
	)
