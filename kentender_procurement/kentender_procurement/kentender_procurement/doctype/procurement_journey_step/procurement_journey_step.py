# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Child row for :doc:`Procurement Journey` — one lifecycle step snapshot (ADR-PLC-002)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.procurement_lifecycle.journey_status_category import JOURNEY_STATUS_CATEGORY_VALUES


class ProcurementJourneyStep(Document):
	def validate(self):
		if not (self.step_key or "").strip():
			frappe.throw(_("Step Key is required."), title=_("Invalid step"))
		if int(self.step_order or 0) < 1:
			frappe.throw(_("Step Order must be >= 1."), title=_("Invalid step order"))
		if self.status_category not in JOURNEY_STATUS_CATEGORY_VALUES:
			frappe.throw(
				_("Status Category must be a standard journey category (R1-001)."),
				title=_("Invalid status category"),
			)
		if int(self.blocker_count or 0) < 0:
			frappe.throw(_("Blocker count cannot be negative."), title=_("Invalid blockers"))
