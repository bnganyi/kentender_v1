# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 plan (registration.py): a new supplier creates their own
login with Frappe's website sign-up, then sets up the Account. With sign-up
off, the login page has no way to create a login and a new supplier is
stuck. Sign-up only creates a Website User; it grants no internal access."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.get_single_value("Website Settings", "disable_signup"):
		frappe.db.set_single_value("Website Settings", "disable_signup", 0)
