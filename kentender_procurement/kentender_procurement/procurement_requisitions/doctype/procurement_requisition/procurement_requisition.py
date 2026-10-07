# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Requisition: written only by the Requisitions commands (AUD-XC-013). A Desk save, REST
call or script outside `command_write("Requisitions")` is refused; see
`kentender_core.services.command_write_guard`."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class ProcurementRequisition(CommandWriteGuardMixin, Document):
	command_write_family = "Requisitions"
