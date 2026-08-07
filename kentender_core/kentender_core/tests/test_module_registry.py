# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.module_registry import KT_MODULES, get_module, get_route_sidebar_keys


def _budget_page_js_slugs() -> list[str]:
	from kentender_budget import hooks as bud_hooks

	return list((bud_hooks.page_js or {}).keys())


def _strategy_page_js_slugs() -> list[str]:
	from kentender_strategy import hooks as str_hooks

	return list((str_hooks.page_js or {}).keys())


def _js_module_registry_source() -> str:
	return (
		Path(frappe.get_app_path("kentender_core")) / "public" / "js" / "kt_module_registry.js"
	).read_text(encoding="utf-8")


def _js_route_prefixes_block(source: str, module_id: str) -> str:
	"""Slice a module routePrefixes array from kt_module_registry.js."""
	marker = f'id: "{module_id}"'
	start = source.find(marker)
	if start < 0:
		return ""
	rp = source.find("routePrefixes:", start)
	if rp < 0:
		return ""
	open_br = source.find("[", rp)
	close_br = source.find("]", open_br)
	if open_br < 0 or close_br < 0:
		return ""
	return source[open_br : close_br + 1]


def _budget_js_route_prefixes_block(source: str) -> str:
	return _js_route_prefixes_block(source, "budget")


def _strategy_js_route_prefixes_block(source: str) -> str:
	return _js_route_prefixes_block(source, "strategy")


def _ticket_doc_read_gate_mdc() -> str:
	from frappe.utils import get_bench_path

	path = Path(get_bench_path()) / ".cursor" / "rules" / "kentender-ticket-doc-read-gate.mdc"
	return path.read_text(encoding="utf-8")


def _budget_registry_table_row(source: str) -> str:
	"""Return the Module pack registry table row for Budget (MVP-1)."""
	for line in source.splitlines():
		if line.startswith("| Budget") and "mvp-1" in line:
			return line
		if line.startswith("| Budget |"):
			return line
	return ""


def _strategy_registry_table_row(source: str) -> str:
	"""Return the Module pack registry table row for Strategy Alignment (MVP-1)."""
	for line in source.splitlines():
		if line.startswith("| Strategy") and "mvp-1" in line.lower():
			return line
		if "01_strategy" in line and line.startswith("|"):
			return line
	return ""


class TestModuleRegistry(IntegrationTestCase):
	def test_modules_defined(self):
		self.assertIn("strategy", KT_MODULES)
		self.assertIn("budget", KT_MODULES)
		self.assertIn("demands", KT_MODULES)
		self.assertNotIn("dia", KT_MODULES)

	def test_get_module(self):
		mod = get_module("budget")
		self.assertIsNotNone(mod)
		self.assertEqual(mod["workspace_label"], "Budget Management")

	def test_route_sidebar_keys_include_builders(self):
		keys = get_route_sidebar_keys()
		# Legacy strategy-builder removed; MVP-1 Alignment portfolio restored.
		self.assertNotIn("strategy-builder", keys)
		self.assertEqual(keys.get("strategy-alignment"), "Procurement")
		self.assertIn("budget-funding", keys)
		self.assertIn("form/demand", keys)

	def test_budget_module_portfolio_route(self):
		mod = get_module("budget")
		self.assertEqual(mod["desk_page"], "budget-funding")
		self.assertEqual(mod["form_doctype"], "Budget")
		self.assertIn("budget-funding", mod["route_prefixes"])

	def test_budget_route_prefixes_cover_all_page_js(self):
		"""BUD-SUP-004 — every Budget Desk page must resolve to the budget module."""
		mod = get_module("budget")
		prefixes = {str(p) for p in (mod["route_prefixes"] or ())}
		sidebar_keys = get_route_sidebar_keys()
		for slug in _budget_page_js_slugs():
			self.assertIn(
				slug,
				prefixes,
				msg=f"budget route_prefixes missing page_js slug {slug!r}",
			)
			# Boot fast-path maps routes to the Procurement rail parent.
			self.assertEqual(
				sidebar_keys.get(slug.lower()),
				"Procurement",
				msg=f"get_route_sidebar_keys missing budget mapping for {slug!r}",
			)
		self.assertIn("Form/Budget", prefixes)
		self.assertEqual(sidebar_keys.get("form/budget"), "Procurement")

	def test_budget_js_registry_route_prefixes_match_page_js(self):
		"""BUD-SUP-004 — kt_module_registry.js must stay in sync with hooks.page_js."""
		source = _js_module_registry_source()
		self.assertIn("Register approved budget", source)
		self.assertNotIn("Manage Allocations", source)
		block = _budget_js_route_prefixes_block(source)
		self.assertTrue(block, msg="budget routePrefixes array not found in kt_module_registry.js")
		for slug in _budget_page_js_slugs():
			self.assertIn(
				f'"{slug}"',
				block,
				msg=f"kt_module_registry.js budget routePrefixes missing {slug!r}",
			)
		self.assertIn('"Form/Budget"', block)

	def test_strategy_route_prefixes_cover_all_page_js(self):
		"""STR-SUP-003 — every Strategy Desk page must resolve to the strategy module."""
		mod = get_module("strategy")
		prefixes = {str(p) for p in (mod["route_prefixes"] or ())}
		sidebar_keys = get_route_sidebar_keys()
		self.assertEqual(mod["desk_page"], "strategy-alignment")
		self.assertEqual(mod["builder_page"], "strategy-plan-structure")
		self.assertEqual(mod.get("form_doctype") or "", "")
		for slug in _strategy_page_js_slugs():
			self.assertIn(
				slug,
				prefixes,
				msg=f"strategy route_prefixes missing page_js slug {slug!r}",
			)
			self.assertEqual(
				sidebar_keys.get(slug.lower()),
				"Procurement",
				msg=f"get_route_sidebar_keys missing strategy mapping for {slug!r}",
			)

	def test_strategy_js_registry_route_prefixes_match_page_js(self):
		"""STR-SUP-003 — kt_module_registry.js must stay in sync with hooks.page_js."""
		source = _js_module_registry_source()
		block = _strategy_js_route_prefixes_block(source)
		self.assertTrue(block, msg="strategy routePrefixes array not found in kt_module_registry.js")
		for slug in _strategy_page_js_slugs():
			self.assertIn(
				f'"{slug}"',
				block,
				msg=f"kt_module_registry.js strategy routePrefixes missing {slug!r}",
			)

	def test_budget_ticket_doc_read_gate_targets_mvp1_pack(self):
		"""BUD-SUP-006 — ticket-doc-read-gate Budget pack is MVP-1, not historical prompts."""
		source = _ticket_doc_read_gate_mdc()
		self.assertIn("docs/mvp-1/02_budget", source)
		self.assertIn("04_Budget_Cross_Module_Lifecycle_Tracker.md", source)
		row = _budget_registry_table_row(source)
		self.assertTrue(row, msg="Budget registry row not found in ticket-doc-read-gate.mdc")
		self.assertIn("docs/mvp-1/02_budget", row)
		self.assertIn("04_Budget_Cross_Module_Lifecycle_Tracker.md", row)
		self.assertNotIn(
			"docs/prompts/budget/",
			row,
			msg="Budget pack folder cell must be MVP-1, not historical prompts/budget",
		)
		self.assertIn("reference only", source.lower())

	def test_strategy_ticket_doc_read_gate_targets_mvp1_pack(self):
		"""STR-SUP-006 — ticket-doc-read-gate Strategy pack is MVP-1, not historical prompts."""
		source = _ticket_doc_read_gate_mdc()
		self.assertIn("docs/mvp-1/01_strategy", source)
		self.assertIn("08_Strategy_Cross_Module_Lifecycle_Tracker.md", source)
		row = _strategy_registry_table_row(source)
		self.assertTrue(row, msg="Strategy registry row not found in ticket-doc-read-gate.mdc")
		self.assertIn("docs/mvp-1/01_strategy", row)
		self.assertIn("08_Strategy_Cross_Module_Lifecycle_Tracker.md", row)
		self.assertNotIn(
			"docs/prompts/strategy/",
			row,
			msg="Strategy pack folder cell must be MVP-1, not historical prompts/strategy",
		)
		self.assertIn("reference only", source.lower())
