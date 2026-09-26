# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Account-status guards shared by every command (BDS-CHG-001 v0.8 §5.2(5)):
a Suspended Account cannot start, edit, submit, replace or withdraw."""

from __future__ import annotations

import frappe

from kentender_suppliers.supplier_accounts.services.errors import fail

ORGANISATION = "Supplier Organisation"


def status_of(organisation: str) -> str:
	return frappe.db.get_value(ORGANISATION, organisation, "account_status") or ""


def require_not_suspended(organisation: str) -> None:
	if status_of(organisation) == "Suspended":
		fail("BDS_ACCOUNT_SUSPENDED")
