# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PerformanceIndicator(Document):
	def validate(self):
		from kentender_strategy.services.strategy_domain_guards import validate_performance_indicator
		validate_performance_indicator(self)
