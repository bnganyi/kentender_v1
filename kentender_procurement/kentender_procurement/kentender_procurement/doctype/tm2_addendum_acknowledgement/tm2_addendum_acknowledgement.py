# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-13 — TM2 Addendum Acknowledgement (doc 9 §5.1, doc 3 §18).

Business code **ACK-{addendum_code}-{supplier_code}** (``supplier_code`` = **Supplier** document name,
same convention as **TM2 Supplier Participation**).

**TM2-ACK-002** — at most one acknowledgement row per **(tm2_addendum, supplier)**.

**TM2-ACK-003** — once **acknowledged** is set, the row is immutable unless
``flags.ignore_tm2_ack_post_ack_immutable``. Acknowledgement cannot be cleared once set.

**Issued addendum** — when **acknowledged** is true (on insert or update), the parent **TM2 Addendum**
must be **Issued** unless ``flags.ignore_tm2_ack_addendum_issued_gate``.

**TM2-ACK-001** (submission blocking) is enforced in bid/submission services (P1-15 / P5), not here.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, now_datetime

_SKIP_POST_ACK_COMPARE: frozenset[str] = frozenset(
	{"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"}
)


class TM2AddendumAcknowledgement(Document):
	def before_insert(self) -> None:
		self._sync_from_links()
		self._allocate_acknowledgement_code()

	def validate(self) -> None:
		self._sync_from_links()
		self._validate_acknowledgement_code_shape()
		self._validate_duplicate_acknowledgement_code()
		self._validate_ack_002_unique_per_addendum_supplier()
		self._validate_addendum_tender_lineage()
		self._validate_supplier_participation()
		self._validate_issued_when_acknowledged()
		self._validate_cannot_clear_acknowledgement()
		if not self.is_new():
			self._validate_ack_003_post_ack_immutable()

	def before_save(self) -> None:
		self._stamp_acknowledgement_metadata()

	def _sync_from_links(self) -> None:
		if self.supplier:
			self.supplier_code = cstr(self.supplier).strip()
		if self.tm2_addendum:
			row = frappe.db.get_value(
				"TM2 Addendum",
				self.tm2_addendum,
				["tm2_tender", "tender_code", "addendum_code"],
				as_dict=True,
			)
			if row:
				self.tm2_tender = row.tm2_tender
				self.tender_code = row.tender_code or self.tender_code
				self.addendum_code = row.addendum_code or self.addendum_code

	def _allocate_acknowledgement_code(self) -> None:
		ac = cstr(self.addendum_code).strip()
		sc = cstr(self.supplier_code).strip()
		if not ac or not sc:
			return
		self.acknowledgement_code = f"ACK-{ac}-{sc}"

	def _validate_acknowledgement_code_shape(self) -> None:
		if not self.is_new():
			return
		ac = cstr(self.addendum_code).strip()
		sc = cstr(self.supplier_code).strip()
		expected = f"ACK-{ac}-{sc}"
		if cstr(self.acknowledgement_code).strip() != expected:
			frappe.throw(
				_("Acknowledgement Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Acknowledgement Code"),
			)

	def _validate_duplicate_acknowledgement_code(self) -> None:
		code = cstr(self.acknowledgement_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Addendum Acknowledgement` where acknowledgement_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Acknowledgement Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Acknowledgement Code"),
			)

	def _validate_ack_002_unique_per_addendum_supplier(self) -> None:
		if not self.tm2_addendum or not self.supplier:
			return
		existing = frappe.db.exists(
			"TM2 Addendum Acknowledgement",
			{"tm2_addendum": self.tm2_addendum, "supplier": self.supplier},
		)
		if existing and existing != self.name:
			frappe.throw(
				_("Only one acknowledgement row is allowed per addendum and supplier (TM2-ACK-002)."),
				title=_("Duplicate Acknowledgement"),
			)

	def _validate_addendum_tender_lineage(self) -> None:
		if not self.tm2_addendum or not self.tm2_tender:
			return
		ad_tender = frappe.db.get_value("TM2 Addendum", self.tm2_addendum, "tm2_tender")
		if ad_tender != self.tm2_tender:
			frappe.throw(
				_("Addendum does not belong to the resolved tender."),
				title=_("Invalid Lineage"),
			)

	def _validate_supplier_participation(self) -> None:
		if getattr(self.flags, "ignore_tm2_ack_participation_gate", False):
			return
		if not self.tm2_tender or not self.supplier:
			return
		if not frappe.db.exists(
			"TM2 Supplier Participation",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
		):
			frappe.throw(
				_("Supplier must have participation on this tender to record addendum acknowledgement."),
				title=_("No Supplier Participation"),
			)

	def _validate_issued_when_acknowledged(self) -> None:
		if not cint(self.acknowledged):
			return
		if getattr(self.flags, "ignore_tm2_ack_addendum_issued_gate", False):
			return
		if not self.tm2_addendum:
			return
		st = cstr(frappe.db.get_value("TM2 Addendum", self.tm2_addendum, "status")).strip()
		if st != "Issued":
			frappe.throw(
				_("Acknowledgement can only be recorded when the addendum is Issued."),
				title=_("Addendum Not Issued"),
			)

	def _validate_cannot_clear_acknowledgement(self) -> None:
		prev = self.get_doc_before_save()
		if not prev:
			return
		if cint(prev.acknowledged) and not cint(self.acknowledged):
			frappe.throw(
				_("Acknowledgement cannot be cleared once set (TM2-ACK-003)."),
				title=_("Acknowledgement Locked"),
			)

	def _validate_ack_003_post_ack_immutable(self) -> None:
		prev = self.get_doc_before_save()
		if not prev or not cint(prev.acknowledged):
			return
		if getattr(self.flags, "ignore_tm2_ack_post_ack_immutable", False):
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_POST_ACK_COMPARE or df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Acknowledged addendum acknowledgement cannot be changed (TM2-ACK-003)."),
					title=_("Immutable Acknowledgement"),
				)

	def _stamp_acknowledgement_metadata(self) -> None:
		prev = self.get_doc_before_save()
		prev_ack = cint(prev.acknowledged) if prev else 0
		if not cint(self.acknowledged) or prev_ack:
			return
		if not self.acknowledged_by:
			self.acknowledged_by = frappe.session.user
		if not self.acknowledged_at:
			self.acknowledged_at = now_datetime()
