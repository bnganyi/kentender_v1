# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-06 — TM2 Tender Access Rule (doc 9 §5.1, doc 3 §11, doc 7 §6.3).

One access rule row per tender (unique ``tm2_tender``). Business code **TAC-{tender_code}**.

**TM2-ACR-001** — **Restricted** or **Direct Invitation** visibility requires
``requires_invitation`` or ``eligibility_service_required``.

**TM2-ACR-003** — after parent **TM2 Tender** is **Published**, policy fields cannot change
unless ``flags.ignore_tm2_access_rule_publication_lock``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

_PUBLISHED_TENDER_STATUS = "Published"

_VISIBILITY_OPTIONS: frozenset[str] = frozenset(
	{"Internal Only", "Public", "Login Required", "Restricted", "Direct Invitation"}
)

# TM2-ACR-003 — policy surface locked post-publication (snapshot remains server-controlled).
_PUBLISHED_LOCKED_FIELDS: frozenset[str] = frozenset(
	{
		"visibility",
		"requires_supplier_login_for_documents",
		"requires_invitation",
		"allows_public_notice",
		"allows_public_document_download",
		"supplier_category_restriction",
		"eligibility_service_required",
	}
)

_RESTRICTED_LIKE: frozenset[str] = frozenset({"Restricted", "Direct Invitation"})


class TM2TenderAccessRule(Document):
	def before_insert(self) -> None:
		self._sync_tender_code()
		if not self.access_rule_code:
			self.access_rule_code = f"TAC-{self.tender_code}"
		if not self.created_at:
			self.created_at = now_datetime()
		if not self.updated_at:
			self.updated_at = now_datetime()

	def validate(self) -> None:
		self._sync_tender_code()
		self._validate_visibility_enum()
		self._validate_access_rule_code_shape()
		self._validate_one_rule_per_tender()
		self._validate_duplicate_access_rule_code()
		self._validate_acr_001_restricted_access_path()
		self._validate_published_parent_lock()
		self.updated_at = now_datetime()

	def _sync_tender_code(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _validate_access_rule_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		expected = f"TAC-{tc}"
		if cstr(self.access_rule_code).strip() != expected:
			frappe.throw(
				_("Access Rule Code must be {0}.").format(frappe.bold(expected)),
				title=_("Invalid Access Rule Code"),
			)

	def _validate_visibility_enum(self) -> None:
		v = cstr(self.visibility).strip()
		if v not in _VISIBILITY_OPTIONS:
			frappe.throw(_("Invalid visibility: {0}").format(frappe.bold(v or _("(empty)"))))

	def _validate_one_rule_per_tender(self) -> None:
		if not self.is_new() or not self.tm2_tender:
			return
		existing = frappe.db.get_value("TM2 Tender Access Rule", {"tm2_tender": self.tm2_tender}, "name")
		if existing:
			frappe.throw(
				_("Only one Tender Access Rule is allowed per TM2 Tender."),
				title=_("Duplicate Access Rule"),
			)

	def _validate_duplicate_access_rule_code(self) -> None:
		code = cstr(self.access_rule_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Tender Access Rule` where access_rule_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Access Rule Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Access Rule Code"),
			)

	def _validate_acr_001_restricted_access_path(self) -> None:
		vis = cstr(self.visibility).strip()
		if vis not in _RESTRICTED_LIKE:
			return
		if not (self.requires_invitation or self.eligibility_service_required):
			frappe.throw(
				_(
					"Restricted or Direct Invitation visibility requires invitation and/or "
					"eligibility service (TM2-ACR-001)."
				),
				title=_("Invalid Access Rule"),
			)

	def _validate_published_parent_lock(self) -> None:
		if not self.tm2_tender or self.is_new():
			return
		status = frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")
		if status != _PUBLISHED_TENDER_STATUS:
			return
		if getattr(self.flags, "ignore_tm2_access_rule_publication_lock", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		for fn in _PUBLISHED_LOCKED_FIELDS:
			if self.get(fn) != prev.get(fn):
				frappe.throw(
					_(
						"Cannot change {0} on access rule while tender is Published (TM2-ACR-003). "
						"Use governed addendum or authorized change."
					).format(fn),
					title=_("Published Access Rule Locked"),
				)
