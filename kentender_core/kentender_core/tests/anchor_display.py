# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""How a test names a seeded story instant on a screen or in a payload, once the world is anchored (SEED-002 v0.9 §A3.1).

A test written with the story's dates ("12 Jun 2027, 11:00 EAT") asks for the same text built from the instant the world holds:
`dt_eat("2027-06-12 11:00:00")`. Each function moves the story instant with `calendar.world` first and prints it in the form a screen uses;
in a v0.7 world `world` is the identity, so the text is the story's own.

A module whose story moves back as one block (the Award tests, Contract Management) builds the same functions over its own mapping:
`Display(block("2027-10-11 10:00:00"))`."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from kentender_core.seeds.calendar import world

_FMT = "%Y-%m-%d %H:%M:%S"


class Display:
    """The printing functions over one mapping of story instants into the world (`calendar.world` by default)."""

    def __init__(self, mapper: Callable[[str], str] | None = None):
        self._map = mapper or world

    def _moved(self, story: str, plus_days: int = 0) -> datetime:
        """The story instant in the world; `plus_days` is added after the move, for a value the system derives from a base instant (a
        reply deadline seven days after the notice) rather than one that is itself an event: `world` adds a week to an event later than
        the story's "now", a derived value does not have it."""
        text = self._map(story)
        return datetime.strptime(text if len(text) > 10 else f"{text} 00:00:00", _FMT) + timedelta(days=plus_days)

    def dt_eat(self, story: str, plus_days: int = 0, seconds: bool = False) -> str:
        """``12 Jun 2027, 11:00 EAT`` (``12 Jun 2027, 11:00:05 EAT`` with `seconds`)"""
        moment = self._moved(story, plus_days)
        return f"{moment.day} {moment:%b %Y}, {moment:%H:%M:%S}" + " EAT" if seconds else f"{moment.day} {moment:%b %Y}, {moment:%H:%M} EAT"

    def dt_eat_long(self, story: str, plus_days: int = 0) -> str:
        """``12 June 2027, 11:00 EAT``"""
        moment = self._moved(story, plus_days)
        return f"{moment.day} {moment:%B %Y}, {moment:%H:%M} EAT"

    def d_short(self, story: str, plus_days: int = 0) -> str:
        """``12 Jun 2027``"""
        moment = self._moved(story, plus_days)
        return f"{moment.day} {moment:%b %Y}"

    def d_long(self, story: str, plus_days: int = 0) -> str:
        """``12 June 2027``"""
        moment = self._moved(story, plus_days)
        return f"{moment.day} {moment:%B %Y}"

    def iso_eat(self, story: str, plus_days: int = 0) -> str:
        """``2027-06-04T14:00:00+03:00``"""
        return self._moved(story, plus_days).strftime("%Y-%m-%dT%H:%M:%S") + "+03:00"

    def dt_long(self, story: str, plus_days: int = 0) -> str:
        """``16 June 2027, 09:00`` (no zone)"""
        moment = self._moved(story, plus_days)
        return f"{moment.day} {moment:%B %Y}, {moment:%H:%M}"

    def home_dt(self, story: str, read: str | None = None) -> str:
        """``16 June, 11:00`` as Home prints a moment: the year is left out when it is the year of the read (`read` is a story instant; the anchor if omitted)."""
        from kentender_core.seeds.calendar import as_at

        moment = self._moved(story)
        read_moment = self._moved(read) if read else datetime.strptime(as_at(), _FMT)
        day = f"{moment.day} {moment:%B}" + ("" if moment.year == read_moment.year else f" {moment.year}")
        return f"{day}, {moment:%H:%M}"


_default = Display()
dt_eat = _default.dt_eat
dt_eat_long = _default.dt_eat_long
d_short = _default.d_short
d_long = _default.d_long
iso_eat = _default.iso_eat
dt_long = _default.dt_long
home_dt = _default.home_dt
