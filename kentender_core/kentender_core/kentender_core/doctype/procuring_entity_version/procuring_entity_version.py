# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class ProcuringEntityVersion(Document):
	def validate(self):
		if not self.timezone:
			self.timezone = "Africa/Nairobi"
		if self.version_no and self.version_no > 1 and not (self.change_reason or "").strip():
			frappe.throw(_("Change reason is required for every version after the initial draft"))
