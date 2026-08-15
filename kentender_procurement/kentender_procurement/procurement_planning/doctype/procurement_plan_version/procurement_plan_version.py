# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.procurement_planning.mvp1_constants import (
	VERSION_APPROVED,
	VERSION_IMMUTABLE_STATUSES,
	VERSION_SUPERSEDED,
)


class ProcurementPlanVersion(Document):
	def before_insert(self) -> None:
		self._sync_open_slot()

	def validate(self) -> None:
		self._sync_open_slot()
		if self.is_new():
			return
		prior = frappe.db.get_value("Procurement Plan Version", self.name, "status")
		if prior not in VERSION_IMMUTABLE_STATUSES:
			return
		# Service supersession uses db.set_value; Doc.save must not mutate immutable versions.
		allowed_supersede = prior == VERSION_APPROVED and self.status == VERSION_SUPERSEDED
		if not allowed_supersede:
			frappe.throw(
				frappe._("Approved, Superseded and Cancelled plan versions are immutable."),
				title="PLN_VERSION_IMMUTABLE",
			)

	def _sync_open_slot(self) -> None:
		self.open_version_slot = self.plan if self.status in ("Draft", "In review", "Returned") else None
