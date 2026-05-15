# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-22 — TM2 Contract Handoff Reference (doc 9 §5.1, doc 3 §27).

Business code **CHR-{tender_code}** — at most **one contract handoff reference per TM2 Tender**.

**TM2-CHR-001** — ``award_decision_code`` must be present (award decision reference) unless
``flags.ignore_tm2_chr_award_gate``.

**TM2-CHR-002** — ``dcm_output_code`` is mandatory (DCM binding).

**TM2-CHR-003** — when the linked tender ``procurement_category`` is **Works**, require a positive
``final_evaluated_price`` and non-empty ``final_boq_reference`` (corrected evaluated BOQ path) unless
``flags.ignore_tm2_chr_works_price_gate``.

**TM2-CHR-004** — Tender Management does not author contract terms; this DocType carries references and
payload bundle only (enforced by product scope, not field-level term editors).

**TM2-CHR-005** — once ``accepted_by_contract_module_at`` is set, the row is immutable except ``modified`` /
``modified_by`` unless ``flags.ignore_tm2_chr_post_accept_immutable``. Before acceptance,
``handoff_status``, ``accepted_by_contract_module_at``, ``rejection_reason``, and
``addendum_history_refs`` may change.

**JSON refs** — ``addendum_history_refs`` uses a ``refs`` array inside a JSON object when present; bare
lists are wrapped on insert. DB string JSON is parsed in validation.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, now_datetime

_HANDOFF_STATUS_OPTIONS: frozenset[str] = frozenset(
	{"Not Ready", "Ready", "Sent", "Accepted", "Rejected", "Superseded"}
)

_PRE_ACCEPT_MUTABLE: frozenset[str] = frozenset(
	{
		"handoff_status",
		"accepted_by_contract_module_at",
		"rejection_reason",
		"addendum_history_refs",
		"modified",
		"modified_by",
	}
)

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2ContractHandoffReference(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_contract_handoff_code()
		self._normalize_refs_json()
		if self.contract_handoff_payload is None:
			self.contract_handoff_payload = {}
		if not self.created_at:
			self.created_at = now_datetime()
		if not cstr(self.created_by).strip():
			self.created_by = "SYSTEM"
		if not cstr(self.currency).strip() and self.tm2_tender:
			self.currency = frappe.db.get_value("TM2 Tender", self.tm2_tender, "currency") or "KES"

	def validate(self) -> None:
		self._sync_identity()
		self._validate_enums()
		self._validate_contract_handoff_code_shape()
		self._validate_duplicate_contract_handoff_code()
		self._validate_unique_per_tender()
		self._validate_chr_001_award()
		self._validate_chr_002_dcm()
		self._validate_chr_003_works_price()
		self._validate_addendum_history_refs()
		if not self.is_new():
			self._validate_chr_005_mutation_rules()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _normalize_refs_json(self) -> None:
		field = "addendum_history_refs"
		val = self.get(field)
		if val is None:
			return
		if isinstance(val, list):
			self.set(field, {"refs": val})

	def _allocate_contract_handoff_code(self) -> None:
		tc = cstr(self.tender_code).strip()
		if not tc:
			return
		self.contract_handoff_code = f"CHR-{tc}"

	def _validate_enums(self) -> None:
		st = cstr(self.handoff_status).strip()
		if st not in _HANDOFF_STATUS_OPTIONS:
			frappe.throw(_("Invalid handoff status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_contract_handoff_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		expected = f"CHR-{tc}"
		if cstr(self.contract_handoff_code).strip() != expected:
			frappe.throw(
				_("Contract Handoff Code must be {0}").format(frappe.bold(expected)),
				title=_("Invalid Contract Handoff Code"),
			)

	def _validate_duplicate_contract_handoff_code(self) -> None:
		code = cstr(self.contract_handoff_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Contract Handoff Reference` where contract_handoff_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Contract Handoff Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Contract Handoff Code"),
			)

	def _validate_unique_per_tender(self) -> None:
		if not self.tm2_tender:
			return
		existing = frappe.db.exists("TM2 Contract Handoff Reference", {"tm2_tender": self.tm2_tender})
		if existing and existing != self.name:
			frappe.throw(
				_("Only one contract handoff reference is allowed per tender."),
				title=_("Duplicate Contract Handoff"),
			)

	def _validate_chr_001_award(self) -> None:
		if getattr(self.flags, "ignore_tm2_chr_award_gate", False):
			return
		if not cstr(self.award_decision_code).strip():
			frappe.throw(
				_("Award decision code is required (TM2-CHR-001)."),
				title=_("Missing Award Reference"),
			)

	def _validate_chr_002_dcm(self) -> None:
		if getattr(self.flags, "ignore_tm2_chr_dcm_gate", False):
			return
		if not cstr(self.dcm_output_code).strip():
			frappe.throw(
				_("DCM Output Code is required (TM2-CHR-002)."),
				title=_("Missing DCM Reference"),
			)
		if not cstr(self.tender_std_instance_code).strip():
			frappe.throw(
				_("Tender STD Instance Code is required."),
				title=_("Missing STD Instance Reference"),
			)

	def _tender_procurement_category(self) -> str | None:
		if not self.tm2_tender:
			return None
		return frappe.db.get_value("TM2 Tender", self.tm2_tender, "procurement_category")

	def _validate_chr_003_works_price(self) -> None:
		if getattr(self.flags, "ignore_tm2_chr_works_price_gate", False):
			return
		if self._tender_procurement_category() != "Works":
			return
		if flt(self.final_evaluated_price) <= 0:
			frappe.throw(
				_("Final evaluated price is required for Works tenders (TM2-CHR-003)."),
				title=_("Missing Corrected Evaluated Price"),
			)
		if not cstr(self.final_boq_reference).strip():
			frappe.throw(
				_("Final BOQ reference is required for Works tenders (TM2-CHR-003)."),
				title=_("Missing Final BOQ Reference"),
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

	def _validate_addendum_history_refs(self) -> None:
		if getattr(self.flags, "ignore_tm2_chr_refs_guard", False):
			return
		if self.addendum_history_refs is None:
			return
		self._validate_refs_object(
			self.addendum_history_refs, label=_("Addendum history refs"), require_refs_key=False
		)

	def _validate_chr_005_mutation_rules(self) -> None:
		if getattr(self.flags, "ignore_tm2_chr_post_accept_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		post_accept = bool(prev.accepted_by_contract_module_at)
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
					"Contract handoff reference cannot be changed after acceptance by the Contract module "
					"(TM2-CHR-005)."
				),
				title=_("Immutable Contract Handoff"),
			)
