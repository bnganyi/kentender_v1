# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1100 — append-only audit events for STD instance flows."""

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
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_DENIED_EDIT_ATTEMPT,
	EVT_STDINST_PARAMETER_CHANGED,
	EVT_STDINST_SNAPSHOT_CREATED,
)
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.snapshot import StdInstanceSnapshotService
from kentender_procurement.tender_management.works_completion.audit import WORKS_TDS_VALUES_CHANGED


class TestStdInstAudit1100(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-1100 Test Tender"
		doc.tender_reference = f"STDINST1100-{frappe.generate_hash(length=8)}"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
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

	def test_std_inst_1100_append_only_parameter_events(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			base = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_PARAMETER_CHANGED, "document_name": si.name},
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"submission_deadline",
				"2026-12-31",
			)
			after_first = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_PARAMETER_CHANGED, "document_name": si.name},
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"submission_deadline",
				"2027-01-01",
			)
			after_second = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_PARAMETER_CHANGED, "document_name": si.name},
			)
			self.assertEqual(after_first, base + 1)
			self.assertEqual(after_second, after_first + 1)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1100_denied_action_is_audited(self) -> None:
		tender = self._minimal_tender()
		base = frappe.db.count("Audit Event", {"event_type": EVT_STDINST_DENIED_EDIT_ATTEMPT})
		try:
			frappe.set_user("Guest")
			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					tender, ignore_permissions=True, record_template_usage=False
				)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_tender(tender)
		after = frappe.db.count("Audit Event", {"event_type": EVT_STDINST_DENIED_EDIT_ATTEMPT})
		self.assertEqual(after, base + 1)

	def test_std_inst_1100_snapshot_creation_is_audited(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			before = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_SNAPSHOT_CREATED, "document_name": si.name},
			)
			snap = StdInstanceSnapshotService.create_configuration_snapshot(
				si.name,
				"Audit validation snapshot",
			)
			after = frappe.db.count(
				"Audit Event",
				{"event_type": EVT_STDINST_SNAPSHOT_CREATED, "document_name": si.name},
			)
			self.assertEqual(after, before + 1)
			rows = frappe.get_all(
				"Audit Event",
				filters={"event_type": EVT_STDINST_SNAPSHOT_CREATED, "document_name": si.name},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			self.assertTrue(rows)
			md = rows[0].get("metadata") or {}
			if isinstance(md, str):
				md = frappe.parse_json(md)
			self.assertEqual((md.get("details") or {}).get("snapshot_type"), "Configuration")
			self.assertEqual(snap.tender_std_instance, si.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1100_direct_parameter_sets_do_not_emit_works_tds_audit(self) -> None:
		"""WORKS-COMP-0900 regression: STD parameter API stays separate from Works TDS façade."""
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			wb = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_TDS_VALUES_CHANGED, "document_name": si.name},
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"submission_deadline",
				"2026-12-31",
			)
			wa = frappe.db.count(
				"Audit Event",
				{"event_type": WORKS_TDS_VALUES_CHANGED, "document_name": si.name},
			)
			self.assertEqual(wa, wb)
		finally:
			self._cleanup_tender(tender)
