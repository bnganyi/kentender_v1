# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-07 — TM2 Tender Invitation (doc 9 §5.1, doc 3 §12).

Business code **INV-{tender_code}-{####}** (4-digit sequence per tender).

**TM2-INV-002** — status **Sent** or **Delivered** (including on first save) requires tender
**Published** unless ``flags.ignore_tm2_invitation_publication_gate``.

**TM2-INV-003** — setting status to **Revoked** requires ``revocation_reason`` unless
``flags.ignore_tm2_invitation_revocation_reason_gate``.

**TM2-INV-004** — at most one concurrently-active invitation per (tender, supplier); active
means status in Draft / Sent / Delivered / Accepted.

Supplier link may not change after the invitation has left **Draft** (doc 3 read-only after send).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

_PUBLISHED_TENDER_STATUS = "Published"

_STATUS_OPTIONS: frozenset[str] = frozenset(
	{"Draft", "Sent", "Delivered", "Accepted", "Declined", "Revoked", "Expired", "Superseded"}
)

_ACTIVE_INV_STATUSES: frozenset[str] = frozenset({"Draft", "Sent", "Delivered", "Accepted"})

_SEND_LIKE_STATUSES: frozenset[str] = frozenset({"Sent", "Delivered"})


class TM2TenderInvitation(Document):
	def before_insert(self) -> None:
		self._sync_tender_code()
		self._sync_supplier_snapshots()
		self._allocate_invitation_code()

	def validate(self) -> None:
		self._sync_tender_code()
		self._sync_supplier_snapshots()
		self._validate_status_enum()
		self._validate_invitation_code_shape()
		self._validate_duplicate_invitation_code()
		self._validate_inv_004_one_active_per_supplier()
		self._validate_inv_002_publication_gate()
		self._validate_inv_003_revocation_reason()
		self._validate_supplier_immutable_after_send()

	def _sync_tender_code(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _sync_supplier_snapshots(self) -> None:
		if not self.supplier:
			return
		name = frappe.db.get_value("Supplier", self.supplier, "supplier_name") or self.supplier
		self.supplier_name_snapshot = cstr(name).strip() or self.supplier
		self.supplier_code = cstr(self.supplier).strip()

	def _allocate_invitation_code(self) -> None:
		if not self.tm2_tender:
			return
		tc = cstr(self.tender_code).strip() or (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		)
		prefix = f"INV-{tc}-"
		rows = frappe.db.sql(
			"select invitation_code from `tabTM2 Tender Invitation` where tm2_tender = %s",
			(self.tm2_tender,),
		)
		max_n = 0
		for (ic,) in rows or []:
			if not ic or not str(ic).startswith(prefix):
				continue
			suffix = str(ic)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.invitation_code = f"{prefix}{max_n + 1:04d}"

	def _validate_status_enum(self) -> None:
		st = cstr(self.status).strip()
		if st not in _STATUS_OPTIONS:
			frappe.throw(_("Invalid invitation status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_invitation_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		ic = cstr(self.invitation_code).strip()
		prefix = f"INV-{tc}-"
		if not ic.startswith(prefix):
			frappe.throw(
				_("Invitation Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Invitation Code"),
			)
		suffix = ic[len(prefix) :]
		if len(suffix) != 4 or not suffix.isdigit():
			frappe.throw(
				_("Invitation Code suffix must be exactly 4 digits."),
				title=_("Invalid Invitation Code"),
			)

	def _validate_duplicate_invitation_code(self) -> None:
		ic = cstr(self.invitation_code).strip()
		if not ic or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Tender Invitation` where invitation_code = %s",
			(ic,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Invitation Code {0} already exists.").format(frappe.bold(ic)),
				title=_("Duplicate Invitation Code"),
			)

	def _validate_inv_004_one_active_per_supplier(self) -> None:
		if not self.is_new() or not (self.tm2_tender and self.supplier):
			return
		others = frappe.get_all(
			"TM2 Tender Invitation",
			filters={"tm2_tender": self.tm2_tender, "supplier": self.supplier},
			pluck="name",
		)
		for name in others:
			st = frappe.db.get_value("TM2 Tender Invitation", name, "status")
			if st in _ACTIVE_INV_STATUSES:
				frappe.throw(
					_("An active invitation already exists for this supplier on this tender (TM2-INV-004)."),
					title=_("Duplicate Invitation"),
				)

	def _tender_is_published(self) -> bool:
		if not self.tm2_tender:
			return False
		return (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "status") == _PUBLISHED_TENDER_STATUS
		)

	def _validate_inv_002_publication_gate(self) -> None:
		if getattr(self.flags, "ignore_tm2_invitation_publication_gate", False):
			return
		st = cstr(self.status).strip()
		if st not in _SEND_LIKE_STATUSES:
			return
		if self._tender_is_published():
			return
		frappe.throw(
			_(
				"Invitation cannot be {0} until the tender is Published (TM2-INV-002)."
			).format(frappe.bold(st)),
			title=_("Publication Required"),
		)

	def _validate_inv_003_revocation_reason(self) -> None:
		if cstr(self.status).strip() != "Revoked":
			return
		if getattr(self.flags, "ignore_tm2_invitation_revocation_reason_gate", False):
			return
		if not cstr(self.revocation_reason).strip():
			frappe.throw(
				_("Revocation reason is required when status is Revoked (TM2-INV-003)."),
				title=_("Revocation Reason Required"),
			)

	def _validate_supplier_immutable_after_send(self) -> None:
		if self.is_new():
			return
		prev = self.get_doc_before_save()
		if not prev or not prev.status or prev.status == "Draft":
			return
		if self.supplier != prev.supplier:
			frappe.throw(
				_("Cannot change supplier after invitation has left Draft."),
				title=_("Supplier Locked"),
			)

	def before_save(self) -> None:
		self._stamp_send_metadata()

	def _stamp_send_metadata(self) -> None:
		prev = self.get_doc_before_save()
		prev_st = cstr(prev.status).strip() if prev else ""
		cur_st = cstr(self.status).strip()
		if prev_st == cur_st:
			return
		if cur_st in _SEND_LIKE_STATUSES and prev_st == "Draft":
			if not self.invited_by:
				self.invited_by = frappe.session.user
			if not self.invited_at:
				self.invited_at = now_datetime()
		if cur_st == "Revoked":
			if not self.revoked_by:
				self.revoked_by = frappe.session.user
			if not self.revoked_at:
				self.revoked_at = now_datetime()
