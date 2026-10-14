# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class ContractTransactionLink(CommandWriteGuardMixin, Document):
	"""Written only by Contract Management commands (`command_write("Contract Management")`); never by a Desk save (plan D3)."""

	command_write_family = "Contract Management"
