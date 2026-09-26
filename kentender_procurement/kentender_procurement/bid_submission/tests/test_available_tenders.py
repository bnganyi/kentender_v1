# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §7.1 `GetAvailableTenders` / §10.2 BDS-DES-01 and the
portal walking skeleton (plan Phase 2C, BDS8-205): the public list read over
the Tenders projection, its filters, the `/tenders` surface resolver and
the page a guest receives. Built on a Tender published by the Tenders
fixtures (this bench has no test rollback; the Tenders fixtures wipe and
restore their own world)."""

from __future__ import annotations

import json
import re

import frappe
from frappe.utils import set_request
from frappe.website.serve import get_response

from kentender_procurement.bid_submission import api, portal
from kentender_procurement.bid_submission.services import reads
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase

ROW_KEYS = {"reference", "title", "procuring_entity", "method", "reservation", "submission_deadline_label", "href"}
LEAK = re.compile(r"\bTD[RVPAC]-\d|\bTBD-|stdr-|PBD-|/private/|file_url|\b[0-9a-f]{64}\b")


class AvailableTendersCase(OpenPeriodCase):
	def setUp(self):
		super().setUp()
		self.reference = self._root().tender_reference
		frappe.flags.kt_bds_clock = "2027-05-20 10:00:00"
		self.addCleanup(setattr, frappe.flags, "kt_bds_clock", None)

	def _mine(self, result):
		return [r for r in result["rows"] if r["reference"] == self.reference]


class TestGetAvailableTenders(AvailableTendersCase):
	def test_open_rows_are_display_ready_and_carry_nothing_internal(self):
		result = reads.get_available_tenders()
		mine = self._mine(result)
		self.assertEqual(len(mine), 1)
		self.assertEqual(set(mine[0]), ROW_KEYS)
		self.assertEqual(
			(mine[0]["title"], mine[0]["method"], mine[0]["submission_deadline_label"], mine[0]["href"]),
			("Supply and delivery of business laptops", "Open Tender", "5 Jun 2027, 11:00 EAT", f"/tenders/{self.reference}"),
		)
		n = len(result["rows"])
		self.assertEqual(result["count_text"], f"{n} available Tender" + ("" if n == 1 else "s"))
		self.assertEqual(result["empty_text"], "")
		self.assertIsNone(LEAK.search(json.dumps(result)))

	def test_filters_narrow_the_list_and_an_empty_result_says_so(self):
		self.assertTrue(self._mine(reads.get_available_tenders(search="LAPTOPS")))
		self.assertTrue(self._mine(reads.get_available_tenders(search=self.reference.lower())))
		self.assertTrue(self._mine(reads.get_available_tenders(method="Open Tender")))
		reservation = self._mine(reads.get_available_tenders())[0]["reservation"]
		self.assertTrue(self._mine(reads.get_available_tenders(reservation=reservation)))
		self.assertFalse(self._mine(reads.get_available_tenders(reservation="Not a category")))
		empty = reads.get_available_tenders(search="no tender is called this")
		self.assertEqual((empty["rows"], empty["empty_text"]), ([], "No Tenders match these filters."))
		self.assertEqual(empty["applied"], {"search": "no tender is called this", "method": "", "reservation": "", "closing": "open"})

	def test_closing_follows_trusted_time_and_unknown_values_fall_back_to_open(self):
		frappe.flags.kt_bds_clock = "2027-06-05 11:00:00"
		self.assertFalse(self._mine(reads.get_available_tenders()))
		self.assertTrue(self._mine(reads.get_available_tenders(closing="closed")))
		self.assertTrue(self._mine(reads.get_available_tenders(closing="all")))
		self.assertEqual(reads.get_available_tenders(closing="whatever")["applied"]["closing"], "open")

	def test_filter_options_lead_with_all_and_list_what_exists(self):
		options = reads.get_available_tenders()["options"]
		self.assertEqual(options["method"][0], {"value": "", "label": "All methods"})
		self.assertEqual(options["reservation"][0], {"value": "", "label": "All categories"})
		self.assertIn({"value": "Open Tender", "label": "Open Tender"}, options["method"])
		self.assertEqual([o["value"] for o in options["closing"]], ["open", "closed", "all"])
		self.assertEqual(options["closing"][0]["label"], "Open Tenders")


class TestTendersSurface(AvailableTendersCase):
	def test_the_resolver_answers_the_list_and_masks_other_paths_for_now(self):
		answer = portal.resolve(path="/tenders", query={"search": "laptops"}, user="Guest")
		self.assertEqual((answer["verdict"], answer["title"], answer["payload"]["screen"]), ("OK", "Available Tenders", "available-tenders"))
		self.assertEqual(answer["payload"]["data"]["applied"]["search"], "laptops")
		self.assertEqual(portal.resolve(path="/tenders/NOT-A-TENDER", query={}, user="Guest")["verdict"], "NOT_FOUND")

	def test_the_api_is_open_to_guests_and_returns_the_same_read(self):
		self.assertIn(api.get_available_tenders, frappe.guest_methods)
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")
		self.assertEqual(api.get_available_tenders(search="laptops"), reads.get_available_tenders(search="laptops"))

	def test_a_guest_receives_the_portal_page_with_the_first_payload(self):
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")
		set_request(method="GET", path="/tenders")
		response = get_response()
		html = response.get_data(as_text=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn('data-kt-portal-surface="tenders"', html)
		self.assertIn("bid_portal", html)
		self.assertIn(self.reference, html)
		self.assertIn('data-kt-portal-nav="tenders" aria-current="page"', html)
		self.assertIsNone(LEAK.search(html.split('id="kt-portal-initial">', 1)[1].split("</script>", 1)[0]))
