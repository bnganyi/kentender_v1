# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home must admit Demands MVP roles (module tile → kt-procurement-home)."""

from __future__ import annotations

import json
import os

import frappe
from frappe.boot import get_allowed_pages
from frappe.tests import IntegrationTestCase

# Same operational set as demands-workspace Page (DEM-PERM / DEM-UI-01).
_DEMANDS_PAGE_ROLES: frozenset[str] = frozenset(
	{
		"Requester",
		"Business Approver",
		"Procurement Approval Authority",
		"Budget Officer",
		"Planning Officer",
		"Demand Viewer",
		"Auditor",
	}
)

_CANONICAL_BA = "moh.business.approver@example.test"


def _procurement_home_json_path() -> str:
	app_path = frappe.get_app_path("kentender_procurement")
	for candidate in (
		os.path.join(
			app_path,
			"kentender_procurement",
			"page",
			"kt_procurement_home",
			"kt_procurement_home.json",
		),
		os.path.join(app_path, "page", "kt_procurement_home", "kt_procurement_home.json"),
	):
		if os.path.isfile(candidate):
			return candidate
	return ""


class TestProcurementHomeDemandsRoles(IntegrationTestCase):
	def test_export_includes_demands_mvp_roles(self):
		path = _procurement_home_json_path()
		self.assertTrue(path, msg="kt_procurement_home.json missing")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		roles = {row.get("role") for row in (data.get("roles") or [])}
		missing = _DEMANDS_PAGE_ROLES - roles
		self.assertFalse(
			missing,
			msg=f"kt-procurement-home export missing Demands roles: {sorted(missing)}",
		)

	def test_site_page_includes_demands_mvp_roles(self):
		if not frappe.db.exists("Page", "kt-procurement-home"):
			self.skipTest("kt-procurement-home Page not on site")
		roles = {
			r.role
			for r in frappe.get_all(
				"Has Role",
				filters={"parent": "kt-procurement-home", "parenttype": "Page"},
				fields=["role"],
			)
		}
		missing = _DEMANDS_PAGE_ROLES - roles
		self.assertFalse(
			missing,
			msg=f"kt-procurement-home site Page missing Demands roles: {sorted(missing)}",
		)

	def test_business_approver_allowed_procurement_home_page(self):
		if not frappe.db.exists("User", _CANONICAL_BA):
			self.skipTest(f"Canonical BA {_CANONICAL_BA} not seeded")
		if not frappe.db.exists("Page", "kt-procurement-home"):
			self.skipTest("kt-procurement-home Page not on site")
		frappe.set_user(_CANONICAL_BA)
		try:
			allowed = get_allowed_pages(cache=False)
			self.assertIn(
				"kt-procurement-home",
				allowed,
				msg="Business Approver must load Procurement Home (Desktop Icon → page)",
			)
		finally:
			frappe.set_user("Administrator")
