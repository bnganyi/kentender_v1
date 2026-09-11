# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — canonical digest, pure and DB-free."""

from __future__ import annotations

import unittest
from datetime import date

from kentender_procurement.procurement_requisitions.services import digest


class TestDigest(unittest.TestCase):
	def test_key_order_does_not_change_the_digest(self):
		a = digest.sha256_hex({"b": 2, "a": 1})
		b = digest.sha256_hex({"a": 1, "b": 2})
		self.assertEqual(a, b)

	def test_a_changed_value_changes_the_digest(self):
		a = digest.sha256_hex({"a": 1})
		b = digest.sha256_hex({"a": 2})
		self.assertNotEqual(a, b)

	def test_dates_canonicalise_to_iso_strings(self):
		out = digest.canonical_json({"d": date(2027, 9, 30)})
		self.assertIn("2027-09-30", out)

	def test_digest_is_a_64_character_hex_string(self):
		value = digest.sha256_hex({"x": "y"})
		self.assertEqual(len(value), 64)
		int(value, 16)  # raises if not hex
