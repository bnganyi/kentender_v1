# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-05 — TM2 Publication Record (immutable publication evidence; doc 9 §5.2.5, doc 3 §10).

**TM2-PUB-001** — no updates after insert except **superseded_by_publication** on a prior row
(``flags.allow_tm2_publication_record_supersede``), mirroring readiness supersede.

**TM2-PUB-003** — ``published_at`` / ``published_by`` default from server session on insert.

**TM2-PUB-004** — tender must be **Approved for Publication** unless
``flags.ignore_tm2_publication_tender_status_gate`` (tests / controlled backfill).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_management.immutability_guards import (
	DEFAULT_IMMUTABLE_SKIP,
	raise_immutable_or_supersede_pointer,
)

_APPROVED_FOR_PUBLICATION = "Approved for Publication"

_PUBLICATION_STATUS_OPTIONS: frozenset[str] = frozenset(
	{"Pending", "Published", "Failed", "Superseded", "Withdrawn"}
)


class TM2PublicationRecord(Document):
	def before_insert(self) -> None:
		self._sync_identity_fields()
		self._allocate_publication_code()
		if self.publication_payload_snapshot is None:
			self.publication_payload_snapshot = {}
		if not self.published_at:
			self.published_at = now_datetime()
		if not self.published_by:
			self.published_by = frappe.session.user

	def validate(self) -> None:
		self._sync_identity_fields()
		self._validate_status_enum()
		self._validate_readiness_binding_lineage()
		self._validate_tender_approved_for_publication()
		self._validate_publication_code_shape()
		self._validate_duplicate_publication_code()
		if not self.is_new():
			self._validate_immutable_or_supersede_only()

	def after_insert(self) -> None:
		self._link_supersede_on_previous_publication()

	def _sync_identity_fields(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.tm2_tender_std_binding:
			bind_tender, bc = frappe.db.get_value(
				"TM2 Tender STD Binding",
				self.tm2_tender_std_binding,
				("tm2_tender", "binding_code"),
			) or (None, None)
			if bind_tender and self.tm2_tender and bind_tender != self.tm2_tender:
				frappe.throw(
					_("TM2 Tender STD Binding belongs to a different tender."),
					title=_("Invalid Binding"),
				)
			self.binding_code = cstr(bc).strip() or self.binding_code
		if self.tm2_publication_readiness:
			rd_tender, rd_binding, rc = frappe.db.get_value(
				"TM2 Publication Readiness",
				self.tm2_publication_readiness,
				("tm2_tender", "tm2_tender_std_binding", "readiness_code"),
			) or (None, None, None)
			if rd_tender and self.tm2_tender and rd_tender != self.tm2_tender:
				frappe.throw(
					_("TM2 Publication Readiness belongs to a different tender."),
					title=_("Invalid Readiness"),
				)
			if rd_binding and self.tm2_tender_std_binding and rd_binding != self.tm2_tender_std_binding:
				frappe.throw(
					_("Readiness record must match the same STD binding as this publication."),
					title=_("Invalid Readiness"),
				)
			self.readiness_code = cstr(rc).strip() or self.readiness_code

	def _allocate_publication_code(self) -> None:
		if not self.tm2_tender:
			return
		tc = cstr(self.tender_code).strip() or (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		)
		prefix = f"PUB-{tc}-"
		rows = frappe.db.sql(
			"select publication_code from `tabTM2 Publication Record` where tm2_tender = %s",
			(self.tm2_tender,),
		)
		max_n = 0
		for (pc,) in rows or []:
			if not pc or not str(pc).startswith(prefix):
				continue
			suffix = str(pc)[len(prefix) :]
			if suffix.isdigit():
				max_n = max(max_n, int(suffix))
		self.publication_code = f"{prefix}{max_n + 1:03d}"

	def _validate_status_enum(self) -> None:
		st = cstr(self.status).strip()
		if st not in _PUBLICATION_STATUS_OPTIONS:
			frappe.throw(_("Invalid publication status: {0}").format(frappe.bold(st or _("(empty)"))))

	def _validate_readiness_binding_lineage(self) -> None:
		if not (self.tm2_tender and self.tm2_tender_std_binding and self.tm2_publication_readiness):
			return
		bt = frappe.db.get_value("TM2 Tender STD Binding", self.tm2_tender_std_binding, "tm2_tender")
		if bt != self.tm2_tender:
			frappe.throw(_("Binding must belong to the selected TM2 Tender."), title=_("Invalid Lineage"))
		rt = frappe.db.get_value("TM2 Publication Readiness", self.tm2_publication_readiness, "tm2_tender")
		if rt != self.tm2_tender:
			frappe.throw(_("Readiness must belong to the selected TM2 Tender."), title=_("Invalid Lineage"))

	def _validate_tender_approved_for_publication(self) -> None:
		if not self.is_new() or not self.tm2_tender:
			return
		if getattr(self.flags, "ignore_tm2_publication_tender_status_gate", False):
			return
		status = frappe.db.get_value("TM2 Tender", self.tm2_tender, "status")
		if status != _APPROVED_FOR_PUBLICATION:
			frappe.throw(
				_(
					"Tender must be Approved for Publication before creating a publication record "
					"(TM2-PUB-004). Current status: {0}"
				).format(frappe.bold(status or _("(empty)"))),
				title=_("Publication Not Allowed"),
			)

	def _validate_publication_code_shape(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		pc = cstr(self.publication_code).strip()
		expected_prefix = f"PUB-{tc}-"
		if not pc.startswith(expected_prefix):
			frappe.throw(
				_("Publication Code must start with {0}").format(frappe.bold(expected_prefix)),
				title=_("Invalid Publication Code"),
			)
		suffix = pc[len(expected_prefix) :]
		if not suffix.isdigit():
			frappe.throw(_("Publication Code suffix must be numeric."), title=_("Invalid Publication Code"))

	def _validate_duplicate_publication_code(self) -> None:
		pc = cstr(self.publication_code).strip()
		if not pc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Publication Record` where publication_code = %s",
			(pc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Publication Code {0} already exists.").format(frappe.bold(pc)),
				title=_("Duplicate Publication Code"),
			)

	def _validate_immutable_or_supersede_only(self) -> None:
		raise_immutable_or_supersede_pointer(
			self,
			pointer_field="superseded_by_publication",
			allow_supersede_flag="allow_tm2_publication_record_supersede",
			message=_("TM2 Publication Record cannot be changed after creation (TM2-PUB-001)."),
			title=_("Immutable Record"),
			skip_fieldnames=DEFAULT_IMMUTABLE_SKIP,
		)

	def _link_supersede_on_previous_publication(self) -> None:
		pc = cstr(self.publication_code).strip()
		tc = cstr(self.tender_code).strip()
		prefix = f"PUB-{tc}-"
		if not pc.startswith(prefix):
			return
		try:
			seq = int(pc[len(prefix) :])
		except ValueError:
			return
		if seq <= 1:
			return
		prev_code = f"{prefix}{seq - 1:03d}"
		prev_name = frappe.db.get_value("TM2 Publication Record", {"publication_code": prev_code}, "name")
		if not prev_name or prev_name == self.name:
			return
		prev_doc = frappe.get_doc("TM2 Publication Record", prev_name)
		prev_doc.flags.allow_tm2_publication_record_supersede = True
		prev_doc.superseded_by_publication = self.name
		prev_doc.save(ignore_permissions=True)
