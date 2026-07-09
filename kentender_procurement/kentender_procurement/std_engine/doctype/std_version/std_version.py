# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document



class STDVersion(Document):

	def validate(self) -> None:
		from kentender_procurement.std_engine.doctype.validators import validate_lifecycle_state

		validate_lifecycle_state(self.lifecycle_state)

