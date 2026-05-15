# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-14 — TM2 Bid Draft Metadata (doc 9 §5.1, doc 3 §19).

Business code **BDM-{tender_code}-{supplier_code}** (stable per tender + supplier; not in doc 3 §3.1
table). **No internal draft body fields** on this DocType — only metadata, DSM reference, and
derived validation summary JSON (TM2-BDM-001).

**TM2-BDM-002** — ``dsm_output_code`` is mandatory (draft validation is DSM-bound).

**TM2-BDM-004** — draft metadata cannot be created/updated after **TM2 Tender Timeline**
``submission_deadline_at`` (server time) unless ``flags.ignore_tm2_bdm_deadline_gate``.

**TM2-BDM-003** — ``tm2_final_bid_submission`` is server-controlled (read-only Link to **TM2 Bid
Submission**); do not treat **TM2 Bid Draft Metadata** as an official bid.

Participation on the tender is required unless ``flags.ignore_tm2_bdm_participation_gate``.
New rows require **TM2 Tender** in **Published** (or **Addendum Pending** / **Suspended Pending Addendum**)
unless ``flags.ignore_tm2_bdm_tender_state_gate``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

_DRAFT_STATUS_OPTIONS: frozenset[str] = frozenset({"Draft", "Saved", "Abandoned"})

_COMPLETENESS_OPTIONS: frozenset[str] = frozenset({"Unknown", "Partial", "Complete", "Not Applicable"})

_ALLOWED_TENDER_STATUSES_FOR_DRAFT: frozenset[str] = frozenset(
	{"Published", "Addendum Pending", "Suspended Pending Addendum"}
)


class TM2BidDraftMetadata(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_draft_metadata_code()
		if not self.draft_started_at:
			self.draft_started_at = now_datetime()

	def validate(self) -> None:
		self._sync_identity()
		self._validate_enums()
		self._validate_draft_metadata_code_shape()
		self._validate_duplicate_draft_metadata_code()
		self._validate_unique_per_tender_supplier()
		self._validate_tender_supplier_lineage()
		self._validate_bdm_002_dsm_code()
		self._validate_tender_state_for_new_row()
		self._validate_participation()
		self._validate_bdm_004_submission_deadline()
		if not self.is_new():
			self._validate_identity_immutable()

	def before_save(self) -> None:
		if not self.is_new():
			self.last_saved_at = now_datetime()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.supplier:
			self.supplier_code = cstr(self.supplier).strip()

	def _allocate_draft_metadata_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		if not tc or not sc:
			return
		self.draft_metadata_code = f"BDM-{tc}-{sc}"

	def _validate_enums(self) -> None:
		ds = cstr(self.draft_status).strip()
		if ds not in _DRAFT_STATUS_OPTIONS:
			frappe.throw(_("Invalid draft status: {0}").format(frappe.bold(ds or _("(empty)"))))
		cs = cstr(self.completeness_status).strip()
		if cs not in _COMPLETENESS_OPTIONS:
			frappe.throw(_("Invalid completeness status: {0}").format(frappe.bold(cs or _("(empty)"))))

	def _validate_draft_metadata_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		expected = f"BDM-{tc}-{sc}"
		if cstr(self.draft_metadata_code).strip() != expected:
			frappe.throw(
				_("Draft Metadata Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Draft Metadata Code"),
			)

	def _validate_duplicate_draft_metadata_code(self) -> None:
		code = cstr(self.draft_metadata_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Bid Draft Metadata` where draft_metadata_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Draft Metadata Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Draft Metadata Code"),
			)

	def _validate_unique_per_tender_supplier(self) -> None:
		if not self.tm2_tender or not self.supplier:
			return
		existing = frappe.db.exists(
			"TM2 Bid Draft Metadata",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
		)
		if existing and existing != self.name:
			frappe.throw(
				_("Only one bid draft metadata row is allowed per tender and supplier."),
				title=_("Duplicate Draft Metadata"),
			)

	def _validate_tender_supplier_lineage(self) -> None:
		"""Defensive: tender_code / supplier_code must match links after sync."""
		if not self.tm2_tender or not self.supplier:
			return
		tc = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if cstr(self.tender_code).strip() != cstr(tc).strip():
			frappe.throw(_("Tender code does not match the linked tender."), title=_("Invalid Lineage"))
		if cstr(self.supplier_code).strip() != cstr(self.supplier).strip():
			frappe.throw(_("Supplier code does not match the linked supplier."), title=_("Invalid Lineage"))

	def _validate_bdm_002_dsm_code(self) -> None:
		if not cstr(self.dsm_output_code).strip():
			frappe.throw(
				_("DSM Output Code is required for bid draft metadata (TM2-BDM-002)."),
				title=_("Missing DSM Reference"),
			)

	def _validate_tender_state_for_new_row(self) -> None:
		if not self.is_new():
			return
		if getattr(self.flags, "ignore_tm2_bdm_tender_state_gate", False):
			return
		if not self.tm2_tender:
			return
		st = cstr(frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")).strip()
		if st not in _ALLOWED_TENDER_STATUSES_FOR_DRAFT:
			frappe.throw(
				_(
					"Bid draft metadata can only be created when the tender is Published, "
					"Addendum Pending, or Suspended Pending Addendum."
				),
				title=_("Invalid Tender State"),
			)

	def _validate_participation(self) -> None:
		if getattr(self.flags, "ignore_tm2_bdm_participation_gate", False):
			return
		if not self.tm2_tender or not self.supplier:
			return
		if not frappe.db.exists(
			"TM2 Supplier Participation",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
		):
			frappe.throw(
				_("Supplier must have participation on this tender before bid draft metadata is created."),
				title=_("No Supplier Participation"),
			)

	def _validate_bdm_004_submission_deadline(self) -> None:
		if getattr(self.flags, "ignore_tm2_bdm_deadline_gate", False):
			return
		if not self.tm2_tender:
			return
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": self.tm2_tender}, "name")
		if not tl_name:
			return
		deadline = frappe.db.get_value("TM2 Tender Timeline", tl_name, "submission_deadline_at")
		if not deadline:
			return
		if now_datetime() > get_datetime(deadline):
			frappe.throw(
				_("Bid draft cannot be started or updated after the submission deadline (TM2-BDM-004)."),
				title=_("Past Submission Deadline"),
			)

	def _validate_identity_immutable(self) -> None:
		if getattr(self.flags, "ignore_tm2_bdm_identity_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		for fn in ("tm2_tender", "supplier", "tender_code", "supplier_code", "draft_metadata_code", "draft_started_at"):
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Tender, supplier, and draft start identity cannot be changed."),
					title=_("Immutable Identity"),
				)
