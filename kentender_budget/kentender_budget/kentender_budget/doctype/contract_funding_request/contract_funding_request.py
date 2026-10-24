# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 §§8.6/8.7 — the one request for a contract and target year, an exact increment or a correction subject. Written only by the Budget services."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class ContractFundingRequest(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
