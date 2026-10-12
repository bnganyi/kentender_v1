# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.11 §4.10 — one Planning request to revise one Budget Line. A request and its outcome, never a revision: approved amounts change only through a successor Version (BUD-BR-028)."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class BudgetRevisionRequest(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
