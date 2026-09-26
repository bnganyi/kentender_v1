# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class STDCfgAssistanceBatch(Document):
	def validate(self):
		if self.is_new() and not self.draft_record_version_snapshot:
			self.draft_record_version_snapshot = (
				frappe.db.get_value("STD Cfg Draft", self.draft_id, "record_version") or 0
			)
