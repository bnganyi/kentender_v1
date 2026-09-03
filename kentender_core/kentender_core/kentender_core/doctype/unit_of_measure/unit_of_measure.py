# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Governed unit catalogue owned by Configuration & Governance.

NDS-CHG-001 v1.1 §3 places the unit catalogue under Configuration & Governance;
consuming modules resolve a unit from here and never store a free-text value
(§1.1 removes the free-text `Other` unit, §17 forbids reintroducing it).
"""

from __future__ import annotations

from frappe.model.document import Document


class UnitOfMeasure(Document):
	def validate(self):
		self.unit_code = (self.unit_code or "").strip().upper()
		self.unit_label = (self.unit_label or "").strip()
		if not self.status:
			self.status = "Active"
