# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Configuration Desk pages must use native <select>, not <datalist>."""

from __future__ import annotations

import unittest
from pathlib import Path

_JS_DIR = Path(__file__).resolve().parents[2] / "public" / "js"


class TestTenderConfigurationNoDatalistGuard(unittest.TestCase):
	def test_it_tender_configuration_pages_have_no_datalist(self) -> None:
		offenders: list[str] = []
		for path in sorted(_JS_DIR.glob("it_tender_configuration*_page.js")):
			text = path.read_text(encoding="utf-8")
			if "<datalist" in text or 'list="kt-cl-' in text or "list='kt-cl-" in text:
				offenders.append(path.name)
		self.assertEqual(
			offenders,
			[],
			"Closed-list fields must use <select>, not <input list>/<datalist>: "
			+ ", ".join(offenders),
		)
