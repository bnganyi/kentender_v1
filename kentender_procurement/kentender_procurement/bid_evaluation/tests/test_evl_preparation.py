# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EnsureEvaluationPreparation (EVL-CHG-001 v0.4 §5.1, §7.2, §7.3 rows 1–2;
tracker EVL4-401, EVL4-402, EVL4-410; acceptance EVL-A16 (service part)).

The first authoritative publication of an in-scope tender records one
preparation case and the Accounting Officer's and Head of Procurement's
tasks; a replay creates nothing new; a known unsupported scope creates no
case and no task; missing scope metadata creates a named issue for the
Tenders owner and no case until repaired and retried; a cancelled tender is
never prepared."""

from __future__ import annotations

import frappe

from kentender_core.services import support_issues
from kentender_procurement.bid_evaluation.services import my_work_provider, preparation
from kentender_procurement.bid_evaluation.tests.support import AO, HOP, EvaluationCase


def titles(user: str) -> dict[str, list[str]]:
	rows = my_work_provider.my_work_rows(user)
	return {k: [r["title"] for r in v if r["module"] == "Bid Evaluation"] for k, v in rows.items()}


class TestPreparation(EvaluationCase):
	def set_tender(self, field: str, value) -> None:
		previous = frappe.db.get_value("Tender", self.name, field)
		self.addCleanup(frappe.db.set_value, "Tender", self.name, field, previous)
		frappe.db.set_value("Tender", self.name, field, value)

	def test_publication_prepares_one_case_with_the_setup_tasks(self):
		out = preparation.ensure_preparation(tender=self.name)
		self.assertTrue(out["prepared"], out)
		doc = frappe.get_doc("Evaluation Case", out["evaluation"])
		self.assertEqual((doc.state, doc.prepared_from, doc.evaluation_id), ("Preparing", "Publication", f"EVL-{self.reference.removeprefix('TND-')}"))
		self.assertTrue(doc.validity_end)
		self.assertIsNone(doc.evaluation_deadline)
		proceeding = frappe.db.get_value("Proceeding", doc.proceeding, ["proceeding_type", "state", "owner_type"], as_dict=True)
		self.assertEqual((proceeding.proceeding_type, proceeding.state, proceeding.owner_type), ("Bid Evaluation", "Open", "Evaluation Case"))
		# a replay or an addendum creates nothing new
		again = preparation.ensure_preparation(tender=self.name)
		self.assertEqual((again["prepared"], again["evaluation"]), (False, doc.name))
		self.assertEqual(frappe.db.count("Evaluation Case", {"tender": self.name}), 1)
		self.assertIn(f"Appoint evaluation committee for {self.reference}", titles(AO)["assigned"])
		# the Head is recorded as secretary when the committee is appointed: no secretary task, no waiting item (EVL-CHG-001 v0.8 §3, EVL-A20)
		self.assertEqual([t for t in titles(HOP)["assigned"] if "secretary" in t.lower()], [])
		self.assertNotIn("Waiting for committee appointment", titles(HOP)["waiting"])
		self.assertNotIn("Waiting for secretary appointment", titles(AO)["waiting"])
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": HOP, "subject": f"Assign evaluation secretary for {self.reference}"}), 0)
		# one courtesy notice per person, even after the replay
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": AO, "subject": f"Appoint evaluation committee for {self.reference}"}), 1)

	def test_a_known_unsupported_scope_prepares_nothing(self):
		self.set_tender("product_key", "WORKS-OPEN-V1")
		out = preparation.ensure_preparation(tender=self.name)
		self.assertEqual((out["prepared"], out["reason"]), (False, "out_of_scope"))
		self.assertFalse(frappe.db.exists("Evaluation Case", {"tender": self.name}))
		self.assertNotIn(f"Appoint evaluation committee for {self.reference}", titles(AO)["assigned"])

	def test_missing_scope_metadata_is_the_tenders_owners_issue_until_repaired(self):
		self.set_tender("product_key", "")
		out = preparation.ensure_preparation(tender=self.name)
		self.assertEqual((out["prepared"], out["reason"]), (False, "scope_unresolved"))
		self.assertFalse(frappe.db.exists("Evaluation Case", {"tender": self.name}))
		issue = support_issues.get(out["issue"])
		self.assertEqual((issue["status"], issue["holder_role"]), ("Open", "Head of Procurement Function"))
		self.assertEqual(preparation.ensure_preparation(tender=self.name)["issue"], out["issue"])  # the same issue, not a second
		frappe.db.set_value("Tender", self.name, "product_key", "IT-EQUIPMENT-OPEN-V1")
		repaired = preparation.ensure_preparation(tender=self.name)
		self.assertTrue(repaired["prepared"], repaired)
		self.assertEqual(support_issues.get(out["issue"])["status"], "Resolved")

	def test_a_cancelled_tender_is_never_prepared(self):
		self.set_tender("overall_status", "Cancelled")
		out = preparation.ensure_preparation(tender=self.name)
		self.assertEqual((out["prepared"], out["reason"]), (False, "cancelled"))
		self.assertFalse(frappe.db.exists("Evaluation Case", {"tender": self.name}))
