# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cstr


# Publication setup fields only — never tender configuration / STD / schema content.
PUBLICATION_SETUP_FIELDS = frozenset(
	{
		"publication_datetime",
		"clarification_deadline",
		"submission_deadline",
		"opening_datetime",
		"supplier_visibility",
		"tender_notice",
		"bidder_workspace_activation",
		"status",
	}
)

PACKAGE_LOCKED_FIELDS = frozenset(
	{
		"configuration",
		"confirmed_package",
		"document_hash",
		"package_payload",
		"configuration_ref",
	}
)


class ITTenderPublicationRecord(Document):
	def validate(self):
		if self.is_new() or getattr(self.flags, "ignore_publication_boundary", False):
			return
		prior_status = cstr(frappe.db.get_value(self.doctype, self.name, "status") or "")
		if prior_status in ("Cancelled", "Returned"):
			frappe.throw(
				frappe._("Cancelled or returned publication records cannot be edited."),
				title="PUBLICATION_LOCKED",
			)
		# Block mutation of package-bound identity / payload fields.
		for field in PACKAGE_LOCKED_FIELDS:
			db_val = frappe.db.get_value(self.doctype, self.name, field)
			if cstr(self.get(field) or "") != cstr(db_val or ""):
				frappe.throw(
					frappe._(
						"Publications cannot change the confirmed tender document package "
						"or tender configuration artifacts."
					),
					title="PUBLICATION_BOUNDARY",
				)
