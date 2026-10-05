#!/usr/bin/env python3
"""Build kentender_core/public/css/kt_industry_tokens.css — the shared Industry stylesheet — from the DS-REV-002 design pack.

HOME-CHG-001 v0.6 Phase 1B (HOME6-0103..0106; owner instruction 5 Oct 2026: one repo-wide switch). It replaces the
hand-ported DS-REV-001 stylesheet. Three parts, in this order:

1. the pack's own stylesheet (`docs/mvp-1-r1/18_home_page/design/_ds/kentender-industry-*/styles.css`), every rule scoped
   under `.kt-industry` by the same generator Home and Analytics use (`home_design_css.py`), minus the design tool's own
   chrome (`.kt-app-shell`, `.kt-sidebar`, `.kt-topbar`, `.kt-nav*`, `.kt-breadcrumb`: Frappe supplies the shell);
2. the old stylesheet's rules for the classes the pack does not define (the tree, the editor grid, the next-step block's
   details, the sticky footer ...), kept as they were: they read `--kt-*` custom properties, which part 3 maps;
3. the old `--kt-*` custom properties, each defined as the pack's token it stands for (2,400 inline styles across the Vue
   screens read them; renaming those is out of scope). Values, not class names: KT-STD-001 v1.22 §10's rule against
   compatibility aliases is about classes, and every old class name is migrated (`RENAMES`).

    python3 scripts/industry_design_css.py            # rewrite the stylesheet
    python3 scripts/industry_design_css.py --check    # exit 1 if it is out of date
    python3 scripts/industry_design_css.py --renames  # print the class renames the codemod applies

Needs `tinycss2` (the bench environment: ../../env/bin/python).
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import tinycss2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import home_design_css as gen  # noqa: E402

ROOT = gen.ROOT
SOURCE = "docs/mvp-1-r1/18_home_page/design/_ds/kentender-industry-*/styles.css"
TARGET = ROOT / "kentender_core/kentender_core/public/css/kt_industry_tokens.css"
OLD = ROOT / "scripts/industry_old_stylesheet.css"

#: The design tool's own shell. Frappe Desk is the shell, so none of it is shipped.
CHROME = frozenset({"kt-app-shell", "kt-sidebar", "kt-sidebar-avatar", "kt-sidebar-footer", "kt-sidebar-header", "kt-sidebar-header-text",
	"kt-sidebar-icon", "kt-sidebar-search", "kt-sidebar-user", "kt-topbar", "kt-topbar-avatar", "kt-topbar-divider", "kt-topbar-icon-btn",
	"kt-topbar-right", "kt-topbar-user", "kt-topbar-user-text", "kt-nav-child", "kt-nav-children", "kt-nav-group", "kt-nav-item",
	"kt-nav-item-tag", "kt-breadcrumb", "nav", "nav-brand", "org", "role", "name", "duotone", "woff2"})

#: Old class -> the pack's class. Every consumer is migrated (no aliases). Applied to whole class tokens only.
RENAMES = {
	"kt-btn": "btn", "kt-btn-primary": "btn-primary", "kt-btn-secondary": "btn-secondary", "kt-btn-ghost": "btn-ghost",
	"kt-btn-danger": "btn-danger", "kt-btn-sm": "btn-sm", "kt-btn-destructive": "btn-destructive", "kt-btn-block": "btn-block", "kt-field": "field", "kt-input": "input", "kt-table": "table",
	"kt-dialog": "dialog", "kt-dialog-actions": "dialog-actions", "kt-dialog-backdrop": "dialog-backdrop", "kt-dialog-title": "dialog-title",
	"kt-card": "card", "kt-blueprint": "blueprint", "kt-corner": "corner", "kt-radio": "radio", "kt-seg-opt": "seg-opt",
	"kt-tag": "tag", "kt-tag-accent": "tag-accent", "kt-tag-accent-2": "tag-accent-2", "kt-tag-neutral": "tag-neutral", "kt-tag-outline": "tag-outline",
	"kt-icon-tile": "kt-icon-chip",
}

#: Old custom property -> what it is now. `None` keeps the old definition (no counterpart in the pack).
TOKEN_MAP = {
	"--kt-color-bg": "--color-bg", "--kt-color-surface": "--color-surface", "--kt-color-surface-2": "--color-control", "--kt-color-text": "--color-text",
	"--kt-color-accent": "--color-accent", "--kt-color-accent-2": "--color-accent-2", "--kt-color-divider": "--color-divider",
	"--kt-font-heading": "--font-heading", "--kt-font-heading-weight": "--font-heading-weight", "--kt-font-body": "--font-body",
	"--kt-radius-sm": "--radius-sm", "--kt-radius-md": "--radius-md", "--kt-radius-lg": "--radius-lg",
	"--kt-shadow-sm": "--shadow-sm", "--kt-shadow-md": "--shadow-md", "--kt-shadow-lg": "--shadow-lg",
	"--kt-space-7": None,
}
for _n in range(1, 7):
	TOKEN_MAP[f"--kt-chart-{_n}"] = f"--chart-{_n}"
	TOKEN_MAP[f"--kt-space-{_n}"] = f"--space-{_n}"
for _n in (100, 200, 300, 400, 500, 600, 700, 800, 900):
	for _fam in ("neutral", "accent", "accent-2"):
		TOKEN_MAP[f"--kt-color-{_fam}-{_n}"] = f"--color-{_fam}-{_n}"
TOKEN_MAP["--kt-space-8"] = "--space-8"
for _s in ("live", "draft", "pending", "attention", "critical"):
	TOKEN_MAP[f"--kt-status-{_s}"] = f"--status-{_s}"
	TOKEN_MAP[f"--kt-status-{_s}-bg"] = f"--status-{_s}-bg"
TOKEN_MAP["--kt-color-attention"] = "--status-attention"
TOKEN_MAP["--kt-color-critical"] = "--status-critical"

#: Leaks of Frappe's own Desk stylesheet that outrank the pack's one-class rules (found on Home and Analytics by the computed-style
#: comparison with the board, 5 Oct 2026; the same reasons apply here). Each is reset to what the board computes.
RESETS = (
	# The page ground: one white sheet (.kt-page) sits on it (the pack's readme, "Direction"). Frappe's own page container is white.
	".kt-industry {\n\tbackground: var(--color-bg);\n\tmin-height: 100vh;\n}",
	# A tab that is a <button role="tab"> (the pages' tabs), not the pack's label around a radio: drop the browser's button look.
	".kt-industry button.kt-tab {\n\tbackground: none;\n\tborder: 0;\n\tborder-radius: 0;\n\tbox-shadow: none;\n\tfont-family: inherit;\n\tpadding-top: 0;\n\tpadding-inline: 0;\n\tmargin: 0;\n\theight: auto;\n}",
	# Desk sets 0.26px of letter spacing on its body; the boards set in Inter with none.
	".kt-industry {\n\tletter-spacing: normal;\n}",
	# Frappe: `.btn:not(.btn-md):not(.btn-lg):not(.btn-xs) { padding: 4px 8px }` (four classes) made every button 27px high, not 32.
	".kt-industry .btn:not(.btn-md):not(.btn-lg):not(.btn-xs):not(.btn-sm) {\n\tpadding: var(--space-2) calc(var(--space-3) * 1.2);\n\tletter-spacing: normal;\n}",
	".kt-industry .btn-ghost:not(.btn-md):not(.btn-lg):not(.btn-xs):not(.btn-sm) {\n\tpadding-inline: var(--space-1);\n}",
	# Frappe: `a { text-decoration: none }` removed the underline KT-STD-001 v1.22 section 2.4 requires of links.
	f".kt-industry a{gen.LINK_GUARD} {{\n\ttext-decoration: underline;\n}}",
	# The pack draws `.kt-page` in a block parent with `margin: 24px auto`. In Desk it is the sole child of `.kt-shell`, a flex column, and a
	# horizontal auto margin on a stretched flex item cancels the stretch: the sheet shrinks to its content width (a narrow card until a wide
	# table is opened). Found live 22 Sep 2026 and fixed in the old stylesheet; the switch to the pack dropped the fix (reported 6 Oct 2026,
	# Needs detail and Award record). `.kt-shell` already centres and caps the column.
	# The pack's top margin is also dropped: `.kt-shell` already pads 16px under the Desk header, and the two stacked to 36px of empty band above
	# the sheet on every module built on `.kt-page` (owner, 6 Oct 2026; Strategy and Budget, which draw their sheet without it, sit at 16px).
	".kt-industry .kt-page {\n\tmargin-inline: 0;\n\tmargin-top: 0;\n}",
	# Frappe: `svg { vertical-align: middle }` moved inline icons off the baseline the board draws them on.
	".kt-industry .kt-icon {\n\tvertical-align: baseline;\n}",
)

#: Table structure (owner, 6 Oct 2026: after the switch a register read as flat). Inside the pack's own rules: no tinted header, no accent rule, no
#: capitals. The pack's final table rules drew a 1 px header rule; its earlier 2 px rule was too strong, so it is a 1 px neutral-500 rule,
#: the identifying first column takes the heading weight with its reference beneath it in muted text, and one size for the row action.
STRUCTURE = (
	".kt-industry .table thead th {\n\tcolor: var(--color-heading);\n\tborder-bottom: 1px solid var(--color-neutral-500);\n}",
	".kt-industry .table tbody td:first-child {\n\tfont-weight: 600;\n\tcolor: var(--color-heading);\n}",
	# The lines under a primary cell's title: the reference, a sub-line, a note. Every screen's own class for them reads the same.
	",\n".join(f".kt-industry .table tbody td:first-child {c}" for c in (".kt-muted", ".kt-label", ".text-muted", ".tnd-sub", ".bds-tender-ref", ".bds-muted", ".pln-row-ref", ".tsr-muted"))
	+ " {\n\tfont-weight: 400;\n\tfont-size: 13px;\n\tcolor: var(--color-text-muted);\n}",
	".kt-industry .table tbody td:first-child .input {\n\tfont-weight: 400;\n}",
	# One row action: the ghost button the boards draw, one size in every register (the global reset gives it 4 px sides, set for a lone link).
	".kt-industry .table td .btn-ghost:not(.btn-md):not(.btn-lg):not(.btn-xs):not(.btn-sm) {\n\tpadding: 4px 10px;\n}",
	".kt-industry .btn-ghost.kt-danger {\n\tcolor: var(--status-critical);\n}",
	".kt-industry .btn-ghost.kt-danger:hover:not(:disabled) {\n\tbackground: var(--status-critical-bg);\n}",
	# A link in a table keeps the link colour on a hovered row (the old stylesheet turned it rust; the pack bars rust from links).
	f".kt-industry .table tbody tr:hover a{gen.LINK_GUARD} {{\n\tcolor: var(--color-accent-900);\n}}",
)

HEADER = (
	"/* GENERATED by scripts/industry_design_css.py from the design pack's design system (DS-REV-002), KT-STD-001 v1.22.\n"
	"   Source: {source}\n"
	"   Part 1: the pack's rules, scoped under .kt-industry. Part 2: the old stylesheet's rules for classes the pack does not\n"
	"   define (scripts/industry_old_stylesheet.css). Part 3: the old --kt-* custom properties, defined as the pack's tokens.\n"
	"   Do not edit by hand: change the generator or its sources, then rerun it. Inter is Frappe's own font (--font-stack), so\n"
	"   no @font-face is shipped. Loaded app-wide by the apps' hooks, scoped to .kt-industry so it cannot reach Desk chrome. */\n\n"
)


def _pack_nodes():
	source = Path(sorted(glob.glob(str(ROOT / SOURCE)))[0])
	return source, tinycss2.parse_stylesheet(source.read_text(encoding="utf-8"), skip_comments=True, skip_whitespace=True)


def _classes(selector: str) -> set[str]:
	return set(re.findall(r"\.([A-Za-z_][\w-]*)", selector))


def _pack_classes(nodes) -> set[str]:
	found: set[str] = set()
	for node in nodes:
		if node.type == "qualified-rule":
			found |= _classes(tinycss2.serialize(node.prelude))
		elif node.type == "at-rule" and node.lower_at_keyword == "media":
			for rule in tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True):
				if rule.type == "qualified-rule":
					found |= _classes(tinycss2.serialize(rule.prelude))
	return found


_RENAME_PATTERN = re.compile(r"(?<![\w-])(" + "|".join(sorted(map(re.escape, RENAMES), key=len, reverse=True)) + r")(?![\w-])")


def _renamed(selector: str) -> str:
	return _RENAME_PATTERN.sub(lambda m: RENAMES[m.group(1)], selector)


def _norm(selector: str) -> str:
	return " ".join(selector.split())


def _selectors_of(rules: list[str]) -> set[str]:
	found: set[str] = set()
	for node in tinycss2.parse_stylesheet("\n".join(rules), skip_comments=True, skip_whitespace=True):
		if node.type == "qualified-rule":
			found |= {_norm(x) for x in gen._split(tinycss2.serialize(node.prelude))}
		elif node.type == "at-rule" and node.lower_at_keyword == "media":
			for rule in tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True):
				if rule.type == "qualified-rule":
					found |= {_norm(x) for x in gen._split(tinycss2.serialize(rule.prelude))}
	return found


def _old_rules(pack_rules: list[str]) -> list[str]:
	"""The old stylesheet's rules that the pack does not already say, with the renamed classes carried over.

	A selector is kept (its class names migrated by `RENAMES`) unless the pack's own output already has exactly that
	selector, in which case the pack's rule is the new design and the old one is dropped. That keeps what the pack never
	drew (a tab that is a button with `aria-selected`, a radio's `.dot`, the tree, the sticky footer ...) and nothing that
	it did. Design-tool chrome selectors are dropped."""
	text = OLD.read_text(encoding="utf-8")
	nodes = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
	pack_selectors = _selectors_of(pack_rules)

	def keep(selector: str) -> bool:
		renamed = _norm(_renamed(selector))
		classes = _classes(renamed) - {"kt-industry"}
		if renamed in pack_selectors or (classes & CHROME):
			return False
		return bool(classes) or renamed.startswith(".kt-industry ")

	def emit(node) -> str | None:
		selectors = [_norm(_renamed(s)) for s in gen._split(tinycss2.serialize(node.prelude).strip()) if keep(s)]
		if not selectors:
			return None
		declarations = gen._declarations(node)
		return (",\n".join(selectors) + " {\n" + declarations + "\n}") if declarations else None

	out: list[str] = []
	for node in nodes:
		if node.type == "qualified-rule":
			rule = emit(node)
			if rule:
				out.append(rule)
		elif node.type == "at-rule" and node.lower_at_keyword in ("media", "container"):
			inner = [emit(r) for r in tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True) if r.type == "qualified-rule"]
			inner = [r for r in inner if r]
			if inner:
				body = "\n".join("\t" + line if line else line for chunk in inner for line in chunk.split("\n"))
				out.append(f"@{node.lower_at_keyword} {tinycss2.serialize(node.prelude).strip()} {{\n{body}\n}}")
		elif node.type == "at-rule" and node.lower_at_keyword == "keyframes":
			out.append(tinycss2.serialize([node]).strip())
	return out


def _pack_containers(nodes, target) -> list[str]:
	"""The pack's `@container` rules, scoped (the shared generator carries only `@media`)."""
	out: list[str] = []
	for node in nodes:
		if node.type == "at-rule" and node.lower_at_keyword == "container":
			inner = gen._rules(tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True), target)
			if inner:
				body = "\n".join("\t" + line if line else line for chunk in inner for line in chunk.split("\n"))
				out.append(f"@container {tinycss2.serialize(node.prelude).strip()} {{\n{body}\n}}")
	return out


def _token_block() -> str:
	lines = []
	for old, new in TOKEN_MAP.items():
		if new is None:
			continue
		lines.append(f"\t{old}: var({new});")
	return ".kt-industry {\n" + "\n".join(lines) + "\n}"


def build() -> str:
	source, nodes = _pack_nodes()
	allowed = frozenset(_pack_classes(nodes) - CHROME)
	target = gen.Target(name="industry", source_glob=SOURCE, target=TARGET, scope=".kt-industry", allowed=allowed, resets=(), header=HEADER)
	pack_rules = list(gen._rules(nodes, target)) + _pack_containers(nodes, target)
	old = _old_rules(pack_rules)
	kept_old_tokens = [f"\t{n}: {v};" for n, v in _old_token_values().items() if TOKEN_MAP.get(n, "x") is None]
	space7 = (".kt-industry {\n" + "\n".join(kept_old_tokens) + "\n}") if kept_old_tokens else ""
	parts = [*pack_rules, "/* Part 2: classes the pack does not define (kept from the previous stylesheet) */", *old, "/* Part 3: the previous --kt-* custom properties, as the pack's tokens */", _token_block()]
	if space7:
		parts.append(space7)
	parts += ["/* Part 4: Frappe Desk rules that outrank the pack's, reset to what the board draws */", *RESETS]
	parts += ["/* Part 5: table structure inside the pack's rules */", *STRUCTURE]
	parts += ["/* Part 6: buttons and fields are rectangular and outlined, so they cannot be mistaken for a status pill */", *gen.control_shape(".kt-industry", fields=True)]
	return HEADER.format(source=source.relative_to(ROOT)) + "\n\n".join(parts) + "\n"


def _old_token_values() -> dict[str, str]:
	return {n: " ".join(v.split()) for n, v in re.findall(r"(--kt-[\w-]+)\s*:\s*([^;]+);", OLD.read_text(encoding="utf-8"))}


if __name__ == "__main__":
	if "--renames" in sys.argv:
		for old, new in RENAMES.items():
			print(f"{old}\t{new}")
		sys.exit(0)
	css = build()
	out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else TARGET
	if "--check" in sys.argv:
		sys.exit(0 if out.exists() and out.read_text(encoding="utf-8") == css else 1)
	out.write_text(css, encoding="utf-8")
	print(f"wrote {out}: {len(css.splitlines())} lines")
