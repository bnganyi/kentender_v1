# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class RequisitionTechnicalRequirement(CommandWriteGuardMixin, Document):
	"""A child row of a guarded parent: inserted, changed and deleted only inside the
	`command_write("Requisitions")` window of the owning command (RG-06). Frappe's REST create inserts
	a child row on its own and a delete runs only this controller, so the parent's guard
	does not see either."""

	command_write_family = "Requisitions"
