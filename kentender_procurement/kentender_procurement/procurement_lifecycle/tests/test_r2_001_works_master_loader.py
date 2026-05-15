# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-001 — WORKS master seed loader contract tests."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
	load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
)
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
	WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)


class TestR2001UnsupportedCheckpoint(unittest.TestCase):
	def test_unknown_checkpoint_returns_error_dict(self):
		out = load_procurement_lifecycle_works_master(reset=False, checkpoint="PHANTOM")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "UNSUPPORTED_CHECKPOINT")


class TestR2001WorksMasterLoaderIntegration(IntegrationTestCase):
	def tearDown(self):
		load_procurement_lifecycle_works_master(reset=True, checkpoint="OPENING_READY")
		super().tearDown()

	def test_tender_published_load_creates_journey_steps_and_handoffs(self):
		out = load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")
		self.assertTrue(out.get("ok"), msg=out)
		self.assertEqual(out.get("journey_code"), JOURNEY_CODE)
		self.assertEqual(out["created_or_updated"].get("handoff_cards"), len(BASE_HANDOFF_CODES))
		self.assertEqual(out["created_or_updated"].get("journey_steps"), len(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER))

		j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
		self.assertEqual(cint(j.is_master_seed), 1)
		self.assertEqual(len(j.steps or []), len(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER))
		for hc in BASE_HANDOFF_CODES:
			self.assertTrue(frappe.db.exists("Procurement Handoff Card", hc))
			self.assertEqual(cint(frappe.db.get_value("Procurement Handoff Card", hc, "is_master_seed")), 1)

	def test_idempotent_reload(self):
		load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")
		out2 = load_procurement_lifecycle_works_master(reset=False, checkpoint="TENDER_PUBLISHED")
		self.assertTrue(out2.get("ok"))
		self.assertEqual(out2["created_or_updated"]["journey_records"], 1)

	def test_opening_ready_adds_optional_handoffs(self):
		out = load_procurement_lifecycle_works_master(reset=True, checkpoint="OPENING_READY")
		self.assertTrue(out.get("ok"))
		self.assertEqual(
			out["created_or_updated"]["handoff_cards"],
			len(BASE_HANDOFF_CODES) + len(OPENING_HANDOFF_CODES),
		)
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", "CLOSECERT-TND-MOH-2026-001"))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", "OPENREADY-TND-MOH-2026-001"))
		j = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
		self.assertEqual(j.current_stage_key, "opening_ready")
		closing_rows = [r for r in (j.steps or []) if r.step_key == "tender_closing"]
		self.assertEqual(len(closing_rows), 1)
		self.assertEqual(closing_rows[0].handoff_code, "CLOSECERT-TND-MOH-2026-001")
