# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""
Demand (DIA header). Business identifier format: DIA-{ProcuringEntityName}-{YYYY}-{seq:04d}
(e.g. DIA-MOH-2026-0001). Generated once procuring_entity and request_date are set.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

# A4 — canonical Select values (must match PRD §13.3 and demand.json options exactly).
PRIORITY_LEVELS = frozenset(("Low", "Normal", "High", "Critical"))
DEMAND_TYPES = frozenset(("Planned", "Unplanned", "Emergency"))
REQUISITION_TYPES = frozenset(("Goods", "Works", "Services"))
STATUSES = frozenset(
	(
		"Draft",
		"Pending HoD Approval",
		"Pending Finance Approval",
		"Approved",
		"Planning Ready",
		"Rejected",
		"Cancelled",
	)
)
PLANNING_STATUSES = frozenset(("Not Planned", "Partially Planned", "Fully Planned", "Planning Ready"))
RESERVATION_STATUSES = frozenset(("None", "Pending Check", "Reserved", "Released", "Failed"))

# B1 — allowed workflow transitions (PRD §8, Cursor Pack B1). Terminal states: Planning Ready, Cancelled.
ALLOWED_STATUS_TRANSITIONS = {
	"Draft": frozenset(("Pending HoD Approval", "Cancelled")),
	"Pending HoD Approval": frozenset(
		("Pending Finance Approval", "Draft", "Rejected", "Cancelled")
	),
	"Pending Finance Approval": frozenset(("Approved", "Draft", "Rejected", "Cancelled")),
	"Approved": frozenset(("Planning Ready", "Cancelled")),
	"Planning Ready": frozenset(),
	"Rejected": frozenset(("Pending HoD Approval",)),
	"Cancelled": frozenset(),
}

# B3 — only these workflow states allow editing header and line items (Cursor Pack B3; Pending HoD fully locked in v1).
STATUSES_FULLY_EDITABLE = frozenset(("Draft", "Rejected"))

_SKIP_FIELD_TYPES = frozenset(
	(
		"Section Break",
		"Column Break",
		"Tab Break",
		"Table",
		"HTML",
		"Button",
		"Heading",
	)
)


class Demand(Document):
	def validate(self):
		self._set_audit_defaults()
		self._sync_is_exception_from_demand_type()
		if self.budget_line:
			self._apply_budget_line_strategy()

		if self.procuring_entity and self.request_date and not self.demand_id:
			self._set_demand_id()
		self._enforce_edit_lock()
		self._recalculate_totals()
		self._validate_canonical_selects()
		self._validate_status_transitions()
		self._validate_rejection_and_closure_metadata()

	def _set_audit_defaults(self):
		if not self.request_date:
			self.request_date = today()
		if not self.requested_by:
			self.requested_by = frappe.session.user
		if not self.created_by:
			self.created_by = frappe.session.user

	def _sync_is_exception_from_demand_type(self):
		if self.demand_type in ("Unplanned", "Emergency"):
			self.is_exception = 1
		else:
			self.is_exception = 0

	def _apply_budget_line_strategy(self):
		"""C1 — derive budget/strategy fields from Budget Line via Budget services only."""
		from kentender_budget.api.dia_budget_control import get_budget_line_context

		ctx = get_budget_line_context(self.budget_line)
		if not ctx.get("ok"):
			frappe.throw(_(ctx.get("message") or _("Invalid budget line.")), title=_("Budget Line"))
		data = ctx.get("data") or {}
		if self.procuring_entity and data.get("procuring_entity") != self.procuring_entity:
			frappe.throw(
				_("Selected budget line belongs to a different procuring entity."),
				title=_("Budget Line"),
			)
		self.budget = data.get("budget")
		self.funding_source = data.get("funding_source")
		self.strategic_plan = data.get("strategic_plan")
		self.program = data.get("program")
		self.sub_program = data.get("sub_program")
		self.output_indicator = data.get("output_indicator")
		self.performance_target = data.get("performance_target")

	def validate_submission_gate(self):
		"""C2–C3 — submit-time validation (Cursor Pack / PRD)."""
		from kentender_budget.api.dia_budget_control import get_budget_line_context

		if not (self.title or "").strip():
			frappe.throw(_("Title is required."), title=_("Cannot submit"))
		if not self.procuring_entity:
			frappe.throw(_("Procuring Entity is required."), title=_("Cannot submit"))
		if not self.requesting_department:
			frappe.throw(_("Department is required."), title=_("Cannot submit"))
		if not self.requested_by:
			frappe.throw(_("Requester is required."), title=_("Cannot submit"))
		if not self.request_date or not self.required_by_date:
			frappe.throw(_("Request Date and Required By Date are required."), title=_("Cannot submit"))
		if not self.budget_line:
			frappe.throw(_("Budget Line is required."), title=_("Cannot submit"))
		ctx = get_budget_line_context(self.budget_line)
		if not ctx.get("ok"):
			frappe.throw(_(ctx.get("message") or _("Budget Line is not valid.")), title=_("Cannot submit"))
		data = ctx.get("data") or {}
		if data.get("procuring_entity") != self.procuring_entity:
			frappe.throw(
				_("Budget line must belong to the same procuring entity as this demand."),
				title=_("Cannot submit"),
			)
		if not self.get("items") or len(self.items) < 1:
			frappe.throw(_("At least one line item is required."), title=_("Cannot submit"))
		if flt(self.total_amount) <= 0:
			frappe.throw(_("Requested amount must be greater than zero."), title=_("Cannot submit"))
		rd = getdate(self.required_by_date)
		rq = getdate(self.request_date)
		if self.demand_type != "Emergency" and rd < rq:
			frappe.throw(
				_("Required By Date must be on or after Request Date."),
				title=_("Cannot submit"),
			)
		if self.demand_type == "Unplanned":
			if not (self.beneficiary_summary or "").strip():
				frappe.throw(
					_("Justification (Beneficiary Summary) is required for Unplanned demands."),
					title=_("Cannot submit"),
				)
			if not (self.impact_if_not_procured or "").strip():
				frappe.throw(
					_("Impact if Not Procured is required for Unplanned demands."),
					title=_("Cannot submit"),
				)
		if self.demand_type == "Emergency":
			if not (self.beneficiary_summary or "").strip():
				frappe.throw(
					_("Justification (Beneficiary Summary) is required for Emergency demands."),
					title=_("Cannot submit"),
				)
			if not (self.impact_if_not_procured or "").strip():
				frappe.throw(
					_("Impact if Not Procured is required for Emergency demands."),
					title=_("Cannot submit"),
				)
			if not (self.emergency_justification or "").strip():
				frappe.throw(
					_("Emergency Justification is required for Emergency demands."),
					title=_("Cannot submit"),
				)

	def _set_demand_id(self):
		"""Assign deterministic demand_id: DIA-{entity}-{year}-{sequence}."""
		entity = (self.procuring_entity or "").strip()
		if not entity:
			return
		rd = self.request_date or today()
		year = getdate(rd).year
		prefix = f"DIA-{entity}-{year}-"
		rows = frappe.db.sql(
			"""SELECT demand_id FROM `tabDemand` WHERE demand_id LIKE %s""",
			(prefix + "%",),
		)
		max_seq = 0
		suffix_len = 4
		for (did,) in rows:
			if not did or not str(did).startswith(prefix):
				continue
			tail = str(did).rsplit("-", 1)[-1]
			try:
				max_seq = max(max_seq, int(tail))
			except ValueError:
				continue
		next_seq = max_seq + 1
		for _ in range(100):
			candidate = prefix + str(next_seq).zfill(suffix_len)
			if not frappe.db.exists("Demand", {"demand_id": candidate}):
				self.demand_id = candidate
				return
			next_seq += 1
		frappe.throw(_("Could not allocate unique Demand ID."))

	def _enforce_edit_lock(self):
		"""B3 — block edits when document was not Draft/Rejected (except B2 lifecycle saves)."""
		if getattr(frappe.flags, "demand_lifecycle_action", None):
			return
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		prev_status = before.get("status")
		if not prev_status:
			prev_status = "Draft"
		if prev_status in STATUSES_FULLY_EDITABLE:
			return
		for df in self.meta.fields:
			if df.fieldtype in _SKIP_FIELD_TYPES or df.fieldname == "items":
				continue
			if df.fieldname == "total_amount":
				continue
			if self.has_value_changed(df.fieldname):
				frappe.throw(
					_("This demand cannot be edited in its current workflow state."),
					title=_("Record locked"),
				)
		if self._items_content_changed(before):
			frappe.throw(
				_("Line items cannot be edited in the current workflow state."),
				title=_("Record locked"),
			)

	def _items_content_changed(self, before_doc):
		return self._items_signature(self) != self._items_signature(before_doc)

	def _items_signature(self, doc):
		tuples = []
		for row in doc.get("items") or []:
			tuples.append(
				(
					(getattr(row, "item_description", None) or "").strip(),
					(getattr(row, "category", None) or "").strip(),
					(getattr(row, "uom", None) or "").strip(),
					flt(getattr(row, "quantity", None)),
					flt(getattr(row, "estimated_unit_cost", None)),
					(getattr(row, "notes", None) or "").strip(),
				)
			)
		return tuple(tuples)

	def _recalculate_totals(self):
		"""A3 — total_amount = sum of line totals; recompute each line from qty × unit cost."""
		total = 0.0
		for row in self.get("items") or []:
			qty = flt(getattr(row, "quantity", None))
			unit = flt(getattr(row, "estimated_unit_cost", None))
			line_total = flt(qty * unit)
			row.line_total = line_total
			total += line_total
		self.total_amount = flt(total)

	def _validate_canonical_selects(self):
		"""A4 — reject values not in PRD/DocType option lists (API/import bypass)."""
		checks = (
			(self.priority_level, PRIORITY_LEVELS, _("Priority")),
			(self.demand_type, DEMAND_TYPES, _("Demand Type")),
			(self.requisition_type, REQUISITION_TYPES, _("Demand Category")),
			(self.status, STATUSES, _("Workflow State")),
			(self.planning_status, PLANNING_STATUSES, _("Planning Status")),
			(self.reservation_status, RESERVATION_STATUSES, _("Reservation Status")),
		)
		for value, allowed, label in checks:
			if value not in allowed:
				frappe.throw(
					_("{0} must be one of the allowed values.").format(label),
					title=_("Invalid value"),
				)

	def _validate_status_transitions(self):
		"""B1 — reject disallowed status changes (API/import bypass of lifecycle actions)."""
		new_status = self.status
		if not new_status:
			return

		if self.is_new():
			if new_status == "Draft":
				return
			self._raise_if_invalid_transition("Draft", new_status)
			return

		if not self.has_value_changed("status"):
			return

		before = self.get_doc_before_save()
		old_status = before.get("status") if before else None
		if not old_status:
			old_status = "Draft"
		if old_status == new_status:
			return
		self._raise_if_invalid_transition(old_status, new_status)

	def _raise_if_invalid_transition(self, old_status, new_status):
		allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status)
		if allowed is None:
			frappe.throw(
				_("Unknown prior workflow state: {0}").format(old_status),
				title=_("Invalid status transition"),
			)
		if new_status not in allowed:
			frappe.throw(
				_("Transition from {0} to {1} is not allowed.").format(old_status, new_status),
				title=_("Invalid status transition"),
			)

	def _validate_rejection_and_closure_metadata(self):
		"""B4 — reject/cancel outcomes must carry reason and actor/time (Cursor Pack B4)."""
		if self.status == "Rejected":
			if not (self.rejection_reason or "").strip():
				frappe.throw(_("Rejection reason is required."), title=_("Missing metadata"))
			if not self.rejected_by or not self.rejected_at:
				frappe.throw(_("Rejection metadata is incomplete."), title=_("Missing metadata"))
		if self.status == "Cancelled":
			if not (self.cancellation_reason or "").strip():
				frappe.throw(_("Cancellation reason is required."), title=_("Missing metadata"))
			if not self.cancelled_by or not self.cancelled_at:
				frappe.throw(_("Cancellation metadata is incomplete."), title=_("Missing metadata"))
