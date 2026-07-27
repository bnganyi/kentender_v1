# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.keys import (
	assert_server_key,
	resource_version_key,
)


class BWMFManifestResource(Document):
	def before_insert(self):
		expected = resource_version_key(
			self.resource_id,
			self.resource_digest,
			self.schema_ref,
			self.schema_version,
		)
		assert_server_key("resource_version_key", self.resource_version_key, expected)
		self.resource_version_key = expected

	def validate(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.guards import (
			enforce_doctype_immutability,
		)

		enforce_doctype_immutability(self)
		expected = resource_version_key(
			self.resource_id,
			self.resource_digest,
			self.schema_ref,
			self.schema_version,
		)
		assert_server_key("resource_version_key", self.resource_version_key, expected)
		self.resource_version_key = expected
