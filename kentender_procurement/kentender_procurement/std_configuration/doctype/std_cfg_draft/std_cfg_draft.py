# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class STDCfgDraft(Document):
	def validate(self):
		from kentender_procurement.std_configuration.services.std_domain_guards import (
			validate_std_cfg_draft,
		)
		from kentender_procurement.std_configuration.services.std_reference import (
			assert_generated_id_immutable,
			assign_generated_id,
		)

		assign_generated_id(self)
		assert_generated_id_immutable(self, "draft_id")
		validate_std_cfg_draft(self)

	def after_insert(self):
		# Thin local invariant (AGENTS.md §4.2), not orchestration: every new Draft
		# is its package's open Draft, full stop. Clearing this pointer again on
		# activation is genuine multi-document orchestration and lives in
		# services/std_lifecycle.py instead (Phase 3).
		frappe.db.set_value("STD Cfg Package", self.package_id, "current_draft_id", self.name)
