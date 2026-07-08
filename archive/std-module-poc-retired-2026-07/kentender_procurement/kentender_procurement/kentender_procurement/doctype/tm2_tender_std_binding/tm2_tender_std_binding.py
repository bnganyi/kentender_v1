# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-02 — TM2 Tender STD Binding (tender-side STD anti-drift record).

Doc 9 §5.2.2; doc 3 §7; binding_status vocabulary doc 3 §7.2.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, now_datetime

from kentender_procurement.tender_management.constants.tm2_std_readiness import STD_READINESS_STATUSES


BINDING_STATUS_OPTIONS: tuple[str, ...] = (
	"Draft",
	"Active",
	"Published",
	"Superseded",
	"Cancelled",
)

# Fields that may not change once binding_status is Published (TM2-TSB-003).
_PUBLISHED_FROZEN_FIELDS: frozenset[str] = frozenset(
	{
		"tm2_tender",
		"tender_code",
		"binding_code",
		"std_template",
		"std_template_code",
		"std_template_version_code",
		"std_applicability_profile_code",
		"tender_std_instance",
		"tender_std_instance_code",
		"bundle_output_code",
		"dsm_output_code",
		"dom_output_code",
		"dem_output_code",
		"dcm_output_code",
		"publication_snapshot_code",
		"published_snapshot_hash",
		"binding_status",
		"readiness_status",
		"is_active",
		"superseded_by_binding",
	}
)


def _next_binding_sequence(tm2_tender_name: str) -> int:
	tc = frappe.db.get_value("TM2 Tender", tm2_tender_name, "tender_code") or tm2_tender_name
	prefix = f"TSB-{tc}-"
	rows = frappe.db.sql(
		"""
		select binding_code from `tabTM2 Tender STD Binding`
		where tm2_tender = %s and binding_code like %s
		""",
		(tm2_tender_name, f"{prefix}%"),
	)
	max_n = 0
	for (bc,) in rows or []:
		if not bc or not bc.startswith(prefix):
			continue
		suffix = bc[len(prefix) :]
		if suffix.isdigit():
			max_n = max(max_n, int(suffix))
	return max_n + 1


def _allocate_binding_code(tm2_tender_name: str) -> str:
	tc = frappe.db.get_value("TM2 Tender", tm2_tender_name, "tender_code") or tm2_tender_name
	seq = _next_binding_sequence(tm2_tender_name)
	return f"TSB-{tc}-{seq:03d}"


class TM2TenderSTDBinding(Document):
	def before_insert(self) -> None:
		if not cstr(self.binding_code).strip():
			self.binding_code = _allocate_binding_code(self.tm2_tender)
		if not self.bound_by:
			self.bound_by = frappe.session.user
		if not self.bound_at:
			self.bound_at = now_datetime()

	def validate(self) -> None:
		self._validate_status_enums()
		self._validate_duplicate_binding_code()
		self._sync_identity_and_snapshots()
		self._validate_tender_std_instance_parent()
		self._validate_single_active_binding()
		self._validate_published_immutable()

	def on_update(self) -> None:
		self._sync_parent_tm2_tender_header()

	def after_insert(self) -> None:
		self._sync_parent_tm2_tender_header()

	def on_trash(self) -> None:
		self._sync_parent_tm2_tender_header()

	def _validate_status_enums(self) -> None:
		bs = cstr(self.binding_status).strip()
		if bs not in BINDING_STATUS_OPTIONS:
			frappe.throw(_("Invalid binding status: {0}").format(frappe.bold(bs or _("(empty)"))))
		rs = cstr(self.readiness_status).strip()
		if rs not in STD_READINESS_STATUSES:
			frappe.throw(_("Invalid readiness status: {0}").format(frappe.bold(rs or _("(empty)"))))

	def _validate_duplicate_binding_code(self) -> None:
		bc = cstr(self.binding_code).strip()
		if not bc:
			return
		if self.is_new():
			cnt = frappe.db.sql(
				"select count(*) from `tabTM2 Tender STD Binding` where binding_code = %s",
				(bc,),
			)[0][0]
			if cnt:
				frappe.throw(
					_("Binding Code {0} already exists.").format(frappe.bold(bc)),
					title=_("Duplicate Binding Code"),
				)

	def _sync_identity_and_snapshots(self) -> None:
		if self.tm2_tender:
			self.tender_code = frappe.db.get_value("TM2 Tender", self.tm2_tender, "tender_code") or self.tm2_tender
		if self.std_template:
			code = frappe.db.get_value("STD Template", self.std_template, "template_code")
			if code:
				self.std_template_code = code
		if self.tender_std_instance:
			self.tender_std_instance_code = self.tender_std_instance

	def _validate_tender_std_instance_parent(self) -> None:
		if not self.tender_std_instance:
			return
		row = frappe.db.get_value(
			"Tender STD Instance",
			self.tender_std_instance,
			["tm2_tender", "procurement_tender"],
			as_dict=True,
		)
		if not row:
			frappe.throw(_("Tender STD Instance {0} not found.").format(self.tender_std_instance))
		if row.tm2_tender:
			if row.tm2_tender != self.tm2_tender:
				frappe.throw(
					_("Tender STD Instance {0} is linked to a different TM2 Tender.").format(
						self.tender_std_instance
					),
					title=_("STD Instance Mismatch"),
				)
		else:
			frappe.throw(
				_("Tender STD Instance {0} has no tender parent.").format(self.tender_std_instance),
				title=_("STD Instance Mismatch"),
			)

	def _validate_single_active_binding(self) -> None:
		if not self.tm2_tender or not cint(self.is_active):
			return
		others = frappe.get_all(
			"TM2 Tender STD Binding",
			filters={
				"tm2_tender": self.tm2_tender,
				"is_active": 1,
				"name": ["!=", self.name],
			},
			pluck="name",
		)
		if others:
			frappe.throw(
				_("Another active TM2 Tender STD Binding exists for this tender: {0}").format(
					", ".join(others)
				),
				title=_("Duplicate Active Binding"),
			)

	def _validate_published_immutable(self) -> None:
		prev = self.get_doc_before_save()
		if not prev or cstr(prev.binding_status).strip() != "Published":
			return
		resync = getattr(self.flags, "allow_tm2_tsb_published_output_resync", False)
		_allowed_on_resync: frozenset[str] = frozenset(
			{
				"bundle_output_code",
				"dsm_output_code",
				"dom_output_code",
				"dem_output_code",
				"dcm_output_code",
				"publication_snapshot_code",
				"published_snapshot_hash",
			}
		)
		for fn in _PUBLISHED_FROZEN_FIELDS:
			if self.get(fn) == prev.get(fn):
				continue
			if resync and fn in _allowed_on_resync:
				continue
			frappe.throw(
				_("Published Tender STD Binding cannot be changed ({0}).").format(fn),
				title=_("Published Binding Locked"),
			)

	def _sync_parent_tm2_tender_header(self) -> None:
		if not self.tm2_tender:
			return
		active = frappe.get_all(
			"TM2 Tender STD Binding",
			filters={
				"tm2_tender": self.tm2_tender,
				"is_active": 1,
				"binding_status": ["not in", ["Cancelled", "Superseded"]],
			},
			fields=["readiness_status"],
			order_by="modified desc",
			limit=1,
		)
		if active:
			frappe.db.set_value(
				"TM2 Tender",
				self.tm2_tender,
				{
					"std_bound": 1,
					"std_readiness_status": active[0].readiness_status,
				},
				update_modified=False,
			)
		else:
			frappe.db.set_value(
				"TM2 Tender",
				self.tm2_tender,
				{
					"std_bound": 0,
					"std_readiness_status": "Not Assessed",
				},
				update_modified=False,
			)
