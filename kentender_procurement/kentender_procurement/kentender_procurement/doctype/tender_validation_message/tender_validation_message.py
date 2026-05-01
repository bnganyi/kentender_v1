# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class TenderValidationMessage(Document):
	"""Child table: validation / rule engine messages (populated in later steps)."""
