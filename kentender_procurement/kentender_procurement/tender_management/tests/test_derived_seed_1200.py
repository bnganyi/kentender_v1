# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1200 — representative Works derived-model seed fixtures (pack §19).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_seed_1200
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	OutputConsumptionService,
)
from kentender_procurement.tender_management.derived_models.seeds.seed_derived_moh_1200 import (
	INSTANCE_CODE,
	OUT_BUNDLE,
	OUT_DCM_V1,
	OUT_DEM,
	OUT_DOM,
	OUT_DSM,
	SNAP_PUB,
	run,
)


TEST_TENDER_REF = "TND-MOH-2026-DER1200"
# Isolated from PKG-MOH-2026-001 (planning-handoff uniqueness: one active tender per package).
TEST_PACKAGE = "PKG-DERIVED-1200-001"


def _as_dict(content_json: object) -> dict:
	if isinstance(content_json, dict):
		return content_json
	if isinstance(content_json, str) and content_json.strip():
		return json.loads(content_json)
	return {}


def _purge_tender_chain(tender_reference: str) -> None:
	tname = frappe.db.get_value(
		"TM2 Tender",
		{"tender_reference": tender_reference},
		"name",
	)
	if not tname:
		return
	for si in frappe.get_all(
		"Tender STD Instance",
		filters={"tm2_tender": tname},
		pluck="name",
	):
		for snap in frappe.get_all(
			"Tender STD Instance Snapshot",
			filters={"tender_std_instance": si},
			pluck="name",
		):
			frappe.delete_doc(
				"Tender STD Instance Snapshot",
				snap,
				force=True,
				ignore_permissions=True,
			)
		for out in frappe.get_all(
			"Tender STD Generated Output",
			filters={"tender_std_instance": si},
			pluck="name",
		):
			frappe.delete_doc(
				"Tender STD Generated Output",
				out,
				force=True,
				ignore_permissions=True,
			)
		for boq in frappe.get_all(
			"Tender STD Instance BOQ",
			filters={"tender_std_instance": si},
			pluck="name",
		):
			frappe.delete_doc(
				"Tender STD Instance BOQ",
				boq,
				force=True,
				ignore_permissions=True,
			)
		frappe.delete_doc("Tender STD Instance", si, force=True, ignore_permissions=True)
	frappe.delete_doc("TM2 Tender", tname, force=True, ignore_permissions=True)


def _purge_std_instance_named(si_name: str) -> None:
	if not frappe.db.exists("Tender STD Instance", si_name):
		return
	tn = frappe.db.get_value("Tender STD Instance", si_name, "tm2_tender")
	if tn and frappe.db.exists("TM2 Tender", tn):
		ref = frappe.db.get_value("TM2 Tender", tn, "tender_reference")
		if ref:
			_purge_tender_chain(ref)
			return
	for snap in frappe.get_all(
		"Tender STD Instance Snapshot",
		filters={"tender_std_instance": si_name},
		pluck="name",
	):
		frappe.delete_doc(
			"Tender STD Instance Snapshot",
			snap,
			force=True,
			ignore_permissions=True,
		)
	for out in frappe.get_all(
		"Tender STD Generated Output",
		filters={"tender_std_instance": si_name},
		pluck="name",
	):
		frappe.delete_doc(
			"Tender STD Generated Output",
			out,
			force=True,
			ignore_permissions=True,
		)
	for boq in frappe.get_all(
		"Tender STD Instance BOQ",
		filters={"tender_std_instance": si_name},
		pluck="name",
	):
		frappe.delete_doc(
			"Tender STD Instance BOQ",
			boq,
			force=True,
			ignore_permissions=True,
		)
	frappe.delete_doc("Tender STD Instance", si_name, force=True, ignore_permissions=True)


class TestDerivedSeed1200(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		_purge_std_instance_named(INSTANCE_CODE)
		_purge_tender_chain(TEST_TENDER_REF)

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		_purge_std_instance_named(INSTANCE_CODE)
		_purge_tender_chain(TEST_TENDER_REF)
		super().tearDown()

	def test_derived_1200_named_fixture_and_consumption(self) -> None:
		out = run(tender_reference=TEST_TENDER_REF, procurement_package_code=TEST_PACKAGE)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("procurement_package_code"), TEST_PACKAGE)
		self.assertEqual(out.get("std_instance_code"), INSTANCE_CODE)
		self.assertEqual(out.get("tender_reference"), TEST_TENDER_REF)
		self.assertEqual(out.get("publication_snapshot_code"), SNAP_PUB)

		for oname in (OUT_BUNDLE, OUT_DSM, OUT_DOM, OUT_DEM, OUT_DCM_V1):
			self.assertTrue(frappe.db.exists("Tender STD Generated Output", oname))

		row = frappe.db.get_value(
			"Tender STD Generated Output",
			OUT_DSM,
			["output_status", "tender_std_instance"],
			as_dict=True,
		)
		self.assertEqual(row.output_status, "Published")
		self.assertEqual(row.tender_std_instance, INSTANCE_CODE)

		dsm_doc = frappe.get_doc("Tender STD Generated Output", OUT_DSM)
		cj = _as_dict(dsm_doc.content_json)
		self.assertTrue(cj)
		reqs = cj.get("requirements") or []
		labels = {str(r.get("label") or "") for r in reqs}
		types = {(str(r.get("label") or ""), r.get("requirement_type")) for r in reqs}
		self.assertIn("Form of Tender", labels)
		self.assertIn(("Method statement", "TechnicalProposal"), types)
		self.assertTrue(any(t == "Document" and "security" in str(l).lower() for l, t in types))
		boq_entry = cj.get("boq_rate_entry") or {}
		self.assertEqual(boq_entry.get("editable_fields"), ["rate"])
		self.assertEqual(
			set(boq_entry.get("locked_fields") or []),
			{"item_number", "description", "unit", "quantity"},
		)
		self.assertTrue(all((r.get("source_trace") or {}).get("source_type") for r in reqs))

		dom_doc = frappe.get_doc("Tender STD Generated Output", OUT_DOM)
		dom_cj = _as_dict(dom_doc.content_json)
		self.assertTrue(dom_cj)
		codes = {r.get("field_code") for r in (dom_cj.get("register_fields") or [])}
		for fc in (
			"bidder_name",
			"submission_timestamp",
			"submitted_total_bid_price",
			"tender_security_present",
			"bid_modification_or_withdrawal",
		):
			self.assertIn(fc, codes)

		dem_doc = frappe.get_doc("Tender STD Generated Output", OUT_DEM)
		dem_cj = _as_dict(dem_doc.content_json)
		self.assertTrue(dem_cj)
		stage_types = [s.get("stage_type") for s in (dem_cj.get("stages") or [])]
		for st in (
			"Responsiveness",
			"Eligibility",
			"Qualification",
			"Technical",
			"Financial",
			"BOQArithmetic",
			"Ranking",
		):
			self.assertIn(st, stage_types)
		bac = dem_cj.get("boq_arithmetic_correction") or {}
		self.assertTrue(bac.get("enabled"))
		self.assertEqual((dem_cj.get("ranking") or {}).get("method"), "LowestEvaluatedCost")

		dcm_doc = frappe.get_doc("Tender STD Generated Output", OUT_DCM_V1)
		dcm_cj = _as_dict(dcm_doc.content_json)
		self.assertTrue(dcm_cj)
		ps = dcm_cj.get("price_source") or {}
		self.assertEqual(ps.get("source_type"), "CorrectedEvaluatedBOQTotal")
		self.assertFalse(ps.get("manual_override_allowed"))
		self.assertEqual(dcm_cj.get("completion_period_days"), 180)
		self.assertEqual(dcm_cj.get("defects_liability_period_days"), 365)
		self.assertEqual(dcm_cj.get("performance_security_percent"), 10)
		self.assertEqual(dcm_cj.get("retention_percent"), 5)

		pub = OutputConsumptionService.validate_consumption(OUT_BUNDLE, "Publication", None)
		self.assertTrue(pub.get("allowed"))
		sub = OutputConsumptionService.validate_consumption(OUT_DSM, "Submission", None)
		self.assertTrue(sub.get("allowed"))

		cur_dcm = (frappe.db.get_value("Tender STD Instance", INSTANCE_CODE, "current_dcm_output_code") or "").strip()
		self.assertNotEqual(cur_dcm, OUT_DCM_V1)
		con = OutputConsumptionService.validate_consumption(cur_dcm, "Contract", None)
		self.assertTrue(con.get("allowed"))
		self.assertEqual(con.get("snapshot_code"), SNAP_PUB)

	def test_derived_1200_idempotent(self) -> None:
		a = run(tender_reference=TEST_TENDER_REF, procurement_package_code=TEST_PACKAGE)
		self.assertTrue(a.get("ok"))
		b = run(tender_reference=TEST_TENDER_REF, procurement_package_code=TEST_PACKAGE)
		self.assertTrue(b.get("ok"))
		self.assertEqual(a.get("std_instance_code"), b.get("std_instance_code"))
		self.assertEqual(a.get("publication_snapshot_code"), b.get("publication_snapshot_code"))
