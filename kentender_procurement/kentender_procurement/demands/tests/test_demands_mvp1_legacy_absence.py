# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-ABS-001…012 — Demands MVP-1 legacy absence evidence (active path only).

Administrator-only operational tests are covered by DEM-AC-013 / DEM-PERM-004
(Cursor prompt list item) — not duplicated as a separate ABS row.

Exclude from runtime absence claims: archive/, docs/, **/patches/*teardown*.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands import api as demands_api
from kentender_procurement.demands.services import demand_transitions as transitions
from kentender_procurement.procurement_lifecycle.seeds.works_master_loader import (
	WORKS_BASE_STEP_ROWS,
)

_PROC = Path(__file__).resolve().parents[2]  # kentender_procurement/
_DEMANDS = _PROC / "demands"
_PUBLIC_JS = _PROC / "public" / "js"
_DEMANDS_JS_GLOBS = (
	"demands_*.js",
	"demands_ui_fixtures/*.js",
)
# Split so this evidence module does not self-fail ABS-001 greps.
_DIA_LABEL = " ".join(("Demand", "Intake", "and", "Approval"))
_FORBIDDEN_OWNERSHIP_FIELDS = frozenset(
	{
		"requesting_department",
		"owner_state_department",
		"owner_directorate",
		"ministry_id",
		"ministry_code",
		"ministry_name",
		"ministry",
	}
)
_ALLOWED_ROUTES = frozenset({"Standard", "Additional", "Emergency"})
_RETIRED_DESK_ROUTES = ("demand-hub", "create-demand", "demand-workbench")
_CANONICAL_FIXTURE_MARKERS = (
	"DMD-MOH-2027-",
	"RSV-MOH-0001",
	"DEM-MOH-2026-001",
)
_DUAL_ADAPTER_MARKERS = (
	"dual_write",
	"dual_read",
	"dual-write",
	"dual-read",
)


def _iter_text_files(root: Path, *, suffixes: tuple[str, ...]) -> list[Path]:
	if not root.is_dir():
		return []
	out: list[Path] = []
	for path in root.rglob("*"):
		if not path.is_file():
			continue
		if path.suffix.lower() not in suffixes:
			continue
		parts = set(path.parts)
		if "archive" in parts or "docs" in parts:
			continue
		if "patches" in parts and "teardown" in path.name.lower():
			continue
		out.append(path)
	return out


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8", errors="replace")


def _demand_js_files() -> list[Path]:
	files: list[Path] = []
	for pattern in _DEMANDS_JS_GLOBS:
		files.extend(_PUBLIC_JS.glob(pattern))
	return [p for p in files if p.is_file()]


def _decorator_is_whitelist(dec: ast.AST) -> bool:
	if isinstance(dec, ast.Name) and dec.id == "whitelist":
		return True
	if isinstance(dec, ast.Attribute) and dec.attr == "whitelist":
		return True
	if isinstance(dec, ast.Call):
		return _decorator_is_whitelist(dec.func)
	return False


def _whitelist_defs_setting_planning_ready(source: str) -> list[str]:
	"""Return whitelist function names that assign planning_ready (AST)."""
	tree = ast.parse(source)
	hits: list[str] = []

	class Visitor(ast.NodeVisitor):
		def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
			if any(_decorator_is_whitelist(d) for d in node.decorator_list):
				for child in ast.walk(node):
					if isinstance(child, ast.Assign):
						for t in child.targets:
							if "planning_ready" in ast.dump(t):
								hits.append(node.name)
					elif isinstance(child, ast.AugAssign):
						if "planning_ready" in ast.dump(child.target):
							hits.append(node.name)
			self.generic_visit(node)

		visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[misc]

	Visitor().visit(tree)
	return sorted(set(hits))


class TestDemandsMvp1LegacyAbsence(IntegrationTestCase):
	"""Consolidated DEM-ABS-001…012 evidence."""

	def test_abs_001_no_dia_labels_in_active_desk_path(self) -> None:
		"""DEM-ABS-001 — no visible Demand Intake and Approval labels."""
		modules_txt = (_PROC / "modules.txt").read_text(encoding="utf-8")
		self.assertIn("Demands", modules_txt)
		self.assertNotIn(_DIA_LABEL, modules_txt)

		self.assertTrue(frappe.db.exists("Module Def", "Demands"))
		mod = frappe.get_doc("Module Def", "Demands")
		self.assertNotEqual((mod.module_name or mod.name or ""), _DIA_LABEL)

		# Active UI / demands runtime / lifecycle seeds (exclude tests + teardown).
		scan_roots = [
			_DEMANDS,
			_PUBLIC_JS,
			_PROC / "procurement_lifecycle" / "seeds",
			_PROC / "procurement_lifecycle" / "budget_funding_handoff.py",
			_PROC / "procurement_lifecycle" / "demand_approval_handoff.py",
			_PROC / "procurement_home",
		]
		hits: list[str] = []
		for root in scan_roots:
			paths = [root] if root.is_file() else _iter_text_files(
				root, suffixes=(".py", ".js", ".json", ".txt", ".html")
			)
			for path in paths:
				if "tests" in path.parts:
					continue
				# Narrow public/js to demands* only
				if _PUBLIC_JS in path.parents or path.parent == _PUBLIC_JS:
					if not (
						path.name.startswith("demands")
						or "demands_ui_fixtures" in path.parts
					):
						continue
				text = _read(path)
				if _DIA_LABEL in text:
					hits.append(str(path.relative_to(_PROC)))

		self.assertEqual(hits, [], f"DIA label still present in: {hits}")

		demand_steps = [s for s in WORKS_BASE_STEP_ROWS if s.get("step_key") == "demand"]
		self.assertTrue(demand_steps)
		self.assertEqual(demand_steps[0]["owner_module"], "Demands")

	def test_abs_002_no_ministry_ownership_fields(self) -> None:
		"""DEM-ABS-002 — Demand has no ministry/department ownership fields."""
		meta = frappe.get_meta("Demand")
		fieldnames = {f.fieldname for f in meta.fields}
		overlap = fieldnames & _FORBIDDEN_OWNERSHIP_FIELDS
		self.assertEqual(overlap, set())

		demand_json = json.loads(
			(_DEMANDS / "doctype" / "demand" / "demand.json").read_text(encoding="utf-8")
		)
		json_fields = {f.get("fieldname") for f in demand_json.get("fields") or []}
		self.assertEqual(json_fields & _FORBIDDEN_OWNERSHIP_FIELDS, set())

	def test_abs_003_no_requester_strategy_budget_selectors(self) -> None:
		"""DEM-ABS-003 — create form has no Strategy/Budget selectors."""
		form_js = _read(_PUBLIC_JS / "demands_ui_fixtures" / "form.js")
		bind_js = _read(_PUBLIC_JS / "demands_live_bind.js")
		# Requester create surface markers that must stay absent.
		for marker in (
			'data-kt-dem-field="strategy',
			'data-kt-dem-field="budget',
			"kt-dem-ui02-strategy",
			"kt-dem-ui02-budget",
			"strategy_plan_selector",
			"budget_line_selector",
		):
			self.assertNotIn(marker, form_js)
			# Create-bind path in live_bind must not introduce those fixtures either.
			self.assertNotIn(marker, bind_js.split("bindDemandForm")[0] if "bindDemandForm" in bind_js else bind_js)

	def test_abs_004_no_pending_hod_finance_workflow(self) -> None:
		"""DEM-ABS-004 — no Pending HoD/Finance operative statuses/stages."""
		for banned in ("Pending HoD", "Pending Finance", "Pending Finance Approval"):
			self.assertNotIn(banned, transitions.STATUSES)
			self.assertNotIn(banned, transitions.STAGES)
			matrix_blob = " ".join(
				f"{a} {b} {c} {r.status} {r.stage}"
				for (a, b, c), r in transitions.DEMAND_TRANSITIONS.items()
			)
			self.assertNotIn(banned, matrix_blob)

		meta = frappe.get_meta("Demand")
		status_opts = (meta.get_field("status").options or "").split("\n")
		stage_opts = (meta.get_field("current_stage").options or "").split("\n")
		for banned in ("Pending HoD", "Pending Finance", "Pending Finance Approval"):
			self.assertNotIn(banned, status_opts)
			self.assertNotIn(banned, stage_opts)

	def test_abs_005_req_routes_only(self) -> None:
		"""DEM-ABS-005 — demand_route options are REQ routes only."""
		meta = frappe.get_meta("Demand")
		opts = {
			o.strip()
			for o in (meta.get_field("demand_route").options or "").split("\n")
			if o.strip()
		}
		self.assertEqual(opts, _ALLOWED_ROUTES)
		self.assertNotIn("Planned", opts)
		self.assertNotIn("Unplanned", opts)

	def test_abs_006_no_manual_planning_ready_whitelist(self) -> None:
		"""DEM-ABS-006 — no whitelist that manually sets planning_ready."""
		api_src = _read(_DEMANDS / "api.py")
		# Whitelisted API must not assign planning_ready; lifecycle approve/cancel may.
		hits = _whitelist_defs_setting_planning_ready(api_src)
		self.assertEqual(
			hits,
			[],
			f"Whitelisted API must not mutate planning_ready directly: {hits}",
		)
		# Approve/cancel paths live in demand_lifecycle (not raw whitelist setters).
		life = _read(_DEMANDS / "services" / "demand_lifecycle.py")
		self.assertIn("doc.planning_ready = 1", life)
		self.assertIn("reserve_funding", life)

	def test_abs_007_no_demand_procurement_method_selection(self) -> None:
		"""DEM-ABS-007 — enrichment forbids procurement-method keys."""
		self.assertTrue(demands_api._FORBIDDEN_ENRICHMENT_KEYS)
		for key in (
			"procurement_method",
			"tender_method",
			"method_of_procurement",
			"evaluation_method",
		):
			self.assertIn(key, demands_api._FORBIDDEN_ENRICHMENT_KEYS)

		review_js = _read(_PUBLIC_JS / "demands_ui_fixtures" / "review.js")
		for key in demands_api._FORBIDDEN_ENRICHMENT_KEYS:
			self.assertNotIn(f'data-kt-dem-field="{key}"', review_js)
			self.assertNotIn(f'name="{key}"', review_js)

	def test_abs_008_no_direct_budget_balance_writes_from_ui(self) -> None:
		"""DEM-ABS-008 — Demand Desk JS does not write Budget balances."""
		forbidden = (
			"amount_available",
			"amount_reserved",
			"set_value(\"Budget",
			"set_value('Budget",
			"frappe.db.set_value",
			"reserve_funding(",
			"mutate_budget",
		)
		hits: list[str] = []
		for path in _demand_js_files():
			text = _read(path)
			for marker in forbidden:
				# Display-only amount_reserved reads are OK; assignments / mutate APIs are not.
				if marker in ("amount_reserved", "amount_available"):
					if re.search(
						rf"{re.escape(marker)}\s*=",
						text,
					) or f"set_value" in text and marker in text:
						# Only flag if writing via frappe.call mutate patterns
						if re.search(
							rf"(set_value|db\.set_value).*{re.escape(marker)}",
							text,
						):
							hits.append(f"{path.name}:{marker}")
					continue
				if marker in text:
					hits.append(f"{path.name}:{marker}")
		self.assertEqual(hits, [], f"Budget balance write markers in Demand JS: {hits}")

	def test_abs_009_no_duplicate_reservation_ledger(self) -> None:
		"""DEM-ABS-009 — Demands call Budget reserve_funding; no Demand RSV ledger."""
		self.assertFalse(frappe.db.exists("DocType", "Demand Reservation"))
		self.assertFalse(frappe.db.exists("DocType", "Demand Funding Reservation"))
		life = _read(_DEMANDS / "services" / "demand_lifecycle.py")
		self.assertIn("from kentender_budget.services.budget_check_reserve_contracts import reserve_funding", life)
		self.assertIn("reserve_funding(", life)
		# No local reservation service module under demands/
		rsv_services = list((_DEMANDS / "services").glob("*reserv*"))
		self.assertEqual(rsv_services, [])

	def test_abs_010_no_page_local_canonical_fixture_json(self) -> None:
		"""DEM-ABS-010 — no canonical contract codes embedded in Demand Desk JS."""
		hits: list[str] = []
		for path in _demand_js_files():
			text = _read(path)
			for marker in _CANONICAL_FIXTURE_MARKERS:
				if marker in text:
					hits.append(f"{path.name}:{marker}")
		self.assertEqual(hits, [], f"Page-local fixture codes in Demand JS: {hits}")

	def test_abs_011_no_dual_read_write_adapters(self) -> None:
		"""DEM-ABS-011 — no dual-write/DIA write fallbacks in active demands/ services."""
		hits: list[str] = []
		for path in _iter_text_files(_DEMANDS / "services", suffixes=(".py",)):
			text = _read(path)
			for marker in _DUAL_ADAPTER_MARKERS:
				if marker in text:
					hits.append(f"{path.name}:{marker}")
			# Legacy DIA DocType write patterns
			if re.search(r'get_doc\(\s*["\']Demand Intake', text):
				hits.append(f"{path.name}:get_doc(DIA)")
			if re.search(r'new_doc\(\s*["\']Demand Intake', text):
				hits.append(f"{path.name}:new_doc(DIA)")
		# Thin INT-010 shim lives outside demands/services — allowed; assert shim delegates.
		shim = (
			_PROC
			/ "procurement_lifecycle"
			/ "legacy_demand_seed_shim.py"
		)
		if shim.is_file():
			shim_text = _read(shim)
			self.assertIn("upsert_works_master_demand", shim_text)
			for marker in _DUAL_ADAPTER_MARKERS:
				self.assertNotIn(marker, shim_text)
		self.assertEqual(hits, [], f"Dual adapter markers: {hits}")

	def test_abs_012_no_stale_demand_desk_routes(self) -> None:
		"""DEM-ABS-012 — no demand-hub / create-demand / demand-workbench in active PP2/Home."""
		pp2 = _read(_PUBLIC_JS / "pp2_planning_router.js")
		home_root = _PROC / "procurement_home"
		blobs = [("pp2_planning_router.js", pp2)]
		for path in list(home_root.rglob("*.js")) + list(home_root.rglob("*.py")):
			if "archive" in path.parts or "docs" in path.parts or "tests" in path.parts:
				continue
			blobs.append((str(path.relative_to(_PROC)), _read(path)))

		for name, text in blobs:
			for route in _RETIRED_DESK_ROUTES:
				self.assertNotIn(
					route,
					text,
					f"{route} still present in {name}",
				)

		for route in _RETIRED_DESK_ROUTES:
			self.assertFalse(
				frappe.db.exists("Page", route),
				f"Retired Page still registered: {route}",
			)
