# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KTSMSupplierProfile(Document):
	def validate(self):
		filters: dict = {"erpnext_supplier": self.erpnext_supplier}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("KTSM Supplier Profile", filters):
			frappe.throw(_("A KenTender profile already exists for this ERPNext Supplier."))
		# B4: governance field transitions only via service (when not bypassing from services)
		if not self.is_new() and not self.flags.get("bypass_governance"):
			st = self.get("approval_status")
			locked = st in ("Submitted", "Under Review", "Rejected", "Approved")
			if locked:
				for f in (
					"approval_status",
					"operational_status",
					"compliance_status",
				):
					if self.has_value_changed(f):
						frappe.throw(
							_(
								"Governance status can only be changed from Supplier Management workflow"
								" (not by editing this form)."
							)
						)

	def before_insert(self):
		if self.erpnext_supplier and not (self.identity_display or "").strip():
			self.identity_display = frappe.db.get_value(
				"Supplier", self.erpnext_supplier, "supplier_name"
			) or ""
