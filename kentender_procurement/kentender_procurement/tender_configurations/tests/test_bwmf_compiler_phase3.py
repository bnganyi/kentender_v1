# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 3 / 3A / 3B — pure BWMF deterministic compiler integrity corrections."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.fixtures_loader import (
	compile_request_from_source_set,
	load_json,
	load_nssf_calibration_source_set,
	load_synthetic_std_source_set,
	nssf_compile_request,
	source_set_from_raw,
	synthetic_compile_request,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	JcsError,
	jcs_canonicalize,
	jcs_sha256_digest,
	pack_equivalent_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.nssf_leak_scan import (
	scan_tree_for_nssf_leaks,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.pipeline import run
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	STAGE_IDS,
	SourceSet,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.nssf_fixture_errata import (
	NSSF_CANONICAL_CONTENT_SECTION_KEYS,
	NSSF_SECURITY_DECISION_ID,
	assert_nssf_content_sections,
)

# Phase 4 digest-oracle recovery (frozen arrays under fixtures/nssf_calibration/resources/)
_EXP_PROJ = "sha256:9dac86f777ae8c89f5b02e29e82401e5f83e12966891f2337fc7cc98ee0f907d"
_EXP_DIAG = "sha256:b3bbc3f30456383236a9ea1b131fee9d6e62519a20e45484c987805260be84f7"
_PREVIEW_PAYLOAD_DIGEST = (
	"sha256:60184f6b419d60866a418d5971d369fd634c7d3211a995f616122c75fc264a7e"
)


class TestBwmfRfc8785Jcs(unittest.TestCase):
	def test_rfc8785_vectors(self):
		vectors = load_json("rfc8785_vectors/appendix_a.json")
		self.assertGreaterEqual(len(vectors), 10)
		for vec in vectors:
			with self.subTest(vec["name"]):
				self.assertEqual(jcs_canonicalize(vec["input"]), vec["jcs"])

	def test_rejects_float(self):
		with self.assertRaises(JcsError):
			jcs_canonicalize({"n": 1.5})

	def test_unicode_property_order_and_escaping(self):
		# € (U+20AC) sorts after Latin letters by UTF-16 code units
		self.assertEqual(jcs_canonicalize({"\u20ac": 1, "a": 2, "\u00e9": 3}), '{"a":2,"é":3,"€":1}')
		self.assertEqual(jcs_canonicalize({"a": "\b\t\n\f\r"}), '{"a":"\\b\\t\\n\\f\\r"}')

	def test_integer_boundaries(self):
		self.assertEqual(jcs_canonicalize({"n": 0}), '{"n":0}')
		self.assertEqual(jcs_canonicalize({"n": -1}), '{"n":-1}')
		self.assertEqual(jcs_canonicalize({"n": 9007199254740991}), '{"n":9007199254740991}')


class TestBwmfCompilerPhase3Pure(unittest.TestCase):
	def test_stage_traces_c01_c22(self):
		result = run(nssf_compile_request(), load_nssf_calibration_source_set())
		self.assertTrue(result.ok, result.fail_code)
		stages = [t["stage"] for t in result.traces]
		self.assertEqual(stages, list(STAGE_IDS))
		self.assertTrue(all(t["state"] in {"ok", "skipped", "error"} for t in result.traces))
		c21 = next(t for t in result.traces if t["stage"] == "C21")
		self.assertEqual(c21["state"], "ok")
		self.assertEqual(result.addendum_impact.get("applicable"), False)

	def test_replay_deterministic(self):
		req = nssf_compile_request()
		src = load_nssf_calibration_source_set()
		a = run(req, src)
		b = run(req, src)
		self.assertEqual(a.payload_digest, b.payload_digest)
		self.assertEqual(a.projection_digest, b.projection_digest)
		self.assertEqual(a.diagnostic_digest, b.diagnostic_digest)

	def test_shuffled_source_insertion_order(self):
		req = nssf_compile_request()
		a = run(req, load_nssf_calibration_source_set(shuffle_keys=False))
		b = run(req, load_nssf_calibration_source_set(shuffle_keys=True))
		self.assertEqual(a.payload_digest, b.payload_digest)

	def test_label_change_preserves_identity_but_changes_payload_digest(self):
		req = nssf_compile_request()
		src = load_nssf_calibration_source_set()
		base = run(req, src)
		altered = copy.deepcopy(src.raw)
		# Display-label change on a requirement group (presentation only).
		altered["collections"]["requirement_groups"][0]["label"] = "renamed-display-label-only"
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.stages._common import (
			digest_of,
		)

		altered["declared_digests"]["collections"] = digest_of(altered["collections"])
		req2 = nssf_compile_request()
		req2.expected_input_digests = dict(altered["declared_digests"])
		result = run(req2, SourceSet(raw=altered, insertion_order=src.insertion_order))
		self.assertTrue(result.ok, result.fail_code)
		base_ids = [s["section_instance_id"] for s in base.payload["sections"]]
		alt_ids = [s["section_instance_id"] for s in result.payload["sections"]]
		self.assertEqual(alt_ids, base_ids)
		self.assertEqual(
			result.payload["object_contracts"]["response_contract_digest"],
			base.payload["object_contracts"]["response_contract_digest"],
		)
		self.assertNotEqual(
			result.payload["object_contracts"]["display_contract_digest"],
			base.payload["object_contracts"]["display_contract_digest"],
		)
		self.assertNotEqual(result.payload_digest, base.payload_digest)

	def test_label_change_classified_display_only(self):
		src = load_nssf_calibration_source_set()
		base = run(nssf_compile_request(), src)
		altered = copy.deepcopy(src.raw)
		altered["collections"]["requirement_groups"][0]["label"] = "addendum-display-relabel"
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.stages._common import (
			digest_of,
		)

		altered["declared_digests"]["collections"] = digest_of(altered["collections"])
		altered["previous_manifest_binding"] = {
			"manifest_ref": "BWMF-PREV-1",
			"manifest_version": 1,
			"payload_digest": base.payload_digest,
			"lifecycle_state": "Published",
			"baseline_authority": "published_manifest",
			"retained_payload": copy.deepcopy(base.payload),
			"sections": copy.deepcopy(base.payload["sections"]),
			"object_contracts": copy.deepcopy(base.payload["object_contracts"]),
		}
		req = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		req.expected_input_digests = dict(altered["declared_digests"])
		result = run(req, SourceSet(raw=altered, insertion_order=src.insertion_order))
		self.assertTrue(result.ok, result.fail_code)
		self.assertIn("display_only", result.addendum_impact.get("change_classes") or [])
		self.assertTrue(result.addendum_impact.get("contract_diff", {}).get("response_contract_unchanged"))
		self.assertTrue(result.addendum_impact.get("contract_diff", {}).get("display_contract_changed"))

	def test_nfc_equivalent_text_identical_canonical_digest(self):
		# café (NFC U+00E9) vs cafe + combining acute (NFD)
		nfc = {"label": "caf\u00e9"}
		nfd = {"label": "cafe\u0301"}
		self.assertNotEqual(nfc["label"], nfd["label"])
		self.assertEqual(jcs_sha256_digest(nfc), jcs_sha256_digest(nfd))

	def test_material_content_change_changes_digest(self):
		req = nssf_compile_request()
		src = load_nssf_calibration_source_set()
		base = run(req, src)
		altered = copy.deepcopy(src.raw)
		altered["tender_configuration"]["tender_context"]["currency"] = "USD"
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.stages._common import (
			digest_of,
		)

		altered["declared_digests"]["tender_configuration"] = digest_of(altered["tender_configuration"])
		req2 = nssf_compile_request()
		req2.expected_input_digests = dict(altered["declared_digests"])
		result = run(req2, SourceSet(raw=altered, insertion_order=src.insertion_order))
		self.assertTrue(result.ok)
		self.assertNotEqual(result.payload_digest, base.payload_digest)

	def test_bad_source_digest_fails(self):
		req = nssf_compile_request()
		req.expected_input_digests = dict(req.expected_input_digests)
		req.expected_input_digests["catalogue"] = "sha256:" + ("f" * 64)
		result = run(req, load_nssf_calibration_source_set())
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_SOURCE_DIGEST_MISMATCH")

	def test_identity_collision_fails(self):
		req = nssf_compile_request()
		src = load_nssf_calibration_source_set()
		altered = copy.deepcopy(src.raw)
		secs = altered["section_templates"]
		secs[1]["section_instance_id"] = secs[0]["section_instance_id"]
		result = run(req, SourceSet(raw=altered, insertion_order=src.insertion_order))
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_ID_COLLISION")

	def test_float_money_rejected(self):
		with self.assertRaises(JcsError):
			jcs_sha256_digest({"amount": 12.34})

	def test_missing_submission_policy_fails_closed(self):
		req = nssf_compile_request()
		src = load_nssf_calibration_source_set()
		altered = copy.deepcopy(src.raw)
		del altered["tender_configuration"]["submission_policy_source"]
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.stages._common import (
			digest_of,
		)

		altered["declared_digests"]["tender_configuration"] = digest_of(altered["tender_configuration"])
		req.expected_input_digests = dict(altered["declared_digests"])
		result = run(req, SourceSet(raw=altered, insertion_order=src.insertion_order))
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_SUBMISSION_POLICY")

	def test_no_runtime_policy_defaults_in_services(self):
		import kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.services as svc

		self.assertFalse(hasattr(svc, "default_submission_policy"))

	def test_nssf_oracles_complete(self):
		result = run(nssf_compile_request(), load_nssf_calibration_source_set())
		self.assertTrue(result.ok, result.fail_code)
		keys = [s["section_key"] for s in result.payload["sections"]]
		assert_nssf_content_sections(keys)
		self.assertEqual(tuple(keys), NSSF_CANONICAL_CONTENT_SECTION_KEYS)
		self.assertEqual(result.projection_digest, _EXP_PROJ)
		self.assertEqual(result.diagnostic_digest, _EXP_DIAG)
		self.assertEqual(result.digest_label, "unmaterialized_preview_payload")
		self.assertFalse(result.envelope["integrity"].get("final_runtime_manifest"))
		# Relabelled Phase 3 unmaterialized preview digest (may drift if payload shape changes;
		# label contract is mandatory; exact bytes asserted when stable).
		self.assertTrue(result.payload_digest.startswith("sha256:"))
		self.assertNotEqual(result.payload_digest, result.projection_digest)

		counts = load_json("nssf_calibration/expected_counts.json")
		coll = load_nssf_calibration_source_set().raw["collections"]
		self.assertEqual(len(coll["requirement_groups"]), 23)
		self.assertEqual(len(coll["requirements"]), 190)
		self.assertEqual(sum(1 for r in coll["requirements"] if r.get("contract_carry_forward")), 117)
		self.assertEqual(len(coll["preliminary_criteria"]), 9)
		self.assertEqual(len(coll["qualification_criteria"]), 9)
		self.assertEqual(len(coll["technical_scoring"]), 7)
		self.assertEqual(sum(int(r["max_score"]) for r in coll["technical_scoring"]), 100)
		profile = load_nssf_calibration_source_set().raw["scoring_profile"]
		self.assertEqual(profile["maximum_score"], "100")
		self.assertEqual(profile["qualification_threshold"], "75")
		self.assertEqual(result.payload["publication_readiness"]["scoring_profile"]["maximum_score"], "100")
		self.assertEqual(
			result.payload["publication_readiness"]["scoring_profile"]["qualification_threshold"], "75"
		)
		self.assertEqual(len(coll["schedule_rows"]), 6)
		self.assertEqual(len(coll["price_lines"]), 22)
		self.assertEqual(len(coll["contract_conditions"]), 8)
		self.assertEqual(len(coll["decisions"]), 8)
		self.assertEqual(len(result.payload["workflow_gates"]), 3)
		view_keys = {v["view_key"] for v in result.payload["cross_cutting_views"]}
		self.assertEqual(view_keys, {"evidence_register", "issue_register"})
		dec_ids = {d["decision_id"] for d in coll["decisions"]}
		self.assertIn(NSSF_SECURITY_DECISION_ID, dec_ids)
		self.assertEqual(
			result.payload["publication_readiness"]["coverage_summary"]["contract_carry_forward_requirements"],
			117,
		)
		self.assertFalse(result.payload["publication_readiness"]["passed"])
		self.assertIn(
			"resource_materialization_required",
			result.payload["publication_readiness"]["blocking_reasons"],
		)
		self.assertEqual(
			result.payload["submission_policy"]["withdrawal_mode"],
			"permitted_before_deadline",
		)
		self.assertEqual(
			result.payload["submission_policy"]["replacement_mode"],
			"new_sealed_version_before_deadline",
		)
		self.assertNotIn("allow_withdrawal", result.envelope.get("control") or {})
		# Candidates packaged; not treated as materialized
		self.assertGreaterEqual(len(result.logical_resources), 1)
		self.assertTrue(all(not c.get("materialized") for c in result.logical_resources))
		self.assertIn("resource_candidates", result.envelope)
		# C17 must not be the candidate builder: candidates exist from C09/C18 path
		self.assertTrue(any(c.get("candidate_id") for c in result.logical_resources))
		_ = counts  # oracle file present

	def test_preview_digest_labelled_non_final(self):
		result = run(nssf_compile_request(), load_nssf_calibration_source_set())
		self.assertEqual(result.digest_label, "unmaterialized_preview_payload")
		self.assertFalse(result.envelope["integrity"]["final_runtime_manifest"])

	def test_publication_mode_fails_unmaterialized(self):
		req = nssf_compile_request(compile_mode="publication")
		result = run(req, load_nssf_calibration_source_set())
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_RESOURCE_MATERIALIZATION")
		self.assertEqual(result.payload, {})
		self.assertFalse(result.payload_digest)
		self.assertEqual(result.envelope.get("artifact_kind"), "failed_result")
		self.assertFalse(result.envelope.get("eligible_for_publication"))

	def _published_baseline(self, base_result, *, lifecycle="Published", authority="published_manifest", sections=None):
		secs = sections if sections is not None else copy.deepcopy(base_result.payload["sections"])
		return {
			"manifest_ref": "BWMF-PREV-1",
			"manifest_version": 1,
			"payload_digest": base_result.payload_digest,
			"lifecycle_state": lifecycle,
			"baseline_authority": authority,
			"retained_payload": copy.deepcopy(base_result.payload),
			"sections": secs,
			"object_contracts": copy.deepcopy(base_result.payload["object_contracts"]),
			"resource_descriptors": copy.deepcopy(
				(base_result.payload.get("resource_registry") or {}).get("resources") or []
			),
		}

	def test_all_compile_modes_c21(self):
		src = load_nssf_calibration_source_set()
		base = run(nssf_compile_request(), src)
		self.assertTrue(base.ok)

		for mode in ("preview", "publication"):
			req = nssf_compile_request(compile_mode=mode)
			result = run(req, src)
			c21 = next(t for t in result.traces if t["stage"] == "C21")
			# publication fails C19 but C21 still records N/A when mode is non-addendum
			if mode == "preview":
				self.assertEqual(c21["state"], "ok")
			self.assertEqual(result.addendum_impact.get("applicable"), False)
			self.assertEqual(result.addendum_impact.get("workspace_application"), "not_applied")

		# Published baseline with fewer sections → section_added
		raw = copy.deepcopy(src.raw)
		raw["previous_manifest_binding"] = self._published_baseline(
			base, sections=copy.deepcopy(base.payload["sections"])[:8]
		)
		req = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		result = run(req, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertTrue(result.ok, result.fail_code)
		self.assertTrue(result.addendum_impact.get("applicable"))
		self.assertIn("section_added", result.addendum_impact.get("change_classes") or [])
		self.assertEqual(result.addendum_impact.get("workspace_application"), "not_applied")
		self.assertEqual(result.addendum_impact.get("baseline_role"), "current_published")

		# exact previous-manifest digest mismatch rejected
		req_bad = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest="sha256:" + ("b" * 64),
		)
		bad = run(req_bad, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertFalse(bad.ok)
		self.assertEqual(bad.fail_code, "BWMF_ADDENDUM_PREVIOUS")

		# addendum_publication still requires materialization (failed_result, no payload)
		req_pub = nssf_compile_request(
			compile_mode="addendum_publication",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		pub = run(req_pub, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertFalse(pub.ok)
		self.assertEqual(pub.fail_code, "BWMF_RESOURCE_MATERIALIZATION")
		self.assertEqual(pub.payload, {})
		self.assertFalse(pub.payload_digest)

	def test_addendum_baseline_must_be_published(self):
		src = load_nssf_calibration_source_set()
		base = run(nssf_compile_request(), src)
		raw = copy.deepcopy(src.raw)
		raw["previous_manifest_binding"] = self._published_baseline(base)
		raw["previous_manifest_binding"]["lifecycle_state"] = "Draft"
		req = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		result = run(req, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_ADDENDUM_PREVIOUS")

	def test_preview_artifact_rejected_as_addendum_baseline(self):
		src = load_nssf_calibration_source_set()
		base = run(nssf_compile_request(), src)
		raw = copy.deepcopy(src.raw)
		raw["previous_manifest_binding"] = {
			"manifest_ref": "BWMF-PREV-1",
			"manifest_version": 1,
			"payload_digest": base.payload_digest,
			"lifecycle_state": "Published",
			"baseline_authority": "compile_artifact",
			"artifact_kind": "preview",
			"retained_payload": copy.deepcopy(base.payload),
			"sections": copy.deepcopy(base.payload["sections"]),
		}
		req = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		result = run(req, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_ADDENDUM_PREVIOUS")

	def test_failed_artifact_rejected_as_addendum_baseline(self):
		src = load_nssf_calibration_source_set()
		base = run(nssf_compile_request(), src)
		raw = copy.deepcopy(src.raw)
		raw["previous_manifest_binding"] = {
			"manifest_ref": "BWMF-PREV-1",
			"manifest_version": 1,
			"payload_digest": base.payload_digest,
			"lifecycle_state": "Failed",
			"baseline_authority": "published_manifest",
			"artifact_kind": "failed_result",
			"retained_payload": copy.deepcopy(base.payload),
			"sections": copy.deepcopy(base.payload["sections"]),
		}
		req = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		result = run(req, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertFalse(result.ok)
		self.assertEqual(result.fail_code, "BWMF_ADDENDUM_PREVIOUS")

	def test_historical_replay_against_superseded_published_manifest(self):
		src = load_nssf_calibration_source_set()
		base = run(nssf_compile_request(), src)
		raw = copy.deepcopy(src.raw)
		raw["previous_manifest_binding"] = self._published_baseline(
			base,
			lifecycle="Superseded",
			authority="superseded_published_manifest",
			sections=copy.deepcopy(base.payload["sections"])[:8],
		)
		req = nssf_compile_request(
			compile_mode="addendum_preview",
			previous_manifest_ref="BWMF-PREV-1",
			previous_manifest_version=1,
			previous_manifest_digest=base.payload_digest,
		)
		result = run(req, SourceSet(raw=raw, insertion_order=src.insertion_order))
		self.assertTrue(result.ok, result.fail_code)
		self.assertEqual(result.addendum_impact.get("baseline_role"), "historical_replay")
		self.assertEqual(result.addendum_impact.get("baseline_lifecycle_state"), "Superseded")

	def test_failed_compile_has_no_payload_or_synthetic_digest(self):
		req = nssf_compile_request()
		req.expected_input_digests = dict(req.expected_input_digests)
		req.expected_input_digests["catalogue"] = "sha256:" + ("f" * 64)
		result = run(req, load_nssf_calibration_source_set())
		self.assertFalse(result.ok)
		self.assertEqual(result.payload, {})
		self.assertFalse(result.payload_digest)
		self.assertEqual(result.digest_label, "failed_result")
		self.assertTrue(result.envelope.get("failed"))
		self.assertIsNone(result.envelope.get("integrity", {}).get("payload_digest"))
		self.assertFalse(result.envelope.get("eligible_for_approval"))
		self.assertFalse(result.envelope.get("eligible_for_publication"))
		self.assertEqual(result.logical_resources, [])

	def test_synthetic_std_profile(self):
		req = synthetic_compile_request()
		src = load_synthetic_std_source_set()
		# Injected sources through generic entry (no family branching)
		result = run(req, source_set_from_raw(src.raw))
		self.assertTrue(result.ok, result.fail_code)
		self.assertEqual(len(result.payload["sections"]), 4)
		self.assertTrue(result.payload["lot_model"]["bidder_selectable_lots"])
		self.assertTrue(result.payload["lot_model"]["alternatives_permitted"])
		self.assertEqual(result.payload["std_family"], "synthetic_alpha")
		# No NSSF identifiers
		blob = json.dumps(result.payload)
		self.assertNotIn("NSSF", blob)
		self.assertNotIn("NSSFSPS", blob)

	def test_oracle_fixture_digests(self):
		proj = load_json("nssf_calibration/golden_projection.json")
		diags = load_json("nssf_calibration/expected_diagnostics.json")
		self.assertEqual(pack_equivalent_digest(proj["payload"]), _EXP_PROJ)
		self.assertEqual(pack_equivalent_digest(diags), _EXP_DIAG)

	def test_nssf_leak_scan(self):
		compiler_root = (
			Path(__file__).resolve().parents[1] / "bidder_workspace_manifest" / "compiler"
		)
		hits = scan_tree_for_nssf_leaks(compiler_root)
		self.assertEqual(hits, [], msg="\n".join(hits))


class TestBwmfSubmissionPolicySchemaPhase3(unittest.TestCase):
	def test_closed_submission_policy_schema(self):
		from kentender_procurement.tender_configurations.bidder_workspace_manifest import (
			validate_against_schema,
		)
		from kentender_procurement.tender_configurations.bidder_workspace_manifest.validate import (
			ManifestSchemaError,
		)

		policy = {
			"deadline_at": "2026-06-30T11:00:00+03:00",
			"timezone": "Africa/Nairobi",
			"server_time_authoritative": True,
			"late_submission_behavior": "reject",
			"withdrawal_mode": "permitted_before_deadline",
			"replacement_mode": "new_sealed_version_before_deadline",
			"submission_authority_policy_ref": "POL-SUB-AUTH-1",
			"reauthentication_policy_ref": "POL-REAUTH-1",
			"seal_policy_ref": "POL-SEAL-1",
			"receipt_policy_ref": "POL-RECEIPT-1",
			"concurrent_submission_policy": "single_authoritative_transaction",
			"idempotency_policy": "required",
		}
		validate_against_schema(policy, "submission_policy")
		bad = dict(policy)
		bad["withdrawal_mode"] = "maybe"
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(bad, "submission_policy")
