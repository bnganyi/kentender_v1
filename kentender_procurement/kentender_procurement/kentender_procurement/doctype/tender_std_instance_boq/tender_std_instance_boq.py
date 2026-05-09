# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender STD Instance BOQ aggregate — STDINST-0300."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.boq import (
	assert_boq_referential_integrity,
	assert_no_duplicate_bill_codes,
	assert_no_duplicate_item_codes,
	assert_published_boq_rows_honored,
)


class TenderSTDInstanceBOQ(Document):
	def validate(self) -> None:
		self._validate_unique_instance()
		assert_no_duplicate_bill_codes(self)
		assert_no_duplicate_item_codes(self)
		assert_boq_referential_integrity(self)
		if not self.is_new():
			prev = frappe.get_doc("Tender STD Instance BOQ", self.name)
			assert_published_boq_rows_honored(prev, self)

	def _validate_unique_instance(self) -> None:
		if not self.tender_std_instance:
			return
		existing = frappe.get_all(
			"Tender STD Instance BOQ",
			filters={
				"tender_std_instance": self.tender_std_instance,
				"name": ["!=", self.name],
			},
			pluck="name",
			limit=1,
		)
		if existing:
			frappe.throw(
				_("A BOQ already exists for STD Instance {0}: {1}").format(
					self.tender_std_instance,
					existing[0],
				),
				title=_("Duplicate STD Instance BOQ"),
			)
