# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_configurations.constants import ACTIVE_CONFIGURATION_STATUSES


class TenderConfiguration(Document):
	def validate(self) -> None:
		self._validate_unique_active_package()
		self._validate_f1_publication_lock()

	def _validate_f1_publication_lock(self) -> None:
		"""F1: after Confirm Preview, CFG/STD values are read-only until Return for Correction."""
		if self.is_new() or getattr(self.flags, "ignore_f1_publication_lock", False):
			return
		from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
			CFG_LOCK_FIELDS,
			configuration_is_locked_for_edit,
		)

		if not configuration_is_locked_for_edit(self.name):
			return
		for field in CFG_LOCK_FIELDS:
			db_val = frappe.db.get_value(self.doctype, self.name, field)
			if cstr(self.get(field) or "") != cstr(db_val or ""):
				frappe.throw(
					frappe._(
						"This tender configuration is locked after preview confirmation. "
						"Return for Correction before editing configuration values."
					),
					title="CONFIGURATION_LOCKED",
				)

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
