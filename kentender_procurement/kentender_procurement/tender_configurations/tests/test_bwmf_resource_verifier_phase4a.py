# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 4A — resource verifier negative matrix."""

from __future__ import annotations

import json
import unittest

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.resource_verifier import (
	ResourceVerifyError,
	assert_candidates_cover_preview,
	verify_descriptor_set,
	verify_resource_row,
	verify_sections_reference_resources,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import services as bwmf
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_MANIFEST_RESOURCE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	content_ref_for_bytes,
	put_canonical_json,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	descriptor_set_digest,
	logical_resource_digest,
)
from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
	clear_bwmf_canonical_fixture,
)


def _ensure():
	for dn in ("bwmf_content_object", "bwmf_manifest_resource"):
		frappe.reload_doc("Tender Configurations", "doctype", dn, force=True)


def _make_resource(
	*,
	resource_id: str,
	items: list[dict],
	schema_ref: str = "bwmf/item/synthetic",
	schema_version: str = "1.0.0",
	ordering: list[str] | None = None,
	source_refs: list | None = None,
	item_count: int | None = None,
	resource_digest: str | None = None,
	content_ref: str | None = None,
	physical: str | None = None,
	resource_type: str = "synthetic",
) -> str:
	ordering = ordering or ["order_weight", "id"]
	stored = put_canonical_json(items, organization="ORG-P4A")
	return bwmf.create_manifest_resource(
		resource_id=resource_id,
		resource_type=resource_type,
		schema_ref=schema_ref,
		schema_version=schema_version,
		item_count=item_count if item_count is not None else len(items),
		ordering_contract=ordering,
		resource_digest=resource_digest or logical_resource_digest(items),
		storage_mode="content_addressed",
		content_ref=content_ref if content_ref is not None else stored["content_ref"],
		physical_object_digest=physical if physical is not None else stored["physical_object_digest"],
		source_refs=source_refs if source_refs is not None else [{"collection": "synthetic"}],
		organization="ORG-P4A",
	)


class TestBwmfResourceVerifierPhase4A(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_ensure()
		clear_bwmf_canonical_fixture()

	def tearDown(self):
		clear_bwmf_canonical_fixture()

	def test_wrong_item_count(self):
		items = [{"id": "a", "order_weight": 1}]
		name = _make_resource(resource_id="R-COUNT", items=items, item_count=2)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name)
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_COUNT")

	def test_unknown_schema(self):
		items = [{"id": "a", "order_weight": 1}]
		# Use an NSSF resource_id so verifier compares against NSSF_RESOURCE_SPECS
		name = _make_resource(
			resource_id="RESOURCE-NSSF-REQUIREMENT-GROUPS",
			items=items,
			schema_ref="bwmf/item/unknown",
			schema_version="1.0.0",
			ordering=["order_weight", "group_key"],
			resource_type="requirement_group",
		)
		# items don't match NSSF fields — force schema check by expected override
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name, expected_schema_ref="bwmf/item/requirement_group")
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_SCHEMA")

	def test_wrong_schema_version(self):
		items = [{"id": "a", "order_weight": 1}]
		name = _make_resource(resource_id="R-VER", items=items, schema_version="9.9.9")
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name, expected_schema_version="1.0.0")
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_SCHEMA")

	def test_unknown_item_property(self):
		items = [{"id": "a", "order_weight": 1, "extra": "nope"}]
		name = _make_resource(resource_id="R-EXTRA", items=items)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name, expected_fields=("id", "order_weight"))
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_SCHEMA")

	def test_missing_required_item_property(self):
		items = [{"id": "a"}]
		name = _make_resource(resource_id="R-MISS", items=items, ordering=["id"])
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name, expected_fields=("id", "order_weight"))
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_SCHEMA")

	def test_duplicate_logical_item_id(self):
		items = [{"id": "a", "order_weight": 1}, {"id": "a", "order_weight": 2}]
		# bypass canonicalize by writing raw
		stored = put_canonical_json(items, organization="ORG-P4A")
		name = bwmf.create_manifest_resource(
			resource_id="R-DUP",
			resource_type="synthetic",
			schema_ref="bwmf/item/synthetic",
			schema_version="1.0.0",
			item_count=2,
			ordering_contract=["order_weight", "id"],
			resource_digest=logical_resource_digest(items),
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[{"c": 1}],
			organization="ORG-P4A",
		)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name, enforce_order=False)
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_DUP_ID")

	def test_reordered_logical_items(self):
		items = [{"id": "b", "order_weight": 20}, {"id": "a", "order_weight": 10}]
		stored = put_canonical_json(items, organization="ORG-P4A")
		name = bwmf.create_manifest_resource(
			resource_id="R-ORDER",
			resource_type="synthetic",
			schema_ref="bwmf/item/synthetic",
			schema_version="1.0.0",
			item_count=2,
			ordering_contract=["order_weight", "id"],
			resource_digest=logical_resource_digest(items),
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[{"c": 1}],
			organization="ORG-P4A",
		)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name)
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_ORDER")

	def test_unreconstructable_ordering_contract(self):
		items = [{"id": "a", "order_weight": 1}]
		stored = put_canonical_json(items, organization="ORG-P4A")
		name = bwmf.create_manifest_resource(
			resource_id="R-BADORD",
			resource_type="synthetic",
			schema_ref="bwmf/item/synthetic",
			schema_version="1.0.0",
			item_count=1,
			ordering_contract=[],
			resource_digest=logical_resource_digest(items),
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[{"c": 1}],
			organization="ORG-P4A",
		)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name)
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_ORDER")

	def test_logical_resource_digest_mismatch(self):
		items = [{"id": "a", "order_weight": 1}]
		name = _make_resource(
			resource_id="R-LDIG",
			items=items,
			resource_digest="sha256:" + ("0" * 64),
		)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name)
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_DIGEST")

	def test_physical_object_digest_mismatch(self):
		items = [{"id": "a", "order_weight": 1}]
		name = _make_resource(
			resource_id="R-PDIG",
			items=items,
			physical="sha256:" + ("1" * 64),
		)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name)
		self.assertEqual(ctx.exception.code, "BWMF_CAS_CORRUPT")

	def test_incorrect_deterministic_content_ref(self):
		items = [{"id": "a", "order_weight": 1}]
		stored = put_canonical_json(items, organization="ORG-P4A")
		# invent a well-formed but wrong ref that does not exist
		wrong = "bwmf-cas:v1:" + ("c" * 64)
		with self.assertRaises(Exception):
			# creation will store wrong ref; verify fails
			name = bwmf.create_manifest_resource(
				resource_id="R-CREF",
				resource_type="synthetic",
				schema_ref="bwmf/item/synthetic",
				schema_version="1.0.0",
				item_count=1,
				ordering_contract=["order_weight", "id"],
				resource_digest=logical_resource_digest(items),
				storage_mode="content_addressed",
				content_ref=wrong,
				physical_object_digest=stored["physical_object_digest"],
				source_refs=[{"c": 1}],
				organization="ORG-P4A",
			)
			verify_resource_row(name)

	def test_missing_source_lineage(self):
		items = [{"id": "a", "order_weight": 1}]
		stored = put_canonical_json(items, organization="ORG-P4A")
		name = bwmf.create_manifest_resource(
			resource_id="R-LINE",
			resource_type="synthetic",
			schema_ref="bwmf/item/synthetic",
			schema_version="1.0.0",
			item_count=1,
			ordering_contract=["order_weight", "id"],
			resource_digest=logical_resource_digest(items),
			storage_mode="content_addressed",
			content_ref=stored["content_ref"],
			physical_object_digest=stored["physical_object_digest"],
			source_refs=[],
			organization="ORG-P4A",
		)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_resource_row(name)
		self.assertEqual(ctx.exception.code, "BWMF_RESOURCE_LINEAGE")

	def test_descriptor_set_digest_mismatch(self):
		items = [{"id": "a", "order_weight": 1}]
		name = _make_resource(resource_id="R-SET", items=items)
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_descriptor_set([name], "sha256:" + ("2" * 64))
		self.assertEqual(ctx.exception.code, "BWMF_DESCRIPTOR_SET")

	def test_section_referencing_absent_resource(self):
		with self.assertRaises(ResourceVerifyError) as ctx:
			verify_sections_reference_resources(
				[{"section_key": "s1", "resource_refs": ["RESOURCE-MISSING"]}],
				{"RESOURCE-PRESENT"},
			)
		self.assertEqual(ctx.exception.code, "BWMF_SECTION_RESOURCE")

	def test_resource_candidate_absent_from_preview(self):
		with self.assertRaises(ResourceVerifyError) as ctx:
			assert_candidates_cover_preview(
				[{"resource_id": "RESOURCE-A"}],
				["RESOURCE-A", "RESOURCE-B"],
			)
		self.assertEqual(ctx.exception.code, "BWMF_CANDIDATE_ABSENT")
