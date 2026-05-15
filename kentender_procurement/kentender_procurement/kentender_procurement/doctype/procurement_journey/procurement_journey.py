# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Journey — cross-module navigation aggregate (ADR-PLC-002; not legal source of truth)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.procurement_lifecycle.constants import JOURNEY_STEP_KEYS_IN_ORDER
from kentender_procurement.procurement_lifecycle.journey_status_category import JOURNEY_STATUS_CATEGORY_VALUES


class ProcurementJourney(Document):
	def before_insert(self):
		if not self.created_at:
			self.created_at = now_datetime()
		self.updated_at = now_datetime()

	def before_save(self):
		self.updated_at = now_datetime()

	def validate(self):
		"""LV-R1-003-03 — reject values that cannot represent a valid aggregate snapshot.

		This does **not** re-validate source module legal state; R3 services own aggregation.
		It only blocks garbage enums / unknown stage keys / inconsistent counters so Desk/API
		cannot silently invent lifecycle vocabulary (PLC-CURSOR-002).

		R1-010 / ADR-PLC-002: **never** persist changes to source DocTypes from this
		controller — journey rows are read models / navigation only.
		"""
		if self.current_status_category not in JOURNEY_STATUS_CATEGORY_VALUES:
			frappe.throw(
				_("Current Status Category must be a standard journey category (R1-001)."),
				title=_("Invalid status category"),
			)
		if self.current_stage_key not in JOURNEY_STEP_KEYS_IN_ORDER:
			frappe.throw(
				_("Current Stage Key must match a spine step_key from JOURNEY_STEP_CONFIG (R1-002)."),
				title=_("Invalid stage key"),
			)
		if int(self.blocker_count or 0) < 0 or int(self.critical_blocker_count or 0) < 0:
			frappe.throw(_("Blocker counts cannot be negative."), title=_("Invalid blockers"))
		self._validate_journey_steps_table()

	def _validate_journey_steps_table(self) -> None:
		"""LV-R1-004 — child rows: unique order and keys; child DocType validates row fields."""
		rows = list(self.get("steps") or [])
		if not rows:
			return
		orders: list[int] = []
		keys: list[str] = []
		for row in rows:
			orders.append(int(row.step_order or 0))
			keys.append((row.step_key or "").strip())
		if any(o < 1 for o in orders):
			frappe.throw(_("Each step must have step_order >= 1."), title=_("Invalid journey steps"))
		if len(orders) != len(set(orders)):
			frappe.throw(_("Step Order must be unique within a journey."), title=_("Duplicate step order"))
		if any(not k for k in keys):
			frappe.throw(_("Each step must have a non-empty Step Key."), title=_("Invalid journey steps"))
		if len(keys) != len(set(keys)):
			frappe.throw(_("Step Key must be unique within a journey."), title=_("Duplicate step key"))
