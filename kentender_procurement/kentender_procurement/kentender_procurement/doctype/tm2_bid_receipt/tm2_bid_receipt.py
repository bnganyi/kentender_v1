# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-17 — TM2 Bid Receipt (doc 9 §5.1, doc 3 §22).

Business code **RCT-{bid_code}** (``bid_code`` = **TM2 Bid Submission** business code / name).

**TM2-RCT-001** — issuance is expected from submission/replacement/withdrawal services (P6); this DocType
stores the receipt row. At most **one receipt per bid submission** (unique ``tm2_bid_submission``).

**TM2-RCT-002** — ``receipt_payload`` must not carry sealed bid bodies or other confidential content;
top-level keys matching **RCT_FORBIDDEN_PAYLOAD_KEYS** are rejected.

**TM2-RCT-003** — immutable after insert unless ``flags.ignore_tm2_bid_receipt_immutable``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, now_datetime

from kentender_procurement.tender_management.immutability_guards import raise_immutable_after_create

_RECEIPT_TYPES: frozenset[str] = frozenset({"Submission", "Replacement", "Withdrawal"})

# Minimal guard for TM2-RCT-002; extend with service-layer validation when wiring submission flows.
RCT_FORBIDDEN_PAYLOAD_KEYS: frozenset[str] = frozenset(
	{
		"sealed_bid_content",
		"full_bid_document",
		"bid_attachment_binary",
		"supplier_private_key",
		"decrypted_bid_payload",
	}
)


class TM2BidReceipt(Document):
	def before_insert(self) -> None:
		self._sync_from_bid()
		self._allocate_receipt_code()
		if self.receipt_payload is None:
			self.receipt_payload = {}
		if not self.issued_at:
			self.issued_at = now_datetime()
		if not cint(self.issued_by_system):
			self.issued_by_system = 1

	def validate(self) -> None:
		self._sync_from_bid()
		self._validate_enums()
		self._validate_receipt_code_shape()
		self._validate_duplicate_receipt_code()
		self._validate_unique_per_bid_submission()
		self._validate_rct_002_payload()
		if not self.is_new():
			self._validate_rct_003_immutable()

	def _sync_from_bid(self) -> None:
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

	def _allocate_receipt_code(self) -> None:
		bc = cstr(self.bid_code).strip()
		if not bc:
			return
		self.receipt_code = f"RCT-{bc}"

	def _validate_enums(self) -> None:
		rt = cstr(self.receipt_type).strip()
		if rt not in _RECEIPT_TYPES:
			frappe.throw(_("Invalid receipt type: {0}").format(frappe.bold(rt or _("(empty)"))))

	def _validate_receipt_code_shape(self) -> None:
		if not self.is_new():
			return
		bc = cstr(self.bid_code).strip()
		expected = f"RCT-{bc}"
		if cstr(self.receipt_code).strip() != expected:
			frappe.throw(
				_("Receipt Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Receipt Code"),
			)

	def _validate_duplicate_receipt_code(self) -> None:
		code = cstr(self.receipt_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Bid Receipt` where receipt_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Receipt Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Receipt Code"),
			)

	def _validate_unique_per_bid_submission(self) -> None:
		if not self.tm2_bid_submission:
			return
		existing = frappe.db.exists("TM2 Bid Receipt", {"tm2_bid_submission": self.tm2_bid_submission})
		if existing and existing != self.name:
			frappe.throw(
				_("Only one receipt is allowed per bid submission (TM2-RCT-001)."),
				title=_("Duplicate Bid Receipt"),
			)

	def _validate_rct_002_payload(self) -> None:
		if getattr(self.flags, "ignore_tm2_bid_receipt_payload_guard", False):
			return
		payload = self.receipt_payload
		if payload is None:
			return
		if not isinstance(payload, dict):
			frappe.throw(
				_("Receipt payload must be a JSON object (TM2-RCT-002)."),
				title=_("Invalid Receipt Payload"),
			)
		for key in payload:
			if key in RCT_FORBIDDEN_PAYLOAD_KEYS:
				frappe.throw(
					_("Receipt payload must not include confidential key {0} (TM2-RCT-002).").format(
						frappe.bold(key)
					),
					title=_("Invalid Receipt Payload"),
				)

	def _validate_rct_003_immutable(self) -> None:
		raise_immutable_after_create(
			self,
			message=_("Bid receipt cannot be changed after creation (TM2-RCT-003)."),
			title=_("Immutable Bid Receipt"),
			ignore_flag="ignore_tm2_bid_receipt_immutable",
		)
