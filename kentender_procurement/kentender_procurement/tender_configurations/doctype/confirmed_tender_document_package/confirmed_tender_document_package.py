# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cstr


class ConfirmedTenderDocumentPackage(Document):
	def validate(self):
		if self.is_new():
			return
		prior = frappe.db.get_value(
			"Confirmed Tender Document Package", self.name, ["package_status", "document_hash"], as_dict=True
		)
		if not prior:
			return
		# Invalidated packages stay immutable except status/meta already set.
		if cstr(prior.package_status) == "Invalidated":
			if cstr(self.package_status) != "Invalidated" or cstr(self.document_hash) != cstr(
				prior.document_hash
			):
				frappe.throw(
					frappe._("Invalidated tender document packages are immutable."),
					title="PACKAGE_IMMUTABLE",
				)
		# Confirmed / awaiting packages: lock artifact fields (handoff APIs use flags).
		if getattr(self.flags, "ignore_package_immutability", False):
			return
		if cstr(prior.package_status) in ("Confirmed", "Awaiting Publication Setup"):
			locked = (
				"tender_html",
				"document_hash",
				"bidder_submission_schema",
				"evaluation_schema",
				"price_schedule_schema",
				"forms_evidence_schema",
				"contract_carry_forward",
				"configuration_version",
				"std_version",
			)
			for field in locked:
				if cstr(self.get(field)) != cstr(frappe.db.get_value(self.doctype, self.name, field) or ""):
					frappe.throw(
						frappe._("Confirmed tender document package artifacts are immutable."),
						title="PACKAGE_IMMUTABLE",
					)
