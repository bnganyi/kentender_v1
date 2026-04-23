# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class BudgetReservation(Document):
	def before_validate(self):
		if self.budget_line:
			self._derive_from_budget_line()
		if self.is_new():
			if not self.created_at:
				self.created_at = now_datetime()
			if not self.created_by:
				self.created_by = frappe.session.user
			if not self.reservation_id:
				self.reservation_id = self._next_reservation_id()

	def validate(self):
		self._validate_amount_br001()
		self._validate_required_br002_to_004()
		self._validate_available_br005()
		self._validate_single_active_br006()
		self._validate_release_audit_br007()

	def _derive_from_budget_line(self):
		values = frappe.db.get_value(
			"Budget Line",
			self.budget_line,
			("budget", "procuring_entity", "fiscal_year", "currency"),
		)
		if not values:
			return
		self.budget, self.procuring_entity, self.fiscal_year, self.currency = values

	def _next_reservation_id(self) -> str:
		entity = (self.procuring_entity or "UNK").strip().upper()
		year = str(self.fiscal_year or now_datetime().year)
		prefix = f"RSV-{entity}-{year}-"
		latest = frappe.get_all(
			"Budget Reservation",
			filters={"reservation_id": ["like", f"{prefix}%"]},
			fields=["reservation_id"],
			order_by="creation desc",
			limit=1,
		)
		seq = 1
		if latest:
			tail = (latest[0].reservation_id or "").rsplit("-", 1)[-1]
			if tail.isdigit():
				seq = int(tail) + 1
		return f"{prefix}{str(seq).zfill(4)}"

	def _validate_amount_br001(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Reservation amount must be greater than zero (BR-001)."), title=_("Budget Reservation"))

	def _validate_required_br002_to_004(self):
		if not self.budget_line:
			frappe.throw(_("Budget Line is required (BR-002)."), title=_("Budget Reservation"))
		if not self.budget:
			frappe.throw(_("Budget is required (BR-002)."), title=_("Budget Reservation"))
		if not self.procuring_entity:
			frappe.throw(_("Procuring Entity is required (BR-003)."), title=_("Budget Reservation"))
		if not self.fiscal_year:
			frappe.throw(_("Fiscal Year is required."), title=_("Budget Reservation"))
		if not self.currency:
			frappe.throw(_("Currency is required (BR-007)."), title=_("Budget Reservation"))
		if not (self.source_doctype or "").strip():
			frappe.throw(_("Source DocType is required (BR-003)."), title=_("Budget Reservation"))
		if not (self.source_docname or "").strip():
			frappe.throw(_("Source document is required (BR-004)."), title=_("Budget Reservation"))

	def _validate_available_br005(self):
		if self.status != "Active":
			return
		bl = frappe.get_doc("Budget Line", self.budget_line)
		avail = flt(bl.amount_allocated) - flt(bl.amount_reserved) - flt(bl.amount_consumed or 0)
		if self.available_before_reservation in (None, ""):
			self.available_before_reservation = avail
		if self.available_after_reservation in (None, ""):
			self.available_after_reservation = flt(avail - flt(self.amount))
		if flt(self.amount) > avail + 1e-9:
			frappe.throw(
				_("Insufficient available budget for this reservation (BR-005)."),
				title=_("Budget Reservation"),
			)

	def _validate_single_active_br006(self):
		if self.status != "Active":
			return
		filters = {
			"source_doctype": self.source_doctype,
			"source_docname": self.source_docname,
			"status": "Active",
		}
		existing = frappe.get_all("Budget Reservation", filters=filters, pluck="name")
		for name in existing:
			if name != self.name:
				frappe.throw(
					_("An active reservation already exists for this source document (BR-006)."),
					title=_("Budget Reservation"),
				)

	def _validate_release_audit_br007(self):
		if self.status == "Released":
			if not self.released_at or not self.released_by or not (self.release_reason or "").strip():
				frappe.throw(
					_("Released reservations must capture release metadata (BR-007)."),
					title=_("Budget Reservation"),
				)
		if not self.is_new():
			prev = self.get_doc_before_save()
			if prev and prev.get("status") == "Released" and self.status != "Released":
				frappe.throw(_("Cannot reopen a released reservation (BR-007)."), title=_("Budget Reservation"))
