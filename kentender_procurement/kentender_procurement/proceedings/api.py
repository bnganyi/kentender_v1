# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Procurement meetings register (OVS-CHG-001 v0.6 §11, §13; PRC-CHG-001
v0.11 §7, §9). One read-only endpoint; Proceedings has no other Desk API (an
owner reads its own Proceeding through its own screens)."""

from __future__ import annotations

from typing import Any

import frappe


@frappe.whitelist(methods=["GET"])
def list_procurement_meetings(type: str = "", department: str = "", state: str = "", date_from: str = "", date_to: str = "", query: str = "", start: int = 0,
		limit: int = 50) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import register

	return register.list_meetings(user=frappe.session.user, type=type, department=department, state=state, date_from=date_from, date_to=date_to, query=query,
		start=start, limit=limit)
