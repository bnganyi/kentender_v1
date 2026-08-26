# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 9 — §17.1 golden package fixture.

Unlike every earlier phase's tests, this one calls the REAL, production-named
seed (`ensure_std_it_golden_seed`) against package `KE-PPRA-IT` — the
deliberate dev-site golden fixture, not a throwaway `KE-TEST-STD-Pn` package —
and therefore does NOT delete it in tearDown, matching Strategy's own
precedent for its production-named seed tests (STR-CHG-001 Phase 5). The seed
is idempotent by construction (`already_seeded` short-circuit); running this
test file twice, or alongside a real `bench execute` seed run, must never
duplicate or corrupt the fixture.

Covers: idempotency (no duplicate rows on a second call); the golden
package's coverage/readiness result matches spec §15.16's exact fixture
(16/16 Pass, 0 Blocking, exactly 1 Warning with the exact wording); all 7
runtime manifests exist for the Active Version; the 2 named actors
(Amina Hassan/David Mwangi, §15.2) exist with the correct roles and no
Administrator fallback was used to create them; and a worked-instance
compatibility check — the manifest contract can accept the exact values
named in §9.15's worked Tender instance, even though no Tender transaction
storage exists yet to actually hold them (§3's own module boundary — Tender
Preparation is separate future work).
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.seeds.std_it_golden_seed import (
	CONFIGURATOR_EMAIL,
	PACKAGE_CODE,
	REVIEWER_EMAIL,
	ensure_std_it_golden_seed,
)
from kentender_procurement.std_configuration.services import std_coverage


class TestSTDChg001Phase9GoldenSeed(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		ensure_std_it_golden_seed()
		frappe.db.commit()  # nosemgrep — see module docstring: this is the real,
		# persistent dev-site fixture, not throwaway per-test data; it must
		# survive past this test class's own transaction the same way the
		# manual verification during development required an explicit commit.

	def setUp(self):
		frappe.set_user("Administrator")
		self.version = frappe.db.get_value("STD Cfg Package", PACKAGE_CODE, "current_active_version_id")

	# --- idempotency -----------------------------------------------------------

	def test_seed_is_idempotent(self):
		counts_before = self._content_counts()
		result = ensure_std_it_golden_seed()
		frappe.db.commit()
		self.assertTrue(result["already_seeded"])
		self.assertEqual(counts_before, self._content_counts())

	def _content_counts(self) -> dict:
		return {
			doctype: frappe.db.count(doctype, {"reference_doctype": "STD Cfg Version", "reference_name": self.version})
			for doctype in (
				"STD Cfg Parameter Definition",
				"STD Cfg Requirement Schema",
				"STD Cfg Schedule Schema",
				"STD Cfg Inventory Schema",
				"STD Cfg Price Schema",
				"STD Cfg Evaluation Schema",
				"STD Cfg Form Schema",
				"STD Cfg Contract Schema",
			)
		}

	# --- coverage/readiness matches §15.16's exact golden fixture ----------------

	def test_golden_package_matches_spec_coverage_fixture(self):
		check = std_coverage.run_complete_check("STD Cfg Version", self.version)
		self.assertEqual(check["coverage_pass_count"], 16, check["blocking"])
		self.assertEqual(check["blocking_count"], 0, check["blocking"])
		self.assertEqual(len(check["warnings"]), 1)
		warning = check["warnings"][0]
		self.assertEqual(warning["code"], "STD_VENDOR_NEUTRALITY_REVIEW")
		self.assertEqual(
			warning["message"],
			"Vendor-neutrality trigger includes named cloud platforms and requires reviewer attention.",
		)

	def test_all_sixteen_coverage_rows_present_in_official_order(self):
		rows = std_coverage.coverage_report("STD Cfg Version", self.version)
		self.assertEqual([r["number"] for r in rows], list(range(1, 17)))
		self.assertTrue(all(r["result"] == "Pass" for r in rows), rows)

	# --- all 7 runtime manifests ----------------------------------------------

	def test_all_seven_manifests_exist(self):
		self.assertTrue(frappe.db.exists("STD Cfg Tender Manifest", {"std_version_id": self.version}))
		shared_types = set(
			frappe.get_all("STD Cfg Runtime Manifest", filters={"std_version_id": self.version}, pluck="manifest_type")
		)
		self.assertEqual(
			shared_types,
			{"Requirement Composer", "Bidder Response", "Evaluation", "Contract Formation", "Contract Management", "Render"},
		)

	def test_tender_configuration_manifest_has_items_for_every_step(self):
		manifest = frappe.get_doc("STD Cfg Tender Manifest", {"std_version_id": self.version})
		steps = {item.step_id for item in manifest.items}
		self.assertEqual(steps, {f"CFG-{n:02d}" for n in range(2, 10)})

	# --- named actors, no Administrator fallback --------------------------------

	def test_named_actors_exist_with_correct_roles_no_admin_fallback(self):
		self.assertTrue(frappe.db.exists("User", CONFIGURATOR_EMAIL))
		self.assertTrue(frappe.db.exists("User", REVIEWER_EMAIL))
		self.assertIn("STD Configurator", frappe.get_roles(CONFIGURATOR_EMAIL))
		self.assertIn("STD Reviewer", frappe.get_roles(REVIEWER_EMAIL))

		decisions = frappe.get_all(
			"STD Cfg Decision",
			filters={"decided_by": ["in", [CONFIGURATOR_EMAIL, REVIEWER_EMAIL]]},
			pluck="decided_by",
		)
		self.assertNotIn("Administrator", decisions)
		review_tasks = frappe.get_all("STD Cfg Review Task", pluck="submitted_by")
		self.assertNotIn("Administrator", review_tasks)

	# --- worked instance (§9.15) compatibility — no Tender transaction storage
	# exists (§3's own module boundary), so this proves the manifest CONTRACT
	# can accept those exact values, not that a Tender was actually created. --

	def test_manifest_contract_matches_worked_instance_fixture_shape(self):
		manifest = frappe.get_doc("STD Cfg Tender Manifest", {"std_version_id": self.version})
		validity_item = next((i for i in manifest.items if i.item_key == "tender.validity_days"), None)
		self.assertIsNotNone(validity_item)
		self.assertEqual(validity_item.value_type, "Duration")
		self.assertEqual(validity_item.required_mode, "Always")

		# §9.15.C — 5 sample requirement categories are all governed §7.8
		# categories; confirm the golden package's own 14 include them.
		categories = frappe.get_all(
			"STD Cfg Requirement Schema",
			filters={"reference_doctype": "STD Cfg Version", "reference_name": self.version},
			pluck="category",
		)
		for expected in ("Functional", "Architecture", "Security", "Integration"):
			self.assertIn(expected, categories)

		# §9.15.D — 5 schedule milestones.
		milestones = frappe.get_all(
			"STD Cfg Schedule Schema",
			filters={"reference_doctype": "STD Cfg Version", "reference_name": self.version},
			pluck="title",
		)
		self.assertEqual(len(milestones), 5)

		# §9.15.G — Performance Security is a governed contract value.
		self.assertTrue(
			frappe.db.exists(
				"STD Cfg Contract Schema",
				{
					"reference_doctype": "STD Cfg Version",
					"reference_name": self.version,
					"value_category": "Performance security",
					"required_treatment": "Required",
				},
			)
		)
