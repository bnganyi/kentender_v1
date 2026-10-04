# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier Account items in the shared Desk My Work queue (BDS-CHG-001 v0.8
§5.14 "Account access suspended"): each Suspended Account is one
**Review suspended supplier account access** item for the current holders
of the Supplier Account Support Officer responsibility. It clears when the
Account is restored — from the decision, never from reading the item."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import next_step as ns
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.labels import datetime_label

TITLE = "Review suspended supplier account access"


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	empty = {"assigned": [], "claimable": [], "waiting": []}
	if not user or user == "Guest" or not authz.is_support_officer(user):
		return empty
	rows = []
	for org in frappe.get_all("Supplier Organisation", filters={"account_status": "Suspended"}, fields=["name", "legal_name", "status_since", "record_version"], order_by="status_since asc", limit_page_length=0):
		rows.append({
			"task_id": f"supplier_accounts.suspended.{org.name}", "task_type": "supplier_accounts.review_suspended_access", "title": TITLE,
			"reference": cstr(org.legal_name), "module": "Supplier Accounts", "stage": "Account access", "fiscal_year": "", "organisation_unit": "",
			"assignment": authz.SUPPORT_ROLE, "status": "Assigned", "received_at": cstr(org.status_since), "due_at": "", "action_label": "Review access",
			"route": ["Form", "Supplier Organisation", org.name], "route_options": {}, "concurrency_token": cstr(org.record_version), "can_claim": False,
			"can_open": True, "comment": "", "since": ns.since(org.status_since, datetime_label(org.status_since)),
		})
	return {**empty, "assigned": rows}
