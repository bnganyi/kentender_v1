# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Child table: derived model readiness placeholders (doc 5 §10, WH-004)."""

import frappe
from frappe.exceptions import ValidationError
from frappe.model.document import Document


class TenderDerivedModelReadiness(Document):
	def validate(self) -> None:
		status = (self.status or "").strip()
		if status in ("Placeholder", "Missing"):
			if not (self.deferred_reason or "").strip():
				frappe.throw(
					frappe._(
						"Deferred Reason is required when Status is Placeholder or Missing (doc 5 §10)."
					),
					title=frappe._("Derived model readiness"),
					exc=ValidationError,
				)
