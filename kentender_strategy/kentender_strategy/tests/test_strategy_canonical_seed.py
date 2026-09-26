# Copyright (c) 2026, KenTender and contributors
"""The canonical Strategy world, as `make seed-canonical` leaves it
(STR-CHG-001 v1.8 §14.3; KT-STD-001 v1.8 §8.6). Reads the seeded site; the
one write (a changed title) is restored in cleanup.

Found 26 Sep 2026: Version 1's draft events carried the seeding day while
its submission and approval were back-stamped to 1 Jul 2023, so the history
showed the draft created three years after approval; and the validator
checked only that one namespaced plan with one Active version existed.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_strategy.seeds import kentender_mvp_v1_strategy as seed


def _canonical() -> tuple[str, str]:
	plan = frappe.db.get_value("Strategic Plan", {"fixture_namespace": seed.FIXTURE_NS}, "name")
	version = frappe.db.get_value("Strategic Plan Version", {"plan_id": plan, "version_number": 1}, "name")
	return plan, version


class TestCanonicalStrategySeed(IntegrationTestCase):
	def test_the_seeded_world_validates(self):
		failed = [row["check"] for row in seed.validate_strategy_seed() if not row["ok"]]
		self.assertEqual(failed, [])

	def test_version_1_history_happens_on_1_july_2023_in_order(self):
		plan, version = _canonical()
		self.assertEqual(str(frappe.db.get_value("Strategic Plan", plan, "creation"))[:10], "2023-07-01")
		events = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Strategic Plan Version", "document_name": version},
			fields=["action", "timestamp", "performed_by"],
			order_by="creation asc",
		)
		self.assertTrue(events)
		self.assertTrue(all(str(e.timestamp)[:10] == "2023-07-01" for e in events), [(e.action, str(e.timestamp)) for e in events])
		stamps = [e.timestamp for e in events]
		self.assertEqual(stamps, sorted(stamps), "the recorded order and the recorded times disagree")
		by_action = {e.action: e for e in events}
		self.assertEqual(str(by_action["Submit for approval"].timestamp)[:16], "2023-07-01 08:30")
		self.assertEqual(by_action["Submit for approval"].performed_by, seed.AUTHOR)
		self.assertEqual(str(by_action["Approve"].timestamp)[:16], "2023-07-01 09:15")
		self.assertEqual(by_action["Approve"].performed_by, seed.APPROVER)

	def test_the_validator_fails_closed_on_a_changed_plan(self):
		plan, _version = _canonical()
		title = frappe.db.get_value("Strategic Plan", plan, "title")
		self.addCleanup(frappe.db.set_value, "Strategic Plan", plan, "title", title, update_modified=False)
		frappe.db.set_value("Strategic Plan", plan, "title", f"{title} — changed", update_modified=False)
		self.assertIn(False, [row["ok"] for row in seed.validate_strategy_seed()])
