# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`GetSubmissionAvailability` (BDS-CHG-001 v0.8 §5.10, §7.4; plan D5): the one
gate that signature preparation, initial submission and replacement
submission all use.

`production_bid_submission_enabled` is read from the site configuration
only. It defaults to false and has no Desk, portal, API, business-role or
per-Tender control; nothing else in the code reads it. In order, the answer
is: the flag is off (or a test environment's GATE world closes it) →
`BDS_PRODUCTION_SUBMISSION_NOT_ENABLED`; the signing/trust service is missing
or unhealthy → `BDS_SIGNATURE_UNAVAILABLE`; trusted time or the tender box is
missing or unhealthy → `BDS_SUBMISSION_SERVICE_UNAVAILABLE`. Every refusal
creates nothing: no signature request, attempt, envelope or receipt."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_submission.services import gateways, simulation
from kentender_procurement.bid_submission.services.errors import MESSAGES, fail

FLAG = "production_bid_submission_enabled"


def production_enabled() -> bool:
	return bool(cint(frappe.conf.get(FLAG)))


def _refused(code: str) -> dict[str, Any]:
	return {"available": False, "code": code, "message": MESSAGES[code]}


def get_submission_availability() -> dict[str, Any]:
	if not production_enabled() or (simulation.enabled() and simulation.controls()["gate_closed"]):
		return _refused("BDS_PRODUCTION_SUBMISSION_NOT_ENABLED")
	if not gateways.trust_healthy():
		return _refused("BDS_SIGNATURE_UNAVAILABLE")
	if not (gateways.time_healthy() and gateways.custody_healthy()):
		return _refused("BDS_SUBMISSION_SERVICE_UNAVAILABLE")
	return {"available": True, "code": "", "message": ""}


def require_available() -> None:
	result = get_submission_availability()
	if not result["available"]:
		fail(result["code"])
