"""HOME-CHG-001 v0.6 — the greeting, the trusted clock and the relative labels Home shows.

HOME §16 forbids computing due labels or Coming up entries in the browser, so
every phrase on the page is made here. Days are site-timezone calendar days
(§5.1 item 4): an instant at 23:59 yesterday is "yesterday" at 00:05 today.
The exact time is always part of the text, never hover-only, and the year is
left out when it is the year of the read. "Overdue" is produced only by a
passed owner deadline (HOME-AC-13): none of these functions takes a received
or since instant and calls it overdue.

Instants are naive datetimes in site time (`kentender_core.utils.instants`).
A deadline may also be a plain date, which means "by the end of that day".
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import formatdate, get_datetime, getdate, now_datetime

from kentender_core.services import test_clock
from kentender_core.utils.display import display_datetime

COMING_UP_DAYS = 14
# HOME §5 leaves "recently" undefined. 30 calendar days is a build interpretation
# pending the owner's confirmation (FU-HOME-23); it bounds the history every
# Show more re-reads.
COMPLETED_DAYS = 30


def now() -> datetime:
	"""The trusted read instant: the shared test-environment clock when a test
	world has set one (the 2027 canonical timeline), else the site clock."""
	instant = test_clock.current_instant()
	return get_datetime(instant) if instant else now_datetime()


def greeting(at: datetime) -> str:
	"""§5.1 item 2: before 12:00, 12:00 to 16:59, from 17:00."""
	hour = get_datetime(at).hour
	if hour < 12:
		return _("Good morning")
	if hour < 17:
		return _("Good afternoon")
	return _("Good evening")


def long_instant(value: Any) -> str:
	"""``18 June 2027, 10:00 EAT`` — the Updated line and owner sentences."""
	if not value:
		return ""
	moment = get_datetime(value)
	abbreviation = display_datetime(moment).rsplit(" ", 1)[-1]
	return f"{formatdate(moment.date(), 'd MMMM y')}, {moment:%H:%M} {abbreviation}".strip()


def _is_date_only(value: Any) -> bool:
	return isinstance(value, date) and not isinstance(value, datetime)


def _as_instant(value: Any) -> tuple[datetime, bool]:
	"""(instant, has_time). A plain date is a date-only deadline."""
	if _is_date_only(value):
		return datetime(value.year, value.month, value.day), False
	if isinstance(value, str) and len(value.strip()) <= 10:
		day = getdate(value)
		return datetime(day.year, day.month, day.day), False
	return get_datetime(value), True


def _days(value: Any, at: datetime) -> int:
	"""Calendar days from the read date to the value's date (negative = past)."""
	instant, _time = _as_instant(value)
	return (instant.date() - get_datetime(at).date()).days


def _day_text(value: Any, at: datetime) -> str:
	instant, _time = _as_instant(value)
	same_year = instant.year == get_datetime(at).year
	return formatdate(instant.date(), "d MMMM" if same_year else "d MMMM y")


def _exact(value: Any, at: datetime) -> str:
	"""``16 June, 11:00`` for an instant, ``16 June`` for a date."""
	instant, has_time = _as_instant(value)
	text = _day_text(instant, at)
	return f"{text}, {instant:%H:%M}" if has_time else text


def _plural_days(count: int) -> str:
	return _("{0} day").format(count) if count == 1 else _("{0} days").format(count)


def entered(verb: str, value: Any, at: datetime) -> str:
	"""My work timing: ``Received 2 days ago (16 June, 11:00)``. ``verb`` is
	the owner's own word (Received, Submitted)."""
	ago = -_days(value, at)
	exact = _exact(value, at)
	if ago <= 0:
		return _("{0} today ({1})").format(verb, exact)
	if ago == 1:
		return _("{0} yesterday ({1})").format(verb, exact)
	return _("{0} {1} ago ({2})").format(verb, _plural_days(ago), exact)


def stated(label: str, value: Any, at: datetime) -> str:
	"""A dated fact on its own line: ``Evaluation report delivered 16 June, 14:07``. ``label`` is the owner's own words."""
	return f"{label} {_exact(value, at)}"


def _since(word: str, value: Any, at: datetime) -> str:
	ago = max(-_days(value, at), 0)
	exact = _exact(value, at)
	if ago == 0:
		return _("{0} today (since {1})").format(word, exact)
	return _("{0} {1} (since {2})").format(word, _plural_days(ago), exact)


def waiting(value: Any, at: datetime) -> str:
	"""Waiting on others: ``Waiting 2 days (since 16 June, 15:30)``."""
	return _since(_("Waiting"), value, at)


def outstanding(value: Any, at: datetime) -> str:
	"""Records you oversee: ``Outstanding 15 days (since 3 June, 10:00)``."""
	return _since(_("Outstanding"), value, at)


def is_overdue(deadline: Any, at: datetime) -> bool:
	"""True only when an owner deadline has passed. A date means the end of
	that day; a datetime is overdue once that time has passed."""
	if not deadline:
		return False
	instant, has_time = _as_instant(deadline)
	moment = get_datetime(at)
	return instant < moment if has_time else instant.date() < moment.date()


def due(deadline: Any, at: datetime) -> str:
	"""§5.1 item 4: a deadline within 14 days is relative, a passed one reads
	Overdue since, anything later shows its date."""
	if not deadline:
		return ""
	text = _day_text(deadline, at)
	if is_overdue(deadline, at):
		return _("Overdue since {0}").format(text)
	days = _days(deadline, at)
	if days == 0:
		return _("Due today ({0})").format(text)
	if days == 1:
		return _("Due tomorrow ({0})").format(text)
	if days <= COMING_UP_DAYS:
		return _("Due in {0} days ({1})").format(days, text)
	return _("Due {0}").format(text)


def in_coming_up_window(value: Any, at: datetime) -> bool:
	"""§5.1 item 3: the read date and the 14 calendar days after it, in site
	time. An event earlier today still counts; yesterday's does not."""
	if not value:
		return False
	return 0 <= _days(value, at) <= COMING_UP_DAYS


def coming_up(value: Any, at: datetime) -> tuple[str, str]:
	"""(badge, exact) for a Coming up row: ``("In 7 days", "25 June, 11:00")``."""
	days = _days(value, at)
	if days <= 0:
		badge = _("Today")
	elif days == 1:
		badge = _("Tomorrow")
	else:
		badge = _("In {0} days").format(days)
	return badge, _exact(value, at)


def in_completed_window(value: Any, at: datetime) -> bool:
	"""Recently completed actions: the last 30 calendar days of site time, today
	included. An instant later than the read is not a completed action."""
	if not value:
		return False
	return -COMPLETED_DAYS <= _days(value, at) <= 0


def completed_sentence(did: str, completed_at: Any, *, follow: str = "") -> str:
	"""``You approved this Tender package on 16 June 2027, 15:30 EAT.`` plus an
	optional follow-on clause the owner supplies (see `awaiting`)."""
	text = _("You {0} on {1}.").format(did, long_instant(completed_at))
	return f"{text} {follow}".strip() if follow else text


def awaiting(stage: str, holder: str) -> str:
	"""``It is awaiting publication authorisation by Amina Hassan.``"""
	return _("It is awaiting {0} by {1}.").format(stage, holder)
