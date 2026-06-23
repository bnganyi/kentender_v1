# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-002 — Unified Workbench item view-model API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"queue": "",
		"total": 0,
		"limit": 0,
		"start": 0,
		"items": [],
	}


@frappe.whitelist()
def get_pp_workbench_item_view_model(
	queue: str,
	limit: int = 20,
	start: int = 0,
) -> dict[str, Any]:
	"""Return canonical PP3 workbench items for one queue."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_QUEUE_READ,
		message=_("You do not have access to Procurement Planning workbench queues."),
		fail=_fail,
		installed_doctype="Procurement Plan",
		require_planning_read=True,
		require_demand_read=False,
		require_package_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	return get_workbench_item_view_model(
		queue=queue,
		actor=frappe.session.user,
		limit=limit,
		start=start,
	)
