# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class ProcurementBudgetVersion(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY

	def validate(self):
		super().validate()
		if self.based_on_budget_version and not self.revision_type:
			frappe.throw(_("Revision type is required for a successor Budget Version."))
		if not self.based_on_budget_version and self.revision_type:
			frappe.throw(_("Revision type is not permitted on the initial Budget Version."))
		if self.approval_date and getdate(self.approval_date) > getdate():
			frappe.throw(_("Approval date cannot be in the future."))
