# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared test-environment instant (BDS-CHG-001 v0.8 plan D18).

A browser world on a test environment runs its live pages on the fixture's
own timeline (the 2027 canonical dates) rather than today's date. The owning
module persists that instant in its test controls and answers the
`kt_test_clock` hook; every app's trusted clock asks here after its own
injected test flag, so Bid Submission and Supplier Accounts read one instant.
Nothing answers on a site that is not a test environment, so production
always reads the site clock."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_test_clock"
SET_HOOK = "kt_test_clock_setters"


def current_instant() -> Any | None:
	for path in frappe.get_hooks(HOOK) or []:
		instant = frappe.get_attr(path)()
		if instant:
			return instant
	return None


def set_instant(instant: Any | None) -> bool:
	"""Put the live pages on `instant` (``None`` clears it) for a browser world
	in any app, through the module that persists it. False when nothing took
	it — the site is not a test environment."""
	taken = False
	for path in frappe.get_hooks(SET_HOOK) or []:
		taken = bool(frappe.get_attr(path)(instant)) or taken
	return taken
