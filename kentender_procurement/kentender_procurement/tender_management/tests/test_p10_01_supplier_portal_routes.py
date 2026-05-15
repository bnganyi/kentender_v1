# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P10-01 — supplier portal website routes (doc 9 §18.1).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p10_01_supplier_portal_routes
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache


class TestP1001SupplierPortalRoutes(IntegrationTestCase):
	def setUp(self):
		clear_website_cache()

	def tearDown(self):
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		frappe.set_user("Administrator")

	def _get(self, path: str):
		set_request(method="GET", path=path)
		return get_response()

	def test_p10_01_guest_redirects_to_login(self) -> None:
		frappe.set_user("Guest")
		resp = self._get("/supplier/tenders")
		self.assertIn(resp.status_code, (301, 302))
		loc = resp.headers.get("Location") or ""
		self.assertIn("/login", loc)

	def test_p10_01_list_route_200_and_selector(self) -> None:
		frappe.set_user("Administrator")
		resp = self._get("/supplier/tenders")
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-tender-list"', body)
		self.assertIn('data-testid="tm2-supplier-tender-list-tabs"', body)

	def test_p10_01_detail_route_200_and_selector(self) -> None:
		frappe.set_user("Administrator")
		resp = self._get("/supplier/tenders/TND-MOH-2026-001")
		self.assertEqual(resp.status_code, 200)
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="tm2-supplier-tender-detail"', body)
		self.assertIn('data-testid="tm2-supplier-tender-detail-header"', body)
		self.assertIn("TND-MOH-2026-001", body)
