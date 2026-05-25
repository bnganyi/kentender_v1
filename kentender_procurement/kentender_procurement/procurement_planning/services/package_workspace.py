# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-006 — Package workspace read context (PP2 UI §13 / PRD §13.6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.api.package_detail import _actions_for_workbench
from kentender_procurement.procurement_planning.services.planning_journey_integration import (
	build_planning_journey_block,
)
from kentender_procurement.procurement_planning.services.package_release_api import (
	format_package_release_tab,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import READINESS_NOT_RUN, pkg_workbench_group
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_budget_line_ref,
)
from kentender_procurement.procurement_planning.services.package_completeness import (
	get_package_completeness_blockers,
)
from kentender_procurement.procurement_planning.services.package_lines import (
	format_package_line_rows,
)
from kentender_procurement.procurement_planning.services.package_method import (
	format_package_method_tab,
)
from kentender_procurement.procurement_planning.services.package_readiness_api import (
	format_package_readiness_tab,
)
from kentender_procurement.procurement_planning.services.package_review_api import (
	format_package_review_tab,
)
from kentender_procurement.procurement_planning.services.package_workbench import (
	_tender_ref,
	derive_package_next_action,
)
from kentender_procurement.procurement_planning.services.planning_evidence_api import (
	fetch_planning_evidence_events_for_package,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)

_EVIDENCE_LIMIT = 10


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _resolve_package_name(package_code: str) -> str | None:
	code = (package_code or "").strip()
	if not code:
		return None
	if frappe.db.exists("Procurement Package", code):
		return code
	name = frappe.db.get_value("Procurement Package", {"package_code": code}, "name")
	return str(name) if name else None


def _plan_ref(plan_id: str | None) -> dict[str, str]:
	plan_name = (plan_id or "").strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"id": "", "code": "", "name": ""}
	row = frappe.db.get_value(
		"Procurement Plan",
		plan_name,
		("name", "plan_code", "plan_name"),
		as_dict=True,
	) or {}
	return {
		"id": row.get("name") or "",
		"code": (row.get("plan_code") or row.get("name") or "").strip(),
		"name": (row.get("plan_name") or row.get("plan_code") or "").strip(),
	}


def _inclusion_ref(inclusion_code: str | None) -> dict[str, str]:
	code = (inclusion_code or "").strip()
	if not code:
		return {"id": "", "code": "", "name": ""}
	inclusion = get_planning_inclusion(code)
	if inclusion:
		return {
			"id": code,
			"code": code,
			"name": code,
		}
	if frappe.db.exists("Procurement Handoff Card", code):
		title = frappe.db.get_value("Procurement Handoff Card", code, "handoff_title") or code
		return {"id": code, "code": code, "name": str(title).strip()}
	return {"id": "", "code": code, "name": code}


def _demand_ref(demand_key: str | None) -> dict[str, str]:
	key = (demand_key or "").strip()
	if not key:
		return {"id": "", "code": "", "name": ""}
	if frappe.db.exists("Demand", key):
		row = frappe.db.get_value(
			"Demand",
			key,
			("name", "demand_id", "title"),
			as_dict=True,
		) or {}
		return {
			"id": row.get("name") or "",
			"code": (row.get("demand_id") or row.get("name") or "").strip(),
			"name": (row.get("title") or row.get("demand_id") or "").strip(),
		}
	row = frappe.db.get_value(
		"Demand",
		{"demand_id": key},
		("name", "demand_id", "title"),
		as_dict=True,
	)
	if not row:
		return {"id": "", "code": key, "name": key}
	return {
		"id": row.get("name") or "",
		"code": (row.get("demand_id") or row.get("name") or "").strip(),
		"name": (row.get("title") or row.get("demand_id") or "").strip(),
	}


def _demand_context(demand_key: str | None) -> dict[str, Any]:
	ref = _demand_ref(demand_key)
	if not ref.get("id") and not ref.get("code"):
		return {"demand": ref, "department": "", "status": ""}
	demand_name = ref.get("id") or ref.get("code")
	row = frappe.db.get_value(
		"Demand",
		demand_name if ref.get("id") else {"demand_id": ref.get("code")},
		("requesting_department", "status"),
		as_dict=True,
	) or {}
	return {
		"demand": ref,
		"department": (row.get("requesting_department") or "").strip(),
		"status": (row.get("status") or "").strip(),
	}


def _format_lines(doc) -> list[dict[str, Any]]:
	return format_package_line_rows(doc)


def _recent_evidence_events(
	package_code: str,
	actor: str,
	*,
	limit: int = _EVIDENCE_LIMIT,
) -> list[dict[str, Any]]:
	events = fetch_planning_evidence_events_for_package(package_code, actor, limit=limit)
	return list(reversed(events)) if events else []


def _method_tab(doc, package_code: str) -> dict[str, Any]:
	return format_package_method_tab(doc, package_code)


def _readiness_tab(doc, package_code: str) -> dict[str, Any]:
	return format_package_readiness_tab(doc, package_code)


def _right_panel_blockers(doc, readiness: dict[str, Any]) -> list[str]:
	blockers = [str(x) for x in get_package_completeness_blockers(doc) if str(x).strip()]
	current = readiness.get("current_result") or {}
	if isinstance(current, dict):
		fail_count = cint(current.get("blocking_failure_count"))
		if fail_count > 0:
			blockers.append(f"{fail_count} readiness check(s) failed.")
	return blockers


def get_package_workspace_context(package_code: str, actor: str) -> dict[str, Any]:
	"""Return tab-oriented workspace context for a procurement package."""
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
	plan_status = frappe.db.get_value("Procurement Plan", doc.plan_id, "status") or ""
	journey = build_planning_journey_block(doc, business_code) if business_code else None

	release = format_package_release_tab(doc, business_code).get("release") if business_code else None
	release_hint = None
	if release:
		release_hint = {
			"handoff_code": release.get("handoff_code"),
			"status": release.get("status"),
			"tender_code": release.get("tender_code"),
			"tender_title": release.get("tender_title"),
		}

	inclusion_code = (doc.planning_inclusion_code or "").strip()
	inclusion = get_planning_inclusion(inclusion_code) if inclusion_code else None
	demand_key = doc.demand_id or (inclusion or {}).get("demand_code")
	demand_ctx = _demand_context(demand_key)
	budget_line = _budget_line_ref(doc.budget_line_id)
	readiness_tab = _readiness_tab(doc, business_code)
	review = format_package_review_tab(doc, business_code).get("latest_review")
	evidence_events = _recent_evidence_events(business_code, actor)
	actions = _actions_for_workbench(doc.status or "", role_key, plan_status=plan_status)
	next_action = derive_package_next_action(
		doc.status or "",
		role_key,
		plan_status=plan_status,
		handoff=release_hint,
	)
	last_event = evidence_events[0] if evidence_events else None

	header = {
		"package": {
			"id": doc.name,
			"code": business_code,
			"name": (doc.package_name or business_code).strip(),
		},
		"status": (doc.status or "").strip(),
		"workbench_group": pkg_workbench_group(doc.status),
		"method": (doc.procurement_method or "").strip(),
		"category": (doc.procurement_category or "").strip(),
		"estimated_value": flt(doc.estimated_value),
		"currency": (doc.currency or "KES").strip() or "KES",
		"plan": _plan_ref(doc.plan_id),
		"planning_inclusion": _inclusion_ref(inclusion_code),
		"budget_line": budget_line,
		"tender": _tender_ref(doc.tender_code, handoff=release_hint),
		"locked_after_release": bool(cint(doc.locked_after_release)),
	}

	return {
		"ok": True,
		"role_key": role_key,
		"header": header,
		"journey": journey,
		"right_panel": {
			"current_state": (doc.status or "").strip(),
			"next_action": next_action,
			"blockers": _right_panel_blockers(doc, readiness_tab),
			"last_evidence_event": last_event,
			"actions": actions,
		},
		"tabs": {
			"overview": {
				"business_readiness": readiness_tab.get("business_readiness"),
				"locked_after_release": bool(cint(doc.locked_after_release)),
				"planning_inclusion_code": inclusion_code,
				"release_code": (doc.release_code or "").strip(),
				"journey_code": (doc.journey_code or "").strip(),
			},
			"source_demand": {
				**demand_ctx,
				"planning_inclusion": inclusion,
			},
			"budget": {
				"budget_line": budget_line,
				"planning_inclusion": inclusion,
				"estimated_value": flt(doc.estimated_value),
				"currency": (doc.currency or "KES").strip() or "KES",
			},
			"lines": _format_lines(doc),
			"method": _method_tab(doc, business_code),
			"readiness": readiness_tab,
			"review": review,
			"release": release,
			"evidence": {
				"recent_events": evidence_events,
				"total_recent": len(evidence_events),
			},
			"advanced": {
				"journey_code": (doc.journey_code or "").strip(),
				"release_code": (doc.release_code or "").strip(),
				"tender_code": (doc.tender_code or "").strip(),
				"latest_readiness_code": (doc.latest_readiness_code or "").strip(),
				"latest_review_code": (doc.latest_review_code or "").strip(),
				"planning_inclusion_code": inclusion_code,
				"locked_after_release": bool(cint(doc.locked_after_release)),
			},
		},
	}
