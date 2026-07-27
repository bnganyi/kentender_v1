# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BWMFConfirmation(Document):
	def validate(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.guards import (
			enforce_doctype_immutability,
		)
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
			DT_RESPONSE_VERSION,
		)
		import frappe
		from frappe import _

		if self.is_new():
			resp = frappe.db.get_value(
				DT_RESPONSE_VERSION,
				{"response_id": self.response_id, "version": self.response_version},
				["response_digest", "workspace"],
				as_dict=True,
			)
			if not resp:
				frappe.throw(_("Missing response version for confirmation."), title="BWMF_REF_MISSING")
			if resp.response_digest != self.response_digest:
				frappe.throw(
					_("Confirmation response digest does not match the response version."),
					title="BWMF_RESPONSE_DIGEST_MISMATCH",
				)
			if resp.workspace != self.workspace:
				frappe.throw(_("Confirmation response is cross-workspace."), title="BWMF_CROSS_WORKSPACE_LINK")

		enforce_doctype_immutability(self)
