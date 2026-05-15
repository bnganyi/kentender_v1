# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-1100 — publication readiness seed fixtures (pack §19 variants).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_seed_1100
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_POST_PUBLICATION_EDIT_DENIED,
	DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.seeds.seed_pub_moh_1100 import (
	fixture_codes,
	run,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)


class TestPubSeed1100(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		super().tearDown()

	def _cleanup_tm2_graph(self, tm2_name: str) -> None:
		if not tm2_name or not frappe.db.exists("TM2 Tender", tm2_name):
			return
		for dname in frappe.get_all(
			"Tender Publication Snapshot",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("Tender Publication Snapshot", dname, force=True, ignore_permissions=True)
		for dname in frappe.get_all(
			"Tender Publication Approval Decision",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			frappe.delete_doc("Tender Publication Approval Decision", dname, force=True, ignore_permissions=True)
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tm2_name},
			pluck="name",
		):
			for snap_name in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance Snapshot", snap_name, force=True, ignore_permissions=True)
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Generated Output", out_name, force=True, ignore_permissions=True)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance BOQ", boq_name, force=True, ignore_permissions=True)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender STD Binding", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Tender STD Binding", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Publication Record", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Publication Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender Audit Event", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Tender Audit Event", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender Access Rule", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Tender Access Rule", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Notification Record", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Notification Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Publication Readiness", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Publication Readiness", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender Timeline", filters={"tm2_tender": tm2_name}, pluck="name"):
			frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		frappe.delete_doc("TM2 Tender", tm2_name, force=True, ignore_permissions=True)

	def _cleanup_variant(self, variant: str) -> None:
		ref = fixture_codes(variant)["tender_reference"]
		tm2 = frappe.db.get_value("TM2 Tender", {"tender_reference": ref}, "name")
		if tm2:
			self._cleanup_tm2_graph(tm2)
		tag = fixture_codes(variant)["tag"]
		pkg = f"PKG-PUB1100-{tag}"
		if frappe.db.exists("Procurement Package", pkg):
			frappe.delete_doc("Procurement Package", pkg, force=True, ignore_permissions=True)

	def test_pub_1100_ready_idempotent(self) -> None:
		self.addCleanup(self._cleanup_variant, "ready")
		a = run("ready")
		b = run("ready")
		self.assertTrue(a.get("ok") and b.get("ok"))
		self.assertEqual(a.get("tender_name"), b.get("tender_name"))
		self.assertEqual(a.get("tender_reference"), fixture_codes("ready")["tender_reference"])
		self.assertEqual(a.get("publication_readiness_status"), "Ready")

	def test_pub_1100_ready_submit_for_approval(self) -> None:
		self.addCleanup(self._cleanup_variant, "ready")
		out = run("ready")
		tn = out["tender_code"]
		sub = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		self.assertTrue(sub.get("ok"))
		self.assertEqual((sub.get("instance_status") or "").strip(), "Locked for Approval")

	def test_pub_1100_no_bundle_blocked(self) -> None:
		self.addCleanup(self._cleanup_variant, "no_bundle")
		out = run("no_bundle")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("publication_readiness_status"), "Blocked")
		self.assertIn("BUNDLE_NOT_CURRENT", out.get("publication_finding_codes") or [])

	def test_pub_1100_stale_dem_blocked(self) -> None:
		self.addCleanup(self._cleanup_variant, "stale_dem")
		out = run("stale_dem")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("publication_readiness_status"), "Blocked")
		self.assertIn("DEM_NOT_CURRENT", out.get("publication_finding_codes") or [])

	def test_pub_1100_no_std_binding_blocked(self) -> None:
		self.addCleanup(self._cleanup_variant, "no_std_binding")
		out = run("no_std_binding")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("publication_readiness_status"), "Blocked")
		self.assertIn("STD_BINDING_MISSING", out.get("publication_finding_codes") or [])

	def test_pub_1100_approved_publish_happy_path(self) -> None:
		self.addCleanup(self._cleanup_variant, "approved")
		out = run("approved")
		tc = out["tender_code"]
		self.assertTrue(tc)
		spec_pub = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_pub)
		assert spec_pub is not None
		res = PublicationTransactionService.publishTender(
			tc,
			actor="Administrator",
			context={"granted_permissions": [spec_pub.required_permission]},
		)
		self.assertTrue(res.get("ok"))
		self.assertEqual((res.get("tender_status") or "").strip(), "Published")

	def test_pub_1100_published_idempotent_and_edit_denied(self) -> None:
		self.addCleanup(self._cleanup_variant, "published")
		a = run("published")
		b = run("published")
		self.assertTrue(a.get("ok") and b.get("ok"))
		self.assertEqual(a.get("tender_name"), b.get("tender_name"))
		self.assertEqual(a.get("tender_status"), "Published")
		tn = a["tender_name"]
		si = a["std_instance_code"]
		self.assertTrue(si)
		before = frappe.db.count(
			"Audit Event",
			{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
		)
		with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
			StdInstanceParameterService.set_parameter_value(
				si,
				"submission_deadline",
				"2027-01-01",
			)
		self.assertEqual(
			frappe.db.count(
				"Audit Event",
				{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
			),
			before + 1,
		)
		rows = frappe.get_all(
			"Audit Event",
			filters={"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
			fields=["metadata"],
			order_by="creation desc",
			limit=1,
		)
		meta = rows[0].get("metadata") or {}
		if isinstance(meta, str):
			meta = json.loads(meta)
		self.assertEqual(meta.get("denial_code"), DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED)

	def test_pub_1100_fixture_codes_match_template(self) -> None:
		c = fixture_codes("ready")
		self.assertEqual(c["procurement_package_code"], "PKG-MOH-2026-001")
		self.assertTrue(c["tender_reference"].startswith("TND-MOH-"))
		self.assertIn("STDINST-", c["std_instance_code"])
		self.assertEqual(c["output_bundle"].startswith("GB-"), True)
