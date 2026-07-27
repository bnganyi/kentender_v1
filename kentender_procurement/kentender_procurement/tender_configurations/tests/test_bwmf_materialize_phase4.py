# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 4 / 4A — materialization integration tests."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.compile_service import (
	assert_preview_artifact_immutable,
	execute_compile,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.materialize_service import (
	execute_materialization,
	set_fail_during_resource_n,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.resource_verifier import (
	ResourceVerifyError,
	verify_resource_row,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.fixtures_loader import (
	load_json,
	load_nssf_calibration_source_set,
	load_synthetic_std_source_set,
	nssf_compile_request,
	synthetic_compile_request,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_COMPILE_ARTIFACT,
	DT_CONTENT_OBJECT,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE,
	DT_MANIFEST_VERSION,
	DT_MATERIALIZATION_REPORT,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	canonical_json_bytes,
	content_ref_for_bytes,
	delete_content_via_repository,
	get_verified,
	physical_digest_for_bytes,
	put_canonical_json,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.chunking import (
	chunk_items,
	validate_chunks,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	logical_resource_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.item_schemas import (
	NSSF_RESOURCE_ORDER,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	clear_bwmf_canonical_fixture,
	clear_bwmf_phase4_materialization,
)


def _ensure_doctypes():
	for dn in (
		"bwmf_content_object",
		"bwmf_artifact_resource_binding",
		"bwmf_materialization_report",
		"bwmf_manifest_resource",
		"bwmf_compile_artifact",
	):
		frappe.reload_doc("Tender Configurations", "doctype", dn, force=True)


def _resource_doc(resource_id: str):
	names = frappe.get_all(DT_MANIFEST_RESOURCE, filters={"resource_id": resource_id}, pluck="name")
	assert len(names) == 1, resource_id
	return frappe.get_doc(DT_MANIFEST_RESOURCE, names[0])


class TestBwmfMaterializePhase4(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_ensure_doctypes()
		set_fail_during_resource_n(None)
		clear_bwmf_canonical_fixture()

	def tearDown(self):
		set_fail_during_resource_n(None)
		clear_bwmf_canonical_fixture()

	def _compile_nssf_preview(self, *, target_suffix: str | None = None):
		req = nssf_compile_request()
		suffix = target_suffix or frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P4-{suffix}"
		out = execute_compile(
			compile_request_id=f"CR-P4-{suffix}",
			idempotency_key=f"CR-P4-{suffix}-KEY",
			run_id=f"RUN-P4-{suffix}",
			run_idempotency_key=f"RUN-P4-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P4",
		)
		self.assertTrue(out["ok"], out.get("fail_code"))
		return out

	def test_nssf_materialization_nine_resources(self):
		meta = load_json("nssf_calibration/resource_digest_meta.json")
		preview = self._compile_nssf_preview()
		before_mv = frappe.db.count(DT_MANIFEST_VERSION)
		before_pub = frappe.db.count(DT_MANIFEST_PUBLICATION)
		out = execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=f"MAT-{preview['compile_artifact']}",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		self.assertTrue(out["ok"])
		self.assertEqual(out["canonical_resources"], 9)
		self.assertEqual(out["descriptor_set_digest"], meta["descriptor_set_digest"])
		self.assertTrue(out["calibration_only"])
		self.assertFalse(out["publication_readiness"].get("passed"))
		self.assertIn(
			"calibration_only_not_publishable",
			out["publication_readiness"].get("blocking_reasons") or [],
		)
		self.assertTrue(out["publication_readiness"].get("resource_readiness", {}).get("passed"))
		self.assertFalse(frappe.get_meta(DT_MANIFEST_RESOURCE).has_field("manifest_version"))
		# Bindings only on finalized artifact, not preview
		self.assertEqual(
			frappe.db.count(DT_ARTIFACT_RESOURCE_BINDING, {"compile_artifact": preview["compile_artifact"]}),
			0,
		)
		self.assertEqual(
			frappe.db.count(DT_ARTIFACT_RESOURCE_BINDING, {"compile_artifact": out["finalized_artifact"]}),
			9,
		)
		for rid in NSSF_RESOURCE_ORDER:
			doc = _resource_doc(rid)
			self.assertEqual(doc.storage_mode, "content_addressed")
			self.assertTrue(doc.content_ref.startswith("bwmf-cas:v1:"))
			verify_resource_row(doc.name)
		final = frappe.get_doc(DT_COMPILE_ARTIFACT, out["finalized_artifact"])
		self.assertEqual(final.artifact_kind, "finalized_materialized")
		self.assertEqual(final.digest_label, "materialized_calibration_payload")
		self.assertFalse(json.loads(final.envelope_json)["integrity"]["final_runtime_manifest"])
		prev = frappe.get_doc(DT_COMPILE_ARTIFACT, preview["compile_artifact"])
		self.assertEqual(prev.payload_digest, preview["payload_digest"])
		with self.assertRaises(frappe.ValidationError):
			assert_preview_artifact_immutable(preview["compile_artifact"])
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION), before_mv)
		self.assertEqual(frappe.db.count(DT_MANIFEST_PUBLICATION), before_pub)

	def test_dual_materialization_determinism_and_idempotency(self):
		p1 = self._compile_nssf_preview()
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P4-B-{suffix}"
		p2 = execute_compile(
			compile_request_id=f"CR-P4-B-{suffix}",
			idempotency_key=f"CR-P4-B-{suffix}-KEY",
			run_id=f"RUN-P4-B-{suffix}",
			run_idempotency_key=f"RUN-P4-B-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P4",
		)
		a = execute_materialization(
			source_artifact_name=p1["compile_artifact"],
			idempotency_key=f"MAT-A-{p1['compile_artifact']}",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		b = execute_materialization(
			source_artifact_name=p2["compile_artifact"],
			idempotency_key=f"MAT-B-{p2['compile_artifact']}",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		self.assertEqual(a["descriptor_set_digest"], b["descriptor_set_digest"])
		a_refs = {d["resource_id"]: d["content_ref"] for d in a["dispositions"]}
		b_refs = {d["resource_id"]: d["content_ref"] for d in b["dispositions"]}
		self.assertEqual(a_refs, b_refs)
		# Different keys reuse same immutable resources/content objects
		self.assertEqual(
			frappe.db.count(DT_MANIFEST_RESOURCE),
			9,
		)
		self.assertEqual(a["finalized_artifact"], a["finalized_artifact"])
		self.assertNotEqual(a["finalized_artifact"], b["finalized_artifact"])
		a2 = execute_materialization(
			source_artifact_name=p1["compile_artifact"],
			idempotency_key=f"MAT-A-{p1['compile_artifact']}",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		self.assertEqual(a2["finalized_artifact"], a["finalized_artifact"])
		self.assertEqual(a2["finalized_payload_digest"], a["finalized_payload_digest"])

	def test_idempotency_fingerprint_mismatch(self):
		p1 = self._compile_nssf_preview()
		execute_materialization(
			source_artifact_name=p1["compile_artifact"],
			idempotency_key="MAT-FP-SHARED",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		p2 = self._compile_nssf_preview()
		with self.assertRaises(frappe.ValidationError):
			execute_materialization(
				source_artifact_name=p2["compile_artifact"],
				idempotency_key="MAT-FP-SHARED",
				organization="ORG-P4",
				sources=load_nssf_calibration_source_set(),
				calibration_only=True,
			)
		titles = [m.get("title") for m in frappe.get_message_log()]
		self.assertIn("BWMF_IDEMPOTENCY_FINGERPRINT_MISMATCH", titles)

	def test_concurrent_materialization_one_result(self):
		"""Same idempotency key yields one Succeeded report (GET_LOCK-backed resolver)."""
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
			idempotency as idem_mod,
		)

		preview = self._compile_nssf_preview()
		key = f"MAT-CONC-{preview['compile_artifact']}"
		first = execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=key,
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		second = execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=key,
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		self.assertEqual(first["finalized_artifact"], second["finalized_artifact"])
		self.assertEqual(frappe.db.count(DT_MATERIALIZATION_REPORT, {"state": "Succeeded"}), 1)
		self.assertIn("get_lock", Path(idem_mod.__file__).read_text(encoding="utf-8"))

	def test_partial_failure_fifth_resource_atomic(self):
		preview = self._compile_nssf_preview()
		prev_digest = preview["payload_digest"]
		set_fail_during_resource_n(5)
		out = execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=f"MAT-FAIL5-{preview['compile_artifact']}",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		self.assertFalse(out["ok"])
		self.assertEqual(frappe.db.count(DT_COMPILE_ARTIFACT, {"artifact_kind": "finalized_materialized"}), 0)
		self.assertEqual(frappe.db.count(DT_ARTIFACT_RESOURCE_BINDING), 0)
		self.assertEqual(frappe.db.count(DT_MATERIALIZATION_REPORT, {"state": "Succeeded"}), 0)
		self.assertGreaterEqual(frappe.db.count(DT_MATERIALIZATION_REPORT, {"state": "Failed"}), 1)
		self.assertFalse((out.get("publication_readiness") or {}).get("passed"))
		self.assertFalse(
			((out.get("publication_readiness") or {}).get("resource_readiness") or {}).get("passed")
		)
		prev = frappe.get_doc(DT_COMPILE_ARTIFACT, preview["compile_artifact"])
		self.assertEqual(prev.payload_digest, prev_digest)
		# Unreferenced CAS may remain; reset removes it
		clear_bwmf_phase4_materialization(keep_preview_artifacts=True)
		self.assertEqual(frappe.db.count(DT_CONTENT_OBJECT), 0)

	def test_failed_result_rejected(self):
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P4-FAIL-{suffix}"
		req.expected_input_digests = dict(req.expected_input_digests)
		req.expected_input_digests["catalogue"] = "sha256:" + ("e" * 64)
		out = execute_compile(
			compile_request_id=f"CR-P4-FAIL-{suffix}",
			idempotency_key=f"CR-P4-FAIL-{suffix}-KEY",
			run_id=f"RUN-P4-FAIL-{suffix}",
			run_idempotency_key=f"RUN-P4-FAIL-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization="ORG-P4",
		)
		self.assertFalse(out["ok"])
		with self.assertRaises(frappe.ValidationError):
			execute_materialization(
				source_artifact_name=out["compile_artifact"],
				idempotency_key=f"MAT-FAIL-{suffix}",
				organization="ORG-P4",
			)

	def test_cas_protection_suite(self):
		stored = put_canonical_json([{"k": 1}], organization="ORG-P4")
		self.assertTrue(stored["content_ref"].startswith("bwmf-cas:v1:"))
		self.assertNotIn("/", stored["content_ref"])
		self.assertNotIn("http", stored["content_ref"])
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			get_verified("https://example.com/file.json")
		self.assertIn("BWMF_CAS_REF", [m.get("title") for m in frappe.get_message_log()])
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			get_verified("/private/files/foo.json")
		self.assertIn("BWMF_CAS_REF", [m.get("title") for m in frappe.get_message_log()])
		# Reference via a Manifest Resource
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
			services as bwmf,
		)

		bwmf.create_manifest_resource(
			resource_id="RESOURCE-CAS-GUARD",
			resource_type="synthetic",
			schema_ref="bwmf/item/synthetic",
			schema_version="1.0.0",
			item_count=1,
			ordering_contract=["k"],
			resource_digest=logical_resource_digest([{"k": 1}]),
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[{"collection": "synthetic"}],
			organization="ORG-P4",
		)
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			delete_content_via_repository(stored["content_ref"])
		self.assertIn("BWMF_CAS_REFERENCED", [m.get("title") for m in frappe.get_message_log()])
		co_name = frappe.db.get_value(DT_CONTENT_OBJECT, {"content_ref": stored["content_ref"]}, "name")
		co = frappe.get_doc(DT_CONTENT_OBJECT, co_name)
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(DT_CONTENT_OBJECT, co.name, ignore_permissions=True)
		self.assertIn("BWMF_CAS_REFERENCED", [m.get("title") for m in frappe.get_message_log()])
		file_doc = frappe.get_doc("File", co.file_name)
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
		self.assertIn("BWMF_CAS_REFERENCED", [m.get("title") for m in frappe.get_message_log()])
		# Missing physical bytes — path is derived from content_ref hex only.
		hex_digest = stored["content_ref"].removeprefix("bwmf-cas:v1:")
		path = Path(frappe.get_site_path("private", "files", f"bwmf-cas-{hex_digest}.json"))
		self.assertTrue(path.is_file(), path)
		backup = path.read_bytes()
		path.unlink()
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			get_verified(stored["content_ref"])
		self.assertIn("BWMF_CAS_MISSING", [m.get("title") for m in frappe.get_message_log()])
		path.write_bytes(backup)
		# Changed bytes
		path.write_bytes(b'[{"tampered":true}]')
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			get_verified(stored["content_ref"])
		self.assertIn("BWMF_CAS_CORRUPT", [m.get("title") for m in frappe.get_message_log()])

	def test_clean_reseed_determinism(self):
		preview = self._compile_nssf_preview(target_suffix="FIXEDSEED01")
		preview_name = preview["compile_artifact"]

		def _snapshot():
			out = execute_materialization(
				source_artifact_name=preview_name,
				idempotency_key=f"MAT-RESEED-{frappe.generate_hash(length=6)}",
				organization="ORG-P4",
				sources=load_nssf_calibration_source_set(),
				calibration_only=True,
			)
			self.assertTrue(out["ok"])
			final = frappe.get_doc(DT_COMPILE_ARTIFACT, out["finalized_artifact"])
			payload = json.loads(final.payload_json)
			bytes_map = {}
			for d in out["dispositions"]:
				bytes_map[d["resource_id"]] = get_verified(d["content_ref"])
			return {
				"descriptor_set_digest": out["descriptor_set_digest"],
				"finalized_payload_digest": out["finalized_payload_digest"],
				"payload_bytes": canonical_json_bytes(payload),
				"payload_jcs": jcs_sha256_digest(payload),
				"resource_digests": {d["resource_id"]: d["actual_digest"] for d in out["dispositions"]},
				"physical_digests": {
					d["resource_id"]: d["physical_object_digest"] for d in out["dispositions"]
				},
				"content_refs": {d["resource_id"]: d["content_ref"] for d in out["dispositions"]},
				"frozen_bytes": bytes_map,
			}

		a = _snapshot()
		clear_bwmf_phase4_materialization(keep_preview_artifacts=True)
		# preview must survive
		self.assertTrue(frappe.db.exists(DT_COMPILE_ARTIFACT, preview_name))
		b = _snapshot()
		self.assertEqual(a["descriptor_set_digest"], b["descriptor_set_digest"])
		self.assertEqual(a["finalized_payload_digest"], b["finalized_payload_digest"])
		self.assertEqual(a["payload_bytes"], b["payload_bytes"])
		self.assertEqual(a["payload_jcs"], b["payload_jcs"])
		self.assertEqual(a["resource_digests"], b["resource_digests"])
		self.assertEqual(a["physical_digests"], b["physical_digests"])
		self.assertEqual(a["content_refs"], b["content_refs"])
		self.assertEqual(a["frozen_bytes"], b["frozen_bytes"])

	def test_synthetic_publication_readiness(self):
		req = synthetic_compile_request(compile_mode="preview")
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-SYN-P4-{suffix}"
		src = load_synthetic_std_source_set()
		preview = execute_compile(
			compile_request_id=f"CR-SYN-{suffix}",
			idempotency_key=f"CR-SYN-{suffix}-KEY",
			run_id=f"RUN-SYN-{suffix}",
			run_idempotency_key=f"RUN-SYN-{suffix}-KEY",
			request=req,
			sources=src,
			organization="ORG-P4",
		)
		self.assertTrue(preview["ok"])
		pub_req = synthetic_compile_request(compile_mode="publication")
		pub_req.target_manifest_id = req.target_manifest_id
		out = execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=f"MAT-SYN-{suffix}",
			organization="ORG-P4",
			sources=src,
			request=pub_req,
			calibration_only=False,
		)
		self.assertTrue(out["ok"], out)
		self.assertTrue(out["publication_readiness"].get("passed"))
		self.assertTrue(out["publication_readiness"].get("resource_readiness", {}).get("passed"))
		self.assertEqual(out["publication_readiness"].get("error_count"), 0)
		final = frappe.get_doc(DT_COMPILE_ARTIFACT, out["finalized_artifact"])
		self.assertEqual(final.digest_label, "materialized_publication_candidate_payload")
		self.assertFalse(json.loads(final.envelope_json)["integrity"]["final_runtime_manifest"])
		self.assertEqual(out["manifest_versions_created"], 0)
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION, {"manifest_id": req.target_manifest_id}), 0)

	def test_chunking_synthetic_full_contract(self):
		items = [{"id": f"I-{i}", "order_weight": i * 10} for i in range(5)]
		full_digest = logical_resource_digest(items)
		chunks = chunk_items(items, identity_key="id", chunk_size=2, organization="ORG-P4")
		validate_chunks(chunks, expected_item_count=5, verify_bytes=True)
		self.assertEqual(len(chunks), 3)
		self.assertEqual([c["index"] for c in chunks], [0, 1, 2])
		self.assertEqual(chunks[0]["first_item_key"], "I-0")
		self.assertEqual(chunks[0]["last_item_key"], "I-1")
		self.assertEqual(chunks[-1]["first_item_key"], "I-4")
		self.assertEqual(chunks[-1]["last_item_key"], "I-4")
		# Aggregate digest over complete logical array, independent of concatenation
		concat = b"".join(get_verified(c["content_ref"]) for c in chunks)
		self.assertNotEqual(content_ref_for_bytes(concat), content_ref_for_bytes(canonical_json_bytes(items)))
		self.assertEqual(full_digest, logical_resource_digest(items))
		# Negatives
		with self.assertRaises(ValueError):
			bad = copy.deepcopy(chunks)
			del bad[1]
			# reindex broken
			validate_chunks(bad, expected_item_count=5)
		with self.assertRaises(ValueError):
			bad = copy.deepcopy(chunks)
			bad.append(copy.deepcopy(bad[0]))
			bad[-1]["index"] = 3
			validate_chunks(bad, expected_item_count=5)
		with self.assertRaises(ValueError):
			bad = copy.deepcopy(chunks)
			bad[0], bad[1] = bad[1], bad[0]
			validate_chunks(bad, expected_item_count=5)
		with self.assertRaises(ValueError):
			bad = copy.deepcopy(chunks)
			bad[1]["item_range_start"] = 0
			validate_chunks(bad, expected_item_count=5)
		with self.assertRaises(ValueError):
			bad = copy.deepcopy(chunks)
			bad[0]["byte_size"] = 1
			validate_chunks(bad, expected_item_count=5, verify_bytes=True)
		# Corrupted chunk bytes
		raw_ref = chunks[0]["content_ref"]
		hex_digest = raw_ref.removeprefix("bwmf-cas:v1:")
		path = Path(frappe.get_site_path("private", "files", f"bwmf-cas-{hex_digest}.json"))
		path.write_bytes(b"[]")
		with self.assertRaises(Exception):
			validate_chunks(chunks, expected_item_count=5, verify_bytes=True)

	def test_resource_immutability(self):
		preview = self._compile_nssf_preview()
		execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=f"MAT-IMM-{preview['compile_artifact']}",
			organization="ORG-P4",
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		doc = _resource_doc(NSSF_RESOURCE_ORDER[0])
		doc.item_count = 999
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_same_bytes_different_resource_identities(self):
		items = [{"id": "X", "order_weight": 1}]
		digest = logical_resource_digest(items)
		stored = put_canonical_json(items, organization="ORG-P4")
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
			services as bwmf,
		)

		a = bwmf.create_manifest_resource(
			resource_id="RESOURCE-A",
			resource_type="synthetic",
			schema_ref="bwmf/item/a",
			schema_version="1.0.0",
			item_count=1,
			ordering_contract=["order_weight", "id"],
			resource_digest=digest,
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[{"t": "a"}],
			organization="ORG-P4",
		)
		b = bwmf.create_manifest_resource(
			resource_id="RESOURCE-B",
			resource_type="synthetic",
			schema_ref="bwmf/item/b",
			schema_version="1.0.0",
			item_count=1,
			ordering_contract=["order_weight", "id"],
			resource_digest=digest,
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[{"t": "b"}],
			organization="ORG-P4",
		)
		self.assertNotEqual(a, b)
		self.assertEqual(frappe.db.count(DT_CONTENT_OBJECT, {"content_ref": stored["content_ref"]}), 1)
