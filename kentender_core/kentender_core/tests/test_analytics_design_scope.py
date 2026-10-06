"""ANL-CHG-001 v0.8 plan Phase 4 (D9, FU-ANL-20) — Analytics' own copy of the design system stays Analytics'.

The same promise Home's copy keeps (test_home_design_scope): the design system is adopted page by page, and
nothing outside the Analytics page may change. These tests keep it and pin the data colours:

* the stylesheet is exactly what the parameterised generator builds from the design pack, the boards' own
  data-colour block and the hand-authored chart rules;
* every selector sits under `.kt-industry.kt-analytics`, and nothing global is defined;
* it is not loaded app-wide;
* every design-system class the Analytics boards draw with is defined;
* the data palette is exactly the boards' "DS-REV-002 data-colour tune (proposal)" block, identical in all six
  board files (the palette itself is still an open owner approval, FU-ANL-10);
* status red, amber and green are never used for a data category or band;
* Home's stylesheet is unchanged by the parameterisation.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_analytics_design_scope
"""

from __future__ import annotations

import glob
import importlib.util
import re
from pathlib import Path

import tinycss2
from frappe.tests import IntegrationTestCase

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "kentender_core/kentender_core/public/js/analytics"
CSS = JS / "kt_analytics_ds.bundle.css"
HOME_CSS = REPO / "kentender_core/kentender_core/public/js/home/kt_home_ds.bundle.css"
CHART_CSS = REPO / "scripts/analytics_charts.css"
HOOKS = REPO / "kentender_core/kentender_core/hooks.py"
BOARDS = sorted((REPO / "docs/mvp-1-r1/19_analytics/design/Analytics").glob("*.dc.html"))
SCOPE = ".kt-industry.kt-analytics"
#: the five area-tab boards plus the index; the six files all carry the same local style block
DATA_TOKENS = (
	"--data-cat-1", "--data-cat-2", "--data-cat-3", "--data-cat-4", "--data-cat-5", "--data-cat-6",
	"--data-seq-1", "--data-seq-2", "--data-seq-3", "--data-seq-4",
	"--data-pair-strong", "--data-pair-tint",
	"--data-family-1", "--data-family-2", "--data-family-3",
)
#: Every class the chart components may be given as a tone (chartUtil.js TONES): data roles only.
EXPECTED_TONES = {
	"cat-1", "cat-2", "cat-3", "cat-4", "cat-5", "cat-6", "seq-1", "seq-2", "seq-3", "seq-4",
	"pair-strong", "pair-tint", "family-1", "family-2", "family-3",
}


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


def _chart_components() -> list[Path]:
	"""The chart components and the icon component this phase owns; the page's own components are checked by its own tests."""
	return sorted([*(JS / "components/charts").glob("*.vue"), JS / "components/AnalyticsIcon.vue"])


def _nodes():
	return tinycss2.parse_stylesheet(CSS.read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True)


def _board_palette(board: Path) -> dict[str, str]:
	"""The data tokens in the board's own local `:root` block."""
	block = re.search(r"<style>(.*?)</style>", board.read_text(encoding="utf-8"), flags=re.S).group(1)
	root = next(n for n in tinycss2.parse_stylesheet(block, skip_comments=True, skip_whitespace=True) if n.type == "qualified-rule" and tinycss2.serialize(n.prelude).strip() == ":root")
	return {i.name: tinycss2.serialize(i.value).strip().lower() for i in tinycss2.parse_declaration_list(root.content, skip_comments=True, skip_whitespace=True) if i.type == "declaration"}


def _scope_tokens() -> dict[str, str]:
	"""Each custom property as the cascade settles it on the Analytics root: the last scope-root declaration wins."""
	tokens: dict[str, str] = {}
	for node in _nodes():
		if node.type == "qualified-rule" and tinycss2.serialize(node.prelude).strip() == SCOPE:
			for item in tinycss2.parse_declaration_list(node.content, skip_comments=True, skip_whitespace=True):
				if item.type == "declaration" and item.name.startswith("--"):
					tokens[item.name] = tinycss2.serialize(item.value).strip().lower()
	return tokens


class TestAnalyticsDesignScope(IntegrationTestCase):
	def test_the_stylesheet_is_what_the_generator_builds_from_the_design_pack_and_boards(self):
		generator = _generator()
		self.assertEqual(CSS.read_text(encoding="utf-8"), generator.build(generator.ANALYTICS), "rerun scripts/home_design_css.py --target analytics")

	def test_the_parameterised_generator_still_builds_homes_stylesheet_unchanged(self):
		generator = _generator()
		self.assertEqual(HOME_CSS.read_text(encoding="utf-8"), generator.build(), "the Analytics change must not alter Home's output")
		self.assertEqual(generator.build(), generator.build(generator.HOME))

	def test_every_selector_is_under_the_analytics_scope(self):
		selectors = [s for s in _selectors(_nodes()) if s]
		self.assertGreater(len(selectors), 100)
		outside = [s for s in selectors if not s.startswith(SCOPE)]
		self.assertEqual(outside, [], "a selector outside the Analytics scope would restyle another page")

	def test_the_hand_authored_chart_rules_are_scoped_whatever_they_are_written_with(self):
		"""The chart source is written without the scope; the generator adds it, so a rule cannot escape."""
		source = CHART_CSS.read_text(encoding="utf-8")
		for forbidden in ("@import", "@font-face", "@keyframes", ":root"):
			self.assertNotIn(forbidden, re.sub(r"/\*.*?\*/", "", source, flags=re.S), forbidden)
		chart_selectors = {s for s in _selectors(tinycss2.parse_stylesheet(source, skip_comments=True, skip_whitespace=True)) if s}
		built = {s for s in _selectors(_nodes()) if s}
		for selector in chart_selectors:
			self.assertIn(f"{SCOPE} {selector}", built)

	def test_nothing_global_is_defined(self):
		text = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)
		for forbidden in ("@import", "@font-face", "@keyframes", ":root"):
			self.assertNotIn(forbidden, text, forbidden)
		bare = [s for s in _selectors(_nodes()) if re.search(r"(?<![\w.#-])(html|body)(?![\w-])", s)]
		self.assertEqual(bare, [], "an element selector for html or body would restyle the page")

	def test_the_stylesheet_is_not_loaded_app_wide(self):
		hooks = HOOKS.read_text(encoding="utf-8")
		self.assertNotIn("kt_analytics_ds", hooks, "Analytics loads its stylesheet itself, lazily; app-wide loading would reach every page")

	def test_every_design_system_class_the_boards_use_is_defined(self):
		used = set()
		for board in BOARDS:
			used |= {token for attr in re.findall(r'class="([^"]*)"', board.read_text(encoding="utf-8")) for token in attr.split()}
		wanted = {c for c in used if c in ("btn", "field", "input", "table") or c.startswith(("btn-", "kt-", "is-"))}
		defined = set(re.findall(r"\.([A-Za-z_][\w-]*)", CSS.read_text(encoding="utf-8")))
		self.assertEqual(sorted(wanted - defined), [], "a board draws with a class the stylesheet does not define")
		for expected in ("kt-tab", "kt-tabs", "kt-icon-chip", "kt-kpi-card", "kt-result-value", "kt-disclosure", "kt-spot", "kt-empty", "btn-secondary"):
			self.assertIn(expected, wanted)

	def test_every_class_the_chart_components_draw_with_is_defined(self):
		classes = set()
		for vue in _chart_components():
			text = vue.read_text(encoding="utf-8")
			classes |= {token for attr in re.findall(r'class="([^"]*)"', text) for token in attr.split() if token.startswith(("kt-", "sr-only"))}
		defined = set(re.findall(r"\.([A-Za-z_][\w-]*)", CSS.read_text(encoding="utf-8")))
		self.assertEqual(sorted(classes - defined), [], "a chart component draws with a class the stylesheet does not define")
		self.assertIn("sr-only", defined)

	def test_the_data_palette_is_exactly_the_boards(self):
		palettes = {board.name: {k: v for k, v in _board_palette(board).items() if k.startswith("--data-")} for board in BOARDS}
		self.assertEqual(len(palettes), 6)
		self.assertEqual(len({tuple(sorted(p.items())) for p in palettes.values()}), 1, "the six board files disagree about the data colours")
		board = next(iter(palettes.values()))
		self.assertEqual(sorted(board), sorted(DATA_TOKENS))
		self.assertEqual({k: v for k, v in _scope_tokens().items() if k in DATA_TOKENS}, board)

	def test_the_data_palette_values_are_pinned(self):
		"""FU-ANL-10: an unapproved proposal. A change to a colour must be a conscious edit of this table."""
		self.assertEqual(
			{k: v for k, v in _scope_tokens().items() if k in DATA_TOKENS},
			{
				"--data-cat-1": "#00857f", "--data-cat-2": "#b8327f", "--data-cat-3": "#2f86c9",
				"--data-cat-4": "#6e44b0", "--data-cat-5": "#475877", "--data-cat-6": "#b0559f",
				"--data-seq-1": "#f1e4d3", "--data-seq-2": "#d8b98f", "--data-seq-3": "#a27845", "--data-seq-4": "#5f4321",
				"--data-pair-strong": "#2a40a8", "--data-pair-tint": "#c2ccfa",
				"--data-family-1": "#1c2a78", "--data-family-2": "#4a62d6", "--data-family-3": "#c2ccfa",
			},
		)

	def test_the_waiting_ramp_has_its_own_hue_not_a_categorys(self):
		tokens = _scope_tokens()
		ramp = {tokens[f"--data-seq-{i}"] for i in range(1, 5)}
		categories = {tokens[f"--data-cat-{i}"] for i in range(1, 7)} | {tokens[k] for k in ("--data-pair-strong", "--data-pair-tint", "--data-family-1", "--data-family-2", "--data-family-3")}
		self.assertEqual(ramp & categories, set())

	def test_status_colours_are_never_a_data_category_or_band(self):
		text = CSS.read_text(encoding="utf-8")
		status = {}
		for name, value in re.findall(r"(--status-[\w-]+):\s*(#[0-9a-fA-F]{6})", text):
			status[name] = value.lower()
		self.assertGreaterEqual(len(status), 10, "the design system's status tokens are no longer in the stylesheet")
		tokens = _scope_tokens()
		clashes = {k: v for k, v in tokens.items() if k in DATA_TOKENS and v in status.values()}
		self.assertEqual(clashes, {}, "a data colour equals a status colour")
		# no rule that draws chart data refers to a status token, and the tone vocabulary is data roles only
		chart_source = CHART_CSS.read_text(encoding="utf-8")
		self.assertNotIn("status", re.sub(r"/\*.*?\*/", "", chart_source, flags=re.S))
		self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", re.sub(r"/\*.*?\*/", "", chart_source, flags=re.S)), ["#fff"] * 3, "chart rules take colour from tokens, not literals (white ink, and the median marker's white halo)")
		util = (JS / "components/charts/chartUtil.js").read_text(encoding="utf-8")
		tones = set(re.findall(r'"((?:cat|seq|pair|family)-[\w-]+)"', re.search(r"export const TONES = Object\.freeze\(\[(.*?)\]\)", util, flags=re.S).group(1)))
		self.assertEqual(tones, EXPECTED_TONES)
		for vue in _chart_components():
			self.assertNotIn("status", vue.read_text(encoding="utf-8").lower(), vue.name)
		# the boards themselves fill chart bars and segments with data tokens only
		for board in BOARDS:
			self.assertNotIn("--status-", board.read_text(encoding="utf-8"), board.name)

	def test_the_old_stylesheets_card_border_is_reset(self):
		self.assertIn(f"{SCOPE} .kt-kpi-card {{\n\tborder: 0;\n}}", CSS.read_text(encoding="utf-8"))

	def test_the_frappe_values_the_design_system_falls_back_to_are_still_frappes(self):
		"""The same pin Home carries: `var(--gray-50, #f8f8f8)` must equal what Desk defines (KT-STD-001 v1.22 §2.4)."""
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

		pinned = [
			(name, fallback)
			for name, fallback in re.findall(r"var\((--[\w-]+),\s*(#[0-9a-fA-F]{3,8}|\d+px)\)", CSS.read_text(encoding="utf-8"))
			if not name.startswith("--kt-")  # the chart rules' own swatch properties are not Frappe's
		]
		self.assertGreater(len(pinned), 15)
		mismatched = {}
		for name, fallback in dict.fromkeys(pinned):
			self.assertIn(name, frappe_vars, f"Frappe no longer defines {name}")
			if norm(resolve(name)) != norm(fallback):
				mismatched[name] = (fallback, resolve(name))
		self.assertEqual(mismatched, {}, "Frappe's value differs from the design system's fallback: review the design system")


class TestAnalyticsIcons(IntegrationTestCase):
	ICONS = JS / "analytics_icons.js"

	def test_the_icon_module_is_what_the_generator_builds_from_the_boards(self):
		self.assertEqual(self.ICONS.read_text(encoding="utf-8"), _generator("analytics_icons_js").build(), "rerun scripts/analytics_icons_js.py")

	def test_the_five_area_icons_are_the_ones_the_boards_draw_on_the_tabs(self):
		text = self.ICONS.read_text(encoding="utf-8")
		areas = dict(re.findall(r"^\t(\w+): \"([\w-]+)\",$", text.split("ANALYTICS_AREA_ICONS = {")[1], flags=re.M))
		self.assertEqual(
			areas,
			{"needs": "lightbulb", "departmental_planning": "clipboard-list", "annual_planning": "calendar-days", "requisitions": "file-check", "tender_proceedings": "megaphone"},
		)
		for name in areas.values():
			self.assertIn(f'"{name}":', text)

	def test_every_other_icon_the_boards_use_is_present(self):
		text = self.ICONS.read_text(encoding="utf-8")
		for name in ("clock", "building-2", "refresh-cw", "chevron-down", "info", "search", "hourglass", "timer", "wallet", "chart-column", "list", "inbox", "circle-x", "lock", "x"):
			self.assertIn(f'"{name}":', text)
