# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic display formats for the human-readable Tender documents.

These reproduce the Tenders serializer's established display vocabulary
("30 September 2027", "27 May 2027, 17:00 EAT", "500,000.00") without any
locale, clock or Frappe dependency, so the curation fixture and the
production renderer format the same canonical fact identically.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from kentender_procurement.std_templates.compiler.canonical import decimal_text, to_decimal

MONTHS = (
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
)
EAT = timezone(timedelta(hours=3))


def long_date(iso: str) -> str:
	if not iso:
		return ""
	d = date.fromisoformat(iso[:10])
	return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def eat_datetime(iso: str) -> str:
	if not iso:
		return ""
	dt = datetime.fromisoformat(iso).astimezone(EAT)
	return f"{dt.day} {MONTHS[dt.month - 1]} {dt.year}, {dt.hour:02d}:{dt.minute:02d} EAT"


def eat_date(iso: str) -> str:
	"""The EAT calendar date (ISO) of an ISO date-time."""
	return datetime.fromisoformat(iso).astimezone(EAT).date().isoformat()


def add_days(iso_date_value: str, days: int) -> str:
	return (date.fromisoformat(iso_date_value) + timedelta(days=int(days))).isoformat()


def money(value: str, *, field: str = "amount") -> str:
	return f"{to_decimal(value, field=field).quantize(Decimal('0.01')):,.2f}"


def number(value) -> str:
	"""Integral values without a decimal point; others without trailing zeros."""
	if value is None or value == "":
		return ""
	if isinstance(value, int) and not isinstance(value, bool):
		return str(value)
	return decimal_text(to_decimal(str(value), field="number"))
