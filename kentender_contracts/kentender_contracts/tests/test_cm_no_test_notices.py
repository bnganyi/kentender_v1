# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-31, DEC-044 and the Project Owner's decision of 16 October 2026: "Remove 'synthetic mechanism test' from ordinary product screens; retain it in test evidence. Where legal authority is unresolved, show
'Change requires legal review.' Removing the test note must not remove that hold."

No board and no screen component of Contract Management draws wording that labels itself a test, and the held quantity change still says it requires legal review."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

APP = Path(frappe.get_app_path("kentender_contracts"))
#: wording that labels a product screen as a test (a fixture or the test evidence may carry it; a board or a screen never does)
FORBIDDEN = ("synthetic mechanism test", "not a legally cleared", "illustrative test record", "these test terms", "under these test terms", "test terms")


def _screens() -> list[Path]:
	boards = sorted((APP / "boards").glob("*.py"))
	components = sorted(path for path in (APP / "public/js/contracts").rglob("*") if path.suffix in (".vue", ".js") and "fixtures" not in path.parts and ".spec." not in path.name)
	return [*boards, *components]


class TestNoScreenCallsItselfATest(IntegrationTestCase):
	def test_no_board_and_no_screen_component_carries_wording_that_labels_it_a_test(self):
		found = {}
		for path in _screens():
			text = path.read_text().lower()
			hits = [phrase for phrase in FORBIDDEN if phrase in text]
			if hits:
				found[str(path.relative_to(APP))] = hits
		self.assertEqual(found, {}, "a test label belongs in test evidence, never on a product screen (DEC-044)")

	def test_the_held_quantity_change_still_says_it_requires_legal_review(self):
		source = (APP / "boards/changes.py").read_text()
		self.assertTrue(re.search(r'kit\.blk\("Change requires legal review"', source), "removing the test note must not remove the legal hold")

	def test_the_demonstration_agreement_text_a_screen_shows_carries_no_stand_in_line(self):
		"""The Project Owner agreed on 16 October 2026 that the bracketed "Synthetic stand-in" line is removed from what a screen shows. The agreement body is what the agreement screen and the signing preview draw; a real
		contract uses its real agreement text, and the fact that the demonstration text is a stand-in stays in the test evidence."""
		from kentender_contracts.simulation import sources

		self.assertNotIn("synthetic", sources.FORM_4.lower())
		self.assertNotIn("stand-in", sources.FORM_4.lower())
		fixture = (APP / "public/js/contracts/fixtures/D02-V.json").read_text().lower()
		self.assertNotIn("stand-in", fixture, "the captured agreement screen does not carry it either")
