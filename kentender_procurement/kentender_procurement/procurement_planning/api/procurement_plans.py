# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-002+ — Procurement Plans setup/oversight APIs."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.procurement_plan_create_service import (
	create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.procurement_plan_evidence_view_model import (
	get_procurement_plan_evidence_view_model,
)
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	get_procurement_plan_summary_view_model,
	get_procurement_plans_list_view_model,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"plans": [],
	}


@frappe.whitelist()
def get_pp_procurement_plans_list() -> dict[str, Any]:
	"""Return PP3 Procurement Plans list rows for the setup/oversight surface."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to procurement plans."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return get_procurement_plans_list_view_model(actor=frappe.session.user)


@frappe.whitelist()
def get_pp_procurement_plan_summary(plan_id: str | None = None) -> dict[str, Any]:
	"""Return PP3 selected plan summary for the setup/oversight surface."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to procurement plan details."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return get_procurement_plan_summary_view_model(
		plan_id=plan_id,
		actor=frappe.session.user,
	)


@frappe.whitelist()
def create_pp_procurement_plan(
	procuring_entity: str | None = None,
	fiscal_year: str | int | None = None,
	plan_title: str | None = None,
	currency: str | None = None,
) -> dict[str, Any]:
	"""Create a draft procurement plan from the PP3 Create Plan modal."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to create procurement plans."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return create_procurement_plan(
		procuring_entity=procuring_entity,
		fiscal_year=fiscal_year,
		plan_title=plan_title,
		currency=currency,
		actor=frappe.session.user,
	)


@frappe.whitelist()
def activate_pp_procurement_plan(plan_id: str | None = None) -> dict[str, Any]:
	"""Activate a draft procurement plan (P4-005)."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to activate procurement plans."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	code = (plan_id or "").strip()
	if not code:
		return _fail(code="MISSING_PLAN", message=_("Select a procurement plan to activate."))
	from kentender_procurement.procurement_planning.api.workflow import activate_plan

	try:
		activate_plan(plan_id=code)
	except Exception as exc:
		return _fail(code="ACTIVATE_FAILED", message=str(exc), role_key=role_key or "auditor")
	return get_procurement_plan_summary_view_model(plan_id=code, actor=frappe.session.user)


@frappe.whitelist()
def close_pp_procurement_plan(plan_id: str | None = None) -> dict[str, Any]:
	"""Close an active procurement plan (P4-006)."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to close procurement plans."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	code = (plan_id or "").strip()
	if not code:
		return _fail(code="MISSING_PLAN", message=_("Select a procurement plan to close."))
	from kentender_procurement.procurement_planning.api.workflow import close_plan

	try:
		close_plan(plan_id=code)
	except Exception as exc:
		return _fail(code="CLOSE_FAILED", message=str(exc), role_key=role_key or "auditor")
	return get_procurement_plan_summary_view_model(plan_id=code, actor=frappe.session.user)


@frappe.whitelist()
def get_pp_procurement_plan_evidence_view_model(plan_id: str | None = None) -> dict[str, Any]:
	"""Return plan-level evidence for the PP3 Evidence Drawer (P4-008)."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_EVIDENCE_READ,
		message=_("You do not have access to procurement plan evidence."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return get_procurement_plan_evidence_view_model(
		plan_id=plan_id,
		actor=frappe.session.user,
	)
