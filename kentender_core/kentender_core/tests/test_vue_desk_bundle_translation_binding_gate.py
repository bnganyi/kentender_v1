# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contracts for Vue-in-Desk bundle entry points (AGENTS.md §6.1/§6.6).

1. Every bundle that mounts a component using __() in a <template> block must
   bind app.config.globalProperties.__ before app.mount(). Vue's SFC compiler
   resolves a template-level __("...") call to `_ctx.__(...)` — a
   component-instance property lookup, not window.__ — so without this
   binding the component crashes on first render with a blank content area.

2. No bundle.js may `import "*.css"` as a plain top-level statement.
   frappe.require("<slug>.bundle.js") only ever loads that one .js URL; a
   plain CSS import still compiles to a real file on disk but nothing ever
   links to it (it isn't an esbuild metafile entry point, so it gets no
   assets.json key and no <link> tag). The component mounts with no JS
   error and the stylesheet just silently never applies.

Both confirmed missing/broken in all three kentender_strategy Phase 7
bundles on 2026-08-24; this gate exists so both classes of bug fail `make`
instead of shipping to a browser.
"""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_TEMPLATE_BLOCK_RE = re.compile(r"<template>(.*?)</template>", re.DOTALL)
_TRANSLATION_CALL_RE = re.compile(r"(?<![\w.])__\s*\(")
_GLOBAL_PROPERTIES_BINDING_RE = re.compile(
	r"globalProperties\.__\s*=\s*window\.__"
)
_TOP_LEVEL_CSS_IMPORT_RE = re.compile(r"^\s*import\s+[\"'][^\"']+\.css[\"'];?\s*$", re.MULTILINE)


def _kentender_apps_root() -> Path:
	# frappe.get_app_path("kentender_core") -> .../apps/kentender_v1/kentender_core/kentender_core
	return Path(frappe.get_app_path("kentender_core")).parent.parent


def _iter_bundle_entry_points(apps_root: Path) -> list[Path]:
	return sorted(apps_root.glob("kentender_*/kentender_*/public/js/**/*.bundle.js"))


def _vue_template_uses_translation_helper(vue_dir: Path) -> list[Path]:
	offenders: list[Path] = []
	for vue_file in vue_dir.rglob("*.vue"):
		source = vue_file.read_text(encoding="utf-8")
		for template_body in _TEMPLATE_BLOCK_RE.findall(source):
			if _TRANSLATION_CALL_RE.search(template_body):
				offenders.append(vue_file)
				break
	return offenders


class TestVueDeskBundleTranslationBindingGate(IntegrationTestCase):
	def test_every_bundle_using_template_translation_binds_global_properties(self) -> None:
		apps_root = _kentender_apps_root()
		bundle_entry_points = _iter_bundle_entry_points(apps_root)
		self.assertTrue(
			bundle_entry_points,
			msg=f"No *.bundle.js entry points found under {apps_root} — glob may be stale.",
		)

		failures: list[str] = []
		for bundle_path in bundle_entry_points:
			if "createApp(" not in bundle_path.read_text(encoding="utf-8"):
				continue

			offending_vue_files = _vue_template_uses_translation_helper(bundle_path.parent)
			if not offending_vue_files:
				continue

			bundle_source = bundle_path.read_text(encoding="utf-8")
			if not _GLOBAL_PROPERTIES_BINDING_RE.search(bundle_source):
				rel_bundle = bundle_path.relative_to(apps_root)
				rel_offenders = ", ".join(
					str(p.relative_to(apps_root)) for p in offending_vue_files
				)
				failures.append(
					f"{rel_bundle} mounts component(s) using __() in <template> "
					f"({rel_offenders}) but never binds "
					"app.config.globalProperties.__ = window.__ before app.mount(). "
					"See AGENTS.md §6.1."
				)

		self.assertFalse(failures, msg="\n".join(failures))

	def test_no_bundle_uses_a_plain_top_level_css_import(self) -> None:
		apps_root = _kentender_apps_root()
		bundle_entry_points = _iter_bundle_entry_points(apps_root)
		self.assertTrue(
			bundle_entry_points,
			msg=f"No *.bundle.js entry points found under {apps_root} — glob may be stale.",
		)

		failures: list[str] = []
		for bundle_path in bundle_entry_points:
			bundle_source = bundle_path.read_text(encoding="utf-8")
			if _TOP_LEVEL_CSS_IMPORT_RE.search(bundle_source):
				rel_bundle = bundle_path.relative_to(apps_root)
				failures.append(
					f"{rel_bundle} has a plain top-level `import \"*.css\"` statement. "
					"frappe.require() never loads a paired CSS output for a bundle.js "
					"entry point, so this compiles to an orphaned file nothing links to "
					"and every rule in it silently never applies. Load shared tokens as "
					"a static file via the owning app's hooks.py app_include_css instead "
					"(see kentender_core's kt_industry_tokens.css), or keep styling "
					"inside each .vue file's own <style scoped> block. See AGENTS.md §6.6."
				)

		self.assertFalse(failures, msg="\n".join(failures))
