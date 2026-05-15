# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-04 — TM2 Publication Readiness (immutable validation snapshot; doc 9 §5.2.4, doc 3 §9).

**TM2-PRD-001** — records are immutable after insert except **TM2-PRD-002** supersede pointer
on the *previous* row (``superseded_by_readiness`` only), via controlled save with
``flags.allow_tm2_publication_readiness_supersede``.

**TM2-PRD-004** — ``readiness_status`` **Ready** (or **Ready With Warnings**) on **new**
documents requires ``flags.allow_tm2_readiness_authorized_ready`` (service / governed path).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, now_datetime

from kentender_procurement.tender_management.constants.tm2_std_readiness import STD_READINESS_STATUSES
from kentender_procurement.tender_management.immutability_guards import (
	DEFAULT_IMMUTABLE_SKIP,
	raise_immutable_or_supersede_pointer,
)

_READINESS_STATUS_OPTIONS: frozenset[str] = frozenset({"Blocked", "Ready", "Ready With Warnings"})


class TM2PublicationReadiness(Document):
	def before_insert(self) -> None:
		self._sync_identity_fields()
		self._allocate_run_and_readiness_code()
		if self.validation_payload is None:
			self.validation_payload = {}
		if not self.validated_at:
			self.validated_at = now_datetime()
		if not self.validated_by:
			self.validated_by = frappe.session.user

	def validate(self) -> None:
		self._sync_identity_fields()
		self._validate_enums()
		self._validate_binding_belongs_to_tender()
		self._validate_readiness_code_and_run_number()
		self._validate_duplicate_readiness_code()
		self._validate_prd_004_authorized_ready_on_insert()
		if not self.is_new():
			self._validate_immutable_or_supersede_only()

	def after_insert(self) -> None:
		self._link_supersede_on_previous_run()

	def _sync_identity_fields(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.tm2_tender_std_binding:
			bind_tc, bc = frappe.db.get_value(
				"TM2 Tender STD Binding",
				self.tm2_tender_std_binding,
				("tm2_tender", "binding_code"),
			) or (None, None)
			if bind_tc and self.tm2_tender and bind_tc != self.tm2_tender:
				frappe.throw(
					_("TM2 Tender STD Binding belongs to a different tender."),
					title=_("Invalid Binding"),
				)
			self.binding_code = cstr(bc).strip() or self.binding_code

	def _allocate_run_and_readiness_code(self) -> None:
		if not self.tm2_tender:
			return
		max_prev = frappe.db.sql(
			"select coalesce(max(validation_run_number), 0) from `tabTM2 Publication Readiness` where tm2_tender = %s",
			(self.tm2_tender,),
		)[0][0]
		max_prev = cint(max_prev)
		self.validation_run_number = max_prev + 1
		tc = cstr(self.tender_code).strip() or (
			frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		)
		self.readiness_code = f"TRD-{tc}-{cint(self.validation_run_number):03d}"

	def _validate_enums(self) -> None:
		rs = cstr(self.readiness_status).strip()
		if rs not in _READINESS_STATUS_OPTIONS:
			frappe.throw(_("Invalid readiness status: {0}").format(frappe.bold(rs or _("(empty)"))))
		srs = cstr(self.std_readiness_status).strip()
		if srs not in STD_READINESS_STATUSES:
			frappe.throw(_("Invalid STD readiness status: {0}").format(frappe.bold(srs or _("(empty)"))))

	def _validate_binding_belongs_to_tender(self) -> None:
		if not self.tm2_tender or not self.tm2_tender_std_binding:
			return
		bt = frappe.db.get_value("TM2 Tender STD Binding", self.tm2_tender_std_binding, "tm2_tender")
		if bt != self.tm2_tender:
			frappe.throw(
				_("TM2 Tender STD Binding must reference the same TM2 Tender."),
				title=_("Invalid Binding"),
			)

	def _validate_readiness_code_and_run_number(self) -> None:
		if not self.is_new():
			return
		tc = cstr(self.tender_code).strip()
		rn = cint(self.validation_run_number)
		if rn < 1:
			frappe.throw(_("Validation run number must be at least 1."), title=_("Invalid Run"))
		expected_code = f"TRD-{tc}-{rn:03d}"
		rc = cstr(self.readiness_code).strip()
		if rc != expected_code:
			frappe.throw(
				_("Readiness Code must be {0} for run {1}.").format(frappe.bold(expected_code), rn),
				title=_("Invalid Readiness Code"),
			)
		max_prev = frappe.db.sql(
			"select coalesce(max(validation_run_number), 0) from `tabTM2 Publication Readiness` where tm2_tender = %s",
			(self.tm2_tender,),
		)[0][0]
		max_prev = cint(max_prev)
		if rn != max_prev + 1:
			frappe.throw(
				_("Validation run number must be the next sequential value ({0}).").format(max_prev + 1),
				title=_("Invalid Run Sequence"),
			)

	def _validate_duplicate_readiness_code(self) -> None:
		rc = cstr(self.readiness_code).strip()
		if not rc or not self.is_new():
			return
		cnt = frappe.db.sql(
			"select count(*) from `tabTM2 Publication Readiness` where readiness_code = %s",
			(rc,),
		)[0][0]
		if cnt:
			frappe.throw(
				_("Readiness Code {0} already exists.").format(frappe.bold(rc)),
				title=_("Duplicate Readiness Code"),
			)

	def _validate_prd_004_authorized_ready_on_insert(self) -> None:
		if not self.is_new():
			return
		rs = cstr(self.readiness_status).strip()
		if rs in ("Ready", "Ready With Warnings") and not getattr(
			self.flags, "allow_tm2_readiness_authorized_ready", False
		):
			frappe.throw(
				_(
					"Cannot mark publication readiness as {0} without governed validation "
					"(TM2-PRD-004)."
				).format(rs),
				title=_("Readiness Not Authorized"),
			)

	def _validate_immutable_or_supersede_only(self) -> None:
		raise_immutable_or_supersede_pointer(
			self,
			pointer_field="superseded_by_readiness",
			allow_supersede_flag="allow_tm2_publication_readiness_supersede",
			message=_("TM2 Publication Readiness records cannot be changed after creation (TM2-PRD-001)."),
			title=_("Immutable Record"),
			skip_fieldnames=DEFAULT_IMMUTABLE_SKIP,
		)

	def _link_supersede_on_previous_run(self) -> None:
		rn = cint(self.validation_run_number)
		if rn <= 1:
			return
		prev_name = frappe.db.get_value(
			"TM2 Publication Readiness",
			{"tm2_tender": self.tm2_tender, "validation_run_number": rn - 1},
			"name",
		)
		if not prev_name or prev_name == self.name:
			return
		prev_doc = frappe.get_doc("TM2 Publication Readiness", prev_name)
		prev_doc.flags.allow_tm2_publication_readiness_supersede = True
		prev_doc.superseded_by_readiness = self.name
		prev_doc.save(ignore_permissions=True)
