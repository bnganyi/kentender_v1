# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document


class STDCfgPackage(Document):
	def before_insert(self):
		self.package_id = self.package_code

	def validate(self):
		self.package_id = self.package_code
