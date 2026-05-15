# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-08 — TM2 Supplier Participation (doc 9 §5.1, doc 3 §13).

Business code **TPR-{tender_code}-{supplier_code}** with ``supplier_code`` = Supplier
document name (stable id).

**TM2-SPR-001** — at most one participation row per **(tm2_tender, supplier)**.

``last_bid_submission_code`` stores the **TM2 Bid Submission** ``bid_code`` (same as document name).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr

_STATUS_OPTIONS: frozenset[str] = frozenset(
	{
		"Viewed Tender",
		"Downloaded Documents",
		"Expressed Interest",
		"Clarification Submitted",
		"Bid Draft Started",
		"Bid Submitted",
		"Bid Replaced",
		"Bid Withdrawn",
		"No Response",
		"Ineligible",
	}
)


class TM2SupplierParticipation(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_participation_code()

	def validate(self) -> None:
		self._sync_identity()
		self._validate_status_enum()
		self._validate_participation_code_shape()
		self._validate_duplicate_participation_code()
		self._validate_spr_001_unique_per_tender_supplier()
		self._validate_supplier_immutable()
		self._normalize_json_fields()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.supplier:
			self.supplier_code = cstr(self.supplier).strip()

	def _allocate_participation_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		if not tc or not sc:
			return
		self.participation_code = f"TPR-{tc}-{sc}"

	def _validate_status_enum(self) -> None:
		st = cstr(self.current_status).strip()
		if st not in _STATUS_OPTIONS:
			frappe.throw(_("Invalid participation status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_participation_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		expected = f"TPR-{tc}-{sc}"
		if cstr(self.participation_code).strip() != expected:
			frappe.throw(
				_("Participation Code must be {0}.").format(frappe.bold(expected)),
				title=_("Invalid Participation Code"),
			)

	def _validate_duplicate_participation_code(self) -> None:
		pc = cstr(self.participation_code).strip()
		if not pc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Supplier Participation` where participation_code = %s",
			(pc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Participation Code {0} already exists.").format(frappe.bold(pc)),
				title=_("Duplicate Participation Code"),
			)

	def _validate_spr_001_unique_per_tender_supplier(self) -> None:
		if not self.is_new() or not (self.tm2_tender and self.supplier):
			return
		existing = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
			"name",
		)
		if existing:
			frappe.throw(
				_("Only one supplier participation row is allowed per tender and supplier (TM2-SPR-001)."),
				title=_("Duplicate Participation"),
			)

	def _validate_supplier_immutable(self) -> None:
		if self.is_new():
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		if self.supplier != prev.supplier or self.tm2_tender != prev.tm2_tender:
			frappe.throw(
				_("Cannot change tender or supplier on an existing participation record."),
				title=_("Identity Locked"),
			)

	def _normalize_json_fields(self) -> None:
		if self.eligibility_snapshot is None:
			self.eligibility_snapshot = {}
		if self.addendum_acknowledgement_status is None:
			self.addendum_acknowledgement_status = {}
		if cint(self.clarification_count) < 0:
			self.clarification_count = 0
