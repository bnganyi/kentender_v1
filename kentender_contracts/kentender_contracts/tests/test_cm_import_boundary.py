# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §3.1, CM-AC-25 / CM-AC-32, plan D2 (tracker CM8-106): Contract
Management installs and runs without the tendering apps, so its code imports only
`frappe`, `erpnext`, `kentender_core` and itself. The Budget adapter is the one
allowed exception, and only under `adapters/`, behind an installed-app guard.

A static scan: it reads every module of the app (tests included) and fails on an
import, or a dotted-path string handed to `frappe.get_attr`, that names another
KenTender app. It cannot prove the app installs on a site without them (that is
`make cm-independence-gate`), but it stops the most common way independence is
lost: an `import kentender_procurement…` added for convenience."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from frappe.tests import IntegrationTestCase

APP_ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"frappe", "erpnext", "kentender_core", "kentender_contracts"}
# Other KenTender apps: never importable here, except where a guarded adapter says so.
ADAPTER_ONLY = {"kentender_budget"}
STDLIB = set(sys.stdlib_module_names)


def violations(source: str, relative_path: str) -> list[str]:
	"""Names of imports (and quoted dotted paths) in `source` that break the boundary."""
	in_adapters = relative_path.startswith("adapters/")
	found: list[str] = []
	for node in ast.walk(ast.parse(source)):
		roots: list[str] = []
		if isinstance(node, ast.Import):
			roots = [alias.name.split(".")[0] for alias in node.names]
		elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
			roots = [node.module.split(".")[0]]
		elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("kentender_") and "." in node.value:
			roots = [node.value.split(".")[0]]
		for root in roots:
			if root in ALLOWED or root in STDLIB:
				continue
			if root in ADAPTER_ONLY and in_adapters:
				continue
			if root.startswith("kentender"):
				found.append(root)
	return found


class TestImportBoundary(IntegrationTestCase):
	def test_the_scan_catches_what_it_is_for(self):
		self.assertEqual(violations("import kentender_procurement.award", "services/x.py"), ["kentender_procurement"])
		self.assertEqual(violations("from kentender_budget.services import a", "services/x.py"), ["kentender_budget"])
		self.assertEqual(violations("from kentender_budget.services import a", "adapters/budget.py"), [])
		self.assertEqual(violations("frappe.get_attr('kentender_suppliers.supplier_accounts.services.provider.x')", "services/x.py"), ["kentender_suppliers"])
		self.assertEqual(violations("import frappe\nfrom kentender_core.services import signing\nimport json", "services/x.py"), [])

	def test_the_app_imports_only_what_independence_allows(self):
		bad: dict[str, list[str]] = {}
		for path in sorted(APP_ROOT.rglob("*.py")):
			relative = path.relative_to(APP_ROOT).as_posix()
			found = violations(path.read_text(), relative)
			if found:
				bad[relative] = found
		self.assertEqual(bad, {}, "Contract Management must not import the tendering or other KenTender apps (plan D2)")
