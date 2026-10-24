# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 §4.12 — one coordinated entry recognising an independently registered contract's confirmed funding charge. Written only by the Budget services; an Approved entry is immutable."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class ExistingContractCommitmentEntry(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
