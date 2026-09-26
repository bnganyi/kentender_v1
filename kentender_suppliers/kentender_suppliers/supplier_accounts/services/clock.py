# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One trusted clock for Supplier Accounts (BDS-CHG-001 v0.8 plan D18).
Tests inject `frappe.flags.kt_accounts_clock`; seeds freeze the process
clock with `kentender_core.seeds.clock.at`; production reads the site clock."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_accounts_clock", None)
	if injected:
		return get_datetime(injected)
	return now_datetime()
