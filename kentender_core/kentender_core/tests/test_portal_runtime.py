# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.1 Supplier Website shell / plan OD-B — the one
public portal page: surface resolution by longest owned prefix, resolver
verdicts (OK, NOT_FOUND, SIGN_IN with a return-to), the header with the
owning section marked current, and the footer built only from what the CFG
public projection supplies (BDS §10.7: never a placeholder).

The page itself is rendered through Frappe's website router so the test
sees exactly what a browser receives. Test surfaces are injected through
`frappe.flags.kt_portal_surfaces`; the Public Portal Settings Single is
snapshotted and restored (this bench has no test rollback).
"""

from __future__ import annotations

import re

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request
from frappe.website.serve import get_response

from kentender_core.services import portal_runtime
from kentender_core.services import public_portal as portal

RESOLVER = "kentender_core.tests.test_portal_runtime.fake_resolver"
SURFACES = [
	{"key": "tenders", "prefix": "/tenders", "resolver": RESOLVER, "bundle": "fake_surface.bundle.js"},
	{"key": "receipts", "prefix": "/account/receipts", "resolver": RESOLVER, "bundle": "fake_receipts.bundle.js"},
]


def fake_resolver(*, path, query, user):
	if path.endswith("/missing"):
		return {"verdict": "NOT_FOUND", "title": "Tender not found", "payload": {"state": "not_found"}}
	if path.endswith("/private"):
		return {"verdict": "SIGN_IN"}
	if path.endswith("/moved"):
		return {"verdict": "OK", "redirect": "/tenders"}
	return {"verdict": "OK", "title": "Available Tenders", "payload": {"path": path, "query": query, "user": user, "html": "</script><b>x</b>"}}


class TestPortalRuntime(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.flags.kt_portal_surfaces = SURFACES
		self.addCleanup(setattr, frappe.flags, "kt_portal_surfaces", None)
		snapshot = {f: frappe.db.get_single_value(portal.SETTINGS, f) for f in (*portal.EDITABLE_FIELDS, "record_version")}
		self.addCleanup(self._restore, snapshot)

	def _restore(self, snapshot):
		for field, value in snapshot.items():
			frappe.db.set_single_value(portal.SETTINGS, field, value)
		frappe.db.commit()

	def _render(self, path: str, user: str = "Guest"):
		frappe.set_user(user)
		self.addCleanup(frappe.set_user, "Administrator")
		route, _, query = path.partition("?")
		set_request(method="GET", path=route, query_string=query)
		return get_response()

	def test_the_longest_owned_prefix_wins_and_near_misses_are_not_owned(self):
		self.assertEqual(portal_runtime.resolve_surface("/tenders")["key"], "tenders")
		self.assertEqual(portal_runtime.resolve_surface("/tenders/TND-MOH-2027-033/bid")["key"], "tenders")
		self.assertEqual(portal_runtime.resolve_surface("/account/receipts/RCPT-1")["key"], "receipts")
		for path in ("/tendersx", "/account", "/", "/kt_portal"):
			self.assertIsNone(portal_runtime.resolve_surface(path), path)

	def test_the_header_marks_the_owning_section_and_keeps_board_order(self):
		items = portal_runtime.nav("/account/receipts")
		self.assertEqual([(i["label"], i["href"], i["current"]) for i in items], [("Tenders", "/tenders", False), ("My bids", "/my-bids", False), ("Account", "/account", True)])

	def test_the_footer_carries_only_what_the_cfg_projection_supplies(self):
		for field, value in {"supplier_support_email": "tendersupport@health.go.ke", "privacy_notice_url": "https://health.example.test/kentender/privacy", "portal_terms_url": "", "accessibility_statement_url": "https://health.example.test/kentender/accessibility"}.items():
			frappe.db.set_single_value(portal.SETTINGS, field, value)
		self.assertEqual(
			[(link["label"], link["href"]) for link in portal_runtime.footer()],
			[("Supplier support", "mailto:tendersupport@health.go.ke"), ("Privacy and data use", "https://health.example.test/kentender/privacy"), ("Accessibility", "https://health.example.test/kentender/accessibility")],
		)
		frappe.db.set_single_value(portal.SETTINGS, "supplier_support_email", "")
		self.assertNotIn("support", [link["key"] for link in portal_runtime.footer()])

	def test_a_surface_page_renders_the_shell_the_first_payload_and_the_surface_bundle(self):
		response = self._render("/tenders?search=laptops")
		html = response.get_data(as_text=True)
		self.assertEqual(response.status_code, 200)
		self.assertIn('data-kt-portal-surface="tenders"', html)
		self.assertIn('href="#kt-portal-main"', html)
		self.assertIn('<a href="/tenders" data-kt-portal-nav="tenders" aria-current="page">Tenders</a>', html)
		self.assertIn("fake_surface.bundle.js", html)
		self.assertIn("kt_portal_runtime", html)
		self.assertIn('"search": "laptops"', html)
		self.assertNotIn("</script><b>", html)  # the payload cannot close its script element
		# every surface's prefix, so in-page navigation keeps the longest-prefix rule
		self.assertIn('{"prefix": "/account/receipts", "key": "receipts"}', html)
		self.assertTrue("frappe.csrf_token" in html or "<!-- csrf_token -->" in html)  # Frappe fills it when the session has one
		# no Frappe website stylesheet, theme, navbar or footer reaches the portal
		stylesheets = re.findall(r'<link[^>]+rel="stylesheet"[^>]*>', html)
		self.assertEqual([s for s in stylesheets if "kentender_core/css/" not in s], [])
		for marker in ("navbar-expand", "web-footer", "website-theme"):
			self.assertNotIn(marker, html, marker)

	def test_verdicts_become_404_sign_in_and_redirect_responses(self):
		missing = self._render("/tenders/missing")
		self.assertEqual(missing.status_code, 404)
		self.assertIn('data-kt-portal-verdict="NOT_FOUND"', missing.get_data(as_text=True))
		private = self._render("/tenders/private")
		self.assertIn(private.status_code, (301, 302, 303, 307, 308))
		self.assertEqual(private.headers["Location"].split("?", 1)[1], "redirect-to=%2Ftenders%2Fprivate")
		self.assertTrue(private.headers["Location"].endswith("/login?redirect-to=%2Ftenders%2Fprivate"))
		moved = self._render("/tenders/moved")
		self.assertTrue(moved.headers["Location"].endswith("/tenders"))

	def test_a_path_no_surface_owns_is_a_plain_not_found_page(self):
		response = self._render("/kt_portal")
		self.assertEqual(response.status_code, 404)
		self.assertIn('data-testid="kt-portal-not-found"', response.get_data(as_text=True))
