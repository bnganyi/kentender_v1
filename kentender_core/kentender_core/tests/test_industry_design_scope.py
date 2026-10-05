# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 Phase 1B — the shared Industry stylesheet is the design pack's, and nothing was lost in the switch.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_industry_design_scope
"""

from __future__ import annotations

import glob
import importlib.util
import re
import sys
from pathlib import Path

from frappe.tests import IntegrationTestCase

REPO = Path(__file__).resolve().parents[3]
CSS = REPO / "kentender_core/kentender_core/public/css/kt_industry_tokens.css"


def _load(name: str):
	sys.path.insert(0, str(REPO / "scripts"))
	try:
		spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
		module = importlib.util.module_from_spec(spec)
		sys.modules[name] = module
		spec.loader.exec_module(module)
		return module
	finally:
		sys.path.pop(0)


def _classes(css: str) -> set[str]:
	return set(re.findall(r"\.([a-zA-Z][\w-]*)", re.sub(r"/\*.*?\*/", "", css, flags=re.S)))


def _at_rules(css: str) -> dict[str, int]:
	counts: dict[str, int] = {}
	for name in re.findall(r"^\s*@([a-z-]+)", css, flags=re.M):
		counts[name] = counts.get(name, 0) + 1
	return counts


class TestIndustryStylesheet(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.ids = _load("industry_design_css")
		cls.css = CSS.read_text(encoding="utf-8")

	def test_the_stylesheet_is_what_the_generator_builds(self):
		self.assertEqual(self.css, self.ids.build(), "rerun scripts/industry_design_css.py")

	def test_every_selector_sits_under_the_industry_scope(self):
		import tinycss2

		def selectors(nodes):
			for node in nodes:
				if node.type == "qualified-rule":
					yield from (s.strip() for s in tinycss2.serialize(node.prelude).split(","))
				elif node.type == "at-rule" and node.lower_at_keyword in ("media", "container"):
					yield from selectors(tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True))

		# `.kt-desk-page-mount` is the Vue-in-Desk mount point itself (it holds .kt-industry, so it cannot sit under it) and sets only min-height.
		loose = [s for s in selectors(tinycss2.parse_stylesheet(self.css, skip_comments=True, skip_whitespace=True)) if not s.startswith(".kt-industry") and s != ".kt-desk-page-mount"]
		self.assertEqual(loose, [], "a selector outside .kt-industry would restyle Desk")

	def test_no_global_rules_font_faces_or_imports(self):
		for needle in (r"^\s*:root", r"^\s*@import", r"^\s*@font-face", r"^html\b", r"^body\b"):
			self.assertIsNone(re.search(needle, self.css, flags=re.M), needle)

	def test_no_source_file_still_uses_an_old_class_name(self):
		rename = _load("industry_rename_classes")
		leftovers = []
		for path in rename.files():
			try:
				hits = rename.PATTERN.findall(path.read_text(encoding="utf-8"))
			except UnicodeDecodeError:
				continue
			if hits:
				leftovers.append(f"{path.relative_to(REPO)}: {sorted(set(hits))}")
		self.assertEqual(leftovers, [], "run scripts/industry_rename_classes.py --apply")

	def test_every_class_the_old_stylesheet_styled_is_still_styled_by_something(self):
		old = _classes((REPO / "scripts/industry_old_stylesheet.css").read_text(encoding="utf-8"))
		wanted = {self.ids.RENAMES.get(c, c) for c in old}
		styled = _classes(self.css)
		for path in glob.glob(str(REPO / "kentender_*/*/public/**/*.css"), recursive=True):
			if "/dist/" not in path and Path(path) != CSS:
				styled |= _classes(Path(path).read_text(encoding="utf-8"))
		self.assertEqual(sorted(c for c in wanted if c not in styled), [])

	def test_the_container_and_keyframe_rules_of_both_sources_are_carried(self):
		old = _at_rules((REPO / "scripts/industry_old_stylesheet.css").read_text(encoding="utf-8"))
		pack = _at_rules(Path(sorted(glob.glob(str(REPO / self.ids.SOURCE)))[0]).read_text(encoding="utf-8"))
		built = _at_rules(self.css)
		for kind in ("container", "keyframes"):
			self.assertEqual(built.get(kind, 0), old.get(kind, 0) + pack.get(kind, 0), f"@{kind} rules were dropped")

	def test_no_module_stylesheet_defines_a_design_token_in_terms_of_the_old_ones(self):
		"""`--color-bg: var(--kt-color-bg)` while `--kt-color-bg` is `var(--color-bg)` is a cycle: both become invalid and the page ground vanishes (found 5 Oct 2026)."""
		pattern = re.compile(r"^\s*--(color|status|font|radius|shadow|space)[a-z0-9-]*:\s*var\(--kt-", re.M)
		bad = []
		for path in glob.glob(str(REPO / "kentender_*/*/public/**/*.css"), recursive=True):
			if "/dist/" in path or Path(path) == CSS:
				continue
			if pattern.search(Path(path).read_text(encoding="utf-8")):
				bad.append(str(Path(path).relative_to(REPO)))
		self.assertEqual(bad, [])

	def test_the_page_has_a_ground_and_links_are_underlined(self):
		self.assertRegex(self.css, r"\.kt-industry \{\s*background: var\(--color-bg\);")
		self.assertRegex(self.css, r"\.kt-industry a:not\(\.btn\)[^{]*\{\s*text-decoration: underline;")
