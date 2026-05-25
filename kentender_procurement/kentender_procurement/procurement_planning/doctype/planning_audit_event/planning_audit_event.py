# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning Audit Event — append-only governance record (PP2 domain §7 / §15)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.immutability_guards import raise_append_only_on_update


class PlanningAuditEvent(Document):
	def validate(self) -> None:
		if not self._may_bypass_append_only():
			raise_append_only_on_update(
				self,
				message=_("Planning audit events are append-only and cannot be modified."),
				title=_("Append-Only Audit Event"),
				ignore_flag="ignore_pp_aud_append_only_override",
			)

	def on_trash(self) -> None:
		if self._may_bypass_append_only():
			return
		if getattr(self.flags, "ignore_pp_aud_allow_delete", False):
			return
		frappe.throw(
			_("Planning audit events cannot be deleted."),
			title=_("Append-Only Audit Event"),
		)

	def _may_bypass_append_only(self) -> bool:
		if getattr(self.flags, "ignore_pp_aud_append_only_override", False):
			return True
		if frappe.session.user == "Administrator":
			return True
		return "System Manager" in set(frappe.get_roles())
