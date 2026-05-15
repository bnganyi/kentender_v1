# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-26 — ``tender_management.business_codes`` (doc 3 §3.1, TM2-ID-008/009).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_business_code_helpers_p1_26
"""

from __future__ import annotations

import unittest

from kentender_procurement.tender_management import business_codes as bc


class TestBusinessCodeHelpersP126(unittest.TestCase):
	def test_p126_entity_slug_and_tender_prefix(self) -> None:
		self.assertEqual(bc.entity_slug("  MOH-KE  "), "MOHKE")
		self.assertEqual(bc.entity_slug(""), "UNK")
		self.assertEqual(bc.entity_slug("VeryLongProcuringEntityCodeHere", max_len=12), "VERYLONGPROC")
		self.assertEqual(bc.normalize_fiscal_year("2026.0"), "2026")
		self.assertEqual(bc.tender_code_prefix("MOH", "2026"), "TND-MOH-2026")

	def test_p126_parse_tender_code(self) -> None:
		self.assertEqual(
			bc.parse_tender_code("TND-MOH-2026-0001"),
			{"entity": "MOH", "fy": "2026", "seq": "0001"},
		)
		self.assertIsNone(bc.parse_tender_code("TND-MOH-2026-1"))
		self.assertIsNone(bc.parse_tender_code("XND-MOH-2026-0001"))

	def test_p126_doc31_pattern_formatters(self) -> None:
		tc = "TND-MOH-2026-0001"
		self.assertEqual(bc.format_tsb(tc), "TSB-TND-MOH-2026-0001")
		self.assertEqual(bc.format_ttl(tc), "TTL-TND-MOH-2026-0001")
		self.assertEqual(bc.format_tac(tc), "TAC-TND-MOH-2026-0001")
		self.assertEqual(bc.format_trd(tc, 1), "TRD-TND-MOH-2026-0001-001")
		self.assertEqual(bc.format_pub(tc, 2), "PUB-TND-MOH-2026-0001-002")
		self.assertEqual(bc.format_inv(tc, 3), "INV-TND-MOH-2026-0001-0003")
		self.assertEqual(bc.format_clr(tc, 4), "CLR-TND-MOH-2026-0001-0004")
		clr = bc.format_clr(tc, 1)
		self.assertEqual(bc.format_clrr(clr, 2), "CLRR-CLR-TND-MOH-2026-0001-0001-02")
		self.assertEqual(bc.format_add(tc, 1), "ADD-TND-MOH-2026-0001-01")
		add = bc.format_add(tc, 1)
		self.assertEqual(bc.format_air(add), "AIR-ADD-TND-MOH-2026-0001-01")
		self.assertEqual(
			bc.format_ack(add, "SUP-ALPHA"),
			"ACK-ADD-TND-MOH-2026-0001-01-SUP-ALPHA",
		)
		self.assertEqual(
			bc.format_bid(tc, "SUP-ALPHA", 1),
			"BID-TND-MOH-2026-0001-SUP-ALPHA-01",
		)
		bid = bc.format_bid(tc, "SUP-ALPHA", 1)
		self.assertEqual(bc.format_rct(bid), f"RCT-{bid}")
		self.assertEqual(
			bc.format_late(tc, "SUP-DELTA", 1),
			"LATE-TND-MOH-2026-0001-SUP-DELTA-01",
		)
		self.assertEqual(bc.format_cls(tc), "CLS-TND-MOH-2026-0001")
		self.assertEqual(bc.format_orr(tc), "ORR-TND-MOH-2026-0001")
		self.assertEqual(bc.format_ehr(tc), "EHR-TND-MOH-2026-0001")
		self.assertEqual(bc.format_chr(tc), "CHR-TND-MOH-2026-0001")
		self.assertEqual(bc.format_ntf(tc, 1), "NTF-TND-MOH-2026-0001-0001")

	def test_p126_tm2_id_008_immutable_when_locked(self) -> None:
		with self.assertRaises(ValueError):
			bc.assert_business_code_immutable("EHR-X", "EHR-Y", locked=True)
		bc.assert_business_code_immutable("EHR-X", "EHR-X", locked=True)
		bc.assert_business_code_immutable("EHR-X", "EHR-Y", locked=False)

	def test_p126_tm2_id_009_immutable_when_historical(self) -> None:
		with self.assertRaises(ValueError):
			bc.assert_business_code_immutable("CHR-X", "CHR-Y", locked=False, historical=True)
		bc.assert_business_code_immutable("CHR-X", "CHR-X", locked=False, historical=True)

	def test_p126_format_tae_example(self) -> None:
		self.assertEqual(bc.format_tae("TND-MOH-2026-0001", 17), "TAE-TND-MOH-2026-0001-0017")
