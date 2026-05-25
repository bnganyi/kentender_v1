# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from kentender_procurement.procurement_planning.pp2_constants import (
	PLAN_ACTIVE,
	PLAN_ALLOWED_TRANSITIONS,
	PLAN_CANCELLED,
	PLAN_CLOSED,
	PLAN_DRAFT,
	PLAN_READONLY_STATUSES,
	PLAN_SUPERSEDED,
	PLAN_TRANSITIONS_REQUIRING_REASON,
	PLAN_VALID_STATUSES,
)

_SKIP_LOCK_VALUE_CHANGE = frozenset(("total_planned_value", "submit_package_integrity_hash"))
_SKIP_FIELD_TYPES = frozenset(
	(
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
		"Button",
		"Heading",
	)
)
_WORKFLOW_FIELDS_WHEN_READONLY = frozenset(("status", "workflow_reason"))

VALID_STATUSES = PLAN_VALID_STATUSES
READONLY_STATUSES = PLAN_READONLY_STATUSES
ALLOWED_STATUS_TRANSITIONS = PLAN_ALLOWED_TRANSITIONS
_TRANSITIONS_REQUIRING_REASON = PLAN_TRANSITIONS_REQUIRING_REASON

_ROLE_PLANNER = frozenset(("Procurement Planner", "Administrator", "System Manager"))
_ROLE_AUTHORITY = frozenset(("Planning Authority", "Administrator", "System Manager"))
_ROLE_ADMIN_ONLY = frozenset(("Administrator", "System Manager"))


def _session_roles():
	return frozenset(frappe.get_roles(frappe.session.user))


def _is_privileged_plan_actor():
	return bool(_session_roles() & _ROLE_ADMIN_ONLY)


class ProcurementPlan(Document):
	def validate(self):
		self._set_defaults()
		self._sync_total_planned_value_from_packages()
		self._validate_canonical_status()
		self._validate_plan_code_unique()
		self._validate_status_transitions()
		self._enforce_lock_on_readonly_states()
		self._sync_approval_metadata()

	def _set_defaults(self):
		if not self.status:
			self.status = PLAN_DRAFT
		if self.is_active is None:
			self.is_active = 1
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_at:
			self.created_at = now_datetime()

	def _sync_total_planned_value_from_packages(self):
		"""Derived total (A5): sum of active packages' estimated_value."""
		if self.is_new():
			self.total_planned_value = 0.0
			return
		total = frappe.db.sql(
			"""select coalesce(sum(estimated_value), 0) from `tabProcurement Package`
			where plan_id = %s and ifnull(is_active, 1) = 1""",
			self.name,
		)[0][0]
		self.total_planned_value = flt(total)

	def _validate_canonical_status(self):
		if self.status not in VALID_STATUSES:
			frappe.throw(
				_("Status must be one of: Draft, Active, Closed, Cancelled, Superseded."),
				title=_("Invalid status"),
			)

	def _validate_plan_code_unique(self):
		if not self.plan_code:
			return
		filters = {"plan_code": self.plan_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Procurement Plan", filters):
			frappe.throw(_("Plan Code must be unique."), title=_("Duplicate plan code"))

	def _validate_status_transitions(self):
		new_status = self.status
		if not new_status:
			return

		if self.is_new():
			if new_status == PLAN_DRAFT:
				return
			self._raise_if_invalid_transition(PLAN_DRAFT, new_status)
			self._validate_transition_roles(PLAN_DRAFT, new_status)
			self._validate_transition_reason(PLAN_DRAFT, new_status)
			return

		if not self.has_value_changed("status"):
			return

		before = self.get_doc_before_save()
		old_status = (before.get("status") if before else None) or PLAN_DRAFT
		if old_status == new_status:
			return

		self._raise_if_invalid_transition(old_status, new_status)
		self._validate_transition_roles(old_status, new_status)
		self._validate_transition_reason(old_status, new_status)
		self._validate_activate_preconditions(old_status, new_status)

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

	def _validate_transition_roles(self, old_status, new_status):
		roles = _session_roles()
		if (old_status, new_status) == (PLAN_DRAFT, PLAN_ACTIVE):
			if not (roles & _ROLE_AUTHORITY):
				frappe.throw(
					_("Only Planning Authority or Administrator may activate this plan."),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) in (
			(PLAN_ACTIVE, PLAN_CLOSED),
			(PLAN_ACTIVE, PLAN_CANCELLED),
			(PLAN_DRAFT, PLAN_CANCELLED),
			(PLAN_ACTIVE, PLAN_SUPERSEDED),
		):
			if not (roles & _ROLE_AUTHORITY):
				frappe.throw(
					_("Only Planning Authority or Administrator may perform this transition."),
					title=_("Not permitted"),
				)

	def _validate_transition_reason(self, old_status, new_status):
		if (old_status, new_status) not in _TRANSITIONS_REQUIRING_REASON:
			return
		if not (self.workflow_reason or "").strip():
			frappe.throw(
				_("A workflow reason is required for this transition."),
				title=_("Missing workflow reason"),
			)

	def _validate_activate_preconditions(self, old_status, new_status):
		if (old_status, new_status) != (PLAN_DRAFT, PLAN_ACTIVE):
			return
		n = frappe.db.sql(
			"""select count(*) from `tabProcurement Package`
			where plan_id = %s and ifnull(is_active, 1) = 1""",
			self.name,
		)[0][0]
		if not n and not _is_privileged_plan_actor():
			frappe.throw(
				_("At least one active procurement package is recommended before activating the plan."),
				title=_("Plan not ready"),
			)

	def _changed_business_fieldnames(self):
		changed = set()
		for df in self.meta.fields:
			fieldname = df.fieldname
			if not fieldname or df.fieldtype in _SKIP_FIELD_TYPES:
				continue
			if fieldname in _SKIP_LOCK_VALUE_CHANGE:
				continue
			if self.has_value_changed(fieldname):
				changed.add(fieldname)
		return changed

	def _enforce_lock_on_readonly_states(self):
		if self.is_new():
			return
		if _is_privileged_plan_actor():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		previous_status = before.get("status") or PLAN_DRAFT
		if previous_status not in READONLY_STATUSES:
			return

		changed = self._changed_business_fieldnames()
		if not changed:
			return

		if changed.issubset(_WORKFLOW_FIELDS_WHEN_READONLY):
			if "status" not in changed and "workflow_reason" in changed:
				frappe.throw(
					_("Closed, Cancelled, and Superseded plans are read-only."),
					title=_("Record locked"),
				)
			return

		frappe.throw(
			_("Closed, Cancelled, and Superseded plans are read-only."),
			title=_("Record locked"),
		)

	def _sync_approval_metadata(self):
		if self.status == PLAN_ACTIVE:
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approved_at:
				self.approved_at = now_datetime()
			self.rejected_by = None
			self.rejected_at = None
		elif self.status == PLAN_CANCELLED:
			self.approved_by = None
			self.approved_at = None
			if not self.rejected_by:
				self.rejected_by = frappe.session.user
			if not self.rejected_at:
				self.rejected_at = now_datetime()
		else:
			if self.status not in (PLAN_CLOSED, PLAN_SUPERSEDED):
				self.approved_by = None
				self.approved_at = None
			self.rejected_by = None
			self.rejected_at = None
