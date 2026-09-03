# Server-side display formatting for the System setup surface.
#
# KT-STD-001 §3: dates display in the site timezone, and every label the UI
# shows comes from the server. The artboards (AUTH-DES/CFG-DES) fix the
# formats: dates as "1 Jul 2026", instants as "25 Nov 2026, 23:59 EAT".

from __future__ import annotations

from zoneinfo import ZoneInfo

from frappe.utils import format_datetime, formatdate, get_datetime, get_system_timezone


def display_date(value) -> str:
	"""``1 Jul 2026`` — the artboard date format, empty for empty."""
	if not value:
		return ""
	return formatdate(value, "d MMM y")


def display_datetime(value) -> str:
	"""``25 Nov 2026, 23:59 EAT`` — site-timezone instant with abbreviation."""
	if not value:
		return ""
	moment = get_datetime(value)
	text = format_datetime(moment, "d MMM y, HH:mm")
	try:
		abbreviation = moment.replace(tzinfo=ZoneInfo(get_system_timezone())).tzname() or ""
	except Exception:
		abbreviation = ""
	return f"{text} {abbreviation}".strip()


def display_period(start, end) -> str:
	"""``1 Jul 2026 – 30 Jun 2027`` — a closed date range."""
	if not (start and end):
		return ""
	return f"{display_date(start)} – {display_date(end)}"
