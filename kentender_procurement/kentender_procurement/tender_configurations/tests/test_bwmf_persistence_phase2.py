# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 2 / 2A — BWMF persistence immutability, concurrency, idempotency, reseed."""

from __future__ import annotations
from kentender_procurement.tender_configurations.tests.helpers.bwmf_policy import explicit_submission_policy

import json
import threading
import unittest

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
	services as bwmf,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.decimal_money import (
	decimal_to_storage_str,
	exact_decimal_roundtrip,
	serialize_manifest_money,
	sum_money,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.idempotency import (
	canonical_request_fingerprint,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_AUDIT_EVENT,
	DT_EVIDENCE_VERSION,
	DT_IDEMPOTENCY_RECORD,
	DT_MANIFEST_VERSION,
	DT_RESPONSE_VERSION,
	DT_SUBMISSION,
	DT_WORKSPACE,
	DT_WORKSPACE_BINDING,
	REQUIRED_PERSISTENCE_CONCEPTS,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.snapshot import (
	assert_closed_submission_snapshot,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.schema_meta import (
	assert_coverage_ledger_complete,
	load_coverage_ledger,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	FIXTURE_ORG,
	FIXTURE_PARTY,
	FIXTURE_TENDER_REF,
	FIXTURE_WORKSPACE_ID,
	clear_bwmf_canonical_fixture,
	seed_bwmf_canonical_fixture,
)

ORG_B = "ORG-CAL-OTHER"
PARTY_B = "BIDDER-CAL-OTHER"


class TestBwmfPersistencePhase2(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fixture = seed_bwmf_canonical_fixture(clear=True)

	def tearDown(self):
		clear_bwmf_canonical_fixture()

	def test_teardown_and_deterministic_reseed(self):
		first = seed_bwmf_canonical_fixture(clear=True)
		second = seed_bwmf_canonical_fixture(clear=True)
		self.assertEqual(first["workspace_id"], second["workspace_id"])
		self.assertEqual(first["workspace_id"], FIXTURE_WORKSPACE_ID)
		ws = frappe.get_all(DT_WORKSPACE, filters={"workspace_id": FIXTURE_WORKSPACE_ID})
		self.assertEqual(len(ws), 1)
		self.assertEqual(first["compile_request"], second["compile_request"])

	def test_published_manifest_mutation_rejected(self):
		name = self.fixture["manifest"]
		doc = frappe.get_doc(DT_MANIFEST_VERSION, name)
		self.assertEqual(doc.lifecycle_state, "Published")
		doc.payload_json = '{"tampered": true}'
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_immutable_response_from_create_rejected(self):
		resp_name = bwmf.append_response_version(
			response_id="BWMF-CAL-RESP-IMM",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			section_key="price_schedule",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"x": 1},
			expected_version=0,
		)
		doc = frappe.get_doc(DT_RESPONSE_VERSION, resp_name)
		self.assertEqual(doc.state, "Immutable")
		doc.values_json = '{"x": 2}'
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_seal_binds_without_rewriting_response(self):
		resp_name = self.fixture["response"]
		before = frappe.db.get_value(DT_RESPONSE_VERSION, resp_name, ["values_json", "state"], as_dict=True)
		bwmf.seal_response_version(resp_name)
		after = frappe.db.get_value(DT_RESPONSE_VERSION, resp_name, ["values_json", "state"], as_dict=True)
		self.assertEqual(before.values_json, after.values_json)
		self.assertEqual(after.state, "Immutable")
		events = frappe.get_all(
			DT_AUDIT_EVENT,
			filters={"event_type": "response.version.bound_for_seal", "response_ref": ("like", "BWMF-CAL-RESP-001%")},
		)
		self.assertTrue(events)

	def test_sealed_evidence_mutation_rejected(self):
		doc = frappe.get_doc(DT_EVIDENCE_VERSION, self.fixture["evidence_version"])
		doc.content_digest = "sha256:" + ("e" * 64)
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_sealed_submission_mutation_rejected(self):
		sub = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-001",
			idempotency_key="BWMF-CAL-SUB-KEY-001",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
		)
		doc = frappe.get_doc(DT_SUBMISSION, sub)
		doc.snapshot_json = '{"tampered":1}'
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_append_only_response_versions(self):
		rid = "BWMF-CAL-RESP-APPEND"
		v1 = bwmf.append_response_version(
			response_id=rid,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			section_key="form_of_tender",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"n": 1},
			expected_version=0,
		)
		v2 = bwmf.append_response_version(
			response_id=rid,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			section_key="form_of_tender",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"n": 2},
			expected_version=1,
		)
		self.assertNotEqual(v1, v2)
		versions = frappe.get_all(
			DT_RESPONSE_VERSION, filters={"response_id": rid}, fields=["version"], order_by="version"
		)
		self.assertEqual([int(r.version) for r in versions], [1, 2])

	def test_duplicate_stable_id_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			bwmf.create_workspace(
				workspace_id=FIXTURE_WORKSPACE_ID,
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				published_tender_ref="X",
			)

	def test_optimistic_concurrency_conflict(self):
		rid = "BWMF-CAL-RESP-OCC"
		bwmf.append_response_version(
			response_id=rid,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			section_key="form_of_tender",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"n": 1},
			expected_version=0,
		)
		with self.assertRaises(frappe.ValidationError):
			bwmf.append_response_version(
				response_id=rid,
				workspace=self.fixture["workspace"],
				manifest_name=self.fixture["manifest"],
				section_key="form_of_tender",
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				values={"n": 2},
				expected_version=0,
			)

	def test_idempotency_same_key_same_request_returns_original(self):
		key = "BWMF-CAL-SUB-IDEM-KEY"
		a = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-IDEM-A",
			idempotency_key=key,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			total_amount="1000.00",
		)
		b = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-IDEM-A",
			idempotency_key=key,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			total_amount="1000.00",
		)
		self.assertEqual(a, b)
		self.assertEqual(
			frappe.db.count(
				DT_IDEMPOTENCY_RECORD,
				{"organization": FIXTURE_ORG, "operation": "seal_submission", "idempotency_key": key},
			),
			1,
		)

	def test_idempotency_same_key_different_request_fails(self):
		key = "BWMF-CAL-SUB-IDEM-CONFLICT"
		bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-IDEM-C1",
			idempotency_key=key,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			total_amount="1000.00",
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			bwmf.create_or_get_sealed_submission(
				submission_id="BWMF-CAL-SUB-IDEM-C2",
				idempotency_key=key,
				workspace=self.fixture["workspace"],
				manifest_name=self.fixture["manifest"],
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				total_amount="2000.00",
			)
		msg = (str(ctx.exception) + str(getattr(ctx.exception, "title", ""))).lower()
		self.assertTrue("idempotency" in msg or "fingerprint" in msg)

	def test_exact_decimal_round_trip_and_totals(self):
		self.assertEqual(decimal_to_storage_str(exact_decimal_roundtrip("0.1")), "0.10")
		self.assertEqual(decimal_to_storage_str(exact_decimal_roundtrip("0.2")), "0.20")
		self.assertEqual(decimal_to_storage_str(sum_money(["0.1", "0.2"])), "0.30")
		self.assertEqual(decimal_to_storage_str(exact_decimal_roundtrip("999999999999.99")), "999999999999.99")
		self.assertEqual(decimal_to_storage_str(exact_decimal_roundtrip("1.005")), "1.00")  # banker's
		self.assertEqual(decimal_to_storage_str(exact_decimal_roundtrip("1.015")), "1.02")
		self.assertEqual(bwmf.prove_money_totals(["0.10", "0.20", "1234.50"]), "1234.80")
		# Canonical money via price response values + sealed snapshot totals (not workspace sample).
		price_resp = bwmf.append_response_version(
			response_id="BWMF-CAL-RESP-PRICE",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			section_key="price_schedule",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"unit_price": "0.1", "line_total": "0.2", "grand_total": "1234.50"},
			expected_version=0,
		)
		values = json.loads(frappe.db.get_value(DT_RESPONSE_VERSION, price_resp, "values_json"))
		self.assertEqual(values["unit_price"], "0.10")
		self.assertEqual(values["line_total"], "0.20")
		self.assertEqual(values["grand_total"], "1234.50")
		sub = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-MONEY",
			idempotency_key="BWMF-CAL-SUB-MONEY-KEY",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			total_amount="1234.50",
		)
		snap = json.loads(frappe.db.get_value(DT_SUBMISSION, sub, "snapshot_json"))
		self.assertEqual(snap["totals"]["grand_total"], "1234.50")
		self.assertEqual(frappe.db.get_value(DT_SUBMISSION, sub, "total_amount"), "1234.50")
		with self.assertRaises(TypeError):
			exact_decimal_roundtrip(1.23)  # type: ignore[arg-type]
		with self.assertRaises(TypeError):
			serialize_manifest_money({"amount": 0.1})

	def test_audit_event_append_only(self):
		before = frappe.db.count(DT_AUDIT_EVENT)
		bwmf.append_response_version(
			response_id="BWMF-CAL-RESP-AUD",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			section_key="form_of_tender",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"n": 1},
			expected_version=0,
		)
		self.assertGreater(frappe.db.count(DT_AUDIT_EVENT), before)
		name = frappe.get_all(DT_AUDIT_EVENT, limit=1, pluck="name")[0]
		doc = frappe.get_doc(DT_AUDIT_EVENT, name)
		doc.event_type = "tampered"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_binding_retains_history_and_unique_active_key(self):
		first = self.fixture["binding"]
		manifest2 = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-NSSF-ERP-001-V2",
			manifest_version=2,
			lifecycle_state="Published",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=FIXTURE_ORG,
					payload={
				"manifest_id": "BWMF-CAL-NSSF-ERP-001-V2",
				"manifest_version": 2,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(),
			},
		)
		second = bwmf.bind_workspace_manifest(
			workspace=self.fixture["workspace"],
			manifest_name=manifest2,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
		)
		self.assertNotEqual(first, second)
		hist = frappe.get_doc(DT_WORKSPACE_BINDING, first)
		self.assertEqual(int(hist.is_active or 0), 0)
		self.assertFalse(hist.active_binding_key)
		active = frappe.get_all(
			DT_WORKSPACE_BINDING,
			filters={"workspace": self.fixture["workspace"], "is_active": 1},
			fields=["name", "active_binding_key"],
		)
		self.assertEqual(len(active), 1)
		self.assertEqual(active[0].active_binding_key, f"active:{self.fixture['workspace']}")

	def test_concurrent_workspace_binding_single_active(self):
		workspace = self.fixture["workspace"]
		m1 = self.fixture["manifest"]
		m2 = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-CONC-M2",
			manifest_version=1,
			lifecycle_state="Published",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=FIXTURE_ORG,
					payload={
				"manifest_id": "BWMF-CAL-CONC-M2",
				"manifest_version": 1,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(),
			},
		)
		frappe.db.commit()
		site = frappe.local.site
		errors: list[BaseException] = []
		results: list[str] = []

		def worker(manifest_name: str):
			try:
				frappe.init(site=site)
				frappe.connect()
				frappe.set_user("Administrator")
				name = bwmf.bind_workspace_manifest(
					workspace=workspace,
					manifest_name=manifest_name,
					organization=FIXTURE_ORG,
					bidder_party=FIXTURE_PARTY,
				)
				frappe.db.commit()
				results.append(name)
			except BaseException as exc:  # noqa: BLE001 — collect for assertion
				errors.append(exc)
				try:
					frappe.db.rollback()
				except Exception:
					pass
			finally:
				frappe.destroy()

		t1 = threading.Thread(target=worker, args=(m1,))
		t2 = threading.Thread(target=worker, args=(m2,))
		t1.start()
		t2.start()
		t1.join(timeout=30)
		t2.join(timeout=30)

		frappe.connect()
		frappe.set_user("Administrator")
		active = frappe.get_all(
			DT_WORKSPACE_BINDING,
			filters={"workspace": workspace, "is_active": 1},
			pluck="name",
		)
		self.assertEqual(len(active), 1, msg=f"active={active} results={results} errors={errors}")
		self.assertGreaterEqual(len(results), 1)
		# At most one failure (unique race); both may succeed serially under FOR UPDATE.
		self.assertLessEqual(len(errors), 1)

	def test_isolation_cross_org_and_party_rejected(self):
		ws_b = bwmf.create_workspace(
			workspace_id="WS-CAL-OTHER-001",
			organization=ORG_B,
			bidder_party=PARTY_B,
			published_tender_ref=FIXTURE_TENDER_REF,
		)
		with self.assertRaises(frappe.ValidationError):
			bwmf.append_response_version(
				response_id="BWMF-XORG-RESP",
				workspace=self.fixture["workspace"],
				manifest_name=self.fixture["manifest"],
				section_key="form_of_tender",
				organization=ORG_B,
				bidder_party=PARTY_B,
				values={"n": 1},
				expected_version=0,
			)
		with self.assertRaises(frappe.ValidationError):
			bwmf.link_evidence(
				evidence_version=self.fixture["evidence_version"],
				workspace=ws_b,
				task_ref="TASK-X",
				organization=ORG_B,
				bidder_party=PARTY_B,
			)
		with self.assertRaises(frappe.ValidationError):
			bwmf.create_or_get_sealed_submission(
				submission_id="BWMF-XORG-SUB",
				idempotency_key="BWMF-XORG-SUB-KEY",
				workspace=self.fixture["workspace"],
				manifest_name=self.fixture["manifest"],
				organization=ORG_B,
				bidder_party=FIXTURE_PARTY,
			)

	def test_closed_submission_snapshot_bindings(self):
		sub = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-SNAP",
			idempotency_key="BWMF-CAL-SUB-SNAP-KEY",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			total_amount="0.30",
		)
		raw = frappe.db.get_value(DT_SUBMISSION, sub, "snapshot_json")
		snap = json.loads(raw)
		assert_closed_submission_snapshot(snap)
		self.assertEqual(snap["totals"]["grand_total"], "0.30")
		self.assertEqual(snap["manifest"]["manifest_doc"], self.fixture["manifest"])
		self.assertTrue(snap["responses"])
		self.assertTrue(snap["jv_identity"]["party_ref"])

	def test_coverage_ledger_includes_all_required_concepts(self):
		assert_coverage_ledger_complete()
		concepts = set(load_coverage_ledger()["persistence_concepts"].keys())
		self.assertTrue(REQUIRED_PERSISTENCE_CONCEPTS.issubset(concepts))
		self.assertIn("audit_event", concepts)
		self.assertIn("idempotency_record", concepts)

	def test_fingerprint_stable(self):
		a = canonical_request_fingerprint({"a": 1, "b": [2, 3]})
		b = canonical_request_fingerprint({"b": [2, 3], "a": 1})
		self.assertEqual(a, b)
		self.assertTrue(a.startswith("sha256:"))
