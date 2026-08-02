# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-03 — Add/Edit Requirement drawer must not dismiss on backdrop click.

Pack-wide coverage lives in ``test_cfg_drawer_dismiss_guard`` (CFG-03…09 + related overlays).
"""

from __future__ import annotations

import unittest
from pathlib import Path

_JS = (
	Path(__file__).resolve().parents[2]
	/ "public"
	/ "js"
	/ "it_tender_configuration_it_requirements_page.js"
)


class TestCfg03DrawerDismissGuard(unittest.TestCase):
	def test_overlay_does_not_close_drawer_on_click(self) -> None:
		js = _JS.read_text(encoding="utf-8")
		self.assertIn('data-testid="kt-cl-cfg03-drawer-overlay"', js)
		self.assertIn('data-dismiss="explicit-only"', js)
		# Regression: overlay click handler previously called closeDrawer()
		self.assertNotIn(
			"[data-testid='kt-cl-cfg03-drawer-overlay']\", function (e) {\n"
			"\t\t\tif (e.target === this) {\n"
			"\t\t\t\tcloseDrawer();",
			js,
		)
		self.assertIn("[data-action='close-drawer']", js)
		self.assertIn("[data-action='save-requirement']", js)
