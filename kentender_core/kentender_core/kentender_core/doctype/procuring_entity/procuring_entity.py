# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class ProcuringEntity(Document):
	def validate(self):
		if not (self.legal_name or "").strip() and (self.entity_name or "").strip():
			self.legal_name = self.entity_name
		if not (self.entity_name or "").strip() and (self.legal_name or "").strip():
			self.entity_name = self.legal_name
		if not (self.entity_reference or "").strip():
			self.entity_reference = make_autoname("PE-.########")
		if not self.status:
			self.status = "Active"
