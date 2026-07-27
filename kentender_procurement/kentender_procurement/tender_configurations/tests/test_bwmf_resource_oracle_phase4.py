# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 4 — NSSF resource oracle recovery and reproducibility (pure)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.fixtures_loader import (
	fixtures_root,
	load_json,
	load_nssf_calibration_source_set,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	descriptor_set_digest,
	freeze_nssf_resources_from_collections,
	logical_resource_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.item_schemas import (
	NSSF_RESOURCE_ORDER,
	NSSF_RESOURCE_SPECS,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.chunking import (
	validate_chunks,
)


class TestBwmfResourceOraclePhase4(unittest.TestCase):
	def test_nine_frozen_resources_match_meta(self):
		meta = load_json("nssf_calibration/resource_digest_meta.json")
		root = Path(fixtures_root()) / "nssf_calibration" / "resources"
		self.assertEqual(len(meta["resources"]), 9)
		digests = []
		for row in meta["resources"]:
			rid = row["resource_id"]
			payload = json.loads((root / f"{rid}.json").read_text(encoding="utf-8"))
			self.assertEqual(payload["resource_id"], rid)
			self.assertEqual(payload["item_count"], len(payload["items"]))
			self.assertEqual(logical_resource_digest(payload["items"]), payload["resource_digest"])
			self.assertEqual(payload["resource_digest"], row["resource_digest"])
			self.assertEqual(payload["resource_type"], NSSF_RESOURCE_SPECS[rid]["resource_type"])
			digests.append(payload["resource_digest"])
		self.assertEqual(descriptor_set_digest(digests), meta["descriptor_set_digest"])
		self.assertEqual(tuple(r["resource_id"] for r in meta["resources"]), NSSF_RESOURCE_ORDER)

	def test_superseded_digests_absent_from_active_fixture_oracles(self):
		"""Orphaned §7 constants live only in the historical erratum, not active oracles."""
		meta_text = (Path(fixtures_root()) / "nssf_calibration" / "resource_digest_meta.json").read_text()
		source_text = (Path(fixtures_root()) / "nssf_calibration" / "source_set.json").read_text()
		orphaned = [
			"76cd5d03583c4c4d042215b212a3b14925284cc6dbf57a5b8486cb0d7d441793",
			"9532a6c363914f10f94af53a832d49e5899e72821cae9361a9608e49bbbf047c",
			"461ffc824759f767f01bdfa9be77b3280da8020267d4743cd5ca7f9fb03ffa22",
		]
		for h in orphaned:
			self.assertNotIn(h, meta_text)
			self.assertNotIn(h, source_text)

	def test_nssf_resource_digest_reproducibility(self):
		"""Delete generated copies, reload frozen arrays, reproduce digests exactly."""
		root = Path(fixtures_root()) / "nssf_calibration" / "resources"
		meta = load_json("nssf_calibration/resource_digest_meta.json")
		with tempfile.TemporaryDirectory() as tmp:
			tmpdir = Path(tmp)
			for rid in NSSF_RESOURCE_ORDER:
				shutil.copy(root / f"{rid}.json", tmpdir / f"{rid}.json")
			# "delete generated outputs" then reload only frozen arrays
			recomputed = []
			for rid in NSSF_RESOURCE_ORDER:
				payload = json.loads((tmpdir / f"{rid}.json").read_text(encoding="utf-8"))
				recomputed.append(logical_resource_digest(payload["items"]))
			self.assertEqual(recomputed, [r["resource_digest"] for r in meta["resources"]])
			self.assertEqual(descriptor_set_digest(recomputed), meta["descriptor_set_digest"])

	def test_freeze_from_collections_matches_frozen_files(self):
		src = load_nssf_calibration_source_set()
		frozen = freeze_nssf_resources_from_collections(src.raw["collections"])
		self.assertEqual(frozen["__descriptor_set_digest__"], load_json("nssf_calibration/resource_digest_meta.json")["descriptor_set_digest"])
		for rid in NSSF_RESOURCE_ORDER:
			self.assertEqual(
				frozen[rid]["resource_digest"],
				json.loads((Path(fixtures_root()) / "nssf_calibration" / "resources" / f"{rid}.json").read_text())[
					"resource_digest"
				],
			)

	def test_chunk_validate_rejects_bad_indexes(self):
		with self.assertRaises(ValueError):
			validate_chunks(
				[
					{
						"index": 1,
						"content_ref": "bwmf-cas:v1:" + ("a" * 64),
						"item_count": 1,
						"chunk_content_digest": "sha256:" + ("b" * 64),
						"byte_size": 2,
					}
				],
				expected_item_count=1,
			)

	def test_carry_forward_and_scoring_oracles(self):
		coll = load_nssf_calibration_source_set().raw["collections"]
		self.assertEqual(sum(1 for r in coll["requirements"] if r.get("contract_carry_forward")), 117)
		self.assertEqual(sum(int(r["max_score"]) for r in coll["technical_scoring"]), 100)
		profile = load_nssf_calibration_source_set().raw["scoring_profile"]
		self.assertEqual(profile["maximum_score"], "100")
		self.assertEqual(profile["qualification_threshold"], "75")
