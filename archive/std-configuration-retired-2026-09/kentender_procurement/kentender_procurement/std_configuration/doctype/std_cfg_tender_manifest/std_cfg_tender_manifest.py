# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document


class STDCfgTenderManifest(Document):
	def validate(self):
		from kentender_procurement.std_configuration.services.std_domain_guards import (
			validate_std_cfg_tender_manifest,
		)

		validate_std_cfg_tender_manifest(self)
