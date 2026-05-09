# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender ↔ STD Instance binding — ``TenderStdBindingService`` (create, validate, supersession).

STDINST-0110. Denies orphan instance creation via DocType rules; requires eligible Active STD Template.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.services.std_template_governance_usage import (
	USAGE_TYPE_INSTANCE,
	check_std_template_tender_creation_eligibility,
	record_std_template_usage,
)

from kentender_procurement.tender_management.std_instance.instance import (
	INSTANCE_STATUS_RELEASES_SLOT,
)
from kentender_procurement.tender_management.std_instance.authorization import (
	StdAuthorizationService,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_CREATED,
)
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TenderStdBindingService:
	"""Bind ``Procurement Tender`` to ``Tender STD Instance`` (pack §6)."""

	@staticmethod
	def get_current_std_instance_for_tender(procurement_tender: str) -> Document | None:
		"""Return the active STD Instance for this tender, or ``None``."""
		if not procurement_tender:
			return None
		names = frappe.get_all(
			"Tender STD Instance",
			filters={
				"procurement_tender": procurement_tender,
				"instance_status": ["not in", list(INSTANCE_STATUS_RELEASES_SLOT)],
			},
			pluck="name",
			limit=2,
		)
		if len(names) > 1:
			frappe.throw(
				_("Multiple active Tender STD Instance rows for tender {0}: {1}").format(
					procurement_tender,
					", ".join(names),
				),
				title=_("STD Instance Data Integrity"),
			)
		if not names:
			return None
		return frappe.get_doc("Tender STD Instance", names[0])

	@staticmethod
	def validate_tender_std_binding(procurement_tender: str) -> dict[str, Any]:
		"""Return eligibility and current-instance snapshot (throws if tender doc missing)."""
		if not frappe.db.exists("Procurement Tender", procurement_tender):
			frappe.throw(
				_("Procurement Tender {0} does not exist.").format(procurement_tender),
				frappe.DoesNotExistError,
			)
		tender = frappe.get_doc("Procurement Tender", procurement_tender)
		std_template = (tender.get("std_template") or "").strip()
		if not std_template:
			return {
				"ok": False,
				"eligible": False,
				"reasons": ["missing_std_template"],
				"warnings": [],
				"current_std_instance": None,
				"procurement_tender": procurement_tender,
				"std_template": None,
			}

		ctx = TenderStdBindingService._eligibility_context(tender)
		elig = check_std_template_tender_creation_eligibility(std_template, ctx)
		current = TenderStdBindingService.get_current_std_instance_for_tender(procurement_tender)
		eligible = bool(elig.get("eligible"))
		out = {
			"ok": eligible,
			"eligible": eligible,
			"reasons": list(elig.get("reasons") or []),
			"warnings": list(elig.get("warnings") or []),
			"current_std_instance": current.name if current else None,
			"procurement_tender": procurement_tender,
			"std_template": std_template,
		}
		return out

	@staticmethod
	def _eligibility_context(tender: Document) -> dict[str, Any]:
		ctx: dict[str, Any] = {
			"emit_usage_blocked_event": False,
		}
		pc = (tender.get("procurement_category") or "").strip()
		if pc:
			ctx["procurement_category"] = pc
		tf = (tender.get("template_family") or "").strip()
		if tf:
			ctx["template_family"] = tf
		st = (tender.get("std_template") or "").strip()
		if st:
			ctx["template_code"] = st
		return ctx

	@staticmethod
	def _codes_from_std_template(std_template_name: str) -> tuple[str, str]:
		st = frappe.get_doc("STD Template", std_template_name)
		version = (st.get("template_version") or st.get("version_label") or "").strip()
		profile = (st.get("procurement_method_profile") or "").strip()
		if not profile:
			profile = (st.get("active_profile_key") or "").strip()
		if not profile:
			profile = (st.get("template_family") or "").strip()
		if not profile:
			profile = "DEFAULT"
		if not version:
			frappe.throw(
				_("STD Template {0} has no template_version / version_label.").format(std_template_name),
				title=_("STD Template Version Missing"),
			)
		return version, profile

	@staticmethod
	def create_std_instance_for_tender(
		procurement_tender: str,
		*,
		ignore_permissions: bool = False,
		record_template_usage: bool = True,
	) -> Document:
		"""Create a ``Tender STD Instance`` from an existing ``Procurement Tender``."""
		StdAuthorizationService.assert_can_create_instance(procurement_tender)
		if not frappe.db.exists("Procurement Tender", procurement_tender):
			frappe.throw(
				_("Procurement Tender {0} does not exist.").format(procurement_tender),
				frappe.DoesNotExistError,
			)
		tender = frappe.get_doc("Procurement Tender", procurement_tender)
		std_template = (tender.get("std_template") or "").strip()
		if not std_template:
			frappe.throw(_("Procurement Tender has no STD Template."), title=_("STD Template Required"))

		ctx = TenderStdBindingService._eligibility_context(tender)
		elig = check_std_template_tender_creation_eligibility(std_template, ctx)
		if not elig.get("eligible"):
			reasons = ", ".join(elig.get("reasons") or [])
			frappe.throw(
				_("STD Template is not eligible for tender instance creation: {0}").format(reasons),
				title=_("STD Template Not Eligible"),
			)

		if TenderStdBindingService.get_current_std_instance_for_tender(procurement_tender):
			frappe.throw(
				_("An active Tender STD Instance already exists for this procurement tender."),
				title=_("Duplicate STD Instance"),
			)

		version_code, profile_code = TenderStdBindingService._codes_from_std_template(std_template)

		pc = (tender.get("procurement_category") or "").strip()
		if not pc:
			pc = (frappe.db.get_value("STD Template", std_template, "procurement_category") or "").strip()
		if not pc:
			pc = "WORKS"
		pm = (tender.get("procurement_method") or "").strip()
		if not pm:
			pm = "OPEN_COMPETITIVE_TENDERING"

		si = frappe.new_doc("Tender STD Instance")
		si.procurement_tender = procurement_tender
		pp = (tender.get("procurement_package") or "").strip()
		if pp:
			si.procurement_package = pp
		si.template_version_code = version_code
		si.applicability_profile_code = profile_code
		si.procurement_category = pc
		si.procurement_method = pm
		si.instance_status = "Draft"
		si.readiness_status = "Not Ready"
		si.created_from_tender_context = 1
		try:
			si.insert(ignore_permissions=ignore_permissions)
		except frappe.DuplicateEntryError:
			frappe.throw(
				_(
					"Another active Tender STD Instance already exists for this procurement tender."
				),
				title=_("Duplicate STD Instance"),
			)

		if record_template_usage:
			record_std_template_usage(
				std_template,
				USAGE_TYPE_INSTANCE,
				tender=procurement_tender,
				tender_std_instance=si.name,
				procurement_package=pp or None,
			)

		emit_std_instance_event(
			EVT_STDINST_CREATED,
			instance_code=si.name,
			details={
				"procurement_tender": procurement_tender,
				"std_template": std_template,
				"template_version_code": version_code,
				"applicability_profile_code": profile_code,
			},
		)
		return si

	@staticmethod
	def replace_std_instance_through_supersession(
		procurement_tender: str,
		*,
		ignore_permissions: bool = False,
		record_template_usage: bool = True,
	) -> Document:
		"""Mark current instance Superseded, create a new instance, link superseded_by on the old row."""
		current = TenderStdBindingService.get_current_std_instance_for_tender(procurement_tender)
		if not current:
			frappe.throw(
				_("No active Tender STD Instance to supersede for tender {0}.").format(procurement_tender),
				title=_("Supersession Not Possible"),
			)
		old_name = current.name
		StdInstanceStateService.apply_transition(
			old_name,
			"Superseded",
			ignore_permissions=ignore_permissions,
		)

		new_si = TenderStdBindingService.create_std_instance_for_tender(
			procurement_tender,
			ignore_permissions=ignore_permissions,
			record_template_usage=record_template_usage,
		)

		frappe.db.set_value(
			"Tender STD Instance",
			old_name,
			"superseded_by_instance_code",
			new_si.name,
			update_modified=False,
		)
		return new_si
