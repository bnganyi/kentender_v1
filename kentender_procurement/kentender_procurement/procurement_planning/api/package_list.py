# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning workbench — package list (Phase D2)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.api.landing import (
	_can_read_planning,
	_high_risk_profile_names,
	_resolve_current_plan,
	resolve_pp_role_key,
)

_ALLOWED_QUEUE_IDS: frozenset[str] = frozenset(
	(
		"all_packages",
		"draft_packages",
		"structured_packages",
		"submitted_packages",
		"high_risk_packages",
		"emergency_packages",
		"pending_approval",
		"high_risk_escalation",
		"method_override",
		"ready_for_tender",
		"approved_not_handed_off",
	)
)


def _fail_list(*, code: str, message: str, role_key: str = "auditor") -> dict:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"rows": [],
		"queue_id": None,
		"plan": None,
	}


def _base_filters(plan_id: str) -> dict:
	return {"plan_id": plan_id, "is_active": 1}


def _high_risk_filter() -> dict:
	names = _high_risk_profile_names()
	if names:
		return {"risk_profile_id": ("in", names)}
	return {"name": ("=", "__none__")}


def _queue_filters(queue_id: str, *, plan_id: str) -> dict:
	"""Build ``Procurement Package`` filters aligned with ``landing.py`` KPI semantics."""
	b = _base_filters(plan_id)
	if queue_id == "all_packages":
		return b
	if queue_id == "draft_packages":
		return {**b, "status": "Draft"}
	if queue_id == "structured_packages":
		return {**b, "status": "Completed"}
	if queue_id in ("submitted_packages", "pending_approval"):
		return {**b, "status": "Submitted"}
	if queue_id == "high_risk_packages":
		return {**b, **_high_risk_filter()}
	if queue_id == "emergency_packages":
		return {**b, "is_emergency": 1}
	if queue_id == "high_risk_escalation":
		hr = _high_risk_filter()
		return {**b, "status": "Submitted", **hr}
	if queue_id == "method_override":
		return {
			**b,
			"method_override_flag": 1,
			"status": ("in", ("Draft", "Completed", "Returned", "Submitted", "Approved")),
		}
	if queue_id == "ready_for_tender":
		return {**b, "status": "Ready for Tender"}
	if queue_id == "approved_not_handed_off":
		return {**b, "status": "Approved"}
	return {**b, "name": ("=", "__none__")}


def _risk_levels_for(ids: list[str]) -> dict[str, str]:
	if not ids:
		return {}
	rows = frappe.get_all("Risk Profile", filters={"name": ("in", ids)}, fields=["name", "risk_level"], limit=500)
	return {r.name: (r.risk_level or "") for r in rows}


def _template_names_for(ids: list[str]) -> dict[str, str]:
	if not ids:
		return {}
	rows = frappe.get_all(
		"Procurement Template",
		filters={"name": ("in", ids)},
		fields=["name", "template_name"],
		limit=500,
	)
	return {r.name: (r.template_name or r.name) for r in rows}


def _row_dict(
	pkg: dict,
	*,
	template_labels: dict[str, str],
	risk_levels: dict[str, str],
) -> dict:
	rid = pkg.get("risk_profile_id")
	high = bool(rid and risk_levels.get(str(rid)) == "High")
	st = str(pkg.get("status") or "")
	return {
		"name": pkg.get("name"),
		"package_code": pkg.get("package_code") or "",
		"package_name": pkg.get("package_name") or "",
		"procurement_method": pkg.get("procurement_method") or "",
		"estimated_value": flt(pkg.get("estimated_value")),
		"currency": (pkg.get("currency") or "KES").strip() or "KES",
		"template_name": template_labels.get(pkg.get("template_id") or "", "") or "",
		"badges": {
			"high_risk": high,
			"emergency": cint(pkg.get("is_emergency")),
			"submitted": st == "Submitted",
			"ready": st == "Ready for Tender",
		},
	}


@frappe.whitelist()
def get_pp_package_list(plan: str | None = None, queue_id: str | None = None, limit: int | None = None) -> dict:
	"""Return packages for the workbench list (current plan + queue)."""
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _fail_list(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)

	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return _fail_list(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to the Procurement Planning workbench."),
			role_key=role_key or "auditor",
		)

	qid = (queue_id or "").strip()
	if not qid or qid not in _ALLOWED_QUEUE_IDS:
		return _fail_list(
			code="INVALID_QUEUE",
			message=_("Unknown or missing queue."),
			role_key=role_key,
		)

	lim = cint(limit) or 100
	if lim < 1:
		lim = 1
	if lim > 500:
		lim = 500

	plan_doc, _plans = _resolve_current_plan(plan)
	if not plan_doc:
		return {
			"ok": True,
			"rows": [],
			"queue_id": qid,
			"plan": None,
			"role_key": role_key,
			"message": _("Select or create a procurement plan to load packages."),
		}

	plan_name = plan_doc.name
	filters = _queue_filters(qid, plan_id=plan_name)

	fields = [
		"name",
		"package_code",
		"package_name",
		"procurement_method",
		"estimated_value",
		"currency",
		"template_id",
		"risk_profile_id",
		"is_emergency",
		"status",
	]
	try:
		pkgs = frappe.get_list(
			"Procurement Package",
			filters=filters,
			fields=fields,
			order_by="modified desc",
			limit_page_length=lim,
		)
	except frappe.PermissionError:
		return _fail_list(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to read procurement packages for this plan."),
			role_key=role_key,
		)

	tpl_ids = [p.get("template_id") for p in pkgs if p.get("template_id")]
	risk_ids = [p.get("risk_profile_id") for p in pkgs if p.get("risk_profile_id")]
	tpl_map = _template_names_for(list({str(x) for x in tpl_ids if x}))
	risk_map = _risk_levels_for(list({str(x) for x in risk_ids if x}))

	rows = [_row_dict(p, template_labels=tpl_map, risk_levels=risk_map) for p in pkgs]

	return {
		"ok": True,
		"rows": rows,
		"queue_id": qid,
		"plan": {"name": plan_name, "plan_code": plan_doc.plan_code, "plan_name": plan_doc.plan_name},
		"role_key": role_key,
	}
