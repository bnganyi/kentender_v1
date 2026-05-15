# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared chain for **P5-03** / **P5-04**: published TM2 tender + Draft addendum helpers.

This mixin is **not** a ``unittest`` discoverable type (name does not start with ``Test``),
so importing it from **P5-04** does not re-register **P5-03** test methods.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.approve_tender_publication import (
	approve_tender_publication,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService


class _P5PublishedTenderChainMixin:
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def setUp(self) -> None:
		super().setUp()
		self._p503_suppliers_created: list[str] = []

	def _ensure_std_bindable(self) -> None:
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def _seed_std_output_refs(self, tender_code: str) -> str:
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tender_code": tender_code},
			"tender_std_instance",
		)
		self.assertTrue(si)
		tc = tender_code
		frappe.db.set_value(
			"Tender STD Instance",
			si,
			{
				"current_bundle_output_code": f"GB-{tc}-STUB",
				"current_dsm_output_code": f"DSM-{tc}-STUB",
				"current_dom_output_code": f"DOM-{tc}-STUB",
				"current_dem_output_code": f"DEM-{tc}-STUB",
				"current_dcm_output_code": f"DCM-{tc}-STUB",
			},
			update_modified=False,
		)
		return str(si)

	def _mk_approved_for_publication(self, *, seed_outputs: bool = True) -> str:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_b = spec_for_action("TND2_BIND_STD")
		spec_r = spec_for_action("TND2_RUN_READINESS")
		spec_sub = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		spec_ap = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_c and spec_b and spec_r and spec_sub and spec_ap
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "")
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		bout = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(bout.get("ok"), bout)
		fake = {
			"ok": True,
			"status": "Ready",
			"blockers": [],
			"warnings": [],
			"instance": "STDINST-FAKE",
			"bundle_current": True,
			"dsm_current": True,
			"dom_current": True,
			"dem_current": True,
			"dcm_current": True,
		}
		with patch(
			"kentender_procurement.tender_management.services.run_publication_readiness.validate_tender_std_readiness",
			return_value=fake,
		):
			rout = run_publication_readiness(
				"Administrator",
				tcode,
				context={"granted_permissions": [spec_r.required_permission]},
			)
		self.assertTrue(rout.get("ok"), rout)
		sout = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_sub.required_permission]},
		)
		self.assertTrue(sout.get("ok"), sout)
		aout = approve_tender_publication(
			"Administrator",
			tcode,
			context={
				"granted_permissions": [spec_ap.required_permission],
				"sod_delegated_override_reason": "P5 addendum fixture — delegated approval for publish chain.",
			},
		)
		self.assertTrue(aout.get("ok"), aout)
		if seed_outputs:
			self._seed_std_output_refs(tcode)
		return tcode

	def _supplier_group(self) -> str:
		sg = frappe.db.get_value(
			"Supplier Group",
			{"is_group": 0},
			"name",
			order_by="lft asc",
		)
		if not sg:
			sg = frappe.db.get_value("Supplier Group", {}, "name")
		if not sg:
			frappe.throw("No Supplier Group for P5 addendum fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P503 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": "Supplier",
				"naming_series": "SUP-.YYYY.-",
				"supplier_name": supplier_name,
				"supplier_type": "Company",
				"supplier_group": self._supplier_group(),
			}
		).insert(ignore_permissions=True)
		self._p503_suppliers_created.append(doc.name)
		return doc.name

	def _cleanup_p503(self, tm2_name: str | None) -> None:
		frappe.set_user("Administrator")
		if not tm2_name or not frappe.db.exists("TM2 Tender", tm2_name):
			return
		for row in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2_name}, pluck="name"):
			for air in frappe.get_all(
				"TM2 Addendum Impact Record",
				filters={"tm2_addendum": row},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Impact Record", air):
					frappe.delete_doc(
						"TM2 Addendum Impact Record",
						air,
						force=True,
						ignore_permissions=True,
					)
			for ack in frappe.get_all(
				"TM2 Addendum Acknowledgement",
				filters={"tm2_addendum": row},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Acknowledgement", ack):
					frappe.delete_doc(
						"TM2 Addendum Acknowledgement",
						ack,
						force=True,
						ignore_permissions=True,
					)
			if frappe.db.exists("TM2 Addendum", row):
				frappe.delete_doc("TM2 Addendum", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Clarification Request",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Clarification Request", row):
				frappe.delete_doc("TM2 Clarification Request", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		self._cleanup_tm2(tm2_name)
		for sn in list(self._p503_suppliers_created):
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		self._p503_suppliers_created.clear()

	def _ensure_open_clarification_window(self, tm2_name: str) -> None:
		deadline = add_to_date(now_datetime(), days=7)
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
		if tl_name:
			frappe.db.set_value(
				"TM2 Tender Timeline",
				tl_name,
				{"clarification_deadline_at": deadline},
				update_modified=False,
			)
			return
		base = now_datetime()
		frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2_name,
				"planned_publication_at": add_to_date(base, hours=-2),
				"clarification_deadline_at": deadline,
				"addendum_cutoff_at": add_to_date(base, days=8),
				"submission_deadline_at": add_to_date(base, days=14),
				"opening_scheduled_at": add_to_date(base, days=14),
				"tender_validity_days": 90,
				"timezone": "Africa/Nairobi",
			}
		).insert(ignore_permissions=True)

	def _published_tender(self) -> tuple[str, str]:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		pub = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertTrue(pub.get("ok"), pub)
		tm2 = str(pub.get("tm2_tender") or "")
		self.assertTrue(tm2)
		self.addCleanup(self._cleanup_p503, tm2)
		return tcode, tm2

	def _add_ctx(self) -> dict:
		spec = spec_for_action("ADD2_CREATE")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _base_payload(self) -> dict:
		return {
			"title": "Addendum No. 1 — BOQ Quantity Revision",
			"reason": "Correction of BOQ quantities following technical review.",
			"primary_impact_type": "BOQ Change",
		}
