# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §16 — deterministic seed contract (tracker TPR-601..603).

Mirrors Requisitions' own `test_requisitions_seed.py`: a static contract
proven independent of any seeded world, and a world-dependent class skipped
unless the canonical MOH Planning baseline is live on this site. Never run
in the same session as the other Tender Preparation modules' `TenderCase`
(its `wipe_all()` is a site-wide Requisitions wipe) with a live seed you
mean to keep."""

from __future__ import annotations

import ast
import os
import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_preparation.seeds import kentender_mvp_v1 as seed

SEED_PATH = os.path.abspath(seed.__file__)


def _world_available() -> bool:
	try:
		seed.verify_prerequisites()
		return True
	except Exception:
		return False


class TestSeedStaticContract(IntegrationTestCase):
	def test_the_seed_never_writes_a_sibling_module_row_directly(self):
		source = open(SEED_PATH, encoding="utf-8").read()
		# spelled by concatenation so this module never trips its own scan
		for token in ('set_value("Authorised ' + 'Requisition Handoff"', 'set_value("Procurement ' + 'Requisition"', 'set_value("Annual ' + 'Plan Item"', 'set_value("Funding ' + 'Reservation"'):
			self.assertNotIn(token, source, token)

	def test_the_seed_reaches_siblings_only_through_published_seams(self):
		tree = ast.parse(open(SEED_PATH, encoding="utf-8").read())
		imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
		for forbidden in ("kentender_procurement.procurement_planning.doctype", "kentender_budget.doctype", "kentender_procurement.procurement_requisitions.doctype", "kentender_procurement.procurement_requisitions.services"):
			self.assertTrue(all(not m.startswith(forbidden) for m in imported), forbidden)
		self.assertTrue(any(m.startswith("kentender_procurement.tender_preparation.services") for m in imported))

	def test_the_clock_matches_section_16_2(self):
		self.assertEqual(seed.CLOCK["draft_created"], "2027-03-20 09:00:00")
		self.assertEqual(seed.CLOCK["submitted"], "2027-03-20 11:40:00")
		self.assertEqual(seed.CLOCK["returned"], "2027-03-25 14:00:00")
		self.assertEqual(seed.CLOCK["resubmitted"], "2027-04-15 09:15:00")
		self.assertEqual(seed.CLOCK["approved"], "2027-04-20 10:00:00")
		self.assertEqual(seed.CLOCK["consumed"], "2027-05-15 08:00:00")
		self.assertEqual(seed.PUBLISHED_ON, "2027-05-15")
		self.assertEqual(seed.OFFICER, "brian.wafula@moh.example.test")
		self.assertEqual(seed.HOPF, "charles.mutiso@moh.example.test")


@unittest.skipUnless(_world_available(), "the KENTENDER_MVP_V1 Planning/Requisitions world is not seeded on this site (make seed-kentender-mvp-v1)")
class TestSeededWalkthrough(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		seed.reset_tender_preparation_seed(commit=False)
		cls.result = seed.upsert_tender_preparation(commit=False)

	def test_the_walkthrough_validates_green(self):
		failures = [c for c in seed.validate_tender_preparation_seed() if not c["ok"]]
		self.assertEqual(failures, [])

	def test_a_rerun_is_idempotent(self):
		before = frappe.db.count("Tender Preparation Version", {"tender": self.result["tender"]})
		again = seed.upsert_tender_preparation(commit=False)
		self.assertTrue(again["idempotent"])
		self.assertEqual(again["tender"], self.result["tender"])
		self.assertEqual(frappe.db.count("Tender Preparation Version", {"tender": self.result["tender"]}), before)
		self.assertEqual(frappe.db.count("Tender Publication Handoff", {"tender": self.result["tender"]}), 1)

	def test_the_consumption_is_real(self):
		handoff = frappe.db.get_value("Authorised Requisition Handoff", self.result["handoff"], ["tender", "consumed_at"], as_dict=True)
		self.assertEqual(handoff.tender, self.result["tender"])
		self.assertTrue(str(handoff.consumed_at).startswith("2027-03-20 09:00"))

	def test_the_stopped_version_profile_is_mutually_exclusive_and_restorable(self):
		before = self._digests(self.result["tender"])
		self.assertTrue(before)
		profile = seed.seed_upstream_correction_profile(commit=False)
		self.assertEqual(frappe.db.get_value("Tender Preparation Version", profile["tender_version"], "version_status"), "Upstream correction required")
		self.assertEqual(profile["handoff_release"], "released")
		self.assertFalse(frappe.db.get_value("Authorised Requisition Handoff", profile["handoff"], "consumed_at"))
		self.assertEqual(frappe.db.count("Prepared Tender", {"requisition_handoff": profile["handoff"]}), 1)
		# restore the integrated walkthrough for whatever runs next — and prove
		# TPR-AC-037: a clean rerun reproduces the same content, readiness and
		# snapshot digests. The publication package digest is NOT expected to
		# repeat: by design it binds the Tender and Version row identity and
		# the approval decision (serializer.package), which differ per run.
		seed.reset_tender_preparation_seed(commit=False)
		rebuilt = seed.upsert_tender_preparation(commit=False)
		self.assertFalse(rebuilt["idempotent"])
		self.assertEqual([c for c in seed.validate_tender_preparation_seed() if not c["ok"]], [])
		self.assertEqual(self._digests(rebuilt["tender"]), before)
		self.assertTrue(frappe.db.get_value("Tender Publication Handoff", {"tender": rebuilt["tender"]}, "package_digest"))

	@staticmethod
	def _digests(tender: str) -> list[tuple]:
		versions = frappe.get_all("Tender Preparation Version", filters={"tender": tender}, fields=["version_number", "content_digest", "readiness_digest", "snapshot_digest"], order_by="version_number asc")
		return [(v.version_number, v.content_digest, v.readiness_digest, v.snapshot_digest) for v in versions]
