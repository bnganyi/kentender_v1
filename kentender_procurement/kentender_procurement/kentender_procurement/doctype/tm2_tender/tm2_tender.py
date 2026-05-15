# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-01 — TM2 Tender canonical lifecycle header (Tender Management v2).

Status vocabulary: doc 4 §4.1 (Tender Lifecycle States).
Tender code pattern: doc 3 §3.1 ``TND-{ENTITY}-{FY}-{####}``.
**EX-04 (doc 9 §25):** ``validate`` rejects v1 DSM/DOM/DEM/DCM rule-injection via
:func:`~kentender_procurement.tender_management.security.legacy_v1_path_guard.assert_tm2_tender_no_legacy_rule_injection`.
**EX-16 (doc 9 §25 / TM2-NB-016):** entering **Published** via :meth:`Document.save` is denied so desk/API
cannot bypass ``publish_tender`` readiness, snapshot, and action-availability checks; governed services
use ``frappe.db.set_value`` or set ``flags.ignore_tm2_tender_governed_status_mutation`` in controlled tests.
"""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode


# Doc 4 — Tender Lifecycle States (strict domain / governance model).
TENDER_LIFECYCLE_STATUSES: tuple[str, ...] = (
	"Draft",
	"STD Instance Incomplete",
	"Ready for Publication Review",
	"Returned for Correction",
	"Approved for Publication",
	"Published",
	"Addendum Pending",
	"Suspended Pending Addendum",
	"Closed",
	"Closed - No Valid Submissions",
	"Opening Ready",
	"Opening Completed",
	"Evaluation Ready",
	"Evaluation In Progress",
	"Awarded",
	"Contract Handoff Completed",
	"Cancelled",
	"Retender Required",
	"Superseded",
	"Archived",
)


def _norm_fiscal_year(value) -> str:
	s = cstr(value).strip()
	if not s:
		return ""
	if s.endswith(".0") and s[:-2].isdigit():
		return s[:-2]
	return s


def _entity_slug(procuring_entity_code: str) -> str:
	raw = re.sub(r"[^0-9A-Za-z]+", "", cstr(procuring_entity_code).upper())
	return (raw[:12] if raw else "UNK")


def _next_tender_sequence(prefix: str) -> int:
	"""Next 4-digit suffix for ``TND-ENTITY-FY-####`` (per existing rows)."""
	like = f"{prefix}-%"
	rows = frappe.db.sql(
		"select tender_code from `tabTM2 Tender` where tender_code like %s",
		(like,),
	)
	max_n = 0
	for (tc,) in rows or []:
		if not tc:
			continue
		parts = tc.rsplit("-", 1)
		if len(parts) == 2 and parts[1].isdigit():
			max_n = max(max_n, int(parts[1]))
	return max_n + 1


def _allocate_tender_code(procuring_entity_code: str, fiscal_year) -> str:
	fy = _norm_fiscal_year(fiscal_year)
	entity = _entity_slug(procuring_entity_code)
	prefix = f"TND-{entity}-{fy}"
	seq = _next_tender_sequence(prefix)
	return f"{prefix}-{seq:04d}"


class TM2Tender(Document):
	def before_insert(self) -> None:
		self._prefill_header_from_planning_links()
		if not cstr(self.status).strip():
			self.status = "Draft"
		self._validate_status_value()
		if not cstr(self.tender_code).strip():
			if not cstr(self.procuring_entity_code).strip() or not cstr(self.fiscal_year).strip():
				frappe.throw(
					_("Procuring Entity Code and Fiscal Year are required to auto-generate Tender Code.")
				)
			self.tender_code = _allocate_tender_code(self.procuring_entity_code, self.fiscal_year)
		if not self.created_by_user:
			self.created_by_user = frappe.session.user
		if not self.created_at:
			self.created_at = now_datetime()

	def _prefill_header_from_planning_links(self) -> None:
		"""Lightweight read so ``tender_code`` allocation can run before full ``validate``."""
		if not self.procurement_package:
			return
		pkg = frappe.db.get_value(
			"Procurement Package",
			self.procurement_package,
			["plan_id", "currency", "procurement_method", "contract_type"],
			as_dict=True,
		)
		if not pkg:
			return
		if pkg.plan_id:
			plan = frappe.db.get_value(
				"Procurement Plan",
				pkg.plan_id,
				["fiscal_year", "procuring_entity", "currency"],
				as_dict=True,
			)
			if plan:
				if not cstr(self.procurement_plan).strip():
					self.procurement_plan = pkg.plan_id
				if not cstr(self.fiscal_year).strip() and plan.fiscal_year is not None:
					self.fiscal_year = _norm_fiscal_year(plan.fiscal_year)
				if not cstr(self.procuring_entity_code).strip() and plan.procuring_entity:
					self.procuring_entity_code = cstr(plan.procuring_entity).strip()
				if not cstr(self.currency).strip() and plan.currency:
					self.currency = plan.currency
		if not cstr(self.currency).strip() and pkg.currency:
			self.currency = pkg.currency
		if not cstr(self.procurement_method).strip() and pkg.procurement_method:
			self.procurement_method = pkg.procurement_method
		if not cstr(self.contract_type).strip() and pkg.contract_type:
			self.contract_type = pkg.contract_type

	def validate(self) -> None:
		self._validate_status_value()
		self._validate_duplicate_tender_code()
		self._sync_from_planning_links()
		self._validate_plan_package_alignment()
		self._reject_direct_publish_status_bypass()
		from kentender_procurement.tender_management.security.legacy_v1_path_guard import (
			assert_tm2_tender_no_legacy_rule_injection,
		)

		assert_tm2_tender_no_legacy_rule_injection(self)
		from kentender_procurement.tender_management.services.planning_tender_handoff_duplicates import (
			validate_at_most_one_active_tm2_tender_per_package,
		)

		validate_at_most_one_active_tm2_tender_per_package(
			self.procurement_package,
			current_tm2_name=None if self.is_new() else self.name,
		)

	def _reject_direct_publish_status_bypass(self) -> None:
		"""Doc 9 §25 **EX-16** / TM2-NB-016 — block ``save()`` paths that skip ``publish_tender``."""
		if getattr(self.flags, "ignore_tm2_tender_governed_status_mutation", False):
			return
		if self.is_new():
			return
		prev = cstr(frappe.db.get_value("TM2 Tender", self.name, "status") or "").strip()
		new_st = cstr(self.status or "").strip()
		if prev == new_st:
			return
		if new_st == "Published" and prev != "Published":
			frappe.throw(
				_(
					"{0}: Tender cannot be set to Published via direct document save. "
					"Use the governed publish service (readiness, publication snapshot, action availability)."
				).format(DenialCode.AUTH_ACTION_AVAILABILITY_DENIED.value),
				title=_("Governed status mutation denied"),
			)

	def _validate_status_value(self) -> None:
		st = cstr(self.status).strip()
		if st not in TENDER_LIFECYCLE_STATUSES:
			frappe.throw(
				_("Invalid tender status {0}. Must be one of the governed lifecycle states.").format(
					frappe.bold(st or _("(empty)"))
				)
			)

	def _validate_duplicate_tender_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		if not tc:
			return
		if self.is_new():
			cnt = frappe.db.sql(
				"select count(*) from `tabTM2 Tender` where tender_code = %s",
				(tc,),
			)[0][0]
			if cnt:
				frappe.throw(
					_("Tender Code {0} already exists.").format(frappe.bold(tc)),
					title=_("Duplicate Tender Code"),
				)

	def _sync_from_planning_links(self) -> None:
		if self.procurement_package:
			pkg = frappe.db.get_value(
				"Procurement Package",
				self.procurement_package,
				["package_code", "plan_id", "procurement_method", "contract_type", "currency"],
				as_dict=True,
			)
			if not pkg:
				frappe.throw(_("Procurement Package {0} not found.").format(self.procurement_package))
			self.procurement_package_code = pkg.package_code
			if pkg.plan_id:
				plan = frappe.db.get_value(
					"Procurement Plan",
					pkg.plan_id,
					["plan_code", "fiscal_year", "procuring_entity", "currency"],
					as_dict=True,
				)
				if plan:
					self.procurement_plan_code = plan.plan_code
					if not self.procurement_plan:
						self.procurement_plan = pkg.plan_id
					if not cstr(self.fiscal_year).strip() and plan.fiscal_year is not None:
						self.fiscal_year = cstr(plan.fiscal_year).strip()
					if not cstr(self.procuring_entity_code).strip() and plan.procuring_entity:
						self.procuring_entity_code = cstr(plan.procuring_entity).strip()
					if not cstr(self.currency).strip() and plan.currency:
						self.currency = plan.currency
			if not cstr(self.procurement_method).strip() and pkg.procurement_method:
				self.procurement_method = pkg.procurement_method
			if not cstr(self.contract_type).strip() and pkg.contract_type:
				self.contract_type = pkg.contract_type
			if not cstr(self.currency).strip() and pkg.currency:
				self.currency = pkg.currency

		if self.procurement_plan and not cstr(self.procurement_plan_code).strip():
			row = frappe.db.get_value(
				"Procurement Plan",
				self.procurement_plan,
				["plan_code", "fiscal_year", "procuring_entity", "currency"],
				as_dict=True,
			)
			if row:
				self.procurement_plan_code = row.plan_code
				if not cstr(self.fiscal_year).strip() and row.fiscal_year is not None:
					self.fiscal_year = cstr(row.fiscal_year).strip()
				if not cstr(self.procuring_entity_code).strip() and row.procuring_entity:
					self.procuring_entity_code = cstr(row.procuring_entity).strip()
				if not cstr(self.currency).strip() and row.currency:
					self.currency = row.currency

	def _validate_plan_package_alignment(self) -> None:
		if not self.procurement_package or not self.procurement_plan:
			return
		plan_from_pkg = frappe.db.get_value("Procurement Package", self.procurement_package, "plan_id")
		if plan_from_pkg and plan_from_pkg != self.procurement_plan:
			frappe.throw(
				_("Procurement Plan {0} does not match the plan on the selected Procurement Package ({1}).").format(
					self.procurement_plan,
					plan_from_pkg,
				)
			)
