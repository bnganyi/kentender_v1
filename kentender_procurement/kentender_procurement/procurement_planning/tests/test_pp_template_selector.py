# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""D5 — ``list_pp_templates`` / ``get_pp_template_preview`` API smoke tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api import template_selector


class TestPpTemplateSelectorApi(IntegrationTestCase):
	def test_guest_list_denied(self) -> None:
		frappe.set_user("Guest")
		out = template_selector.list_pp_templates()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_guest_preview_denied(self) -> None:
		frappe.set_user("Guest")
		out = template_selector.get_pp_template_preview("does-not-matter")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_invalid_template_preview(self) -> None:
		frappe.set_user("Administrator")
		out = template_selector.get_pp_template_preview("___no_such_template_ref_zz__")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_admin_list_when_templates_exist(self) -> None:
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Template"):
			return
		seed = frappe.get_all(
			"Procurement Template", filters={"is_active": 1}, fields=["name", "template_code"], limit=1
		)
		if not seed:
			return
		first = seed[0].get("name")
		if not first:
			return
		out = template_selector.list_pp_templates()
		self.assertTrue(out.get("ok"), msg=str(out.get("message")))
		rows = out.get("rows") or []
		self.assertGreaterEqual(len(rows), 1)
		codes = {r.get("template_code") for r in rows if r.get("template_code")}
		pv = template_selector.get_pp_template_preview(first)
		self.assertTrue(pv.get("ok"))
		tcode = (pv.get("template_code") or "").strip()
		if tcode:
			self.assertIn(tcode, codes)
		self.assertIn("profile_labels", pv)
		self.assertIn("profile_links", pv)
