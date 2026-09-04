# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §4.1 — the stable identity of one fiscal year's
procurement allocation record. One site is one Procuring Entity: there is no
`procuring_entity` field, and at most one Procurement Budget exists per
Fiscal Year (BUD-BR-002)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class ProcurementBudget(Document):
	def validate(self):
		self._assert_one_budget_per_fy()
		self._assert_currency_immutable()
		self.title = self._derived_title()

	def _assert_one_budget_per_fy(self):
		# BUD-BR-002 — at most one Budget per Fiscal Year. The `fiscal_year`
		# field's own `unique: 1` is the database-level guard; this is the
		# friendlier application-level message on the same invariant.
		existing = frappe.db.get_value(
			"Procurement Budget",
			{"fiscal_year": self.fiscal_year, "name": ["!=", self.name or ""]},
			"name",
		)
		if existing:
			frappe.throw(
				_("A Budget already exists for this Fiscal Year: {0}").format(existing),
				frappe.DuplicateEntryError,
				title="BUDGET_ALREADY_EXISTS",
			)

	def _assert_currency_immutable(self):
		if self.is_new():
			return
		existing_currency = frappe.db.get_value("Procurement Budget", self.name, "currency")
		if existing_currency and existing_currency != self.currency:
			frappe.throw(_("Budget currency is immutable after creation."))

	def _derived_title(self) -> str:
		entity_name = frappe.db.get_single_value("Site Procuring Entity", "pe_name") or ""
		return f"{entity_name} procurement budget {self.fiscal_year}".strip()
