# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class SupplierBusinessProfile(Document):
	def validate(self) -> None:
		# Written only by the Supplier Accounts commands (`flags.kt_account_command`),
		# like the Account it belongs to; it holds personal data (owners, ages).
		if not self.flags.get("kt_account_command"):
			frappe.throw("%s records change only through Supplier Account commands." % self.doctype)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
