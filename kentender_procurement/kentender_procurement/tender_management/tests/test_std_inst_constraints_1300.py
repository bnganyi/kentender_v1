# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1300 — DB-backed constraints and safeguard checks."""

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
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)


class TestStdInstConstraints1300(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-1300 Test Tender"
		doc.tender_reference = f"STDINST1300-{frappe.generate_hash(length=8)}"
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
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _index_exists(self, table_name: str, index_name: str) -> bool:
		return bool(
			frappe.db.sql(
				"""
				select 1
				from information_schema.statistics
				where table_schema = database()
				  and table_name = %s
				  and index_name = %s
				limit 1
				""",
				(table_name, index_name),
			)
		)

	def test_std_inst_1300_required_indexes_exist(self) -> None:
		self.assertTrue(self._index_exists("tabTender STD Instance", "uniq_stdinst_active_tender_slot"))
		self.assertTrue(
			self._index_exists("tabTender STD Generated Output", "uniq_stdout_instance_type_version")
		)
		self.assertTrue(
			self._index_exists(
				"tabTender STD Instance Section Attachment",
				"uniq_stdatt_parent_attachment_code",
			)
		)

	def test_std_inst_1300_db_unique_active_slot_blocks_duplicate(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(Exception):
				frappe.db.sql(
					"""
					insert into `tabTender STD Instance`
					(name, creation, modified, modified_by, owner, docstatus, naming_series,
					 procurement_tender, template_version_code, applicability_profile_code,
					 procurement_category, procurement_method, instance_status, readiness_status,
					 created_from_tender_context, active_tender_slot)
					values
					(%s, now(), now(), 'Administrator', 'Administrator', 0, 'STDINST-.#####',
					 %s, 'TV-DB-1300', 'PROFILE-1300', 'WORKS', 'OPEN_COMPETITIVE_TENDERING',
					 'Draft', 'Not Ready', 1, %s)
					""",
					(f"STDINST-DUP-{frappe.generate_hash(length=8)}", tender, tender),
				)
			self.assertTrue(si.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1300_db_unique_output_version_blocks_duplicate(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			with self.assertRaises(Exception):
				frappe.db.sql(
					"""
					insert into `tabTender STD Generated Output`
					(name, creation, modified, modified_by, owner, docstatus, naming_series,
					 tender_std_instance, output_type, version_number, output_status,
					 source_template_version_code, source_profile_code, content_json,
					 input_hash, output_hash, generated_by_job_code, generated_at)
					values
					(%s, now(), now(), 'Administrator', 'Administrator', 0, 'STD-OUT-.#####',
					 %s, %s, %s, 'Draft', %s, %s, %s, %s, %s, %s, now())
					""",
					(
						f"STD-OUT-DUP-{frappe.generate_hash(length=8)}",
						out.tender_std_instance,
						out.output_type,
						int(out.version_number),
						out.source_template_version_code,
						out.source_profile_code,
						"{}",
						f"dup-in-{frappe.generate_hash(length=6)}",
						f"dup-out-{frappe.generate_hash(length=6)}",
						out.generated_by_job_code,
					),
				)
		finally:
			self._cleanup_tender(tender)
