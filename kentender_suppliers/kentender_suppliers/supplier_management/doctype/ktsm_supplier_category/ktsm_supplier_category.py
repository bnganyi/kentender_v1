# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KTSMSupplierCategory(Document):
	def validate(self):
		if self.parent_category and self.parent_category == self.name:
			frappe.throw(_("Parent category cannot be the same as the category."))
		# B3 / CAT-003: no cycles in the parent chain (walk from parent up)
		if self.parent_category:
			seen: set = set()
			cur = self.parent_category
			depth = 0
			while cur and depth < 64:
				if cur in seen:
					frappe.throw(_("Category hierarchy cannot contain a cycle."))
				seen.add(cur)
				if self.name and cur == self.name:
					frappe.throw(_("Category hierarchy cannot contain a cycle."))
				cur = frappe.db.get_value("KTSM Supplier Category", cur, "parent_category")
				depth += 1
