# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One trusted clock for Bid Submission (BDS-CHG-001 v0.8 plan D18). Production
reads the site clock; tests inject `frappe.flags.kt_bds_clock` and the
canonical seed runs under `kentender_core.seeds.clock.at`, so recorded
instants are the spec's own fixture times, never now-relative. A browser world
on a test environment sets the test controls' `current_instant`."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def now() -> datetime:
	injected = getattr(frappe.flags, "kt_bds_clock", None)
	if injected:
		return get_datetime(injected)
	# Browser worlds (plan D18): a test environment's persisted instant, so a
	# live page runs on the fixture's 2027 timeline. Never on another site.
	from kentender_procurement.bid_submission.services import simulation

	if simulation.enabled():
		instant = simulation.controls().get("current_instant")
		if instant:
			return get_datetime(instant)
	return now_datetime()
