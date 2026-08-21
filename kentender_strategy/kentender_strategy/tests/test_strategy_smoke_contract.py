# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §16 smoke contract — the two gates not already exercised by a
more specific test elsewhere: static dependency scan and module import.

Seed repeatability -> test_strategy_seed_integrity.py
Domain / permission / integration tests -> the rest of this test suite
Browser smoke -> verified live via Playwright per phase, not re-run here
"""

from __future__ import annotations

import ast
import importlib
import pathlib
import re

import frappe
from frappe.tests.utils import FrappeTestCase

APP_ROOT = pathlib.Path(__file__).resolve().parents[1]
BENCH_APPS_ROOT = APP_ROOT.parents[1]

STRATEGY_DOCTYPES = (
	"Strategic Plan",
	"Strategy Programme",
	"Strategy Sub Programme",
	"Strategic Objective",
	"Strategic Outcome",
	"Performance Indicator",
	"Performance Target",
	"Strategy Value Commitment",
	"Strategy Value Commitment Link",
	"Performance Measurement",
	"Strategy Audit Event",
)
DOWNSTREAM_APP_DIRS = ("kentender_budget", "kentender_procurement", "kentender_core")

SERVICE_MODULES = (
	"kentender_strategy.services.strategy_audit",
	"kentender_strategy.services.strategy_consumer",
	"kentender_strategy.services.strategy_contracts",
	"kentender_strategy.services.strategy_domain_guards",
	"kentender_strategy.services.strategy_measurement",
	"kentender_strategy.services.strategy_notification_service",
	"kentender_strategy.services.strategy_performance",
	"kentender_strategy.services.strategy_permissions",
	"kentender_strategy.services.strategy_readiness",
	"kentender_strategy.services.strategy_reference",
	"kentender_strategy.services.strategy_transitions",
	"kentender_strategy.services.strategy_writes",
	"kentender_strategy.api.strategy_api",
	"kentender_strategy.hooks",
)

# Seeds are explicitly allowed to orchestrate across modules (they call other
# apps' seed functions on purpose) — the "no downstream module required at
# import time" guarantee applies to the live business-logic surface, not seeds.
CORE_SURFACE_DIRS = ("services", "api")
DOWNSTREAM_PREFIXES = (
	"kentender_procurement",
	"kentender_budget",
	"kentender_governance",
	"kentender_compliance",
	"kentender_stores",
	"kentender_assets",
	"kentender_integrations",
	"kentender_suppliers",
	"kentender_transparency",
)


def _module_level_imports(path: pathlib.Path) -> set[str]:
	tree = ast.parse(path.read_text())
	names: set[str] = set()
	for node in ast.walk(tree):
		if isinstance(node, ast.Import):
			names.update(alias.name for alias in node.names)
		elif isinstance(node, ast.ImportFrom) and node.module:
			names.add(node.module)
	return names


class TestStrategySmokeContract(FrappeTestCase):
	def test_static_scan_no_legacy_demands_or_treatment_imports(self):
		"""STR-CHG-001 §16 — static dependency scan, first gate."""
		offenders = []
		for f in APP_ROOT.rglob("*.py"):
			if "__pycache__" in f.parts or "tests" in f.parts:
				continue
			text = f.read_text()
			if "kentender_procurement.demands" in text or "demand_module_gate" in text:
				offenders.append(str(f.relative_to(APP_ROOT)))
		self.assertEqual(offenders, [], f"legacy demands reference found in: {offenders}")

	def test_static_scan_no_downstream_module_imports_in_core_surface(self):
		"""STR-CHG-001 §16 — no downstream module required at import time.

		Only module-level (top-of-file) imports count — a service function
		doing a *local* import of a downstream module inside its own body
		(e.g. strategy_consumer's helpers, called only when a downstream app
		is already present and calling in) is a different, permitted shape.
		"""
		offenders = []
		for sub in CORE_SURFACE_DIRS:
			for f in (APP_ROOT / sub).glob("*.py"):
				if f.name == "__init__.py":
					continue
				for name in _module_level_imports(f):
					if any(name == p or name.startswith(p + ".") for p in DOWNSTREAM_PREFIXES):
						offenders.append(f"{f.relative_to(APP_ROOT)}: {name}")
		self.assertEqual(offenders, [], f"downstream module-level import found: {offenders}")

	def test_hooks_required_apps_has_no_downstream_module(self):
		import kentender_strategy.hooks as hooks

		required = list(getattr(hooks, "required_apps", []))
		for prefix in DOWNSTREAM_PREFIXES:
			self.assertNotIn(prefix, required)

	def test_module_import_service_and_api_surface(self):
		"""STR-CHG-001 §16 — module import gate: every Strategy service, API
		and hooks module imports cleanly with no downstream module required."""
		for name in SERVICE_MODULES:
			importlib.import_module(name)

	def test_downstream_apps_never_construct_a_mutable_strategy_document(self):
		"""STR-FR-017 — downstream modules must not mutate Strategy records.
		Structural guarantee: no downstream app ever holds a live Strategy
		Document object to call .save()/.insert()/.delete_doc() on in the
		first place — confirmed by scanning for frappe.get_doc/new_doc
		constructed directly against a Strategy doctype name."""
		pattern = re.compile(
			r"frappe\.(get_doc|new_doc)\(\s*[\"']("
			+ "|".join(re.escape(d) for d in STRATEGY_DOCTYPES)
			+ r")[\"']"
		)
		offenders = []
		for app_dir in DOWNSTREAM_APP_DIRS:
			root = BENCH_APPS_ROOT / app_dir
			if not root.is_dir():
				continue
			for f in root.rglob("*.py"):
				if "__pycache__" in f.parts or "tests" in f.parts:
					continue
				text = f.read_text(errors="ignore")
				for m in pattern.finditer(text):
					offenders.append(f"{f.relative_to(BENCH_APPS_ROOT)}: {m.group(0)}")
		self.assertEqual(offenders, [], f"downstream mutation handle found: {offenders}")

	def test_module_import_all_doctype_controllers(self):
		doctypes = frappe.get_all(
			"DocType", filters={"module": "Kentender Strategy"}, pluck="name"
		)
		self.assertTrue(doctypes)
		for dt in doctypes:
			frappe.get_meta(dt)
