# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §4.3 — the stable identity of one funded purpose across Budget Versions."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class ProcurementBudgetLine(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
