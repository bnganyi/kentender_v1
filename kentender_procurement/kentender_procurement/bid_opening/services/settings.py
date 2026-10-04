# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Operating-profile inputs (BOP-CHG-001 v0.10 §5 presence "timeout are
operating-profile inputs"; §7 RequestOpeningRegister self-service; §10 join
window; plan D7).

A value left unset means the approved operating profile has not supplied it,
and opening is not available (availability.py). On a test environment the
stand-in values are the plan's: a 60-second presence lapse, the public join
opening five minutes before the scheduled time (§10: join from 10:55 for an
11:00 opening), and self-service register copies."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_opening.services import simulation

SETTINGS = "Bid Opening Settings"
FIELDS = ("presence_lapse_seconds", "public_join_lead_minutes", "register_self_service")
SIMULATION_DEFAULTS = {"presence_lapse_seconds": 60, "public_join_lead_minutes": 5, "register_self_service": 1}


def get() -> dict[str, Any]:
	saved = frappe.db.get_singles_dict(SETTINGS) or {}
	out: dict[str, Any] = {}
	for field in FIELDS:
		value = saved.get(field)
		if value in (None, ""):
			out[field] = None
		elif field == "register_self_service":
			out[field] = cint(value)
		else:
			out[field] = cint(value) or None  # a zero duration is not a profile value
	if simulation.enabled():
		out = {f: out[f] if out[f] is not None else SIMULATION_DEFAULTS[f] for f in FIELDS}
	elif out["register_self_service"] is None:
		out["register_self_service"] = 0
	return out


def complete() -> bool:
	values = get()
	return bool(values["presence_lapse_seconds"]) and values["public_join_lead_minutes"] is not None
