# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-12 — TM2 Addendum Impact Record (doc 9 §5.2.6, doc 3 §17).

Business code **AIR-{addendum_code}** per doc 3 §3.1. At most **one** impact row per **TM2 Addendum**
in this schema revision (matches seed ``AIR-ADD-…`` shape without extra suffix).

**TM2-AIR-002** — once the parent **TM2 Addendum** is **Issued**, this record is immutable unless
``flags.ignore_tm2_air_issued_immutable``.

**TM2-AIR-003 / TM2-AIR-004** — revised refs and payload must be supplied by the STD Engine / server
integration (not ad-hoc desk mutation). Row-level enforcement before issue is left to those
services; **Issued** immutability below covers the legally frozen state.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

_SKIP_ISSUED_COMPARE: frozenset[str] = frozenset(
	{"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"}
)


class TM2AddendumImpactRecord(Document):
	def before_insert(self) -> None:
		self._sync_from_addendum()
		self._allocate_impact_record_code()
		self._validate_single_per_addendum()
		if not self.created_at:
			self.created_at = now_datetime()

	def validate(self) -> None:
		self._sync_from_addendum()
		self._validate_std_impact_analysis_code()
		self._validate_impact_payload_present()
		self._validate_impact_record_code_shape()
		self._validate_duplicate_impact_record_code()
		self._validate_addendum_tender_lineage()
		if not self.is_new():
			self._validate_air_002_issued_immutable()

	def _sync_from_addendum(self) -> None:
		if not self.tm2_addendum:
			return
		row = frappe.db.get_value(
			"TM2 Addendum",
			self.tm2_addendum,
			["tm2_tender", "tender_code", "addendum_code"],
			as_dict=True,
		)
		if not row:
			return
		self.tm2_tender = row.tm2_tender
		self.tender_code = row.tender_code or self.tender_code
		self.addendum_code = row.addendum_code or self.addendum_code

	def _allocate_impact_record_code(self) -> None:
		ac = cstr(self.addendum_code).strip()
		if not ac:
			return
		self.impact_record_code = f"AIR-{ac}"

	def _validate_single_per_addendum(self) -> None:
		if not self.tm2_addendum:
			return
		if getattr(self.flags, "allow_tm2_air_duplicate_per_addendum", False):
			return
		existing = frappe.db.exists("TM2 Addendum Impact Record", {"tm2_addendum": self.tm2_addendum})
		if existing:
			frappe.throw(
				_("Only one Addendum Impact Record is allowed per addendum."),
				title=_("Duplicate Impact Record"),
			)

	def _validate_std_impact_analysis_code(self) -> None:
		if not cstr(self.std_impact_analysis_code).strip():
			frappe.throw(
				_("STD Impact Analysis Code is required."),
				title=_("Missing STD Analysis Reference"),
			)

	def _validate_impact_payload_present(self) -> None:
		if self.impact_payload is None:
			frappe.throw(_("Impact Payload is required."), title=_("Missing Impact Payload"))

	def _validate_impact_record_code_shape(self) -> None:
		if not self.is_new():
			return
		ac = cstr(self.addendum_code).strip()
		irc = cstr(self.impact_record_code).strip()
		expected = f"AIR-{ac}"
		if irc != expected:
			frappe.throw(
				_("Impact Record Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Impact Record Code"),
			)

	def _validate_duplicate_impact_record_code(self) -> None:
		irc = cstr(self.impact_record_code).strip()
		if not irc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Addendum Impact Record` where impact_record_code = %s",
			(irc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Impact Record Code {0} already exists.").format(frappe.bold(irc)),
				title=_("Duplicate Impact Record Code"),
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

	def _validate_air_002_issued_immutable(self) -> None:
		prev = self.get_doc_before_save()
		if not prev or not self.tm2_addendum:
			return
		st = cstr(frappe.db.get_value("TM2 Addendum", self.tm2_addendum, "status")).strip()
		if st != "Issued":
			return
		if getattr(self.flags, "ignore_tm2_air_issued_immutable", False):
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_ISSUED_COMPARE or df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Impact record cannot be changed after the addendum is issued (TM2-AIR-002)."),
					title=_("Immutable Impact Record"),
				)
