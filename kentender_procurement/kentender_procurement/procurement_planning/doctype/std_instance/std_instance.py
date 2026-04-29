from frappe.model.document import Document
from kentender_procurement.std_engine.state_transition_guard import assert_transition_service_controlled


class STDInstance(Document):
	def validate(self):
		assert_transition_service_controlled(self, "instance_status")
		assert_transition_service_controlled(self, "readiness_status")

