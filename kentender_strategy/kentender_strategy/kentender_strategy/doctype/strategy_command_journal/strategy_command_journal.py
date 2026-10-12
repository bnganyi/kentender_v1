# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class StrategyCommandJournal(CommandWriteGuardMixin, Document):
	"""The replay-protection journal: a key row is written only by `strategy_idempotency`, inside
	`command_write("Strategy")` (RG-40). A technical user who could delete a key row would let its
	command run twice."""

	command_write_family = "Strategy"
