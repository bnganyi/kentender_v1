# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BWMFValidationReport(Document):
	def validate(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.guards import (
			enforce_doctype_immutability,
		)

		enforce_doctype_immutability(self)
