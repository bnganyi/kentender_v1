# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B2 — Whitelisted Demand lifecycle actions (Cursor Pack B2, PRD §8 / §17)."""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kentender_budget.api.dia_budget_control import (
	check_available_budget,
	create_reservation,
	get_active_reservation_for_source,
	release_reservation,
)
from kentender_procurement.demand_intake.api.dia_access import require_demand_write

# Map PRD actors to Frappe Role names (see kentender_core.seeds.constants.BUSINESS_ROLES).
ROLE_REQUISITIONER = "Requisitioner"
ROLE_DEPARTMENT_APPROVER = "Department Approver"
ROLE_FINANCE_REVIEWER = "Finance Reviewer"
ROLE_PROCUREMENT_PLANNER = "Procurement Planner"


def _is_privileged_user():
	user = frappe.session.user
	if user == "Administrator":
		return True
	return "System Manager" in frappe.get_roles(user)


def _has_any_role(role_names: tuple[str, ...]) -> bool:
	if _is_privileged_user():
		return True
	roles = set(frappe.get_roles(frappe.session.user))
	return bool(roles & set(role_names))


def _require_roles(*role_names: str) -> None:
	if _has_any_role(tuple(role_names)):
		return
	frappe.throw(
		_("You do not have permission to perform this action."),
		frappe.PermissionError,
	)


def _require_reason(value, label: str) -> str:
	text = (value or "").strip()
	if not text:
		frappe.throw(_("{0} is required.").format(label))
	return text


def _ensure_not_self_approving(doc) -> None:
	if doc.requested_by and doc.requested_by == frappe.session.user:
		frappe.throw(_("You cannot approve your own demand."), title=_("Not allowed"))


def _require_submit_authority(doc) -> None:
	if _is_privileged_user():
		return
	if frappe.session.user != doc.requested_by:
		frappe.throw(_("Only the request owner may submit this demand."), title=_("Not allowed"))
	_require_roles(ROLE_REQUISITIONER)


def _cancel_allowed_for_current_user(doc) -> bool:
	if _is_privileged_user():
		return True
	user = frappe.session.user
	st = doc.status
	if st == "Draft":
		return _has_any_role((ROLE_REQUISITIONER,)) and user == doc.requested_by
	if st == "Pending HoD Approval":
		return _has_any_role((ROLE_DEPARTMENT_APPROVER,))
	if st == "Pending Finance Approval":
		return _has_any_role((ROLE_FINANCE_REVIEWER,))
	if st == "Approved":
		if _has_any_role((ROLE_PROCUREMENT_PLANNER,)):
			return True
		return _has_any_role((ROLE_REQUISITIONER,)) and user == doc.requested_by
	if st == "Rejected":
		return _has_any_role((ROLE_REQUISITIONER,)) and user == doc.requested_by
	return False


def _require_cancel_authority(doc) -> None:
	if _cancel_allowed_for_current_user(doc):
		return
	frappe.throw(
		_("You are not allowed to cancel this demand in its current state."),
		frappe.PermissionError,
	)


def _save_doc(doc):
	"""Persist with B3 bypass so Demand.validate allows workflow/metadata updates."""
	frappe.flags.demand_lifecycle_action = True
	try:
		doc.save()
	finally:
		frappe.flags.demand_lifecycle_action = False


@frappe.whitelist()
def submit_demand(demand_name: str | None = None):
	"""Draft or Rejected → Pending HoD Approval."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_submit_authority(doc)
	if doc.status not in ("Draft", "Rejected"):
		frappe.throw(_("Only Draft or Rejected demands can be submitted."))
	if doc.status == "Rejected":
		# B4 — clear last return-to-draft metadata on resubmit; keep rejection audit fields.
		doc.return_reason = None
		doc.returned_by = None
		doc.returned_at = None
	doc.validate_submission_gate()
	now = now_datetime()
	doc.status = "Pending HoD Approval"
	doc.submitted_by = frappe.session.user
	doc.submitted_at = now
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_hod(demand_name: str | None = None):
	"""Pending HoD Approval → Pending Finance Approval."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_DEPARTMENT_APPROVER)
	if doc.status != "Pending HoD Approval":
		frappe.throw(_("Demand is not awaiting HoD approval."))
	_ensure_not_self_approving(doc)
	now = now_datetime()
	doc.status = "Pending Finance Approval"
	doc.hod_approved_by = frappe.session.user
	doc.hod_approved_at = now
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def return_from_hod(demand_name: str | None = None, reason: str | None = None):
	"""Pending HoD Approval → Draft."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	text = _require_reason(reason, _("Return reason"))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_DEPARTMENT_APPROVER)
	if doc.status != "Pending HoD Approval":
		frappe.throw(_("Demand is not awaiting HoD approval."))
	now = now_datetime()
	doc.status = "Draft"
	doc.return_reason = text
	doc.returned_by = frappe.session.user
	doc.returned_at = now
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_from_hod(demand_name: str | None = None, rejection_reason: str | None = None):
	"""Pending HoD Approval → Rejected."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	text = _require_reason(rejection_reason, _("Rejection reason"))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_DEPARTMENT_APPROVER)
	if doc.status != "Pending HoD Approval":
		frappe.throw(_("Demand is not awaiting HoD approval."))
	now = now_datetime()
	doc.status = "Rejected"
	doc.rejected_by = frappe.session.user
	doc.rejected_at = now
	doc.rejection_reason = text
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_finance(demand_name: str | None = None):
	"""Pending Finance Approval → Approved. C4–C5: budget check, snapshot, reservation."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_FINANCE_REVIEWER)
	if doc.status != "Pending Finance Approval":
		frappe.throw(_("Demand is not awaiting finance approval."))
	_ensure_not_self_approving(doc)
	if not doc.budget_line:
		frappe.throw(_("Budget Line is required for finance approval."))
	chk = check_available_budget(doc.budget_line, flt(doc.total_amount))
	if not chk.get("ok"):
		frappe.throw(_(chk.get("message") or _("Insufficient available budget.")), title=_("Finance approval"))
	chk_data = chk.get("data") or {}
	now = now_datetime()
	doc.available_budget_at_check = flt(chk_data.get("amount_available"))
	doc.budget_check_datetime = now
	business_id = (getattr(doc, "demand_id", None) or "").strip() or None
	res = create_reservation(
		doc.budget_line,
		"Demand",
		doc.name,
		flt(doc.total_amount),
		actor=frappe.session.user,
		source_business_id=business_id,
	)
	if not res.get("ok"):
		frappe.throw(_(res.get("message") or _("Reservation creation failed.")), title=_("Finance approval"))
	res_data = res.get("data") or {}
	doc.reservation_reference = res_data.get("reservation_id")
	doc.reservation_status = "Reserved"
	doc.status = "Approved"
	doc.finance_approved_by = frappe.session.user
	doc.finance_approved_at = now
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def return_from_finance(demand_name: str | None = None, reason: str | None = None):
	"""Pending Finance Approval → Draft."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	text = _require_reason(reason, _("Return reason"))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_FINANCE_REVIEWER)
	if doc.status != "Pending Finance Approval":
		frappe.throw(_("Demand is not awaiting finance approval."))
	now = now_datetime()
	doc.status = "Draft"
	doc.return_reason = text
	doc.returned_by = frappe.session.user
	doc.returned_at = now
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_from_finance(demand_name: str | None = None, rejection_reason: str | None = None):
	"""Pending Finance Approval → Rejected."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	text = _require_reason(rejection_reason, _("Rejection reason"))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_FINANCE_REVIEWER)
	if doc.status != "Pending Finance Approval":
		frappe.throw(_("Demand is not awaiting finance approval."))
	now = now_datetime()
	doc.status = "Rejected"
	doc.rejected_by = frappe.session.user
	doc.rejected_at = now
	doc.rejection_reason = text
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def cancel_demand(demand_name: str | None = None, cancellation_reason: str | None = None):
	"""Draft / Pending HoD / Pending Finance / Approved → Cancelled."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	text = _require_reason(cancellation_reason, _("Cancellation reason"))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	if doc.status not in (
		"Draft",
		"Pending HoD Approval",
		"Pending Finance Approval",
		"Approved",
		"Rejected",
	):
		frappe.throw(_("This demand cannot be cancelled in its current state."))
	_require_cancel_authority(doc)
	if doc.status == "Approved":
		reservation_id = (doc.reservation_reference or "").strip()
		if not reservation_id:
			lookup = get_active_reservation_for_source("Demand", doc.name)
			if lookup.get("ok"):
				reservation_id = ((lookup.get("data") or {}).get("reservation_id") or "").strip()
		if reservation_id:
			release = release_reservation(
				reservation_id,
				reason=text,
				actor=frappe.session.user,
			)
			if not release.get("ok"):
				err_code = release.get("error_code") or ""
				if err_code not in ("RESERVATION_NOT_ACTIVE",):
					frappe.throw(
						_(release.get("message") or _("Could not release reservation.")),
						title=_("Cancellation"),
					)
			doc.reservation_status = "Released"
	now = now_datetime()
	doc.status = "Cancelled"
	doc.cancellation_reason = text
	doc.cancelled_by = frappe.session.user
	doc.cancelled_at = now
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def mark_planning_ready(demand_name: str | None = None):
	"""Approved → Planning Ready."""
	if not demand_name:
		frappe.throw(_("Demand name is required."))
	require_demand_write(demand_name)
	doc = frappe.get_doc("Demand", demand_name)
	doc.check_permission("write")
	_require_roles(ROLE_PROCUREMENT_PLANNER)
	if doc.status != "Approved":
		frappe.throw(_("Only Approved demands can be marked Planning Ready."))
	doc.status = "Planning Ready"
	doc.planning_status = "Planning Ready"
	_save_doc(doc)
	return {"name": doc.name, "status": doc.status}
