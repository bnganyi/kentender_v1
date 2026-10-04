# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The test-environment switch (BDS-CHG-001 v0.8 owner decision OD-C).

Simulated services (the Test Scanner now; the Test Trust Service, Test
Tender Box and test clock later) answer only on a site whose own
site_config sets `kt_bds_simulation_environment: 1`. There is no Desk,
portal or API control, and a production site leaves it unset, so every
simulation stays silent there. Everything a simulation produces says so in
its own words."""

from __future__ import annotations

import frappe
from frappe.utils import cint

CONFIG_KEY = "kt_bds_simulation_environment"


def enabled() -> bool:
	return bool(cint(frappe.conf.get(CONFIG_KEY)))


# --------------------------------------------------------------------------
# The test-environment controls (plan D5): a Single no role can read or
# write, set only by fixtures and tests through `set_controls`, consulted
# only on a test environment. It forces the gate, outage, custody-outcome
# and bound-release worlds; it has no effect anywhere else.
# --------------------------------------------------------------------------

CONTROLS = "BDS Test Environment Controls"
DEFAULTS: dict = {
	"gate_closed": 0, "trust_service_down": 0, "time_service_down": 0, "custody_service_down": 0,
	"deposit_outcome": "Accept", "rejection_reference": "", "uncertain_resolution": "Pending", "accept_after_seconds": 0, "current_instant": "",
	"bound_release_state": "",
	# BOP-CHG-001 v0.10 plan D4/D17: the Test Tender Box reveal outcome for Bid Opening.
	"reveal_outcome": "Deliver",
}


def controls() -> dict:
	if not enabled():
		return dict(DEFAULTS)
	cached = getattr(frappe.local, "kt_bds_controls", None)
	if cached is not None:
		return dict(cached)
	saved = frappe.db.get_singles_dict(CONTROLS) or {}
	out = dict(DEFAULTS)
	for key, default in DEFAULTS.items():
		value = saved.get(key)
		if value not in (None, ""):
			out[key] = cint(value) if isinstance(default, int) else value
	frappe.local.kt_bds_controls = dict(out)
	return out


def set_controls(**values) -> dict:
	if not enabled():
		frappe.throw("The Bid Submission test controls exist only on a test environment.")
	unknown = set(values) - set(DEFAULTS)
	if unknown:
		raise ValueError(f"Unknown test controls: {sorted(unknown)}")
	doc = frappe.get_doc(CONTROLS)
	for key, value in values.items():
		doc.set(key, value)
	doc.flags.kt_bds_test_service = True
	doc.save(ignore_permissions=True)
	frappe.local.kt_bds_controls = None
	return controls()


def reset_controls() -> dict:
	if not enabled():
		return dict(DEFAULTS)
	return set_controls(**DEFAULTS)


def current_instant():
	"""`kt_test_clock` (kentender_core test_clock): the browser world's instant,
	on a test environment only."""
	if not enabled():
		return None
	return controls().get("current_instant") or None


def set_test_instant(instant) -> bool:
	"""`kt_test_clock_setters`: persist (or with ``None`` clear) the browser
	world's instant; refused silently outside a test environment."""
	if not enabled():
		return False
	set_controls(current_instant=instant or None)
	return True
