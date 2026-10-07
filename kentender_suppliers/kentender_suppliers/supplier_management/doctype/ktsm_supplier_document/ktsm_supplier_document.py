# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class KTSMSupplierDocument(CommandWriteGuardMixin, Document):
	"""Verification (status, verifier, reason) and the external-upload mark change only through
	`services/governance.py` or the upload endpoint, inside `command_write("Supplier Registry")`
	(RG-13); the descriptive fields stay editable."""

	command_write_family = "Supplier Registry"
	command_user_insert = True
	command_user_editable_fields = (
		"supplier_profile",
		"document_type",
		"document_name",
		"file",
		"document_number",
		"issue_date",
		"expiry_date",
		"is_current",
	)

	def user_editable_when(self, before) -> bool:  # noqa: ARG002
		return True

	def validate(self):
		super().validate()
		# B3: inactive type
		if self.document_type:
			if not frappe.db.get_value("KTSM Document Type", self.document_type, "is_active"):
				frappe.throw(_("This document type is not active for new use."))
		if self.expires_required() and not self.expiry_date:
			frappe.throw(_("Expiry date is required for this document type."))
		if self.verification_status == "Rejected" and not (self.rejection_reason or "").strip():
			frappe.throw(_("Rejection reason is required when verification is Rejected."))

	def on_update(self):
		# B2: one current per profile + type
		if not (self.is_current and self.document_type and self.supplier_profile):
			return
		others = frappe.get_all(
			"KTSM Supplier Document",
			filters={
				"supplier_profile": self.supplier_profile,
				"document_type": self.document_type,
				"name": ("!=", self.name),
				"is_current": 1,
			},
			pluck="name",
		)
		for o in others or []:
			frappe.db.set_value("KTSM Supplier Document", o, "is_current", 0)

	def expires_required(self):
		if not self.document_type:
			return False
		return bool(
			frappe.db.get_value("KTSM Document Type", self.document_type, "expires")
		)
