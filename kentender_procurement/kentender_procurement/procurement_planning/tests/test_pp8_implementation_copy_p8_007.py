# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-007 — Implementation copy scan (no shell/stub/deferred/P5 copy)."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import UnitTestCase

from kentender_procurement.procurement_planning.tests.pp8_gate_constants import (
	P8_FORBIDDEN_IMPLEMENTATION_COPY,
)

_PP3_JS_ASSETS = (
	"pp2_planning_router.js",
	"pp2_planning_page_header.js",
	"pp3_planning_workbench_queue_tabs.js",
	"pp3_planning_work_list.js",
	"pp3_planning_selected_work_summary.js",
	"pp3_planning_released_list.js",
	"pp3_planning_release_summary.js",
	"package_detail_page.js",
	"pp3_planning_evidence_drawer.js",
)


def _extract_translated_strings(source: str) -> list[str]:
	strings = re.findall(r'__\(\s*"([^"]+)"\s*\)', source)
	strings += re.findall(r"__\(\s*'([^']+)'\s*\)", source)
	return strings


class TestPP8ImplementationCopyP8007(UnitTestCase):
	def test_pp8_007_pp3_assets_have_no_forbidden_implementation_copy(self) -> None:
		root = Path(frappe.get_app_path("kentender_procurement")) / "public" / "js"
		hits: list[str] = []
		for filename in _PP3_JS_ASSETS:
			path = root / filename
			self.assertTrue(path.exists(), msg=f"missing {path}")
			source = path.read_text(encoding="utf-8", errors="replace")
			for text in _extract_translated_strings(source):
				if any(token.lower() in text.lower() for token in P8_FORBIDDEN_IMPLEMENTATION_COPY):
					hits.append(f"{filename}: {text}")
			for token in P8_FORBIDDEN_IMPLEMENTATION_COPY:
				if token.lower() in source.lower() and token not in _extract_translated_strings(source):
					if "FORBIDDEN" in source and token in source:
						continue
		self.assertFalse(hits, msg=f"Forbidden implementation copy: {hits}")

	def test_pp8_007_router_has_no_planning_workflow_status_panel_copy(self) -> None:
		path = Path(frappe.get_app_path("kentender_procurement")) / "public" / "js" / "pp2_planning_router.js"
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertNotIn("Planning Workflow Status", source)
		self.assertNotIn("shell baseline", source.lower())
		self.assertNotIn("feature content deferred", source.lower())
