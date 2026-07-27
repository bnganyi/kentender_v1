# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 1 — closed schema conformance (BWMF contract v1.0.0)."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from kentender_procurement.tender_configurations.bidder_workspace_manifest import (
	MANIFEST_SCHEMA_VERSION,
	list_schema_ids,
	load_schema,
	validate_against_schema,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.validate import (
	ManifestSchemaError,
)

_FIX = (
	Path(__file__).resolve().parents[1]
	/ "bidder_workspace_manifest"
	/ "fixtures"
	/ "examples"
)

_HASH_A = "sha256:" + ("a" * 64)
_HASH_B = "sha256:" + ("b" * 64)


def _valid_submission_policy(**overrides) -> dict:
	base = {
		"deadline_at": "2026-06-30T11:00:00+03:00",
		"timezone": "Africa/Nairobi",
		"server_time_authoritative": True,
		"late_submission_behavior": "reject",
		"withdrawal_mode": "not_permitted",
		"replacement_mode": "not_permitted",
		"submission_authority_policy_ref": "POL-SUB-AUTH-1",
		"reauthentication_policy_ref": "POL-REAUTH-1",
		"seal_policy_ref": "POL-SEAL-1",
		"receipt_policy_ref": "POL-RECEIPT-1",
		"concurrent_submission_policy": "single_authoritative_transaction",
		"idempotency_policy": "required",
	}
	base.update(overrides)
	return base


def _load_example(name: str) -> dict:
	with (_FIX / name).open(encoding="utf-8") as fh:
		return json.load(fh)


class TestBwmfSchemaConformancePhase1(unittest.TestCase):
	def test_manifest_schema_version_is_100(self):
		self.assertEqual(MANIFEST_SCHEMA_VERSION, "1.0.0")

	def test_schema_inventory_loads(self):
		ids = list_schema_ids()
		self.assertGreaterEqual(len(ids), 18)
		for schema_id in ids:
			schema = load_schema(schema_id)
			self.assertEqual(schema.get("schema_version"), "1.0.0")

	def test_source_binding_valid_closed_object(self):
		validate_against_schema(_load_example("source_binding.valid.json"), "source_binding")

	def test_source_binding_rejects_unknown_property(self):
		inst = _load_example("source_binding.valid.json")
		inst["extra_field"] = True
		with self.assertRaises(ManifestSchemaError) as ctx:
			validate_against_schema(inst, "source_binding")
		self.assertIn("unknown property", str(ctx.exception))

	def test_source_binding_requires_document_content_digest_archive_optional(self):
		inst = _load_example("source_binding.valid.json")
		# archive provenance is optional separate provenance
		inst.pop("archive_provenance_digest", None)
		validate_against_schema(inst, "source_binding")
		del inst["document_content_digest"]
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(inst, "source_binding")

	def test_source_binding_rejects_malformed_digest(self):
		inst = _load_example("source_binding.valid.json")
		inst["archive_provenance_digest"] = "not-a-digest"
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(inst, "source_binding")

	def test_compile_request_valid(self):
		validate_against_schema(_load_example("compile_request.valid.json"), "compile_request")

	def test_compile_request_rejects_unknown_property(self):
		inst = _load_example("compile_request.valid.json")
		inst["unexpected"] = 1
		with self.assertRaises(ManifestSchemaError) as ctx:
			validate_against_schema(inst, "compile_request")
		self.assertIn("unknown property", str(ctx.exception))

	def test_manifest_envelope_rejects_wrong_schema_version(self):
		payload = {
			"manifest_id": "M1",
			"manifest_version": 1,
			"published_tender_ref": "T1",
			"published_tender_version": 1,
			"std_family": "information_technology",
			"bindings": {},
			"tender_context": {},
			"localization": {},
			"submission_policy": _valid_submission_policy(),
			"lot_model": {},
			"document_package": {
				"package_ref": "DOC-1",
				"package_version": 1,
				"source_digest": _HASH_A,
				"document_content_digest": _HASH_B,
				"active_addenda": [],
			},
			"role_policy": {},
			"rule_registry": {},
			"validation_registry": {},
			"resource_registry": {},
			"evidence_contract": {},
			"sections": [],
			"cross_cutting_views": {},
			"workflow_gates": [],
			"projections": {},
			"publication_readiness": {},
		}
		envelope = {
			"manifest_schema_version": "0.9.0",
			"control": {
				"artifact_mode": "preview",
				"generated_at": "2026-07-24T00:00:00Z",
				"generated_by": "system:test",
				"compiler_run_id": "RUN-1",
			},
			"payload": payload,
			"integrity": {"payload_digest": _HASH_A},
		}
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(envelope, "manifest_envelope")

		envelope["manifest_schema_version"] = "1.0.0"
		validate_against_schema(envelope, "manifest_envelope")

	def test_manifest_envelope_rejects_unknown_top_level(self):
		payload = {
			"manifest_id": "M1",
			"manifest_version": 1,
			"published_tender_ref": "T1",
			"published_tender_version": 1,
			"std_family": "information_technology",
			"bindings": {},
			"tender_context": {},
			"localization": {},
			"submission_policy": _valid_submission_policy(),
			"lot_model": {},
			"document_package": {
				"package_ref": "DOC-1",
				"package_version": 1,
				"source_digest": _HASH_A,
				"document_content_digest": _HASH_B,
				"active_addenda": [],
			},
			"role_policy": {},
			"rule_registry": {},
			"validation_registry": {},
			"resource_registry": {},
			"evidence_contract": {},
			"sections": [],
			"cross_cutting_views": {},
			"workflow_gates": [],
			"projections": {},
			"publication_readiness": {},
		}
		envelope = {
			"manifest_schema_version": "1.0.0",
			"control": {
				"artifact_mode": "preview",
				"generated_at": "2026-07-24T00:00:00Z",
				"generated_by": "system:test",
				"compiler_run_id": "RUN-1",
			},
			"payload": payload,
			"integrity": {"payload_digest": _HASH_A},
			"extra": True,
		}
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(envelope, "manifest_envelope")

	def test_confirmation_has_no_client_editable_accepted_field(self):
		"""Phase 2: confirmation records must not expose client-editable accepted."""
		inst = _load_example("confirmation.valid.json")
		self.assertNotIn("accepted", inst)
		validate_against_schema(inst, "confirmation")
		schema = load_schema("confirmation")
		self.assertNotIn("accepted", schema.get("properties") or {})
		self.assertNotIn("accepted", schema.get("required") or [])
		# Unknown client-injected accepted is rejected (closed object)
		bad = copy.deepcopy(inst)
		bad["accepted"] = True
		with self.assertRaises(ManifestSchemaError) as ctx:
			validate_against_schema(bad, "confirmation")
		self.assertIn("unknown property", str(ctx.exception))

	def test_bindings_require_std_source_archive_digest(self):
		bindings = {
			"std_template_version_ref": "STD-1",
			"std_template_digest": _HASH_A,
			"std_source_digest": _HASH_B,
			"obligation_catalogue_version_ref": "CAT-1",
			"obligation_catalogue_digest": _HASH_A,
			"section_blueprint_version_ref": "BP-1",
			"section_blueprint_digest": _HASH_A,
			"tender_configuration_snapshot_ref": "CFG-1",
			"tender_configuration_digest": _HASH_A,
			"document_package_version_ref": "DOC-1",
			"document_package_digest": _HASH_A,
			"addendum_set_version": 0,
			"submission_policy_version_ref": "POL-1",
			"submission_policy_digest": _HASH_A,
			"compiler_contract_version": "1.0.0",
			"compiler_version": "1.0.0",
			"identity_algorithm_version": "id-v1",
			"rule_language_version": "1.0.0",
		}
		validate_against_schema(bindings, "bindings")
		del bindings["std_source_digest"]
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(bindings, "bindings")
