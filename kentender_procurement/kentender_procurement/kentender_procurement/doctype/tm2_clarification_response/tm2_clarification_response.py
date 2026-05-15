# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-10 — TM2 Clarification Response (doc 9 §5.1, doc 3 §15).

Business code **CLRR-{clarification_code}-{##}** (2-digit sequence per clarification request).

**TM2-CLRR-001** — **Published** requires **approved_by** and **approved_at** unless
``flags.ignore_tm2_clrr_approval_gate``.

**TM2-CLRR-002** — cannot set **Published** when **addendum_required** is set unless
``flags.ignore_tm2_clrr_addendum_publish_gate``.

**TM2-CLRR-003** — once **Published**, the document is immutable unless
``flags.ignore_tm2_clrr_published_immutable``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

_STATUS_OPTIONS: frozenset[str] = frozenset(
	{
		"Draft",
		"Response Drafted",
		"Pending Approval",
		"Published",
		"Rejected",
		"Returned",
		"Converted to Addendum",
	}
)

_VISIBILITY_OPTIONS: frozenset[str] = frozenset(
	{"Requesting Supplier Only", "All Participants", "Public", "Internal Only"}
)

_SKIP_PUBLISHED_COMPARE: frozenset[str] = frozenset(
	{"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx"}
)


class TM2ClarificationResponse(Document):
	def before_insert(self) -> None:
		self._sync_from_request()
		self._allocate_response_code()
		if not self.drafted_by:
			self.drafted_by = frappe.session.user
		if not self.drafted_at:
			self.drafted_at = now_datetime()

	def validate(self) -> None:
		self._sync_from_request()
		self._validate_status_and_visibility()
		self._validate_response_code_shape()
		self._validate_duplicate_response_code()
		self._validate_request_tender_lineage()
		self._validate_clrr_001_approval_for_publish()
		self._validate_clrr_002_addendum_vs_publish()
		if not self.is_new():
			self._validate_clrr_003_published_immutable()

	def before_save(self) -> None:
		self._stamp_publication_metadata()

	def _sync_from_request(self) -> None:
		if not self.tm2_clarification_request:
			return
		req_tender, req_code = frappe.db.get_value(
			"TM2 Clarification Request",
			self.tm2_clarification_request,
			("tm2_tender", "clarification_code"),
		) or (None, None)
		self.clarification_request_code = cstr(req_code).strip() or self.clarification_request_code
		if req_tender:
			self.tm2_tender = req_tender
			self.tender_code = frappe.db.get_value("TM2 Tender", req_tender, "tender_code") or req_tender

	def _allocate_response_code(self) -> None:
		cc = cstr(self.clarification_request_code).strip()
		if not cc or not self.tm2_clarification_request:
			return
		prefix = f"CLRR-{cc}-"
		rows = frappe.db.sql(
			"""
			select response_code from `tabTM2 Clarification Response`
			where tm2_clarification_request = %s
			""",
			(self.tm2_clarification_request,),
		)
		max_n = 0
		for (rc,) in rows or []:
			if not rc or not str(rc).startswith(prefix):
				continue
			suffix = str(rc)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.response_code = f"{prefix}{max_n + 1:02d}"

	def _validate_status_and_visibility(self) -> None:
		st = cstr(self.status).strip()
		if st not in _STATUS_OPTIONS:
			frappe.throw(_("Invalid response status: {0}").format(frappe.bold(st or _("(empty)"))))
		v = cstr(self.visibility).strip()
		if v not in _VISIBILITY_OPTIONS:
			frappe.throw(_("Invalid visibility: {0}").format(frappe.bold(v or _("(empty)"))))

	def _validate_response_code_shape(self) -> None:
		if not self.is_new():
			return
		cc = cstr(self.clarification_request_code).strip()
		rc = cstr(self.response_code).strip()
		prefix = f"CLRR-{cc}-"
		if not rc.startswith(prefix):
			frappe.throw(
				_("Response Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Response Code"),
			)
		suffix = rc[len(prefix) :]
		if len(suffix) != 2 or not suffix.isdigit():
			frappe.throw(
				_("Response Code suffix must be exactly 2 digits."),
				title=_("Invalid Response Code"),
			)

	def _validate_duplicate_response_code(self) -> None:
		rc = cstr(self.response_code).strip()
		if not rc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Clarification Response` where response_code = %s",
			(rc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Response Code {0} already exists.").format(frappe.bold(rc)),
				title=_("Duplicate Response Code"),
			)

	def _validate_request_tender_lineage(self) -> None:
		if not self.tm2_clarification_request or not self.tm2_tender:
			return
		req_tender = frappe.db.get_value(
			"TM2 Clarification Request", self.tm2_clarification_request, "tm2_tender"
		)
		if req_tender != self.tm2_tender:
			frappe.throw(
				_("Clarification request does not belong to the resolved tender."),
				title=_("Invalid Lineage"),
			)

	def _validate_clrr_001_approval_for_publish(self) -> None:
		if cstr(self.status).strip() != "Published":
			return
		if getattr(self.flags, "ignore_tm2_clrr_approval_gate", False):
			return
		if not self.approved_by or not self.approved_at:
			frappe.throw(
				_("Published clarification responses require approval metadata (TM2-CLRR-001)."),
				title=_("Approval Required"),
			)

	def _validate_clrr_002_addendum_vs_publish(self) -> None:
		if cstr(self.status).strip() != "Published":
			return
		if not self.addendum_required:
			return
		if getattr(self.flags, "ignore_tm2_clrr_addendum_publish_gate", False):
			return
		frappe.throw(
			_(
				"Cannot publish as ordinary clarification when addendum is required (TM2-CLRR-002); "
				"use addendum / conversion path."
			),
			title=_("Addendum Required"),
		)

	def _validate_clrr_003_published_immutable(self) -> None:
		prev = self.get_doc_before_save()
		if not prev or cstr(prev.status).strip() != "Published":
			return
		if getattr(self.flags, "ignore_tm2_clrr_published_immutable", False):
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_PUBLISHED_COMPARE or df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) != self.get(fn):
				frappe.throw(
					_("Published clarification response cannot be changed (TM2-CLRR-003)."),
					title=_("Immutable Response"),
				)

	def _stamp_publication_metadata(self) -> None:
		prev = self.get_doc_before_save()
		prev_st = cstr(prev.status).strip() if prev else ""
		cur_st = cstr(self.status).strip()
		if prev_st == cur_st:
			return
		if cur_st == "Published" and prev_st != "Published":
			if not self.published_by:
				self.published_by = frappe.session.user
			if not self.published_at:
				self.published_at = now_datetime()
