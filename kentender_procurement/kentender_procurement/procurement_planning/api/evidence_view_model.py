# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-003 — PP3 Evidence view-model API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.evidence_view_model import (
	get_evidence_view_model,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


@frappe.whitelist()
def get_pp_evidence_view_model(package_code: str | None = None) -> dict[str, Any]:
	"""Return canonical PP3 Evidence view-model for one package."""
	role_key, denied = pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_EVIDENCE_READ,
		message=_("You do not have access to the Procurement Planning evidence timeline."),
		fail=_fail,
		installed_doctype="Procurement Package",
		require_planning_read=True,
		require_demand_read=False,
		require_package_read=False,
	)
	if denied:
		return denied
	if role_key:
		pass
	code = (package_code or "").strip()
	if not code:
		return _fail(code="NOT_FOUND", message=_("Package not found."))
	return get_evidence_view_model(package_code=code, actor=frappe.session.user)
