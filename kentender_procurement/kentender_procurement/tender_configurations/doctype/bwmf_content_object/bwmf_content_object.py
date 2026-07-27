# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BWMFContentObject(Document):
	def validate(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.guards import (
			enforce_doctype_immutability,
		)

		enforce_doctype_immutability(self)

	def on_trash(self):
		if frappe.flags.get("bwmf_force_clear"):
			return
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
			assert_content_not_deletable,
		)

		assert_content_not_deletable(self.content_ref)
