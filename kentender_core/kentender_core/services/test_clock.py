# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared test-environment instant (BDS-CHG-001 v0.8 plan D18).

A browser world on a test environment runs its live pages on the fixture's
own timeline rather than today's date. The owning module persists that
instant in its test controls and answers the `kt_test_clock` hook; every
app's trusted clock asks here after its own injected test flag, so Bid
Submission and Supplier Accounts read one instant. Nothing answers on a site
that is not a test environment, so production always reads the site clock.

**Policy (seed-world real-date anchor plan, step 1).** Each site decides in
its own site_config (`kt_test_clock_policy`) what the clock may be:

- `free` (the default while the canonical world is dated 2027): any instant
  may be set, exactly as before.
- `never_ahead`: an instant later than the real clock is refused when it is
  set and ignored when it is read. Native ERPNext documents carry the real
  date and refuse a later one (a Purchase Receipt: "Posting Date cannot be
  future date"), so a simulated moment ahead of the real clock cannot be
  followed by them (CM-CHG-001 v0.8 follow-up FU-CM-61).
- `off`: the site runs on the real clock. Nothing may be stored, a stored
  value is ignored, and a stored value may only be cleared. An unknown value
  reads as `off`, never as `free`."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

HOOK = "kt_test_clock"
SET_HOOK = "kt_test_clock_setters"

POLICY_KEY = "kt_test_clock_policy"
FREE, NEVER_AHEAD, OFF = "free", "never_ahead", "off"


def policy() -> str:
	"""The site's clock policy; no key is `free`, an unrecognised one is `off`."""
	value = str(frappe.conf.get(POLICY_KEY) or FREE).strip().lower()
	return value if value in (FREE, NEVER_AHEAD) else OFF


def stored_instant() -> Any | None:
	"""What the owning module has persisted, whatever the policy says about using it."""
	for path in frappe.get_hooks(HOOK) or []:
		instant = frappe.get_attr(path)()
		if instant:
			return instant
	return None


def ahead_of_real(instant: Any) -> bool:
	return bool(instant) and get_datetime(instant) > get_datetime(now_datetime())


def current_instant() -> Any | None:
	mode = policy()
	if mode == OFF:
		return None
	instant = stored_instant()
	if instant and mode == NEVER_AHEAD and ahead_of_real(instant):
		return None
	return instant


def set_instant(instant: Any | None) -> bool:
	"""Put the live pages on `instant` (``None`` clears it) for a browser world
	in any app, through the module that persists it. False when nothing took
	it — the site is not a test environment, or its policy is `off`. Under
	`never_ahead` an instant later than the real clock is refused outright,
	because a caller that believed it had been set would run on the wrong day."""
	if instant:
		mode = policy()
		if mode == OFF:
			return False
		if mode == NEVER_AHEAD and ahead_of_real(instant):
			frappe.throw(
				f"The test clock cannot be set to {get_datetime(instant)}: it is later than the real clock ({get_datetime(now_datetime())}) and this site's clock policy is {NEVER_AHEAD}."
			)
	taken = False
	for path in frappe.get_hooks(SET_HOOK) or []:
		taken = bool(frappe.get_attr(path)(instant)) or taken
	return taken


def describe() -> dict[str, Any]:
	"""The policy, what is stored, the real clock and whether the stored instant is ahead of it."""
	stored = stored_instant()
	return {"policy": policy(), "stored": str(stored) if stored else None, "real_now": str(get_datetime(now_datetime())), "ahead": ahead_of_real(stored)}


def problem(expected: str | None = None) -> str:
	"""Why the site's clock is not as its policy requires, or ``""`` when it is.

	`free` keeps the legacy rule for a canonical world on a test environment
	(the caller passes the instant it expects); `never_ahead` objects to a stored
	instant that is ahead of the real clock; `off` objects to any stored instant."""
	mode, stored = policy(), stored_instant()
	if mode == OFF:
		return f"the site clock policy is off, so no test instant may be stored (found {str(stored)!r})" if stored else ""
	if mode == NEVER_AHEAD:
		return f"the test clock {str(stored)!r} is ahead of the real clock {str(get_datetime(now_datetime()))!r} (policy {NEVER_AHEAD})" if ahead_of_real(stored) else ""
	if expected and str(stored or "")[:19] != str(expected)[:19]:
		return f"the site test clock is not at {expected} (found {stored!r})"
	return ""
