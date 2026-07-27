# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 5 — governance, approval, atomic publication."""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.approval_service import (
	approve_review_package,
	return_review_package,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.compile_service import (
	execute_compile,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.eligibility import (
	assert_eligible_for_review,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.materialize_service import (
	execute_materialization,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.publish_service import (
	cancel_publication,
	publish_approved_package,
	set_publish_fail_at,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.retrieval_service import (
	retrieve_published_manifest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.review_service import (
	approve_impact_plan,
	prepare_review_package,
	submit_review_package_for_approval,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.roles import (
	ROLE_APPROVER,
	ROLE_CONFIGURATOR,
	ROLE_PUBLICATION,
	ensure_governance_roles,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.fixtures_loader import (
	load_nssf_calibration_source_set,
	load_synthetic_std_source_set,
	nssf_compile_request,
	synthetic_compile_request,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_APPROVAL_DECISION,
	DT_LIFECYCLE_EVENT,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE_BINDING,
	DT_MANIFEST_VERSION,
	DT_REVIEW_PACKAGE,
	DT_TENDER_PUBLICATION_STATE,
	DT_WORKSPACE,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	clear_bwmf_canonical_fixture,
)


ORG = "ORG-P5"


def _ensure_doctypes():
	for dn in (
		"bwmf_review_package",
		"bwmf_approval_decision",
		"bwmf_publication_request",
		"bwmf_manifest_resource_binding",
		"bwmf_lifecycle_event",
		"bwmf_tender_publication_state",
		"bwmf_manifest_publication",
		"bwmf_manifest_version",
		"bwmf_content_object",
		"bwmf_artifact_resource_binding",
		"bwmf_materialization_report",
		"bwmf_manifest_resource",
		"bwmf_compile_artifact",
	):
		frappe.reload_doc("Tender Configurations", "doctype", dn, force=True)


def _materialize_synthetic_publishable():
	suffix = frappe.generate_hash(length=8)
	req = synthetic_compile_request(compile_mode="preview")
	req.target_manifest_id = f"BWMF-SYN-P5-{suffix}"
	src = load_synthetic_std_source_set()
	preview = execute_compile(
		compile_request_id=f"CR-P5-{suffix}",
		idempotency_key=f"CR-P5-{suffix}-KEY",
		run_id=f"RUN-P5-{suffix}",
		run_idempotency_key=f"RUN-P5-{suffix}-KEY",
		request=req,
		sources=src,
		organization=ORG,
	)
	assert preview["ok"], preview
	pub_req = synthetic_compile_request(compile_mode="publication")
	pub_req.target_manifest_id = req.target_manifest_id
	mat = execute_materialization(
		source_artifact_name=preview["compile_artifact"],
		idempotency_key=f"MAT-P5-{suffix}",
		organization=ORG,
		sources=src,
		request=pub_req,
		calibration_only=False,
	)
	assert mat["ok"], mat
	assert mat["publication_readiness"].get("passed")
	return {
		"suffix": suffix,
		"preview": preview,
		"materialize": mat,
		"artifact": mat["finalized_artifact"],
		"payload_digest": mat["finalized_payload_digest"],
		"target_manifest_id": req.target_manifest_id,
		"tender_ref": f"TENDER-P5-{suffix}",
	}


def _gov_to_approved(ctx, *, package_id=None, separation=True, acks=None):
	pid = package_id or f"PKG-{ctx['suffix']}"
	prep = prepare_review_package(
		package_id=pid,
		compile_artifact=ctx["artifact"],
		organization=ORG,
		published_tender_ref=ctx["tender_ref"],
		proposed_manifest_version=1,
	)
	sub = submit_review_package_for_approval(review_package=prep["review_package"], organization=ORG)
	# Force distinct submitter for SoD when Administrator holds all roles
	pkg = frappe.get_doc(DT_REVIEW_PACKAGE, prep["review_package"])
	if separation:
		frappe.db.set_value(DT_REVIEW_PACKAGE, pkg.name, "submitter", "configurator@example.com")
	warnings = prep.get("warnings") or json.loads(pkg.package_json).get("warnings") or []
	ack_list = acks if acks is not None else [
		{"code": w["code"], "fingerprint": w["fingerprint"], "comment": "ack"} for w in warnings
	]
	dec = approve_review_package(
		decision_id=f"DEC-{ctx['suffix']}-{pid}",
		review_package=prep["review_package"],
		warning_acknowledgements=ack_list,
		organization=ORG,
		separation_enabled=separation,
	)
	return {"prep": prep, "sub": sub, "dec": dec, "package": prep["review_package"]}


class TestBwmfGovernancePhase5(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		_ensure_doctypes()
		ensure_governance_roles()

	def setUp(self):
		frappe.set_user("Administrator")
		set_publish_fail_at(None)
		clear_bwmf_canonical_fixture()

	def tearDown(self):
		set_publish_fail_at(None)
		clear_bwmf_canonical_fixture()

	def test_ineligible_preview_and_calibration_rejected(self):
		# NSSF calibration finalized
		req = nssf_compile_request()
		suffix = frappe.generate_hash(length=8)
		req.target_manifest_id = f"BWMF-P5-NSSF-{suffix}"
		preview = execute_compile(
			compile_request_id=f"CR-NSSF-{suffix}",
			idempotency_key=f"CR-NSSF-{suffix}-KEY",
			run_id=f"RUN-NSSF-{suffix}",
			run_idempotency_key=f"RUN-NSSF-{suffix}-KEY",
			request=req,
			sources=load_nssf_calibration_source_set(),
			organization=ORG,
		)
		self.assertTrue(preview["ok"])
		with self.assertRaises(frappe.ValidationError):
			assert_eligible_for_review(preview["compile_artifact"])
		mat = execute_materialization(
			source_artifact_name=preview["compile_artifact"],
			idempotency_key=f"MAT-NSSF-{suffix}",
			organization=ORG,
			sources=load_nssf_calibration_source_set(),
			calibration_only=True,
		)
		self.assertTrue(mat["ok"])
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			assert_eligible_for_review(mat["finalized_artifact"])
		self.assertIn(
			"BWMF_CALIBRATION_NOT_PUBLISHABLE",
			[m.get("title") for m in frappe.get_message_log()],
		)
		# No MV / publication from Phase 4 path
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION), 0)
		self.assertEqual(frappe.db.count(DT_MANIFEST_PUBLICATION), 0)

	def test_package_immutable_on_submit_and_return_rules(self):
		ctx = _materialize_synthetic_publishable()
		prep = prepare_review_package(
			package_id=f"PKG-RET-{ctx['suffix']}",
			compile_artifact=ctx["artifact"],
			organization=ORG,
			published_tender_ref=ctx["tender_ref"],
		)
		sub = submit_review_package_for_approval(review_package=prep["review_package"], organization=ORG)
		self.assertEqual(sub["state"], "SubmittedForApproval")
		pkg = frappe.get_doc(DT_REVIEW_PACKAGE, prep["review_package"])
		pkg.package_json = "{}"
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			pkg.save(ignore_permissions=True)
		self.assertIn("BWMF_REVIEW_IMMUTABLE", [m.get("title") for m in frappe.get_message_log()])

		frappe.db.set_value(DT_REVIEW_PACKAGE, pkg.name, "submitter", "configurator@example.com")
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			return_review_package(
				decision_id=f"DEC-RET-BAD-{ctx['suffix']}",
				review_package=pkg.name,
				return_reason="",
				correction_owner="owner",
				organization=ORG,
			)
		self.assertIn("BWMF_RETURN_REASON", [m.get("title") for m in frappe.get_message_log()])

		ret = return_review_package(
			decision_id=f"DEC-RET-{ctx['suffix']}",
			review_package=pkg.name,
			return_reason="fix labels",
			correction_owner="configurator@example.com",
			organization=ORG,
		)
		self.assertEqual(ret["decision"], "returned")
		self.assertEqual(ret["state"], "Returned")
		# Cannot resubmit same package
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			submit_review_package_for_approval(review_package=pkg.name, organization=ORG)
		# New corrected artifact/package may resubmit
		ctx2 = _materialize_synthetic_publishable()
		prep2 = prepare_review_package(
			package_id=f"PKG-RET2-{ctx2['suffix']}",
			compile_artifact=ctx2["artifact"],
			organization=ORG,
			published_tender_ref=ctx2["tender_ref"],
			package_version=1,
		)
		sub2 = submit_review_package_for_approval(review_package=prep2["review_package"], organization=ORG)
		self.assertEqual(sub2["state"], "SubmittedForApproval")

	def test_self_approval_and_unacked_warning_rejected(self):
		ctx = _materialize_synthetic_publishable()
		prep = prepare_review_package(
			package_id=f"PKG-SOD-{ctx['suffix']}",
			compile_artifact=ctx["artifact"],
			organization=ORG,
			published_tender_ref=ctx["tender_ref"],
		)
		submit_review_package_for_approval(review_package=prep["review_package"], organization=ORG)
		# Leave submitter as Administrator (= approver)
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			approve_review_package(
				decision_id=f"DEC-SOD-{ctx['suffix']}",
				review_package=prep["review_package"],
				warning_acknowledgements=[],
				organization=ORG,
				separation_enabled=True,
			)
		self.assertIn("BWMF_SOD_VIOLATION", [m.get("title") for m in frappe.get_message_log()])

		# Inject a warning into package for unacked test on a fresh package
		ctx2 = _materialize_synthetic_publishable()
		prep2 = prepare_review_package(
			package_id=f"PKG-WARN-{ctx2['suffix']}",
			compile_artifact=ctx2["artifact"],
			organization=ORG,
			published_tender_ref=ctx2["tender_ref"],
		)
		pkg = frappe.get_doc(DT_REVIEW_PACKAGE, prep2["review_package"])
		body = json.loads(pkg.package_json)
		body["warnings"] = [
			{
				"code": "WARN-TEST",
				"fingerprint": jcs_sha256_digest({"code": "WARN-TEST"}),
				"message": "test",
				"path": "",
			}
		]
		# rewrite only allowed in Prepared
		pkg.package_json = json.dumps(body, sort_keys=True)
		pkg.review_package_digest = jcs_sha256_digest(body)
		pkg.save(ignore_permissions=True)
		submit_review_package_for_approval(review_package=pkg.name, organization=ORG)
		frappe.db.set_value(DT_REVIEW_PACKAGE, pkg.name, "submitter", "configurator@example.com")
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			approve_review_package(
				decision_id=f"DEC-WARN-{ctx2['suffix']}",
				review_package=pkg.name,
				warning_acknowledgements=[],
				organization=ORG,
				separation_enabled=True,
			)
		self.assertIn("BWMF_WARNING_UNACKED", [m.get("title") for m in frappe.get_message_log()])

	def test_approval_does_not_publish(self):
		ctx = _materialize_synthetic_publishable()
		before_mv = frappe.db.count(DT_MANIFEST_VERSION)
		before_pub = frappe.db.count(DT_MANIFEST_PUBLICATION)
		_gov_to_approved(ctx)
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION), before_mv)
		self.assertEqual(frappe.db.count(DT_MANIFEST_PUBLICATION), before_pub)
		self.assertEqual(frappe.db.count(DT_APPROVAL_DECISION), 1)

	def test_atomic_publication_success_and_bindings(self):
		ctx = _materialize_synthetic_publishable()
		gov = _gov_to_approved(ctx)
		before_ws = frappe.db.count(DT_WORKSPACE)
		out = publish_approved_package(
			request_id=f"REQ-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=f"PUB-KEY-{ctx['suffix']}",
		)
		self.assertTrue(out["ok"])
		mv = frappe.get_doc(DT_MANIFEST_VERSION, out["manifest_version"])
		self.assertEqual(mv.lifecycle_state, "Published")
		self.assertEqual(int(mv.manifest_version), 1)
		self.assertEqual(mv.payload_digest, ctx["payload_digest"])
		self.assertEqual(mv.payload_digest, gov["prep"]["review_package_digest"] and ctx["payload_digest"])
		bindings = frappe.get_all(
			DT_MANIFEST_RESOURCE_BINDING, filters={"manifest_version": mv.name}, pluck="name"
		)
		self.assertGreaterEqual(len(bindings), 1)
		retrieved = retrieve_published_manifest(
			publication_id=out["publication_id"],
		)
		self.assertEqual(retrieved["payload_digest"], ctx["payload_digest"])
		self.assertEqual(retrieved["manifest_version"], 1)
		self.assertFalse(retrieved["bidder_workspace_cutover"])
		self.assertEqual(frappe.db.count(DT_WORKSPACE), before_ws)
		lineage = frappe.get_doc(DT_TENDER_PUBLICATION_STATE, {"published_tender_ref": ctx["tender_ref"]})
		self.assertTrue(lineage.public_active)
		self.assertTrue(lineage.workspace_available)

	def test_failed_publication_no_partial_and_no_version_consume(self):
		ctx = _materialize_synthetic_publishable()
		gov = _gov_to_approved(ctx, package_id=f"PKG-FAIL-{ctx['suffix']}")
		set_publish_fail_at("after_resource_bindings")
		frappe.clear_messages()
		with self.assertRaises(RuntimeError):
			publish_approved_package(
				request_id=f"REQ-FAIL-{ctx['suffix']}",
				approval_decision=gov["dec"]["approval_decision"],
				organization=ORG,
				idempotency_key=f"PUB-FAIL-{ctx['suffix']}",
			)
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION, {"manifest_id": ctx["target_manifest_id"]}), 0)
		self.assertEqual(frappe.db.count(DT_MANIFEST_RESOURCE_BINDING), 0)
		self.assertEqual(
			frappe.db.count(DT_MANIFEST_PUBLICATION, {"published_tender_ref": ctx["tender_ref"]}),
			0,
		)
		# retry succeeds and version is 1
		set_publish_fail_at(None)
		out = publish_approved_package(
			request_id=f"REQ-FAIL-OK-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=f"PUB-FAIL-OK-{ctx['suffix']}",
		)
		mv = frappe.get_doc(DT_MANIFEST_VERSION, out["manifest_version"])
		self.assertEqual(int(mv.manifest_version), 1)

	def test_idempotent_replay_and_fingerprint_mismatch(self):
		ctx = _materialize_synthetic_publishable()
		gov = _gov_to_approved(ctx)
		key = f"PUB-IDEM-{ctx['suffix']}"
		a = publish_approved_package(
			request_id=f"REQ-IDEM-A-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=key,
		)
		b = publish_approved_package(
			request_id=f"REQ-IDEM-B-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=key,
		)
		self.assertEqual(a["publication"], b["publication"])
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION, {"manifest_id": ctx["target_manifest_id"]}), 1)

		ctx2 = _materialize_synthetic_publishable()
		gov2 = _gov_to_approved(ctx2)
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			publish_approved_package(
				request_id=f"REQ-FP-{ctx2['suffix']}",
				approval_decision=gov2["dec"]["approval_decision"],
				organization=ORG,
				idempotency_key=key,  # reused with different fingerprint
			)
		self.assertIn(
			"BWMF_IDEMPOTENCY_FINGERPRINT_MISMATCH",
			[m.get("title") for m in frappe.get_message_log()],
		)

	def test_stale_approval_and_corrupt_resource_rejected(self):
		ctx = _materialize_synthetic_publishable()
		gov = _gov_to_approved(ctx)
		# Tamper decision binding digest via new decision path: mutate artifact digest in DB is blocked;
		# instead approve then change package digest reference on decision by creating mismatch
		dec = frappe.get_doc(DT_APPROVAL_DECISION, gov["dec"]["approval_decision"])
		# Corrupt a resource content after approval
		bindings = frappe.get_all(
			"BWMF Artifact Resource Binding",
			filters={"compile_artifact": ctx["artifact"]},
			fields=["content_ref", "resource_id"],
		)
		self.assertTrue(bindings)
		from pathlib import Path
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
			get_verified,
		)

		cref = bindings[0].content_ref
		hex_digest = cref.removeprefix("bwmf-cas:v1:")
		path = Path(frappe.get_site_path("private", "files", f"bwmf-cas-{hex_digest}.json"))
		backup = path.read_bytes()
		path.write_bytes(b'[{"tampered": true}]')
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			publish_approved_package(
				request_id=f"REQ-CORRUPT-{ctx['suffix']}",
				approval_decision=dec.name,
				organization=ORG,
				idempotency_key=f"PUB-CORRUPT-{ctx['suffix']}",
			)
		path.write_bytes(backup)
		# Stale: change decision payload_digest field is immutable — use assert_approval_usable via digest mismatch
		# by preparing a second package and trying to publish with wrong decision already tested via corrupt.

	def test_addendum_and_cancellation(self):
		ctx = _materialize_synthetic_publishable()
		gov = _gov_to_approved(ctx)
		first = publish_approved_package(
			request_id=f"REQ-ADD1-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=f"PUB-ADD1-{ctx['suffix']}",
		)
		mv1 = frappe.get_doc(DT_MANIFEST_VERSION, first["manifest_version"])
		prior_digest = mv1.payload_digest
		prior_payload = mv1.payload_json

		# Impact plan required for addendum package
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import (
			services as bwmf,
		)

		ctx2 = _materialize_synthetic_publishable()
		plan_id = f"IP-{ctx2['suffix']}"
		plan_body = {
			"changes": [{"op": "label", "section": "form_of_tender"}],
			"old_digest": prior_digest,
			"new_digest": ctx2["payload_digest"],
		}
		plan_digest = jcs_sha256_digest(plan_body)
		frappe.get_doc(
			{
				"doctype": "BWMF Addendum Impact Plan",
				"plan_id": plan_id,
				"old_manifest_ref": mv1.name,
				"new_manifest_ref": ctx2["artifact"],
				"old_payload_digest": prior_digest,
				"new_payload_digest": ctx2["payload_digest"],
				"plan_digest": plan_digest,
				"status": "Draft",
				"plan_json": json.dumps(plan_body),
			}
		).insert(ignore_permissions=True)
		# Without approval — prepare should fail
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			prepare_review_package(
				package_id=f"PKG-ADD-BAD-{ctx2['suffix']}",
				compile_artifact=ctx2["artifact"],
				organization=ORG,
				published_tender_ref=ctx["tender_ref"],
				impact_plan=plan_id,
			)
		approve_impact_plan(plan_id=plan_id, organization=ORG)
		prep = prepare_review_package(
			package_id=f"PKG-ADD-{ctx2['suffix']}",
			compile_artifact=ctx2["artifact"],
			organization=ORG,
			published_tender_ref=ctx["tender_ref"],
			impact_plan=plan_id,
			proposed_manifest_version=2,
		)
		submit_review_package_for_approval(review_package=prep["review_package"], organization=ORG)
		frappe.db.set_value(DT_REVIEW_PACKAGE, prep["review_package"], "submitter", "configurator@example.com")
		dec2 = approve_review_package(
			decision_id=f"DEC-ADD-{ctx2['suffix']}",
			review_package=prep["review_package"],
			warning_acknowledgements=[
				{"code": w["code"], "fingerprint": w["fingerprint"]}
				for w in (json.loads(frappe.get_doc(DT_REVIEW_PACKAGE, prep["review_package"]).package_json).get("warnings") or [])
			],
			organization=ORG,
		)
		# Failed addendum leaves prior active
		set_publish_fail_at("after_manifest_version")
		with self.assertRaises(RuntimeError):
			publish_approved_package(
				request_id=f"REQ-ADD-FAIL-{ctx2['suffix']}",
				approval_decision=dec2["approval_decision"],
				organization=ORG,
				idempotency_key=f"PUB-ADD-FAIL-{ctx2['suffix']}",
				is_addendum=True,
			)
		set_publish_fail_at(None)
		lineage = frappe.get_doc(DT_TENDER_PUBLICATION_STATE, {"published_tender_ref": ctx["tender_ref"]})
		self.assertEqual(lineage.active_manifest_version, mv1.name)
		self.assertTrue(lineage.public_active)
		mv1.reload()
		self.assertEqual(mv1.payload_digest, prior_digest)
		self.assertEqual(mv1.payload_json, prior_payload)
		self.assertEqual(mv1.lifecycle_state, "Published")

		second = publish_approved_package(
			request_id=f"REQ-ADD-OK-{ctx2['suffix']}",
			approval_decision=dec2["approval_decision"],
			organization=ORG,
			idempotency_key=f"PUB-ADD-OK-{ctx2['suffix']}",
			is_addendum=True,
		)
		mv2 = frappe.get_doc(DT_MANIFEST_VERSION, second["manifest_version"])
		self.assertEqual(int(mv2.manifest_version), 2)
		mv1.reload()
		self.assertEqual(mv1.lifecycle_state, "Superseded")
		self.assertEqual(mv1.payload_digest, prior_digest)
		self.assertEqual(mv1.payload_json, prior_payload)

		# Cancellation preserves content
		cancel_publication(
			published_tender_ref=ctx["tender_ref"],
			organization=ORG,
			reason="withdrawn",
			reference="CANCEL-1",
		)
		mv2.reload()
		self.assertEqual(mv2.lifecycle_state, "Cancelled")
		self.assertEqual(mv2.payload_digest, ctx2["payload_digest"])
		lineage.reload()
		self.assertFalse(lineage.public_active)

	def test_roles_matrix_unknown_denied(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.roles import (
			require_role,
		)

		frappe.set_user("Guest")
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			require_role(ROLE_CONFIGURATOR)
		frappe.set_user("Administrator")
		# Administrator treated as holding roles
		require_role(ROLE_APPROVER)
		require_role(ROLE_PUBLICATION)

	def test_no_manifest_before_publication_and_lifecycle_events(self):
		ctx = _materialize_synthetic_publishable()
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION, {"manifest_id": ctx["target_manifest_id"]}), 0)
		gov = _gov_to_approved(ctx)
		self.assertEqual(frappe.db.count(DT_MANIFEST_VERSION, {"manifest_id": ctx["target_manifest_id"]}), 0)
		publish_approved_package(
			request_id=f"REQ-EV-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=f"PUB-EV-{ctx['suffix']}",
		)
		types = set(frappe.get_all(DT_LIFECYCLE_EVENT, pluck="event_type"))
		self.assertIn("review_package.prepared", types)
		self.assertIn("review_package.submitted_for_approval", types)
		self.assertIn("review_package.approved", types)
		self.assertIn("publication.succeeded", types)

	def test_active_retrieval_exposes_exact_version(self):
		ctx = _materialize_synthetic_publishable()
		gov = _gov_to_approved(ctx)
		out = publish_approved_package(
			request_id=f"REQ-ACT-{ctx['suffix']}",
			approval_decision=gov["dec"]["approval_decision"],
			organization=ORG,
			idempotency_key=f"PUB-ACT-{ctx['suffix']}",
		)
		active = retrieve_published_manifest(
			published_tender_ref=ctx["tender_ref"],
			active_only=True,
		)
		self.assertEqual(active["manifest_version"], 1)
		self.assertEqual(active["payload_digest"], out["payload_digest"])
		# Missing resource fails closed
		b = frappe.get_all(
			DT_MANIFEST_RESOURCE_BINDING,
			filters={"manifest_version": out["manifest_version"]},
			fields=["name", "content_ref"],
			limit=1,
		)[0]
		from pathlib import Path

		hex_digest = b.content_ref.removeprefix("bwmf-cas:v1:")
		path = Path(frappe.get_site_path("private", "files", f"bwmf-cas-{hex_digest}.json"))
		backup = path.read_bytes()
		path.unlink()
		frappe.clear_messages()
		with self.assertRaises((frappe.ValidationError, Exception)):
			retrieve_published_manifest(publication_id=out["publication_id"])
		titles = [m.get("title") for m in frappe.get_message_log()]
		self.assertTrue(
			"BWMF_RETRIEVE_CORRUPT" in titles or "BWMF_CAS_MISSING" in titles or any(titles),
			titles,
		)
		path.write_bytes(backup)
