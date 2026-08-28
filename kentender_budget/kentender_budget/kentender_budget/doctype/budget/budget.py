# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §4.1 — the stable identity of one PE/FY procurement budget."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class Budget(Document):
	def validate(self):
		self._assert_one_budget_per_pe_fy()
		self._assert_currency_immutable()
		self.title = self._derived_title()

	def _assert_one_budget_per_pe_fy(self):
		# BUD-BR-002 — at most one Budget for a PE/FY pair.
		existing = frappe.db.get_value(
			"Budget",
			{
				"procuring_entity": self.procuring_entity,
				"financial_year": self.financial_year,
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("A Budget already exists for this Procuring Entity and Financial Year: {0}").format(
					existing
				),
				frappe.DuplicateEntryError,
			)

	def _assert_currency_immutable(self):
		if self.is_new():
			return
		existing_currency = frappe.db.get_value("Budget", self.name, "currency")
		if existing_currency and existing_currency != self.currency:
			frappe.throw(_("Budget currency is immutable after creation."))

	def _derived_title(self) -> str:
		pe_name = frappe.db.get_value("Procuring Entity", self.procuring_entity, "legal_name") or self.procuring_entity
		fy_label = frappe.db.get_value("Financial Year", self.financial_year, "label") or self.financial_year
		return f"{pe_name} procurement budget {fy_label}"
