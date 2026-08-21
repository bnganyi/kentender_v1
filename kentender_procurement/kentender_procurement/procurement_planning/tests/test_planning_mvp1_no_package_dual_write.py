# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-ABS-018 — no Package dual-write / dual-read adapters in Planning MVP-1."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_SERVICES = Path(__file__).resolve().parents[1] / "services"

_FORBIDDEN_SNIPPETS = (
	"Procurement Package",
	"Package Line",
	"pp2_constants",
	"create_tender_from_package",
	"release_procurement_package",
	"dual_write",
	"dual-write",
)


class TestPlanningMvp1NoPackageDualWrite(IntegrationTestCase):
	def test_package_doctype_absent(self) -> None:
		self.assertFalse(frappe.db.exists("DocType", "Procurement Package"))
		self.assertFalse(frappe.db.exists("DocType", "Procurement Package Line"))

	def test_mvp_services_have_no_package_adapters(self) -> None:
		hits: list[str] = []
		for path in _SERVICES.rglob("*.py"):
			text = path.read_text(encoding="utf-8", errors="ignore")
			for snip in _FORBIDDEN_SNIPPETS:
				if snip in text:
					hits.append(f"{path.name}: {snip}")
		self.assertEqual(hits, [], msg="Package dual-write markers remain:\n" + "\n".join(hits))
