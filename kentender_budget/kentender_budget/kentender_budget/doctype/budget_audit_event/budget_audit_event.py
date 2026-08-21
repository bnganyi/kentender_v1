# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class BudgetAuditEvent(Document):
	def on_trash(self):
		# Pack Phase 8 — audit records are immutable through the UI.
		if frappe.flags.in_migrate or frappe.flags.in_install:
			return
		if frappe.flags.get("allow_budget_audit_purge"):
			return
		frappe.throw(_("Budget Audit Event records cannot be deleted"), frappe.ValidationError)
