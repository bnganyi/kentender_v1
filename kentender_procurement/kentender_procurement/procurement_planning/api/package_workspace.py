# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-006 — Package workspace read API."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.package_workspace import (
	get_package_workspace_context,
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
		pp_api_gates.PLANNING_PACKAGE_READ,
		message=_("You do not have access to the Procurement Planning package workspace."),
		fail=_fail,
	)


@frappe.whitelist()
def get_pp_package_workspace(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 package workspace — tab-oriented read context."""
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

	return get_package_workspace_context(code, frappe.session.user)
