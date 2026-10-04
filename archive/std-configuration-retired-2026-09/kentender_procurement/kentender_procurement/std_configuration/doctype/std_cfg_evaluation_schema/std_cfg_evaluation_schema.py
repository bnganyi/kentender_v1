# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document


class STDCfgEvaluationSchema(Document):
	def validate(self):
		from kentender_procurement.std_configuration.services.std_domain_guards import (
			validate_owning_reference,
			validate_std_cfg_evaluation_schema,
			validate_unique_key_within_reference,
		)

		validate_owning_reference(self)
		validate_unique_key_within_reference(self, "criterion_key")
		validate_std_cfg_evaluation_schema(self)
