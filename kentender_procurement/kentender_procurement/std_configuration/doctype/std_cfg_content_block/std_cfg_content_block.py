# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document


class STDCfgContentBlock(Document):
	def validate(self):
		from kentender_procurement.std_configuration.services.std_domain_guards import (
			validate_owning_reference,
			validate_std_cfg_content_block,
		)
		from kentender_procurement.std_configuration.services.std_reference import (
			assert_generated_id_immutable,
			assign_generated_id,
		)

		assign_generated_id(self)
		assert_generated_id_immutable(self, "content_block_id")
		validate_owning_reference(self)
		validate_std_cfg_content_block(self)
