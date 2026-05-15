# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-20 — TM2 Opening Readiness Record (doc 9 §5.1, doc 3 §25).

Business code **ORR-{tender_code}** — at most **one readiness row per TM2 Tender** (``tm2_tender`` unique).

**TM2-ORR-001** — ``tm2_tender_closing_record`` must belong to the same **TM2 Tender** as ``tm2_tender``
unless ``flags.ignore_tm2_orr_closing_lineage_gate``.

**TM2-ORR-002** — ``dom_output_code`` is mandatory.

**TM2-ORR-003** — register field definitions are owned by DOM / Bid Opening; this DocType stores refs only.

**TM2-ORR-004** — ``sealed_submission_refs`` is a JSON **object** with a ``refs`` key whose value is a list
of non-empty strings (bid codes). Frappe JSON fields do not accept a raw list on the document; services map
DOM arrays into ``refs``.

**TM2-ORR-005** — once ``accepted_by_opening_module_at`` is set, the row is immutable except
``modified`` / ``modified_by`` unless ``flags.ignore_tm2_orr_post_accept_immutable``. Before acceptance,
``readiness_status``, ``blocker_payload``, ``accepted_by_opening_module_at``, ``opening_record_code``,
and ``sealed_submission_refs`` may change.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

_HANDOFF_STATUS_OPTIONS: frozenset[str] = frozenset(
	{"Not Ready", "Ready", "Sent", "Accepted", "Rejected", "Superseded"}
)

_PRE_ACCEPT_MUTABLE: frozenset[str] = frozenset(
	{
		"readiness_status",
		"blocker_payload",
		"accepted_by_opening_module_at",
		"opening_record_code",
		"sealed_submission_refs",
		"modified",
		"modified_by",
	}
)

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2OpeningReadinessRecord(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_opening_readiness_code()
		if self.sealed_submission_refs is None:
			self.sealed_submission_refs = {"refs": []}
		elif isinstance(self.sealed_submission_refs, list):
			self.sealed_submission_refs = {"refs": self.sealed_submission_refs}
		if self.blocker_payload is None:
			self.blocker_payload = {}
		if not self.prepared_at:
			self.prepared_at = now_datetime()
		if not cstr(self.prepared_by).strip():
			self.prepared_by = "SYSTEM"

	def validate(self) -> None:
		self._sync_identity()
		self._validate_enums()
		self._validate_opening_readiness_code_shape()
		self._validate_duplicate_opening_readiness_code()
		self._validate_unique_per_tender()
		self._validate_orr_001_closing_lineage()
		self._validate_orr_002_dom()
		self._validate_orr_004_sealed_refs()
		if not self.is_new():
			self._validate_orr_005_mutation_rules()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _allocate_opening_readiness_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		if not tc:
			return
		self.opening_readiness_code = f"ORR-{tc}"

	def _validate_enums(self) -> None:
		st = cstr(self.readiness_status).strip()
		if st not in _HANDOFF_STATUS_OPTIONS:
			frappe.throw(_("Invalid readiness status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_opening_readiness_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		expected = f"ORR-{tc}"
		if cstr(self.opening_readiness_code).strip() != expected:
			frappe.throw(
				_("Opening Readiness Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Opening Readiness Code"),
			)

	def _validate_duplicate_opening_readiness_code(self) -> None:
		code = cstr(self.opening_readiness_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Opening Readiness Record` where opening_readiness_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Opening Readiness Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Opening Readiness Code"),
			)

	def _validate_unique_per_tender(self) -> None:
		if not self.tm2_tender:
			return
		existing = frappe.db.exists("TM2 Opening Readiness Record", {"tm2_tender": self.tm2_tender})
		if existing and existing != self.name:
			frappe.throw(
				_("Only one opening readiness record is allowed per tender."),
				title=_("Duplicate Opening Readiness"),
			)

	def _validate_orr_001_closing_lineage(self) -> None:
		if getattr(self.flags, "ignore_tm2_orr_closing_lineage_gate", False):
			return
		if not (self.tm2_tender and self.tm2_tender_closing_record):
			return
		cl_tender = frappe.db.get_value(
			"TM2 Tender Closing Record", self.tm2_tender_closing_record, "tm2_tender"
		)
		if cl_tender and cl_tender != self.tm2_tender:
			frappe.throw(
				_("Closing record must belong to the same tender (TM2-ORR-001)."),
				title=_("Invalid Closing Lineage"),
			)

	def _validate_orr_002_dom(self) -> None:
		if not cstr(self.dom_output_code).strip():
			frappe.throw(
				_("DOM Output Code is required (TM2-ORR-002)."),
				title=_("Missing DOM Reference"),
			)
		if not cstr(self.tender_std_instance_code).strip():
			frappe.throw(
				_("Tender STD Instance Code is required."),
				title=_("Missing STD Instance Reference"),
			)

	def _parse_sealed_submission_refs(self):
		refs = self.sealed_submission_refs
		if isinstance(refs, str) and cstr(refs).strip():
			try:
				return json.loads(refs)
			except json.JSONDecodeError:
				return refs
		return refs

	def _validate_orr_004_sealed_refs(self) -> None:
		if getattr(self.flags, "ignore_tm2_orr_sealed_refs_guard", False):
			return
		refs = self._parse_sealed_submission_refs()
		if refs is None:
			return
		if not isinstance(refs, dict):
			frappe.throw(
				_("Sealed submission refs must be a JSON object with a refs list (TM2-ORR-004)."),
				title=_("Invalid Sealed Submission Refs"),
			)
		inner = refs.get("refs")
		if inner is None:
			frappe.throw(
				_("Sealed submission refs must include a refs array (TM2-ORR-004)."),
				title=_("Invalid Sealed Submission Refs"),
			)
		if not isinstance(inner, list):
			frappe.throw(
				_("refs must be a list of bid reference strings (TM2-ORR-004)."),
				title=_("Invalid Sealed Submission Refs"),
			)
		for item in inner:
			if not isinstance(item, str) or not cstr(item).strip():
				frappe.throw(
					_("Each sealed submission ref must be a non-empty string (TM2-ORR-004)."),
					title=_("Invalid Sealed Submission Refs"),
				)

	def _validate_orr_005_mutation_rules(self) -> None:
		if getattr(self.flags, "ignore_tm2_orr_post_accept_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		post_accept = bool(prev.accepted_by_opening_module_at)
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_COMPARE:
				continue
			if df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) == self.get(fn):
				continue
			if not post_accept and fn in _PRE_ACCEPT_MUTABLE:
				continue
			if post_accept and fn in ("modified", "modified_by"):
				continue
			frappe.throw(
				_(
					"Opening readiness record cannot be changed after acceptance by the Opening module "
					"(TM2-ORR-005)."
				),
				title=_("Immutable Opening Readiness"),
			)
