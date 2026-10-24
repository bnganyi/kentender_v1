# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The isolated cancellation-ground profile for the post-close route (TPR-CHG-001 v0.24 §5.12, §13.6 OF-F02: "the test supplies its ground evidence
explicitly, rather than deriving it from the fault").

Registered under `kt_tender_cancellation_ground_verifiers`. It answers only on a test environment (`kt_bds_simulation_environment`), and only with the
ground keys a test or browser world names in the test controls; anywhere else it declines and no ground is verified. It shows no label or notice to
any user (DEC-044): the evidence it returns reads like any documented legal-basis review."""

from __future__ import annotations

import frappe
from frappe.utils import cstr, now_datetime

CONTROLS = "Tender Test Environment Controls"


def enabled() -> bool:
	return bool(frappe.conf.get("kt_bds_simulation_environment"))


def controls() -> dict:
	if not enabled():
		return {}
	doc = frappe.get_single(CONTROLS)
	return {"verified_cancellation_grounds": cstr(doc.verified_cancellation_grounds)}


def set_controls(**values) -> dict:
	if not enabled():
		raise frappe.PermissionError("Tender simulation controls are available on a test environment only.")
	doc = frappe.get_single(CONTROLS)
	for key, value in values.items():
		if key != "verified_cancellation_grounds":
			raise ValueError(f"unknown Tender control {key!r}")
		doc.set(key, value)
	doc.save(ignore_permissions=True)
	return controls()


def reset_controls() -> None:
	if enabled():
		set_controls(verified_cancellation_grounds="")


def verify(*, tender: str, stage: str) -> dict:
	keys = [k.strip() for k in controls().get("verified_cancellation_grounds", "").replace("\n", ",").split(",") if k.strip()]
	at = str(now_datetime())
	return {"grounds": [{"key": k, "verified": True, "source": "Documented legal-basis review", "reference": f"GRD-{k}", "version": "1", "checked_at": at} for k in keys]}
