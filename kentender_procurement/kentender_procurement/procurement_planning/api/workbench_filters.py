# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP3 workbench filters metadata API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.workbench_filter_metadata import (
	get_workbench_filter_metadata,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"queue": "",
		"total": 0,
		"facets": {},
	}


@frappe.whitelist()
def get_pp_workbench_filter_metadata(
	queue: str,
	include_test_data: int = 0,
	search: str | None = None,
) -> dict[str, Any]:
	"""Return queue-scoped filter options/counts for the workbench toolbar."""
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
	return get_workbench_filter_metadata(
		queue=queue,
		actor=frappe.session.user,
		include_test_data=bool(cint(include_test_data or 0)),
		search=search,
	)
