# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared guards for Bid Evaluation commands (EVL-CHG-001 v0.4 §5.7, §7.2, §8).

A closed evaluation (No evaluation required, Cancelled) accepts nothing. An
authoritative suspension pauses committee decisions, requests and report
signing; appointment and personal-declaration actions continue only where
the recorded instruction explicitly permits those administrative actions
(§5.7), and there is no local Resume. Guards collect every applicable reason
so the caller raises them together (§8)."""

from __future__ import annotations

import json

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services.errors import Guards

#: Administrative actions an instruction may permit during a suspension.
ADMINISTRATIVE = ("appointments", "declarations")


def closed(doc, guards: Guards) -> Guards:
	if doc.state == "Cancelled":
		guards.add("EVL_CANCELLED", cancellation=cstr(doc.cancellation_event))
	elif doc.state == "No evaluation required":
		guards.add("EVL_VERSION_CONFLICT", reason="no_evaluation_required")
	return guards


def suspension(doc, action: str, guards: Guards) -> Guards:
	"""`action` is one of ADMINISTRATIVE, or any other action (always paused)."""
	if not doc.suspended:
		return guards
	event = frappe.db.get_value("Evaluation Source Event", doc.suspension_event, ["instruction_reference", "authority", "permitted_actions_json"], as_dict=True) or {}
	permitted = json.loads(event.get("permitted_actions_json") or "[]")
	if action in ADMINISTRATIVE and action in permitted:
		return guards
	return guards.add("EVL_SUSPENDED", instruction=cstr(event.get("instruction_reference")), authority=cstr(event.get("authority")))


def open_case(doc, action: str = "") -> Guards:
	"""Closed and suspension checks for one action."""
	guards = Guards()
	closed(doc, guards)
	if not guards:
		suspension(doc, action, guards)
	return guards
