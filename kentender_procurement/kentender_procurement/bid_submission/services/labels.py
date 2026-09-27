# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier-facing display values (BDS-CHG-001 v0.8 §10: "12 Jun 2027, 11:00
EAT", "30 Sep 2027", "KES 500,000.00"). Reads format on the server so every
surface shows the same words; machine values stay alongside where a screen
needs them."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from frappe.utils import formatdate, get_datetime, getdate

TIME_ZONE_LABEL = "EAT"


def datetime_label(value) -> str:
	if not value:
		return ""
	dt = get_datetime(value)
	if dt.tzinfo is not None:
		from zoneinfo import ZoneInfo

		from frappe.utils import get_system_timezone

		dt = dt.astimezone(ZoneInfo(get_system_timezone() or "Africa/Nairobi")).replace(tzinfo=None)
	return f"{formatdate(dt.date(), 'd MMM yyyy')}, {dt.strftime('%H:%M')} {TIME_ZONE_LABEL}"


def datetime_seconds_label(value) -> str:
	"""The receipt's instants to the second (BDS-CHG-001 v0.8 §10.1: "10 Jun 2027, 14:31:58 EAT")."""
	if not value:
		return ""
	label = datetime_label(value)
	return label.replace(f" {TIME_ZONE_LABEL}", f":{get_datetime(value).strftime('%S')} {TIME_ZONE_LABEL}") if label else ""


def date_label(value) -> str:
	return formatdate(getdate(value), "d MMM yyyy") if value else ""


def money_label(amount, currency: str = "KES") -> str:
	try:
		value = Decimal(str(amount if amount not in (None, "") else "0"))
	except InvalidOperation:
		return ""
	return f"{currency} {value.quantize(Decimal('0.01')):,.2f}"
