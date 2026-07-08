# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1400 — minimal seed fixture verification."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.seed_std_inst_1400 import (
	PACKAGE_CODE,
	TENDER_REFERENCE,
	WORKS_PROFILE_CODE,
	run,
)


class TestStdInstSeed1400(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_std_inst_1400_seed_creates_publishable_fixture(self) -> None:
		out = run()
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("procurement_package_code"), PACKAGE_CODE)
		self.assertEqual(out.get("tender_reference"), TENDER_REFERENCE)
		self.assertEqual(out.get("works_applicability_profile_code"), WORKS_PROFILE_CODE)
		self.assertEqual(out.get("instance_status"), "Published Locked")
		self.assertEqual(out.get("readiness_status"), "Ready")
		self.assertTrue(out.get("publication_snapshot_code"))

		instance_name = out.get("std_instance_code")
		self.assertTrue(instance_name and frappe.db.exists("Tender STD Instance", instance_name))
		for output_type in ("Bundle", "DSM", "DOM", "DEM", "DCM"):
			code = (out.get("generated_outputs") or {}).get(output_type)
			self.assertTrue(code)
			row = frappe.db.get_value(
				"Tender STD Generated Output",
				code,
				["output_type", "output_status"],
				as_dict=True,
			)
			self.assertEqual(row.output_type, output_type)
			self.assertEqual(row.output_status, "Published")

		snap = frappe.db.get_value(
			"Tender STD Instance Snapshot",
			out.get("publication_snapshot_code"),
			["snapshot_type", "snapshot_status"],
			as_dict=True,
		)
		self.assertEqual(snap.snapshot_type, "Publication")
		self.assertEqual(snap.snapshot_status, "Final")
