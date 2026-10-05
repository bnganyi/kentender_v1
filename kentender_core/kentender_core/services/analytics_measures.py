"""ANL-CHG-001 v0.8 §4A, §5.4, §5.5 — the arithmetic of Procurement Analytics.

Pure functions, no database and no framework import, so every rule is testable
with plain values. Owners return facts (`analytics_contract`); this module
turns facts into the figures the page shows. The browser computes none of them
(ANL §16).
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable

# §4A ANL-M-02: waiting bands, from the owner's recorded `since` to the read time.
BANDS: tuple[tuple[str, str, int, int | None], ...] = (
	("0_7", "0–7 days", 0, 7),
	("8_30", "8–30 days", 8, 30),
	("31_90", "31–90 days", 31, 90),
	("over_90", "Over 90 days", 91, None),
)

AXIS_DEFAULT_MAX = 60
AXIS_STEP = 10


def _day(value: Any) -> date:
	return value.date() if isinstance(value, datetime) else value


def calendar_days(start: Any, end: Any) -> int:
	"""§5.4 rule 2: the difference between the local calendar dates of two
	site-time instants, a whole number of days, zero or more. ``ValueError``
	when ``end`` falls before ``start`` (a data fault the caller excludes and
	marks incomplete; Analytics never shows a negative elapsed time)."""
	days = (_day(end) - _day(start)).days
	if days < 0:
		raise ValueError("end precedes start")
	return days


def band_key(days: int) -> str:
	"""§4A ANL-M-02 band for a waiting time in whole days."""
	for key, _label, low, high in BANDS:
		if days >= low and (high is None or days <= high):
			return key
	raise ValueError(f"negative waiting time: {days}")


def band_label(key: str) -> str:
	return next(label for k, label, _low, _high in BANDS if k == key)


def _month_start(day: date, back: int) -> date:
	index = day.year * 12 + (day.month - 1) - back
	return date(index // 12, index % 12 + 1, 1)


def window_months(at: datetime) -> list[dict[str, Any]]:
	"""§5.4 rule 1: the twelve calendar months ending with the month that
	contains the read time, oldest first, in site time. The current month is
	labelled ``to date``."""
	today = _day(at)
	months = []
	for back in range(11, -1, -1):
		first = _month_start(today, back)
		last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
		label = f"{calendar.month_abbr[first.month]} {first.year}"
		months.append({
			"key": f"{first.year}-{first.month:02d}", "label": label + (" (to date)" if back == 0 else ""),
			"start": first, "end": last,
		})
	return months


def in_window(instant: Any, at: datetime) -> bool:
	if instant is None:
		return False
	months = window_months(at)
	return months[0]["start"] <= _day(instant) <= months[-1]["end"]


def month_counts(instants: Iterable[Any], at: datetime) -> list[int]:
	"""§4A ANL-M-03: events per month slot of the window, twelve numbers."""
	months = window_months(at)
	counts = [0] * 12
	for instant in instants:
		if instant is None:
			continue
		day = _day(instant)
		for index, month in enumerate(months):
			if month["start"] <= day <= month["end"]:
				counts[index] += 1
				break
	return counts


def day_phrase(days: int | float) -> str:
	"""``1 day``, ``8.5 days``, ``26 days``."""
	text = f"{days:.1f}" if isinstance(days, float) and days != int(days) else f"{int(days)}"
	return f"{text} day" if text == "1" else f"{text} days"


def step_stats(values: list[int]) -> dict[str, Any] | None:
	"""§5.4 rule 3: number completed, median, shortest and longest. With an
	even number of values the median is the mean of the two middle values,
	shown with one decimal place only when it ends in .5. ``None`` when no
	step completed."""
	if not values:
		return None
	ordered = sorted(values)
	size = len(ordered)
	if size % 2:
		median: int | float = ordered[size // 2]
	else:
		total = ordered[size // 2 - 1] + ordered[size // 2]
		median = total // 2 if total % 2 == 0 else total / 2
	return {"completed": size, "median": median, "shortest": ordered[0], "longest": ordered[-1]}


def axis_max(longest_values: Iterable[int]) -> int:
	"""§10A.3: the shared axis runs 0 to 60 days, ticks every 10; it only
	widens, in steps of 10, when a recorded step is longer than that."""
	peak = max(list(longest_values) or [0])
	return max(AXIS_DEFAULT_MAX, -(-peak // AXIS_STEP) * AXIS_STEP)


def percent_half_up(covered: Decimal, planned: Decimal) -> int | None:
	"""§5.5 rule 3: Covered ÷ Planned × 100, rounded half up to a whole number.
	``None`` when Planned is zero (no percentage is shown)."""
	if planned is None or planned <= 0:
		return None
	return int((covered * 100 / planned).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def kes(amount: Decimal) -> str:
	"""§5.5 rule 1: ``KES 55,500,000``; the two decimal places appear only
	when the cents are not zero, ``KES 7,185,000.50``. Negative amounts keep
	a leading minus (Analytics shows none today)."""
	amount = Decimal(amount)
	cents = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	if cents == cents.to_integral_value():
		return f"KES {int(cents):,}"
	return f"KES {cents:,.2f}"


def kes_tick(amount: Decimal) -> str:
	"""§5.5 rule 1: an axis tick label may abbreviate millions, ``KES 20 m``."""
	millions = Decimal(amount) / Decimal(1_000_000)
	text = f"{millions:f}".rstrip("0").rstrip(".") if millions != millions.to_integral_value() else f"{int(millions)}"
	return f"KES {text} m"


def count_phrase(count: int, singular: str, plural: str) -> str:
	return f"{count} {singular if count == 1 else plural}"


def join_and(items: list[str]) -> str:
	"""``a``, ``a and b``, ``a, b and c`` (no serial comma)."""
	if len(items) <= 1:
		return "".join(items)
	return ", ".join(items[:-1]) + " and " + items[-1]
