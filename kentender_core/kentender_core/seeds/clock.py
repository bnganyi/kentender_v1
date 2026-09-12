# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §13.1–13.2 / plan D19 — the frozen seed clock.

Seeds call the same commands as the UI (KT-STD-001 §8.6). A command checks
the actor's authority *at command time* (AUTH-ADR-001 §4.6) and stamps its
own instants from the wall clock, so a fixture whose actions happen on
25 November 2026 can only be built honestly by running each command **at**
that instant. This module freezes the process clock (freezegun) for the
duration of one command; nothing is back-stamped afterwards ("Do not backdate
real evidence to repair fixtures", v1.18 §13.1).

Instants are given as EAT wall-clock strings (`YYYY-MM-DD HH:MM:SS`), the
form every KenTender fixture register uses; the site stores naive
Africa/Nairobi datetimes, so `frappe.utils.now_datetime()` inside the block
returns exactly that wall-clock value.

Usage:
	with clock.at("2026-11-25 10:30:00"):
		lifecycle.submit_departmental_plan(...)
"""

from __future__ import annotations

import datetime as _dt
from contextlib import contextmanager
from typing import Iterator
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import get_datetime, get_system_timezone

try:
	from freezegun import freeze_time
except ImportError:  # pragma: no cover — freezegun is a bench dependency
	freeze_time = None


def _to_utc(instant: str | _dt.datetime) -> _dt.datetime:
	local = get_datetime(instant)
	if local.microsecond == 0:
		# Frappe's optimistic-lock check compares `modified` as strings; a
		# whole-second instant renders as `…:00.000000` in memory but `…:00`
		# from the database and would fail every second save inside the
		# block. One microsecond keeps both renderings identical.
		local = local.replace(microsecond=1)
	tz = ZoneInfo(get_system_timezone())
	return local.replace(tzinfo=tz).astimezone(_dt.timezone.utc).replace(tzinfo=None)


@contextmanager
def at(instant: str | _dt.datetime) -> Iterator[None]:
	"""Run the block with the process clock set to `instant` (site-local).

	Time *ticks* from that instant (so consecutive saves inside one block get
	distinct `modified` stamps, as they would in production) but never leaves
	the fixture second before the block ends."""
	if freeze_time is None:
		frappe.throw("freezegun is required to run seeds at fixture instants (plan D19).")
	frappe.flags.kt_frozen_clock = str(get_datetime(instant))
	try:
		with freeze_time(_to_utc(instant), tick=True):
			yield
	finally:
		frappe.flags.kt_frozen_clock = None


def frozen_at() -> str:
	"""The instant a seed block is currently frozen at, or '' outside one."""
	return frappe.flags.get("kt_frozen_clock") or ""
