# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class PlanDemandAllocation(Document):
	def before_insert(self) -> None:
		self._sync_active_hold()

	def validate(self) -> None:
		self._sync_active_hold()

	def _sync_active_hold(self) -> None:
		self.active_hold_key = self.demand_item if self.status in ("Draft", "Effective") else None
