# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §16 — deterministic seed contract (tracker REQ-401..403).

Mirrors Planning's own `test_planning_seed.py`: a static contract proven
independent of any seeded world, and a world-dependent class skipped unless
the canonical MOH baseline (Planning's own `make seed-kentender-mvp-v1`) is
already live on this site.

Not run alongside the rest of this app's test suite in the same session as
a live seeded fixture: every other Requisitions test module's `wipe_requisition_rows()`
is an unscoped delete across every Requisitions doctype (§ tracker note),
which would strand this seed's own live Planning drawdown / Budget
reservations exactly as it stranded a hand-built live fixture earlier this
build — always `reset_requisitions_seed()` (or accept the loss and reverse
it through `plan_requisition.reverse_requisition_drawdown` per orphaned
`Plan Drawdown Reference`) before or after running this suite alongside others."""

from __future__ import annotations

import ast
import os
import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.seeds import kentender_mvp_v1 as seed

SEED_PATH = os.path.abspath(seed.__file__)


def _world_available() -> bool:
	try:
		seed.verify_prerequisites()
		return True
	except Exception:
		return False


class TestSeedStaticContract(IntegrationTestCase):
	def test_the_seed_never_writes_a_planning_or_budget_position_field_directly(self):
		source = open(SEED_PATH, encoding="utf-8").read()
		# spelled by concatenation so this module never trips its own scan
		retired = ("frappe.db.set_value(\"Plan " + "Drawdown", "frappe.db.set_value(\"Funding " + "Reservation")
		for token in retired:
			self.assertNotIn(token, source, token)

	def test_the_seed_touches_planning_and_budget_only_through_published_services(self):
		"""§16.2/§16.5 — no direct Planning/Budget doctype module import;
		every position change is a real command, never a raw write."""
		tree = ast.parse(open(SEED_PATH, encoding="utf-8").read())
		imported = set()
		for node in ast.walk(tree):
			if isinstance(node, ast.ImportFrom) and node.module:
				imported.add(node.module)
		self.assertTrue(all(not m.startswith("kentender_procurement.procurement_planning.doctype") for m in imported))
		self.assertTrue(all(not m.startswith("kentender_budget.doctype") for m in imported))
		self.assertTrue(any(m.startswith("kentender_procurement.procurement_requisitions.services") for m in imported))

	def test_only_the_combined_item_is_ever_prepared_into_a_requisition(self):
		"""Decision D10 — the single-department item is Non-consulting
		services and REQ_PRODUCT_UNSUPPORTED refuses it; every profile
		function must target the combined item only."""
		source = open(SEED_PATH, encoding="utf-8").read()
		self.assertNotIn('prereqs["single_item"]', source)


@unittest.skipUnless(_world_available(), "the KENTENDER_MVP_V1 Requisitions world is not seeded on this site (make seed-kentender-mvp-v1)")
class TestSeedContract(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.baseline = seed.upsert_requisitions_base(commit=False)

	def test_prerequisites_resolve_the_authoritative_records(self):
		resolved = seed.verify_prerequisites()
		self.assertTrue(resolved["dhi"] and resolved["hrmd"] and resolved["single_item"] and resolved["combined_item"])

	def test_the_base_fixture_is_authorised_with_the_exact_16_3_package_and_16_4_timeline(self):
		failures = [row for row in seed.validate_requisitions_seed() if not row["ok"]]
		self.assertEqual(failures, [])

	def test_a_rerun_is_idempotent(self):
		before = frappe.db.count("Requisition Version", {"requisition": self.baseline["requisition"]})
		again = seed.upsert_requisitions_base(commit=False)
		self.assertTrue(again["idempotent"])
		self.assertEqual(again["requisition"], self.baseline["requisition"])
		self.assertEqual(frappe.db.count("Requisition Version", {"requisition": self.baseline["requisition"]}), before)

	def test_the_synthetic_consumption_is_retired_in_favour_of_tender_preparation(self):
		"""TPR-CHG-001 plan D19 — fixture 6 is a real Tender's consumption,
		seeded by Tender Preparation after this module; the old synthetic
		consumption refuses with the pointer."""
		with self.assertRaises(frappe.ValidationError) as caught:
			seed.seed_consumed_handoff(commit=False)
		self.assertIn("tender_preparation.seeds.kentender_mvp_v1.upsert_tender_preparation", str(caught.exception))


@unittest.skipUnless(_world_available(), "the KENTENDER_MVP_V1 Requisitions world is not seeded on this site (make seed-kentender-mvp-v1)")
class TestLifecycleProfiles(IntegrationTestCase):
	"""Each profile is mutually exclusive with the others and with the base
	fixture (Decision D10) — this class runs them in sequence, restoring the
	base fixture at the end for whatever runs next."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# A consumed base handoff cannot be reset to another profile (one-way
		# consumption, by design). Tender Preparation's §16 seed consumes it
		# on a seeded site; release it there first, never from here.
		plan_item_id = seed._plan_item_id(seed.COMBINED_ITEM_TITLE)
		consumed = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": "Authorised"}, "handoff_consumed_at")
		if consumed:
			raise unittest.SkipTest(
				"the canonical handoff is consumed by Tender Preparation's seed — run "
				"kentender_procurement.tender_preparation.seeds.kentender_mvp_v1.reset_tender_preparation_seed first"
			)

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		seed.reset_requisitions_seed(commit=False)
		seed.upsert_requisitions_base(commit=False)
		super().tearDownClass()

	def test_draft_profile(self):
		result = seed.seed_draft_profile(commit=False)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", result["requisition"], "current_state"), "Draft")

	def test_department_task_profile(self):
		result = seed.seed_department_task_profile(commit=False)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", result["requisition"], "current_state"), "Awaiting Department Approval")

	def test_procurement_task_profile(self):
		result = seed.seed_procurement_task_profile(commit=False)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", result["requisition"], "current_state"), "Submitted to Procurement")

	def test_returned_profile(self):
		result = seed.seed_returned_profile(commit=False)
		root = frappe.get_doc("Procurement Requisition", result["requisition"])
		self.assertEqual(root.current_version, result["correction_version"])
		self.assertEqual(frappe.db.get_value("Requisition Version", result["correction_version"], "version_status"), "Draft")

	def test_upstream_correction_profile(self):
		result = seed.seed_upstream_correction_profile(commit=False)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", result["requisition"], "current_state"), "Upstream correction required")
		self.assertTrue(frappe.db.exists("Plan Item Correction Request", result["correction_request"]))
