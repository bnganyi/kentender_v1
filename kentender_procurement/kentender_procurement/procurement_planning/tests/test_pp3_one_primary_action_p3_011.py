# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-011 — Workbench one primary action surface source contract."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP3OnePrimaryActionP3011(UnitTestCase):
	def test_selected_summary_exposes_single_primary_action_button(self) -> None:
		path = _pkg_public("js", "pp3_planning_selected_work_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function primaryActionHtml", 1)[1].split("function secondaryActionsHtml", 1)[0]
		self.assertEqual(fn_block.count('data-testid="pp3-primary-action"'), 1)
		self.assertIn("btn btn-primary", fn_block)

	def test_secondary_actions_use_default_button_style(self) -> None:
		path = _pkg_public("js", "pp3_planning_selected_work_summary.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		fn_block = source.split("function secondaryActionsHtml", 1)[1].split("function evidenceActionHtml", 1)[0]
		self.assertIn("btn btn-default", fn_block)
		self.assertIn('data-testid="pp3-secondary-actions"', fn_block)

	def test_view_model_items_include_one_primary_action(self) -> None:
		path = Path(__file__).resolve().parents[1] / "services" / "workbench_item_view_model.py"
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('"primary_action":', source)
		self.assertNotIn('"primary_actions":', source)
