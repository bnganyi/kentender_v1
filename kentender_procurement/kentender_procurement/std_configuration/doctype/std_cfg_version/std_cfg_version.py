# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document


class STDCfgVersion(Document):
	def validate(self):
		from kentender_procurement.std_configuration.services.std_domain_guards import (
			validate_std_cfg_version,
		)
		from kentender_procurement.std_configuration.services.std_reference import (
			assert_generated_id_immutable,
			assign_generated_id,
		)

		assign_generated_id(self)
		assert_generated_id_immutable(self, "version_id")
		validate_std_cfg_version(self)
