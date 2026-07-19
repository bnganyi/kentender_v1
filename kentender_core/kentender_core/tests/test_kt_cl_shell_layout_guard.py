# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Layout guard for Civic Ledger desk shell + component library (kt-cl-*).

Verifies faithful port of B-Components/code.html into Frappe Desk:
- compiled, scoped Tailwind stylesheet (civic_ledger.css) wins over Bootstrap
  without leaking (no preflight, no unscoped container);
- every code.html block has a parity marker present in both the mock and the
  rendered implementation;
- the component library exports each reusable renderer;
- both desk surfaces (POC page + component gallery) are wired.
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase


def _core_public(*parts: str) -> Path:
	return Path(frappe.get_app_path("kentender_core")) / "public" / Path(*parts)


def _proc_public(*parts: str) -> Path:
	return Path(frappe.get_app_path("kentender_procurement")) / "public" / Path(*parts)


def _code_html_path() -> Path:
	repo_root = Path(frappe.get_app_path("kentender_core")).parent.parent
	return (
		repo_root
		/ "docs"
		/ "std-prod-impl"
		/ "IT-STD-Wizard-v3"
		/ "B-Components"
		/ "code.html"
	)


class TestKtClShellLayoutGuard(IntegrationTestCase):
	# ---- Asset wiring ---------------------------------------------------
	def test_cl_assets_registered_on_desk_hooks(self) -> None:
		css = frappe.get_hooks("app_include_css", app_name="kentender_core", default=[])
		js = frappe.get_hooks("app_include_js", app_name="kentender_core", default=[])
		flat_css = [item for row in css for item in (row if isinstance(row, (list, tuple)) else [row])]
		flat_js = [item for row in js for item in (row if isinstance(row, (list, tuple)) else [row])]
		for needle in ("kt_cl_fonts.css", "civic_ledger.css", "kt_cl_code_layout.css"):
			self.assertTrue(any(needle in str(path) for path in flat_css), f"{needle} missing from hooks")
		# The superseded hand-ported utilities file must be gone.
		self.assertFalse(
			any("kt_cl_code_utilities.css" in str(path) for path in flat_css),
			"kt_cl_code_utilities.css must be replaced by civic_ledger.css",
		)
		for needle in (
			"kt_cl_code_spec.js",
			"kt_cl_components.js",
			"kt_cl_sidebar.js",
			"kt_cl_shell.js",
			"kt_cl_surface_registry.js",
			"kt_cl_shell_router.js",
		):
			self.assertTrue(any(needle in str(path) for path in flat_js), f"{needle} missing from hooks")

	def test_code_html_source_exists(self) -> None:
		self.assertTrue(_code_html_path().is_file(), f"Missing design source: {_code_html_path()}")

	def test_utilities_file_removed(self) -> None:
		self.assertFalse(
			_core_public("css", "kt_cl_code_utilities.css").exists(),
			"kt_cl_code_utilities.css should be deleted in favour of compiled civic_ledger.css",
		)

	# ---- Compiled CSS: scoping + tokens + no leaks ----------------------
	def test_civic_ledger_css_is_scoped_and_has_primary_token(self) -> None:
		text = _core_public("css", "civic_ledger.css").read_text(encoding="utf-8")
		self.assertTrue(text.strip(), "civic_ledger.css is empty — recompile via tools/civic-ledger-css")
		# Utilities are scoped under .kt-cl-shell so they win over Bootstrap.
		self.assertIn(".kt-cl-shell .text-primary", text)
		# primary #000b1d compiles to rgb(0 11 29).
		self.assertIn("rgb(0 11 29", text)

	def test_civic_ledger_css_has_no_preflight_or_leaks(self) -> None:
		text = _core_public("css", "civic_ledger.css").read_text(encoding="utf-8")
		# preflight disabled: no global universal reset.
		self.assertNotIn("*,::before,::after", text)
		self.assertNotIn("-webkit-text-size-adjust", text)
		# container plugin disabled: no unscoped `.container` rule that would
		# leak into Frappe's Bootstrap layout.
		self.assertNotIn(".container{", text)

	# ---- Parity markers for every code.html block -----------------------
	def test_code_html_parity_markers_in_implementation(self) -> None:
		code_html = _code_html_path().read_text(encoding="utf-8")
		spec = _core_public("js", "kt_cl_code_spec.js").read_text(encoding="utf-8")
		components = _core_public("js", "kt_cl_components.js").read_text(encoding="utf-8")
		sidebar = _core_public("js", "kt_cl_sidebar.js").read_text(encoding="utf-8")
		haystack = spec + components + sidebar

		markers = [
			# sidebar
			"fixed left-0 top-0 h-screen z-50 hidden md:flex flex-col w-64 bg-surface-container-low",
			"bg-primary-fixed-dim/20",
			# NOTE: the child (sub-item) block intentionally diverges from the raw
			# code.html utilities — it is refined via semantic classes + CSS. Its
			# contract is asserted by test_two_level_children_are_refined below.
			# top bar
			"sticky top-0 z-40 flex justify-between items-center px-4 w-full",
			"pl-8 pr-3 py-1 border border-outline-variant rounded-full bg-surface-container-lowest",
			# page header buttons
			"px-3 py-1.5 rounded border border-primary text-primary",
			"px-3 py-1.5 rounded bg-primary text-on-primary",
			# bento grid
			"grid grid-cols-1 md:grid-cols-12 gap-4",
			"md:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-4",
			# KPI metric card (emerald) + progress card (blue)
			"bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-900/20 dark:to-surface border border-emerald-200",
			"bg-gradient-to-br from-amber-50 to-white dark:from-amber-900/20 dark:to-surface border border-amber-200",
			"bg-gradient-to-br from-blue-50 to-white dark:from-blue-900/20 dark:to-surface border border-blue-200",
			"bg-blue-600 h-full rounded-full shadow-sm",
			# calendar widget
			"md:col-span-4 bg-surface-container-lowest border border-outline-variant rounded-lg p-3 flex flex-col hover:shadow-[0px_2px_8px_rgba(0,0,0,0.05)]",
			"flex flex-col items-center justify-center bg-primary-container/10 text-primary-container rounded p-1 min-w-[36px]",
			"flex-1 overflow-y-auto space-y-1 pr-1 max-h-[140px]",
			# data table
			"w-full min-w-[800px] text-left border-collapse",
			"divide-y divide-outline-variant/50",
			"bg-surface-bright/50 hover:bg-surface-container-lowest transition-colors group",
			"p-2 border-t border-outline-variant flex justify-between items-center bg-surface-bright/50 rounded-b-lg",
			# status chips
			"inline-flex items-center px-1.5 py-0.5 rounded-sm",
			"bg-primary-fixed/20 text-on-primary-fixed-variant",
			"bg-secondary-fixed/30 text-on-secondary-fixed-variant",
			"bg-error-container/30 text-on-error-container",
		]
		for marker in markers:
			self.assertIn(marker, code_html, f"code.html missing marker: {marker}")
			self.assertIn(marker, haystack, f"Implementation missing code.html marker: {marker}")

	# ---- Fonts ----------------------------------------------------------
	def test_public_sans_font_files_exist(self) -> None:
		font_dir = _core_public("fonts", "public-sans")
		for name in (
			"public-sans-400-latin.woff2",
			"public-sans-500-latin.woff2",
			"public-sans-600-latin.woff2",
			"public-sans-700-latin.woff2",
		):
			self.assertTrue((font_dir / name).is_file(), f"Missing font file: {font_dir / name}")

	def test_material_symbols_font_exists(self) -> None:
		path = _core_public("fonts", "material-symbols", "material-symbols-outlined.woff2")
		self.assertTrue(path.is_file(), f"Missing font file: {path}")

	def test_jetbrains_mono_font_exists(self) -> None:
		path = _core_public("fonts", "jetbrains-mono", "jetbrains-mono-400-latin.woff2")
		self.assertTrue(path.is_file(), f"Missing font file: {path}")

	# ---- Frappe integration overrides -----------------------------------
	def test_layout_hides_frappe_sidebar_when_shell_active(self) -> None:
		"""Full-replacement POC mode hides the native sidebar; native mode keeps it."""
		layout = _core_public("css", "kt_cl_code_layout.css").read_text(encoding="utf-8")
		self.assertIn("body.kt-cl-shell:not(.kt-cl-shell-native) .body-sidebar-container", layout)
		self.assertIn("body.kt-cl-shell .navbar", layout)
		self.assertIn("body.kt-cl-shell .page-head", layout)

	def test_native_shell_mode_keeps_sidebar_hides_top_chrome(self) -> None:
		"""Step 2: kt-cl-shell-native must not hide .body-sidebar-container."""
		layout = _core_public("css", "kt_cl_code_layout.css").read_text(encoding="utf-8")
		self.assertIn("kt-cl-shell-native", layout)
		self.assertIn("#kt-cl-chrome-host", layout)
		# Native mode must never list body-sidebar-container in a hide rule without :not.
		self.assertNotIn(
			"body.kt-cl-shell-native .body-sidebar-container",
			layout,
			"native mode must not hide the Workspace Sidebar",
		)

	# ---- Component library exports --------------------------------------
	def test_components_js_exports_full_library(self) -> None:
		source = _core_public("js", "kt_cl_components.js").read_text(encoding="utf-8")
		for fn in (
			"renderTopToolbar",
			"renderBreadcrumbs",
			"renderPageHeader",
			"renderPageTitle",
			"kpiCard",
			"calendarWidget",
			"dataTable",
			"statusChip",
			"bentoGrid",
			"metricsGrid",
			"queueSummaryCard",
			"queueSummaryGrid",
			"tabBar",
			"filterBar",
			"queueTable",
			"createTenderConfigurationModal",
			"confirmDialog",
			"showConfirm",
		):
			self.assertIn(fn, source, f"component library missing {fn}")
		# Library aliases + aggregator namespace.
		for alias in (
			"C.topBar",
			"C.breadcrumbs",
			"C.button",
			"C.pageTitle",
			"kentender_core.cl.components",
			"kentender_core.cl.confirm",
		):
			self.assertIn(alias, source, f"missing library alias/namespace: {alias}")
		spec = _core_public("js", "kt_cl_code_spec.js").read_text(encoding="utf-8")
		self.assertIn("PAGE_TITLE", spec)
		self.assertIn("QUEUE", spec)

	def test_sidebar_js_is_config_driven(self) -> None:
		source = _core_public("js", "kt_cl_sidebar.js").read_text(encoding="utf-8")
		self.assertIn('data-testid="kt-cl-sidenav"', source)
		self.assertIn("KenTender", source)
		self.assertIn("renderNavGroup", source)
		self.assertIn("cl-nested-hidden", source)
		# Curated config, not boot-derived workspace items.
		self.assertNotIn("frappe.boot.workspace_sidebar_item", source)

	def test_two_level_children_are_refined(self) -> None:
		"""The collapsible group's children render via semantic classes and a
		dedicated CSS contract (connector line + indentation + hover/active),
		so the two-level structure reads clearly rather than as flat links."""
		spec = _core_public("js", "kt_cl_code_spec.js").read_text(encoding="utf-8")
		sidebar = _core_public("js", "kt_cl_sidebar.js").read_text(encoding="utf-8")
		css = _core_public("css", "kt_cl_code_layout.css").read_text(encoding="utf-8")

		# Semantic class hooks are the single source of truth (spec) and are used
		# by the renderer for both the list and the child links (+ active state).
		self.assertIn('NAV_CHILDREN_LIST = "kt-cl-nav-children"', spec)
		self.assertIn('NAV_CHILD = "kt-cl-nav-child"', spec)
		self.assertIn("is-active", spec)
		self.assertIn("spec().NAV_CHILDREN_LIST", sidebar)
		self.assertIn("NAV_CHILD_ACTIVE", sidebar)

		# CSS contract: the children container draws the tree connector line and
		# indents from the parent icon; child links get hover + active emphasis.
		# All scoped to the shell.
		self.assertIn(".kt-cl-shell .kt-cl-nav-children", css)
		self.assertIn("border-left: 1px solid #c4c6cf", css)
		self.assertIn(".kt-cl-shell .kt-cl-nav-children .kt-cl-nav-child:hover", css)
		self.assertIn(".kt-cl-shell .kt-cl-nav-children .kt-cl-nav-child.is-active", css)

		# Root/rail anchors must not render Frappe's global link underline — the
		# mock uses a surface highlight, not a link decoration.
		self.assertIn(".kt-cl-shell #kt-cl-sidenav a", css)
		self.assertIn("text-decoration: none !important", css)

	def test_shell_js_lifecycle_hooks(self) -> None:
		source = _core_public("js", "kt_cl_shell.js").read_text(encoding="utf-8")
		for fn in (
			"enter:",
			"leave:",
			"mountPageChrome:",
			"enterNative:",
			"leaveNative:",
			"updateChrome:",
			"mountContent:",
		):
			self.assertIn(fn, source)

	def test_surface_registry_exports_ui00(self) -> None:
		source = _core_public("js", "kt_cl_surface_registry.js").read_text(encoding="utf-8")
		self.assertIn('"UI-00"', source)
		self.assertIn("it-tender-configuration-dashboard", source)
		self.assertIn("resolveFromRoute", source)
		self.assertIn("sidebarWorkspaceKey", source)

	def test_shell_router_is_wired(self) -> None:
		source = _core_public("js", "kt_cl_shell_router.js").read_text(encoding="utf-8")
		self.assertIn('frappe.router.on("change"', source)
		self.assertIn("enterNative", source)
		self.assertIn("leaveNative", source)

	# ---- Desk wiring: POC page + gallery + permanent redirect ------------
	def test_poc_page_is_wired(self) -> None:
		page_js = frappe.get_hooks("page_js", app_name="kentender_procurement", default={})
		self.assertIn("kt-cl-shell-poc", page_js)
		source = _proc_public("js", "kt_cl_shell_poc_page.js").read_text(encoding="utf-8")
		# Composes from the component library, not hand-rolled markup.
		for call in ("comp.kpiCard", "comp.calendarWidget", "comp.dataTable", "civicLedgerIA"):
			self.assertIn(call, source, f"POC page not composing via {call}")

	def test_gallery_page_is_wired(self) -> None:
		page_js = frappe.get_hooks("page_js", app_name="kentender_core", default={})
		self.assertIn("kt-cl-components", page_js)
		page_json = (
			Path(frappe.get_app_path("kentender_core"))
			/ "kentender_core"
			/ "page"
			/ "kt_cl_components"
			/ "kt_cl_components.json"
		)
		self.assertTrue(page_json.is_file(), f"Missing gallery page fixture: {page_json}")

	def test_procurement_home_redirect_is_retired(self) -> None:
		"""Step 1 (restore + restyle native menu): the custom rail is no longer
		navigation. The Procurement Home → POC redirect (kt_cl_routes.js) must NOT
		be registered, so Procurement Home renders its native Workspace + the
		restyled native `.body-sidebar` rail."""
		js = frappe.get_hooks("app_include_js", app_name="kentender_procurement", default=[])
		flat_js = [item for row in js for item in (row if isinstance(row, (list, tuple)) else [row])]
		self.assertFalse(
			any("kt_cl_routes.js" in str(path) for path in flat_js),
			"kt_cl_routes.js redirect must be retired so Procurement Home uses the native sidebar",
		)

	def test_native_sidebar_restyle_is_wired(self) -> None:
		"""The scoped native-sidebar restyle stylesheet must ship globally so the
		native `.body-sidebar` carries the Civic Ledger tokens app-wide."""
		css_hooks = frappe.get_hooks("app_include_css", app_name="kentender_core", default=[])
		flat_css = [item for row in css_hooks for item in (row if isinstance(row, (list, tuple)) else [row])]
		self.assertTrue(
			any("kt_native_sidebar_civic.css" in str(path) for path in flat_css),
			"kt_native_sidebar_civic.css must be registered in kentender_core app_include_css",
		)
		css = _core_public("css", "kt_native_sidebar_civic.css").read_text(encoding="utf-8")
		self.assertIn(".body-sidebar", css)
		self.assertIn(".active-sidebar", css)
		self.assertIn("--sidebar-width: 256px", css)
		self.assertIn("Material Symbols Outlined", css)

	def test_rail_collapse_to_icons_is_wired(self) -> None:
		"""Whole-rail collapse (native Desk pattern): a bottom toggle shrinks the
		rail to an icon-only mini nav, persisted in localStorage, with labels
		hidden and the canvas offset following the collapsed width."""
		sidebar = _core_public("js", "kt_cl_sidebar.js").read_text(encoding="utf-8")
		css = _core_public("css", "kt_cl_code_layout.css").read_text(encoding="utf-8")

		# Toggle control + persistence + state helpers.
		self.assertIn("data-kt-cl-collapse", sidebar)
		self.assertIn('data-testid="kt-cl-collapse-toggle"', sidebar)
		self.assertIn("left_panel_close", sidebar)
		self.assertIn("left_panel_open", sidebar)
		self.assertIn("kt-cl-rail-collapsed", sidebar)
		self.assertIn("setRailCollapsed", sidebar)
		self.assertIn("localStorage", sidebar)
		# Labels are class-tagged so the collapsed rail can hide them.
		self.assertIn("kt-cl-label", sidebar)

		# CSS contract: collapsed width, hidden labels, canvas offset, transition.
		self.assertIn("body.kt-cl-shell.kt-cl-rail-collapsed .kt-cl-sidenav", css)
		self.assertIn("width: 64px !important", css)
		self.assertIn("margin-left: 64px", css)
		self.assertIn("transition: width 0.3s", css)
		self.assertIn(".kt-cl-label", css)
