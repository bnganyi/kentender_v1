# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Project Owner, 10 October 2026: "Not yet matched" "exposes internal processing and suggests something is wrong". No
supplier-facing source says it; a supplier reads its actual status instead."""

from __future__ import annotations

import re
from pathlib import Path

from frappe.tests import IntegrationTestCase

APP = Path(__file__).resolve().parents[2]
PHRASE = re.compile(r"not\s+yet\s+matched|not\s+matched", re.I)
SCANNED = [APP / "bid_submission" / "services", APP / "public" / "js" / "bid_portal"]


class TestNoNotYetMatched(IntegrationTestCase):
	def test_no_supplier_facing_source_says_not_matched(self):
		hits = []
		for root in SCANNED:
			for path in root.rglob("*"):
				if path.suffix not in (".py", ".js", ".vue") or ".spec." in path.name or "node_modules" in path.parts:
					continue
				for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
					if PHRASE.search(line):
						hits.append(f"{path.relative_to(APP)}:{number}: {line.strip()[:100]}")
		self.assertEqual(hits, [], "supplier-facing sources must read the actual status, never 'not matched'")
