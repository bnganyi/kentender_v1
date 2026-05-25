# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-014 — Planning journey/handoff read API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.planning_journey_integration import (
	get_planning_journey_handoff_context,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _planning_read_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_EVIDENCE_READ,
		message=_("You do not have access to Procurement Planning journey handoffs."),
		fail=_fail,
	)


@frappe.whitelist()
def get_pp_planning_journey_handoffs(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 journey/handoff read context for a procurement package."""
	role_key, gate_err = _planning_read_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (package_code or "").strip()
	if not code:
		return _fail(
			code="NOT_FOUND",
			message=_("Package not found."),
			role_key=role_key,
		)

	return get_planning_journey_handoff_context(code, frappe.session.user)
