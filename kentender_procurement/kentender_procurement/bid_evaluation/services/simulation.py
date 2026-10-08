# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Evaluation test-environment switch and controls (owner decision
OD-D; plan D16).

The same site_config key as Bid Submission and Bid Opening,
`kt_bds_simulation_environment`, marks a test environment; on a production
site every Evaluation stand-in stays silent and these controls read as their
defaults. The controls are a Single no role can read or write, set only by
fixtures and tests. They force the worlds the EVL-CHG-001 v0.4 §11.2 branches
need: a failed opening-package intake, a failed clarification notice, a
failed report delivery and an unavailable downstream decision status. Owner
events Tenders cannot yet produce (suspension, resumption, post-close
cancellation, validity extension, award decision, a dated evaluation rule)
are recorded by `record_simulated_event`, again only on a test environment."""

from __future__ import annotations

import frappe
from frappe.utils import cint

CONFIG_KEY = "kt_bds_simulation_environment"
CONTROLS = "EVL Test Environment Controls"
DEFAULTS: dict = {"intake_outcome": "", "notice_outcome": "", "delivery_outcome": "", "downstream_status": "", "head_of_procurement": ""}


def enabled() -> bool:
	return bool(cint(frappe.conf.get(CONFIG_KEY)))


def controls() -> dict:
	if not enabled():
		return dict(DEFAULTS)
	saved = frappe.db.get_singles_dict(CONTROLS) or {}
	return {key: (saved.get(key) or default) for key, default in DEFAULTS.items()}


def set_controls(**values) -> dict:
	if not enabled():
		frappe.throw("The Bid Evaluation test controls exist only on a test environment.")
	unknown = set(values) - set(DEFAULTS)
	if unknown:
		raise ValueError(f"Unknown test controls: {sorted(unknown)}")
	doc = frappe.get_doc(CONTROLS)
	for key, value in values.items():
		doc.set(key, value or "")
	doc.save(ignore_permissions=True)
	return controls()


def reset_controls() -> dict:
	if not enabled():
		return dict(DEFAULTS)
	return set_controls(**DEFAULTS)
