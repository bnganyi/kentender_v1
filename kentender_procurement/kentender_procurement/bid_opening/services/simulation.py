# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Opening test-environment switch and controls (owner decision OD-C;
plan D5, D11, D17).

The same site_config key as Bid Submission, `kt_bds_simulation_environment`,
marks a test environment; a production site leaves it unset and every
Bid Opening stand-in stays silent. The controls are a Single no role can read
or write, set only by fixtures and tests. They force the Bid Opening worlds
the §10 branches need: the opening service unavailable (branch 6), the public
attendance service down (branch 4), an unreadable package (branch 2) and a
failed support notification (branch 6). The tender box's own reveal outcome
belongs to Bid Submission's controls."""

from __future__ import annotations

import frappe
from frappe.utils import cint

CONFIG_KEY = "kt_bds_simulation_environment"
CONTROLS = "BOP Test Environment Controls"
DEFAULTS: dict = {"opening_profile_down": 0, "attendance_service_down": 0, "render_outcome": "Render", "notify_outcome": "Deliver"}


def enabled() -> bool:
	return bool(cint(frappe.conf.get(CONFIG_KEY)))


def controls() -> dict:
	if not enabled():
		return dict(DEFAULTS)
	saved = frappe.db.get_singles_dict(CONTROLS) or {}
	out = dict(DEFAULTS)
	for key, default in DEFAULTS.items():
		value = saved.get(key)
		if value not in (None, ""):
			out[key] = cint(value) if isinstance(default, int) else value
	return out


def set_controls(**values) -> dict:
	if not enabled():
		frappe.throw("The Bid Opening test controls exist only on a test environment.")
	unknown = set(values) - set(DEFAULTS)
	if unknown:
		raise ValueError(f"Unknown test controls: {sorted(unknown)}")
	doc = frappe.get_doc(CONTROLS)
	for key, value in values.items():
		doc.set(key, value)
	doc.flags.kt_bop_test_service = True
	doc.save(ignore_permissions=True)
	return controls()


def reset_controls() -> dict:
	if not enabled():
		return dict(DEFAULTS)
	return set_controls(**DEFAULTS)
