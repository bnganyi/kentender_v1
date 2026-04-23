# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA queue list (D3) — work tab + role queue drives `frappe.get_list` on Demand."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, today

from kentender_procurement.demand_intake.api.dia_context import resolve_dia_role_key
from kentender_procurement.demand_intake.api.landing import _fail_payload

ALLOWED_QUEUES: dict[str, frozenset[str]] = {
	"requisitioner": frozenset(
		{"my_drafts", "submitted_by_me", "returned_to_me", "rejected", "my_approved"}
	),
	"hod": frozenset({"pending_hod", "returned_await", "emergency", "all_dept", "hod_rejected"}),
	"finance": frozenset({"pending_finance", "budget_exceptions", "emergency_fin", "approved_today", "dia_rejected"}),
	"procurement": frozenset(
		{"my_drafts", "all_demands", "planning_ready", "approved_not_planned", "emergency_approved", "all_approved", "dia_rejected"}
	),
	"admin": frozenset(
		{"my_drafts", "all_demands", "planning_ready", "approved_not_planned", "emergency_approved", "all_approved", "dia_rejected"}
	),
	"auditor": frozenset({"all_demands", "pending_hod", "pending_finance", "planning_ready", "all_approved", "dia_rejected"}),
}

DEFAULT_QUEUE: dict[str, str] = {
	"requisitioner": "my_drafts",
	"hod": "pending_hod",
	"finance": "pending_finance",
	"procurement": "all_demands",
	"admin": "all_demands",
	"auditor": "all_demands",
}

LIST_FIELDS = [
	"name",
	"demand_id",
	"title",
	"status",
	"demand_type",
	"priority_level",
	"requisition_type",
	"requested_by",
	"requesting_department",
	"procuring_entity",
	"total_amount",
	"required_by_date",
	"budget_line",
	"reservation_status",
	"reservation_reference",
	"is_exception",
	"modified",
]

DT = "Demand"


def _select_field_options(fieldname: str) -> list[str]:
	meta = frappe.get_meta(DT, cached=True)
	f = meta.get_field(fieldname)
	if not f or not getattr(f, "options", None):
		return []
	return [x.strip() for x in str(f.options).split("\n") if x.strip()]


def _scrub_search(q: str, max_len: int = 120) -> str:
	s = (q or "").strip()
	s = s.replace("%", "")
	# Do not strip `_`: common in IDs/titles; stripping broke OR search on titles (D4).
	if len(s) > max_len:
		s = s[:max_len]
	return s


def _dict_to_filter_list(filters: dict) -> list[list[Any]]:
	"""Turn Demand filter dict (D3 shapes) into get_list list form."""
	out: list[list[Any]] = []
	for field, val in (filters or {}).items():
		if val is None:
			continue
		if isinstance(val, (list, tuple)) and len(val) >= 2:
			op, rhs = val[0], val[1]
			op_s = str(op).lower()
			if op_s == "in":
				out.append([DT, field, "in", rhs])
			elif op_s == "not in":
				out.append([DT, field, "not in", rhs])
			elif op_s == "between":
				out.append([DT, field, "Between", rhs])
			elif str(op) in (">=", "<=", "!="):
				out.append([DT, field, str(op), rhs])
			else:
				out.append([DT, field, "=", val])
		else:
			out.append([DT, field, "=", val])
	return out


def _status_allowed_subset(base_val: Any, user_status: str) -> bool:
	if not user_status:
		return False
	if isinstance(base_val, str):
		return user_status == base_val
	if isinstance(base_val, (list, tuple)) and len(base_val) >= 2:
		op = str(base_val[0]).lower()
		if op == "in" and isinstance(base_val[1], (list, tuple)):
			return user_status in base_val[1]
	return False


def _parse_refine_dict(filters_arg: Any) -> dict[str, Any]:
	"""Parse client JSON object for D4 refine fields."""
	if filters_arg in (None, "", {}):
		return {}
	if isinstance(filters_arg, str):
		try:
			raw = json.loads(filters_arg)
		except json.JSONDecodeError:
			return {}
	else:
		raw = filters_arg
	if not isinstance(raw, dict):
		return {}
	out: dict[str, Any] = {}
	if raw.get("demand_type"):
		out["demand_type"] = str(raw["demand_type"]).strip()
	if raw.get("priority_level"):
		out["priority_level"] = str(raw["priority_level"]).strip()
	if raw.get("requisition_type"):
		out["requisition_type"] = str(raw["requisition_type"]).strip()
	if raw.get("status"):
		out["status"] = str(raw["status"]).strip()
	if raw.get("requesting_department"):
		out["requesting_department"] = str(raw["requesting_department"]).strip()
	if raw.get("budget_line"):
		out["budget_line"] = str(raw["budget_line"]).strip()
	if raw.get("date_from"):
		out["date_from"] = str(raw["date_from"]).strip()
	if raw.get("date_to"):
		out["date_to"] = str(raw["date_to"]).strip()
	if raw.get("amount_min") not in (None, "",):
		out["amount_min"] = flt(raw.get("amount_min"))
	if raw.get("amount_max") not in (None, "",):
		out["amount_max"] = flt(raw.get("amount_max"))
	return out


def _validate_refine_against_meta(refine: dict[str, Any]) -> dict[str, Any]:
	"""Drop refine values that are not valid Select / Link targets."""
	clean: dict[str, Any] = {}
	dt_opts = {k: set(_select_field_options(k)) for k in ("demand_type", "priority_level", "requisition_type", "status")}
	for key in ("demand_type", "priority_level", "requisition_type", "status"):
		v = refine.get(key)
		if not v:
			continue
		if v in dt_opts.get(key, set()):
			clean[key] = v
	dept = refine.get("requesting_department")
	if dept and frappe.db.exists("Procuring Department", dept):
		clean["requesting_department"] = dept
	bl = refine.get("budget_line")
	if bl and frappe.db.exists("DocType", "Budget Line") and frappe.db.exists("Budget Line", bl):
		clean["budget_line"] = bl
	if refine.get("date_from"):
		try:
			clean["date_from"] = getdate(refine["date_from"])
		except Exception:
			pass
	if refine.get("date_to"):
		try:
			clean["date_to"] = getdate(refine["date_to"])
		except Exception:
			pass
	if "amount_min" in refine:
		clean["amount_min"] = flt(refine["amount_min"])
	if "amount_max" in refine:
		clean["amount_max"] = flt(refine["amount_max"])
	if clean.get("date_from") and clean.get("date_to") and clean["date_from"] > clean["date_to"]:
		clean["date_from"], clean["date_to"] = clean["date_to"], clean["date_from"]
	if clean.get("amount_min") is not None and clean.get("amount_max") is not None:
		if flt(clean["amount_min"]) > flt(clean["amount_max"]):
			clean["amount_min"], clean["amount_max"] = clean["amount_max"], clean["amount_min"]
	return clean


def _merge_queue_and_refine(base: dict | None, refine: dict[str, Any]) -> list[list[Any]]:
	if base is None:
		return []
	refine = dict(refine)
	base_status = base.get("status") if base else None
	us = refine.get("status")
	if us and not _status_allowed_subset(base_status, us):
		refine.pop("status", None)
		us = None
	flist = _dict_to_filter_list(base)
	if us:
		bs = base.get("status") if base else None
		if not (isinstance(bs, str) and bs == us):
			flist = [x for x in flist if len(x) < 2 or x[1] != "status"]
			flist.append([DT, "status", "=", us])
	for key in ("demand_type", "priority_level", "requisition_type", "requesting_department", "budget_line"):
		if refine.get(key):
			flist.append([DT, key, "=", refine[key]])
	if refine.get("date_from") and refine.get("date_to"):
		flist.append([DT, "request_date", "Between", [refine["date_from"], refine["date_to"]]])
	elif refine.get("date_from"):
		flist.append([DT, "request_date", ">=", refine["date_from"]])
	elif refine.get("date_to"):
		flist.append([DT, "request_date", "<=", refine["date_to"]])
	if "amount_min" in refine and refine["amount_min"] is not None:
		flist.append([DT, "total_amount", ">=", flt(refine["amount_min"])])
	if "amount_max" in refine and refine["amount_max"] is not None:
		flist.append([DT, "total_amount", "<=", flt(refine["amount_max"])])
	return flist


def _search_or_filters(search: str) -> list[list[Any]] | None:
	q = _scrub_search(search)
	if not q:
		return None
	pat = f"%{q}%"
	return [
		[DT, "demand_id", "like", pat],
		[DT, "title", "like", pat],
		[DT, "requested_by", "like", pat],
		[DT, "requesting_department", "like", pat],
	]


def _normalize_queue_id(role_key: str, queue_id: str | None) -> str:
	allowed = ALLOWED_QUEUES.get(role_key, ALLOWED_QUEUES["requisitioner"])
	if queue_id and queue_id in allowed:
		return queue_id
	return DEFAULT_QUEUE.get(role_key, "my_drafts")


def _today_datetime_bounds():
	d0 = get_datetime(f"{today()} 00:00:00")
	d1 = get_datetime(f"{today()} 23:59:59")
	return d0, d1


def _filters_requisitioner(*, work_tab: str, queue_id: str, user: str) -> dict | None:
	if work_tab == "approved":
		if queue_id != "my_approved":
			return None
		return {"status": ["in", ["Approved", "Planning Ready"]], "requested_by": user}

	if work_tab == "rejected":
		if queue_id == "rejected":
			return {"status": "Rejected", "requested_by": user}
		if queue_id == "returned_to_me":
			return {"status": "Draft", "return_reason": ("!=", ""), "requested_by": user}
		return None

	if queue_id == "my_drafts":
		f: dict = {"status": "Draft"}
		if work_tab == "mywork":
			f["requested_by"] = user
		return f

	if queue_id == "submitted_by_me":
		f = {"status": ["in", ["Pending HoD Approval", "Pending Finance Approval"]]}
		if work_tab == "mywork":
			f["requested_by"] = user
		return f

	if queue_id == "returned_to_me":
		f = {"status": "Draft", "return_reason": ("!=", "")}
		if work_tab == "mywork":
			f["requested_by"] = user
		return f

	if queue_id == "rejected":
		f = {"status": "Rejected"}
		if work_tab == "mywork":
			f["requested_by"] = user
		return f

	if queue_id == "my_approved":
		f = {"status": ["in", ["Approved", "Planning Ready"]]}
		if work_tab == "mywork":
			f["requested_by"] = user
		return f

	return None


def _filters_hod(*, work_tab: str, queue_id: str) -> dict | None:
	if work_tab == "approved":
		if queue_id == "all_dept":
			return {"status": ["in", ["Approved", "Planning Ready"]]}
		if queue_id == "emergency":
			return {
				"demand_type": "Emergency",
				"status": ["in", ["Approved", "Planning Ready"]],
			}
		return None

	if work_tab == "rejected":
		if queue_id == "returned_await":
			return {"status": "Draft", "return_reason": ("!=", "")}
		if queue_id == "hod_rejected":
			return {"status": "Rejected"}
		return {"status": "Rejected"}

	if queue_id == "hod_rejected":
		return {"status": "Rejected"}

	if queue_id == "pending_hod":
		return {"status": "Pending HoD Approval"}
	if queue_id == "returned_await":
		return {"status": "Draft", "return_reason": ("!=", "")}
	if queue_id == "emergency":
		return {"demand_type": "Emergency", "status": "Pending HoD Approval"}
	if queue_id == "all_dept":
		return {"status": ["not in", ["Cancelled"]]}
	return None


def _filters_finance(*, work_tab: str, queue_id: str) -> dict | None:
	if work_tab == "approved":
		if queue_id == "approved_today":
			d0, d1 = _today_datetime_bounds()
			return {"status": "Approved", "finance_approved_at": ["between", [d0, d1]]}
		return None

	if work_tab == "rejected":
		if queue_id == "budget_exceptions":
			return {"reservation_status": "Failed"}
		if queue_id == "dia_rejected":
			return {"status": "Rejected"}
		return {"status": "Rejected"}

	if queue_id == "dia_rejected":
		return {"status": "Rejected"}

	if queue_id == "pending_finance":
		return {"status": "Pending Finance Approval"}
	if queue_id == "budget_exceptions":
		return {"reservation_status": "Failed"}
	if queue_id == "emergency_fin":
		return {"demand_type": "Emergency", "status": "Pending Finance Approval"}
	if queue_id == "approved_today":
		d0, d1 = _today_datetime_bounds()
		return {"status": "Approved", "finance_approved_at": ["between", [d0, d1]]}
	return None


def _filters_procurement(*, work_tab: str, queue_id: str, user: str) -> dict | None:
	if work_tab == "mywork":
		if queue_id == "my_drafts":
			return {"status": "Draft", "requested_by": user}
		if queue_id == "all_demands":
			return {"status": ["not in", ["Cancelled"]]}
		return {"status": "Draft", "requested_by": user}

	if work_tab == "rejected":
		return {"status": "Rejected"}

	if queue_id == "dia_rejected":
		return {"status": "Rejected"}
	if queue_id == "my_drafts":
		return {"status": "Draft", "requested_by": user}
	if queue_id == "all_demands":
		return {"status": ["not in", ["Cancelled"]]}

	if queue_id == "planning_ready":
		return {"status": "Planning Ready"}
	if queue_id == "approved_not_planned":
		return {"status": "Approved", "planning_status": ["in", ["Not Planned", "Partially Planned"]]}
	if queue_id == "emergency_approved":
		return {
			"demand_type": "Emergency",
			"status": ["in", ["Approved", "Planning Ready"]],
		}
	if queue_id == "all_approved":
		return {"status": ["in", ["Approved", "Planning Ready"]]}
	return None


def _filters_auditor(*, work_tab: str, queue_id: str) -> dict | None:
	if work_tab == "approved":
		if queue_id == "planning_ready":
			return {"status": "Planning Ready"}
		if queue_id == "all_approved":
			return {"status": ["in", ["Approved", "Planning Ready"]]}
		return None

	if work_tab == "rejected":
		if queue_id == "dia_rejected":
			return {"status": "Rejected"}
		return None

	if queue_id == "pending_hod":
		return {"status": "Pending HoD Approval"}
	if queue_id == "pending_finance":
		return {"status": "Pending Finance Approval"}
	if queue_id == "planning_ready":
		return {"status": "Planning Ready"}
	if queue_id == "all_approved":
		return {"status": ["in", ["Approved", "Planning Ready"]]}
	if queue_id == "dia_rejected":
		return {"status": "Rejected"}
	if queue_id == "all_demands":
		return {"status": ["not in", ["Cancelled"]]}
	return None


def _resolve_filters(*, role_key: str, work_tab: str, queue_id: str, user: str) -> dict | None:
	if work_tab not in ("mywork", "all", "approved", "rejected"):
		work_tab = "mywork"

	if role_key == "requisitioner":
		return _filters_requisitioner(work_tab=work_tab, queue_id=queue_id, user=user)
	if role_key == "hod":
		return _filters_hod(work_tab=work_tab, queue_id=queue_id)
	if role_key == "finance":
		return _filters_finance(work_tab=work_tab, queue_id=queue_id)
	if role_key in ("procurement", "admin"):
		return _filters_procurement(work_tab=work_tab, queue_id=queue_id, user=user)
	if role_key == "auditor":
		return _filters_auditor(work_tab=work_tab, queue_id=queue_id)
	return _filters_requisitioner(work_tab=work_tab, queue_id=queue_id, user=user)


def _enrich_demand_queue_rows(rows: list[dict]) -> None:
	"""Add display labels for DIA master list (UI spec §4.2, D5)."""
	if not rows:
		return
	dept_ids = {r.get("requesting_department") for r in rows if r.get("requesting_department")}
	dept_map: dict[str, str] = {}
	if dept_ids:
		for d in frappe.get_all(
			"Procuring Department",
			filters={"name": ("in", list(dept_ids))},
			fields=["name", "department_name"],
			limit_page_length=len(dept_ids) + 10,
		):
			dept_map[d.name] = (d.get("department_name") or d.name or "").strip() or d.name

	bl_ids = {r.get("budget_line") for r in rows if r.get("budget_line")}
	bl_map: dict[str, str] = {}
	if bl_ids and frappe.db.exists("DocType", "Budget Line"):
		for b in frappe.get_all(
			"Budget Line",
			filters={"name": ("in", list(bl_ids))},
			fields=["name", "budget_line_name", "budget_line_code"],
			limit_page_length=len(bl_ids) + 10,
		):
			lbl = b.get("budget_line_name") or b.get("budget_line_code") or b.get("name")
			bl_map[b.name] = str(lbl).strip() if lbl else b.name

	user_ids = {r.get("requested_by") for r in rows if r.get("requested_by")}
	user_map: dict[str, str] = {}
	if user_ids:
		for u in frappe.get_all(
			"User",
			filters={"name": ("in", list(user_ids))},
			fields=["name", "full_name"],
			limit_page_length=len(user_ids) + 10,
		):
			user_map[u.name] = (u.get("full_name") or u.name or "").strip() or u.name

	for r in rows:
		did = r.get("requesting_department")
		r["requesting_department_label"] = dept_map.get(did, did or "")
		bn = r.get("budget_line")
		r["budget_line_label"] = bl_map.get(bn, "") if bn else ""
		uid = r.get("requested_by")
		r["requested_by_label"] = user_map.get(uid, uid or "")
		if r.get("is_exception") is not None:
			r["is_exception"] = cint(r.get("is_exception"))


def _empty_caption(queue_id: str) -> str:
	return {
		"my_drafts": _("No drafts in this queue."),
		"submitted_by_me": _("Nothing submitted is waiting in this queue."),
		"returned_to_me": _("No returned demands."),
		"rejected": _("No rejected demands."),
		"my_approved": _("No approved demands yet."),
		"pending_hod": _("Nothing pending HoD approval."),
		"returned_await": _("No demands awaiting resubmission."),
		"emergency": _("No emergency requests."),
		"all_dept": _("No department demands match this view."),
		"pending_finance": _("Nothing pending finance approval."),
		"budget_exceptions": _("No budget failures."),
		"emergency_fin": _("No emergency requests at finance."),
		"approved_today": _("No demands finance-approved today."),
		"planning_ready": _("Nothing is planning ready."),
		"approved_not_planned": _("No approved demands pending planning."),
		"emergency_approved": _("No emergency demands in approved states."),
		"all_approved": _("No approved or planning-ready demands."),
		"all_demands": _("No demands match this view."),
		"dia_rejected": _("No rejected demands in this view."),
		"hod_rejected": _("No rejected demands for this department view."),
		"all_demands": _("No demand records in this view."),
		"pending_hod": _("Nothing pending HoD approval."),
		"pending_finance": _("Nothing pending finance approval."),
	}.get(queue_id, _("This queue is empty."))


@frappe.whitelist()
def get_dia_queue_filter_meta():
	"""Select options + link picklists for DIA list refine (UI spec §3.6)."""
	from kentender_procurement.demand_intake.api.dia_access import user_has_dia_workspace_access

	if not frappe.db.exists("DocType", "Demand"):
		return {"ok": False, "message": _("Demand is not installed on this site.")}
	if not user_has_dia_workspace_access():
		return {"ok": False, "message": _("You are not allowed to access Demand Intake."), "error_code": "DIA_ACCESS_DENIED"}
	if not frappe.has_permission("Demand", "read"):
		return {"ok": False, "message": _("No permission to read Demand.")}

	depts = frappe.get_all(
		"Procuring Department",
		fields=["name", "department_name"],
		order_by="department_name asc",
		limit_page_length=400,
	)
	department_options = [{"value": d.name, "label": d.get("department_name") or d.name} for d in depts]

	budget_lines: list[dict[str, str]] = []
	if frappe.db.exists("DocType", "Budget Line"):
		bl_rows = frappe.get_all(
			"Budget Line",
			filters={"is_active": 1},
			fields=["name", "budget_line_name", "budget_line_code"],
			order_by="budget_line_code asc",
			limit_page_length=400,
		)
		for r in bl_rows:
			lbl = r.get("budget_line_name") or r.get("budget_line_code") or r.get("name")
			budget_lines.append({"value": r.name, "label": str(lbl)})

	return {
		"ok": True,
		"demand_types": _select_field_options("demand_type"),
		"priorities": _select_field_options("priority_level"),
		"requisition_types": _select_field_options("requisition_type"),
		"statuses": _select_field_options("status"),
		"departments": department_options,
		"budget_lines": budget_lines,
	}


@frappe.whitelist()
def get_dia_queue_list(
	work_tab: str = "mywork",
	queue_id: str | None = None,
	limit: int = 50,
	start: int = 0,
	search: str | None = None,
	filters: str | None = None,
):
	"""Return Demand rows for the active work tab + queue, refined by filters/search (§3.6, D4)."""
	from kentender_procurement.demand_intake.api.dia_access import user_has_dia_workspace_access

	if not frappe.db.exists("DocType", "Demand"):
		site = frappe.local.site or "this site"
		return _fail_payload(
			error_code="DEMAND_NOT_INSTALLED",
			message=_(
				"The Demand document type is not installed on site {0}. "
				"Confirm `kentender_procurement` is installed, then run: bench --site {0} migrate"
			).format(site),
		)
	if not user_has_dia_workspace_access():
		return _fail_payload(
			error_code="DIA_ACCESS_DENIED",
			message=_("You are not allowed to access Demand Intake."),
		)
	if not frappe.has_permission("Demand", "read"):
		return _fail_payload(
			error_code="NO_READ_PERMISSION",
			message=_(
				"You do not have permission to read Demand records. Ask an administrator to grant Demand read access for your role."
			),
		)

	limit = cint(limit)
	start = cint(start)
	if limit < 1:
		limit = 50
	if limit > 200:
		limit = 200
	if start < 0:
		start = 0

	user = frappe.session.user
	role_key = resolve_dia_role_key()
	queue_id = _normalize_queue_id(role_key, queue_id)
	work_tab = (work_tab or "mywork").strip().lower()
	if work_tab not in ("mywork", "all", "approved", "rejected"):
		work_tab = "mywork"

	base_filters = _resolve_filters(role_key=role_key, work_tab=work_tab, queue_id=queue_id, user=user)
	if base_filters is None:
		return {
			"ok": True,
			"role_key": role_key,
			"work_tab": work_tab,
			"queue_id": queue_id,
			"queue_label": queue_id,
			"demands": [],
			"has_more": False,
			"empty_caption": _("This view does not apply to the selected queue. Pick another queue or tab."),
		}

	refine_in: Any = {}
	if isinstance(filters, str):
		try:
			refine_in = json.loads(filters) if (filters and filters.strip()) else {}
		except json.JSONDecodeError:
			refine_in = {}
	elif isinstance(filters, dict):
		refine_in = filters
	refine = _validate_refine_against_meta(_parse_refine_dict(refine_in))
	flist = _merge_queue_and_refine(base_filters, refine)
	or_filters = _search_or_filters(search or "")
	gl_kwargs: dict[str, Any] = {
		"doctype": DT,
		"filters": flist,
		"fields": LIST_FIELDS,
		"order_by": "modified desc",
		"limit_start": start,
		"limit_page_length": limit + 1,
	}
	if or_filters:
		gl_kwargs["or_filters"] = or_filters
	demands = frappe.get_list(**gl_kwargs)
	has_more = len(demands) > limit
	if has_more:
		demands = demands[:limit]

	_enrich_demand_queue_rows(demands)
	for d in demands:
		if d.get("total_amount") is not None:
			d["total_amount"] = flt(d["total_amount"])

	currency = "KES"
	try:
		currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "KES"
	except Exception:
		pass

	return {
		"ok": True,
		"role_key": role_key,
		"work_tab": work_tab,
		"queue_id": queue_id,
		"queue_label": queue_id,
		"demands": demands,
		"has_more": has_more,
		"empty_caption": _empty_caption(queue_id),
		"currency": currency,
		"applied_refine": refine,
	}
