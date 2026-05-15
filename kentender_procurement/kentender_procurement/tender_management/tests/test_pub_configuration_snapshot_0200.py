# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0200 — ``ConfigurationSnapshotService`` (readiness + STD configuration snapshot + lock).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_configuration_snapshot_0200
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tests.tm2_std_test_fixtures import (
	insert_minimal_tm2_for_std,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	CONFIG_SNAPSHOT_READINESS_REQUIRED,
	ConfigurationSnapshotService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubConfigurationSnapshot0200(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
		for dname in frappe.get_all(
			"Tender Publication Approval Decision",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc(
				"Tender Publication Approval Decision",
				dname,
				force=True,
				ignore_permissions=True,
			)
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
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
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		return insert_minimal_tm2_for_std(
			tender_title=f"PUB-0200 {ref}",
			tender_reference=ref,
		)

	def _publish_all_outputs(self, instance_name: str) -> None:
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(instance_name)
			StdInstanceGeneratedOutputService.publish_output(out.name)

	def _ensure_minimum_boq(self, instance_name: str) -> None:
		boq = StdInstanceBoqService.create_boq_for_instance(
			instance_name,
			ignore_boq_publication_lock=True,
		)
		boq = StdInstanceBoqService.add_bill(
			boq.name,
			"1",
			"General",
			"Works",
			ignore_boq_publication_lock=True,
		)
		bill_code = (boq.boq_bills or [])[0].bill_instance_code
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"1.1",
			"Site mobilization",
			"Item",
			1,
			ignore_boq_publication_lock=True,
		)

	def _ready_tender(self, ref: str) -> tuple[str, str]:
		tn = self._minimal_tender(ref=ref)
		frappe.db.set_value("TM2 Tender", tn, "source_package_code", f"REL-{ref}")
		si = TenderStdBindingService.create_std_instance_for_tm2_tender(
			tn,
			ignore_permissions=True,
			record_template_usage=False,
		)
		StdInstanceParameterService.set_parameter_value(
			si.name,
			"submission_deadline",
			"2026-12-31",
			ignore_publication_lock=True,
		)
		StdInstanceWorksRequirementService.set_works_requirement(
			si.name,
			"WR-COMP-001",
			structured_text="PUB-0200 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		return tn, si.name

	def test_pub_0200_create_denied_when_readiness_not_ready(self) -> None:
		tn = self._minimal_tender(ref="PUB0200-NOREL")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), CONFIG_SNAPSHOT_READINESS_REQUIRED)
			self.assertIsNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0200_create_snapshot_locks_instance_and_get_current(self) -> None:
		tn, si_name = self._ready_tender("PUB0200-OK")
		try:
			self.assertIsNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
			out = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			self.assertTrue(out.get("ok"))
			snap_name = out.get("snapshot")
			self.assertTrue(snap_name)
			self.assertEqual(out.get("instance_status"), "Locked for Approval")

			inst = frappe.get_doc("Tender STD Instance", si_name)
			self.assertEqual((inst.instance_status or "").strip(), "Locked for Approval")

			cur = ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn)
			self.assertIsNotNone(cur)
			assert cur is not None
			self.assertEqual(cur["snapshot_code"], snap_name)
			self.assertEqual(cur["tm2_tender"], tn)
			self.assertEqual(cur["tender_std_instance"], si_name)
			self.assertEqual((cur.get("snapshot_status") or "").strip(), "Final")
			for field, otype in (
				("ref_bundle_output", "current_bundle_output_code"),
				("ref_dsm_output", "current_dsm_output_code"),
				("ref_dom_output", "current_dom_output_code"),
				("ref_dem_output", "current_dem_output_code"),
				("ref_dcm_output", "current_dcm_output_code"),
			):
				self.assertEqual(
					(cur.get(field) or "").strip(),
					(frappe.db.get_value("Tender STD Instance", si_name, otype) or "").strip(),
				)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0200_second_create_fails_before_new_snapshot(self) -> None:
		tn, _si_name = self._ready_tender("PUB0200-DUP")
		try:
			ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			prev_snaps = frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tm2_tender": tn, "snapshot_type": "Configuration"},
				pluck="name",
			)
			with self.assertRaises(frappe.ValidationError):
				ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			after_snaps = frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tm2_tender": tn, "snapshot_type": "Configuration"},
				pluck="name",
			)
			self.assertEqual(sorted(prev_snaps), sorted(after_snaps))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0200_invalidate_supersedes_get_current_none(self) -> None:
		tn, _si_name = self._ready_tender("PUB0200-INV")
		try:
			out = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			snap_name = out["snapshot"]
			self.assertIsNotNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
			ConfigurationSnapshotService.invalidateConfigurationSnapshot(
				snap_name,
				"Test supersede",
				actor="Administrator",
			)
			doc = frappe.get_doc("Tender STD Instance Snapshot", snap_name)
			self.assertEqual((doc.snapshot_status or "").strip(), "Superseded")
			self.assertIsNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0200_second_invalidate_raises(self) -> None:
		tn, _si_name = self._ready_tender("PUB0200-2INV")
		try:
			out = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			snap_name = out["snapshot"]
			ConfigurationSnapshotService.invalidateConfigurationSnapshot(
				snap_name,
				"First supersede",
				actor="Administrator",
			)
			with self.assertRaises(frappe.ValidationError):
				ConfigurationSnapshotService.invalidateConfigurationSnapshot(
					snap_name,
					"Second supersede",
					actor="Administrator",
				)
		finally:
			self._cleanup_tender(tn)
