# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — Evaluation Setup tab layout guard (6. evaluation/code structure)."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import UnitTestCase


def _tab_renderers_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_tab_renderers.js"
	)


def _shared_ui_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "std_config"
		/ "std_configurator_shared_ui.js"
	)


def _mockup_css_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "css"
		/ "std_configurator_mockup.css"
	)


class TestStdConfigEvaluationSetupLayoutGuard(UnitTestCase):
	def test_evaluation_setup_tab_markers_in_renderer(self) -> None:
		source = _tab_renderers_path().read_text(encoding="utf-8", errors="replace")
		section = source.split('tabs["evaluation-setup"]')[1].split("tabs[")[0]
		for marker in (
			"ui.evaluationSetupTabDocument",
			"ui.evaluationSetupBasisPanel",
			"ui.evaluationSetupBentoGrid",
			"ui.evaluationSetupStagesSection",
			"ui.stageDetailDrawerBody",
			"stage-detail-drawer",
			"data-kt-std-stage-edit",
			"data-kt-std-add-stage",
		):
			self.assertIn(marker, source, msg=marker)
		self.assertNotIn("ui.sectionCard", section)
		self.assertNotIn("ui.dataTable", section)

	def test_evaluation_setup_shared_ui_markers(self) -> None:
		source = _shared_ui_path().read_text(encoding="utf-8", errors="replace")
		for marker in (
			"EVALUATION_BASIS_OPTIONS",
			"evaluationSetupTabDocument",
			"evaluationSetupBasisPanel",
			"evaluationSetupBentoGrid",
			"evaluationSetupConflictBanner",
			"evaluationSetupReadyBanner",
			"evaluationSetupStagesSection",
			"stageDetailDrawerBody",
			'data-testid="kt-std-cfg-ev-bento"',
			'data-testid="kt-std-cfg-ev-stages"',
			"kt-std-cfg-ev-stage-card",
		):
			self.assertIn(marker, source, msg=marker)

	def test_evaluation_setup_mockup_css_regions(self) -> None:
		source = _mockup_css_path().read_text(encoding="utf-8", errors="replace")
		for selector in (
			".kt-std-cfg-ev-layout",
			".kt-std-cfg-ev-basis",
			".kt-std-cfg-ev-bento",
			".kt-std-cfg-ev-total-stages",
			".kt-std-cfg-ev-structure",
			".kt-std-cfg-ev-conflict",
			".kt-std-cfg-ev-ready",
			".kt-std-cfg-ev-stages",
			".kt-std-cfg-ev-stage-card",
			".kt-std-cfg-ev-type",
		):
			self.assertIn(selector, source, msg=selector)
