# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning workbench — package detail (Phase D3)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.api.landing import (
	_can_read_planning,
	resolve_pp_role_key,
)
from kentender_procurement.procurement_planning.api.package_list import _template_names_for


def _fail(
	*,
	code: str,
	message: str,
	role_key: str = "auditor",
) -> dict:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _as_list(raw: Any, *, max_items: int) -> list:
	if raw is None:
		return []
	if isinstance(raw, str):
		text = raw.strip()
		if not text:
			return []
		try:
			parsed = json.loads(text)
		except Exception:
			return []
		raw = parsed
	if not isinstance(raw, list):
		return []
	return raw[:max_items]


def _normalize_metrics(items: list) -> list[str]:
	out: list[str] = []
	for x in items:
		if isinstance(x, str) and x.strip():
			out.append(x.strip())
		elif isinstance(x, dict):
			label = str(x.get("label") or x.get("name") or x.get("metric") or "").strip()
			if label:
				out.append(label)
		if len(out) >= 30:
			break
	return out


def _normalize_risks(items: list) -> list[dict[str, str]]:
	out: list[dict[str, str]] = []
	for x in items:
		if not isinstance(x, dict):
			continue
		risk = str(x.get("risk") or "").strip()
		mit = str(x.get("mitigation") or "").strip()
		if risk or mit:
			out.append({"risk": risk, "mitigation": mit})
		if len(out) >= 12:
			break
	return out


def _normalize_criteria(items: list) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for x in items:
		if not isinstance(x, dict):
			continue
		crit = str(x.get("criterion") or x.get("name") or "").strip()
		if not crit:
			continue
		w = x.get("weight")
		try:
			weight = flt(w)
		except Exception:
			weight = None
		out.append({"criterion": crit, "weight": weight})
		if len(out) >= 20:
			break
	return out


def _flatten_json_obj(obj: Any, *, max_lines: int) -> list[str]:
	if not isinstance(obj, dict):
		return []
	lines: list[str] = []
	for k, v in list(obj.items())[:max_lines]:
		key = str(k).strip()
		if not key:
			continue
		if isinstance(v, (dict, list)):
			val = json.dumps(v, ensure_ascii=False)[:200]
		else:
			val = str(v).strip()[:200]
		lines.append(f"{key}: {val}")
		if len(lines) >= max_lines:
			break
	return lines


def _badges_for_pkg(pkg: dict, *, risk_level: str) -> dict:
	rid = pkg.get("risk_profile_id")
	high = bool(rid and (risk_level or "") == "High")
	st = str(pkg.get("status") or "")
	return {
		"high_risk": high,
		"emergency": bool(cint(pkg.get("is_emergency"))),
		"submitted": st == "Submitted",
		"ready": st == "Ready for Tender",
		"released": st == "Released to Tender",
	}


def _actions_for_workbench(status: str, role_key: str, *, plan_status: str = "") -> dict[str, bool]:
	"""E2 — Matrix §7.2: actions by role + package status (server is source of truth)."""
	st = status or ""
	ps = (plan_status or "").strip()
	rk = role_key or ""
	is_planner = rk in ("planner", "admin")
	is_authority = rk in ("authority", "admin")
	is_officer = rk == "officer"
	is_admin = rk == "admin"
	can_edit_lines = is_planner and st in ("Draft", "Completed", "Returned")
	can_release = ps == "Approved"
	return {
		"edit": can_edit_lines,
		"add_demand_lines": can_edit_lines,
		"remove_demand_lines": can_edit_lines,
		"complete": is_planner and st in ("Draft", "Returned"),
		"submit": is_planner and st == "Completed",
		"approve": is_authority and st == "Submitted",
		"return": is_authority and st == "Submitted",
		"reject": is_authority and st == "Submitted",
		"mark_ready": (is_officer or is_authority or is_admin) and st == "Approved",
		"release": (is_officer or is_authority or is_admin) and st == "Ready for Tender" and can_release,
	}


@frappe.whitelist()
def get_pp_package_detail(package: str | None = None) -> dict:
	"""Return read-only detail payload for the workbench right panel."""
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)

	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return _fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to the Procurement Planning workbench."),
			role_key=role_key or "auditor",
		)

	pkg_name = (package or "").strip()
	if not pkg_name:
		return _fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	if not frappe.db.exists("Procurement Package", pkg_name):
		return _fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	try:
		if not frappe.has_permission("Procurement Package", "read", pkg_name):
			return _fail(
				code="NO_PACKAGE_PERMISSION",
				message=_("You do not have permission to view this package."),
				role_key=role_key,
			)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to view this package."),
			role_key=role_key,
		)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		doc.check_permission("read")
	except frappe.DoesNotExistError:
		return _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to view this package."),
			role_key=role_key,
		)

	risk_level = ""
	if doc.risk_profile_id:
		risk_level = (
			frappe.db.get_value("Risk Profile", doc.risk_profile_id, "risk_level") or ""
		).strip()

	template_name = ""
	if doc.template_id:
		tpl_map = _template_names_for([str(doc.template_id)])
		template_name = tpl_map.get(str(doc.template_id), "") or ""

	lines = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": doc.name, "is_active": 1},
		fields=[
			"name",
			"demand_id",
			"budget_line_id",
			"amount",
			"department",
			"priority",
			"quantity",
		],
		order_by="idx asc, creation asc",
		limit_page_length=200,
	)

	demand_keys = [ln.get("demand_id") for ln in lines if ln.get("demand_id")]
	budget_keys = [ln.get("budget_line_id") for ln in lines if ln.get("budget_line_id")]
	demand_keys = list({str(x) for x in demand_keys if x})
	budget_keys = list({str(x) for x in budget_keys if x})

	demand_rows: list = []
	if demand_keys:
		demand_rows = frappe.get_all(
			"Demand",
			filters={"name": ("in", demand_keys)},
			fields=["name", "demand_id", "title", "requesting_department", "status"],
			limit_page_length=300,
		)
		found = {r.name for r in demand_rows}
		missing = [k for k in demand_keys if k not in found]
		if missing:
			demand_rows.extend(
				frappe.get_all(
					"Demand",
					filters={"demand_id": ("in", missing)},
					fields=["name", "demand_id", "title", "requesting_department", "status"],
					limit_page_length=300,
				)
			)
		seen_d: set[str] = set()
		deduped: list = []
		for r in demand_rows:
			if r.name in seen_d:
				continue
			seen_d.add(r.name)
			deduped.append(r)
		demand_rows = deduped
	demand_by_name = {r.name: r for r in demand_rows}
	demand_by_biz = {str(r.demand_id): r for r in demand_rows if r.get("demand_id")}

	budget_rows = (
		frappe.get_all(
			"Budget Line",
			filters={"name": ("in", budget_keys)},
			fields=["name", "budget_line_code", "budget_line_name"],
			limit_page_length=300,
		)
		if budget_keys
		else []
	)
	budget_by_name = {r.name: r for r in budget_rows}

	demand_lines_out: list[dict] = []
	for ln in lines:
		did = ln.get("demand_id")
		bid = ln.get("budget_line_id")
		dr = None
		if did:
			dr = demand_by_name.get(did) or demand_by_biz.get(str(did))
		br = budget_by_name.get(bid) if bid else None
		biz_demand = (dr.demand_id if dr else "") or (str(did) if did else "")
		demand_title = (dr.title if dr else "") or ""
		dept = (ln.get("department") or "") or (dr.requesting_department if dr else "") or ""
		bl_display = ""
		if br:
			bl_display = f"{br.budget_line_code or ''} — {br.budget_line_name or ''}".strip(" —")
		demand_lines_out.append(
			{
				"line_name": ln.get("name") or "",
				"demand_id": biz_demand,
				"demand_title": demand_title,
				"demand_status": (dr.status if dr else "") or "",
				"department": dept,
				"budget_line": bl_display,
				"amount": flt(ln.get("amount")),
				"priority": ln.get("priority") or "",
			}
		)

	risk_block: dict[str, Any] = {
		"profile_name": "",
		"profile_code": "",
		"risk_level": risk_level,
		"risks": [],
	}
	if doc.risk_profile_id:
		rp = frappe.db.get_value(
			"Risk Profile",
			doc.risk_profile_id,
			["profile_name", "profile_code", "risk_level", "risks"],
			as_dict=True,
		)
		if rp:
			risk_block["profile_name"] = rp.profile_name or ""
			risk_block["profile_code"] = rp.profile_code or ""
			risk_block["risk_level"] = (rp.risk_level or risk_level or "").strip()
			risk_block["risks"] = _normalize_risks(_as_list(rp.risks, max_items=20))

	kpi_block: dict[str, Any] = {"profile_name": "", "profile_code": "", "metrics": []}
	if doc.kpi_profile_id:
		kp = frappe.db.get_value(
			"KPI Profile",
			doc.kpi_profile_id,
			["profile_name", "profile_code", "metrics"],
			as_dict=True,
		)
		if kp:
			kpi_block["profile_name"] = kp.profile_name or ""
			kpi_block["profile_code"] = kp.profile_code or ""
			kpi_block["metrics"] = _normalize_metrics(_as_list(kp.metrics, max_items=40))

	decision_block: dict[str, Any] = {"profile_name": "", "profile_code": "", "criteria": []}
	if doc.decision_criteria_profile_id:
		dp = frappe.db.get_value(
			"Decision Criteria Profile",
			doc.decision_criteria_profile_id,
			["profile_name", "profile_code", "criteria"],
			as_dict=True,
		)
		if dp:
			decision_block["profile_name"] = dp.profile_name or ""
			decision_block["profile_code"] = dp.profile_code or ""
			decision_block["criteria"] = _normalize_criteria(_as_list(dp.criteria, max_items=30))

	vendor_block: dict[str, Any] = {
		"profile_name": "",
		"profile_code": "",
		"monitoring_summary": [],
		"escalation_summary": [],
	}
	if doc.vendor_management_profile_id:
		vp = frappe.db.get_value(
			"Vendor Management Profile",
			doc.vendor_management_profile_id,
			["profile_name", "profile_code", "monitoring_rules", "escalation_rules"],
			as_dict=True,
		)
		if vp:
			vendor_block["profile_name"] = vp.profile_name or ""
			vendor_block["profile_code"] = vp.profile_code or ""
			mr = vp.monitoring_rules
			er = vp.escalation_rules
			if isinstance(mr, str):
				try:
					mr = json.loads(mr)
				except Exception:
					mr = {}
			if isinstance(er, str):
				try:
					er = json.loads(er)
				except Exception:
					er = {}
			vendor_block["monitoring_summary"] = _flatten_json_obj(mr, max_lines=8)
			vendor_block["escalation_summary"] = _flatten_json_obj(er, max_lines=8)

	pkg_dict = doc.as_dict()
	badges = _badges_for_pkg(pkg_dict, risk_level=risk_level)
	plan_status = frappe.db.get_value("Procurement Plan", doc.plan_id, "status") or ""
	actions = _actions_for_workbench(doc.status or "", role_key, plan_status=plan_status)
	release_blocked_by_plan = (doc.status or "") == "Ready for Tender" and plan_status != "Approved"

	return {
		"ok": True,
		"role_key": role_key,
		"name": doc.name,
		"package_code": doc.package_code or "",
		"package_name": doc.package_name or "",
		"template_name": template_name,
		"procurement_method": doc.procurement_method or "",
		"contract_type": doc.contract_type or "",
		"currency": (doc.currency or "KES").strip() or "KES",
		"estimated_value": flt(doc.estimated_value),
		"schedule_start": doc.schedule_start,
		"schedule_end": doc.schedule_end,
		"status": doc.status or "",
		"plan_status": plan_status,
		"release_blocked_by_plan": release_blocked_by_plan,
		"planning_status": doc.planning_status or "",
		"method_override_flag": bool(cint(doc.method_override_flag)),
		"method_override_reason": doc.method_override_reason or "",
		"workflow_reason": doc.workflow_reason or "",
		"badges": badges,
		"actions": actions,
		"definition": {
			"package_name": doc.package_name or "",
			"package_code": doc.package_code or "",
			"template_name": template_name,
			"procurement_method": doc.procurement_method or "",
			"contract_type": doc.contract_type or "",
			"status": doc.status or "",
			"plan_status": plan_status,
			"method_override_flag": bool(cint(doc.method_override_flag)),
		},
		"financial": {
			"estimated_value": flt(doc.estimated_value),
			"currency": (doc.currency or "KES").strip() or "KES",
			"schedule_start": doc.schedule_start,
			"schedule_end": doc.schedule_end,
		},
		"demand_lines": demand_lines_out,
		"risk": risk_block,
		"kpi": kpi_block,
		"decision_criteria": decision_block,
		"vendor_management": vendor_block,
		"workflow": {
			"status": doc.status or "",
			"created_by": doc.created_by or "",
			"approved_by": doc.approved_by or "",
			"approved_at": doc.approved_at,
			"rejected_by": doc.rejected_by or "",
			"rejected_at": doc.rejected_at,
			"workflow_reason": doc.workflow_reason or "",
			"planning_status": doc.planning_status or "",
		},
	}
