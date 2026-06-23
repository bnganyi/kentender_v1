# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-001 — Active Plan view-model API endpoint."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	get_active_plan_view_model,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"has_active_plan": False,
	}


@frappe.whitelist()
def get_pp_active_plan_view_model(
	procuring_entity: str | None = None,
	fiscal_year: str | int | None = None,
) -> dict[str, Any]:
	"""Return the PP3 active-plan context envelope for Workbench consumers."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to the Procurement Planning active plan context."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return get_active_plan_view_model(
		actor=frappe.session.user,
		procuring_entity=procuring_entity,
		fiscal_year=fiscal_year,
	)
