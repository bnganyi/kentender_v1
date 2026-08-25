# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Hard gate — Industry design system is canonical (AGENTS.md §6.6).

kt_industry_tokens.css (owned by kentender_core, .kt-industry scope) is the
one design system for every Vue-in-Desk page across the whole application,
effective from the Strategy rebuild onward. No app may fork its own token
file or component-class vocabulary the way Strategy once did
(strategy_shared_tokens.css / .kt-strategy-ui, deleted — see STR-706 in
docs/mvp-1-r1/02_strategy/IMPLEMENTATION_TRACKER.md).

This gate finds every Vue-in-Desk page-level root component by locating
`createApp(<Component>)` calls in `*.bundle.js` entry files — the mount-point
convention this codebase already uses everywhere (see reference_data.bundle.js,
strategy_portfolio.bundle.js, etc.: a bundle imports its page's root .vue file
and calls createApp() on it directly in a `frappe.kt_mount_*` function). That is
a more reliable page-root signal than any naming or directory heuristic, since
it is exactly the code Frappe actually executes to mount the page.

Each resolved root .vue file's template must wrap in `class="kt-industry"`,
unless its bundle's filename is on LEGACY_BUNDLE_ALLOWLIST below — modules not
yet rebuilt onto Industry (Civic Ledger, Stitch Desk, and Procurement's other
bespoke systems are plain-JS/Tailwind fixtures today, not Vue-in-Desk pages,
so none of them currently appear here at all; the allowlist exists for the
day one of them is rebuilt as Vue but deliberately staged before its Industry
pass, not as a permanent exemption).
"""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

# Bundle-file basenames known to intentionally not be on Industry yet.
# Append only with a comment naming the tracking item; remove an entry only
# when that module's own full Industry rebuild lands.
LEGACY_BUNDLE_ALLOWLIST: frozenset[str] = frozenset()

KENTENDER_APPS: tuple[str, ...] = (
	"kentender_core",
	"kentender_strategy",
	"kentender_budget",
	"kentender_procurement",
	"kentender_stores",
	"kentender_assets",
	"kentender_suppliers",
	"kentender_governance",
	"kentender_compliance",
	"kentender_integrations",
	"kentender_transparency",
)

CREATE_APP_RE = re.compile(r"createApp\(\s*([A-Za-z0-9_$]+)\s*[,)]")
IMPORT_RE = re.compile(r"""import\s+([A-Za-z0-9_$]+)\s+from\s+["']([^"']+\.vue)["']""")


def _app_public_js(app: str) -> Path | None:
	try:
		base = Path(frappe.get_app_path(app)) / "public" / "js"
	except Exception:
		return None
	return base if base.is_dir() else None


def _find_bundle_files() -> list[Path]:
	found: list[Path] = []
	for app in KENTENDER_APPS:
		base = _app_public_js(app)
		if not base:
			continue
		found.extend(base.rglob("*.bundle.js"))
	return found


class TestIndustryDesignGate(FrappeTestCase):
	def test_industry_tokens_css_is_published(self):
		from kentender_core import hooks as core_hooks

		includes = "\n".join(core_hooks.app_include_css or [])
		self.assertIn("kt_industry_tokens.css", includes)

	def test_page_root_components_wrap_kt_industry(self):
		bundles = _find_bundle_files()
		self.assertGreaterEqual(len(bundles), 3, "expected at least the Reference Data + Strategy bundles")

		checked = 0
		allowlisted: list[str] = []
		for bundle_path in bundles:
			src = bundle_path.read_text(encoding="utf-8")
			match = CREATE_APP_RE.search(src)
			if not match:
				# Not a page-mount bundle (e.g. kt_industry_page_rail.bundle.js's
				# own internal createApp({...}) call has no named component and
				# is not itself a page root — it is the shared rail helper).
				continue

			if bundle_path.name in LEGACY_BUNDLE_ALLOWLIST:
				allowlisted.append(bundle_path.name)
				continue

			component_name = match.group(1)
			imports = dict(IMPORT_RE.findall(src))
			vue_rel = imports.get(component_name)
			self.assertIsNotNone(
				vue_rel, f"{bundle_path}: could not resolve import for createApp({component_name})"
			)
			vue_path = (bundle_path.parent / vue_rel).resolve()
			self.assertTrue(vue_path.is_file(), vue_path)
			vue_src = vue_path.read_text(encoding="utf-8")
			self.assertIn(
				'class="kt-industry"',
				vue_src,
				f"{vue_path}: page root must wrap class=\"kt-industry\" (AGENTS.md §6.6) "
				f"or its bundle ({bundle_path.name}) must be added to LEGACY_BUNDLE_ALLOWLIST "
				f"in kentender_core/tests/test_industry_design_gate.py with a tracking comment",
			)
			checked += 1

		print(
			f"[ui-industry-design-gate] checked {checked} Industry page root(s); "
			f"legacy-allowlisted bundle(s): {sorted(set(allowlisted)) or 'none'}"
		)
		self.assertGreaterEqual(checked, 3, "expected Reference Data + at least 2 Strategy pages checked")

	def test_no_app_forks_a_competing_token_file(self):
		"""No app's own public/css/*.css may define a second design-system root
		scope (its own --*-color-accent / --*-color-bg custom-property block) —
		exactly the strategy_shared_tokens.css / .kt-strategy-ui pattern this
		gate exists to prevent from recurring."""
		token_root_re = re.compile(r"\.[\w-]+\s*\{[^}]*--[\w-]*-color-accent\s*:", re.DOTALL)
		violations: list[str] = []
		for app in KENTENDER_APPS:
			try:
				css_root = Path(frappe.get_app_path(app)) / "public" / "css"
			except Exception:
				continue
			if not css_root.is_dir():
				continue
			for css_path in css_root.glob("*.css"):
				if css_path.name == "kt_industry_tokens.css":
					continue
				text = css_path.read_text(encoding="utf-8")
				if token_root_re.search(text) and ".kt-industry" not in text.split("{", 1)[0]:
					# A match inside a block that isn't itself scoped under
					# .kt-industry is a second token-root definition.
					for m in token_root_re.finditer(text):
						selector = text[: m.start()].rsplit("}", 1)[-1].strip().splitlines()[-1]
						if ".kt-industry" not in selector and ".kt-stitch" not in selector and ".kt-cl" not in selector:
							violations.append(f"{css_path}: {selector!r}")
		self.assertEqual(
			violations,
			[],
			"found a competing design-system token root outside kt_industry_tokens.css / "
			"the pre-existing Stitch Desk (.kt-stitch*) / Civic Ledger (.kt-cl*) systems "
			"already carved out of this rule by the plan's explicit out-of-scope list: "
			+ "; ".join(violations),
		)
