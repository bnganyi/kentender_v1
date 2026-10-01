# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Simulation-only fault switches (AWD-CHG-001 v0.4 plan D16; §13 "synthetic
Trust, delivery and Contracting adapters only, visibly labelled").

They load only on a test environment (`kt_bds_simulation_environment`, as for
Bid Submission, Bid Opening and Bid Evaluation); elsewhere every switch reads
as off and no stand-in answers."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

CONTROLS = "Award Test Environment Controls"
FIELDS = ("signing_outcome", "email_failure_organisations", "email_service_down", "status_service_down", "contracting_down", "event_delivery_down",
	"rule_unverified", "revised_treatment_unverified")
TEST_LABEL = "Test environment — no live award notices are sent."


def enabled() -> bool:
	return bool(frappe.conf.get("kt_bds_simulation_environment"))


def controls() -> dict[str, Any]:
	if not enabled():
		return {}
	doc = frappe.get_single(CONTROLS)
	return {f: doc.get(f) for f in FIELDS}


def flag(name: str) -> bool:
	return bool(cint(controls().get(name)))


def failing_organisations() -> set[str]:
	return {x.strip() for x in cstr(controls().get("email_failure_organisations")).replace(",", "\n").split("\n") if x.strip()}


def set_controls(**values) -> dict[str, Any]:
	if not enabled():
		raise frappe.PermissionError("Award simulation controls are available on a test environment only.")
	doc = frappe.get_single(CONTROLS)
	for key, value in values.items():
		if key not in FIELDS:
			raise ValueError(f"unknown Award control {key!r}")
		doc.set(key, value)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return controls()


def reset_controls() -> None:
	if not enabled():
		return
	doc = frappe.get_single(CONTROLS)
	for f in FIELDS:
		doc.set(f, 0 if f in ("email_service_down", "status_service_down", "contracting_down", "event_delivery_down", "rule_unverified",
			"revised_treatment_unverified") else "")
	doc.save(ignore_permissions=True)
