# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.model.document import Document
from frappe.utils import flt, now_datetime
from frappe.utils.data import parse_json

# Governance v1 — package lifecycle (spec-aligned labels).
ST_DRAFT = "Draft"
ST_COMPLETED = "Completed"
ST_SUBMITTED = "Submitted"
ST_APPROVED = "Approved"
ST_READY_FOR_TENDER = "Ready for Tender"
ST_RELEASED_TO_TENDER = "Released to Tender"
ST_RETURNED = "Returned"
ST_REJECTED = "Rejected"

VALID_STATUSES = frozenset(
	(
		ST_DRAFT,
		ST_COMPLETED,
		ST_SUBMITTED,
		ST_APPROVED,
		ST_READY_FOR_TENDER,
		ST_RELEASED_TO_TENDER,
		ST_RETURNED,
		ST_REJECTED,
	)
)
# B4: Submitted onward — field lock for non-privileged users (Roles §11).
READONLY_STATUSES = frozenset(
	(ST_SUBMITTED, ST_APPROVED, ST_READY_FOR_TENDER, ST_RELEASED_TO_TENDER, ST_REJECTED)
)
VALID_METHODS = frozenset(("Open Tender", "RFQ", "Direct"))
VALID_CONTRACT_TYPES = frozenset(("Fixed Price", "Cost Reimbursable", "T&M"))
COMPETITIVE_METHODS = frozenset(("Open Tender", "RFQ"))

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
_SKIP_LOCK_VALUE_CHANGE = frozenset(("estimated_value",))
_WORKFLOW_FIELDS_WHEN_READONLY = frozenset(("status", "workflow_reason"))
_NOTES_FIELDS_IN_READONLY = frozenset(("planner_notes", "exception_notes"))
_ALLOWED_CHANGES_WHEN_READONLY = _WORKFLOW_FIELDS_WHEN_READONLY | _NOTES_FIELDS_IN_READONLY

ALLOWED_STATUS_TRANSITIONS = {
	ST_DRAFT: (ST_COMPLETED,),
	ST_COMPLETED: (ST_SUBMITTED,),
	ST_SUBMITTED: (ST_APPROVED, ST_RETURNED, ST_REJECTED),
	ST_RETURNED: (ST_COMPLETED,),
	ST_APPROVED: (ST_READY_FOR_TENDER,),
	ST_READY_FOR_TENDER: (ST_RELEASED_TO_TENDER, ST_DRAFT),
	ST_RELEASED_TO_TENDER: (),
	ST_REJECTED: (),
}

_TRANSITIONS_REQUIRING_REASON = frozenset(
	(
		(ST_SUBMITTED, ST_RETURNED),
		(ST_SUBMITTED, ST_REJECTED),
		(ST_READY_FOR_TENDER, ST_DRAFT),
	)
)

_ROLE_PLANNER = frozenset(("Procurement Planner", "Administrator", "System Manager"))
_ROLE_AUTHORITY = frozenset(("Planning Authority", "Administrator", "System Manager"))
_ROLE_OFFICER_OR_AUTHORITY = frozenset(
	("Procurement Officer", "Planning Authority", "Administrator", "System Manager")
)
_ROLE_ADMIN_ONLY = frozenset(("Administrator", "System Manager"))

_EDITABLE_METHOD_STATUSES = frozenset((ST_DRAFT, ST_COMPLETED, ST_RETURNED))


def _session_roles():
	return frozenset(frappe.get_roles(frappe.session.user))


def _is_privileged_package_actor():
	return bool(_session_roles() & _ROLE_ADMIN_ONLY)


def recompute_package_estimated_value(package_id, exclude_line_name=None):
	"""Sum active line amounts into Procurement Package.estimated_value; refresh plan total."""
	if not package_id:
		return
	clauses = ["package_id = %s", "ifnull(is_active, 1) = 1"]
	params = [package_id]
	if exclude_line_name:
		clauses.append("name != %s")
		params.append(exclude_line_name)
	where_sql = " and ".join(clauses)
	total = frappe.db.sql(
		f"select coalesce(sum(amount), 0) from `tabProcurement Package Line` where {where_sql}",
		tuple(params),
	)[0][0]
	frappe.db.set_value(
		"Procurement Package", package_id, "estimated_value", flt(total), update_modified=False
	)
	plan_id = frappe.db.get_value("Procurement Package", package_id, "plan_id")
	if plan_id:
		recompute_plan_total_planned_value(plan_id)


def recompute_plan_total_planned_value(plan_id, exclude_package_name=None):
	"""Sum active package estimated_value into Procurement Plan.total_planned_value."""
	if not plan_id:
		return
	clauses = ["plan_id = %s", "ifnull(is_active, 1) = 1"]
	params = [plan_id]
	if exclude_package_name:
		clauses.append("name != %s")
		params.append(exclude_package_name)
	where_sql = " and ".join(clauses)
	total = frappe.db.sql(
		f"select coalesce(sum(estimated_value), 0) from `tabProcurement Package` where {where_sql}",
		tuple(params),
	)[0][0]
	frappe.db.set_value(
		"Procurement Plan", plan_id, "total_planned_value", flt(total), update_modified=False
	)


class ProcurementPackage(Document):
	def autoname(self):
		"""Use package code as document name to avoid hash-style identifiers in UI."""
		if not self.package_code:
			self.package_code = self._generate_unique_package_code()
		if self.package_code:
			self.name = self.package_code

	def validate(self):
		self._set_defaults()
		self._validate_parent_plan_draft_for_bootstrap()
		self._ensure_package_code()
		self._apply_template_derived_defaults_c3()
		self._sync_estimated_value_from_lines()
		self._validate_estimated_value()
		self._validate_canonical_selects()
		self._validate_required_links()
		self._validate_package_code_unique()
		self._validate_method_override()
		self._validate_allowed_methods_from_template_when_overridden()
		self._validate_procurement_method_editable_states_c3()
		self._validate_competitive_decision_profile()
		self._validate_status_transitions()
		self._enforce_lock_on_terminal_states()
		self._sync_approval_metadata()

	def after_insert(self):
		if self.plan_id:
			recompute_plan_total_planned_value(self.plan_id)

	def on_update(self):
		if self.plan_id:
			recompute_plan_total_planned_value(self.plan_id)

	def on_trash(self):
		if self.plan_id:
			recompute_plan_total_planned_value(self.plan_id, exclude_package_name=self.name)

	def _set_defaults(self):
		if not self.status:
			self.status = ST_DRAFT
		if self.method_override_flag is None:
			self.method_override_flag = 0
		if self.is_emergency is None:
			self.is_emergency = 0
		if self.is_active is None:
			self.is_active = 1
		if not self.created_by:
			self.created_by = frappe.session.user
		if self.estimated_value is None:
			self.estimated_value = 0.0

	def _ensure_package_code(self):
		"""Generate package_code server-side; do not require manual user input (UX/data-integrity)."""
		before = self.get_doc_before_save() if not self.is_new() else None
		if before and self.has_value_changed("package_code") and not _is_privileged_package_actor():
			frappe.throw(_("Package Code is system-generated and cannot be edited."), title=_("Code locked"))

		manual_code = (self.package_code or "").strip()
		if self.is_new():
			# Ignore user-supplied code for normal users (v1 no planner override).
			if manual_code and not _is_privileged_package_actor():
				self.package_code = None
			if not self.package_code:
				self.package_code = self._generate_unique_package_code()
			# autoname may have run with a discarded manual code; keep `name` aligned with field:package_code.
			if self.package_code:
				self.name = self.package_code
		elif not self.package_code:
			self.package_code = (before.get("package_code") if before else None) or self._generate_unique_package_code()

	def _generate_unique_package_code(self):
		"""Generate a unique package code, retrying series collisions defensively."""
		for _ in range(8):
			code = self._generate_package_code()
			if not code:
				return None
			filters = {"package_code": code}
			if not self.is_new():
				filters["name"] = ("!=", self.name)
			if not frappe.db.exists("Procurement Package", filters):
				return code
		frappe.throw(
			_("Could not generate a unique Package Code. Please retry save."),
			title=_("Package code collision"),
		)

	def _generate_package_code(self):
		if not self.plan_id:
			return None
		plan = frappe.db.get_value(
			"Procurement Plan",
			self.plan_id,
			("plan_code", "fiscal_year", "procuring_entity"),
			as_dict=True,
		)
		if not plan:
			return None
		entity_code = self._derive_entity_code(plan)
		fy = str(plan.get("fiscal_year") or "").strip()
		if not entity_code or not fy:
			return None
		return make_autoname(f"PKG-{entity_code}-{fy}-.###")

	def _derive_entity_code(self, plan_row):
		plan_code = str(plan_row.get("plan_code") or "").strip().upper()
		if plan_code.startswith("PP-"):
			parts = [p for p in plan_code.split("-") if p]
			# Expected PP-ENTITY-YYYY -> ENTITY
			if len(parts) >= 3 and parts[0] == "PP":
				return parts[1]
		ent = str(plan_row.get("procuring_entity") or "").upper()
		ent = "".join(ch for ch in ent if ch.isalnum())
		return (ent[:6] or "GEN")

	def _sync_estimated_value_from_lines(self):
		"""Derived total (A5): sum of active package line amounts; not user-editable."""
		if self.is_new():
			self.estimated_value = 0.0
			return
		total = frappe.db.sql(
			"""select coalesce(sum(amount), 0) from `tabProcurement Package Line`
			where package_id = %s and ifnull(is_active, 1) = 1""",
			self.name,
		)[0][0]
		self.estimated_value = flt(total)

	def _validate_estimated_value(self):
		self.estimated_value = flt(self.estimated_value)
		if flt(self.estimated_value) < 0:
			frappe.throw(_("Estimated Value cannot be negative."), title=_("Invalid value"))

	def _validate_canonical_selects(self):
		if self.status not in VALID_STATUSES:
			frappe.throw(
				_(
					"Status must be one of: Draft, Completed, Submitted, Approved, "
					"Ready for Tender, Released to Tender, Returned, Rejected."
				),
				title=_("Invalid status"),
			)
		if self.procurement_method not in VALID_METHODS:
			frappe.throw(
				_("Procurement Method must be one of: Open Tender, RFQ, Direct."),
				title=_("Invalid procurement method"),
			)
		if self.contract_type not in VALID_CONTRACT_TYPES:
			frappe.throw(
				_("Contract Type must be one of: Fixed Price, Cost Reimbursable, T&M."),
				title=_("Invalid contract type"),
			)

	def _validate_parent_plan_draft_for_bootstrap(self):
		"""H3 — New packages / plan_id moves under Draft or Returned plan (governance v1)."""
		if not self.plan_id or not frappe.db.exists("Procurement Plan", self.plan_id):
			return
		if _is_privileged_package_actor():
			return
		bootstrap = bool(self.is_new())
		if not bootstrap:
			before = self.get_doc_before_save()
			if before and self.has_value_changed("plan_id"):
				bootstrap = True
		if not bootstrap:
			return
		plan_status = frappe.db.get_value("Procurement Plan", self.plan_id, "status")
		if plan_status not in (ST_DRAFT, "Returned"):
			frappe.throw(
				_(
					"New procurement packages can only be created or assigned under a Procurement Plan "
					"in Draft or Returned status (current plan status: {0})."
				).format(plan_status or _("unknown")),
				title=_("Invalid plan state"),
			)

	def _validate_required_links(self):
		if not self.plan_id:
			frappe.throw(_("Procurement Plan is required."), title=_("Missing plan"))
		if not frappe.db.exists("Procurement Plan", self.plan_id):
			frappe.throw(_("Invalid Procurement Plan."), title=_("Invalid plan"))
		if not self.template_id:
			frappe.throw(_("Procurement Template is required."), title=_("Missing template"))
		if not frappe.db.exists("Procurement Template", self.template_id):
			frappe.throw(_("Invalid Procurement Template."), title=_("Invalid template"))
		for field, label, doctype in (
			("risk_profile_id", _("Risk Profile"), "Risk Profile"),
			("kpi_profile_id", _("KPI Profile"), "KPI Profile"),
			("vendor_management_profile_id", _("Vendor Management Profile"), "Vendor Management Profile"),
		):
			if not self.get(field):
				frappe.throw(_("{0} is required.").format(label), title=_("Missing profile"))
			if not frappe.db.exists(doctype, self.get(field)):
				frappe.throw(_("{0} is not valid.").format(label), title=_("Invalid profile"))
		if self.decision_criteria_profile_id and not frappe.db.exists(
			"Decision Criteria Profile", self.decision_criteria_profile_id
		):
			frappe.throw(_("Invalid Decision Criteria Profile."), title=_("Invalid profile"))

	def _validate_package_code_unique(self):
		if not self.package_code:
			frappe.throw(
				_("Package Code could not be generated. Check Procurement Plan code/fiscal year setup."),
				title=_("Missing package code"),
			)
		filters = {"package_code": self.package_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Procurement Package", filters):
			frappe.throw(_("Package Code must be unique."), title=_("Duplicate package code"))

	def _validate_method_override(self):
		if self.method_override_flag and not (self.method_override_reason or "").strip():
			frappe.throw(
				_("Method Override Reason is required when Method Override is set."),
				title=_("Missing override reason"),
			)
		if not self.method_override_flag and (self.method_override_reason or "").strip():
			self.method_override_reason = None

	def _apply_template_derived_defaults_c3(self):
		"""When not overriding, copy method/contract from template in Draft / Completed / Returned (C3)."""
		st = self.status or ST_DRAFT
		if st not in _EDITABLE_METHOD_STATUSES:
			return
		if self.method_override_flag:
			return
		if not self.template_id:
			return
		row = frappe.db.get_value(
			"Procurement Template",
			self.template_id,
			("default_method", "default_contract_type", "threshold_rules"),
			as_dict=True,
		)
		if not row:
			return
		if row.threshold_rules not in (None, "", "[]", {}):
			# v1: explicit non-empty threshold_rules are ignored until band interpreter ships.
			pass
		if row.default_method:
			self.procurement_method = row.default_method
		if row.default_contract_type:
			self.contract_type = row.default_contract_type
		raw_am = frappe.db.get_value("Procurement Template", self.template_id, "allowed_methods")
		allowed = self._parse_allowed_methods_list(raw_am)
		if allowed and self.procurement_method not in allowed:
			frappe.throw(
				_(
					"The template default method is not in this template's allowed methods list. "
					"Update the template configuration or use method override with a justification."
				),
				title=_("Invalid template"),
			)

	def _parse_allowed_methods_list(self, raw) -> list[str] | None:
		if raw in (None, ""):
			return None
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, list):
			return None
		out = [str(x).strip() for x in parsed if str(x).strip()]
		return out or None

	def _validate_allowed_methods_from_template_when_overridden(self):
		if not self.method_override_flag or not self.template_id:
			return
		raw = frappe.db.get_value("Procurement Template", self.template_id, "allowed_methods")
		allowed = self._parse_allowed_methods_list(raw)
		if not allowed:
			return
		if self.procurement_method not in allowed:
			frappe.throw(
				_("Overridden procurement method must be one of the template allowed methods: {0}.").format(
					", ".join(allowed)
				),
				title=_("Invalid method"),
			)

	def _validate_procurement_method_editable_states_c3(self):
		"""Method, contract, and override flag may only change while package is editable pre-submit."""
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		st = self.status or ST_DRAFT
		if st in _EDITABLE_METHOD_STATUSES:
			return
		for fn in ("procurement_method", "contract_type", "method_override_flag"):
			if self.has_value_changed(fn):
				frappe.throw(
					_(
						"Procurement method, contract type, and method override may only be changed "
						"while the package is Draft, Completed, or Returned."
					),
					title=_("Method locked"),
				)

	def _validate_competitive_decision_profile(self):
		if self.procurement_method in COMPETITIVE_METHODS and not self.decision_criteria_profile_id:
			frappe.throw(
				_("Decision Criteria Profile is required for competitive methods (Open Tender, RFQ)."),
				title=_("Missing decision criteria"),
			)

	def _active_line_count(self):
		if self.is_new() or not self.name:
			return 0
		return frappe.db.sql(
			"""select count(*) from `tabProcurement Package Line`
			where package_id = %s and ifnull(is_active, 1) = 1""",
			self.name,
		)[0][0]

	def _validate_status_transitions(self):
		new_status = self.status
		if not new_status:
			return

		if self.is_new():
			if new_status == ST_DRAFT:
				return
			self._raise_if_invalid_transition(ST_DRAFT, new_status)
			self._validate_transition_roles(ST_DRAFT, new_status)
			self._validate_transition_reason(ST_DRAFT, new_status)
			self._validate_transition_preconditions(ST_DRAFT, new_status)
			return

		if not self.has_value_changed("status"):
			return

		before = self.get_doc_before_save()
		old_status = (before.get("status") if before else None) or ST_DRAFT
		if old_status == new_status:
			return

		self._raise_if_invalid_transition(old_status, new_status)
		self._validate_transition_roles(old_status, new_status)
		self._validate_transition_reason(old_status, new_status)
		self._validate_transition_preconditions(old_status, new_status)

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
		if (old_status, new_status) in (
			(ST_DRAFT, ST_COMPLETED),
			(ST_RETURNED, ST_COMPLETED),
			(ST_COMPLETED, ST_SUBMITTED),
		):
			if not (roles & _ROLE_PLANNER):
				frappe.throw(
					_(
						"Only a Procurement Planner, Administrator, or System Manager may perform this transition."
					),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) in (
			(ST_SUBMITTED, ST_APPROVED),
			(ST_SUBMITTED, ST_RETURNED),
			(ST_SUBMITTED, ST_REJECTED),
		):
			if not (roles & _ROLE_AUTHORITY):
				frappe.throw(
					_(
						"Only Planning Authority, Administrator, or System Manager may perform this transition."
					),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) == (ST_APPROVED, ST_READY_FOR_TENDER):
			if not (roles & _ROLE_OFFICER_OR_AUTHORITY):
				frappe.throw(
					_(
						"Only Procurement Officer, Planning Authority, or Administrator may mark this package ready for tender."
					),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) == (ST_READY_FOR_TENDER, ST_DRAFT):
			if not (roles & _ROLE_ADMIN_ONLY):
				frappe.throw(
					_(
						"Only Administrator or System Manager may revert a Ready for Tender package to Draft."
					),
					title=_("Not permitted"),
				)
		elif (old_status, new_status) == (ST_READY_FOR_TENDER, ST_RELEASED_TO_TENDER):
			if not (roles & _ROLE_OFFICER_OR_AUTHORITY):
				frappe.throw(
					_("Only Procurement Officer, Planning Authority, or Administrator may release to tender."),
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

	def _validate_transition_preconditions(self, old_status, new_status):
		if (old_status, new_status) in ((ST_DRAFT, ST_COMPLETED), (ST_RETURNED, ST_COMPLETED)):
			if self.is_new():
				frappe.throw(
					_("Save the package once as Draft before completing the package."),
					title=_("Invalid transition"),
				)
			if self._active_line_count() < 1:
				frappe.throw(
					_("At least one active package line is required before completing the package."),
					title=_("Package not ready"),
				)
			from kentender_procurement.procurement_planning.services.package_completeness import (
				get_package_completeness_blockers,
			)

			blockers = get_package_completeness_blockers(self)
			if blockers:
				frappe.throw(
					_("Package is not complete: {0}").format("; ".join(blockers)),
					title=_("Package not complete"),
				)
		elif (old_status, new_status) == (ST_COMPLETED, ST_SUBMITTED):
			if self._active_line_count() < 1:
				frappe.throw(
					_("At least one active package line is required before submitting the package."),
					title=_("Package not ready"),
				)
		elif (old_status, new_status) == (ST_APPROVED, ST_READY_FOR_TENDER):
			if self._active_line_count() < 1:
				frappe.throw(
					_("At least one active package line is required before marking ready for tender."),
					title=_("Package not ready"),
				)
			if self.procurement_method in COMPETITIVE_METHODS and not self.decision_criteria_profile_id:
				frappe.throw(
					_("Decision Criteria Profile is required for competitive methods before handoff."),
					title=_("Missing decision criteria"),
				)
		elif (old_status, new_status) == (ST_READY_FOR_TENDER, ST_RELEASED_TO_TENDER):
			if not getattr(frappe.local, "pp_allow_package_release_to_tender", False):
				frappe.throw(
					_("Release to Tender must be performed via the release workflow action."),
					title=_("Invalid transition"),
				)
			plan_st = frappe.db.get_value("Procurement Plan", self.plan_id, "status")
			if plan_st != "Approved":
				frappe.throw(
					_("Procurement Plan must be Approved before a package can be released to tender."),
					title=_("Plan not approved"),
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

	def _enforce_lock_on_terminal_states(self):
		if self.is_new():
			return
		if _is_privileged_package_actor():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		previous_status = before.get("status") or ST_DRAFT
		if previous_status not in READONLY_STATUSES:
			return

		changed = self._changed_business_fieldnames()
		if not changed:
			return

		if changed.issubset(_ALLOWED_CHANGES_WHEN_READONLY):
			if "status" not in changed and "workflow_reason" in changed:
				frappe.throw(
					_(
						"Submitted, Approved, Ready for Tender, Released to Tender, and Rejected packages are read-only."
					),
					title=_("Record locked"),
				)
			return

		frappe.throw(
			_(
				"Submitted, Approved, Ready for Tender, Released to Tender, and Rejected packages are read-only."
			),
			title=_("Record locked"),
		)

	def _sync_approval_metadata(self):
		if self.status == ST_APPROVED:
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approved_at:
				self.approved_at = now_datetime()
			self.rejected_by = None
			self.rejected_at = None
		elif self.status in (ST_READY_FOR_TENDER, ST_RELEASED_TO_TENDER):
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approved_at:
				self.approved_at = now_datetime()
			self.rejected_by = None
			self.rejected_at = None
			if self.status != ST_RELEASED_TO_TENDER:
				self.released_to_tender_at = None
			elif not self.released_to_tender_at:
				self.released_to_tender_at = now_datetime()
		elif self.status == ST_REJECTED:
			self.approved_by = None
			self.approved_at = None
			self.released_to_tender_at = None
			if not self.rejected_by:
				self.rejected_by = frappe.session.user
			if not self.rejected_at:
				self.rejected_at = now_datetime()
		else:
			self.approved_by = None
			self.approved_at = None
			self.rejected_by = None
			self.rejected_at = None
			self.released_to_tender_at = None
