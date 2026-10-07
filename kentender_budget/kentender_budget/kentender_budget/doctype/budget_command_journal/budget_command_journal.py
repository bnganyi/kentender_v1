# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-16 / AUD-XC-002 / AUD-XC-131 — Budget's command idempotency journal. A
command claims its key by inserting a row (the unique index is the authority),
then records its result on that row. Written only by
`budget_idempotency.run_idempotent` inside the Budget write window; never edited
or deleted by a user."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class BudgetCommandJournal(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY

	def on_trash(self):
		if frappe.flags.in_migrate or frappe.flags.in_install:
			return
		super().on_trash()
