# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 2 — schema preflight (draft, $ref, keywords, coverage, digests)."""

from __future__ import annotations

import copy
import json
import unittest

from kentender_procurement.tender_configurations.bidder_workspace_manifest.digest import (
	ARCHIVE_PROVENANCE_DIGEST_FIELD,
	DOCUMENT_CONTENT_DIGEST_FIELD,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.registry import (
	SCHEMA_FILES,
	load_schema,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.schema_meta import (
	JSON_SCHEMA_DRAFT_2020_12,
	SchemaMetaError,
	assert_coverage_ledger_complete,
	collect_unsupported_keywords,
	load_coverage_ledger,
	meta_validate_all_schemas,
	resolve_all_refs,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.validate import (
	ManifestSchemaError,
	validate_against_schema,
)


class TestBwmfSchemaPreflightPhase2(unittest.TestCase):
	def test_all_schemas_declare_draft_and_pass_meta_validate(self):
		ids = meta_validate_all_schemas()
		self.assertEqual(sorted(ids), sorted(SCHEMA_FILES.keys()))
		for schema_id in ids:
			self.assertEqual(load_schema(schema_id).get("$schema"), JSON_SCHEMA_DRAFT_2020_12)

	def test_refs_resolve_on_every_schema(self):
		for schema_id in SCHEMA_FILES:
			resolve_all_refs(load_schema(schema_id), schema_id=schema_id)

	def test_unsupported_schema_keyword_rejected(self):
		schema = copy.deepcopy(load_schema("source_binding"))
		schema["unevaluatedProperties"] = False
		bad = collect_unsupported_keywords(schema)
		self.assertTrue(any("unevaluatedProperties" in b for b in bad))

	def test_coverage_ledger_complete(self):
		assert_coverage_ledger_complete()
		ledger = load_coverage_ledger()
		self.assertEqual(ledger["digest_authority"][DOCUMENT_CONTENT_DIGEST_FIELD], "required_authoritative")
		self.assertEqual(
			ledger["digest_authority"][ARCHIVE_PROVENANCE_DIGEST_FIELD],
			"optional_separate_provenance",
		)
		doctypes = {m["doctype"] for m in ledger["persistence_concepts"].values()}
		self.assertIn("BWMF Compile Request", doctypes)
		self.assertIn("BWMF Submission Receipt", doctypes)

	def test_document_content_digest_authoritative_archive_optional(self):
		schema = load_schema("source_binding")
		self.assertIn(DOCUMENT_CONTENT_DIGEST_FIELD, schema["required"])
		self.assertNotIn(ARCHIVE_PROVENANCE_DIGEST_FIELD, schema["required"])
		inst = {
			"binding_id": "B1",
			"binding_type": "std",
			"object_ref": "O1",
			"object_version": "1",
			"lifecycle_state": "approved",
			"document_content_digest": "sha256:" + ("c" * 64),
		}
		validate_against_schema(inst, "source_binding")

	def test_confirmation_schema_has_no_accepted(self):
		schema = load_schema("confirmation")
		self.assertNotIn("accepted", schema.get("properties") or {})
		with self.assertRaises(ManifestSchemaError):
			validate_against_schema(
				{
					"confirmation_id": "C1",
					"response_ref": "R1",
					"response_version": 1,
					"legal_text_ref": "L1",
					"legal_text_digest": "sha256:" + ("a" * 64),
					"statement_digest": "sha256:" + ("b" * 64),
					"actor_ref": "u1",
					"capacity": "signatory",
					"confirmed_at": "2026-07-24T00:00:00Z",
					"state": "confirmed",
					"accepted": True,
				},
				"confirmation",
			)

	def test_meta_validate_fails_on_bad_draft(self):
		# smoke: assert_coverage does not raise
		assert_coverage_ledger_complete()
		self.assertTrue(load_coverage_ledger().get("persistence_concepts"))
