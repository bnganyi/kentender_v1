# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-11 — TM2 Addendum (doc 9 §5.1, doc 3 §16).

Business code **ADD-{tender_code}-{##}** (2-digit sequence per tender). **TM2-ID-006** — addendum
numbers match that sequence.

**TM2-ADD-001** — new addenda only when **TM2 Tender** status is **Published**, **Addendum Pending**,
or **Suspended Pending Addendum**, unless ``flags.ignore_tm2_add_tender_state_gate``.

**TM2-ADD-002** — **reason** is mandatory (non-whitespace).

**TM2-ADD-003** — structural **primary_impact_type** (anything other than *No Structural Impact*)
cannot reach **Pending Approval**, **Approved**, or **Issued** without at least one linked
**TM2 Addendum Impact Record** once that DocType exists, unless
``flags.ignore_tm2_add_structural_impact_gate``.

**TM2-ADD-004** — **Issued** addendum is immutable unless ``flags.ignore_tm2_add_issued_immutable``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

_STATUS_OPTIONS: frozenset[str] = frozenset(
	{
		"Draft",
		"Impact Analysis Pending",
		"Impact Analysis Complete",
		"Pending Legal Review",
		"Pending Approval",
		"Approved",
		"Issued",
		"Cancelled",
		"Superseded",
		"Withdrawn",
	}
)

_PRIMARY_IMPACT_OPTIONS: frozenset[str] = frozenset(
	{
		"No Structural Impact",
		"Parameter Change",
		"Deadline Change",
		"Works Requirement Change",
		"BOQ Change",
		"Submission Model Change",
		"Opening Model Change",
		"Evaluation Model Change",
		"Contract Carry-Forward Change",
		"Cancellation / Reissue Required",
	}
)

_ALLOWED_TENDER_STATUSES_FOR_NEW_ADDENDUM: frozenset[str] = frozenset(
	{"Published", "Addendum Pending", "Suspended Pending Addendum"}
)

_STRUCTURAL_GATE_STATUSES: frozenset[str] = frozenset({"Pending Approval", "Approved", "Issued"})

_SKIP_ISSUED_COMPARE: frozenset[str] = frozenset(
	{"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"}
)


class TM2Addendum(Document):
	def before_insert(self) -> None:
		self._sync_tender_code()
		self._allocate_addendum_identity()
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_at:
			self.created_at = now_datetime()

	def validate(self) -> None:
		self._sync_tender_code()
		self._validate_enums()
		self._validate_add_001_tender_state()
		self._validate_add_002_reason()
		self._validate_cancelled_reason()
		self._validate_source_clarification_lineage()
		self._validate_addendum_code_shape()
		self._validate_duplicate_addendum_code()
		self._validate_add_003_structural_impact()
		if not self.is_new():
			self._validate_add_004_issued_immutable()

	def before_save(self) -> None:
		self._stamp_lifecycle_metadata()

	def _sync_tender_code(self) -> None:
		if not self.tm2_tender:
			return
		self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _allocate_addendum_identity(self) -> None:
		if not self.tm2_tender:
			return
		tc = cstr(self.tender_code).strip()
		if not tc:
			return
		prefix = f"ADD-{tc}-"
		rows = frappe.db.sql(
			"select addendum_code from `tabTM2 Addendum` where tm2_tender = %s",
			(self.tm2_tender,),
		)
		max_n = 0
		for (ac,) in rows or []:
			if not ac or not str(ac).startswith(prefix):
				continue
			suffix = str(ac)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		next_n = max_n + 1
		self.addendum_number = next_n
		self.addendum_code = f"{prefix}{next_n:02d}"

	def _validate_enums(self) -> None:
		st = cstr(self.status).strip()
		if st not in _STATUS_OPTIONS:
			frappe.throw(_("Invalid addendum status: {0}").format(frappe.bold(st or _("(empty)"))))
		pit = cstr(self.primary_impact_type).strip()
		if pit not in _PRIMARY_IMPACT_OPTIONS:
			frappe.throw(_("Invalid primary impact type: {0}").format(frappe.bold(pit or _("(empty)"))))

	def _validate_add_001_tender_state(self) -> None:
		if not self.is_new():
			return
		if getattr(self.flags, "ignore_tm2_add_tender_state_gate", False):
			return
		if not self.tm2_tender:
			return
		t_st = cstr(frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")).strip()
		if t_st not in _ALLOWED_TENDER_STATUSES_FOR_NEW_ADDENDUM:
			frappe.throw(
				_(
					"Addendum can only be created when the tender is Published, Addendum Pending, or "
					"Suspended Pending Addendum (TM2-ADD-001)."
				),
				title=_("Invalid Tender State"),
			)

	def _validate_add_002_reason(self) -> None:
		if not cstr(self.reason).strip():
			frappe.throw(_("Addendum reason is required (TM2-ADD-002)."), title=_("Reason Required"))

	def _validate_cancelled_reason(self) -> None:
		if cstr(self.status).strip() != "Cancelled":
			return
		if not cstr(self.cancellation_reason).strip():
			frappe.throw(
				_("Cancellation reason is required when addendum status is Cancelled."),
				title=_("Cancellation Reason Required"),
			)

	def _validate_source_clarification_lineage(self) -> None:
		if not self.tm2_source_clarification_request or not self.tm2_tender:
			return
		req_tender = frappe.db.get_value(
			"TM2 Clarification Request", self.tm2_source_clarification_request, "tm2_tender"
		)
		if req_tender != self.tm2_tender:
			frappe.throw(
				_("Source clarification request does not belong to this tender."),
				title=_("Invalid Lineage"),
			)

	def _validate_addendum_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		ac = cstr(self.addendum_code).strip()
		prefix = f"ADD-{tc}-"
		if not ac.startswith(prefix):
			frappe.throw(
				_("Addendum Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Addendum Code"),
			)
		suffix = ac[len(prefix) :]
		if len(suffix) != 2 or not suffix.isdigit():
			frappe.throw(
				_("Addendum Code suffix must be exactly 2 digits."),
				title=_("Invalid Addendum Code"),
			)
		if int(suffix) != int(self.addendum_number or 0):
			frappe.throw(
				_("Addendum Number must match the numeric suffix of Addendum Code."),
				title=_("Invalid Addendum Number"),
			)

	def _validate_duplicate_addendum_code(self) -> None:
		ac = cstr(self.addendum_code).strip()
		if not ac or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Addendum` where addendum_code = %s",
			(ac,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Addendum Code {0} already exists.").format(frappe.bold(ac)),
				title=_("Duplicate Addendum Code"),
			)

	def _primary_impact_is_structural(self) -> bool:
		return cstr(self.primary_impact_type).strip() != "No Structural Impact"

	def _validate_add_003_structural_impact(self) -> None:
		if getattr(self.flags, "ignore_tm2_add_structural_impact_gate", False):
			return
		st = cstr(self.status).strip()
		if st not in _STRUCTURAL_GATE_STATUSES:
			return
		if not self._primary_impact_is_structural():
			return
		if not frappe.db.exists("DocType", "TM2 Addendum Impact Record"):
			return
		dt = "TM2 Addendum Impact Record"
		if not frappe.db.count(dt, {"tm2_addendum": self.name}):
			frappe.throw(
				_(
					"Structural addendum requires at least one TM2 Addendum Impact Record before "
					"approval or issue (TM2-ADD-003)."
				),
				title=_("Impact Analysis Required"),
			)

	def _validate_add_004_issued_immutable(self) -> None:
		prev = self.get_doc_before_save()
		if not prev or cstr(prev.status).strip() != "Issued":
			return
		if getattr(self.flags, "ignore_tm2_add_issued_immutable", False):
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_ISSUED_COMPARE or df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Issued addendum cannot be changed (TM2-ADD-004)."),
					title=_("Immutable Addendum"),
				)

	def _stamp_lifecycle_metadata(self) -> None:
		prev = self.get_doc_before_save()
		prev_st = cstr(prev.status).strip() if prev else ""
		cur_st = cstr(self.status).strip()
		if prev_st == cur_st:
			return
		if cur_st == "Issued" and prev_st != "Issued":
			if not self.issued_by:
				self.issued_by = frappe.session.user
			if not self.issued_at:
				self.issued_at = now_datetime()
		if cur_st == "Cancelled" and prev_st != "Cancelled":
			if not self.cancelled_by:
				self.cancelled_by = frappe.session.user
			if not self.cancelled_at:
				self.cancelled_at = now_datetime()
