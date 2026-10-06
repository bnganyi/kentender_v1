# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Suspended Supplier Accounts on the Home page (HOME-CHG-001 v0.6, owner decision 5 Oct 2026, FU-HOME-46).

The same work `my_work_provider` puts on My Work (BDS-CHG-001 v0.8 §5.14 "Account access suspended"): each Suspended
Account is one **Review suspended supplier account access** item for the current holders of the Supplier Account Support
Officer responsibility, cleared when the Account is restored, never by reading the item. Home's row leads with the
business name (the Supplier's legal name) and opens the Supplier Organisation record, whose own permission decides who may read it.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import home_entries as he
from kentender_suppliers.supplier_accounts.services import authorization as authz

OWNER = "suppliers"
ACTION = "Review suspended supplier account access"


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	"""My work for a Supplier Account support officer; not applicable (None) to anyone else, and to every other region."""
	if region != he.MY_WORK or not user or user == "Guest" or not authz.is_support_officer(user):
		return None
	return [
		he.make(
			region=he.MY_WORK, owner=OWNER, root=org.name, action_id="review-suspended-access", title=org.legal_name, action=ACTION,
			destination=["Form", "Supplier Organisation", org.name], entered_at=org.status_since, entered_verb="Suspended",
		)
		for org in frappe.get_all("Supplier Organisation", filters={"account_status": "Suspended"}, fields=["name", "legal_name", "status_since"], order_by="status_since asc", limit_page_length=0)
		if org.status_since
	]
