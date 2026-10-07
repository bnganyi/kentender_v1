# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_procurement.procurement_planning.write_family import PLANNING_WRITE_FAMILY


class AnnualPlanItem(CommandWriteGuardMixin, Document):
	"""Shape validation only; readiness blockers and lifecycle rules live in services."""

	command_write_family = PLANNING_WRITE_FAMILY

	def validate(self):
		super().validate()
		if self.title and not (5 <= len(self.title) <= 160):
			frappe.throw(_("Plan Item title must be 5–160 characters."))
		if self.description and not (10 <= len(self.description) <= 1000):
			frappe.throw(_("Procurement description must be 10–1,000 characters."))
		if self.aggregation_reason and not (20 <= len(self.aggregation_reason) <= 500):
			frappe.throw(_("Aggregation reason must be 20–500 characters."))
