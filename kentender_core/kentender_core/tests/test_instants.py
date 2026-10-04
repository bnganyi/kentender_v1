# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Owner decision 26 Sep 2026 (FU-V127-01) — instants are stored in the site
timezone and cross module boundaries as ISO-8601 UTC; these two helpers are
the only conversion between the two."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_core.utils import instants


class TestInstants(IntegrationTestCase):
	def test_a_site_time_leaves_as_utc_and_comes_back_unchanged(self):
		with patch("kentender_core.utils.instants.get_system_timezone", return_value="Africa/Nairobi"):
			self.assertEqual(instants.to_utc_iso("2026-11-25 10:00:00"), "2026-11-25T07:00:00Z")
			self.assertEqual(instants.to_utc_iso(datetime(2026, 12, 31, 23, 30)), "2026-12-31T20:30:00Z")
			self.assertEqual(instants.from_utc_iso("2026-11-25T07:00:00Z"), datetime(2026, 11, 25, 10, 0))
			self.assertEqual(instants.from_utc_iso("2026-12-31T22:15:00+00:00"), datetime(2027, 1, 1, 1, 15))
			self.assertEqual(instants.from_utc_iso(instants.to_utc_iso("2026-09-26 00:56:12")), datetime(2026, 9, 26, 0, 56, 12))

	def test_empty_stays_empty(self):
		self.assertEqual(instants.to_utc_iso(None), "")
		self.assertIsNone(instants.from_utc_iso(""))
