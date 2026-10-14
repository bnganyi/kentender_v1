# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The trusted clock for Contract Management (CM-CHG-001 v0.8 §7 "trusted time", §12; plan D19).

Tests inject `frappe.flags.kt_cm_clock`; a test environment reads the shared test instant (so a supplier's timeliness is judged
by the same clock as every internal action, never the browser's or the real date); production reads the site clock. Instants
are site time; UTC appears only in cross-module payloads (AGENTS.md §4.4). A recording time is never back-dated to the
physical event (§12): callers record the observed time as its own fact and `now()` as the recorded time."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_cm_clock", None)
	if injected:
		return get_datetime(injected)
	from kentender_core.services.test_clock import current_instant

	instant = current_instant()
	return get_datetime(instant) if instant else now_datetime()


def when(value) -> str:
	"""The boards' display form: "2 Jul 2027, 09:01 EAT"."""
	return get_datetime(value).strftime("%-d %b %Y, %H:%M") + " EAT" if value else ""
