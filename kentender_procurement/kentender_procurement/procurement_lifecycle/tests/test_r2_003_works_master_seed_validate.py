# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-003 — WORKS master seed validator (VAL-SEED-001–022, OPEN-001–006)."""

from __future__ import annotations

import unittest

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
	validate_procurement_lifecycle_works_master_seed,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_loader import run_load


class TestR2003UnsupportedCheckpoint(unittest.TestCase):
	def test_unknown_checkpoint_returns_error_dict(self):
		out = validate_procurement_lifecycle_works_master_seed(checkpoint="PHANTOM")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "UNSUPPORTED_CHECKPOINT")


class TestR2003ValidateResponseShape(IntegrationTestCase):
	def test_tender_published_returns_twenty_two_checks(self):
		out = validate_procurement_lifecycle_works_master_seed(checkpoint="TENDER_PUBLISHED")
		self.assertIn("checks", out)
		self.assertEqual(len(out["checks"]), 22)
		ids = [c["check_id"] for c in out["checks"]]
		self.assertEqual(ids[0], "VAL-SEED-001")
		self.assertEqual(ids[-1], "VAL-SEED-022")
		for c in out["checks"]:
			self.assertIn(c["result"], ("PASS", "FAIL"))
			self.assertIn("message", c)

	def test_opening_ready_includes_extra_open_checks(self):
		out = validate_procurement_lifecycle_works_master_seed(checkpoint="OPENING_READY")
		self.assertEqual(len(out["checks"]), 28)
		ids = [c["check_id"] for c in out["checks"]]
		self.assertIn("VAL-SEED-OPEN-006", ids)


class TestR2003ValidateAfterPlcLoad(IntegrationTestCase):
	"""PLC-only load satisfies handoff/journey subset; full PASS needs upstream seeds (LV-R2-001-03…09)."""

	def tearDown(self):
		run_load(reset=True, checkpoint="OPENING_READY")

	def test_after_plc_base_load_handoff_checks_can_pass(self):
		run_load(reset=True, checkpoint="TENDER_PUBLISHED")
		out = validate_procurement_lifecycle_works_master_seed(checkpoint="TENDER_PUBLISHED")
		by_id = {c["check_id"]: c for c in out["checks"]}
		for hid in ("VAL-SEED-001", "VAL-SEED-016", "VAL-SEED-017", "VAL-SEED-018", "VAL-SEED-019"):
			self.assertEqual(by_id[hid]["result"], "PASS", msg=f"{hid}: {by_id[hid]}")
