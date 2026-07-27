# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 3A / 3B — compile artifact persistence boundary."""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.compile_service import (
	assert_failed_result_not_submittable,
	assert_preview_artifact_immutable,
	execute_compile,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.fixtures_loader import (
	load_nssf_calibration_source_set,
	nssf_compile_request,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_COMPILE_ARTIFACT,
	DT_COMPILE_RUN,
	DT_MANIFEST_RESOURCE,
	DT_MANIFEST_VERSION,
	DT_WORKSPACE,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	clear_bwmf_canonical_fixture,
)


class TestBwmfCompileServicePhase3(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		clear_bwmf_canonical_fixture()
		# Ensure Compile Artifact DocType is loaded
		if not frappe.db.exists("DocType", DT_COMPILE_ARTIFACT):
			frappe.reload_doc("Tender Configurations", "doctype", "bwmf_compile_artifact", force=True)

	def tearDown(self):
		clear_bwmf_canonical_fixture()

	def test_successful_compile_persists_artifact_not_manifest_version(self):
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P3-{suffix}"
		out = execute_compile(
			compile_request_id=f"CR-P3-{suffix}",
			idempotency_key=f"CR-P3-{suffix}-KEY",
			run_id=f"RUN-P3-{suffix}",
			run_idempotency_key=f"RUN-P3-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P3-CAL",
		)
		self.assertTrue(out["ok"])
		self.assertFalse(out["publication_ready"])
		self.assertEqual(out["manifest_version"], "")
		self.assertTrue(out["compile_artifact"])
		self.assertEqual(out["digest_label"], "unmaterialized_preview_payload")
		self.assertEqual(out["canonical_resources_created"], 0)
		self.assertEqual(
			out["projection_digest"],
			"sha256:9dac86f777ae8c89f5b02e29e82401e5f83e12966891f2337fc7cc98ee0f907d",
		)
		run = frappe.get_doc(DT_COMPILE_RUN, out["compile_run"])
		self.assertEqual(run.state, "Succeeded")
		self.assertEqual(len(run.stage_trace), 22)
		art = frappe.get_doc(DT_COMPILE_ARTIFACT, out["compile_artifact"])
		self.assertEqual(art.target_manifest_id, req.target_manifest_id)
		self.assertEqual(art.target_manifest_version, 1)
		self.assertEqual(art.digest_label, "unmaterialized_preview_payload")
		candidates = json.loads(art.resource_candidates_json)
		self.assertGreaterEqual(len(candidates), 1)
		self.assertTrue(all(not c.get("materialized") for c in candidates))
		# No canonical Manifest Resource rows for this compile
		self.assertEqual(frappe.db.count(DT_MANIFEST_RESOURCE), 0)
		# No Manifest Version consumed by preview compile
		self.assertFalse(
			frappe.db.exists(
				DT_MANIFEST_VERSION,
				{"manifest_id": req.target_manifest_id, "manifest_version": 1},
			)
		)

	def test_two_preview_compiles_same_manifest_version(self):
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P3-DUP-{suffix}"
		src = load_nssf_calibration_source_set()
		first = execute_compile(
			compile_request_id=f"CR-P3-A-{suffix}",
			idempotency_key=f"CR-P3-A-{suffix}-KEY",
			run_id=f"RUN-P3-A-{suffix}",
			run_idempotency_key=f"RUN-P3-A-{suffix}-KEY",
			request=req,
			sources=src,
			organization="ORG-P3-CAL",
		)
		second = execute_compile(
			compile_request_id=f"CR-P3-B-{suffix}",
			idempotency_key=f"CR-P3-B-{suffix}-KEY",
			run_id=f"RUN-P3-B-{suffix}",
			run_idempotency_key=f"RUN-P3-B-{suffix}-KEY",
			request=req,
			sources=src,
			organization="ORG-P3-CAL",
		)
		self.assertTrue(first["ok"])
		self.assertTrue(second["ok"])
		self.assertNotEqual(first["compile_artifact"], second["compile_artifact"])
		a1 = frappe.get_doc(DT_COMPILE_ARTIFACT, first["compile_artifact"])
		a2 = frappe.get_doc(DT_COMPILE_ARTIFACT, second["compile_artifact"])
		self.assertEqual(a1.target_manifest_id, a2.target_manifest_id)
		self.assertEqual(a1.target_manifest_version, a2.target_manifest_version)
		# First artifact immutable / preserved
		self.assertEqual(a1.payload_digest, first["payload_digest"])
		prior_payload = a1.payload_json
		with self.assertRaises(frappe.ValidationError):
			assert_preview_artifact_immutable(first["compile_artifact"])
		a1_after = frappe.get_doc(DT_COMPILE_ARTIFACT, first["compile_artifact"])
		self.assertEqual(a1_after.payload_json, prior_payload)

	def test_failed_compile_not_publication_ready(self):
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P3-FAIL-{suffix}"
		req.expected_input_digests = dict(req.expected_input_digests)
		req.expected_input_digests["catalogue"] = "sha256:" + ("e" * 64)
		out = execute_compile(
			compile_request_id=f"CR-P3-FAIL-{suffix}",
			idempotency_key=f"CR-P3-FAIL-{suffix}-KEY",
			run_id=f"RUN-P3-FAIL-{suffix}",
			run_idempotency_key=f"RUN-P3-FAIL-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P3-CAL",
		)
		self.assertFalse(out["ok"])
		self.assertFalse(out["publication_ready"])
		self.assertEqual(out["manifest_version"], "")
		self.assertIsNone(out["payload_digest"])
		self.assertEqual(out["digest_label"], "failed_result")
		self.assertEqual(out["artifact_kind"], "failed_result")
		run = frappe.get_doc(DT_COMPILE_RUN, out["compile_run"])
		self.assertEqual(run.state, "Failed")
		self.assertEqual(len(run.stage_trace), 22)
		art = frappe.get_doc(DT_COMPILE_ARTIFACT, out["compile_artifact"])
		self.assertEqual(art.artifact_kind, "failed_result")
		self.assertFalse((art.payload_digest or "").strip())
		self.assertFalse((art.payload_json or "").strip())
		self.assertTrue((art.diagnostic_digest or "").strip())
		envelope = json.loads(art.envelope_json)
		self.assertTrue(envelope.get("failed"))
		self.assertIsNone(envelope.get("integrity", {}).get("payload_digest"))
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION), 0)
		self.assertEqual(frappe.db.count(DT_MANIFEST_RESOURCE), 0)
		with self.assertRaises(frappe.ValidationError):
			assert_failed_result_not_submittable(out["compile_artifact"])

	def test_compile_does_not_mutate_workspace_or_tender(self):
		before_ws = frappe.db.count(DT_WORKSPACE)
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P3-ISO-{suffix}"
		execute_compile(
			compile_request_id=f"CR-P3-ISO-{suffix}",
			idempotency_key=f"CR-P3-ISO-{suffix}-KEY",
			run_id=f"RUN-P3-ISO-{suffix}",
			run_idempotency_key=f"RUN-P3-ISO-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P3-CAL",
		)
		self.assertEqual(frappe.db.count(DT_WORKSPACE), before_ws)

	def test_candidates_not_stored_as_canonical_resources(self):
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P3-RES-{suffix}"
		before = frappe.db.count(DT_MANIFEST_RESOURCE)
		before_mv = frappe.db.count(DT_MANIFEST_VERSION)
		out = execute_compile(
			compile_request_id=f"CR-P3-RES-{suffix}",
			idempotency_key=f"CR-P3-RES-{suffix}-KEY",
			run_id=f"RUN-P3-RES-{suffix}",
			run_idempotency_key=f"RUN-P3-RES-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P3-CAL",
		)
		self.assertTrue(out["ok"])
		self.assertEqual(frappe.db.count(DT_MANIFEST_RESOURCE), before)
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION), before_mv)
		art = frappe.get_doc(DT_COMPILE_ARTIFACT, out["compile_artifact"])
		self.assertTrue(json.loads(art.resource_candidates_json))
		self.assertNotEqual(art.artifact_kind, "failed_result")
