# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B8 — handoff audit + ``source_package_snapshot_json`` (doc 2 sec. 18).

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_planning_tender_handoff_audit_b8
"""

from __future__ import annotations

import hashlib
import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	release_procurement_package_to_tender,
)
from kentender_procurement.tender_management.services.std_template_engine import hash_config
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestPlanningTenderHandoffAuditB8(_ReleaseProcurementPackageHandoffFixtures):
	def test_b8_snapshot_hash_counts_and_audit_comment(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		tn = out["tender"]
		self._created.append(("Procurement Tender", tn))

		raw_snap = frappe.db.get_value("Procurement Tender", tn, "source_package_snapshot_json") or ""
		self.assertTrue(raw_snap.strip())
		snap = json.loads(raw_snap)
		self.assertEqual(snap.get("schema"), "kentender.planning_to_tender.handoff_snapshot/v1")
		self.assertEqual(snap.get("package", {}).get("name"), pkg.name)

		db_hash = frappe.db.get_value("Procurement Tender", tn, "source_package_hash")
		expect_hash = hashlib.sha256(raw_snap.encode("utf-8")).hexdigest()
		self.assertEqual(db_hash, expect_hash)

		cfg_raw = frappe.db.get_value("Procurement Tender", tn, "configuration_json") or "{}"
		expect_cfg_hash = hash_config(json.loads(cfg_raw))
		self.assertEqual(
			frappe.db.get_value("Procurement Tender", tn, "configuration_hash"),
			expect_cfg_hash,
		)

		self.assertEqual(frappe.db.get_value("Procurement Tender", tn, "source_demand_count"), 1)
		self.assertEqual(frappe.db.get_value("Procurement Tender", tn, "source_budget_line_count"), 1)

		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Procurement Tender", "reference_name": tn},
			fields=["content"],
			order_by="creation desc",
			limit=5,
		)
		self.assertTrue(comments, "expected at least one Comment on the tender")
		payload = json.loads(comments[0].content)
		self.assertEqual(payload.get("event"), "planning_to_tender_handoff")
		self.assertEqual(payload.get("target_tender"), tn)
		self.assertEqual(payload.get("handoff_snapshot_sha256"), db_hash)
		self.assertEqual(payload.get("configuration_hash_after_init"), expect_cfg_hash)
		self.assertEqual(payload.get("std_template"), TEMPLATE_CODE)

	def test_b8_audit_failure_deletes_tender(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		with patch(
			"kentender_procurement.tender_management.services.release_procurement_package_to_tender.append_handoff_audit_comment",
			side_effect=RuntimeError("simulated audit failure"),
		):
			with self.assertRaises(frappe.ValidationError):
				release_procurement_package_to_tender(pkg.name)

		linked = frappe.get_all(
			"Procurement Tender",
			filters={"procurement_package": pkg.name, "tender_status": ("!=", "Cancelled")},
			pluck="name",
		)
		self.assertFalse(linked, "tender must be removed when audit comment fails")
