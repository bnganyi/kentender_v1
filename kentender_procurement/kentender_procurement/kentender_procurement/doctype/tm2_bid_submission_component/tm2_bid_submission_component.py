# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-16 — TM2 Bid Submission Component (doc 9 §5.1, doc 3 §21).

Business code **BSC-{bid_code}-{##}** (two-digit sequence per **TM2 Bid Submission**).

**TM2-BSC-001** — ``std_submission_requirement_code`` must be declared by DSM. When
``flags.tm2_bsc_allowed_requirement_codes`` is a ``set``/``frozenset`` of strings, the code must be a
member; when unset and ``flags.ignore_tm2_bsc_dsm_requirement_gate`` is false, only a non-empty code
is required (full DSM graph validation is P6).

**TM2-BSC-002** — ``required`` is immutable after insert; on insert, marking ``required`` requires
passing the DSM gate in **TM2-BSC-001** (unless ``flags.ignore_tm2_bsc_dsm_requirement_gate``).

**TM2-BSC-003** — enforced when finalising bids in submission services (missing required components).

**TM2-BSC-004** — after insert, all substantive fields are immutable unless
``flags.ignore_tm2_bsc_sealed_immutable``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr

_COMPONENT_TYPES: frozenset[str] = frozenset(
	{
		"STRUCTURED_TEXT",
		"STRUCTURED_TEXT_AND_FILE",
		"STRUCTURED_TEXT_AND_TABLE",
		"FILE_SET",
		"OTHER",
	}
)

_VALIDATION_STATUS: frozenset[str] = frozenset({"Pending", "Passed", "Failed", "Warning"})

_FILE_LIKE_TYPES: frozenset[str] = frozenset({"FILE_SET", "STRUCTURED_TEXT_AND_FILE"})

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2BidSubmissionComponent(Document):
	def before_insert(self) -> None:
		self._sync_from_parent()
		self._allocate_bsc_code()

	def validate(self) -> None:
		self._sync_from_parent()
		self._validate_enums()
		self._validate_bsc_code_shape()
		self._validate_duplicate_bsc_code()
		self._validate_unique_requirement_per_bid()
		self._validate_bsc_001()
		self._validate_bsc_002_on_insert()
		self._validate_submitted_payload_refs()
		if not self.is_new():
			self._validate_bsc_002_required_immutable()
			self._validate_bsc_004_immutable()

	def _sync_from_parent(self) -> None:
		if not self.tm2_bid_submission:
			return
		row = frappe.db.get_value(
			"TM2 Bid Submission",
			self.tm2_bid_submission,
			["bid_code", "tm2_tender", "tender_code", "supplier", "supplier_code"],
			as_dict=True,
		)
		if not row:
			return
		self.bid_code = row.bid_code or self.bid_code
		self.tm2_tender = row.tm2_tender
		self.tender_code = row.tender_code or self.tender_code
		self.supplier = row.supplier
		self.supplier_code = row.supplier_code or self.supplier_code

	def _allocate_bsc_code(self) -> None:
		bc = cstr(self.bid_code).strip()
		if not bc or not self.tm2_bid_submission:
			return
		prefix = f"BSC-{bc}-"
		rows = frappe.db.sql(
			"""
			select bsc_code from `tabTM2 Bid Submission Component`
			where tm2_bid_submission = %s
			""",
			(self.tm2_bid_submission,),
		)
		max_n = 0
		for (existing,) in rows or []:
			if not existing or not str(existing).startswith(prefix):
				continue
			suffix = str(existing)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.bsc_code = f"{prefix}{max_n + 1:02d}"

	def _validate_enums(self) -> None:
		ct = cstr(self.component_type).strip()
		if ct not in _COMPONENT_TYPES:
			frappe.throw(_("Invalid component type: {0}").format(frappe.bold(ct or _("(empty)"))))
		vs = cstr(self.validation_status).strip()
		if vs not in _VALIDATION_STATUS:
			frappe.throw(_("Invalid validation status: {0}").format(frappe.bold(vs or _("(empty)"))))

	def _validate_bsc_code_shape(self) -> None:
		if not self.is_new():
			return
		bc = cstr(self.bid_code).strip()
		prefix = f"BSC-{bc}-"
		code = cstr(self.bsc_code).strip()
		if not code.startswith(prefix):
			frappe.throw(
				_("BSC Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid BSC Code"),
			)
		suffix = code[len(prefix) :]
		if len(suffix) != 2 or not suffix.isdigit():
			frappe.throw(_("BSC Code suffix must be exactly 2 digits."), title=_("Invalid BSC Code"))

	def _validate_duplicate_bsc_code(self) -> None:
		code = cstr(self.bsc_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Bid Submission Component` where bsc_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("BSC Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate BSC Code"),
			)

	def _validate_unique_requirement_per_bid(self) -> None:
		req = cstr(self.std_submission_requirement_code).strip()
		if not req or not self.tm2_bid_submission:
			return
		existing = frappe.db.exists(
			"TM2 Bid Submission Component",
			{"tm2_bid_submission": self.tm2_bid_submission, "std_submission_requirement_code": req},
		)
		if existing and existing != self.name:
			frappe.throw(
				_("Only one component row is allowed per bid and STD submission requirement code."),
				title=_("Duplicate Requirement Row"),
			)

	def _validate_bsc_001(self) -> None:
		code = cstr(self.std_submission_requirement_code).strip()
		if not code:
			frappe.throw(
				_("STD Submission Requirement Code is required (TM2-BSC-001)."),
				title=_("Missing DSM Requirement Code"),
			)
		if getattr(self.flags, "ignore_tm2_bsc_dsm_requirement_gate", False):
			return
		allowed = getattr(self.flags, "tm2_bsc_allowed_requirement_codes", None)
		if allowed is not None and code not in allowed:
			frappe.throw(
				_("Requirement code {0} is not declared for this DSM output (TM2-BSC-001).").format(
					frappe.bold(code)
				),
				title=_("Unknown DSM Requirement"),
			)

	def _validate_bsc_002_on_insert(self) -> None:
		if not self.is_new():
			return
		if not cint(self.required):
			return
		if getattr(self.flags, "ignore_tm2_bsc_dsm_requirement_gate", False):
			return
		allowed = getattr(self.flags, "tm2_bsc_allowed_requirement_codes", None)
		if allowed is None:
			frappe.throw(
				_(
					"Marking a component as required needs DSM context "
					"(set flags.tm2_bsc_allowed_requirement_codes or ignore_tm2_bsc_dsm_requirement_gate) "
					"(TM2-BSC-002)."
				),
				title=_("Ad Hoc Required Component"),
			)
		code = cstr(self.std_submission_requirement_code).strip()
		if code not in allowed:
			frappe.throw(
				_("Required components must map to DSM codes (TM2-BSC-002)."),
				title=_("Invalid Required Flag"),
			)

	def _validate_bsc_002_required_immutable(self) -> None:
		prev = self.get_doc_before_save()
		if not prev:
			return
		if cint(prev.required) != cint(self.required):
			frappe.throw(
				_("The required flag cannot change after the row is created (TM2-BSC-002)."),
				title=_("Immutable Requirement Flag"),
			)

	def _validate_submitted_payload_refs(self) -> None:
		if not cint(self.submitted):
			return
		ct = cstr(self.component_type).strip()
		if ct not in _FILE_LIKE_TYPES:
			return
		if not cstr(self.file_ref).strip() and not cstr(self.structured_payload_ref).strip():
			frappe.throw(
				_("Submitted file-like components must include a file or structured payload reference."),
				title=_("Missing Submission Reference"),
			)

	def _validate_bsc_004_immutable(self) -> None:
		if getattr(self.flags, "ignore_tm2_bsc_sealed_immutable", False):
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
					_("Bid submission component fields are sealed with the bid (TM2-BSC-004)."),
					title=_("Immutable Bid Component"),
				)
