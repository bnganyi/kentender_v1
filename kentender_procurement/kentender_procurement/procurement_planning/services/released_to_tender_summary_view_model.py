# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-003+ — Released package follow-up summary view-model."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
	summarize_planning_release_handoff_for_package_detail,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import PKG_CONSUMED, PKG_RELEASED
from kentender_procurement.procurement_planning.services.package_workbench import (
	_tender_ref,
	derive_package_next_action,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _status_label(*, package_status: str, tender_code: str, consumption_status: str) -> str:
	if tender_code or consumption_status == "Consumed":
		return "Tender created"
	if package_status in (PKG_RELEASED, PKG_CONSUMED):
		return "Released"
	return "Released"


def _next_action_label(*, tender_code: str, next_action: dict[str, Any]) -> str:
	if tender_code:
		return "Continue in Tender"
	label = str((next_action or {}).get("label") or "").strip()
	return label or "View release follow-up."


def get_released_package_summary(package_code: str, actor: str) -> dict[str, Any]:
	"""Return business summary for Released to Tender follow-up panel."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	code = (package_code or "").strip()
	if not code:
		return _fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	pkg_name = frappe.db.get_value("Procurement Package", {"package_code": code}, "name")
	if not pkg_name and frappe.db.exists("Procurement Package", code):
		pkg_name = code
	if not pkg_name:
		return _fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.DoesNotExistError:
		return _fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this release.",
			role_key=role_key,
		)

	package_status = (doc.status or "").strip()
	if package_status not in (PKG_RELEASED, PKG_CONSUMED):
		return _fail(code="NOT_RELEASED", message="Package is not released.", role_key=role_key)

	business_code = (doc.package_code or doc.name or "").strip()
	journey_code = (doc.journey_code or "").strip()
	release_code = (doc.release_code or "").strip() or pkgrel_handoff_code_from_journey_code(journey_code)
	release_display = summarize_planning_release_handoff_for_package_detail(business_code) or {}
	tender_code = (doc.tender_code or "").strip() or str(release_display.get("tender_code") or "").strip()
	tender = _tender_ref(tender_code, handoff=release_display)
	tender_open_route = str(release_display.get("tender_open_route") or "").strip()
	consumption_status = ""
	if release_code and frappe.db.exists("DocType", "Planning Release Consumption Record"):
		consumption_status = (
			frappe.db.get_value(
				"Planning Release Consumption Record",
				{"release_code": release_code},
				"consumption_status",
			)
			or ""
		).strip()

	next_action = derive_package_next_action(
		package_status,
		role_key,
		handoff={"status": str(release_display.get("status") or ""), "tender_code": tender_code},
	)

	return {
		"ok": True,
		"role_key": role_key,
		"headline": "Released to Tender Management",
		"status_label": _status_label(
			package_status=package_status,
			tender_code=tender_code,
			consumption_status=consumption_status,
		),
		"next_action_label": _next_action_label(tender_code=tender_code, next_action=next_action),
		"package": {
			"id": doc.name,
			"code": business_code,
			"name": (doc.package_name or business_code).strip(),
			"open_route": f"/desk/procurement-planning/packages/{business_code}",
		},
		"tender": {
			**tender,
			"open_route": tender_open_route,
		},
		"may_open_tender": bool(tender_open_route),
		"may_open_package": True,
		"may_view_evidence": True,
	}
