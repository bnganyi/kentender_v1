"""HOME-CHG-001 v0.6 plan Phase 1A — Home's own copy of the design system stays Home's.

The owner moved the design system to the Home page first and put the rest of the
repository on hold (4 Oct 2026). These tests keep that promise and keep the copy
honest:

* the stylesheet is exactly what the generator builds from the design pack;
* every selector sits under `.kt-industry.kt-home`, and nothing global is defined,
  so no other page can change;
* it is not loaded app-wide;
* every design-system class the Home board draws with is defined;
* the Frappe variable values the design system falls back to still equal Frappe's
  own (KT-STD-001 v1.22 §2.4: an upgrade that changes one must fail a test).

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_home_design_scope
"""

from __future__ import annotations

import glob
import importlib.util
import re
from pathlib import Path

import tinycss2
from frappe.tests import IntegrationTestCase

REPO = Path(__file__).resolve().parents[3]
CSS = REPO / "kentender_core/kentender_core/public/js/home/kt_home_ds.bundle.css"
HOOKS = REPO / "kentender_core/kentender_core/hooks.py"
BOARD = REPO / "docs/mvp-1-r1/18_home_page/design/Home/Home.dc.html"
SCOPE = ".kt-industry.kt-home"


def _generator(name: str = "home_design_css"):
	spec = importlib.util.spec_from_file_location(name, REPO / f"scripts/{name}.py")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def _selectors(nodes):
	for node in nodes:
		if node.type == "at-rule" and node.lower_at_keyword == "media":
			yield from _selectors(tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True))
		elif node.type == "qualified-rule":
			prelude = tinycss2.serialize(node.prelude)
			depth, current = 0, ""
			for char in prelude:
				depth += (char == "(") - (char == ")")
				if char == "," and depth == 0:
					yield current.strip()
					current = ""
				else:
					current += char
			yield current.strip()


def _nodes():
	return tinycss2.parse_stylesheet(CSS.read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True)


class TestHomeDesignScope(IntegrationTestCase):
	def test_the_stylesheet_is_what_the_generator_builds_from_the_design_pack(self):
		self.assertEqual(CSS.read_text(encoding="utf-8"), _generator().build(), "rerun scripts/home_design_css.py")

	def test_every_selector_is_under_the_home_scope(self):
		selectors = [s for s in _selectors(_nodes()) if s]
		self.assertGreater(len(selectors), 50)
		outside = [s for s in selectors if not s.startswith(SCOPE)]
		self.assertEqual(outside, [], "a selector outside the Home scope would restyle another page")

	def test_nothing_global_is_defined(self):
		text = CSS.read_text(encoding="utf-8")
		for forbidden in ("@import", "@font-face", "@keyframes", ":root", "html ", "body "):
			self.assertNotIn(forbidden, re.sub(r"/\*.*?\*/", "", text, flags=re.S), forbidden)

	def test_the_stylesheet_is_not_loaded_app_wide(self):
		hooks = HOOKS.read_text(encoding="utf-8")
		self.assertNotIn("kt_home_ds", hooks, "Home loads its stylesheet itself, lazily; app-wide loading would reach every page")

	def test_every_design_system_class_the_board_uses_is_defined(self):
		board = BOARD.read_text(encoding="utf-8")
		used = {token for attr in re.findall(r'class="([^"]*)"', board) for token in attr.split()}
		wanted = {c for c in used if c == "btn" or c.startswith(("btn-", "kt-", "is-"))}
		defined = set(re.findall(r"\.([A-Za-z_][\w-]*)", CSS.read_text(encoding="utf-8")))
		self.assertEqual(sorted(wanted - defined), [], "the board draws with a class the stylesheet does not define")
		self.assertIn("kt-icon-chip", wanted)
		self.assertIn("kt-kpi-card", wanted)

	def test_the_frappe_values_the_design_system_falls_back_to_are_still_frappes(self):
		"""`var(--gray-50, #f8f8f8)`: the fallback is what a preview shows outside Desk, and it must equal what Desk
		defines. Reads the built desk stylesheet's light theme."""
		bundles = sorted(glob.glob(str(REPO.parents[1] / "apps/frappe/frappe/public/dist/css/desk.bundle.*.css")))
		self.assertTrue(bundles, "Frappe's desk stylesheet is not built")
		frappe_vars: dict[str, str] = {}
		for node in tinycss2.parse_stylesheet(Path(bundles[-1]).read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True):
			if node.type != "qualified-rule":
				continue
			prelude = tinycss2.serialize(node.prelude)
			if ":root" not in prelude or "dark" in prelude:
				continue
			for item in tinycss2.parse_declaration_list(node.content, skip_comments=True, skip_whitespace=True):
				if item.type == "declaration" and item.name.startswith("--"):
					frappe_vars.setdefault(item.name, tinycss2.serialize(item.value).strip())

		def resolve(name: str, depth: int = 0) -> str:
			value = frappe_vars[name]
			match = re.fullmatch(r"var\((--[\w-]+)\)", value)
			return resolve(match.group(1), depth + 1) if match and depth < 5 else value

		def norm(value: str) -> str:
			value = value.strip().lower()
			return "#ffffff" if value == "white" else value

		pinned = re.findall(r"var\((--[\w-]+),\s*(#[0-9a-fA-F]{3,8}|\d+px)\)", CSS.read_text(encoding="utf-8"))
		self.assertGreater(len(pinned), 15)
		mismatched = {}
		for name, fallback in dict.fromkeys(pinned):
			self.assertIn(name, frappe_vars, f"Frappe no longer defines {name}")
			if norm(resolve(name)) != norm(fallback):
				mismatched[name] = (fallback, resolve(name))
		self.assertEqual(mismatched, {}, "Frappe's value differs from the design system's fallback: review the design system")

	def test_inter_comes_from_frappe_so_no_font_files_are_shipped(self):
		bundles = sorted(glob.glob(str(REPO.parents[1] / "apps/frappe/frappe/public/dist/css/desk.bundle.*.css")))
		self.assertIn('"InterVariable"', Path(bundles[-1]).read_text(encoding="utf-8"))


class TestHomeIcons(IntegrationTestCase):
	ICONS = REPO / "kentender_core/kentender_core/public/js/home/home_icons.js"

	def test_the_icon_module_is_what_the_generator_builds_from_the_board(self):
		self.assertEqual(self.ICONS.read_text(encoding="utf-8"), _generator("home_icons_js").build(), "rerun scripts/home_icons_js.py")

	def test_the_three_icons_the_design_system_list_lacks_are_present(self):
		text = self.ICONS.read_text(encoding="utf-8")
		for name in ("clock", "list-checks", "calendar-clock"):
			self.assertIn(f'"{name}":', text)

	def test_every_module_icon_the_page_needs_is_present(self):
		text = self.ICONS.read_text(encoding="utf-8")
		# Requisitions, Award, Bid opening, Evaluation, Tenders, Needs, Analytics (HOME §10B.1 module icons) and the region icons
		for name in ("file-check", "badge-check", "inbox", "scale", "megaphone", "lightbulb", "chart-column", "hourglass", "eye", "triangle-alert", "target", "wallet", "clipboard-list", "users", "circle-alert"):
			self.assertIn(f'"{name}":', text)
