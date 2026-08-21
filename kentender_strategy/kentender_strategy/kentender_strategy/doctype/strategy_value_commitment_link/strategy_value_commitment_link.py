# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StrategyValueCommitmentLink(Document):
	def validate(self):
		from kentender_strategy.services.strategy_domain_guards import validate_strategy_value_commitment_link
		validate_strategy_value_commitment_link(self)
