# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical world's calendar.

**v0.7 (two-year seed world, owner 4 Oct 2026).** Two financial years read as at
one instant, 18 June 2027 10:00 EAT (`STORY_AS_AT`, formerly `AS_AT`): Year 1,
FY 2026/27, carried out; Year 2, FY 2027/28, prepared. Every seed instant is
written in that **story's** own coordinates.

**v0.8 (real-date anchor, owner 15 Oct 2026, RA-PROP-001 / SEED-002 v0.8).**
No simulated instant is later than the real clock. A seed run stores an
**anchor**, the world's reference instant, and every story instant is mapped to
a **world** instant:

- *Execution* instants (requisitions to award, supplier registrations, the
  portfolio) move by one whole number of weeks, `E`, so the story's "now"
  (`STORY_AS_AT`, a Friday 10:00) lands on the anchor (the latest Friday 10:00
  not later than the run's start) and every weekday and spacing is kept.
- *Planning* journeys (budget, Needs, departmental plans, the Annual Plan)
  keep a fixed relation to the fiscal calendar, one whole year, in whole weeks,
  per year; the prepared year's journey is pulled earlier by whole weeks just
  far enough that its Needs have happened by the anchor (`prepared_pull_days`).
- *Fiscal* dates (a year's end, a Required by, a latest delivery date) move by
  whole years only (`fiscal`).

Until a run stores an anchor the site is in **legacy** mode and every mapping is
the identity, so the v0.7 world is exactly what it was. Instants are resolved
when a seed module is imported, so the anchor is prepared in its own process
before the seed runs (`prepare`) and a change in the same process is refused
(`AnchorChangedError`)."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from dateutil.relativedelta import relativedelta

#: The story's "now" (plan D1): the read time of HOME-CHG-001 v0.6 H10–H12 and
#: ANL-CHG-001 v0.8 dataset A1. A Friday, 10:00.
STORY_AS_AT = "2027-06-18 10:00:00"
#: The name v0.7 code used; it is the story's reference, not the anchor.
AS_AT = STORY_AS_AT

#: Year 1's planning history is Year 2's moved back this many days (plan D8).
YEAR1_SHIFT_DAYS = -364

#: Site-wide default holding the stored state (JSON). No schema, no migrate.
STATE_KEY = "kt_seed_world_state"

#: Story coordinates below this are the 2023–24 baselines (Strategy) and never move.
_BASELINE_END = datetime(2025, 1, 1)
#: Story coordinates below this are Year 1's history (2025); then Year 2's
#: journey (2026); from 1 Jan 2027 execution.
_HISTORY_END = datetime(2026, 1, 1)
_EXECUTION_START = datetime(2027, 1, 1)
#: Story coordinates and the authored fiscal year they belong to (the year that
#: `Year 2` authored its journey for).
_AUTHORED_YEAR2_START = 2027

#: Last instants of each stage of the prepared year's journey, in story
#: coordinates (SEED-002 v0.7 §A3). A stage is built only when its last instant,
#: moved into the world, is not later than the anchor less `_MARGIN`.
PREPARED_STAGE_ENDS = (
	("budget", "2026-10-03 11:15:00"),
	("needs", "2026-11-25 10:00:00"),
	("departmental_plans", "2026-11-27 14:05:00"),
	("annual_plan", "2026-12-10 15:00:00"),
)
_MARGIN = timedelta(hours=2)

#: The executed year's shortest honest history, in days, before its anchor (plan
#: Phase 1, spike A). Below it a run anchors on the end of the previous season.
SEASON_MIN_ELAPSED_DAYS = 100
#: The story's own date inside the season's end (18 June).
_SEASON_END_MONTH_DAY = (6, 18)

_WEEK = timedelta(days=7)
_FMT_DT = "%Y-%m-%d %H:%M:%S"
_FMT_D = "%Y-%m-%d"


class AnchorChangedError(RuntimeError):
	"""The stored anchor changed after dates were resolved in this process."""


# --------------------------------------------------------------------------
# Parsing and forms
# --------------------------------------------------------------------------


def _story_as_at() -> datetime:
	return datetime.strptime(STORY_AS_AT, _FMT_DT)


def _parse(value: Any) -> tuple[datetime, str]:
	"""(datetime, form) where form is `date`, `datetime` or `str:<fmt>` so the result keeps its type."""
	if isinstance(value, datetime):
		return value, "datetime"
	if isinstance(value, date):
		return datetime(value.year, value.month, value.day), "date"
	text = str(value).strip()
	for fmt in (_FMT_DT, "%Y-%m-%d %H:%M:%S.%f", _FMT_D):
		try:
			return datetime.strptime(text, fmt), f"str:{fmt}"
		except ValueError:
			continue
	raise ValueError(f"Not a date or an instant: {value!r}")


def _form(moved: datetime, form: str) -> Any:
	if form == "datetime":
		return moved
	if form == "date":
		return moved.date()
	fmt = form[4:]
	return moved.strftime(_FMT_D if fmt == _FMT_D else _FMT_DT)


def shift(instant: Any, days: float) -> Any:
	"""`instant` moved by `days`, keeping its form (date or datetime, string or object)."""
	if not instant or not days:
		return instant
	moved, form = _parse(instant)
	return _form(moved + timedelta(days=days), form)


# --------------------------------------------------------------------------
# The stored state, and the mode
# --------------------------------------------------------------------------

_resolved: dict[str, Any] = {}


def _load_state() -> dict[str, Any] | None:
	import frappe

	try:
		if not getattr(frappe.local, "db", None):
			return None
		raw = frappe.db.get_default(STATE_KEY)
	except Exception:
		return None
	if not raw:
		return None
	try:
		state = json.loads(raw)
	except (TypeError, ValueError):
		return None
	return state if isinstance(state, dict) and state.get("mode") == "anchored" and state.get("anchor") else None


def state() -> dict[str, Any] | None:
	"""The stored anchored state, or ``None`` (legacy). Resolved once per process."""
	if "state" not in _resolved:
		_resolved["state"] = _load_state()
		_resolved["signature"] = json.dumps(_resolved["state"], sort_keys=True)
	return _resolved["state"]


def reset_resolution() -> None:
	"""Forget what this process resolved (tests only)."""
	_resolved.clear()


def mode() -> str:
	return "anchored" if state() else "legacy"


def assert_resolution_current() -> None:
	"""Raise when the stored state is not the one this process resolved its dates with."""
	if "state" not in _resolved:
		return
	stored = _load_state()
	if json.dumps(stored, sort_keys=True) != _resolved["signature"]:
		raise AnchorChangedError("The seed world's anchor changed after this process resolved its dates; run the seed in a new process (`make seed-canonical` prepares the anchor first).")


def store_state(new_state: dict[str, Any] | None) -> None:
	"""Write (or, with ``None``, clear) the stored state. The caller commits."""
	import frappe

	if new_state:
		frappe.db.set_default(STATE_KEY, json.dumps(new_state, sort_keys=True))
	else:
		frappe.db.set_default(STATE_KEY, "")
	frappe.clear_cache()


# --------------------------------------------------------------------------
# Choosing the anchor
# --------------------------------------------------------------------------


def fiscal_start_year(moment: datetime) -> int:
	"""The start year of the financial year (1 July to 30 June) that contains `moment`."""
	return moment.year if moment.month >= 7 else moment.year - 1


def latest_reference_not_after(moment: datetime) -> datetime:
	"""The latest instant with the story reference's weekday and time of day (Friday 10:00) not later than `moment`."""
	reference = _story_as_at()
	weeks = math.ceil((reference - moment) / _WEEK)
	return reference - weeks * _WEEK


def choose_anchor(started: datetime) -> tuple[datetime, str]:
	"""The anchor for a run that starts at `started`, and why: ``("", ...)`` is the
	plain case, otherwise a notice. When too little of the year that contains the
	anchor has elapsed to hold the executed history (`SEASON_MIN_ELAPSED_DAYS`),
	the anchor is the end of the previous season (the previous 18 June, weekday-aligned)."""
	anchor = latest_reference_not_after(started)
	start_year = fiscal_start_year(anchor)
	elapsed = (anchor - datetime(start_year, 7, 1)).days
	# The story's own season ends on 18 June; an anchor after it, in the year's last days, would put the executed plan's
	# delivery windows past the year's end (each Plan Item's invitation plus its schedule must fit by 30 June), so it is held to
	# the end of the season too.
	late_limit = latest_reference_not_after(datetime(start_year + 1, *_SEASON_END_MONTH_DAY, 10, 0, 0))
	if anchor > late_limit:
		return late_limit, (
			f"NOTICE: {anchor:%d %b %Y} is after the end of FY {start_year}/{str(start_year + 1)[-2:]}'s season, so the world is anchored on the end of the season, "
			f"{late_limit:%d %b %Y %H:%M}."
		)
	if elapsed >= SEASON_MIN_ELAPSED_DAYS:
		return anchor, ""
	season_end = datetime(start_year, *_SEASON_END_MONTH_DAY, 10, 0, 0)
	fallback = latest_reference_not_after(season_end)
	return fallback, (
		f"NOTICE: only {max(elapsed, 0)} days of FY {start_year}/{str(start_year + 1)[-2:]} have elapsed at {anchor:%d %b %Y}, "
		f"fewer than the {SEASON_MIN_ELAPSED_DAYS} the executed history needs, so the world is anchored on the end of the previous season, {fallback:%d %b %Y %H:%M}."
	)


def new_state(started: datetime) -> tuple[dict[str, Any], str]:
	anchor, notice = choose_anchor(started)
	return {"mode": "anchored", "anchor": anchor.strftime(_FMT_DT), "started": started.strftime(_FMT_DT), "season_notice": notice}, notice


def prepare(*, anchor: bool = True, fresh: bool = False, commit: bool = True) -> dict[str, Any]:
	"""Store the anchor for the run that follows, in its own process. ``anchor=False`` returns
	the site to legacy; ``fresh`` replaces a stored anchor (a rebuild re-anchors, a plain rerun keeps it)."""
	import frappe
	from frappe.utils import now_datetime

	existing = _load_state()
	# Changing between the v0.7 world and the real-date world changes every instant the seed wrote, and the years the clears keep;
	# a site that holds a world is rebuilt for it (REBUILD=True), never converted by a plain rerun.
	holds_a_world = bool(frappe.db.exists("DocType", "Procurement Budget") and frappe.db.count("Procurement Budget"))
	if holds_a_world and not fresh and bool(existing) != bool(anchor):
		raise RuntimeError(
			"This site holds a canonical world built "
			+ ("on the real date" if existing else "as the v0.7 story")
			+ f"; {'ANCHOR=story' if existing else 'ANCHOR=real'} needs REBUILD=True (or WIPE=True) to rebuild it, because the dates and the years kept differ."
		)
	if not anchor:
		if existing:
			store_state(None)
		out = {"mode": "legacy", "was": existing}
	elif existing and not fresh:
		out = {"mode": "anchored", "kept": True, **existing}
	else:
		new, notice = new_state(frappe.utils.get_datetime(now_datetime()).replace(microsecond=0))
		store_state(new)
		out = {"mode": "anchored", "kept": False, **new}
		if notice:
			print(notice)
		if existing and fiscal_start_year(datetime.strptime(existing["anchor"], _FMT_DT)) != fiscal_start_year(datetime.strptime(new["anchor"], _FMT_DT)):
			# The dated responsibilities (the acting and handover terms) move with the years, and an existing grant is returned as
			# it is: only a wipe of the site stage grants the new terms.
			print("NOTICE: the world's years moved on (a new financial year). The dated responsibilities of KT-STD-001 §8.3 take their new terms only "
				"when the site stage is rebuilt: run `make seed-canonical REBUILD=True WIPE=True FORCE=True RESEED=True`.")
	if commit:
		frappe.db.commit()
	return out


# --------------------------------------------------------------------------
# Reading the anchor
# --------------------------------------------------------------------------


def anchor_datetime() -> datetime:
	current = state()
	return datetime.strptime(current["anchor"], _FMT_DT) if current else _story_as_at()


def as_at() -> str:
	"""The world's reference instant (the anchor); the story's own in legacy mode."""
	return anchor_datetime().strftime(_FMT_DT)


def execution_shift_days() -> int:
	"""E: whole weeks, in days, the story's execution instants move by (0 in legacy mode)."""
	return round((anchor_datetime() - _story_as_at()).total_seconds() / 86400)


def anchor_fiscal_start_year() -> int:
	return fiscal_start_year(anchor_datetime())


def years_from_authored() -> int:
	"""How many financial years the world's Year 1 is from the authored FY 2026/27."""
	return anchor_fiscal_start_year() - 2026


def _base_weeks_days(years: int) -> int:
	return 7 * round(years * 52.1775)


# --------------------------------------------------------------------------
# Years
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Year:
	key: str  # "year0" | "year1" | "year2"
	index: int  # -1, 0, 1 from Year 1

	@property
	def start_year(self) -> int:
		return anchor_fiscal_start_year() + self.index

	@property
	def fiscal_year(self) -> str:
		"""The ERPNext Fiscal Year name, e.g. ``2026-2027``."""
		return f"{self.start_year}-{self.start_year + 1}"

	@property
	def label(self) -> str:
		return f"FY {self.start_year}/{str(self.start_year + 1)[-2:]}"

	@property
	def start_date(self) -> str:
		return f"{self.start_year}-07-01"

	@property
	def end_date(self) -> str:
		return f"{self.start_year + 1}-06-30"

	@property
	def base_shift_days(self) -> int:
		"""This year's journey against the authored Year 2 journey (FY 2027/28): whole weeks per year (Year 1 is -364, plan D8)."""
		return _base_weeks_days(self.start_year - _AUTHORED_YEAR2_START)

	@property
	def shift_days(self) -> int:
		"""The days a journey instant of the authored Year 2 moves by to be this year's."""
		pull = prepared_pull_days() if self.index == 1 else 0
		return self.base_shift_days - pull

	def at(self, instant: str) -> str:
		"""`instant` (a Year 2 journey instant in story coordinates) moved into this year, in the same form."""
		return shift(instant, self.shift_days)

	def window(self, instant: str) -> str:
		"""An instant fixed to the fiscal calendar (an intake window's close): the year's base shift, never pulled earlier."""
		return shift(instant, self.base_shift_days)

	def fiscal(self, value: Any) -> Any:
		"""A fiscal date of the authored Year 1 or Year 2 (a year's end, a Required by) moved by whole years."""
		return fiscal(value)


YEAR0 = Year("year0", -1)
YEAR1 = Year("year1", 0)
YEAR2 = Year("year2", 1)
YEARS = (YEAR1, YEAR2)
ALL_YEARS = (YEAR0, YEAR1, YEAR2)


def seeded_years() -> tuple[Year, ...]:
	"""The years the seeds build: all three once an anchor is stored (the closed Year 0 included), the two of
	the v0.7 world before."""
	return ALL_YEARS if mode() == "anchored" else YEARS


def year(key: str) -> Year:
	for candidate in ALL_YEARS:
		if candidate.key == key:
			return candidate
	raise ValueError(f"Unknown seed year {key!r}; expected one of {[y.key for y in ALL_YEARS]}")


def prepared_pull_days() -> int:
	"""Days (a whole number of weeks) the prepared year's journey is pulled earlier so its Needs
	have happened by the anchor; 0 in legacy mode and whenever the story's Needs are already past."""
	if not state():
		return 0
	needs_end = datetime.strptime(dict(PREPARED_STAGE_ENDS)["needs"], _FMT_DT) + timedelta(days=_base_weeks_days(anchor_fiscal_start_year() + 1 - _AUTHORED_YEAR2_START))
	limit = anchor_datetime() - _MARGIN
	if needs_end <= limit:
		return 0
	return 7 * math.ceil((needs_end - limit) / _WEEK)


def prepared_stage_available(stage: str) -> bool:
	"""Whether the prepared year's stage has happened by the anchor in the world."""
	if not state():
		return True
	end = datetime.strptime(dict(PREPARED_STAGE_ENDS)[stage], _FMT_DT) + timedelta(days=YEAR2.shift_days)
	return end <= anchor_datetime() - _MARGIN


def default_next_stage() -> str:
	"""The furthest prepared-year stage the anchor allows, up to `annual_plan` (``budget`` at the least)."""
	furthest = "budget"
	for stage, _end in PREPARED_STAGE_ENDS:
		if prepared_stage_available(stage):
			furthest = stage
	return furthest


# --------------------------------------------------------------------------
# Mapping story coordinates into the world
# --------------------------------------------------------------------------


def shift_years(value: Any, years: int) -> Any:
	if not value or not years:
		return value
	moved, form = _parse(value)
	return _form(moved + relativedelta(years=years), form)


def fiscal(value: Any) -> Any:
	"""A fiscal-calendar date in story coordinates (a year's end, a Required by, a latest
	delivery date, an effective-from at a year's start) moved by whole years; the identity in legacy mode."""
	if not state():
		return value
	return shift_years(value, years_from_authored())


def world(value: Any) -> Any:
	"""A seed instant or date in story coordinates, moved into the world (same form).
	The identity in legacy mode. Which shift applies follows from where the story put it."""
	if value is None or value == "":
		return value
	if not state():
		return value
	moved, form = _parse(value)
	if moved < _BASELINE_END:
		return _form(moved, form)
	if moved < _HISTORY_END:
		days = _base_weeks_days(years_from_authored())
	elif moved < _EXECUTION_START:
		days = YEAR2.shift_days
	else:
		days = execution_shift_days()
		if moved > _story_as_at():
			days += 7  # a live deadline: a week beyond the world's lag behind the run's start
	return _form(moved + timedelta(days=days), form)


#: Short names the seed modules import: `from kentender_core.seeds.calendar import world as W`.
W = world
F = fiscal


#: The closed year's three Tenders start this many slots apart (0, 1, 2); see `closed_year_offset_days`.
CLOSED_YEAR_SLOTS = 3
#: The last instant of the closed year's chain in story coordinates (the last acceptance of its awards) and the days kept
#: clear of the year's end.
_CLOSED_YEAR_LAST_STORY_INSTANT = "2027-06-15 09:00:00"
_CLOSED_YEAR_END_MARGIN_DAYS = 14


def closed_year_offset_days(slot: int) -> int:
	"""Whole weeks (in days) the closed year's `slot`-th Tender chain is moved later than the first, so its Tenders do not
	all sit in one quarter and the trailing twelve months of the Analytics page each hold a record. The first slot stays where
	the executed year's story one year earlier puts it; the last ends at least `_CLOSED_YEAR_END_MARGIN_DAYS` before the
	year's end; a run late in the year, when the year has no room left, spreads nothing. 0 in legacy mode."""
	if not state() or slot <= 0:
		return 0
	last = datetime.strptime(shift(world(_CLOSED_YEAR_LAST_STORY_INSTANT), YEAR0.base_shift_days - YEAR1.base_shift_days), _FMT_DT)
	end = datetime.strptime(YEAR0.end_date, _FMT_D) + timedelta(hours=23)
	room = (end - last).days - _CLOSED_YEAR_END_MARGIN_DAYS
	if room < 7:
		return 0
	return 7 * ((room * min(slot, CLOSED_YEAR_SLOTS - 1) // (CLOSED_YEAR_SLOTS - 1)) // 7)


def delivery(value: Any, boundary: str = "2027-06-30") -> Any:
	"""A delivery date of the executed year's story: `world(value)` held to the year's last day (`fiscal(boundary)`, the Plan Items'
	completion boundary). A date at the end of the story is after the story's "now", so `world` adds the live-deadline week and,
	late in the year, would pass the boundary a Requisition refuses (DATE_BEYOND_BOUNDARY). The identity in legacy mode."""
	moved = world(value)
	if not state() or not moved:
		return moved
	cap = fiscal(boundary)
	moved_at, form = _parse(moved)
	cap_at, _ = _parse(cap)
	return _form(min(moved_at, cap_at), form)


def world0(value: Any, slot: int = 0) -> Any:
	"""An execution-type story instant of the closed year (Year 0): the executed year's moved one financial year
	earlier, in whole weeks (the same machinery one year back, SEED-002 v0.8 §A7), and `slot` Tender-chains later
	(`closed_year_offset_days`). The identity in legacy mode."""
	if value is None or value == "" or not state():
		return value
	return shift(world(value), YEAR0.base_shift_days - YEAR1.base_shift_days + closed_year_offset_days(slot))


W0 = world0


def not_after_anchor(instant: str) -> str:
	"""`instant` (already in the world), or ``_MARGIN`` before the anchor when it would be later: a step of a profile that
	sits after the prepared year's Needs in the story, in a world whose Needs have only just happened. The identity in legacy mode."""
	if not instant or not state():
		return instant
	limit = anchor_datetime() - _MARGIN
	moved, form = _parse(instant)
	return _form(min(moved, limit), form)


def describe() -> dict[str, Any]:
	"""Everything a browser spec needs to compute the instants and labels a screen shows, as plain numbers: the anchor,
	the shifts `world`/`world0`/`fiscal` apply and the three years. Read by `tests/ui/helpers/anchor.ts` through
	`bench execute`, which mirrors the mapping rules of `world` (SEED-002 v0.8 §A3)."""
	return {
		"mode": mode(),
		"story_as_at": STORY_AS_AT,
		"anchor": as_at(),
		"execution_shift_days": execution_shift_days(),
		"history_shift_days": _base_weeks_days(years_from_authored()) if state() else 0,
		"year2_journey_shift_days": YEAR2.shift_days if state() else 0,
		"closed_year_extra_shift_days": (YEAR0.base_shift_days - YEAR1.base_shift_days) if state() else 0,
		"closed_year_slot_days": [closed_year_offset_days(slot) for slot in range(CLOSED_YEAR_SLOTS)],
		"fiscal_years_from_authored": years_from_authored() if state() else 0,
		"years": {y.key: {"fiscal_year": y.fiscal_year, "label": y.label, "start_date": y.start_date, "end_date": y.end_date, "shift_days": y.shift_days} for y in ALL_YEARS},
		"boundaries": {"baseline_end": _BASELINE_END.strftime(_FMT_DT), "history_end": _HISTORY_END.strftime(_FMT_DT), "execution_start": _EXECUTION_START.strftime(_FMT_DT)},
	}


def block_shift_days(last_story_instant: str) -> int:
	"""The extra days (whole weeks, <= 0) a block of execution instants must move earlier so its last
	instant is not later than the anchor: a demonstration whose story runs past the story's "now"."""
	last = datetime.strptime(last_story_instant, _FMT_DT)
	over = last - _story_as_at()
	if over <= timedelta(0):
		return 0
	return -7 * math.ceil(over / _WEEK)


def block(last_story_instant: str):
	"""The mapping for a block of events whose story runs past the story's "now" (a demonstration profile or a browser
	world that goes on after the as-at instant): every instant moves by the execution shift and the block's own whole weeks
	earlier, so the last one is not later than the anchor. No live-deadline week is added, since the block holds events, not
	deadlines. The block moves as a whole, so the spacing and weekdays inside it stay. The identity in legacy mode."""
	extra = block_shift_days(last_story_instant) if state() else 0

	def moved(value: Any) -> Any:
		if value is None or value == "" or not state():
			return value
		return shift(value, execution_shift_days() + extra)

	return moved


def years_back(last_story_instant: str) -> int:
	"""The whole years (>= 0) a block of instants must move back so its last instant is not later than the anchor; 0 in legacy mode."""
	if not state():
		return 0
	last = datetime.strptime(last_story_instant, _FMT_DT)
	anchor = anchor_datetime()
	years = 0
	while last - relativedelta(years=years) > anchor:
		years += 1
	return years


def years_block(last_story_instant: str):
	"""The mapping for a block whose story is told in calendar months and quarters (Contract Management's monthly and quarterly reports,
	a twelve-month warranty): the whole story moves back by whole years, so a month starts on a month's first day, a quarter on a quarter's
	and a calendar date keeps its day and month. It does not keep weekdays, and a duration across a 29 February differs by a day.
	The identity in legacy mode."""
	years = years_back(last_story_instant)

	def moved(value: Any) -> Any:
		if value is None or value == "" or not state():
			return value
		return shift_years(value, -years)

	return moved


def never_ahead_problem(instant: Any, real_now: Any = None) -> str:
	"""Why `instant` may not be recorded in the world, or ``""``: it is later than the real clock. `real_now` is the real clock
	read outside any frozen block (a nested block is checked against it, since inside the outer block `now_datetime` is frozen)."""
	from frappe.utils import get_datetime, now_datetime

	now = get_datetime(real_now if real_now is not None else now_datetime())
	if instant and get_datetime(instant) > now:
		return f"{instant} is later than the real clock ({now})"
	return ""
