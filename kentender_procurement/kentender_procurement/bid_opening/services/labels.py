# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Display values for Bid Opening (BOP-CHG-001 v0.10 §10: "12 Jun 2027, 11:00
EAT", "10:55", "11:00:41"). Formatted on the server so every surface shows
the same words."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from frappe.utils import cstr, get_datetime

from kentender_core.utils.display import display_datetime


def when(value) -> str:
	return display_datetime(value) if value else ""


def when_seconds(value) -> str:
	"""``12 Jun 2027, 11:10:30 EAT`` — the boards show seconds for the instants
	a member acted at (completion, a finished record; FU-BOP-25)."""
	if not value:
		return ""
	from zoneinfo import ZoneInfo

	from frappe.utils import format_datetime, get_system_timezone

	moment = get_datetime(value)
	try:
		zone = moment.replace(tzinfo=ZoneInfo(get_system_timezone())).tzname() or ""
	except Exception:
		zone = ""
	return f"{format_datetime(moment, 'd MMM y, HH:mm:ss')} {zone}".strip()


def time(value) -> str:
	return get_datetime(value).strftime("%H:%M") if value else ""


def time_seconds(value) -> str:
	return get_datetime(value).strftime("%H:%M:%S") if value else ""


def money(amount, currency: str = "KES") -> str:
	"""BOP-CHG-001 v0.10 §10: "KES 46,400,000.00"."""
	try:
		value = Decimal(cstr(amount if amount not in (None, "") else "0"))
	except InvalidOperation:
		return cstr(amount)
	return f"{cstr(currency) or 'KES'} {value:,.2f}"


def security(given: dict | None) -> str:
	"""§10: "KES 500,000.00, KCB/TG/2027/8841"; empty when none was given."""
	if not given:
		return ""
	parts = [money(given.get("amount"), given.get("currency") or "KES")] if given.get("amount") else []
	if given.get("reference"):
		parts.append(cstr(given["reference"]))
	return ", ".join(parts)


def read_aloud(entry) -> str:
	"""§10: "Afya Digital Supplies Limited; KES 46,400,000.00; tender security given: KES 500,000.00, KCB/TG/2027/8841"."""
	text = f"{entry.bidder_name}; {money(entry.submitted_total, entry.currency)}"
	return f"{text}; tender security given: {entry.security_given}" if entry.security_given else text
