# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender STD Generated Output — STDINST-0400."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.generated_output import (
	assert_draft_current_generated_output_content_guarded,
	assert_published_generated_output_honored,
)


class TenderSTDGeneratedOutput(Document):
	def validate(self) -> None:
		self._validate_single_published_per_instance_type()
		if not self.is_new():
			prev = frappe.get_doc("Tender STD Generated Output", self.name)
			assert_published_generated_output_honored(prev, self)
			assert_draft_current_generated_output_content_guarded(prev, self)

	def _validate_single_published_per_instance_type(self) -> None:
		if (self.output_status or "").strip() != "Published":
			return
		if not self.tender_std_instance or not self.output_type:
			return
		existing = frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": self.tender_std_instance,
				"output_type": self.output_type,
				"output_status": "Published",
				"name": ["!=", self.name],
			},
			pluck="name",
			limit=1,
		)
		if existing:
			frappe.throw(
				_("Another Published output exists for this STD Instance and output type: {0}").format(
					existing[0],
				),
				title=_("STD Generated Output"),
			)
