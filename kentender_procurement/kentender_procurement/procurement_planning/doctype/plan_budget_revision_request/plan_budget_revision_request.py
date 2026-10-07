# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.27 §4.7 BudgetRevisionRequest — the Planner's request that the Budget Officer revise one over-budget line. Created only by RequestBudgetRevision; status changes only from the Budget outcome event. Creates no Budget record, reservation or ledger event in Planning."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_procurement.procurement_planning.write_family import PLANNING_WRITE_FAMILY


class PlanBudgetRevisionRequest(CommandWriteGuardMixin, Document):
	command_write_family = PLANNING_WRITE_FAMILY
