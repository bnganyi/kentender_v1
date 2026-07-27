# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.keys import (
	assert_server_key,
	manifest_resource_binding_key,
)


class BWMFManifestResourceBinding(Document):
	def before_insert(self):
		expected = manifest_resource_binding_key(self.manifest_version, self.resource_id)
		assert_server_key("binding_key", self.binding_key, expected)
		self.binding_key = expected

	def validate(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.guards import (
			enforce_doctype_immutability,
		)

		enforce_doctype_immutability(self)
		expected = manifest_resource_binding_key(self.manifest_version, self.resource_id)
		assert_server_key("binding_key", self.binding_key, expected)
		self.binding_key = expected
