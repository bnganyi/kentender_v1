# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Display values for Bid Opening (BOP-CHG-001 v0.10 §10: "12 Jun 2027, 11:00
EAT", "10:55", "11:00:41"). Formatted on the server so every surface shows
the same words."""

from __future__ import annotations

from frappe.utils import get_datetime

from kentender_core.utils.display import display_datetime


def when(value) -> str:
	return display_datetime(value) if value else ""


def time(value) -> str:
	return get_datetime(value).strftime("%H:%M") if value else ""


def time_seconds(value) -> str:
	return get_datetime(value).strftime("%H:%M:%S") if value else ""
