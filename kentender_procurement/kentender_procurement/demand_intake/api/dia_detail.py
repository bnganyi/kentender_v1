# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA landing detail (D6 §5.2), toolbar actions (D7 §6), Form header chrome (E1 §7)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, format_datetime, get_datetime, getdate

from kentender_procurement.demand_intake.api.dia_access import require_demand_read, user_has_dia_workspace_access
from kentender_procurement.demand_intake.api.dia_context import resolve_dia_role_key
from kentender_procurement.demand_intake.api.landing import _fail_payload
from kentender_procurement.demand_intake.doctype.demand.demand import STATUSES_FULLY_EDITABLE

DT = "Demand"

# (doctype, field names…) first non-empty wins
_LINK_LABEL_FIELDS: dict[str, tuple[str, ...]] = {
	"Procuring Department": ("department_name",),
	"Procuring Entity": ("entity_name",),
	"User": ("full_name",),
	"Budget Line": ("budget_line_name", "budget_line_code"),
	"Budget": ("budget_name",),
	"Funding Source": ("title",),
	"Strategic Plan": ("strategic_plan_name",),
	"Strategy Program": ("program_title", "program_code"),
	"Sub Program": ("title", "sub_program_code"),
	"Strategy Objective": ("objective_title", "objective_code"),
	"Strategy Target": ("target_title", "target_code"),
}


def _link_label(doctype: str, name: str | None) -> str:
	if not name or not doctype:
		return ""
	if not frappe.db.exists("DocType", doctype):
		return str(name)
	if not frappe.db.exists(doctype, name):
		return str(name)
	fields = _LINK_LABEL_FIELDS.get(doctype, ("name",))
	row = frappe.db.get_value(doctype, name, fields, as_dict=True)
	if not row:
		return str(name)
	for fn in fields:
		v = row.get(fn)
		if v:
			return str(v).strip()
	return str(name)


def _date_str(val) -> str | None:
	if not val:
		return None
	return str(getdate(val))


def _dt_str(val) -> str | None:
	if not val:
		return None
	try:
		return format_datetime(get_datetime(val))
	except Exception:
		return str(val)


def _user_label(uid: str | None) -> str:
	return _link_label("User", uid) if uid else ""


def _approval_stage_label(doc) -> str:
	st = doc.status or ""
	if st == "Draft":
		if (getattr(doc, "return_reason", None) or "").strip():
			return _("Returned — awaiting resubmission")
		return _("Draft")
	if st == "Pending HoD Approval":
		return _("HoD approval")
	if st == "Pending Finance Approval":
		return _("Finance approval")
	if st == "Approved":
		return _("Approved")
	if st == "Planning Ready":
		return _("Planning ready")
	if st == "Rejected":
		return _("Rejected")
	if st == "Cancelled":
		return _("Cancelled")
	return st or _("Unknown")


def _cannot_self_service_approve(doc) -> bool:
	return bool(doc.requested_by and doc.requested_by == frappe.session.user)


def _action_open_form(doc) -> dict:
	can_write = bool(frappe.has_permission("Demand", "write", doc=doc.name))
	edit = can_write and doc.status in ("Draft", "Rejected")
	return {
		"id": "open_form",
		"label": _("Edit Demand") if edit else _("View demand"),
		"client_action": "open_form",
		"primary": False,
		"danger": False,
		"reason": None,
		"edit": edit,
	}


def _rpc(
	action_id: str,
	label: str,
	method: str,
	*,
	primary: bool = False,
	danger: bool = False,
	reason: str | None = None,
) -> dict:
	return {
		"id": action_id,
		"label": str(label),
		"method": method,
		"primary": primary,
		"danger": danger,
		"reason": reason,
	}


def _role_workflow_actions(doc, role_key: str) -> list[dict]:
	"""D7 — lifecycle buttons only (no open_form)."""
	from kentender_procurement.demand_intake.api.lifecycle import _cancel_allowed_for_current_user

	L = "kentender_procurement.demand_intake.api.lifecycle."
	st = doc.status or ""
	out: list[dict] = []

	def _cancel_action() -> dict:
		return _rpc(
			"cancel_demand",
			_("Cancel demand"),
			f"{L}cancel_demand",
			danger=True,
			reason="cancellation",
		)

	if role_key == "requisitioner":
		if st == "Draft":
			out.append(
				_rpc(
					"submit_demand",
					_("Submit for Approval"),
					f"{L}submit_demand",
					primary=True,
				)
			)
			if _cancel_allowed_for_current_user(doc):
				out.append(_cancel_action())
		elif st == "Rejected":
			out.append(
				_rpc(
					"submit_demand",
					_("Re-submit for Approval"),
					f"{L}submit_demand",
					primary=True,
				)
			)
			if _cancel_allowed_for_current_user(doc):
				out.append(_cancel_action())
		return out

	if role_key == "hod" and st == "Pending HoD Approval":
		if not _cannot_self_service_approve(doc):
			out.append(_rpc("approve_hod", _("Approve"), f"{L}approve_hod", primary=True))
		out.append(
			_rpc(
				"return_from_hod",
				_("Return to draft"),
				f"{L}return_from_hod",
				reason="return",
			)
		)
		out.append(
			_rpc(
				"reject_from_hod",
				_("Reject"),
				f"{L}reject_from_hod",
				danger=True,
				reason="rejection",
			)
		)
		if _cancel_allowed_for_current_user(doc):
			out.append(_cancel_action())
		return out

	if role_key == "finance" and st == "Pending Finance Approval":
		if not _cannot_self_service_approve(doc):
			out.append(
				_rpc(
					"approve_finance",
					_("Approve and reserve budget"),
					f"{L}approve_finance",
					primary=True,
				)
			)
		out.append(
			_rpc(
				"return_from_finance",
				_("Return to draft"),
				f"{L}return_from_finance",
				reason="return",
			)
		)
		out.append(
			_rpc(
				"reject_from_finance",
				_("Reject"),
				f"{L}reject_from_finance",
				danger=True,
				reason="rejection",
			)
		)
		if _cancel_allowed_for_current_user(doc):
			out.append(_cancel_action())
		return out

	if role_key == "procurement" and st == "Approved":
		out.append(
			_rpc(
				"mark_planning_ready",
				_("Mark planning ready"),
				f"{L}mark_planning_ready",
				primary=True,
			)
		)
		if _cancel_allowed_for_current_user(doc):
			out.append(_cancel_action())
		return out

	return out


def _landing_actions(doc, role_key: str) -> list[dict]:
	"""D7 — ordered toolbar actions for the detail panel (UI spec §6, D7)."""
	out: list[dict] = [_action_open_form(doc)]
	if role_key == "admin":
		seen: set[str] = {"open_form"}
		for rk in ("requisitioner", "hod", "finance", "procurement"):
			for a in _role_workflow_actions(doc, rk):
				aid = a.get("id")
				if not aid or aid in seen:
					continue
				seen.add(aid)
				out.append(a)
		return out
	out.extend(_role_workflow_actions(doc, role_key))
	return out


def _form_header_actions(doc, role_key: str) -> list[dict]:
	"""Same as landing toolbar but omit *open_form* (user is already on the Form)."""
	return [a for a in _landing_actions(doc, role_key) if a.get("id") != "open_form"]


def _basic_items_editable_for_status(status: str | None) -> bool:
	"""B3 / E3 — Basic Request + Items match server edit lock (Draft, Rejected only)."""
	return bool(status) and status in STATUSES_FULLY_EDITABLE


@frappe.whitelist()
def get_dia_demand_form_header(name: str | None = None):
	"""Minimal Demand Form chrome for DIA builder shell (E1): IDs, status, D7 workflow actions; E3 edit flag."""
	if not frappe.db.exists("DocType", DT):
		return {
			"ok": False,
			"error_code": "DEMAND_NOT_INSTALLED",
			"actions": [],
			"basic_items_editable": False,
		}
	if not user_has_dia_workspace_access():
		return {
			"ok": False,
			"error_code": "DIA_ACCESS_DENIED",
			"actions": [],
			"basic_items_editable": False,
		}
	if not name or not str(name).strip():
		return {
			"ok": True,
			"name": None,
			"demand_id": None,
			"status": "Draft",
			"demand_type": None,
			"priority_level": None,
			"role_key": resolve_dia_role_key(),
			"actions": [],
			"basic_items_editable": True,
		}
	name = str(name).strip()
	if not frappe.db.exists(DT, name):
		return {
			"ok": False,
			"error_code": "NOT_FOUND",
			"actions": [],
			"basic_items_editable": False,
		}
	try:
		require_demand_read(name)
	except frappe.PermissionError:
		return {
			"ok": False,
			"error_code": "NO_READ_PERMISSION",
			"actions": [],
			"basic_items_editable": False,
		}
	try:
		doc = frappe.get_doc(DT, name)
	except frappe.DoesNotExistError:
		return {
			"ok": False,
			"error_code": "NOT_FOUND",
			"actions": [],
			"basic_items_editable": False,
		}
	except frappe.PermissionError:
		return {
			"ok": False,
			"error_code": "NO_READ_PERMISSION",
			"actions": [],
			"basic_items_editable": False,
		}

	role_key = resolve_dia_role_key()
	return {
		"ok": True,
		"name": doc.name,
		"demand_id": doc.demand_id,
		"status": doc.status,
		"demand_type": doc.demand_type,
		"priority_level": doc.priority_level,
		"role_key": role_key,
		"actions": _form_header_actions(doc, role_key),
		"basic_items_editable": _basic_items_editable_for_status(doc.status),
	}


@frappe.whitelist()
def get_dia_demand_detail(name: str | None = None):
	"""Return structured Demand fields for the DIA detail panel (§5.2, D6)."""
	if not frappe.db.exists("DocType", DT):
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
	if not name or not str(name).strip():
		return _fail_payload(
			error_code="MISSING_NAME",
			message=_("No demand was specified."),
		)
	name = str(name).strip()
	if not frappe.db.exists(DT, name):
		return _fail_payload(
			error_code="NOT_FOUND",
			message=_("Demand {0} was not found.").format(name),
		)

	try:
		require_demand_read(name)
	except frappe.PermissionError:
		return _fail_payload(
			error_code="NO_READ_PERMISSION",
			message=_("You do not have permission to read this demand."),
		)

	try:
		doc = frappe.get_doc(DT, name)
	except frappe.DoesNotExistError:
		return _fail_payload(
			error_code="NOT_FOUND",
			message=_("Demand {0} was not found.").format(name),
		)
	except frappe.PermissionError:
		return _fail_payload(
			error_code="NO_READ_PERMISSION",
			message=_("You do not have permission to read this demand."),
		)

	role_key = resolve_dia_role_key()
	currency = "KES"
	try:
		currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "KES"
	except Exception:
		pass

	dept_l = _link_label("Procuring Department", doc.requesting_department)
	req_l = _user_label(doc.requested_by)
	ent_l = _link_label("Procuring Entity", doc.procuring_entity)

	items_out: list[dict] = []
	for row in doc.get("items") or []:
		items_out.append(
			{
				"item_description": getattr(row, "item_description", None) or "",
				"category": getattr(row, "category", None) or "",
				"uom": getattr(row, "uom", None) or "",
				"quantity": flt(getattr(row, "quantity", None)),
				"estimated_unit_cost": flt(getattr(row, "estimated_unit_cost", None)),
				"line_total": flt(getattr(row, "line_total", None)),
			}
		)

	return {
		"ok": True,
		"role_key": role_key,
		"currency": currency,
		"name": doc.name,
		"a": {
			"title": doc.title,
			"demand_id": doc.demand_id,
			"status": doc.status,
			"demand_type": doc.demand_type,
			"priority_level": doc.priority_level,
			"requisition_type": doc.requisition_type,
			"requesting_department": doc.requesting_department,
			"requesting_department_label": dept_l,
			"requested_by": doc.requested_by,
			"requested_by_label": req_l,
			"procuring_entity": doc.procuring_entity,
			"procuring_entity_label": ent_l,
			"request_date": _date_str(doc.request_date),
			"required_by_date": _date_str(doc.required_by_date),
		},
		"b": {
			"budget_line": doc.budget_line,
			"budget_line_label": _link_label("Budget Line", doc.budget_line),
			"budget": doc.budget,
			"budget_label": _link_label("Budget", doc.budget),
			"funding_source": doc.funding_source,
			"funding_source_label": _link_label("Funding Source", doc.funding_source),
			"reservation_status": doc.reservation_status,
			"strategic_plan": doc.strategic_plan,
			"strategic_plan_label": _link_label("Strategic Plan", doc.strategic_plan),
			"program": doc.program,
			"program_label": _link_label("Strategy Program", doc.program),
			"sub_program": doc.sub_program,
			"sub_program_label": _link_label("Sub Program", doc.sub_program),
			"output_indicator": doc.output_indicator,
			"output_indicator_label": _link_label("Strategy Objective", doc.output_indicator),
			"performance_target": doc.performance_target,
			"performance_target_label": _link_label("Strategy Target", doc.performance_target),
		},
		"c": {
			"total_amount": flt(doc.total_amount),
			"available_budget_at_check": flt(doc.available_budget_at_check)
			if doc.available_budget_at_check is not None
			else None,
			"reservation_reference": doc.reservation_reference or None,
			"budget_check_datetime": _dt_str(doc.budget_check_datetime),
		},
		"d": {
			"line_count": len(items_out),
			"rows": items_out,
		},
		"e": {
			"current_stage": str(_approval_stage_label(doc)),
			"planning_status": doc.planning_status,
			"status": doc.status,
			"submitted_by": doc.submitted_by,
			"submitted_by_label": _user_label(doc.submitted_by),
			"submitted_at": _dt_str(doc.submitted_at),
			"hod_approved_by": doc.hod_approved_by,
			"hod_approved_by_label": _user_label(doc.hod_approved_by),
			"hod_approved_at": _dt_str(doc.hod_approved_at),
			"finance_approved_by": doc.finance_approved_by,
			"finance_approved_by_label": _user_label(doc.finance_approved_by),
			"finance_approved_at": _dt_str(doc.finance_approved_at),
			"rejected_by": doc.rejected_by,
			"rejected_by_label": _user_label(doc.rejected_by),
			"rejected_at": _dt_str(doc.rejected_at),
			"rejection_reason": doc.rejection_reason or None,
			"returned_by": doc.returned_by,
			"returned_by_label": _user_label(doc.returned_by),
			"returned_at": _dt_str(doc.returned_at),
			"return_reason": doc.return_reason or None,
			"cancelled_by": doc.cancelled_by,
			"cancelled_by_label": _user_label(doc.cancelled_by),
			"cancelled_at": _dt_str(doc.cancelled_at),
			"cancellation_reason": doc.cancellation_reason or None,
			"is_exception": bool(cint(doc.is_exception)),
		},
		"actions": _landing_actions(doc, role_key),
	}
