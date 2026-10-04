# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The trusted clock for Proceedings (PRC-CHG-001 v0.9 §16 "no client clock";
BOP-CHG-001 v0.10 plan D3). Tests inject `frappe.flags.kt_prc_clock`; a
browser world on a test environment reads the shared test instant; production
reads the site clock. Callers never pass their own time for a trusted instant."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_prc_clock", None)
	if injected:
		return get_datetime(injected)
	from kentender_core.services.test_clock import current_instant

	instant = current_instant()
	return get_datetime(instant) if instant else now_datetime()
