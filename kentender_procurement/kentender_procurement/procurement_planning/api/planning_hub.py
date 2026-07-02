# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP4 — Planning Hub whitelisted APIs."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.planning_hub_view_model import (
	get_planning_hub_shell_data,
)
from kentender_procurement.procurement_planning.services.procurement_plans_view_model import (
	get_planning_hub_plans_page,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"active_plan": {"has_active_plan": False},
		"hero_stats": [],
		"header_actions": {},
		"cta_actions": {},
		"ledger_preview": {"total": 0, "start": 0, "limit": 20, "rows": []},
	}


def _plans_fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"total": 0,
		"start": 0,
		"limit": 20,
		"rows": [],
	}


def _read_gate(fail):
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to the Procurement Planning hub."),
		fail=fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)


@frappe.whitelist()
def get_pp_planning_hub_shell_data(
	procuring_entity: str | None = None,
	fiscal_year: str | int | None = None,
) -> dict[str, Any]:
	"""Return Planning Hub v4 shell data for /desk/planning-hub."""
	role_key, denied = _read_gate(_fail)
	if denied:
		return denied
	_ = role_key
	return get_planning_hub_shell_data(
		actor=frappe.session.user,
		procuring_entity=procuring_entity,
		fiscal_year=fiscal_year,
	)


@frappe.whitelist()
def get_pp_planning_hub_plans_page(
	search: str | None = None,
	start: int = 0,
	limit: int = 20,
) -> dict[str, Any]:
	"""Return paginated procurement plan ledger rows for the Planning Hub."""
	role_key, denied = _read_gate(_plans_fail)
	if denied:
		return denied
	_ = role_key
	return get_planning_hub_plans_page(
		actor=frappe.session.user,
		search=search,
		start=int(start or 0),
		limit=int(limit or 20),
	)
