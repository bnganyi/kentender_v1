# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StrategicObjective(Document):
	def before_insert(self):
		from kentender_strategy.services.strategy_reference import before_insert_assign_reference
		before_insert_assign_reference(self)

	def validate(self):
		from kentender_strategy.services.strategy_reference import validate_reference_field
		from kentender_strategy.services.strategy_domain_guards import validate_strategic_objective
		validate_reference_field(self)
		validate_strategic_objective(self)
