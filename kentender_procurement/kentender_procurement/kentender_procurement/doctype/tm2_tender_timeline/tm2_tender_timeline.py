# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-03 — TM2 Tender Timeline (legal deadlines; doc 9 §5.2.3, doc 3 §8).

Enforces **TM2-ID-005** (one row per tender) via unique ``tm2_tender`` on DocType
and ordering rules **TM2-TTL-001**–**003**. **TM2-TTL-004**: core deadlines are
immutable once the parent **TM2 Tender** is **Published** except extension fields.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


_PUBLISHED_TENDER_STATUS = "Published"

# TM2-TTL-004 — after tender publication, only extension / metadata may change here.
_PUBLISHED_CORE_FIELDS: frozenset[str] = frozenset(
	{
		"planned_publication_at",
		"clarification_deadline_at",
		"addendum_cutoff_at",
		"submission_deadline_at",
		"opening_scheduled_at",
		"tender_validity_days",
		"timezone",
	}
)


class TM2TenderTimeline(Document):
	def before_insert(self) -> None:
		self._sync_tender_code()
		if not self.timeline_code:
			self.timeline_code = f"TTL-{self.tender_code}"
		if not self.created_at:
			self.created_at = now_datetime()
		if not self.updated_at:
			self.updated_at = now_datetime()

	def validate(self) -> None:
		self._sync_tender_code()
		self._validate_one_timeline_per_tender()
		self._validate_duplicate_timeline_code()
		self._validate_deadline_ordering()
		self._validate_published_parent_lock()
		self.updated_at = now_datetime()

	def _sync_tender_code(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _validate_one_timeline_per_tender(self) -> None:
		if not self.is_new() or not self.tm2_tender:
			return
		existing = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": self.tm2_tender}, "name")
		if existing:
			frappe.throw(
				_("Only one Tender Timeline row is allowed per TM2 Tender (TM2-ID-005)."),
				title=_("Duplicate Timeline"),
			)

	def _validate_duplicate_timeline_code(self) -> None:
		tc = (self.timeline_code or "").strip()
		if not tc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Tender Timeline` where timeline_code = %s",
			(tc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Timeline Code {0} already exists.").format(frappe.bold(tc)),
				title=_("Duplicate Timeline Code"),
			)

	def _validate_deadline_ordering(self) -> None:
		clar = self.clarification_deadline_at
		sub = self.submission_deadline_at
		opn = self.opening_scheduled_at
		if clar and sub and get_datetime(clar) >= get_datetime(sub):
			frappe.throw(
				_("Clarification deadline must be before submission deadline (TM2-TTL-002)."),
				title=_("Invalid Timeline"),
			)
		if sub and opn and get_datetime(opn) < get_datetime(sub):
			frappe.throw(
				_("Opening must be on or after submission deadline (TM2-TTL-003)."),
				title=_("Invalid Timeline"),
			)
		pub = self.actual_publication_at or self.planned_publication_at
		if pub and sub and get_datetime(sub) <= get_datetime(pub):
			frappe.throw(
				_("Submission deadline must be after publication time (TM2-TTL-001)."),
				title=_("Invalid Timeline"),
			)

	def _validate_published_parent_lock(self) -> None:
		if not self.tm2_tender or self.is_new():
			return
		status = frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")
		if status != _PUBLISHED_TENDER_STATUS:
			return
		if getattr(self.flags, "ignore_tm2_timeline_publication_lock", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		if getattr(self.flags, "allow_tm2_ttl_addendum_deadline_patch", False):
			allowed_patch = frozenset({"submission_deadline_at", "opening_scheduled_at"})
			for fn in _PUBLISHED_CORE_FIELDS:
				if fn in allowed_patch:
					continue
				if self.get(fn) != prev.get(fn):
					frappe.throw(
						_(
							"Cannot change {0} on timeline while tender is Published (TM2-TTL-004). "
							"Use governed addendum / extension flow."
						).format(fn),
						title=_("Published Timeline Locked"),
					)
			return
		for fn in _PUBLISHED_CORE_FIELDS:
			if self.get(fn) != prev.get(fn):
				frappe.throw(
					_(
						"Cannot change {0} on timeline while tender is Published (TM2-TTL-004). "
						"Use governed addendum / extension flow."
					).format(fn),
					title=_("Published Timeline Locked"),
				)
