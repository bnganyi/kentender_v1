# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-21 — TM2 Evaluation Handoff Record (doc 9 §5.1, doc 3 §26).

Business code **EHR-{tender_code}** — at most **one evaluation handoff row per TM2 Tender**.

**TM2-EHR-001** — ``opening_record_code`` must be present (completed opening reference) unless
``flags.ignore_tm2_ehr_opening_gate``.

**TM2-EHR-002** — ``dem_output_code`` and ``dsm_output_code`` are mandatory (DEM + DSM bindings).

**TM2-EHR-003** — evaluation criteria live in DEM / Evaluation; this DocType carries references only.

**TM2-EHR-004** — once ``accepted_by_evaluation_at`` is set, the row is immutable except ``modified`` /
``modified_by`` unless ``flags.ignore_tm2_ehr_post_accept_immutable``. Before acceptance,
``handoff_status``, ``accepted_by_evaluation_at``, ``rejection_reason``, ``addendum_history_refs``,
and ``opened_submission_refs`` may change.

**JSON refs** — ``opened_submission_refs`` and ``addendum_history_refs`` use a ``refs`` array inside a JSON
object; bare lists are wrapped on insert. DB string JSON is parsed in validation.
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
		"handoff_status",
		"accepted_by_evaluation_at",
		"rejection_reason",
		"addendum_history_refs",
		"opened_submission_refs",
		"modified",
		"modified_by",
	}
)

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2EvaluationHandoffRecord(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_evaluation_handoff_code()
		self._normalize_refs_json()
		if self.handoff_payload is None:
			self.handoff_payload = {}
		if not self.sent_at:
			self.sent_at = now_datetime()
		if not cstr(self.sent_by).strip():
			self.sent_by = "SYSTEM"

	def validate(self) -> None:
		self._sync_identity()
		self._validate_enums()
		self._validate_evaluation_handoff_code_shape()
		self._validate_duplicate_evaluation_handoff_code()
		self._validate_unique_per_tender()
		self._validate_ehr_001_opening()
		self._validate_ehr_002_outputs()
		self._validate_opened_submission_refs()
		self._validate_addendum_history_refs()
		if not self.is_new():
			self._validate_ehr_004_mutation_rules()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _normalize_refs_json(self) -> None:
		for field in ("opened_submission_refs", "addendum_history_refs"):
			val = self.get(field)
			if val is None:
				if field == "opened_submission_refs":
					self.set(field, {"refs": []})
				continue
			if isinstance(val, list):
				self.set(field, {"refs": val})

	def _allocate_evaluation_handoff_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		if not tc:
			return
		self.evaluation_handoff_code = f"EHR-{tc}"

	def _validate_enums(self) -> None:
		st = cstr(self.handoff_status).strip()
		if st not in _HANDOFF_STATUS_OPTIONS:
			frappe.throw(_("Invalid handoff status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_evaluation_handoff_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		expected = f"EHR-{tc}"
		if cstr(self.evaluation_handoff_code).strip() != expected:
			frappe.throw(
				_("Evaluation Handoff Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Evaluation Handoff Code"),
			)

	def _validate_duplicate_evaluation_handoff_code(self) -> None:
		code = cstr(self.evaluation_handoff_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Evaluation Handoff Record` where evaluation_handoff_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Evaluation Handoff Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Evaluation Handoff Code"),
			)

	def _validate_unique_per_tender(self) -> None:
		if not self.tm2_tender:
			return
		existing = frappe.db.exists("TM2 Evaluation Handoff Record", {"tm2_tender": self.tm2_tender})
		if existing and existing != self.name:
			frappe.throw(
				_("Only one evaluation handoff record is allowed per tender."),
				title=_("Duplicate Evaluation Handoff"),
			)

	def _validate_ehr_001_opening(self) -> None:
		if getattr(self.flags, "ignore_tm2_ehr_opening_gate", False):
			return
		if not cstr(self.opening_record_code).strip():
			frappe.throw(
				_("Opening record code is required (TM2-EHR-001)."),
				title=_("Missing Opening Reference"),
			)

	def _validate_ehr_002_outputs(self) -> None:
		if not cstr(self.dem_output_code).strip():
			frappe.throw(
				_("DEM Output Code is required (TM2-EHR-002)."),
				title=_("Missing DEM Reference"),
			)
		if not cstr(self.dsm_output_code).strip():
			frappe.throw(
				_("DSM Output Code is required (TM2-EHR-002)."),
				title=_("Missing DSM Reference"),
			)
		if not cstr(self.tender_std_instance_code).strip():
			frappe.throw(
				_("Tender STD Instance Code is required."),
				title=_("Missing STD Instance Reference"),
			)

	def _parse_json_field(self, value):
		if isinstance(value, str) and cstr(value).strip():
			try:
				return json.loads(value)
			except json.JSONDecodeError:
				return value
		return value

	def _validate_refs_object(self, value, *, label: str, require_refs_key: bool) -> None:
		if value is None:
			return
		parsed = self._parse_json_field(value)
		if not isinstance(parsed, dict):
			frappe.throw(
				_("{0} must be a JSON object with a refs list.").format(label),
				title=_("Invalid Refs"),
			)
		inner = parsed.get("refs")
		if inner is None and require_refs_key:
			frappe.throw(
				_("{0} must include a refs array.").format(label),
				title=_("Invalid Refs"),
			)
		if inner is None:
			return
		if not isinstance(inner, list):
			frappe.throw(_("{0} refs must be a list.").format(label), title=_("Invalid Refs"))
		for item in inner:
			if not isinstance(item, str) or not cstr(item).strip():
				frappe.throw(
					_("{0} must be a list of non-empty strings.").format(label),
					title=_("Invalid Refs"),
				)

	def _validate_opened_submission_refs(self) -> None:
		if getattr(self.flags, "ignore_tm2_ehr_refs_guard", False):
			return
		self._validate_refs_object(self.opened_submission_refs, label=_("Opened submission refs"), require_refs_key=True)

	def _validate_addendum_history_refs(self) -> None:
		if getattr(self.flags, "ignore_tm2_ehr_refs_guard", False):
			return
		if self.addendum_history_refs is None:
			return
		self._validate_refs_object(
			self.addendum_history_refs, label=_("Addendum history refs"), require_refs_key=False
		)

	def _validate_ehr_004_mutation_rules(self) -> None:
		if getattr(self.flags, "ignore_tm2_ehr_post_accept_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		post_accept = bool(prev.accepted_by_evaluation_at)
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
					"Evaluation handoff record cannot be changed after acceptance by the Evaluation module "
					"(TM2-EHR-004)."
				),
				title=_("Immutable Evaluation Handoff"),
			)
