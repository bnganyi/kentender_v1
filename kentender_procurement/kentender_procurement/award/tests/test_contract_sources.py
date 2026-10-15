# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 19.4 (plan D20; tracker CM8-513, CM8-515 to CM8-518): Award's provider of the contract's source material, on the canonical laptop award.

Level L2: nothing here is synthetic. The canonical award (AWD-MOH-2026-002, tender TND-MOH-2026-002, Afya Digital Supplies Limited, KES 46,400,000) is asked for each of the twelve sources through the
owners' published seams (Tenders, Bid Evaluation, the site configuration, Supplier Accounts, Budget). The assertions are the **present truth**, including the sources that cannot yet be given and why:
S9 (the award draws on two reservations and nobody has allocated the price between them) and S10 (the entity's principal address is not held in its site configuration). S7 is served: the issued
Form No. 4 is a recorded tender document, byte for byte; that its blanks are not declared as insertions is what Contract Management's own coverage check reports."""

from __future__ import annotations

import hashlib
import json
import unittest
import unittest.mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import contract_source_contract as seam
from kentender_procurement.award.services import contract_sources, eligibility

AWARD = "AWD-MOH-2026-002"
GAPS = {"S9", "S10"}  # S7 is built (the issued Form No. 4 is served byte for byte); whether it can be generated into an agreement is Contract Management's coverage check


class TestAwardContractSources(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Award Case", AWARD):
			raise unittest.SkipTest("the canonical award is not on this site")

	def doc(self):
		return frappe.get_doc("Award Case", AWARD)

	def test_every_source_the_owners_can_give_is_built_and_the_rest_say_why_and_whose_they_are(self):
		rows = {r["source"]: r for r in contract_sources.Provider().references(award_case=AWARD)}
		self.assertEqual(list(rows), [f"S{n}" for n in range(1, 13)])
		self.assertEqual({n for n, r in rows.items() if "unavailable" in r}, GAPS)
		for number, row in rows.items():
			self.assertEqual(row["reference"], f"{number}-{AWARD}")
			self.assertTrue(row["owner"] and row["category"])
			if number not in GAPS:
				self.assertTrue(row["version"] and row["media_type"] and row["size"], number)
		self.assertNotIn("sha256", rows["S12"], "a restriction is a live fact, not 'a source that changed after the award'")
		for number in set(rows) - GAPS - {"S12"}:
			self.assertEqual(len(rows[number]["sha256"]), 64, number)
		self.assertIn("2 reservations", rows["S9"]["unavailable"])
		self.assertIn("principal address", rows["S10"]["unavailable"])

	def test_what_is_described_is_what_is_fetched_and_it_does_not_change_with_the_clock(self):
		provider = contract_sources.Provider()
		for number in ("S1", "S3", "S8", "S11"):
			described, fetched = provider.describe(reference=f"{number}-{AWARD}"), provider.fetch(reference=f"{number}-{AWARD}")
			self.assertEqual(hashlib.sha256(fetched["content"]).hexdigest(), described["sha256"], number)
		before = provider.describe(reference=f"S11-{AWARD}")["sha256"]
		frappe.flags.kt_cm_clock = "2031-01-01 09:00:00"
		self.addCleanup(lambda: setattr(frappe.flags, "kt_cm_clock", None))
		self.assertEqual(provider.describe(reference=f"S11-{AWARD}")["sha256"], before, "who could sign is read at the instant Award retains, not at 'now'")

	def test_the_provider_answers_only_award_cases(self):
		provider = contract_sources.Provider()
		self.assertIsNone(provider.describe(reference="S1-NO-SUCH-AWARD"))
		self.assertIsNone(provider.describe(reference=f"S99-{AWARD}"))
		self.assertIsNone(provider.fetch(reference="not a reference"))
		self.assertEqual(provider.references(award_case="NO-SUCH-AWARD"), [])

	def test_the_awarded_terms_are_the_issued_and_accepted_ones(self):
		def source(number):
			return json.loads(seam.fetch(f"{number}-{AWARD}")["content"])

		price = source("S3")["lines"][0]
		self.assertEqual((source("S3")["total"], price["quantity"], price["net_rate"], price["rate"], price["tax_amount"]), (46_400_000.0, 250, 160_000.0, 185_600.0, 6_400_000.0))
		conditions = source("S5")
		self.assertEqual((conditions["warranty"]["months"], conditions["payment"]["days"], conditions["performance_security"]["required"], conditions["performance_security"]["percentage"]), (36, 30, True, "10"))
		self.assertNotIn("advance", conditions, "an advance the conditions state only in prose is not invented as a value")
		schedule = source("S4")["delivery_schedule"]
		self.assertEqual(schedule["due"], "2027-06-30")
		self.assertIn("3rd Floor Procurement Stores", schedule["destination"], "the addendum is applied")
		self.assertEqual(source("S1")["addenda"][0]["reference"], "ADD-MOH-2026-002-001")
		criteria = source("S6")
		self.assertIn("Memory", [c["name"] for c in criteria["criteria"]])
		self.assertTrue(criteria["untyped"], "the acceptance checks stated only as text are carried untyped")
		accepted = source("S2")
		self.assertEqual((accepted["bid"]["reference"], accepted["bid"]["submitted_total"]), ("BID-MOH-2026-002-001", "46400000.00"))
		self.assertEqual(source("S8")["signing_window"]["earliest_signing_at"], "2027-07-02 09:00:00")
		self.assertEqual([s["name"] for s in source("S11")["signatories"]], ["Mary Wanjiku"])

	def test_the_package_award_freezes_carries_the_unit_and_every_reference(self):
		package = eligibility._content(self.doc())
		self.assertTrue(package["managing_unit"])
		self.assertEqual([r["source"] for r in package["handoff"]], [f"S{n}" for n in range(1, 13)])
		self.assertEqual({r["source"] for r in package["handoff"] if "unavailable" in r}, GAPS)
		for key in ("award_case", "tender", "decision", "notice_batch", "restrictions", "legal_profile"):
			self.assertIn(key, package, "what the package carried before is still carried")

	def test_a_source_that_cannot_be_built_is_reported_not_raised(self):
		with unittest.mock.patch.dict(contract_sources.BUILDERS, {"S9": lambda doc: (_ for _ in ()).throw(contract_sources.Unavailable("Budget did not answer."))}):
			row = next(r for r in contract_sources.Provider().references(award_case=AWARD) if r["source"] == "S9")
		self.assertEqual(row["unavailable"], "Budget did not answer.")
