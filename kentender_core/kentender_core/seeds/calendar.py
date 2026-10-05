# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical world's calendar: two financial years read as at one instant
(two-year seed world plan D1, D8; owner, 4 Oct 2026: "Decisions for the
owner: recommendations accepted").

- **Year 1**, FY 2026/27, is the year being carried out: its budget, needs,
  departmental plans and Annual Plan are always built, and the requisitions,
  Tenders and later stages run against that plan.
- **Year 2**, FY 2027/28, is the year being prepared: budget, needs,
  departmental plans and Annual Plan only, never further.

Year 2 keeps the instants the module seeds have always used (needs on
24 Nov 2026, the Plan published 10 Dec 2026). Year 1's planning history is
the same journey **364 days (52 weeks) earlier**, so every event keeps its
weekday and its spacing from its neighbours (one calendar year back would
move each date a weekday earlier, putting the Plan's signature on a Sunday).
Year 1's execution (requisitions to award) keeps its own fixed instants in
March–June 2027, which fall inside FY 2026/27.

Every recorded event is at or before ``AS_AT``; every live deadline is after
it. A test site runs its live pages on ``AS_AT`` (the site test clock)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

#: The story's "now" (plan D1): the read time of HOME-CHG-001 v0.6 H10–H12
#: and ANL-CHG-001 v0.8 dataset A1.
AS_AT = "2027-06-18 10:00:00"

#: Year 1's planning history is Year 2's moved back this many days (plan D8).
YEAR1_SHIFT_DAYS = -364


@dataclass(frozen=True)
class Year:
	key: str  # "year1" | "year2"
	fiscal_year: str  # the ERPNext Fiscal Year name, e.g. "2026-2027"
	start_year: int
	label: str  # "FY 2026/27"
	shift_days: int  # applied to the module seeds' Year 2 instants

	def at(self, instant: str) -> str:
		"""`instant` (a Year 2 fixture instant, ``YYYY-MM-DD`` or
		``YYYY-MM-DD HH:MM:SS``) moved into this year, in the same form."""
		return shift(instant, self.shift_days)


YEAR1 = Year("year1", "2026-2027", 2026, "FY 2026/27", YEAR1_SHIFT_DAYS)
YEAR2 = Year("year2", "2027-2028", 2027, "FY 2027/28", 0)
YEARS = (YEAR1, YEAR2)


def shift(instant: str, days: int) -> str:
	"""`instant` moved by `days`, keeping its form (date or datetime string)."""
	if not instant or not days:
		return instant
	text = str(instant)
	if len(text) <= 10:
		return (date.fromisoformat(text) + timedelta(days=days)).isoformat()
	moved = datetime.fromisoformat(text) + timedelta(days=days)
	return moved.strftime("%Y-%m-%d %H:%M:%S")


def year(key: str) -> Year:
	for candidate in YEARS:
		if candidate.key == key:
			return candidate
	raise ValueError(f"Unknown seed year {key!r}; expected one of {[y.key for y in YEARS]}")
