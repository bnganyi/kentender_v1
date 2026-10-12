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
	# The segmented control (Yes/No, Permanent/Acting ...) is the pack's `.seg` / `.seg-opt`, once, for every screen. These are the only
	# things a screen needed beyond the pack: a track that does not stretch in a column, no label margin, and a disabled option that
	# stays readable. No module may define its own copy (test_one_segmented_control).
	".kt-industry .seg {\n\twidth: fit-content;\n}",
	".kt-industry .seg-opt {\n\tmargin: 0;\n}",
	".kt-industry .seg-opt:has(input:disabled) {\n\tcursor: default;\n\topacity: 0.7;\n}",
	".kt-industry .seg-opt.is-disabled {\n\topacity: 0.55;\n\tcursor: not-allowed;\n}",
	# A dialog never grows past the window: the backdrop centres it and pads it, so a tall one (the Start Tender dialog with both disclosures
	# open) was clipped at the top and the bottom with no way to scroll to its title or its buttons on a short screen. It scrolls inside the
	# window instead. `dvh` follows a phone's moving address bar; `vh` is the fallback. A dialog that sets its own height keeps it.
	".kt-industry .dialog {\n\tmax-height: calc(100vh - 2 * var(--space-4));\n\tmax-height: calc(100dvh - 2 * var(--space-4));\n\toverflow-y: auto;\n\toverscroll-behavior: contain;\n}",
)

HEADER = (
	"/* GENERATED by scripts/industry_design_css.py from the design pack's design system (DS-REV-002), KT-STD-001 v1.22.\n"
	"   Source: {source}\n"
	"   Part 1: the pack's rules, scoped under .kt-industry. Part 2: the old stylesheet's rules for classes the pack does not\n"
	"   define (scripts/industry_old_stylesheet.css). Part 3: the old --kt-* custom properties, defined as the pack's tokens.\n"
	"   Do not edit by hand: change the generator or its sources, then rerun it. Inter is Frappe's own font (--font-stack), so\n"
	"   no @font-face is shipped. Loaded app-wide by the apps' hooks, scoped to .kt-industry so it cannot reach Desk chrome. */\n\n"
)
#: The table pager (table-pagination standard). Not in the pack yet: the pack should own it, so the rules are written to read
#: from its tokens only. Count at the far left, "Rows per page" and the numbered pages to the right; the current page is a solid
#: accent square, every other control is a ghost button. On a narrow screen the numbers give way to "Page n of m".
PAGER = (
	".kt-industry .kt-pager {\n\tdisplay: flex;\n\talign-items: center;\n\tflex-wrap: wrap;\n\tgap: var(--space-3) var(--space-5);\n\tmargin-top: var(--space-4);\n\tpadding-top: var(--space-3);\n\tborder-top: 1px solid var(--color-divider);\n}",
	".kt-industry .kt-pager-count {\n\tmargin: 0 auto 0 0;\n\tfont-size: 13px;\n\tcolor: var(--color-neutral-700);\n}",
	".kt-industry .kt-pager-size {\n\tdisplay: inline-flex;\n\talign-items: center;\n\tgap: var(--space-2);\n\tmargin: 0;\n\tfont-size: 13px;\n\tcolor: var(--color-neutral-700);\n}",
	".kt-industry .kt-pager-size .input {\n\twidth: auto;\n\tmin-height: 32px;\n\tpadding-block: 4px;\n}",
	".kt-industry .kt-pager-nav {\n\tdisplay: inline-flex;\n\talign-items: center;\n\tgap: 4px;\n}",
	".kt-industry .kt-pager-page {\n\tmin-width: 32px;\n\tpadding-inline: var(--space-2);\n\tfont-variant-numeric: tabular-nums;\n}",
	".kt-industry .kt-pager-page.is-current,\n.kt-industry .kt-pager-page.is-current:hover:not(:disabled) {\n\tbackground: var(--color-accent);\n\tcolor: #fff;\n\tcursor: default;\n}",
	".kt-industry .kt-pager-step {\n\tpadding-inline: var(--space-2);\n}",
	".kt-industry .kt-pager-gap {\n\tpadding-inline: 2px;\n\tcolor: var(--color-neutral-600);\n}",
	".kt-industry .kt-pager-status {\n\tdisplay: none;\n\tfont-size: 13px;\n\tcolor: var(--color-neutral-700);\n}",
	"@media (max-width: 640px) {\n\t.kt-industry .kt-pager-count {\n\t\tflex-basis: 100%;\n\t}\n\t.kt-industry .kt-pager-nav {\n\t\tmargin-left: auto;\n\t}\n\t.kt-industry .kt-pager-page,\n\t.kt-industry .kt-pager-gap {\n\t\tdisplay: none;\n\t}\n\t.kt-industry .kt-pager-status {\n\t\tdisplay: inline;\n\t\tpadding-inline: var(--space-2);\n\t}\n}",
)



#: DS-REV-004 (Project Owner approved 6 Oct 2026, "2e it is. Approved"): the journey position figure, the compact track and the blocked next step.
#: The pack does not carry these yet; the rules are the handoff's, scoped to `.kt-industry`, with the narrow-screen, forced-colours and print handling
#: it asks for. They sit after the pack's `.kt-journey-*` rules, so the compact form (`.is-compact`) overrides the 4px slabs.
JOURNEY = (
	".kt-industry .kt-journey-lead {\n\tdisplay: grid;\n\tgap: 32px;\n\talign-items: start;\n}",
	".kt-industry .kt-journey-lead.has-position {\n\tgrid-template-columns: 200px minmax(0, 1fr);\n}",
	".kt-industry .kt-journey-position {\n\tdisplay: grid;\n\tgap: 4px;\n\tpadding-right: 24px;\n\tborder-right: 1px solid var(--color-divider);\n}",
	".kt-industry .kt-journey-position-label {\n\tfont-size: 12px;\n\tfont-weight: 600;\n\tcolor: var(--color-neutral-700);\n}",
	".kt-industry .kt-journey-position-value {\n\tdisplay: flex;\n\talign-items: baseline;\n\tgap: 6px;\n\tline-height: 1;\n\tfont-variant-numeric: tabular-nums;\n}",
	".kt-industry .kt-journey-position-n {\n\tfont-size: 44px;\n\tfont-weight: 600;\n\tcolor: var(--color-figure);\n}",
	".kt-industry .kt-journey-position-of {\n\tfont-size: 20px;\n\tfont-weight: 500;\n\tcolor: var(--color-neutral-600);\n}",
	".kt-industry .kt-journey-position-state {\n\tmargin-top: 6px;\n\tfont-size: 12px;\n\tfont-weight: 600;\n\tcolor: var(--color-figure);\n}",
	".kt-industry .kt-journey-position.is-blocked .kt-journey-position-n,\n.kt-industry .kt-journey-position.is-blocked .kt-journey-position-state {\n\tcolor: var(--status-attention);\n}",
	"/* D1/K3, applied as recommended: with every stage done the figure reads \"N of N\" and the word Done in the live status colour. */\n.kt-industry .kt-journey-position.is-done .kt-journey-position-state {\n\tcolor: var(--status-live);\n}",
	".kt-industry .kt-journey.is-compact {\n\tgap: 3px;\n\tpadding-top: 6px;\n}",
	".kt-industry .kt-journey.is-compact .kt-journey-stage {\n\tgap: 10px;\n}",
	".kt-industry .kt-journey.is-compact .kt-journey-bar {\n\theight: 6px;\n\tborder-radius: 3px;\n}",
	".kt-industry .kt-journey.is-compact .kt-journey-title {\n\tgap: 5px;\n\tpadding-right: 12px;\n\tfont-size: 13px;\n}",
	".kt-industry .kt-journey.is-compact .kt-journey-num {\n\tfont-family: inherit;\n\tfont-size: inherit;\n\tfont-variant-numeric: tabular-nums;\n}",
	".kt-industry .kt-journey.is-compact .is-current .kt-journey-title,\n.kt-industry .kt-journey.is-compact .is-blocked .kt-journey-title {\n\tfont-weight: 600;\n}",
	".kt-industry .kt-journey-check {\n\tflex: none;\n\twidth: 12px;\n\theight: 12px;\n\ttransform: translateY(1px);\n\tfill: none;\n\tstroke: var(--status-live);\n\tstroke-width: 2.5;\n\tstroke-linecap: round;\n\tstroke-linejoin: round;\n}",
	"/* The per-stage state stays in the markup for assistive technology; the figure and the check carry it on screen (KT-STD-001 section 2.9.2, v1.23). */\n.kt-industry .kt-journey.is-compact .kt-journey-state {\n\tposition: absolute;\n\twidth: 1px;\n\theight: 1px;\n\toverflow: hidden;\n\tclip: rect(0 0 0 0);\n\twhite-space: nowrap;\n}",
	".kt-industry .kt-journey.is-compact .kt-journey-stage {\n\tposition: relative;\n}",
	"/* Between 600 and about 760px five labels would sit in about 350px: stack the figure above the track (proposed in the handoff; checked at 700px). */\n@container (max-width: 760px) {\n\t.kt-industry .kt-journey-lead.has-position {\n\t\tgrid-template-columns: 1fr;\n\t\tgap: 16px;\n\t}\n\t.kt-industry .kt-journey-position {\n\t\tborder-right: 0;\n\t\tpadding-right: 0;\n\t}\n}",
	"/* Under 600px the one-line form takes over, as before; the figure goes with the row it leads. */\n@container (max-width: 600px) {\n\t.kt-industry .kt-journey-host > .kt-journey-lead {\n\t\tdisplay: none;\n\t}\n}",
	"@media (forced-colors: active) {\n\t.kt-industry .kt-journey.is-compact .kt-journey-bar {\n\t\theight: 0;\n\t\tborder-top-width: 6px;\n\t}\n\t.kt-industry .kt-journey-check {\n\t\tstroke: CanvasText;\n\t}\n}",
	"@media print {\n\t.kt-industry .kt-journey.is-compact .kt-journey-state {\n\t\tposition: static;\n\t\twidth: auto;\n\t\theight: auto;\n\t\toverflow: visible;\n\t\tclip: auto;\n\t\twhite-space: normal;\n\t}\n\t.kt-industry .kt-journey-check {\n\t\tstroke: #000;\n\t}\n\t.kt-industry .kt-journey-position-n,\n\t.kt-industry .kt-journey-position-state {\n\t\tcolor: #000 !important;\n\t}\n}",
	"/* The blocked next step: a 3px warning rule over the warning tint, square on the rule side, no icon. The rule is a status mark, not an accent rule. */\n.kt-industry .kt-notice.is-warning.kt-next-step {\n\tdisplay: grid;\n\tgap: 3px;\n\tpadding: 12px 16px 14px 14px;\n\tborder-left: 3px solid var(--status-attention);\n\tborder-radius: 0 var(--radius-lg) var(--radius-lg) 0;\n\tbackground: var(--status-attention-bg);\n}",
	".kt-industry .kt-notice.is-warning.kt-next-step .kt-notice-icon {\n\tdisplay: none;\n}",
	".kt-industry .kt-notice.is-warning.kt-next-step .kt-next-step-label {\n\tcolor: var(--status-attention);\n}",
	"@media (forced-colors: active) {\n\t.kt-industry .kt-notice.is-warning.kt-next-step {\n\t\tborder: 1px solid CanvasText;\n\t\tborder-left-width: 3px;\n\t}\n}",
)

#: The access state ("You do not have access to ..."). The pack draws it as `.kt-empty` + `.kt-spot.is-neutral` on the white sheet below a
#: 1px rule (readme, "Empty, success, error and access states"); the access state stands alone on the sheet, with no heading above it for the rule to separate, so it drops the rule. Modules had each rebuilt it by hand (a blueprint card, a notice, a bare
#: heading, a panel) and no two matched. `.kt-access` is the one remaining piece the pack does not size: the heading over the lock spot,
#: the reason beneath it, and the hint, always on the same top margin and measure and never centred vertically on the page.
ACCESS = (
	".kt-industry .kt-empty.kt-access {\n\tpadding: var(--space-8) var(--space-6);\n\tgap: var(--space-3);\n\talign-content: start;\n\tborder-top: 0;\n}",
	".kt-industry .kt-empty.kt-access h2 {\n\tmargin: var(--space-2) 0 0;\n\tmax-width: 52ch;\n\tfont-family: var(--font-heading);\n\tfont-weight: var(--font-heading-weight);\n\tfont-size: 23px;\n\tline-height: 1.25;\n\tcolor: var(--color-heading);\n\ttext-wrap: balance;\n}",
	".kt-industry .kt-empty.kt-access p {\n\tmax-width: 60ch;\n\tfont-size: 14.5px;\n\tline-height: 1.55;\n\tcolor: var(--color-neutral-700);\n}",
	".kt-industry .kt-empty.kt-access .kt-access-actions {\n\tmargin-top: var(--space-2);\n\tdisplay: flex;\n\tflex-wrap: wrap;\n\tjustify-content: center;\n\tgap: var(--space-2);\n}",
)

#: Fact values. The pack's `.kt-meta-value` is the figure style (heading face, 18px: an amount, a count, a total, an identifier).
#: A recorded fact (a name, a date, a reference, a status) that a board draws as plain text under its label is the same
#: label with a plain value; `.is-plain` is that one shared form, so no module carries its own copy of the rule. Planning's
#: boards draw their recorded facts this way (plain body-face text, 14px); a screen that left the figure style on a fact set
#: a date as large and as heavy as its own section heading (found live 9 Oct 2026, the publication details).
FACTS = (
	".kt-industry .kt-meta-value.is-plain {\n\tfont-family: inherit;\n\tfont-weight: 400;\n\tfont-size: 14px;\n}",
)


ALIGN = (
	# A flat section has no box, so its content starts where its heading starts. The pack's
	# own rules inset a group, a table's first column and a disclosure by one gutter, which
	# only reads as tidy inside a card (Budget). The rule of a group hangs in the gutter.
	".kt-industry .kt-page .kt-region .table th:first-child,\n.kt-industry .kt-page .kt-region .table td:first-child {\n\tpadding-left: 0;\n}",
	".kt-industry .kt-page .kt-region .table th:last-child,\n.kt-industry .kt-page .kt-region .table td:last-child {\n\tpadding-right: 0;\n}",
	".kt-industry .kt-page > .kt-disclosure .kt-disclosure-head,\n.kt-industry .kt-page > .kt-disclosure .kt-disclosure-body,\n.kt-industry .kt-page .kt-region .kt-disclosure .kt-disclosure-head,\n.kt-industry .kt-page .kt-region .kt-disclosure .kt-disclosure-body {\n\tpadding-left: 0;\n\tpadding-right: 0;\n}",
	".kt-industry .kt-page .kt-group {\n\tposition: relative;\n\tborder-left: 0;\n\tpadding-left: 0;\n}",
	".kt-industry .kt-page .kt-group::before {\n\tcontent: \"\";\n\tposition: absolute;\n\ttop: 2px;\n\tbottom: 2px;\n\tleft: calc(-1 * (var(--space-4) + 2px));\n\twidth: 2px;\n\tbackground: var(--color-divider);\n}",
	".kt-industry .kt-page > .kt-guidance-mount > .kt-guidance {\n\tpadding-left: 0;\n\tpadding-right: 0;\n}",
	".kt-industry .kt-page .kt-next-step.is-turn,\n.kt-industry .kt-page .kt-next-step.is-waiting,\n.kt-industry .kt-page .kt-next-step.is-done {\n\tposition: relative;\n\tborder-left: 0;\n\tpadding-left: 0;\n}",
	".kt-industry .kt-page .kt-next-step.is-turn::before,\n.kt-industry .kt-page .kt-next-step.is-waiting::before,\n.kt-industry .kt-page .kt-next-step.is-done::before {\n\tcontent: \"\";\n\tposition: absolute;\n\ttop: 2px;\n\tbottom: 2px;\n\tleft: calc(-1 * (14px + 3px));\n\twidth: 3px;\n\tbackground: var(--color-neutral-400);\n}",
	".kt-industry .kt-page .kt-next-step.is-turn::before {\n\tbackground: var(--color-accent);\n}",
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
	parts += ["/* Part 7: the table pager (table-pagination standard) */", *PAGER]
	parts += ["/* Part 8: journey position figure, compact track and blocked next step (DS-REV-004) */", *JOURNEY]
	parts += ["/* Part 9: the access state (\"You do not have access to ...\") */", *ACCESS]
	parts += ["/* Part 10: a recorded fact beside the pack's figure style (.kt-meta-value) */", *FACTS]
	parts += ["/* Part 11: flat sections start content at the heading's edge */", *ALIGN]
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
