# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class SourceDocumentRegistry(Document):
	def on_trash(self):
		if self._is_referenced_by_template_version():
			frappe.throw(
				_(
					"Cannot delete Source Document Registry {0} because it is referenced by an STD template version."
				).format(self.source_document_code),
				title=_("Delete blocked"),
			)

	def _is_referenced_by_template_version(self) -> bool:
		if not frappe.db.exists("DocType", "STD Template Version"):
			return False
		return bool(
			frappe.db.exists(
				"STD Template Version",
				{"source_document_code": self.source_document_code},
			)
		)

