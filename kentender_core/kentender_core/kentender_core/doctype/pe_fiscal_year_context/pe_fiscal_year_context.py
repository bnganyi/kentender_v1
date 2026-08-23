# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


def _context_name(procuring_entity: str, financial_year: str) -> str:
	pe_short = procuring_entity.removeprefix("PE-")
	fy_years = financial_year.removeprefix("FY-")
	return f"CTX-{pe_short}-{fy_years}"


class PEFiscalYearContext(Document):
	def autoname(self):
		# BR-001 — deriving the docname from (procuring_entity, financial_year)
		# makes Frappe's own name-uniqueness the real database-level constraint
		# for "one stable context per pair", not just an app-level validate check.
		self.name = _context_name(self.procuring_entity, self.financial_year)

	def validate(self):
		if self.active_from and self.active_to and get_datetime(self.active_to) <= get_datetime(self.active_from):
			frappe.throw(_("Active To must be later than Active From"), frappe.ValidationError)
