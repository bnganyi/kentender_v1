# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_procurement.procurement_planning.write_family import PLANNING_WRITE_FAMILY


class DepartmentalPlanEntry(CommandWriteGuardMixin, Document):
	"""Shape validation only (at save). Completeness is enforced at submission
	by the lifecycle service — deliberately split, do not merge (NDS FU-04)."""

	command_write_family = PLANNING_WRITE_FAMILY

	def validate(self):
		super().validate()
		if self.title and len(self.title) > 160:
			frappe.throw(_("Title must be at most 160 characters."))
		if (self.quantity or 0) <= 0:
			frappe.throw(_("Quantity must be greater than zero."))
		if self.indicative_amount is not None and self.indicative_amount < 0:
			frappe.throw(_("Indicative amount cannot be negative."))
		if self.source_origin == "Accepted Departmental Need" and not self.need:
			frappe.throw(_("A Need-origin entry must reference its accepted Need."))
		if self.source_origin == "Direct departmental requirement" and (self.need or self.need_revision):
			frappe.throw(_("A direct entry must not reference a Need."))
