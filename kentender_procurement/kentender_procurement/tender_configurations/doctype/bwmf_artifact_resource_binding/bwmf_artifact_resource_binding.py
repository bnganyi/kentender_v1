# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.keys import (
	artifact_resource_key,
	assert_server_key,
)


class BWMFArtifactResourceBinding(Document):
	def before_insert(self):
		expected = artifact_resource_key(self.compile_artifact, self.resource_id)
		assert_server_key("artifact_resource_key", self.artifact_resource_key, expected)
		self.artifact_resource_key = expected

	def validate(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.guards import (
			enforce_doctype_immutability,
		)

		enforce_doctype_immutability(self)
		expected = artifact_resource_key(self.compile_artifact, self.resource_id)
		assert_server_key("artifact_resource_key", self.artifact_resource_key, expected)
		self.artifact_resource_key = expected
