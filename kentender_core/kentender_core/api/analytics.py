"""ANL-CHG-001 v0.8 §7 — the Analytics endpoints. Thin: the work is in
`kentender_core.services.analytics_workspace`."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import analytics_workspace


@frappe.whitelist()
def get_procurement_analytics(tab: str = "overview", fy: str = "", dept: str = "", state: str = "", search: str = "",
		cursor: str | None = None) -> dict[str, Any]:
	"""Procurement Analytics for the signed-in user. The route carries `tab`, `fy`, `dept` and `state`; `search` and
	`cursor` are component state and never enter the URL (ANL §9.1)."""
	return analytics_workspace.get_workspace(frappe.session.user, tab=tab, fy=fy, dept=dept, state=state, search=search, cursor=cursor)


@frappe.whitelist()
def get_analytics_access() -> dict[str, Any]:
	"""May the signed-in user open Analytics at all? Cheap (no scan); Home's gated link reads it."""
	return analytics_workspace.get_access(frappe.session.user)
