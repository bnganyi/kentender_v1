# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.2 — the stable identity and scope of one requirement.

The root carries no requirement content; title, description, expected
operational result, quantity, unit and required-by all live on
`Departmental Need Version` (§4.3). PE, OU and FY are immutable after creation.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import IMMUTABLE_NEED_SCOPE_FIELDS, NEED_STATES
from kentender_procurement.departmental_needs.errors import fail


class DepartmentalNeed(Document):
	def validate(self):
		if self.current_state not in NEED_STATES:
			fail("NDS_STATE_CONFLICT", "Invalid Departmental Need state.")
		self._require_unit_within_entity()
		self._guard_immutable_scope()

	def _require_unit_within_entity(self):
		owning_entity = frappe.db.get_value(
			"Organisation Unit", self.organisation_unit, "procuring_entity"
		)
		if owning_entity != self.procuring_entity:
			fail(
				"NDS_CONTEXT_REQUIRED",
				"Organisation Unit must belong to the selected Procuring Entity.",
			)

	def _guard_immutable_scope(self):
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		changed = [f for f in IMMUTABLE_NEED_SCOPE_FIELDS if self.get(f) != before.get(f)]
		if changed:
			fail(
				"NDS_STATE_CONFLICT",
				f"Departmental Need scope is immutable. Attempted to change: {', '.join(changed)}.",
			)

	def on_trash(self):
		fail("NDS_STATE_CONFLICT", "Departmental Needs are retained and cannot be deleted.")
