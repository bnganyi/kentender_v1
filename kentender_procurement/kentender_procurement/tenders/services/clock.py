# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One clock for every Tenders command. Production reads the site clock;
the §13 seeds and the §15.3 integrity tests inject the exact fixture
instant through `frappe.flags.kt_tenders_clock` so recorded decision times
are the spec's own (KT-STD-001 §8.4A), never now-relative."""

from __future__ import annotations

from datetime import date, datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_tenders_clock", None)
	if injected:
		return get_datetime(injected)
	return now_datetime()


def today() -> date:
	return now().date()
