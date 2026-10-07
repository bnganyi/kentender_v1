# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget's published funding read for Evaluation and Award (AUD-EVL-014): it
answers as Budget, independent of the session user's Budget roles, and never
guesses about a reservation it cannot find."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.services.budget_funding_read import read_reservation_funding


class TestFundingRead(IntegrationTestCase):
	def test_nothing_named_or_unknown_is_not_known(self):
		self.assertEqual(read_reservation_funding([]), {"known": False, "rows": [], "missing": []})
		self.assertEqual(read_reservation_funding(["NO-SUCH-RESERVATION"]), {"known": False, "rows": [], "missing": ["NO-SUCH-RESERVATION"]})

	def test_a_reservation_reads_the_same_for_any_session_user(self):
		name = frappe.db.get_value("Funding Reservation", {}, "name")
		if not name:
			self.skipTest("this site holds no Funding Reservation")
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")
		out = read_reservation_funding([name, name, "NO-SUCH-RESERVATION"])
		self.assertEqual((out["known"], out["missing"], [r["id"] for r in out["rows"]]), (False, ["NO-SUCH-RESERVATION"], [name]))
		self.assertTrue(read_reservation_funding([name])["known"])
		self.assertEqual(set(read_reservation_funding([name])["rows"][0]), {"id", "code", "status", "original_amount", "remaining_amount"})
