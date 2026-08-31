"""NDS-910 — the firm D1 module boundary, enforced in both directions.

Project Owner decision (2026-08-29): Departmental Needs and Procurement
Planning stay separate modules inside `kentender_procurement`. Planning
consumes Accepted Needs **only** through the published handoff contract. Direct
access to Departmental Needs DocTypes, tables or internal services is
prohibited, and the prohibition is enforced by automated architecture tests
rather than by convention.

This module replaces the two-file guard written in Phase 5
(`test_departmental_needs_events.TestPlanningBoundary`), which checked only the
two Planning files that were being rewritten at the time and only the
Planning → Needs direction. The decision names both directions, and a boundary
that is only checked where it was last broken is not enforced — the next
violation lands in one of the other hundred files.

Why an AST walk rather than a text scan, in both directions: these modules
*document* the boundary in their docstrings, so a plain substring scan fires on
the prose that forbids the thing. Stripping string literals to fix that would
also blank `frappe.get_all("Departmental Need", …)` — precisely the call the
test exists to catch. So the scan looks at what is actually called, and treats
string constants as evidence only for raw SQL naming a table.

`test_the_guard_catches_a_real_violation` proves the walk is not vacuous by
running it over synthetic source that commits every violation it claims to
detect.
"""

from __future__ import annotations

import ast
import pathlib

from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.services import lifecycle

MODULE_ROOT = pathlib.Path(lifecycle.__file__).parents[2]
NEEDS = "departmental_needs"
PLANNING = "procurement_planning"

# Frappe data access whose first positional argument names a DocType.
ACCESSORS = frozenset(
	{
		"get_all",
		"get_list",
		"get_doc",
		"new_doc",
		"get_value",
		"set_value",
		"get_single_value",
		"exists",
		"count",
		"delete",
		"delete_doc",
		"get_cached_doc",
		"get_cached_value",
		"rename_doc",
	}
)

NEEDS_DOCTYPES = frozenset(
	{
		"Departmental Need",
		"Departmental Need Version",
		"Departmental Need Decision",
		"Departmental Need Review Task",
		"Departmental Need Event",
		"Need Withdrawal Request",
		"Needs Intake Window",
		"Need Planning Usage Projection",
	}
)

PLANNING_DOCTYPES = frozenset(
	{
		# PLN-CHG-001 v1.2 model (the Demand-era doctypes were dropped in its
		# Phase 1); Needs still consumes nothing of Planning's directly.
		"Departmental Plan",
		"Departmental Plan Version",
		"Departmental Plan Entry",
		"Departmental Plan Submission",
		"Departmental Plan Submission Window",
		"Departmental Plan Validation Task",
		"Departmental Plan Validation Decision",
		"Annual Plan",
		"Annual Plan Version",
		"Annual Plan Item",
		"Plan Source Allocation",
		"Plan Finance Task",
		"Plan Finance Decision",
		"Plan Reservation Reference",
		"Plan Governance Task",
		"Plan Governance Decision",
		"Annual Plan Publication",
		"Planning Command Journal",
	}
)

# §8.1/§7.1 — the published handoff contract, and the only Needs modules
# Planning may import. `events` replays DepartmentalNeedAccepted.v2; `workspace`
# exposes get_current_accepted_need, which refuses a stale or unaccepted source.
PUBLISHED_TO_PLANNING = frozenset(
	{
		f"kentender_procurement.{NEEDS}.services.events",
		f"kentender_procurement.{NEEDS}.services.workspace",
		# The typed error the published reads raise (NDS_NOT_ACCEPTED,
		# NDS_SOURCE_STALE, …): a consumer cannot catch a contract's refusal
		# without its exception type, so the errors module is part of the
		# published surface (added for PLN-CHG-001 v1.2 Phase 2).
		f"kentender_procurement.{NEEDS}.errors",
		# The outbound half of the same handoff (§7.1/§4.7): Planning
		# publishes NeedPlanningUsageChanged.v1 by calling
		# `usage.project_planning_usage` directly (its own module docstring,
		# and the PUBLISHED_TO_NEEDS comment below, already describe this as
		# the intended direction) — added when Phase 9 built the first real
		# publisher, closing a gap this guard's own allow-list had left open
		# since Phase 2 only wired the read side.
		f"kentender_procurement.{NEEDS}.services.usage",
	}
)

# Needs publishes to Planning; it consumes nothing back. Planning calls into
# `usage.project_planning_usage` rather than Needs reading Planning's tables,
# so the permitted set in this direction is empty by design.
PUBLISHED_TO_NEEDS: frozenset[str] = frozenset()

# Procurement Home renders the cross-module dashboard, so it consumes Needs too.
# It was outside this guard until its pipeline was rewired (the two Demand-era
# stages returned a hard-coded 0 and linked to a deleted route), which made the
# boundary accidental there rather than enforced: nothing would have caught
# Procurement Home querying `tabDepartmental Need` directly. `usage` is allowed
# alongside `events` because the §4.7 planning-usage projection is the published
# way to ask whether an Active Plan already represents an accepted version.
HOME = "procurement_home"
PUBLISHED_TO_HOME = frozenset(
	{
		f"kentender_procurement.{NEEDS}.constants",
		f"kentender_procurement.{NEEDS}.services.events",
		f"kentender_procurement.{NEEDS}.services.usage",
		f"kentender_procurement.{NEEDS}.services.workspace",
	}
)


def _sources(package: str) -> list[tuple[str, str]]:
	"""Every non-test module in *package*, as (relative path, source).

	Tests are excluded: they legitimately name both modules' doctypes, and this
	file is itself the clearest example.
	"""
	out = []
	for path in sorted((MODULE_ROOT / package).rglob("*.py")):
		parts = path.parts
		if "tests" in parts or "__pycache__" in parts:
			continue
		out.append((str(path.relative_to(MODULE_ROOT)), path.read_text()))
	return out


def data_access_violations(source: str, doctypes: frozenset[str]) -> list[str]:
	"""Frappe calls naming a foreign DocType, plus raw SQL on its table."""
	found: list[str] = []
	tree = ast.parse(source)
	for node in ast.walk(tree):
		if not isinstance(node, ast.Call):
			continue
		func = node.func
		name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
		first = node.args[0] if node.args else None
		value = first.value if isinstance(first, ast.Constant) else None
		if name in ACCESSORS and value in doctypes:
			found.append(f"{name}({value!r})")
		if name == "sql" and isinstance(value, str):
			for doctype in doctypes:
				if f"tab{doctype}" in value:
					found.append(f"raw SQL on `tab{doctype}`")
	# A table name can also reach frappe.db.sql through a variable or an
	# f-string, so any string constant naming one counts as well.
	for node in ast.walk(tree):
		if isinstance(node, ast.Constant) and isinstance(node.value, str):
			for doctype in doctypes:
				if f"tab{doctype}" in node.value:
					found.append(f"string naming `tab{doctype}`")
	return sorted(set(found))


def import_violations(source: str, foreign: str, allowed: frozenset[str]) -> list[str]:
	"""Imports of the foreign module that are not a published contract."""
	prefix = f"kentender_procurement.{foreign}"
	found: list[str] = []
	for node in ast.walk(ast.parse(source)):
		if isinstance(node, ast.ImportFrom):
			module = node.module or ""
			# `from ...<foreign>.services import events` — the imported names
			# are submodules, so check each rather than only the parent.
			if module == prefix or module.startswith(prefix + "."):
				candidates = [module] + [f"{module}.{alias.name}" for alias in node.names]
				if not any(c in allowed for c in candidates):
					found.append(module)
		elif isinstance(node, ast.Import):
			for alias in node.names:
				if alias.name.startswith(prefix) and alias.name not in allowed:
					found.append(alias.name)
	return sorted(set(found))


class DepartmentalNeedsArchitectureTest(IntegrationTestCase):
	"""NDS-910 — D1 is executable, not documentary."""

	def test_planning_never_touches_a_needs_table(self):
		offenders = [
			f"{relative}: {hit}"
			for relative, source in _sources(PLANNING)
			for hit in data_access_violations(source, NEEDS_DOCTYPES)
		]
		self.assertEqual(
			offenders,
			[],
			msg="Planning must reach Accepted Needs only through the published contract",
		)

	def test_planning_imports_only_the_published_contract(self):
		offenders = [
			f"{relative}: {hit}"
			for relative, source in _sources(PLANNING)
			for hit in import_violations(source, NEEDS, PUBLISHED_TO_PLANNING)
		]
		self.assertEqual(
			offenders,
			[],
			msg=f"only {sorted(PUBLISHED_TO_PLANNING)} may be imported by Planning",
		)

	def test_procurement_home_never_touches_a_needs_table(self):
		offenders = [
			f"{relative}: {hit}"
			for relative, source in _sources(HOME)
			for hit in data_access_violations(source, NEEDS_DOCTYPES)
		]
		self.assertEqual(
			offenders,
			[],
			msg="Procurement Home must count Accepted Needs through the published contract",
		)

	def test_procurement_home_imports_only_the_published_contract(self):
		offenders = [
			f"{relative}: {hit}"
			for relative, source in _sources(HOME)
			for hit in import_violations(source, NEEDS, PUBLISHED_TO_HOME)
		]
		self.assertEqual(
			offenders,
			[],
			msg=f"only {sorted(PUBLISHED_TO_HOME)} may be imported by Procurement Home",
		)

	def test_needs_never_touches_a_planning_table(self):
		"""The reverse direction, which the Phase 5 guard never checked.

		Needs owns the §4.7 usage projection and Planning writes it through
		`usage.project_planning_usage`. Needs reading `Plan Need Allocation`
		directly would rebuild the coupling from the other side — and did, until
		NDS-406 moved `planning_usage()` and `check_withdrawal_dependency()`
		onto the projection.
		"""
		offenders = [
			f"{relative}: {hit}"
			for relative, source in _sources(NEEDS)
			for hit in data_access_violations(source, PLANNING_DOCTYPES)
		]
		self.assertEqual(
			offenders,
			[],
			msg="Departmental Needs must not read or write Planning's records",
		)

	def test_needs_imports_nothing_from_planning(self):
		offenders = [
			f"{relative}: {hit}"
			for relative, source in _sources(NEEDS)
			for hit in import_violations(source, PLANNING, PUBLISHED_TO_NEEDS)
		]
		self.assertEqual(
			offenders,
			[],
			msg="Needs publishes to Planning and consumes nothing back",
		)

	def test_both_packages_are_actually_scanned(self):
		"""A scan over an empty file list passes vacuously and proves nothing."""
		for package in (NEEDS, PLANNING):
			with self.subTest(package=package):
				self.assertGreater(
					len(_sources(package)),
					20,
					msg=f"{package} source list looks wrong — the scan may be reading nothing",
				)

	def test_the_guard_catches_a_real_violation(self):
		"""Every rule above, committed deliberately, must be detected.

		The prose case matters as much as the code case: these modules describe
		the boundary in their own docstrings, so a guard that fired on comments
		would be unusable, and one that stripped strings would miss the SQL.
		"""
		prose = '"""Planning must never call frappe.get_all("Departmental Need")."""\n'
		self.assertEqual(
			data_access_violations(prose, NEEDS_DOCTYPES),
			[],
			msg="a docstring describing the rule is not a violation",
		)

		guilty = (
			"import frappe\n"
			'rows = frappe.get_all("Departmental Need", filters={})\n'
			'one = frappe.db.get_value("Departmental Need Version", "x", "title")\n'
			'raw = frappe.db.sql("select name from `tabDepartmental Need`")\n'
		)
		self.assertEqual(
			data_access_violations(guilty, NEEDS_DOCTYPES),
			[
				"get_all('Departmental Need')",
				"get_value('Departmental Need Version')",
				"raw SQL on `tabDepartmental Need`",
				"string naming `tabDepartmental Need`",
			],
		)

		self.assertEqual(
			import_violations(
				"from kentender_procurement.departmental_needs.services import lifecycle\n",
				NEEDS,
				PUBLISHED_TO_PLANNING,
			),
			["kentender_procurement.departmental_needs.services"],
			msg="importing an internal service through its parent package must be caught",
		)
		self.assertEqual(
			import_violations(
				"from kentender_procurement.departmental_needs.services import events\n",
				NEEDS,
				PUBLISHED_TO_PLANNING,
			),
			[],
			msg="the published contract must still be importable",
		)
		self.assertEqual(
			import_violations(
				"from kentender_procurement.procurement_planning.services import plan_items\n",
				PLANNING,
				PUBLISHED_TO_NEEDS,
			),
			["kentender_procurement.procurement_planning.services"],
			msg="Needs may import nothing from Planning at all",
		)
