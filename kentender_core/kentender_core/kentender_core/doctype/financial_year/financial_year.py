# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


def _generate(start_year: int) -> dict:
	"""BR-003 — identifier/label/dates are generated from start_year and cannot diverge."""
	start_year = int(start_year)
	end_year = start_year + 1
	return {
		"name": f"FY-{start_year}-{end_year}",
		"label": f"{start_year}/{str(end_year)[-2:]}",
		"start_date": getdate(f"{start_year}-07-01"),
		"end_date": getdate(f"{end_year}-06-30"),
	}


class FinancialYear(Document):
	def autoname(self):
		self.name = _generate(self.start_year)["name"]

	def validate(self):
		if not self.timezone:
			self.timezone = "Africa/Nairobi"

		generated = _generate(self.start_year)
		if self.is_new():
			self.label = generated["label"]
			self.start_date = generated["start_date"]
			self.end_date = generated["end_date"]
		else:
			# AC-007 — once persisted, generated fields are immutable at the database
			# level too, not only hidden in the UI. Compare the DOCUMENT BEING SAVED
			# (self.*, which carries whatever a direct API/save call just set) against
			# what start_year generates — not the DB's existing row against a fresh
			# regeneration, which only catches start_year itself changing and misses
			# label/start_date/end_date being tampered with directly.
			existing_start_year = frappe.db.get_value("Financial Year", self.name, "start_year")
			if existing_start_year is not None and int(existing_start_year) != int(self.start_year):
				frappe.throw(
					_("Financial Year start year cannot be changed once created"), frappe.ValidationError
				)
			if (
				str(self.label) != generated["label"]
				or getdate(self.start_date) != generated["start_date"]
				or getdate(self.end_date) != generated["end_date"]
			):
				frappe.throw(
					_("Financial Year identifier, label and dates are generated and cannot be changed"),
					frappe.ValidationError,
				)
