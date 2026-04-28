from frappe.model.document import Document
from kentender_procurement.std_engine.state_transition_guard import assert_transition_service_controlled


class STDAddendumImpactAnalysis(Document):
	def validate(self):
		assert_transition_service_controlled(self, "status")

