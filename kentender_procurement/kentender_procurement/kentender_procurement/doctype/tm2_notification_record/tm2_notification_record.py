# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-23 — TM2 Notification Record (doc 9 §5.1, doc 3 §28).

Business code **NTF-{tender_code}-{####}** — four-digit sequence **per TM2 Tender**.

**TM2-NTF-001** — this record is **notification evidence** only; it does not replace publication or audit
records (product scope; enforced by workflows, not by deleting other DocTypes).

**TM2-NTF-002** — addendum-driven supplier notifications are an orchestration concern; the DocType holds
the persisted row once created.

**TM2-NTF-003** — ``payload_snapshot`` must not carry confidential evaluation-style payloads when
``recipient_type`` is **Public** unless ``flags.ignore_tm2_ntf_payload_confidentiality``. A structured
marker key ``confidential_evaluation_payload`` is rejected for Public recipients (minimal guardrail for
tests and CI).

**Immutability** — once ``sent_at`` is set, core addressing and payload fields are locked; only
``delivery_status``, ``failure_reason``, ``modified``, and ``modified_by`` may change unless
``flags.ignore_tm2_ntf_post_send_immutable``.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

_CONFIDENTIAL_PAYLOAD_MARKERS: frozenset[str] = frozenset({"confidential_evaluation_payload"})

_NOTIFICATION_TYPE_OPTIONS: frozenset[str] = frozenset(
	{
		"Publication",
		"Invitation",
		"Addendum",
		"Clarification",
		"Closing",
		"Opening",
		"Evaluation",
		"Contract",
		"General",
	}
)

_RECIPIENT_TYPE_OPTIONS: frozenset[str] = frozenset({"Supplier", "Internal", "Public", "System"})

_CHANNEL_OPTIONS: frozenset[str] = frozenset({"Email", "Portal", "SMS", "In App", "Other"})

_DELIVERY_STATUS_OPTIONS: frozenset[str] = frozenset(
	{"Pending", "Queued", "Sent", "Delivered", "Failed", "Skipped"}
)

_POST_SEND_MUTABLE: frozenset[str] = frozenset(
	{
		"delivery_status",
		"failure_reason",
		"modified",
		"modified_by",
	}
)

_SKIP_COMPARE: frozenset[str] = frozenset({"name", "owner", "creation", "docstatus", "idx"})


class TM2NotificationRecord(Document):
	def before_insert(self) -> None:
		self._sync_identity()
		self._allocate_notification_code()
		if self.payload_snapshot is None:
			self.payload_snapshot = {}

	def validate(self) -> None:
		self._sync_identity()
		self._validate_enums()
		self._validate_notification_code_shape()
		self._validate_duplicate_notification_code()
		self._validate_ntf_003_payload_confidentiality()
		if not self.is_new():
			self._validate_post_send_immutable()

	def _sync_identity(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender

	def _allocate_notification_code(self) -> None:
		if not self.tm2_tender:
			return
		tc = cstr(self.tender_code).strip() or (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		)
		prefix = f"NTF-{tc}-"
		rows = frappe.db.sql(
			"select notification_code from `tabTM2 Notification Record` where tm2_tender = %s",
			(self.tm2_tender,),
		)
		max_n = 0
		for (nc,) in rows or []:
			if not nc or not str(nc).startswith(prefix):
				continue
			suffix = str(nc)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.notification_code = f"{prefix}{max_n + 1:04d}"

	def _validate_enums(self) -> None:
		nt = cstr(self.notification_type).strip()
		if nt not in _NOTIFICATION_TYPE_OPTIONS:
			frappe.throw(_("Invalid notification type: {0}").format(frappe.bold(nt or _("(empty)"))))
		rt = cstr(self.recipient_type).strip()
		if rt not in _RECIPIENT_TYPE_OPTIONS:
			frappe.throw(_("Invalid recipient type: {0}").format(frappe.bold(rt or _("(empty)"))))
		ch = cstr(self.channel).strip()
		if ch not in _CHANNEL_OPTIONS:
			frappe.throw(_("Invalid channel: {0}").format(frappe.bold(ch or _("(empty)"))))
		ds = cstr(self.delivery_status).strip()
		if ds not in _DELIVERY_STATUS_OPTIONS:
			frappe.throw(_("Invalid delivery status: {0}").format(frappe.bold(ds or _("(empty)"))))

	def _validate_notification_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		nc = cstr(self.notification_code).strip()
		prefix = f"NTF-{tc}-"
		if not nc.startswith(prefix):
			frappe.throw(
				_("Notification Code must start with {0}").format(frappe.bold(prefix)),
				title=_("Invalid Notification Code"),
			)
		suffix = nc[len(prefix) :]
		if len(suffix) != 4 or not suffix.isdigit():
			frappe.throw(
				_("Notification Code suffix must be exactly four digits."),
				title=_("Invalid Notification Code"),
			)

	def _validate_duplicate_notification_code(self) -> None:
		code = cstr(self.notification_code).strip()
		if not code or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Notification Record` where notification_code = %s",
			(code,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Notification Code {0} already exists.").format(frappe.bold(code)),
				title=_("Duplicate Notification Code"),
			)

	def _payload_as_dict(self):
		val = self.payload_snapshot
		if isinstance(val, str) and cstr(val).strip():
			try:
				return json.loads(val)
			except json.JSONDecodeError:
				return val
		return val

	def _validate_ntf_003_payload_confidentiality(self) -> None:
		if getattr(self.flags, "ignore_tm2_ntf_payload_confidentiality", False):
			return
		if cstr(self.recipient_type).strip() != "Public":
			return
		payload = self._payload_as_dict()
		if not isinstance(payload, dict):
			return
		for key in _CONFIDENTIAL_PAYLOAD_MARKERS:
			if key in payload and payload.get(key) not in (None, "", False, 0, [], {}):
				frappe.throw(
					_(
						"Public recipient notifications must not include confidential evaluation payload "
						"markers (TM2-NTF-003)."
					),
					title=_("Invalid Payload For Public Recipient"),
				)

	def _validate_post_send_immutable(self) -> None:
		if getattr(self.flags, "ignore_tm2_ntf_post_send_immutable", False):
			return
		prev = self.get_doc_before_save()
		if not prev or not prev.get("sent_at"):
			return
		for df in self.meta.fields:
			fn = df.fieldname
			if fn in _SKIP_COMPARE:
				continue
			if df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
				continue
			if prev.get(fn) == self.get(fn):
				continue
			if fn in _POST_SEND_MUTABLE:
				continue
			frappe.throw(
				_("Notification cannot be changed after it has been sent (sent_at is set)."),
				title=_("Immutable Notification"),
			)
