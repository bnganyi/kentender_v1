# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-RET-005 / PLN-ABS-* — PP2 Planning full removal evidence."""

from __future__ import annotations

import unittest
from pathlib import Path

import frappe


_PROC = Path(__file__).resolve().parents[2]  # kentender_procurement package
_V1 = Path(__file__).resolve().parents[4]  # apps/kentender_v1


# MVP-1 may use procurement_planning.services.*; PP2 stems remain forbidden.
_FORBIDDEN_LIVE_IMPORT_STEMS = (
	"procurement_planning.pp2_constants",
	"procurement_planning.api.",
	"procurement_planning.seeds.",
	"procurement_planning.permissions.",
)

_FORBIDDEN_ASSET_NAMES = (
	"pp2_planning_router.js",
	"pp2_planning_home.js",
	"create_package_wizard_page.js",
	"package_detail_page.js",
	"planning_hub_page.js",
)

_PP2_DOCTYPES = (
	"Procurement Package",
	"Procurement Package Line",
	"Package Review Decision",
	"Package Readiness Result",
	"Package Method Decision",
	"Planning Release Consumption",
	"Planning Correction Supersession",
)


class TestPp2FullRemovalAbs(unittest.TestCase):
	def test_abs_001_002_003_package_doctypes_gone(self) -> None:
		for dt in _PP2_DOCTYPES:
			self.assertFalse(
				frappe.db.exists("DocType", dt),
				msg=f"PP2 DocType still present: {dt}",
			)

	def test_abs_006_pp2_desk_pages_gone(self) -> None:
		for page in ("planning-hub", "create-package-wizard", "package-detail"):
			self.assertFalse(
				frappe.db.exists("Page", page),
				msg=f"PP2 Desk page still present: {page}",
			)

	def test_abs_assets_removed_from_disk(self) -> None:
		public_js = _PROC / "public" / "js"
		for name in _FORBIDDEN_ASSET_NAMES:
			self.assertFalse((public_js / name).exists(), msg=f"PP2 asset still on disk: {name}")

	def test_abs_no_live_pp2_module_imports(self) -> None:
		"""Scan live Python under apps (exclude archive/docs)."""
		roots = [
			_V1 / "kentender_procurement" / "kentender_procurement",
			_V1 / "kentender_core" / "kentender_core",
			_V1 / "kentender_strategy" / "kentender_strategy",
			_V1 / "kentender_budget" / "kentender_budget",
		]
		hits: list[str] = []
		for root in roots:
			if not root.is_dir():
				continue
			for path in root.rglob("*.py"):
				rel = str(path.relative_to(_V1))
				if "/archive/" in f"/{rel}" or "/__pycache__/" in f"/{rel}":
					continue
				if path.name == "test_pp2_full_removal_abs.py":
					continue
				text = path.read_text(encoding="utf-8", errors="ignore")
				for stem in _FORBIDDEN_LIVE_IMPORT_STEMS:
					if stem in text:
						hits.append(f"{rel}: {stem}")
		self.assertEqual(hits, [], msg="Live PP2 Planning imports remain:\n" + "\n".join(hits[:40]))
