# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-01 — doc 9 §9.1 ``create_tender_from_package`` (+ §8.2 adapter hook).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_tender_from_package import (
	create_tender_from_package,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	HandoffStdResolution,
)
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.services.tm2_std_adapter import get_eligible_std_templates
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class _P401Tm2Cleanup(_ReleaseProcurementPackageHandoffFixtures):
	def _cleanup_tm2(self, tm2_name: str | None) -> None:
		if not tm2_name or not frappe.db.exists("TM2 Tender", tm2_name):
			return
		for row in frappe.get_all(
			"TM2 Notification Record",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Notification Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Publication Record",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Publication Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Tender Audit Event", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Access Rule",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Publication Readiness",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Publication Readiness", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender STD Binding",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", row, force=True, ignore_permissions=True)
		frappe.delete_doc("TM2 Tender", tm2_name, force=True, ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()


class TestP401CreateTenderFromPackage(_P401Tm2Cleanup):
	def test_p4_01_rejects_unreleased_package(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		spec = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec)
		assert spec is not None
		out = create_tender_from_package(
			"Administrator",
			pkg.name,
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.PACKAGE_NOT_AUTHORIZED.value)

	def test_p4_01_auth_role_denied_without_permission(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		out = create_tender_from_package("Administrator", pkg.name, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_01_creates_draft_tender_audit_and_access_rule(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec)
		assert spec is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		eligible = get_eligible_std_templates(pc)
		self.assertTrue(eligible)

		now = now_datetime()
		ctx = {
			"granted_permissions": [spec.required_permission],
			"wizard_timeline_dates": {
				"clarification_deadline_at": add_days(now, 1),
				"submission_deadline_at": add_days(now, 10),
				"opening_scheduled_at": add_days(now, 11),
				"tender_validity_days": 30,
				"planned_publication_at": add_days(now, 0),
			},
		}
		out = create_tender_from_package("Administrator", pc, context=ctx)
		self.assertTrue(out.get("ok"), out)
		tm2_name = out.get("tm2_tender")
		self.assertTrue(tm2_name)
		self.addCleanup(self._cleanup_tm2, tm2_name)

		tcode = out.get("tender_code")
		self.assertTrue(tcode)
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2_name,
			["status", "procurement_package", "tender_title"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Draft")
		self.assertEqual(row.get("procurement_package"), pkg.name)

		ar = frappe.db.get_value(
			"TM2 Tender Access Rule",
			{"tm2_tender": tm2_name},
			["access_rule_code", "visibility"],
			as_dict=True,
		)
		self.assertTrue(ar)
		self.assertEqual(ar.get("access_rule_code"), f"TAC-{tcode}")
		self.assertEqual(ar.get("visibility"), "Public")

		self.assertTrue(frappe.db.exists("TM2 Tender Timeline", {"tm2_tender": tm2_name}))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2_name, "event_type": "Tender Created"},
			fields=["name", "event_payload"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		payload = ev[0].get("event_payload")
		if isinstance(payload, str):
			payload = json.loads(payload)
		self.assertIsInstance(payload, dict)
		self.assertEqual(payload.get("package_code"), pc)

	def test_p4_01_active_tender_blocks_second_create(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec)
		assert spec is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		ctx = {"granted_permissions": [spec.required_permission]}
		out1 = create_tender_from_package("Administrator", pc, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		self.addCleanup(self._cleanup_tm2, out1.get("tm2_tender"))

		out2 = create_tender_from_package("Administrator", pc, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.ACTIVE_TENDER_EXISTS.value)

	def test_p4_01_preferred_std_template_allows_multi_eligible(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec)
		assert spec is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

		fake_eligible = [
			{
				"std_template": TEMPLATE_CODE,
				"template_code": "T1",
				"template_name": "T1",
				"lifecycle_status": "Active",
				"resolution_path": "test",
			},
			{
				"std_template": "OTHER-STD-TEMPLATE",
				"template_code": "T2",
				"template_name": "T2",
				"lifecycle_status": "Active",
				"resolution_path": "test",
			},
		]
		ctx = {
			"granted_permissions": [spec.required_permission],
			"preferred_std_template": TEMPLATE_CODE,
		}
		with patch(
			"kentender_procurement.tender_management.services.create_tender_from_package.get_eligible_std_templates",
			return_value=fake_eligible,
		):
			out = create_tender_from_package("Administrator", pc, context=ctx)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))

	def test_p4_01_std_ambiguous_denies(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec)
		assert spec is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		with patch(
			"kentender_procurement.tender_management.services.create_tender_from_package.resolve_std_template_for_handoff",
			return_value=HandoffStdResolution(None, "ambiguous", ambiguous_candidates=("A", "B")),
		):
			out = create_tender_from_package(
				"Administrator",
				pc,
				context={"granted_permissions": [spec.required_permission]},
			)
		self.assertFalse(out.get("ok"))
		self.assertEqual(
			out.get("denial_code"),
			DenialCode.STD_MULTIPLE_ELIGIBLE_REQUIRES_SELECTION.value,
		)
