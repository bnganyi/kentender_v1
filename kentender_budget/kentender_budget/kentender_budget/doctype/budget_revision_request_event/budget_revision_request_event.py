# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.11 §8.5 item 3 — the transactional outbox for BudgetRevisionRequestOutcome.v1: committed with the state change, delivered idempotently and in order, retried until delivered."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class BudgetRevisionRequestEvent(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
