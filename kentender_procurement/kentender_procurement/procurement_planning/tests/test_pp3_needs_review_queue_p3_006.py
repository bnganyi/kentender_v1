# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-006 — Workbench Needs Review queue surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3NeedsReviewQueueP3006(UnitTestCase):
	def test_work_list_maps_needs_review_queue(self) -> None:
		source = _pkg_public("js", "pp3_planning_work_list.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('needs_review: "needs_review"', source)

	def test_needs_review_empty_copy(self) -> None:
		empty_state = _pkg_public("js", "pp2_planning_empty_state.js").read_text(encoding="utf-8", errors="replace")
		self.assertIn('needs_review: __("No packages are waiting for review.")', empty_state)

	def test_view_model_review_package_action(self) -> None:
		source = (Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py").read_text(
			encoding="utf-8", errors="replace"
		)
		self.assertIn('"review_package": ("Review Package", "review_package")', source)
