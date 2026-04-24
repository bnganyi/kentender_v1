# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

VALID_STATUSES = frozenset(("Draft", "Submitted", "Approved", "Locked", "Rejected", "Returned"))
# B4: Submitted onward — field lock for non-privileged users (Roles §11). Returned is planner-editable.
READONLY_STATUSES = frozenset(("Submitted", "Approved", "Locked", "Rejected"))
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

ALLOWED_STATUS_TRANSITIONS = {
	"Draft": ("Submitted",),
	"Returned": ("Submitted",),
	"Submitted": ("Approved", "Returned", "Rejected"),
	"Approved": ("Locked",),
	"Locked": ("Draft",),
	"Rejected": (),
}

_TRANSITIONS_REQUIRING_REASON = frozenset(
	(
		("Submitted", "Returned"),
		("Submitted", "Rejected"),
		("Locked", "Draft"),
	)
)

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
		self._enforce_lock_on_approved_states()
		self._sync_approval_metadata()

	def _set_defaults(self):
		if not self.status:
			self.status = "Draft"
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
				_("Status must be one of: Draft, Submitted, Approved, Locked, Rejected, Returned."),
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
			if new_status == "Draft":
				return
			self._raise_if_invalid_transition("Draft", new_status)
			self._validate_transition_roles("Draft", new_status)
			self._validate_transition_reason("Draft", new_status)
			self._validate_submitted_to_approved_preconditions("Draft", new_status)
			# Strict submit (all packages Approved + integrity hash) applies on real
			# Draft/Returned → Submitted saves, not on rare insert-with-status bootstrap rows.
			return

		if not self.has_value_changed("status"):
			return

		before = self.get_doc_before_save()
		old_status = (before.get("status") if before else None) or "Draft"
		if old_status == new_status:
			return

		self._raise_if_invalid_transition(old_status, new_status)
		self._validate_transition_roles(old_status, new_status)
		self._validate_transition_reason(old_status, new_status)
		self._validate_submitted_to_approved_preconditions(old_status, new_status)
		self._validate_transition_to_submitted(old_status, new_status)

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
		if (old_status, new_status) in (("Draft", "Submitted"), ("Returned", "Submitted")):
			if not (roles & _ROLE_PLANNER):
				frappe.throw(
					_("Only a Procurement Planner or Administrator may submit this plan."),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) in (
			("Submitted", "Approved"),
			("Submitted", "Returned"),
			("Submitted", "Rejected"),
		):
			if not (roles & _ROLE_AUTHORITY):
				frappe.throw(
					_("Only Planning Authority or Administrator may perform this transition."),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) == ("Approved", "Locked"):
			if not (roles & _ROLE_AUTHORITY):
				frappe.throw(
					_("Only Planning Authority or Administrator may lock this plan."),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) == ("Locked", "Draft"):
			if not (roles & _ROLE_ADMIN_ONLY):
				frappe.throw(
					_("Only Administrator or System Manager may unlock this plan."),
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

	def _compute_package_integrity_hash(self) -> str:
		rows = frappe.db.sql(
			"""
			select name, status, estimated_value,
				(select count(*) from `tabProcurement Package Line` pl
				 where pl.package_id = p.name and ifnull(pl.is_active,1)=1) as line_count
			from `tabProcurement Package` p
			where plan_id = %s and ifnull(is_active,1)=1
			order by name
			""",
			self.name,
		)
		payload = json.dumps(rows, sort_keys=True, default=str)
		return hashlib.sha256(payload.encode()).hexdigest()

	def _validate_transition_to_submitted(self, old_status, new_status):
		if new_status != "Submitted" or old_status not in ("Draft", "Returned"):
			return
		rows = frappe.get_all(
			"Procurement Package",
			filters={"plan_id": self.name, "is_active": 1},
			fields=["name", "package_code", "status"],
			limit=500,
		)
		if not rows:
			frappe.throw(
				_("At least one active procurement package is required before the plan can be submitted."),
				title=_("Plan not ready"),
			)
		not_approved = [r for r in rows if (r.status or "") != "Approved"]
		if not_approved:
			detail = "; ".join(
				f"{(r.package_code or r.name or '').strip()}: {r.status or _('unknown')}" for r in not_approved
			)
			frappe.throw(
				_("Every active package must be Approved before the plan can be submitted: {0}").format(detail),
				title=_("Packages not approved"),
			)
		self.submit_package_integrity_hash = self._compute_package_integrity_hash()

	def _validate_submitted_to_approved_preconditions(self, old_status, new_status):
		if (old_status, new_status) != ("Submitted", "Approved"):
			return
		n = frappe.db.sql(
			"""select count(*) from `tabProcurement Package`
			where plan_id = %s and ifnull(is_active, 1) = 1""",
			self.name,
		)[0][0]
		if not n:
			frappe.throw(
				_("At least one active procurement package is required before the plan can be approved."),
				title=_("Plan not ready for approval"),
			)
		not_ap = frappe.db.sql(
			"""select name, package_code, status from `tabProcurement Package`
			where plan_id = %s and ifnull(is_active,1)=1 and ifnull(status,'') != 'Approved'""",
			self.name,
		)
		if not_ap:
			detail = "; ".join(f"{(r[1] or r[0]).strip()}: {r[2]}" for r in not_ap)
			frappe.throw(
				_("All active packages must remain Approved before the plan can be approved: {0}").format(detail),
				title=_("Package not approved"),
			)
		before = self.get_doc_before_save()
		expected = (before.get("submit_package_integrity_hash") if before else None) or ""
		if expected and not _is_privileged_plan_actor():
			current = self._compute_package_integrity_hash()
			if current != expected:
				frappe.throw(
					_(
						"Package data changed after plan submission. Re-submit the plan or contact an administrator."
					),
					title=_("Integrity check failed"),
				)
		elif expected and _is_privileged_plan_actor():
			current = self._compute_package_integrity_hash()
			if current != expected:
				frappe.log_error(
					message=f"Plan {self.name}: package integrity drift at approve (admin override by {frappe.session.user}).",
					title="Procurement Plan approve override",
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

	def _enforce_lock_on_approved_states(self):
		if self.is_new():
			return
		if _is_privileged_plan_actor():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		previous_status = before.get("status") or "Draft"
		if previous_status not in READONLY_STATUSES:
			return

		changed = self._changed_business_fieldnames()
		if not changed:
			return

		if changed.issubset(_WORKFLOW_FIELDS_WHEN_READONLY):
			if "status" not in changed and "workflow_reason" in changed:
				frappe.throw(
					_("Submitted, Approved, Locked, and Rejected plans are read-only."),
					title=_("Record locked"),
				)
			return

		frappe.throw(
			_("Submitted, Approved, Locked, and Rejected plans are read-only."),
			title=_("Record locked"),
		)

	def _sync_approval_metadata(self):
		if self.status == "Approved":
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approved_at:
				self.approved_at = now_datetime()
			self.rejected_by = None
			self.rejected_at = None
		elif self.status == "Locked":
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approved_at:
				self.approved_at = now_datetime()
			self.rejected_by = None
			self.rejected_at = None
		elif self.status == "Rejected":
			self.approved_by = None
			self.approved_at = None
			if not self.rejected_by:
				self.rejected_by = frappe.session.user
			if not self.rejected_at:
				self.rejected_at = now_datetime()
		else:
			self.approved_by = None
			self.approved_at = None
			self.rejected_by = None
			self.rejected_at = None
