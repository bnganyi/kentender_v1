# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-18 — TM2 Late Submission Attempt (doc 9 §5.1, doc 3 §23).

Business code **LATE-{tender_code}-{supplier_code}-{##}** (two-digit sequence per tender + supplier),
same supplier_code convention as **TM2 Bid Submission** / **TM2 Supplier Participation** (Supplier name).

**TM2-LATE-001** — enforced by submission services (no **TM2 Bid Submission** on this path); this DocType
only records the rejected attempt.

**TM2-LATE-002** — auditable: required actor/time/deadline/reason; immutable after insert unless
``flags.ignore_tm2_late_submission_attempt_immutable``.

**TM2-LATE-003** — ``attempted_payload_metadata`` must not carry sealed bid content; forbidden top-level
keys in **LATE_FORBIDDEN_METADATA_KEYS** (bypass with ``flags.ignore_tm2_late_metadata_guard``).

**Late-time rule** — ``attempted_at`` must be strictly after ``submission_deadline_at`` unless
``flags.ignore_tm2_late_submission_time_gate`` (tests / controlled backfill).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

LATE_FORBIDDEN_METADATA_KEYS: frozenset[str] = frozenset(
	{
		"sealed_bid_content",
		"full_bid_document",
		"bid_attachment_binary",
		"supplier_private_key",
		"decrypted_bid_payload",
	}
)

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2LateSubmissionAttempt(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._stamp_defaults()
		self._allocate_late_attempt_code()
		if self.attempted_payload_metadata is None:
			self.attempted_payload_metadata = {}

	def validate(self) -> None:
		self._sync_identity()
		self._validate_late_attempt_code_shape()
		self._validate_duplicate_late_attempt_code()
		self._validate_unique_per_tender_supplier_sequence()
		self._validate_rejection_reason()
		self._validate_late_003_metadata()
		self._validate_attempt_after_deadline()
		if not self.is_new():
			self._validate_late_002_immutable()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.supplier:
			self.supplier_code = cstr(self.supplier).strip()
		if not self.submission_deadline_at and self.tm2_tender:
			tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": self.tm2_tender}, "name")
			if tl_name:
				self.submission_deadline_at = frappe.db.get_value(
					"TM2 Tender Timeline", tl_name, "submission_deadline_at"
				)

	def _stamp_defaults(self) -> None:
		if not self.attempted_by:
			self.attempted_by = frappe.session.user
		if not self.attempted_at:
			self.attempted_at = now_datetime()
		if not cstr(self.rejection_reason).strip():
			self.rejection_reason = "AUTH_DEADLINE_PASSED: submission deadline has passed."

	def _allocate_late_attempt_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		if not tc or not sc or not self.tm2_tender or not self.supplier:
			return
		prefix = f"LATE-{tc}-{sc}-"
		rows = frappe.db.sql(
			"""
			select late_attempt_code from `tabTM2 Late Submission Attempt`
			where tm2_tender = %s and supplier = %s
			""",
			(self.tm2_tender, self.supplier),
		)
		max_n = 0
		for (lac,) in rows or []:
			if not lac or not str(lac).startswith(prefix):
				continue
			suffix = str(lac)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.late_attempt_code = f"{prefix}{max_n + 1:02d}"

	def _validate_late_attempt_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		prefix = f"LATE-{tc}-{sc}-"
		code = cstr(self.late_attempt_code).strip()
		if not code.startswith(prefix):
			frappe.throw(
				_("Late Attempt Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Late Attempt Code"),
			)
		suffix = code[len(prefix) :]
		if len(suffix) != 2 or not suffix.isdigit():
			frappe.throw(_("Late Attempt Code suffix must be exactly 2 digits."), title=_("Invalid Late Attempt Code"))

	def _validate_duplicate_late_attempt_code(self) -> None:
		code = cstr(self.late_attempt_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Late Submission Attempt` where late_attempt_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Late Attempt Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Late Attempt Code"),
			)

	def _validate_unique_per_tender_supplier_sequence(self) -> None:
		if not self.tm2_tender or not self.supplier or not self.late_attempt_code:
			return
		rows = frappe.db.sql(
			"""
			select name from `tabTM2 Late Submission Attempt`
			where tm2_tender = %s and supplier = %s and late_attempt_code = %s
			""",
			(self.tm2_tender, self.supplier, self.late_attempt_code),
		)
		for (nm,) in rows or []:
			if nm != self.name:
				frappe.throw(
					_("Duplicate late attempt row for this tender, supplier, and code."),
					title=_("Duplicate Late Submission Attempt"),
				)

	def _validate_rejection_reason(self) -> None:
		if not cstr(self.rejection_reason).strip():
			frappe.throw(_("Rejection reason is required."), title=_("Missing Rejection Reason"))

	def _validate_late_003_metadata(self) -> None:
		if getattr(self.flags, "ignore_tm2_late_metadata_guard", False):
			return
		meta = self.attempted_payload_metadata
		if meta is None:
			return
		if not isinstance(meta, dict):
			frappe.throw(
				_("Attempted payload metadata must be a JSON object (TM2-LATE-003)."),
				title=_("Invalid Metadata"),
			)
		for key in meta:
			if key in LATE_FORBIDDEN_METADATA_KEYS:
				frappe.throw(
					_("Metadata must not include confidential key {0} (TM2-LATE-003).").format(frappe.bold(key)),
					title=_("Invalid Metadata"),
				)

	def _validate_attempt_after_deadline(self) -> None:
		if getattr(self.flags, "ignore_tm2_late_submission_time_gate", False):
			return
		if not self.attempted_at or not self.submission_deadline_at:
			return
		if get_datetime(self.attempted_at) <= get_datetime(self.submission_deadline_at):
			frappe.throw(
				_("A late submission attempt must be recorded after the submission deadline."),
				title=_("Not Late"),
			)

	def _validate_late_002_immutable(self) -> None:
		if getattr(self.flags, "ignore_tm2_late_submission_attempt_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_COMPARE:
				continue
			if df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if fn in ("modified", "modified_by"):
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Late submission attempt cannot be changed after creation (TM2-LATE-002)."),
					title=_("Immutable Late Attempt"),
				)
