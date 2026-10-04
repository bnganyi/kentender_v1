# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Is electronic bid opening available? (BOP-CHG-001 v0.10 §8, §15; plan D5, D16;
owner decision OD-C.)

One answer, in a fixed order:

1. `BOP_OPENING_PROFILE_UNAVAILABLE`: production opening is not enabled
   (`production_bid_opening_enabled`, read only here, default false) and this
   is not a test environment; or the test controls say the opening service is
   down; or the operating profile is incomplete; or no renderer or signing
   service answers.
2. `BOP_CREDENTIAL_UNAVAILABLE`: the tender box's custody service is not healthy.

Production stays unavailable until the approved Trust, custody and legal
operating profile exists (TRUST-ADR-001 v0.1 §3). A stand-in never makes it
available in production."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_opening.services import custody, errors, renderer, settings, simulation

PRODUCTION_KEY = "production_bid_opening_enabled"


def _blocked(code: str, reason: str) -> dict[str, Any]:
	return {"available": False, "code": code, "message": errors.message(code), "reason": reason}


def get_opening_availability() -> dict[str, Any]:
	from kentender_procurement.proceedings.services import signing

	production = bool(cint(frappe.conf.get(PRODUCTION_KEY)))
	if not production and not simulation.enabled():
		return _blocked("BOP_OPENING_PROFILE_UNAVAILABLE", "production_not_enabled")
	if simulation.enabled() and simulation.controls()["opening_profile_down"]:
		return _blocked("BOP_OPENING_PROFILE_UNAVAILABLE", "opening_service_down")
	if not settings.complete():
		return _blocked("BOP_OPENING_PROFILE_UNAVAILABLE", "operating_profile_incomplete")
	if not custody.healthy():
		return _blocked("BOP_CREDENTIAL_UNAVAILABLE", "custody_unavailable")
	if not renderer.healthy():
		return _blocked("BOP_OPENING_PROFILE_UNAVAILABLE", "renderer_unavailable")
	if signing.service() is None:
		return _blocked("BOP_OPENING_PROFILE_UNAVAILABLE", "signing_unavailable")
	return {"available": True, "code": "", "message": "", "reason": ""}


def attendance_channel_available() -> bool:
	"""The published public attendance service (BOP-CHG-001 v0.10 §10 branch (4)).
	No production channel is configured; on a test environment the stand-in
	channel answers unless the test controls take it down."""
	if simulation.enabled():
		return not simulation.controls()["attendance_service_down"]
	return False
