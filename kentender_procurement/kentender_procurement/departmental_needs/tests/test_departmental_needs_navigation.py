"""Phase 8 shell and navigation tests for NDS-CHG-001 v1.1 §10.

§10 fixes three things this module has to get right outside its own code:

1. Departmental Needs is a top-level module placed **after** Budget & Funding
   and **before** Procurement Planning in the business-flow rail.
2. Its module menu contains exactly three entries — Departmental Needs, Review
   tasks (effective Head of User Department only) and Intake window (effective
   Procurement Planner only) — and nothing else.
3. Every entry targets one of the eight canonical §10 routes. No legacy
   NDS-CHG-002 route survives anywhere in the navigation surface (NDS-AC-030,
   NDS-BR-020).

The menu's ``display_depends_on`` is evaluated **client-side** by
``frappe.utils.eval`` in Frappe's own ``sidebar.js`` (``create_sidebar``). It
decides what a user is shown, never what a user may do — §17 forbids inferring
authority from a route, tab or role label. ``test_hidden_row_is_not_the_control``
proves the server still refuses the command behind a hidden row.
"""

from __future__ import annotations

import json
import os
import re

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.constants import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
)
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	FY,
	PE,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.context import save_intake_window

SIDEBAR_EXPORT = ("kentender_procurement", "workspace_sidebar", "procurement.json")
REGISTRY = ("kentender_core", "public", "js", "kt_cl_surface_registry.js")

# §10 — the module menu, in order. Each row is (label, link_type, target, role).
# ``role`` is None where the entry is visible to every user who can reach the
# module at all; the workspace itself resolves its own audience server-side.
MENU: tuple[tuple[str, str, str, str | None], ...] = (
	("Departmental Needs", "Page", "departmental-needs", None),
	("Review tasks", "URL", "/desk/departmental-needs/review", ROLE_HEAD_OF_USER_DEPARTMENT),
	("Intake window", "URL", "/desk/departmental-needs/intake-window", ROLE_PROCUREMENT_PLANNER),
)

# Every retired route this module replaced, named in full. §1.1 removes them
# with no alias, redirect or fallback.
#
# The four departmental-needs-* prefixes are the NDS-CHG-002 Civic Ledger
# screens deleted in Phase 7. The five demand* prefixes are the Demand module
# Departmental Needs supersedes (NDS-BR-020). Enumerating the family matters:
# an earlier version of this list carried the single stem "demands", which a
# reintroduced "demand-form" registration passed straight through.
LEGACY_ROUTES = (
	"departmental-needs-new",
	"departmental-needs-edit",
	"departmental-needs-review",
	"departmental-needs-detail",
	"demands-workspace",
	"demand-form",
	"demand-review",
	"demand-detail",
	"demand-performance",
)


def _app_file(*parts: str) -> str:
	head, *tail = parts
	return os.path.join(frappe.get_app_path(head), *tail)


def route_prefixes(source: str) -> list[str]:
	"""Every route prefix the Civic Ledger registry claims, in order."""
	groups = re.findall(r"routePrefixes:\s*\[([^\]]*)\]", source)
	return [p.strip().strip("\"'") for g in groups for p in g.split(",") if p.strip()]


def strip_js_comments(source: str) -> str:
	"""Return *source* with // and /* */ comments blanked, strings preserved.

	A scan that reads raw source fires on the prose that documents the rule —
	the registry's own comment has to name the retired routes to explain why
	they were removed. Blanking rather than deleting keeps offsets stable, so a
	failure message still points at a usable line.
	"""
	out: list[str] = []
	i, n = 0, len(source)
	quote: str | None = None
	while i < n:
		ch = source[i]
		if quote:
			out.append(ch)
			if ch == "\\" and i + 1 < n:
				out.append(source[i + 1])
				i += 2
				continue
			if ch == quote:
				quote = None
			i += 1
			continue
		if ch in "\"'`":
			quote = ch
			out.append(ch)
			i += 1
			continue
		if ch == "/" and i + 1 < n and source[i + 1] == "/":
			while i < n and source[i] != "\n":
				out.append(" ")
				i += 1
			continue
		if ch == "/" and i + 1 < n and source[i + 1] == "*":
			end = source.find("*/", i + 2)
			end = n if end == -1 else end + 2
			out.append("".join(" " if c != "\n" else "\n" for c in source[i:end]))
			i = end
			continue
		out.append(ch)
		i += 1
	return "".join(out)


def _sidebar_rows() -> list[dict]:
	with open(_app_file(*SIDEBAR_EXPORT), encoding="utf-8") as f:
		return json.load(f).get("items") or []


class DepartmentalNeedsMenuTest(IntegrationTestCase):
	"""§10 module menu: composition, order, targets and role visibility."""

	def setUp(self):
		super().setUp()
		self.rows = _sidebar_rows()
		self.labels = [row.get("label") or "" for row in self.rows]

	def test_menu_is_exactly_the_three_entries(self):
		"""§10: 'Its module menu contains only' these three."""
		ours = [
			row
			for row in self.rows
			if "departmental-needs" in (row.get("url") or "")
			or row.get("link_to") == "departmental-needs"
		]
		self.assertEqual(
			[row.get("label") for row in ours],
			[label for label, _, _, _ in MENU],
			msg="§10 fixes the Departmental Needs module menu at exactly three entries",
		)

	def test_menu_entries_are_contiguous_and_in_order(self):
		"""The two flow entries sit together; the configuration entry does not.

		§10 lists the three entries together, but the rail groups every
		configuration surface under "Configuration and Governance" — and Frappe
		nests one level only (Sidebar.find_nested_items), so that group cannot
		hold a Departmental Needs sub-group. NDS-UI-08 is therefore a child of
		that section, away from the two business-flow rows.
		"""
		flow = [label for label, _, _, _ in MENU if label != "Intake window"]
		start = self.labels.index("Departmental Needs")
		self.assertEqual(
			tuple(self.labels[start : start + len(flow)]),
			tuple(flow),
			msg="The §10 flow entries must sit together, workspace first",
		)

	def test_intake_window_is_a_configuration_and_governance_child(self):
		"""NDS-UI-08 is configuration, so it lives in the configuration group."""
		section = self.labels.index("Configuration and Governance")
		self.assertEqual(self.rows[section].get("type"), "Section Break")
		intake = self.labels.index("Intake window")
		self.assertGreater(intake, section)
		self.assertEqual(int(self.rows[intake].get("child") or 0), 1)
		# No Section Break may intervene, or the row belongs to another group.
		between = [
			row.get("label")
			for row in self.rows[section + 1 : intake]
			if row.get("type") == "Section Break"
		]
		self.assertEqual(between, [])

	def test_module_sits_after_budget_and_before_planning(self):
		"""§10 placement in the business-flow rail."""
		budget = self.labels.index("Budget & Funding")
		needs = self.labels.index("Departmental Needs")
		planning = self.labels.index("Procurement Plans")
		self.assertLess(budget, needs, msg="Departmental Needs follows Budget & Funding")
		self.assertLess(needs, planning, msg="Departmental Needs precedes Procurement Planning")

	def test_each_entry_targets_its_canonical_route(self):
		by_label = {row.get("label"): row for row in self.rows}
		for label, link_type, target, _role in MENU:
			with self.subTest(label=label):
				row = by_label[label]
				self.assertEqual(row.get("link_type"), link_type)
				# The two sub-routes are segments of the same Page, so they are
				# URL links. Frappe's router only intercepts a same-host link
				# whose first path segment is "desk" (router.js is_app_route),
				# so an /app/ href would force a full page load instead of SPA
				# navigation — hence /desk/, matching every sibling module.
				actual = row.get("url") if link_type == "URL" else row.get("link_to")
				self.assertEqual(actual, target)

	def test_role_visibility_matches_section_10(self):
		by_label = {row.get("label"): row for row in self.rows}
		for label, _link_type, _target, role in MENU:
			with self.subTest(label=label):
				condition = by_label[label].get("display_depends_on") or ""
				if role is None:
					self.assertEqual(
						condition,
						"",
						msg="The module entry itself is not role-gated in the menu",
					)
					continue
				self.assertIn(role, condition)
				self.assertIn("frappe.user_roles", condition)
				# Exactly one role — §10 names one audience per entry, and a
				# second name here would silently widen who is shown the link.
				named = [
					r
					for r in (
						ROLE_DEPARTMENTAL_AUTHOR,
						ROLE_HEAD_OF_USER_DEPARTMENT,
						ROLE_PROCUREMENT_PLANNER,
					)
					if r in condition
				]
				self.assertEqual(named, [role])

	def test_boot_sidebar_preserves_url_and_visibility(self):
		"""The row is useless if boot drops either field.

		``_build_sidebar_dict`` copies an explicit field list, so a URL link
		without ``url``, or a gated link without ``display_depends_on``, would
		reach the browser as a dead or universally-visible row.
		"""
		if not frappe.db.exists("Workspace Sidebar", "Procurement"):
			self.skipTest("Procurement Workspace Sidebar not on site")
		from kentender_procurement.setup.workspace_permissions import patch_bootinfo

		bootinfo: dict = {"workspace_sidebar_item": {}}
		patch_bootinfo(bootinfo)
		items = (bootinfo["workspace_sidebar_item"].get("procurement") or {}).get("items") or []
		by_label = {row.get("label"): row for row in items}
		for label, link_type, target, role in MENU:
			with self.subTest(label=label):
				self.assertIn(label, by_label, msg="row must survive the boot rebuild")
				row = by_label[label]
				if link_type == "URL":
					self.assertEqual(row.get("url"), target)
				if role:
					self.assertIn(role, row.get("display_depends_on") or "")


class DepartmentalNeedsSurfaceRegistryTest(IntegrationTestCase):
	"""NDS-801 — the Industry page must stay out of the Civic Ledger registry."""

	def setUp(self):
		super().setUp()
		with open(_app_file(*REGISTRY), encoding="utf-8") as f:
			self.registry_src = strip_js_comments(f.read())

	def test_registry_claims_no_departmental_needs_route(self):
		"""A registered prefix lets kt_cl_shell_router force Civic Ledger chrome.

		The router listens to frappe.router "change" globally and re-renders the
		matched surface's toolbar into #kt-cl-chrome-host on every route settle
		— including the in-page segment navigation this module does for all
		eight NDS-UI routes, i.e. after the page has cleared that host once.
		"""
		offenders = [p for p in route_prefixes(self.registry_src) if p.startswith("departmental-need")]
		self.assertEqual(
			offenders,
			[],
			msg="Departmental Needs is an Industry surface — see the comment in the registry",
		)

	def test_the_scan_is_not_vacuous(self):
		"""Blanking comments must not blank code.

		The registry's own comment names the retired routes to explain why they
		went, so a raw-text scan fires on its own documentation. Stripping
		comments fixes that and immediately raises the opposite risk — a
		stripper that eats too much would pass no matter what the file
		contains. This drives a synthetic registry that both documents *and*
		commits the violation through the same helpers.
		"""
		synthetic = strip_js_comments(
			"/* departmental-needs-new was retired; never register it again. */\n"
			'"NDS-UI-01": { routePrefixes: ["departmental-needs"] },\n'
			'"NDS-UI-02A": { routePrefixes: ["departmental-needs-new"] },\n'
		)
		self.assertNotIn("retired", synthetic, msg="comment text must be blanked")
		self.assertEqual(
			route_prefixes(synthetic),
			["departmental-needs", "departmental-needs-new"],
			msg="code outside comments must survive stripping",
		)
		self.assertIn("departmental-needs-new", synthetic, msg="the legacy scan must still see code")
		# The registry, sanitised the same way, still parses as real content —
		# proof the stripper did not simply empty the file.
		self.assertGreater(len(route_prefixes(self.registry_src)), 10)

	def test_no_legacy_route_survives_in_navigation(self):
		"""NDS-AC-030 / NDS-BR-020 — no alias, redirect or stale menu target."""
		rows = _sidebar_rows()
		targets = [
			f"{row.get('link_to') or ''} {row.get('url') or ''}" for row in rows
		]
		for legacy in LEGACY_ROUTES:
			with self.subTest(route=legacy):
				self.assertNotIn(
					legacy,
					self.registry_src,
					msg=f"{legacy} is a retired NDS-CHG-002 route",
				)
				hits = [t for t in targets if re.search(rf"(^|[/ ]){re.escape(legacy)}($|[/ ])", t)]
				self.assertEqual(hits, [], msg=f"{legacy} still targeted from the rail")

	def test_page_is_registered_once_with_its_own_controller(self):
		"""NDS-803 — one Page, one page_js, no leftover Page records."""
		from kentender_procurement import hooks

		pages = frappe.get_all(
			"Page",
			filters={"name": ("like", "departmental-needs%")},
			pluck="name",
		)
		self.assertEqual(sorted(pages), ["departmental-needs"])
		nds_page_js = {
			route: path
			for route, path in (hooks.page_js or {}).items()
			if "departmental" in route
		}
		self.assertEqual(
			nds_page_js,
			{"departmental-needs": "public/js/departmental_needs_page.js"},
		)


class DepartmentalNeedsMenuIsNotAuthorizationTest(IntegrationTestCase):
	"""§17 — a hidden menu row is presentation; the server is the control."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	def test_hidden_row_is_not_the_control(self):
		"""An author does not see Intake window — and cannot save one either.

		``display_depends_on`` runs in the browser and is trivially bypassed by
		typing the route. The refusal below is the actual control.
		"""
		condition = next(
			row.get("display_depends_on") or ""
			for row in _sidebar_rows()
			if row.get("label") == "Intake window"
		)
		self.assertNotIn(ROLE_DEPARTMENTAL_AUTHOR, condition)

		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as raised:
			save_intake_window(
				procuring_entity=PE,
				financial_year=FY,
				opens_at="2026-09-01 00:00:00",
				closes_at="2026-09-30 23:59:59",
			)
		# §9 defines NDS_SCOPE_DENIED as "actor lacks the exact current Frappe
		# role and User Permission scope" — a missing role is that code, not a
		# separate one; the closed fifteen-code set has no NDS_NOT_AUTHORIZED.
		self.assertEqual(raised.exception.code, "NDS_SCOPE_DENIED")
		self.assertIn(ROLE_PROCUREMENT_PLANNER, str(raised.exception))


class DepartmentalNeedsPageRolesTest(IntegrationTestCase):
	"""§6/§10 — one Page carries all eight routes, so one role list serves them.

	The pre-v1.1 build had a Page per screen and could give each its own roles.
	§10 collapses them into `departmental-needs`, so that Page's role list must
	be the union of everyone §6 admits to *any* NDS surface — otherwise a role
	is locked out of the whole module to protect one route it should not see.

	The Procurement Planner is the case that proves it: NDS-AC-043 gives them
	the intake window, §10 gives them its menu entry, and both are meaningless
	if they cannot open the Page the route lives on.

	Per-route authority stays where §17 requires it — on the server. The
	Planner reaching the Page does not let them read a Draft Need or decide
	anything; `can_view` gives them accepted sources only, and every command
	re-checks its own role.
	"""

	def page_roles(self) -> set[str]:
		return {row.role for row in frappe.get_doc("Page", "departmental-needs").roles}

	def test_every_section_6_business_role_may_open_the_page(self):
		for role in (
			ROLE_DEPARTMENTAL_AUTHOR,
			ROLE_HEAD_OF_USER_DEPARTMENT,
			ROLE_PROCUREMENT_PLANNER,
			"Auditor",
		):
			with self.subTest(role=role):
				self.assertIn(role, self.page_roles())

	def test_the_page_admits_no_role_section_1_1_removed(self):
		"""NDS-AC-023 — Budget Officer and Accounting Officer get no surface."""
		for role in ("Budget Officer", "Accounting Officer", "Departmental Review Delegate"):
			with self.subTest(role=role):
				self.assertNotIn(role, self.page_roles())

	def test_the_checked_in_fixture_matches_the_live_record(self):
		"""A fresh install must not reapply a different list.

		The Phase 3 patch corrected the live Page once; the fixture is what a
		new site reads, so the two drifting apart is invisible until someone
		installs from scratch.
		"""
		path = _app_file(
			"kentender_procurement",
			"departmental_needs",
			"page",
			"departmental_needs",
			"departmental_needs.json",
		)
		with open(path, encoding="utf-8") as handle:
			fixture = {row["role"] for row in json.load(handle).get("roles") or []}
		self.assertEqual(fixture, self.page_roles())

	def test_the_role_source_names_only_pages_that_exist(self):
		"""The generator still mapped five Pages Phase 7 deleted."""
		from kentender_procurement.setup.departmental_needs_page import PAGE_ROLES

		for page in PAGE_ROLES:
			with self.subTest(page=page):
				self.assertTrue(
					frappe.db.exists("Page", page),
					msg=f"{page} is reconciled but no longer exists",
				)
