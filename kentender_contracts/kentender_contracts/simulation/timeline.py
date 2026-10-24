# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The synthetic Contract Management world's calendar (SEED-002 v0.9 §A8; CM-CHG-001 v0.8 §10.1B: the dates are illustrative, the durations authoritative).

The demonstration profiles, the browser world and the tests tell one ten-laptop contract from the Award package's arrival on 2 July 2027 to its close on 28 July
2028. In the seed world's real-date anchor model no simulated instant is later than the real clock, so the whole story moves back as one block, in whole years, until
its last instant is not later than the anchor: Contract Management tells its story in calendar months and quarters (monthly and quarterly reports, a twelve-month
warranty), and only a whole-year move keeps a month starting on its first day and a quarter on its first. Every date keeps its day and month, every duration its length
(a duration across a 29 February differs by a day); weekdays are not kept, and nothing in Contract Management depends on them. `D` is that move: the identity when
the site's world is the v0.7 story (the development site until it is reseeded), the block's shift when the world is anchored.

Write a story instant or date as `D("2027-07-12 10:00:00")`, never as a bare literal, wherever it is stored, set as a clock or compared."""

from __future__ import annotations

from kentender_core.seeds import calendar

#: The last instant of the story: the contract's close (the `CLOSED` demonstration profile).
LAST_STORY_INSTANT = "2028-07-28 11:00:00"

D = calendar.years_block(LAST_STORY_INSTANT)


def _moved(value):
    from frappe.utils import get_datetime

    return get_datetime(D(value))


def long_date(value: str) -> str:
    """A story date as the boards print it once moved: ``20 July 2028``."""
    return _moved(value).strftime("%-d %B %Y")


def short_date(value: str) -> str:
    """``20 Jul 2027``"""
    return _moved(value).strftime("%-d %b %Y")


def short_instant(value: str) -> str:
    """``17 Jun 2027, 10:00 EAT``"""
    return _moved(value).strftime("%-d %b %Y, %H:%M") + " EAT"


def day(value: str) -> str:
    """``23``"""
    return _moved(value).strftime("%-d")


def day_month(value: str) -> str:
    """``25 Jul``"""
    return _moved(value).strftime("%-d %b")


def after_months(value: str, months: int) -> str:
    """The date `months` calendar months after a story date, counted in the world: a twelve-month warranty is twelve calendar months from the unit's
    acceptance wherever that falls, so across a leap day its length in days is not the story's (the story's 2028 has a 29 February; the moved block may have none)."""
    from frappe.utils import add_months, getdate

    return str(add_months(getdate(D(value)), months))
