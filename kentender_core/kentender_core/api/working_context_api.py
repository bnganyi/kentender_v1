"""CTX-CHG-001 — whitelisted working-context endpoints.

Thin wrappers over :mod:`kentender_core.services.working_context`. Explicit
signatures (no ``**kwargs``) so Frappe filters the transport fields
(``cmd``/``csrf_token``) out of the call itself.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services.working_context import (
	get_module_fy,
	get_working_pe,
	select_module_fy,
	select_working_pe as _select_working_pe,
)


@frappe.whitelist()
def get_working_context(module: str | None = None, requested_pe: str | None = None) -> dict[str, Any]:
	"""The caller's working context: global PE, plus `module`'s remembered FY
	(registry-default eligibility) when a module is named. The PageRail
	switcher calls this with no module; default-eligibility workspaces pass
	theirs. Modules with custom FY eligibility resolve FY through their own
	contracts instead."""
	pe = get_working_pe(requested=requested_pe)
	fy = None
	if module and pe["selected"]:
		fy = get_module_fy(module, procuring_entity=pe["selected"]["id"])
	return {"pe": pe, "fy": fy}


@frappe.whitelist()
def select_working_pe(pe_id: str) -> dict[str, Any]:
	return _select_working_pe(pe_id)


@frappe.whitelist()
def select_module_financial_year(module: str, financial_year: str) -> dict[str, Any]:
	"""Persist `module`'s FY against the registry-default eligibility for the
	caller's working PE. Modules with custom eligibility persist through
	their own endpoints (which call the service with ``offered=``)."""
	pe = get_working_pe()
	if not pe["selected"]:
		frappe.throw("Select a Procuring Entity first.", frappe.ValidationError)
	return select_module_fy(module, financial_year, procuring_entity=pe["selected"]["id"])
