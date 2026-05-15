# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-19 — TM2 Tender Closing Record (doc 9 §5.1, doc 3 §24).

Business code **CLS-{tender_code}** — at most **one closing row per TM2 Tender** (``tm2_tender`` unique).

**TM2-CLS-001** — ``closed_at`` must not be before ``submission_deadline_at`` unless the tender is on an
allowed early-close path (**Cancelled**, **Suspended Pending Addendum**) or
``flags.ignore_tm2_cls_deadline_gate``.

**TM2-CLS-002** — ``closed_at`` defaults to server **now** on insert when omitted.

**TM2-CLS-003** — immutable after insert unless ``flags.ignore_tm2_cls_immutable``.

**TM2-CLS-004** — enforced when wiring closing services / tender status transitions (P5/P6).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.immutability_guards import raise_immutable_after_create

_CLOSING_STATUS_OPTIONS: frozenset[str] = frozenset(
	{
		"Pending",
		"Closed On Time",
		"Closed With No Valid Submissions",
		"Closure Failed",
		"Manually Confirmed",
		"Reopened by Authorized Addendum",
	}
)

_EARLY_CLOSE_TENDER_STATUSES: frozenset[str] = frozenset(
	{
		"Cancelled",
		"Suspended Pending Addendum",
	}
)


class TM2TenderClosingRecord(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_closing_code()
		if self.closing_payload is None:
			self.closing_payload = {}
		if not self.closed_at:
			self.closed_at = now_datetime()
		if not cstr(self.closed_by).strip():
			self.closed_by = "SYSTEM"

	def validate(self) -> None:
		self._sync_identity()
		if self.is_new():
			self._derive_no_valid_submissions_flag()
		self._validate_enums()
		self._validate_closing_code_shape()
		self._validate_duplicate_closing_code()
		self._validate_unique_per_tender()
		self._validate_counts()
		self._validate_cls_001_deadline()
		if not self.is_new():
			self._validate_cls_003_immutable()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if not self.submission_deadline_at and self.tm2_tender:
			tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": self.tm2_tender}, "name")
			if tl_name:
				self.submission_deadline_at = frappe.db.get_value(
					"TM2 Tender Timeline", tl_name, "submission_deadline_at"
				)

	def _allocate_closing_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		if not tc:
			return
		self.closing_code = f"CLS-{tc}"

	def _validate_enums(self) -> None:
		st = cstr(self.closing_status).strip()
		if st not in _CLOSING_STATUS_OPTIONS:
			frappe.throw(_("Invalid closing status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_closing_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		expected = f"CLS-{tc}"
		if cstr(self.closing_code).strip() != expected:
			frappe.throw(
				_("Closing Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Closing Code"),
			)

	def _validate_duplicate_closing_code(self) -> None:
		code = cstr(self.closing_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Tender Closing Record` where closing_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Closing Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Closing Code"),
			)

	def _validate_unique_per_tender(self) -> None:
		if not self.tm2_tender:
			return
		existing = frappe.db.exists("TM2 Tender Closing Record", {"tm2_tender": self.tm2_tender})
		if existing and existing != self.name:
			frappe.throw(
				_("Only one tender closing record is allowed per tender."),
				title=_("Duplicate Tender Closing"),
			)

	def _derive_no_valid_submissions_flag(self) -> None:
		v = int(self.valid_submission_count or 0)
		self.no_valid_submissions = 1 if v == 0 else 0

	def _validate_counts(self) -> None:
		v = int(self.valid_submission_count or 0)
		if v < 0:
			frappe.throw(_("Valid submission count cannot be negative."))
		w = int(self.withdrawn_submission_count or 0)
		if w < 0:
			frappe.throw(_("Withdrawn submission count cannot be negative."))
		lc = int(self.late_attempt_count or 0)
		if lc < 0:
			frappe.throw(_("Late attempt count cannot be negative."))

	def _validate_cls_001_deadline(self) -> None:
		if getattr(self.flags, "ignore_tm2_cls_deadline_gate", False):
			return
		if not self.closed_at or not self.submission_deadline_at:
			return
		if get_datetime(self.closed_at) >= get_datetime(self.submission_deadline_at):
			return
		if not self.tm2_tender:
			return
		st = cstr(frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")).strip()
		if st in _EARLY_CLOSE_TENDER_STATUSES:
			return
		frappe.throw(
			_("Closing cannot be recorded before the submission deadline (TM2-CLS-001)."),
			title=_("Invalid Closing Time"),
		)

	def _validate_cls_003_immutable(self) -> None:
		raise_immutable_after_create(
			self,
			message=_("Tender closing record cannot be changed after creation (TM2-CLS-003)."),
			title=_("Immutable Closing Record"),
			ignore_flag="ignore_tm2_cls_immutable",
		)
