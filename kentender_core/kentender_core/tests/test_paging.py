"""The table-pagination standard's server arithmetic: ten rows by default, a page
size from a fixed offer, a page past the end clamped to the last, and a total
that is what matched, not what exists.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_paging
"""

from __future__ import annotations

import unittest

from kentender_core.services.paging import DEFAULT_PAGE_SIZE, PAGE_SIZES, page_of


class TestPageOf(unittest.TestCase):
	rows = list(range(47))

	def test_the_standard_offer_and_default(self):
		self.assertEqual((DEFAULT_PAGE_SIZE, PAGE_SIZES), (10, (10, 25, 50, 100)))

	def test_defaults_to_the_first_ten(self):
		shown, paging = page_of(self.rows)
		self.assertEqual(shown, list(range(10)))
		self.assertEqual(paging, {"page": 1, "page_size": 10, "total": 47, "pages": 5})

	def test_a_later_page_and_a_short_last_page(self):
		self.assertEqual(page_of(self.rows, page=2)[0], list(range(10, 20)))
		shown, paging = page_of(self.rows, page=5)
		self.assertEqual((shown, paging["page"]), (list(range(40, 47)), 5))

	def test_a_page_past_the_end_clamps_and_a_page_below_one_is_one(self):
		self.assertEqual(page_of(self.rows, page=999)[1]["page"], 5)
		self.assertEqual(page_of(self.rows, page=0)[1]["page"], 1)
		self.assertEqual(page_of(self.rows, page=-3)[1]["page"], 1)

	def test_a_page_size_outside_the_offer_falls_back_to_ten(self):
		self.assertEqual(page_of(self.rows, page_size=7)[1]["page_size"], 10)
		self.assertEqual(page_of(self.rows, page_size=100000)[1]["page_size"], 10)
		self.assertEqual(page_of(self.rows, page_size=25)[1]["pages"], 2)

	def test_values_arrive_as_text_from_a_json_request(self):
		shown, paging = page_of(self.rows, page="2", page_size="25")
		self.assertEqual((len(shown), paging["page"], paging["page_size"]), (22, 2, 25))
		self.assertEqual(page_of(self.rows, page="abc", page_size=None)[1]["page"], 1)

	def test_no_rows_is_one_empty_page(self):
		self.assertEqual(page_of([]), ([], {"page": 1, "page_size": 10, "total": 0, "pages": 1}))
