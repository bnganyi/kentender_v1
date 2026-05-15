# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-09 — TM2 Clarification Request (doc 9 §5.1, doc 3 §14).

Business code **CLR-{tender_code}-{####}** (4-digit sequence per tender).

**TM2-CLR-001** — if **TM2 Tender Timeline** exists for the tender, ``submitted_at`` must be on or
before ``clarification_deadline_at`` unless ``flags.ignore_tm2_clr_deadline_gate``.

**TM2-CLR-002** — **TM2 Supplier Participation** must exist for (tender, supplier) unless
``flags.ignore_tm2_clr_access_gate``.

**TM2-CLR-004** — after insert, only **status**, **requires_addendum**, and **tm2_converted_addendum**
may change (plus controlled flags).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

_STATUS_OPTIONS: frozenset[str] = frozenset(
	{
		"Submitted",
		"Under Review",
		"Response Drafted",
		"Pending Approval",
		"Published",
		"Rejected",
		"Converted to Addendum",
		"Withdrawn",
	}
)

# TM2-CLR-004 — content locked after first persistence.
_MUTABLE_AFTER_INSERT: frozenset[str] = frozenset(
	{"status", "requires_addendum", "tm2_converted_addendum", "modified", "modified_by"}
)


class TM2ClarificationRequest(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_clarification_code()
		if not self.submitted_at:
			self.submitted_at = now_datetime()
		if self.attachment_refs is None:
			self.attachment_refs = {}

	def validate(self) -> None:
		self._sync_identity()
		self._validate_status_enum()
		self._validate_clarification_code_shape()
		self._validate_duplicate_clarification_code()
		self._validate_clr_001_deadline()
		self._validate_clr_002_participation()
		if not self.is_new():
			self._validate_clr_004_immutable_content()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.supplier:
			self.supplier_code = cstr(self.supplier).strip()

	def _allocate_clarification_code(self) -> None:
		if not self.tm2_tender:
			return
		tc = cstr(self.tender_code).strip() or (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		)
		prefix = f"CLR-{tc}-"
		rows = frappe.db.sql(
			"select clarification_code from `tabTM2 Clarification Request` where tm2_tender = %s",
			(self.tm2_tender,),
		)
		max_n = 0
		for (cc,) in rows or []:
			if not cc or not str(cc).startswith(prefix):
				continue
			suffix = str(cc)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.clarification_code = f"{prefix}{max_n + 1:04d}"

	def _validate_status_enum(self) -> None:
		st = cstr(self.status).strip()
		if st not in _STATUS_OPTIONS:
			frappe.throw(_("Invalid clarification status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_clarification_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		cc = cstr(self.clarification_code).strip()
		prefix = f"CLR-{tc}-"
		if not cc.startswith(prefix):
			frappe.throw(
				_("Clarification Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Clarification Code"),
			)
		suffix = cc[len(prefix) :]
		if len(suffix) != 4 or not suffix.isdigit():
			frappe.throw(
				_("Clarification Code suffix must be exactly 4 digits."),
				title=_("Invalid Clarification Code"),
			)

	def _validate_duplicate_clarification_code(self) -> None:
		cc = cstr(self.clarification_code).strip()
		if not cc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Clarification Request` where clarification_code = %s",
			(cc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Clarification Code {0} already exists.").format(frappe.bold(cc)),
				title=_("Duplicate Clarification Code"),
			)

	def _validate_clr_001_deadline(self) -> None:
		if getattr(self.flags, "ignore_tm2_clr_deadline_gate", False):
			return
		if not self.tm2_tender or not self.submitted_at:
			return
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": self.tm2_tender}, "name")
		if not tl_name:
			return
		deadline = frappe.db.get_value("TM2 Tender Timeline", tl_name, "clarification_deadline_at")
		if not deadline:
			return
		if get_datetime(self.submitted_at) > get_datetime(deadline):
			frappe.throw(
				_("Clarification must be submitted before the clarification deadline (TM2-CLR-001)."),
				title=_("Past Clarification Deadline"),
			)

	def _validate_clr_002_participation(self) -> None:
		if getattr(self.flags, "ignore_tm2_clr_access_gate", False):
			return
		if not self.tm2_tender or not self.supplier:
			return
		if not frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
			"name",
		):
			frappe.throw(
				_("Supplier must have participation on this tender before submitting a clarification (TM2-CLR-002)."),
				title=_("No Supplier Participation"),
			)

	def _validate_clr_004_immutable_content(self) -> None:
		if getattr(self.flags, "ignore_tm2_clr_immutable_content", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in ("name", "owner", "creation", "docstatus", "idx"):
				continue
			if df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if fn in _MUTABLE_AFTER_INSERT:
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_(
						"Submitted clarification content cannot be changed (TM2-CLR-004); only status, "
						"requires addendum, and converted addendum code may be updated."
					),
					title=_("Immutable Clarification"),
				)
