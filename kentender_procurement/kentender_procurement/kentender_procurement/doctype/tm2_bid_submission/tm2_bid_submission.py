# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-15 — TM2 Bid Submission (doc 9 §5.2.7, doc 3 §20).

Business code **BID-{tender_code}-{supplier_code}-{##}** (2-digit sequence per tender + supplier).

**TM2-BID-001 / TM2-BID-009** — insert/update rejected after **TM2 Tender Timeline**
``submission_deadline_at`` unless ``flags.ignore_tm2_bid_deadline_gate``.

**TM2-BID-002** — ``dsm_output_code`` is mandatory.

**TM2-BID-003** — ``sealed_at`` is stamped with ``submitted_at`` when omitted so the row is sealed
at submission time.

**TM2-LOCK-008** — after insert, core submission references (DSM, publication snapshot, STD instance,
identity, seal timestamps, hash, finance snapshot, acknowledgement JSON) are immutable unless
``flags.ignore_tm2_bid_submission_core_immutable``. Pipeline fields **bid_status**, **opened_at**,
**evaluation_locked_at**, withdrawal, and **superseded_by_tm2_bid_submission** may still change.

``after_insert`` updates **TM2 Supplier Participation** ``last_bid_submission_code`` / ``bid_submitted_at``
and links **TM2 Bid Draft Metadata** ``tm2_final_bid_submission`` when a draft row exists.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, get_datetime, now_datetime

_BID_STATUS_OPTIONS: frozenset[str] = frozenset(
	{
		"Draft",
		"Submitted",
		"Sealed",
		"Superseded",
		"Withdrawn",
		"Late Attempt Rejected",
		"Opened",
		"Excluded by System Rule",
		"Evaluation Locked",
	}
)

_ALLOWED_TENDER_STATUSES_FOR_BID: frozenset[str] = frozenset(
	{"Published", "Addendum Pending", "Suspended Pending Addendum"}
)

_POST_INSERT_MUTABLE: frozenset[str] = frozenset(
	{
		"bid_status",
		"opened_at",
		"evaluation_locked_at",
		"withdrawn_by",
		"withdrawn_at",
		"withdrawal_reason",
		"superseded_by_tm2_bid_submission",
		"modified",
		"modified_by",
	}
)

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2BidSubmission(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_bid_identity()
		if not self.submitted_by:
			self.submitted_by = frappe.session.user
		ts = now_datetime()
		if not self.submitted_at:
			self.submitted_at = ts
		if not self.sealed_at:
			self.sealed_at = self.submitted_at
		if not cstr(self.currency).strip() and self.tm2_tender:
			self.currency = cstr(frappe.db.get_value("TM2 Tender", self.tm2_tender, "currency")).strip() or "KES"
		if self.addendum_acknowledgement_snapshot is None:
			self.addendum_acknowledgement_snapshot = {}

	def validate(self) -> None:
		self._sync_identity()
		self._validate_enums()
		self._validate_bid_code_shape()
		self._validate_duplicate_bid_code()
		self._validate_unique_per_tender_supplier_sequence()
		self._validate_tender_supplier_lineage()
		self._validate_previous_submission_lineage()
		self._validate_tender_state_for_new_row()
		self._validate_participation()
		self._validate_bid_001_deadline()
		self._validate_bid_002_dsm()
		self._validate_publication_and_std_refs()
		if not self.is_new():
			self._validate_core_immutable_after_insert()

	def after_insert(self) -> None:
		self._sync_participation_last_bid()
		self._sync_bid_draft_final_link()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.supplier:
			self.supplier_code = cstr(self.supplier).strip()

	def _allocate_bid_identity(self) -> None:
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		if not tc or not sc or not self.tm2_tender or not self.supplier:
			return
		prefix = f"BID-{tc}-{sc}-"
		rows = frappe.db.sql(
			"""
			select bid_code from `tabTM2 Bid Submission`
			where tm2_tender = %s and supplier = %s
			""",
			(self.tm2_tender, self.supplier),
		)
		max_n = 0
		for (bc,) in rows or []:
			if not bc or not str(bc).startswith(prefix):
				continue
			suffix = str(bc)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		next_n = max_n + 1
		self.submission_sequence = next_n
		self.bid_code = f"{prefix}{next_n:02d}"

	def _validate_enums(self) -> None:
		st = cstr(self.bid_status).strip()
		if st not in _BID_STATUS_OPTIONS:
			frappe.throw(_("Invalid bid status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_bid_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		sc = cstr(self.supplier_code).strip()
		prefix = f"BID-{tc}-{sc}-"
		bc = cstr(self.bid_code).strip()
		if not bc.startswith(prefix):
			frappe.throw(
				_("Bid Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Bid Code"),
			)
		suffix = bc[len(prefix) :]
		if len(suffix) != 2 or not suffix.isdigit():
			frappe.throw(_("Bid Code suffix must be exactly 2 digits."), title=_("Invalid Bid Code"))
		if int(suffix) != int(self.submission_sequence or 0):
			frappe.throw(
				_("Submission Sequence must match the numeric suffix of Bid Code."),
				title=_("Invalid Submission Sequence"),
			)

	def _validate_duplicate_bid_code(self) -> None:
		bc = cstr(self.bid_code).strip()
		if not bc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Bid Submission` where bid_code = %s",
			(bc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Bid Code {0} already exists.").format(frappe.bold(bc)),
				title=_("Duplicate Bid Code"),
			)

	def _validate_unique_per_tender_supplier_sequence(self) -> None:
		if not self.tm2_tender or not self.supplier or not self.bid_code:
			return
		rows = frappe.db.sql(
			"""
			select name from `tabTM2 Bid Submission`
			where tm2_tender = %s and supplier = %s and bid_code = %s
			""",
			(self.tm2_tender, self.supplier, self.bid_code),
		)
		for (nm,) in rows or []:
			if nm != self.name:
				frappe.throw(
					_("Duplicate bid row for this tender, supplier, and bid code."),
					title=_("Duplicate Bid Submission"),
				)

	def _validate_tender_supplier_lineage(self) -> None:
		if not self.tm2_tender or not self.supplier:
			return
		tc = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if cstr(self.tender_code).strip() != cstr(tc).strip():
			frappe.throw(_("Tender code does not match the linked tender."), title=_("Invalid Lineage"))
		if cstr(self.supplier_code).strip() != cstr(self.supplier).strip():
			frappe.throw(_("Supplier code does not match the linked supplier."), title=_("Invalid Lineage"))

	def _validate_previous_submission_lineage(self) -> None:
		if not self.previous_tm2_bid_submission:
			return
		row = frappe.db.get_value(
			"TM2 Bid Submission",
			self.previous_tm2_bid_submission,
			["tm2_tender", "supplier"],
			as_dict=True,
		)
		if not row:
			return
		if row.tm2_tender != self.tm2_tender or row.supplier != self.supplier:
			frappe.throw(
				_("Previous bid submission must be for the same tender and supplier."),
				title=_("Invalid Lineage"),
			)

	def _validate_tender_state_for_new_row(self) -> None:
		if not self.is_new():
			return
		if getattr(self.flags, "ignore_tm2_bid_tender_state_gate", False):
			return
		if not self.tm2_tender:
			return
		st = cstr(frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")).strip()
		if st not in _ALLOWED_TENDER_STATUSES_FOR_BID:
			frappe.throw(
				_(
					"Bid submission can only be created when the tender is Published, Addendum Pending, "
					"or Suspended Pending Addendum."
				),
				title=_("Invalid Tender State"),
			)

	def _validate_participation(self) -> None:
		if getattr(self.flags, "ignore_tm2_bid_participation_gate", False):
			return
		if not self.tm2_tender or not self.supplier:
			return
		if not frappe.db.exists(
			"TM2 Supplier Participation",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
		):
			frappe.throw(
				_("Supplier must have participation on this tender before submitting a bid."),
				title=_("No Supplier Participation"),
			)

	def _validate_bid_001_deadline(self) -> None:
		if getattr(self.flags, "ignore_tm2_bid_deadline_gate", False):
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
				_("Bid submission is not permitted after the submission deadline (TM2-BID-001)."),
				title=_("Past Submission Deadline"),
			)

	def _validate_bid_002_dsm(self) -> None:
		if not cstr(self.dsm_output_code).strip():
			frappe.throw(
				_("DSM Output Code is required (TM2-BID-002)."),
				title=_("Missing DSM Reference"),
			)

	def _validate_publication_and_std_refs(self) -> None:
		if not cstr(self.publication_snapshot_code).strip():
			frappe.throw(
				_("Publication Snapshot Code is required."),
				title=_("Missing Publication Snapshot"),
			)
		if not cstr(self.tender_std_instance_code).strip():
			frappe.throw(
				_("Tender STD Instance Code is required."),
				title=_("Missing STD Instance Reference"),
			)

	def _validate_core_immutable_after_insert(self) -> None:
		if getattr(self.flags, "ignore_tm2_bid_submission_core_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_COMPARE or fn in _POST_INSERT_MUTABLE:
				continue
			if df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Submitted bid fields cannot be changed (TM2-LOCK-008)."),
					title=_("Immutable Bid Submission"),
				)

	def _sync_participation_last_bid(self) -> None:
		part = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
			"name",
		)
		if not part:
			return
		frappe.db.set_value(
			"TM2 Supplier Participation",
			part,
			{
				"last_bid_submission_code": self.bid_code,
				"bid_submitted_at": self.submitted_at or now_datetime(),
				"current_status": "Bid Submitted",
			},
		)

	def _sync_bid_draft_final_link(self) -> None:
		bdm = frappe.db.get_value(
			"TM2 Bid Draft Metadata",
			{"tm2_tender": self.tm2_tender, "supplier": self.supplier},
			"name",
		)
		if not bdm:
			return
		frappe.db.set_value("TM2 Bid Draft Metadata", bdm, "tm2_final_bid_submission", self.name)
