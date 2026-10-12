# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class KTSMSupplierProfile(CommandWriteGuardMixin, Document):
	"""The governance state (approval, operational, compliance, submit/approve/return/reject stamps)
	changes only through `services/governance.py`, inside `command_write("Supplier Registry")`, for
	every user and every state (RG-13). The mixin compares the stored record with the edit, so
	moving an Approved profile back to Draft is refused as well as moving it forward; a registry
	officer may still edit the descriptive fields below."""

	command_write_family = "Supplier Registry"
	command_user_insert = True
	command_user_editable_fields = ("erpnext_supplier", "identity_display", "risk_level", "external_user", "is_active")

	def user_editable_when(self, before) -> bool:  # noqa: ARG002
		return True

	def validate(self):
		super().validate()
		filters: dict = {"erpnext_supplier": self.erpnext_supplier}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("KTSM Supplier Profile", filters):
			frappe.throw(_("A KenTender profile already exists for this ERPNext Supplier."))

	def before_insert(self):
		if self.erpnext_supplier and not (self.identity_display or "").strip():
			self.identity_display = frappe.db.get_value(
				"Supplier", self.erpnext_supplier, "supplier_name"
			) or ""
