# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 §4.12 — one allocation row of an existing-contract entry. Child of the entry; written with it."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY
from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class ExistingContractEntryRow(CommandWriteGuardMixin, Document):
	"""A child row of a guarded parent: inserted, changed and deleted only inside the Budget command-write window of the owning command. Frappe's
	REST create inserts a child row on its own and a delete runs only this controller, so the parent's guard does not see either."""

	command_write_family = BUDGET_WRITE_FAMILY
