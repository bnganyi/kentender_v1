# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Consumption Velocity endpoint.

Aggregates monthly Budget Reservation activity for the last N calendar months
and computes a month-on-month trend note.  When no reservation data exists the
endpoint returns zero-filled buckets with data_source="none".
"""
from __future__ import annotations

import calendar

import frappe
from frappe.utils import add_months, getdate


_MONTH_ABBR = [
	"JAN", "FEB", "MAR", "APR", "MAY", "JUN",
	"JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]


@frappe.whitelist()
def get_consumption_velocity(months: int = 7) -> dict:
	"""Return monthly reservation-activity totals for the last *months* months.

	Response shape::

	    {
	      "data_source": "reservation" | "none",
	      "months": [
	        {"label": "JAN", "year": 2026, "amount": 1_234_567.0, "pct": 62.5},
	        ...                                      # oldest → newest
	      ],
	      "trend_note": "Activity up 14% this month vs last month."
	    }

	``pct`` is the bar height relative to the maximum bucket (max = 100).
	"""
	months = max(1, int(months))

	# ── Build the ordered list of (year, month) buckets oldest → newest ────────
	today = getdate()
	buckets: list[tuple[int, int]] = []
	for i in range(months - 1, -1, -1):
		d = add_months(today, -i)
		buckets.append((d.year, d.month))

	# ── Query Budget Reservation activity grouped by month ─────────────────────
	oldest = buckets[0]
	# Earliest day of the oldest bucket
	oldest_date = f"{oldest[0]}-{oldest[1]:02d}-01"

	rows = frappe.db.sql(
		"""
		SELECT
		    YEAR(created_at)  AS yr,
		    MONTH(created_at) AS mo,
		    SUM(amount)       AS total
		FROM `tabBudget Reservation`
		WHERE created_at >= %(oldest_date)s
		GROUP BY YEAR(created_at), MONTH(created_at)
		""",
		{"oldest_date": oldest_date},
		as_dict=True,
	)

	# Build lookup: (year, month) → amount
	lookup: dict[tuple[int, int], float] = {
		(int(r.yr), int(r.mo)): float(r.total or 0)
		for r in rows
	}

	has_data = bool(lookup)

	# ── Assemble ordered month list ─────────────────────────────────────────────
	amounts = [lookup.get(b, 0.0) for b in buckets]
	max_amount = max(amounts) if amounts else 0.0

	month_entries = []
	for (yr, mo), amount in zip(buckets, amounts):
		pct = round((amount / max_amount) * 100.0, 1) if max_amount else 0.0
		month_entries.append({
			"label": _MONTH_ABBR[mo - 1],
			"year": yr,
			"amount": amount,
			"pct": pct,
		})

	# ── Trend note ──────────────────────────────────────────────────────────────
	trend_note = _build_trend_note(amounts)

	return {
		"data_source": "reservation" if has_data else "none",
		"months": month_entries,
		"trend_note": trend_note,
	}


def _build_trend_note(amounts: list[float]) -> str:
	"""Compute a plain-English trend note from the monthly amounts list.

	Compares the most recent complete month (second-to-last bucket) to the
	month before it.  The current month is excluded from the comparison
	because it is always partial.
	"""
	if len(amounts) < 2:
		return "Insufficient data for trend analysis."

	# Use the two most recent *completed* months (exclude current partial month)
	# If the window is 7: index -2 = last completed, index -3 = prev completed
	if len(amounts) >= 3:
		current  = amounts[-2]   # last completed month
		previous = amounts[-3]   # the month before
	else:
		current  = amounts[-1]
		previous = amounts[-2]

	if previous == 0 and current == 0:
		return "No reservation activity recorded for the current period."
	if previous == 0:
		return "Activity recorded this period — no prior month for comparison."

	delta_pct = round((current - previous) / previous * 100.0, 0)

	if delta_pct > 0:
		return f"Activity up {int(delta_pct)}% vs the previous month."
	elif delta_pct < 0:
		return f"Activity down {int(abs(delta_pct))}% vs the previous month."
	else:
		return "Activity unchanged vs the previous month."
