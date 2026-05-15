# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-24 — TM2 Tender Audit Event (doc 9 §5.1, doc 3 §29).

Business code **TAE-{tender_code}-{####}** — four-digit sequence **per TM2 Tender**.

**TM2-AUD-001** — row is **append-only**: no updates after insert unless
``flags.ignore_tm2_aud_append_only_override``.

**TM2-AUD-002** — material transitions must emit events (orchestration; not enforced on this class alone).

**TM2-AUD-003** — high-risk ``event_type`` values require a non-empty ``reason`` unless
``flags.ignore_tm2_aud_reason_gate``.

**TM2-AUD-004** — **Tender Published** events must carry ``publication_snapshot_code`` inside ``event_payload``
(and top-level ``publication_snapshot_code`` is encouraged) unless ``flags.ignore_tm2_aud_std_payload_gate``.

**TM2-AUD-005** — rows must not be deleted via ordinary application paths; ``on_trash`` blocks unless
``frappe.in_test``, ``flags.ignore_tm2_aud_allow_delete``, or ``frappe.flags.in_migrate``.

**TM2-AUD-006** — denial-class events require ``denial_code`` unless ``flags.ignore_tm2_aud_denial_gate``.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_management.immutability_guards import raise_append_only_on_update

_ACTOR_TYPE_OPTIONS: frozenset[str] = frozenset({"User", "System", "Supplier", "API"})

_HIGH_RISK_EVENT_TYPES: frozenset[str] = frozenset(
	{
		"Tender Cancelled",
		"Administrative Override",
	}
)

_DENIAL_EVENT_TYPES: frozenset[str] = frozenset({"Access Denied", "Late Submission Rejected"})


class TM2TenderAuditEvent(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_audit_event_code()
		if self.event_payload is None:
			self.event_payload = {}
		if not self.occurred_at:
			self.occurred_at = now_datetime()

	def validate(self) -> None:
		self._sync_identity()
		self._validate_actor_type()
		self._validate_actor_user_gate()
		self._validate_audit_event_code_shape()
		self._validate_duplicate_audit_event_code()
		self._validate_aud_003_reason()
		self._validate_aud_004_publication_payload()
		self._validate_aud_006_denial_code()
		self._validate_aud_001_append_only()

	def on_trash(self) -> None:
		if getattr(self.flags, "ignore_tm2_aud_allow_delete", False):
			return
		if frappe.in_test:
			return
		if getattr(frappe.flags, "in_migrate", False):
			return
		frappe.throw(
			_("Tender audit events cannot be deleted (TM2-AUD-005)."),
			title=_("Append-Only Audit Event"),
		)

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _allocate_audit_event_code(self) -> None:
		if not self.tm2_tender:
			return
		tc = cstr(self.tender_code).strip() or (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		)
		prefix = f"TAE-{tc}-"
		rows = frappe.db.sql(
			"select audit_event_code from `tabTM2 Tender Audit Event` where tm2_tender = %s",
			(self.tm2_tender,),
		)
		max_n = 0
		for (ac,) in rows or []:
			if not ac or not str(ac).startswith(prefix):
				continue
			suffix = str(ac)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.audit_event_code = f"{prefix}{max_n + 1:04d}"

	def _validate_actor_type(self) -> None:
		at = cstr(self.actor_type).strip()
		if at not in _ACTOR_TYPE_OPTIONS:
			frappe.throw(_("Invalid actor type: {0}").format(frappe.bold(at or _("(empty)"))))

	def _validate_actor_user_gate(self) -> None:
		if getattr(self.flags, "ignore_tm2_aud_actor_gate", False):
			return
		if cstr(self.actor_type).strip() == "User" and not cstr(self.actor_user).strip():
			frappe.throw(
				_("Actor User is required when actor type is User."),
				title=_("Missing Actor User"),
			)

	def _validate_audit_event_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		ac = cstr(self.audit_event_code).strip()
		prefix = f"TAE-{tc}-"
		if not ac.startswith(prefix):
			frappe.throw(
				_("Audit Event Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Audit Event Code"),
			)
		suffix = ac[len(prefix) :]
		if len(suffix) != 4 or not suffix.isdigit():
			frappe.throw(
				_("Audit Event Code suffix must be exactly four digits."),
				title=_("Invalid Audit Event Code"),
			)

	def _validate_duplicate_audit_event_code(self) -> None:
		code = cstr(self.audit_event_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Tender Audit Event` where audit_event_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Audit Event Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Audit Event Code"),
			)

	def _event_payload_dict(self):
		val = self.event_payload
		if isinstance(val, str) and cstr(val).strip():
			try:
				return json.loads(val)
			except json.JSONDecodeError:
				return val
		return val

	def _validate_aud_003_reason(self) -> None:
		if getattr(self.flags, "ignore_tm2_aud_reason_gate", False):
			return
		et = cstr(self.event_type).strip()
		if et in _HIGH_RISK_EVENT_TYPES and not cstr(self.reason).strip():
			frappe.throw(
				_("Reason is required for this audit event type (TM2-AUD-003)."),
				title=_("Missing Audit Reason"),
			)

	def _validate_aud_004_publication_payload(self) -> None:
		if getattr(self.flags, "ignore_tm2_aud_std_payload_gate", False):
			return
		if cstr(self.event_type).strip() != "Tender Published":
			return
		payload = self._event_payload_dict()
		if not isinstance(payload, dict):
			frappe.throw(
				_("Tender Published audit payload must be a JSON object (TM2-AUD-004)."),
				title=_("Invalid Publication Audit Payload"),
			)
		if not cstr(payload.get("publication_snapshot_code")).strip():
			frappe.throw(
				_("Tender Published audit payload must include publication_snapshot_code (TM2-AUD-004)."),
				title=_("Missing Publication Snapshot In Payload"),
			)

	def _validate_aud_006_denial_code(self) -> None:
		if getattr(self.flags, "ignore_tm2_aud_denial_gate", False):
			return
		et = cstr(self.event_type).strip()
		if et in _DENIAL_EVENT_TYPES and not cstr(self.denial_code).strip():
			frappe.throw(
				_("Denial code is required for this audit event type (TM2-AUD-006)."),
				title=_("Missing Denial Code"),
			)

	def _validate_aud_001_append_only(self) -> None:
		raise_append_only_on_update(
			self,
			message=_("Tender audit events are append-only and cannot be modified (TM2-AUD-001)."),
			title=_("Append-Only Audit Event"),
			ignore_flag="ignore_tm2_aud_append_only_override",
		)
