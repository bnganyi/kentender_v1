# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared P6 TM2 published-tender fixtures (not a ``TestCase``).

Used by ``test_p6_02_*`` through ``test_p6_07_*``, ``test_p7_01_*``, ``test_p7_02_*``, ``test_p7_03_*``, ``test_p7_04_*`` so subclasses do not inherit
each other's ``test_*`` methods.
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
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService


class P6PublishedTm2Fixture:
	"""Mixin: published TM2 + supplier participation (P6-* desk gates)."""

	def _ensure_std_bindable(self) -> None:
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def _seed_published_outputs(self, si: str) -> None:
		for gen in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			doc = gen(si)
			StdInstanceGeneratedOutputService.publish_output(doc.name)

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
		si = str(bout.get("tender_std_instance") or "")
		self.assertTrue(si)
		if seed_outputs:
			self._seed_published_outputs(si)
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
				"sod_delegated_override_reason": "P6 fixture — delegated approval for publish chain.",
			},
		)
		self.assertTrue(aout.get("ok"), aout)
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
			frappe.throw("No Supplier Group for P6 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		prefix = getattr(self, "p6_supplier_fixture_prefix", "P6")
		supplier_name = f"{prefix} {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			# Other tests may leave the row disabled; P6 gates require an active supplier.
			frappe.db.set_value("Supplier", existing, "disabled", 0, update_modified=False)
			return str(existing)
		doc = frappe.get_doc(
			{
				"doctype": "Supplier",
				"naming_series": "SUP-.YYYY.-",
				"supplier_name": supplier_name,
				"supplier_type": "Company",
				"supplier_group": self._supplier_group(),
			}
		).insert(ignore_permissions=True)
		self._p602_suppliers_created.append(doc.name)
		return doc.name

	def _cleanup_p602(self, tm2_name: str | None) -> None:
		frappe.set_user("Administrator")
		if not tm2_name or not frappe.db.exists("TM2 Tender", tm2_name):
			return
		for row in frappe.get_all(
			"TM2 Contract Handoff Reference",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Contract Handoff Reference", row):
				frappe.delete_doc("TM2 Contract Handoff Reference", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Evaluation Handoff Record",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Evaluation Handoff Record", row):
				frappe.delete_doc("TM2 Evaluation Handoff Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Opening Readiness Record",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Opening Readiness Record", row):
				frappe.delete_doc("TM2 Opening Readiness Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Closing Record",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Closing Record", row):
				frappe.delete_doc("TM2 Tender Closing Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Late Submission Attempt",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Late Submission Attempt", row):
				frappe.delete_doc("TM2 Late Submission Attempt", row, force=True, ignore_permissions=True)
		for bid in frappe.get_all(
			"TM2 Bid Submission",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			for rct in frappe.get_all(
				"TM2 Bid Receipt",
				filters={"tm2_bid_submission": bid},
				pluck="name",
			):
				if frappe.db.exists("TM2 Bid Receipt", rct):
					frappe.delete_doc("TM2 Bid Receipt", rct, force=True, ignore_permissions=True)
			for comp in frappe.get_all(
				"TM2 Bid Submission Component",
				filters={"tm2_bid_submission": bid},
				pluck="name",
			):
				if frappe.db.exists("TM2 Bid Submission Component", comp):
					frappe.delete_doc(
						"TM2 Bid Submission Component", comp, force=True, ignore_permissions=True
					)
			if frappe.db.exists("TM2 Bid Submission", bid):
				frappe.delete_doc("TM2 Bid Submission", bid, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Addendum",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			for ack in frappe.get_all(
				"TM2 Addendum Acknowledgement",
				filters={"tm2_addendum": row},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Acknowledgement", ack):
					frappe.delete_doc("TM2 Addendum Acknowledgement", ack, force=True, ignore_permissions=True)
			if frappe.db.exists("TM2 Addendum", row):
				frappe.delete_doc("TM2 Addendum", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Bid Draft Metadata",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Draft Metadata", row):
				frappe.delete_doc("TM2 Bid Draft Metadata", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		self._cleanup_tm2(tm2_name)
		for sn in list(self._p602_suppliers_created):
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		self._p602_suppliers_created.clear()

	def _ensure_open_submission_window(self, tm2_name: str) -> None:
		deadline = add_to_date(now_datetime(), days=14)
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
		base = now_datetime()
		tc = frappe.db.get_value("TM2 Tender", tm2_name, "tender_code") or tm2_name
		if not tl_name:
			frappe.get_doc(
				{
					"doctype": "TM2 Tender Timeline",
					"tm2_tender": tm2_name,
					"tender_code": tc,
					"planned_publication_at": add_to_date(base, hours=-2),
					"clarification_deadline_at": add_to_date(base, days=3),
					"addendum_cutoff_at": add_to_date(base, days=8),
					"submission_deadline_at": deadline,
					"opening_scheduled_at": add_to_date(base, days=15),
					"tender_validity_days": 90,
					"timezone": "Africa/Nairobi",
				}
			).insert(ignore_permissions=True)
			return
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl_name,
			{
				"submission_deadline_at": deadline,
				"clarification_deadline_at": add_to_date(now_datetime(), days=3),
				"opening_scheduled_at": add_to_date(now_datetime(), days=15),
			},
			update_modified=False,
		)

	def _published_with_supplier(self, *, seed_outputs: bool = True) -> tuple[str, str, str]:
		tcode = self._mk_approved_for_publication(seed_outputs=seed_outputs)
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
		self._ensure_open_submission_window(tm2)
		sup = self._ensure_supplier("Alpha")
		frappe.get_doc({"doctype": "TM2 Supplier Participation", "tm2_tender": tm2, "supplier": sup}).insert(
			ignore_permissions=True
		)
		self.addCleanup(self._cleanup_p602, tm2)
		return tcode, tm2, sup
