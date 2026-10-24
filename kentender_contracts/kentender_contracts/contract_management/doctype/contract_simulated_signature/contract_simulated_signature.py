# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class ContractSimulatedSignature(CommandWriteGuardMixin, Document):
	"""The simulation provider's own ledger (plan D8). Written only by `kentender_contracts.simulation.signing`, inside `command_write`."""

	command_write_family = "Contract Management"
