#!/usr/bin/env python3
"""Build kentender_core/public/js/home/kt_home_ds.bundle.css from the Home design pack.

HOME-CHG-001 v0.6, plan Phase 1A (owner instruction 4 Oct 2026: the design
system is adopted for the Home page first; the rest of the repository stays on
the old stylesheet until the owner says otherwise).

The source is the pack's own stylesheet, `docs/mvp-1-r1/18_home_page/design/_ds/
kentender-industry-*/styles.css` (DS-REV-002). This keeps only the rules for the
classes the Home board uses, in their original order (the pack's later blocks
override its earlier ones, so order is the design), and puts every selector under
`.kt-industry.kt-home`. That scope is the whole point: nothing outside the Home
page root can be restyled, and the doubled class beats the repository's existing
`.kt-industry .kt-kpi-card` and `.kt-industry .kt-icon-tile` rules on the same
element.

    python3 scripts/home_design_css.py            # rewrite the stylesheet
    python3 scripts/home_design_css.py --check    # exit 1 if it is out of date

ANL-CHG-001 v0.8 plan Phase 4 (D9, FU-ANL-20): the generator is parameterised by a `Target` (source pack, class
allow-list, scope class, output path, header). `HOME` is the original, byte-for-byte unchanged; `ANALYTICS` emits
`kentender_core/public/js/analytics/kt_analytics_ds.bundle.css` under `.kt-industry.kt-analytics`.

    python3 scripts/home_design_css.py --target analytics          # rewrite the Analytics stylesheet
    python3 scripts/home_design_css.py --target analytics --check

Needs `tinycss2` (it is in the bench environment: ../../env/bin/python).
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path
from typing import NamedTuple

import tinycss2

ROOT = Path(__file__).resolve().parent.parent

#: Element and pseudo selectors kept (under the scope), as the pack writes them.
BASE = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "a:hover", ":focus", ":focus-visible", "::selection"}
#: `body` carries the page ground and margin, which belong to Frappe; the rest is the page's text.
BODY_KEEP = {"color", "font-family", "font-size", "line-height", "font-weight"}
#: The shared stylesheet colours links with `.kt-industry a:not(.btn):not(.kt-tab):not(.kt-add-child)`
#: (specificity 0,4,1). Links use the same exclusions so they outrank it and stay indigo.
LINK_GUARD = ":not(.btn):not(.kt-tab):not(.kt-add-child)"


class Target(NamedTuple):
	"""One scoped copy of the design system: which pack, which classes, which scope, where it is written.

	A NamedTuple, not a dataclass: the repository's tests load this file with `importlib` without registering
	it in `sys.modules`, which a dataclass cannot survive."""

	name: str
	source_glob: str
	target: Path
	scope: str
	#: Every class the page's board draws with. A rule that names any other class is dropped.
	allowed: frozenset
	#: Declarations the old stylesheet puts on a class that the design system never sets, so they would leak through.
	resets: tuple
	#: Header comment; `{source}` is the pack stylesheet's repository-relative path.
	header: str
	#: The page's boards. When set, their identical local `<style>` (the board's own `:root` data-colour block and its
	#: `a` / `a:hover` rules) is emitted after the pack's rules, scoped, because the owner accepted the boards as rendered.
	boards_glob: "str | None" = None
	#: Hand-authored rules for classes the pack does not define (the chart components), every selector scoped on write.
	extra_css: "Path | None" = None


def control_shape(scope: str, fields: bool = False) -> tuple:
	"""Buttons and form controls are rectangular and outlined; a status pill stays the only soft, tinted, filled element.

	Owner, 6 Oct 2026: a grey-filled, 8px-cornered secondary button read as the same kind of object as a grey status pill, and the soft
	corners felt too playful. So a button is a 2px-cornered rectangle, a secondary is outlined on white (grey fill only on hover), and
	a field shares that corner and carries a visible border. Pills, cards and sheets keep their own rounding. Contrast of the 1px rule
	against white (neutral-600) is 4.2:1, above the 3:1 non-text minimum.
	"""
	rules = [
		f"{scope} {{\n\t--radius-control: 2px;\n}}",
		f"{scope} .btn {{\n\tborder-radius: var(--radius-control);\n}}",
		f"{scope} .btn-secondary {{\n\tbackground: var(--color-surface);\n\tborder-color: var(--color-neutral-600);\n}}",
		f"{scope} .btn-secondary:hover:not(:disabled) {{\n\tbackground: var(--color-neutral-100);\n}}",
		f"{scope} .btn-secondary:active:not(:disabled) {{\n\tbackground: var(--color-neutral-200);\n}}",
		f"{scope} .btn-secondary:disabled {{\n\tbackground: transparent;\n\tborder-color: var(--color-neutral-300);\n}}",
		# Frappe's own `.btn:focus` / `.btn:active` add an inset highlight, a drop shadow and a 2px grey ring (and a grey fill) on top
		# of the control's outline: after a mouse click a secondary button read as a doubled dark border (found live 6 Oct 2026).
		# The design system marks keyboard focus with the one accent outline (`:focus-visible`) and nothing else.
		# Frappe sets its ring on `.btn.btn-secondary:focus-visible` and `.btn:active` with `!important`, so the reset must too.
		f"{scope} .btn:focus {{\n\tbox-shadow: none;\n}}",
		f"{scope} .btn:focus-visible,\n{scope} .btn:active {{\n\tbox-shadow: none !important;\n}}",
		f"{scope} .btn-secondary:focus:not(:hover):not(:active):not(:disabled) {{\n\tbackground: var(--color-surface);\n}}",
	]
	if fields:
		rules += [
			f"{scope} .input,\n{scope} .date-field {{\n\tborder-radius: var(--radius-control);\n\tborder-color: var(--color-neutral-600);\n}}",
			f"{scope} .input:hover:not(:disabled):not(:focus-visible) {{\n\tborder-color: var(--color-neutral-700);\n}}",
		]
	return tuple(rules)


#: Every class the Home board (design/Home/Home.dc.html) draws with.
HOME_ALLOWED = frozenset({
	"btn", "btn-primary", "btn-secondary", "btn-ghost",
	"kt-status", "is-live", "is-draft", "is-pending", "is-attention", "is-critical",
	"kt-kpi-card", "kt-kpi-head", "kt-kpi-value", "kt-kpi-sub", "kt-kpi-icon",
	"kt-icon", "is-sm", "is-lg", "kt-icon-chip",
	"kt-spot", "is-success", "is-error", "is-neutral",
})

HOME = Target(
	name="home",
	source_glob="docs/mvp-1-r1/18_home_page/design/_ds/kentender-industry-*/styles.css",
	target=ROOT / "kentender_core/kentender_core/public/js/home/kt_home_ds.bundle.css",
	scope=".kt-industry.kt-home",
	allowed=HOME_ALLOWED,
	resets=(
		".kt-industry.kt-home .kt-kpi-card {\n\tborder: 0;\n}",  # old: a 1px bordered card; the design system's is borderless with a left rule
		# Leaks of Frappe's own Desk stylesheet, found by the Phase 8 computed-style comparison with the board
		# (tests/ui/smoke/home/home-style-parity.spec.ts, 5 Oct 2026); each outranks the design system's one-class rule.
		# Frappe: `.btn:not(.btn-md):not(.btn-lg):not(.btn-xs) { padding: 4px 8px }` (four classes) made every button 27 px high, not 32.
		".kt-industry.kt-home .btn:not(.btn-md):not(.btn-lg):not(.btn-xs) {\n\tpadding: var(--space-2) calc(var(--space-3) * 1.2);\n\tletter-spacing: normal;\n}",
		".kt-industry.kt-home .btn-ghost:not(.btn-md):not(.btn-lg):not(.btn-xs) {\n\tpadding-inline: var(--space-1);\n}",
		# Frappe: `a { text-decoration: none }` removed the underline the board keeps (KT-STD-001 v1.22 section 2.4: links stay underlined).
		f".kt-industry.kt-home a{LINK_GUARD} {{\n\ttext-decoration: underline;\n}}",
		# Frappe: `svg { vertical-align: middle }` moved inline icons off the baseline the board draws them on.
		".kt-industry.kt-home .kt-icon {\n\tvertical-align: baseline;\n}",
		*control_shape(".kt-industry.kt-home"),
	),
	#: The board's own `:root` data-colour block ("DS-REV-002 data-colour tune (proposal)") and `a` rules, because the
	#: owner approved HOME v0.6 with the board as rendered (FU-HOME-44).
	boards_glob="docs/mvp-1-r1/18_home_page/design/Home/Home.dc.html",
	header=(
		"/* GENERATED by scripts/home_design_css.py from the Home design pack's design system (DS-REV-002).\n"
		"   Source: {source}\n"
		"   Scope: every selector sits under .kt-industry.kt-home, so no other page is restyled (plan Phase 1A).\n"
		"   Do not edit by hand: change the generator or the design source, then rerun it. Inter is Frappe's own font\n"
		"   (--font-stack), so no @font-face is shipped. Loaded lazily by the Home page controller (frappe.require), not app-wide. */\n\n"
	),
)

#: Every design-system class the Analytics boards (design/Analytics/*.dc.html) draw with, plus the swatch roles the
#: chart components pass as tone keys (`is-cat-*`, `is-seq-*`, `is-pair-*`, `is-family-*`).
ANALYTICS_ALLOWED = frozenset({
	"btn", "btn-primary", "btn-secondary", "btn-ghost",
	"field", "input", "is-num", "table",
	"kt-icon", "is-sm", "is-md", "is-lg", "kt-icon-chip",
	"kt-tabs", "kt-tab",
	"kt-kpi-card", "kt-kpi-head", "kt-kpi-value",
	"kt-result-value",
	"kt-disclosure", "kt-disclosure-head", "kt-disclosure-title-row", "kt-disclosure-title", "kt-disclosure-chevron", "kt-disclosure-body",
	"kt-empty", "kt-spot", "is-zero", "is-error", "is-neutral",
	"is-cat-1", "is-cat-2", "is-cat-3", "is-cat-4", "is-cat-5", "is-cat-6",
	"is-seq-1", "is-seq-2", "is-seq-3", "is-seq-4",
	"is-pair-strong", "is-pair-tint",
	"is-family-1", "is-family-2", "is-family-3",
})

ANALYTICS = Target(
	name="analytics",
	source_glob="docs/mvp-1-r1/19_analytics/design/_ds/kentender-industry-*/styles.css",
	target=ROOT / "kentender_core/kentender_core/public/js/analytics/kt_analytics_ds.bundle.css",
	scope=".kt-industry.kt-analytics",
	allowed=ANALYTICS_ALLOWED,
	resets=(
		# Leaks of the repository's old kt_industry_tokens.css into Analytics' classes, found by the computed-style
		# comparison with that stylesheet loaded (scripts/analytics_design_scope_check.mjs, variant V1; Home found the
		# first and the link one the same way, HOME6-0112). The design system never sets these, so each is reset to
		# the value the board computes.
		".kt-industry.kt-analytics .kt-kpi-card {\n\tborder: 0;\n}",  # old: a 1px bordered card behind a summary column
		".kt-industry.kt-analytics .kt-tab {\n\tfont-family: inherit;\n}",  # old: the body face (Barlow) on every tab
		".kt-industry.kt-analytics .kt-disclosure-title {\n\tletter-spacing: normal;\n\ttext-transform: none;\n}",  # old: small capitals
		".kt-industry.kt-analytics .kt-empty {\n\tflex: 0 1 auto;\n\tflex-direction: row;\n\talign-items: normal;\n\tjustify-content: normal;\n}",  # old: a centred, growing column
		# Leaks of Frappe's own Desk stylesheet (computed-style comparison, variant V2). Each is a rule of Frappe's or
		# Bootstrap's that outranks the design system's single-class rule and changes what the board draws.
		# Frappe: `.btn:not(.btn-md):not(.btn-lg):not(.btn-xs) { padding: 4px 8px }` (four classes) shrank every button.
		f".kt-industry.kt-analytics .btn:not(.btn-md):not(.btn-lg):not(.btn-xs) {{\n\tpadding: var(--space-2) calc(var(--space-3) * 1.2);\n}}",
		f".kt-industry.kt-analytics .btn-ghost:not(.btn-md):not(.btn-lg):not(.btn-xs) {{\n\tpadding-inline: var(--space-1);\n}}",
		# Bootstrap: `label { margin-bottom: .5rem }` made the tab row 8px taller (a tab is a label).
		".kt-industry.kt-analytics .kt-tab {\n\tmargin-bottom: 0;\n}",
		# Frappe: `a { text-decoration: none }` removed the underline the boards keep (ANL §10A.1 rule 8: links stay underlined).
		f".kt-industry.kt-analytics a{LINK_GUARD} {{\n\ttext-decoration: underline;\n}}",
		# Frappe: `svg { vertical-align: middle }` moved inline icons off the baseline the board draws them on.
		".kt-industry.kt-analytics .kt-icon {\n\tvertical-align: baseline;\n}",
		*control_shape(".kt-industry.kt-analytics", fields=True),
	),
	header=(
		"/* GENERATED by scripts/home_design_css.py --target analytics from the Analytics design pack's design system (DS-REV-002)\n"
		"   and the Analytics boards' own data-colour block (\"DS-REV-002 data-colour tune (proposal)\", FU-ANL-10: not yet approved).\n"
		"   Source: {source}\n"
		"   Boards: docs/mvp-1-r1/19_analytics/design/Analytics/*.dc.html (their local style block is identical in all six files).\n"
		"   Scope: every selector sits under .kt-industry.kt-analytics, so no other page is restyled (ANL plan D9, Phase 4).\n"
		"   Chart rules: scripts/analytics_charts.css (hand-authored, scoped here on write).\n"
		"   Do not edit by hand: change the generator or its sources, then rerun it. Inter is Frappe's own font (--font-stack),\n"
		"   so no @font-face is shipped. Loaded lazily by the Analytics page controller (frappe.require), not app-wide. */\n\n"
	),
	boards_glob="docs/mvp-1-r1/19_analytics/design/Analytics/*.dc.html",
	extra_css=ROOT / "scripts/analytics_charts.css",
)

TARGETS = {"home": HOME, "analytics": ANALYTICS}

# Back-compat names: Home's tests and tooling read these.
SOURCE_GLOB = HOME.source_glob
TARGET = HOME.target
SCOPE = HOME.scope
ALLOWED = set(HOME.allowed)
RESETS = HOME.resets


def _split(selector: str) -> list[str]:
	parts, depth, current = [], 0, ""
	for char in selector:
		depth += (char == "(") - (char == ")")
		if char == "," and depth == 0:
			parts.append(current.strip())
			current = ""
		else:
			current += char
	return [part for part in (*parts, current.strip()) if part]


def _declarations(rule, keep: set[str] | None = None) -> str:
	out = []
	for item in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
		if item.type != "declaration":
			continue
		if keep is not None and item.name not in keep:
			continue
		important = " !important" if item.important else ""
		out.append(f"\t{item.name}: {tinycss2.serialize(item.value).strip()}{important};")
	return "\n".join(out)


def _scoped(selector: str, target: Target = HOME) -> list[str] | None:
	"""The scoped selector(s) for one source selector, or None to drop it."""
	scope = target.scope
	if selector == ":root":
		return [scope]
	if selector == "body":
		return [scope]
	if selector in ("*", "*::before", "*::after"):
		return {"*": [scope, f"{scope} *"], "*::before": [f"{scope} *::before"], "*::after": [f"{scope} *::after"]}[selector]
	classes = set(re.findall(r"\.([A-Za-z_][\w-]*)", selector))
	if not classes:
		if selector in ("a", "a:hover"):
			head, _, pseudo = selector.partition(":")
			return [f"{scope} {head}{LINK_GUARD}{':' + pseudo if pseudo else ''}"]
		return [f"{scope} {selector}"] if selector in BASE else None
	return [f"{scope} {selector}"] if classes <= target.allowed else None


def _rules(nodes, target: Target = HOME) -> list[str]:
	out: list[str] = []
	for node in nodes:
		if node.type == "at-rule" and node.lower_at_keyword == "media":
			inner = _rules(tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True), target)
			if inner:
				query = tinycss2.serialize(node.prelude).strip()
				body = "\n".join("\t" + line if line else line for chunk in inner for line in chunk.split("\n"))
				out.append(f"@media {query} {{\n{body}\n}}")
			continue
		if node.type != "qualified-rule":
			continue
		selectors = _split(tinycss2.serialize(node.prelude).strip())
		kept: list[str] = []
		body_only = selectors == ["body"]
		for selector in selectors:
			scoped = _scoped(selector, target)
			if scoped:
				kept.extend(scoped)
		if not kept:
			continue
		declarations = _declarations(node, BODY_KEEP if body_only else None)
		if declarations:
			out.append(",\n".join(dict.fromkeys(kept)) + " {\n" + declarations + "\n}")
	return out


def _board_style(target: Target) -> list[str]:
	"""The boards' local `<style>` rules, scoped: the data-colour `:root` block and the `a` / `a:hover` rules.

	The page's `body` rule (ground colour and margin of the artboard sheet) is not carried: the ground is Frappe's.
	Every board must carry the same block, otherwise the boards disagree about the palette and the build stops."""
	if not target.boards_glob:
		return []
	boards = sorted(glob.glob(str(ROOT / target.boards_glob)))
	styles = {Path(b).name: re.search(r"<style>(.*?)</style>", Path(b).read_text(encoding="utf-8"), flags=re.S) for b in boards}
	blocks = {name: match.group(1).strip() for name, match in styles.items() if match}
	if len(set(blocks.values())) != 1 or len(blocks) != len(boards):
		raise SystemExit(f"the boards' local style blocks differ or are missing: {sorted(blocks)}")
	nodes = tinycss2.parse_stylesheet(next(iter(blocks.values())), skip_comments=True, skip_whitespace=True)
	return _rules([n for n in nodes if not (n.type == "qualified-rule" and tinycss2.serialize(n.prelude).strip() == "body")], target)


def _extra(target: Target) -> list[str]:
	"""Hand-authored rules for classes the pack does not define. Every selector is put under the scope here, so a
	rule written without it still cannot reach another page."""
	if not target.extra_css:
		return []
	out: list[str] = []
	for node in tinycss2.parse_stylesheet(target.extra_css.read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True):
		if node.type == "at-rule" and node.lower_at_keyword == "media":
			inner = []
			for rule in tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True):
				if rule.type == "qualified-rule":
					inner.append(_extra_rule(rule, target))
			query = tinycss2.serialize(node.prelude).strip()
			body = "\n".join("\t" + line if line else line for chunk in inner for line in chunk.split("\n"))
			out.append(f"@media {query} {{\n{body}\n}}")
		elif node.type == "qualified-rule":
			out.append(_extra_rule(node, target))
		elif node.type == "at-rule":
			raise SystemExit(f"{target.extra_css.name}: only @media is allowed, not @{node.lower_at_keyword}")
	return out


def _extra_rule(node, target: Target) -> str:
	selectors = [f"{target.scope} {s}" for s in _split(tinycss2.serialize(node.prelude).strip())]
	return ",\n".join(selectors) + " {\n" + _declarations(node) + "\n}"


def build(target: Target = HOME) -> str:
	source = Path(sorted(glob.glob(str(ROOT / target.source_glob)))[0])
	nodes = tinycss2.parse_stylesheet(source.read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True)
	header = target.header.format(source=source.relative_to(ROOT))
	return header + "\n\n".join([*_rules(nodes, target), *_board_style(target), *_extra(target), *target.resets]) + "\n"


if __name__ == "__main__":
	name = sys.argv[sys.argv.index("--target") + 1] if "--target" in sys.argv else "home"
	if name not in TARGETS:
		sys.exit(f"unknown --target {name!r}; choose from {sorted(TARGETS)}")
	chosen = TARGETS[name]
	css = build(chosen)
	if "--check" in sys.argv:
		sys.exit(0 if chosen.target.exists() and chosen.target.read_text(encoding="utf-8") == css else 1)
	chosen.target.parent.mkdir(parents=True, exist_ok=True)
	chosen.target.write_text(css, encoding="utf-8")
	print(f"wrote {chosen.target.relative_to(ROOT)}: {len(css.splitlines())} lines")
