# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_configurations.constants import ACTIVE_CONFIGURATION_STATUSES


class TenderConfiguration(Document):
	def validate(self) -> None:
		self._validate_unique_active_package()

	def _validate_unique_active_package(self) -> None:
		if not self.procurement_package:
			return
		if (self.status or "").strip() not in ACTIVE_CONFIGURATION_STATUSES:
			return
		filters = {
			"procurement_package": self.procurement_package,
			"status": ("in", list(ACTIVE_CONFIGURATION_STATUSES)),
		}
		existing = frappe.get_all(
			"Tender Configuration",
			filters=filters,
			pluck="name",
			limit=5,
		)
		for name in existing:
			if name != self.name:
				frappe.throw(
					frappe._(
						"This procurement package already has a tender configuration. "
						"Open the existing configuration instead."
					),
					title="TCFG_PACKAGE_ALREADY_CONFIGURED",
				)
