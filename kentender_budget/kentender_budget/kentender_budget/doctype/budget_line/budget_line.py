# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class BudgetLine(Document):
	def validate(self):
		if flt(self.approved_amount) <= 0:
			frappe.throw("Approved amount must be positive.")
		available = (
			flt(self.approved_amount) - flt(self.amount_reserved) - flt(self.amount_committed)
		)
		if available < 0:
			frappe.throw("Budget Line Available cannot be negative.")

		# XMOD-STR-001 — belt-and-braces Strategy Reference (Desk / direct save).
		# save_budget_line already applied + flagged skip to avoid double Active checks.
		if getattr(self.flags, "skip_budget_strategy_validate", False):
			self.primary_strategy_linked = 1 if (self.primary_target_code or "").strip() else 0
			return

		target_id = (self.primary_target_id or "").strip()
		if target_id:
			try:
				from kentender_strategy.services.strategy_consumer import (
					apply_budget_primary_strategy_reference,
				)

				require_active = self.is_new() or self.has_value_changed("primary_target_id")
				apply_budget_primary_strategy_reference(
					self, target_id, require_active=require_active
				)
			except ImportError:
				pass
		else:
			self.primary_strategy_linked = 0
			return

		self.primary_strategy_linked = 1 if (self.primary_target_code or "").strip() else 0
