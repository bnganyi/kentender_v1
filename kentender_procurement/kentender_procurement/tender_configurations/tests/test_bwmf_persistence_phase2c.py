# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 2 — final lifecycle alignment (workspace status, manifest cancel, totals)."""

from __future__ import annotations
from kentender_procurement.tender_configurations.tests.helpers.bwmf_policy import explicit_submission_policy

import json
import unittest

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
	services as bwmf,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_MANIFEST_VERSION,
	DT_WORKSPACE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.snapshot import (
	build_submission_snapshot,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.workspace_lifecycle import (
	WS_CLOSED,
	WS_DRAFT,
	WS_IN_PROGRESS,
	WS_NEEDS_ATTENTION,
	WS_NOT_STARTED,
	WS_READY_TO_SUBMIT,
	WS_SUBMITTED,
	WS_WITHDRAWN,
	WorkspaceReadinessSignals,
	derive_workspace_status,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	FIXTURE_ORG,
	FIXTURE_PARTY,
	FIXTURE_TENDER_REF,
	clear_bwmf_canonical_fixture,
	seed_bwmf_canonical_fixture,
)


class TestBwmfPersistencePhase2c(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fixture = seed_bwmf_canonical_fixture(clear=True)

	def tearDown(self):
		clear_bwmf_canonical_fixture()

	def test_open_status_rejected(self):
		doc = frappe.get_doc(DT_WORKSPACE, self.fixture["workspace"])
		self.assertNotEqual(doc.status, "Open")
		self.assertEqual(doc.status, WS_NOT_STARTED)
		doc.status = "Open"
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.save(ignore_permissions=True)
		self.assertIn("FORBIDDEN", str(getattr(ctx.exception, "title", "")) + str(ctx.exception).upper())

	def test_direct_preparatory_status_mutation_rejected(self):
		doc = frappe.get_doc(DT_WORKSPACE, self.fixture["workspace"])
		doc.status = WS_DRAFT
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		doc = frappe.get_doc(DT_WORKSPACE, self.fixture["workspace"])
		doc.status = WS_READY_TO_SUBMIT
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_derived_readiness_state_calculation_boundary(self):
		self.assertEqual(derive_workspace_status(WorkspaceReadinessSignals()), WS_NOT_STARTED)
		self.assertEqual(
			derive_workspace_status(WorkspaceReadinessSignals(response_count=1, has_incomplete_response=True)),
			WS_DRAFT,
		)
		self.assertEqual(
			derive_workspace_status(WorkspaceReadinessSignals(response_count=2, has_incomplete_response=False)),
			WS_IN_PROGRESS,
		)
		self.assertEqual(
			derive_workspace_status(WorkspaceReadinessSignals(response_count=1, has_blockers=True)),
			WS_NEEDS_ATTENTION,
		)
		self.assertEqual(
			derive_workspace_status(
				WorkspaceReadinessSignals(
					response_count=1,
					confirmations_complete=True,
					dependencies_ok=True,
					readiness_pass=True,
				)
			),
			WS_READY_TO_SUBMIT,
		)
		# Derivation never returns transactional statuses
		self.assertNotIn(
			derive_workspace_status(
				WorkspaceReadinessSignals(
					response_count=1,
					confirmations_complete=True,
					dependencies_ok=True,
					readiness_pass=True,
				)
			),
			{WS_SUBMITTED, WS_WITHDRAWN, WS_CLOSED},
		)
		status = bwmf.refresh_derived_workspace_status(
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
		self.assertEqual(status, WS_READY_TO_SUBMIT)
		self.assertEqual(frappe.db.get_value(DT_WORKSPACE, self.fixture["workspace"], "status"), WS_READY_TO_SUBMIT)

	def test_policy_controlled_withdrawal(self):
		# Fixture manifest denies withdrawal by default
		sub = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-WD-DENY",
			idempotency_key="BWMF-CAL-SUB-WD-DENY-KEY",
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
		bwmf.submit_workspace(
			workspace=self.fixture["workspace"],
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			active_submission=sub,
		)
		with self.assertRaises(frappe.ValidationError):
			bwmf.withdraw_workspace(
				workspace=self.fixture["workspace"],
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
			)

		# Policy-permitted path on a fresh workspace
		ws2 = bwmf.create_workspace(
			workspace_id="WS-CAL-WD-OK",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			published_tender_ref=FIXTURE_TENDER_REF,
		)
		m2 = bwmf.create_manifest_version(
			manifest_id="BWMF-CAL-WD-M",
			manifest_version=1,
			lifecycle_state="Published",
			published_tender_ref=FIXTURE_TENDER_REF,
			organization=FIXTURE_ORG,
					payload={
				"manifest_id": "BWMF-CAL-WD-M",
				"manifest_version": 1,
				"sections": [{"section_key": "form_of_tender"}],
				"submission_policy": explicit_submission_policy(withdrawal_mode="permitted_before_deadline"),
			},
		)
		bwmf.bind_workspace_manifest(
			workspace=ws2, manifest_name=m2, organization=FIXTURE_ORG, bidder_party=FIXTURE_PARTY
		)
		bwmf.append_response_version(
			response_id="BWMF-WD-RESP",
			workspace=ws2,
			manifest_name=m2,
			section_key="form_of_tender",
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			values={"ok": 1},
			expected_version=0,
		)
		sub2 = bwmf.create_or_get_sealed_submission(
			submission_id="BWMF-CAL-SUB-WD-OK",
			idempotency_key="BWMF-CAL-SUB-WD-OK-KEY",
			workspace=ws2,
			manifest_name=m2,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
		)
		bwmf.refresh_derived_workspace_status(
			workspace=ws2,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			signals=WorkspaceReadinessSignals(
				response_count=1,
				confirmations_complete=True,
				dependencies_ok=True,
				readiness_pass=True,
			),
		)
		bwmf.submit_workspace(
			workspace=ws2,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			active_submission=sub2,
		)
		bwmf.withdraw_workspace(workspace=ws2, organization=FIXTURE_ORG, bidder_party=FIXTURE_PARTY)
		self.assertEqual(frappe.db.get_value(DT_WORKSPACE, ws2, "status"), WS_WITHDRAWN)
		bwmf.close_workspace(workspace=ws2, organization=FIXTURE_ORG, bidder_party=FIXTURE_PARTY)
		self.assertEqual(frappe.db.get_value(DT_WORKSPACE, ws2, "status"), WS_CLOSED)

	def test_manifest_cancellation_without_payload_mutation(self):
		name = self.fixture["manifest"]
		before = frappe.db.get_value(
			DT_MANIFEST_VERSION, name, ["payload_digest", "payload_json", "lifecycle_state"], as_dict=True
		)
		self.assertEqual(before.lifecycle_state, "Published")
		bwmf.cancel_manifest_version(name, organization=FIXTURE_ORG)
		after = frappe.db.get_value(
			DT_MANIFEST_VERSION, name, ["payload_digest", "payload_json", "lifecycle_state"], as_dict=True
		)
		self.assertEqual(after.lifecycle_state, "Cancelled")
		self.assertEqual(after.payload_digest, before.payload_digest)
		self.assertEqual(after.payload_json, before.payload_json)
		events = frappe.get_all(
			"BWMF Audit Event",
			filters={"event_type": "manifest.cancelled", "manifest_doc": name},
		)
		self.assertTrue(events)
		doc = frappe.get_doc(DT_MANIFEST_VERSION, name)
		doc.payload_json = '{"tampered":true}'
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_total_mismatch_rejected(self):
		ws = frappe.db.get_value(DT_WORKSPACE, self.fixture["workspace"], "workspace_id")
		snap = build_submission_snapshot(
			submission_id="BWMF-CAL-SUB-TOT-MIS",
			submission_version=1,
			organization=FIXTURE_ORG,
			bidder_party=FIXTURE_PARTY,
			workspace_id=ws,
			manifest={
				"manifest_id": "X",
				"manifest_version": 1,
				"payload_digest": frappe.db.get_value(DT_MANIFEST_VERSION, self.fixture["manifest"], "payload_digest"),
				"manifest_doc": self.fixture["manifest"],
			},
			responses=[
				{
					"response_id": r.response_id,
					"version": int(r.version),
					"response_digest": r.response_digest,
					"section_key": r.section_key,
				}
				for r in frappe.get_all(
					"BWMF Response Version",
					filters={"workspace": self.fixture["workspace"]},
					fields=["response_id", "version", "response_digest", "section_key"],
				)
			],
			totals={"grand_total": "1.00"},
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			bwmf.create_or_get_sealed_submission(
				submission_id="BWMF-CAL-SUB-TOT-MIS",
				idempotency_key="BWMF-CAL-SUB-TOT-MIS-KEY",
				workspace=self.fixture["workspace"],
				manifest_name=self.fixture["manifest"],
				organization=FIXTURE_ORG,
				bidder_party=FIXTURE_PARTY,
				snapshot=snap,
				total_amount="2.00",
			)
		msg = (str(ctx.exception) + str(getattr(ctx.exception, "title", ""))).upper()
		self.assertTrue("TOTAL" in msg or "MISMATCH" in msg)
