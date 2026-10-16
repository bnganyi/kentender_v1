# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.13 proposal (owner decision 1, 16 October 2026) — one correction that lowers a Closed commitment: its reason, its evidence, who recorded and who decided it, and the amounts
before and after. A correction is its own record; the original conversion and closure events are never edited. Written only by the Budget services."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class CommitmentCorrection(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
