# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class StrategicPlan(CommandWriteGuardMixin, Document):
	# AUD-XC-005 — the record changes only through the Strategy commands
	# (services/strategy_writes.py, strategy_transitions.py); no user edit, create or delete.
	command_write_family = "Strategy"

	def before_insert(self):
		from kentender_strategy.services.strategy_reference import before_insert_assign_reference
		before_insert_assign_reference(self)

	def validate(self):
		super().validate()
		from kentender_strategy.services.strategy_reference import validate_reference_field
		from kentender_strategy.services.strategy_domain_guards import validate_strategic_plan
		validate_reference_field(self)
		validate_strategic_plan(self)
