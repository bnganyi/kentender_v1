# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The trusted clock for Bid Opening (BOP-CHG-001 v0.10 §7 "uses trusted server
time"; plan D3). Tests inject `frappe.flags.kt_bop_clock`; a browser world on
a test environment reads the shared test instant; production reads the site
clock. Proceedings reads the same instant through the shared test clock."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_bop_clock", None)
	if injected:
		return get_datetime(injected)
	from kentender_core.services.test_clock import current_instant

	instant = current_instant()
	return get_datetime(instant) if instant else now_datetime()
