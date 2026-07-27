# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 2B — final persistence lifecycle and relationship corrections."""

from __future__ import annotations
from kentender_procurement.tender_configurations.tests.helpers.bwmf_policy import explicit_submission_policy

import json
import unittest

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
	services as bwmf,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_COMPILE_REQUEST,
	DT_COMPILE_RUN,
	DT_EVIDENCE_VERSION,
	DT_IDEMPOTENCY_RECORD,
	DT_MANIFEST_VERSION,
	DT_RESPONSE_VERSION,
	DT_WORKSPACE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.snapshot import (
	build_submission_snapshot,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	FIXTURE_ORG,
	FIXTURE_PARTY,
	FIXTURE_TENDER_REF,
	clear_bwmf_canonical_fixture,
	seed_bwmf_canonical_fixture,
)

ORG_B = "ORG-CAL-OTHER"
PARTY_B = "BIDDER-CAL-OTHER"


class TestBwmfPersistencePhase2b(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fixture = seed_bwmf_canonical_fixture(clear=True)

	def tearDown(self):
		clear_bwmf_canonical_fixture()

	# --- compile-run lifecycle ---

	def test_compile_run_illegal_transition_rejected(self):
		run = self.fixture["compile_run"]
		# Fixture completes to Succeeded; create a fresh Queued run for illegal hop.
		req = self.fixture["compile_request"]
		queued = bwmf.create_compile_run(
			run_id="BWMF-CAL-RUN-ILLEGAL",
			idempotency_key="BWMF-CAL-RUN-ILLEGAL-KEY",
			compile_request=req,
			organization=FIXTURE_ORG,
		)
		self.assertEqual(frappe.db.get_value(DT_COMPILE_RUN, queued, "state"), "Queued")
		with self.assertRaises(frappe.ValidationError):
			bwmf.transition_compile_run(run_name=queued, new_state="Succeeded", organization=FIXTURE_ORG)

	def test_compile_run_terminal_mutation_rejected(self):
		run = self.fixture["compile_run"]
		self.assertEqual(frappe.db.get_value(DT_COMPILE_RUN, run, "state"), "Succeeded")
		doc = frappe.get_doc(DT_COMPILE_RUN, run)
		doc.state = "Failed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		doc = frappe.get_doc(DT_COMPILE_RUN, run)
		doc.append("stage_trace", {"stage": "X", "state": "tamper"})
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_compile_run_stage_trace_append_only(self):
		req = self.fixture["compile_request"]
		run = bwmf.create_compile_run(
			run_id="BWMF-CAL-RUN-TRACE",
			idempotency_key="BWMF-CAL-RUN-TRACE-KEY",
			compile_request=req,
			organization=FIXTURE_ORG,
		)
		bwmf.transition_compile_run(run_name=run, new_state="Running", organization=FIXTURE_ORG)
		bwmf.append_compile_stage_trace(run_name=run, stage="C01", state="ok", organization=FIXTURE_ORG)
		doc = frappe.get_doc(DT_COMPILE_RUN, run)
		doc.stage_trace[0].state = "tampered"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_compile_request_bindings_immutable_after_acceptance(self):
		req = frappe.get_doc(DT_COMPILE_REQUEST, self.fixture["compile_request"])
		self.assertEqual(req.status, "Accepted")
		req.input_bindings[0].object_ref = "TAMPERED"
		with self.assertRaises(frappe.ValidationError):
			req.save(ignore_permissions=True)

	# --- manifest lifecycle ---

	def test_manifest_supersession_preserves_payload_and_digest(self):
		name = self.fixture["manifest"]
		before = frappe.db.get_value(
			DT_MANIFEST_VERSION, name, ["payload_digest", "payload_json", "lifecycle_state"], as_dict=True
		)
		self.assertEqual(before.lifecycle_state, "Published")
		bwmf.supersede_manifest_version(name, organization=FIXTURE_ORG)
		after = frappe.db.get_value(
			DT_MANIFEST_VERSION, name, ["payload_digest", "payload_json", "lifecycle_state"], as_dict=True
		)
		self.assertEqual(after.lifecycle_state, "Superseded")
		self.assertEqual(after.payload_digest, before.payload_digest)
		self.assertEqual(after.payload_json, before.payload_json)
		doc = frappe.get_doc(DT_MANIFEST_VERSION, name)
		doc.payload_json = '{"tampered":true}'
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_manifest_payload_immutable_while_draft_to_published(self):
		m = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-DRAFT-M",
			manifest_version=1,
			lifecycle_state="Draft",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=FIXTURE_ORG,
					payload={
				"manifest_id": "BWMF-CAL-DRAFT-M",
				"manifest_version": 1,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(),
			},
		)
		doc = frappe.get_doc(DT_MANIFEST_VERSION, m)
		doc.payload_digest = "sha256:" + ("a" * 64)
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		bwmf.publish_manifest_version(m, organization=FIXTURE_ORG)
		self.assertEqual(frappe.db.get_value(DT_MANIFEST_VERSION, m, "lifecycle_state"), "Published")

	# --- evidence digest uniqueness ---

	def test_identical_content_digest_allowed_across_orgs(self):
		shared = "sha256:" + ("ab" * 32)
		ws_b = bwmf.create_workspace(
			workspace_id="WS-CAL-OTHER-EV",
			organization=ORG_B,
			bidder_party=PARTY_B,
			published_tender_ref=FIXTURE_TENDER_REF,
		)
		# Bind org B workspace to a published manifest (reuse fixture tender ref; own published copy)
		m_b = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-OTHER-M",
			manifest_version=1,
			lifecycle_state="Published",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=ORG_B,
					payload={
				"manifest_id": "BWMF-CAL-OTHER-M",
				"manifest_version": 1,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(),
			},
		)
		bwmf.bind_workspace_manifest(
			workspace=ws_b, manifest_name=m_b, organization=ORG_B, bidder_party=PARTY_B
		)
		item_a = bwmf.create_evidence_item(
			evidence_id="BWMF-EV-A",
			workspace=self.fixture["workspace"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
		)
		item_b = bwmf.create_evidence_item(
			evidence_id="BWMF-EV-B",
			workspace=ws_b,
			organization=ORG_B,
			bidder_party=PARTY_B,
		)
		v_a = bwmf.create_evidence_version(
			evidence_item=item_a,
			version=1,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			content_label="same-bytes",
			content_digest=shared,
		)
		v_b = bwmf.create_evidence_version(
			evidence_item=item_b,
			version=1,
			organization=ORG_B,
			bidder_party=PARTY_B,
			content_label="same-bytes",
			content_digest=shared,
		)
		self.assertNotEqual(v_a, v_b)
		self.assertEqual(frappe.db.get_value(DT_EVIDENCE_VERSION, v_a, "content_digest"), shared)
		self.assertEqual(frappe.db.get_value(DT_EVIDENCE_VERSION, v_b, "content_digest"), shared)

	# --- workspace service-only lifecycle ---

	def test_workspace_direct_state_mutation_rejected(self):
		doc = frappe.get_doc(DT_WORKSPACE, self.fixture["workspace"])
		doc.status = "submitted"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_workspace_service_submit_emits_audit(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.workspace_lifecycle import (
			WorkspaceReadinessSignals,
			WS_READY_TO_SUBMIT,
			WS_SUBMITTED,
		)

		sub = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-WS",
			idempotency_key="BWMF-CAL-SUB-WS-KEY",
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
		)
		bwmf.refresh_derived_workspace_status(
			workspace=self.fixture["workspace"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			signals=WorkspaceReadinessSignals(
				response_count=1,
				confirmations_complete=True,
				dependencies_ok=True,
				readiness_pass=True,
			),
		)
		self.assertEqual(
			frappe.db.get_value(DT_WORKSPACE, self.fixture["workspace"], "status"), WS_READY_TO_SUBMIT
		)
		bwmf.submit_workspace(
			workspace=self.fixture["workspace"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			active_submission=sub,
		)
		self.assertEqual(frappe.db.get_value(DT_WORKSPACE, self.fixture["workspace"], "status"), WS_SUBMITTED)
		events = frappe.get_all(
			"BWMF Audit Event",
			filters={"event_type": "workspace.submitted", "workspace": self.fixture["workspace"]},
		)
		self.assertTrue(events)

	# --- idempotency atomic insert-on-completion ---

	def test_idempotency_record_atomic_and_immutable(self):
		key = "BWMF-CAL-IDEM-ATOMIC"
		name = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-ATOMIC",
			idempotency_key=key,
			workspace=self.fixture["workspace"],
			manifest_name=self.fixture["manifest"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			total_amount="10.00",
		)
		rec = frappe.get_all(
			DT_IDEMPOTENCY_RECORD,
			filters={"organization": FIXTURE_ORG, "operation": "seal_submission", "idempotency_key": key},
			fields=["name", "request_fingerprint", "result_name"],
		)
		self.assertEqual(len(rec), 1)
		self.assertEqual(rec[0].result_name, name)
		self.assertTrue(rec[0].request_fingerprint.startswith("sha256:"))
		doc = frappe.get_doc(DT_IDEMPOTENCY_RECORD, rec[0].name)
		doc.request_fingerprint = "sha256:" + ("f" * 64)
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	# --- relationship integrity negatives ---
	#
	# Frappe Link fields are not native DB foreign keys. Relationship integrity is
	# enforced server-side in persistence services + DocType validate hooks
	# (titles BWMF_REF_MISSING, BWMF_CROSS_* , BWMF_SNAPSHOT_BINDING_MISMATCH,
	# BWMF_RESPONSE_DIGEST_MISMATCH, BWMF_ISOLATION_VIOLATION).

	def test_missing_linked_record_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			bwmf.create_compile_run(
				run_id="BWMF-CAL-RUN-MISSING",
				idempotency_key="BWMF-CAL-RUN-MISSING-KEY",
				compile_request="DOES-NOT-EXIST",
				organization=FIXTURE_ORG,
			)
		with self.assertRaises(frappe.ValidationError):
			bwmf.link_evidence(
				evidence_version="DOES-NOT-EXIST",
				workspace=self.fixture["workspace"],
				task_ref="T1",
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
			)

	def test_response_wrong_workspace_or_manifest_rejected(self):
		ws_b = bwmf.create_workspace(
			workspace_id="WS-CAL-WRONG-RESP",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			published_tender_ref=FIXTURE_TENDER_REF,
		)
		m2 = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-WRONG-M",
			manifest_version=1,
			lifecycle_state="Published",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=FIXTURE_ORG,
					payload={
				"manifest_id": "BWMF-CAL-WRONG-M",
				"manifest_version": 1,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(),
			},
		)
		bwmf.bind_workspace_manifest(
			workspace=ws_b, manifest_name=m2, organization=FIXTURE_ORG, bidder_party=FIXTURE_PARTY
		)
		# Wrong manifest for fixture workspace (active binding is fixture manifest)
		with self.assertRaises(frappe.ValidationError):
			bwmf.append_response_version(
				response_id="BWMF-WRONG-MANIFEST-RESP",
				workspace=self.fixture["workspace"],
				manifest_name=m2,
				section_key="form_of_tender",
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				values={"n": 1},
				expected_version=0,
			)

	def test_evidence_link_cross_workspace_rejected(self):
		ws_b = bwmf.create_workspace(
			workspace_id="WS-CAL-EV-CROSS",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			published_tender_ref=FIXTURE_TENDER_REF,
		)
		m2 = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-EV-CROSS-M",
			manifest_version=1,
			lifecycle_state="Published",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=FIXTURE_ORG,
					payload={
				"manifest_id": "BWMF-CAL-EV-CROSS-M",
				"manifest_version": 1,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(),
			},
		)
		bwmf.bind_workspace_manifest(
			workspace=ws_b, manifest_name=m2, organization=FIXTURE_ORG, bidder_party=FIXTURE_PARTY
		)
		with self.assertRaises(frappe.ValidationError):
			bwmf.link_evidence(
				evidence_version=self.fixture["evidence_version"],
				workspace=ws_b,
				task_ref="TASK-CROSS",
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
			)

	def test_confirmation_wrong_response_version_or_digest_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			bwmf.create_confirmation(
				confirmation_id="BWMF-CONF-MISSING",
				workspace=self.fixture["workspace"],
				response_id="NO-SUCH-RESP",
				response_version=99,
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
			)
		resp = frappe.db.get_value(
			DT_RESPONSE_VERSION,
			self.fixture["response"],
			["response_id", "version"],
			as_dict=True,
		)
		with self.assertRaises(frappe.ValidationError):
			bwmf.create_confirmation(
				confirmation_id="BWMF-CONF-BAD-DIGEST",
				workspace=self.fixture["workspace"],
				response_id=resp.response_id,
				response_version=int(resp.version),
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				expected_response_digest="sha256:" + ("0" * 64),
			)

	def test_submission_snapshot_mismatched_binding_rejected(self):
		ws = frappe.db.get_value(DT_WORKSPACE, self.fixture["workspace"], "workspace_id")
		bad = build_submission_snapshot(
			submission_id="BWMF-CAL-SUB-BAD-SNAP",
			submission_version=1,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			workspace_id=ws,
			manifest={
				"manifest_id": "WRONG",
				"manifest_version": 1,
				"payload_digest": "sha256:" + ("c" * 64),
				"manifest_doc": self.fixture["manifest"],
			},
			responses=[
				{
					"response_id": "NOPE",
					"version": 1,
					"response_digest": "sha256:" + ("d" * 64),
					"section_key": "form_of_tender",
				}
			],
			totals={"grand_total": "1.00"},
		)
		with self.assertRaises(frappe.ValidationError):
			bwmf.create_or_get_sealed_submission(
				submission_id="BWMF-CAL-SUB-BAD-SNAP",
				idempotency_key="BWMF-CAL-SUB-BAD-SNAP-KEY",
				workspace=self.fixture["workspace"],
				manifest_name=self.fixture["manifest"],
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				snapshot=bad,
				total_amount="1.00",
			)
