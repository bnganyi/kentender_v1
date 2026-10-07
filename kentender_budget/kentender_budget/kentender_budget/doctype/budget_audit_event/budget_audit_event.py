# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The funding ledger (BUD §4.7). Append-only: inserted only by the Budget
services (`budget_audit_contracts.record_event`), never edited, and deleted only
by test/seed clean-up under `maintenance_write` (AUD-XC-006, AUD-XC-013)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class BudgetAuditEvent(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY

	def validate(self):
		super().validate()
		# A ledger row is written once: even the owning service never changes it.
		if not self.is_new():
			frappe.throw(_("Budget Audit Event records cannot be changed"), frappe.ValidationError)

	def on_trash(self):
		# Pack Phase 8 — audit records are immutable through the UI. Migration
		# and install may drop them; test/seed clean-up opens the maintenance
		# window (never reachable from a request).
		if frappe.flags.in_migrate or frappe.flags.in_install:
			return
		super().on_trash()
