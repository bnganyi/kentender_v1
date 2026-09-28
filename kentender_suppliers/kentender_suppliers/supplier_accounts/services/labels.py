# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier-facing display values ("18 May 2027", "18 May 2027, 09:00 EAT")."""

from __future__ import annotations

from frappe.utils import formatdate, get_datetime, getdate


def date_label(value) -> str:
	return formatdate(getdate(value), "d MMM yyyy") if value else ""


def datetime_seconds_label(value) -> str:
	"""An audit instant to the second ("19 May 2027, 08:00:00 EAT")."""
	label = datetime_label(value)
	return label.replace(" EAT", f":{get_datetime(value).strftime('%S')} EAT") if label else ""


def datetime_label(value) -> str:
	if not value:
		return ""
	dt = get_datetime(value)
	return f"{formatdate(dt.date(), 'd MMM yyyy')}, {dt.strftime('%H:%M')} EAT"
