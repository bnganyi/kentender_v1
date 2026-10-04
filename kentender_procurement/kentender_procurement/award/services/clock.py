# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The trusted clock for Award (AWD-CHG-001 v0.4 §7 "trusted time"; plan D9).

Tests inject `frappe.flags.kt_awd_clock`; a test environment reads the shared
test instant (so a supplier's timeliness is judged by the same clock as every
internal action, never the browser's or the real date); production reads the
site clock. Instants are site time; UTC appears only in cross-module payloads
(AGENTS.md §4.4)."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_awd_clock", None)
	if injected:
		return get_datetime(injected)
	from kentender_core.services.test_clock import current_instant

	instant = current_instant()
	return get_datetime(instant) if instant else now_datetime()


def when(value) -> str:
	"""The boards' display form: "17 Jun 2027, 09:10 EAT"."""
	return get_datetime(value).strftime("%-d %b %Y, %H:%M") + " EAT" if value else ""
