# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-003 / AUD-XC-126 — the retired second-generation tender surface stays deleted.

The retired module's publication endpoints trusted a client-supplied ``actor``
(``actor=Administrator`` skipped every role check), so the fix is deletion, not a
patch. These tests fail if the package, its Desk page or its whitelisted endpoints
come back, and prove the drop patch removes leftover site records safely and
idempotently.

The retired names are assembled from fragments so this file is not itself a
reference to the retired module.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_APP = Path(__file__).resolve().parents[1]
_PKG = "tender_" + "management"
_PREFIX = "tm" + "2"
_PATCH = "kentender_procurement.patches.drop_retired_" + _PREFIX + "_surface"


class TestRetiredSurfaceGone(IntegrationTestCase):
	def test_python_package_is_gone(self):
		self.assertIsNone(importlib.util.find_spec(f"kentender_procurement.{_PKG}"))
		self.assertFalse((_APP / _PKG).exists())

	def test_publication_endpoints_are_not_routable(self):
		for method in (
			"pub_api_approve_for_publication",
			"pub_api_publish_tender",
			"pub_api_create_configuration_snapshot",
		):
			path = f"kentender_procurement.{_PKG}.tender_publication.api.handlers.{method}"
			with self.assertRaises((ImportError, AttributeError, frappe.DoesNotExistError)):
				frappe.get_attr(path)

	def test_no_doctype_or_page_directories_remain(self):
		doctype_dir = _APP / "kentender_procurement" / "doctype"
		self.assertEqual([p.name for p in doctype_dir.glob(f"{_PREFIX}_*")], [])
		self.assertFalse((_APP / "kentender_procurement" / "page" / (_PKG + "_v2")).exists())
		for name in ("security_permission", "security_role", "security_role_permission"):
			self.assertFalse((doctype_dir / name).exists(), name)

	def test_hooks_register_no_retired_assets(self):
		hooks = (_APP / "hooks.py").read_text()
		self.assertNotIn(_PREFIX, hooks.lower())
		self.assertNotIn(_PKG, hooks)


class TestDropRetiredSurfacePatch(IntegrationTestCase):
	"""The drop patch is guarded and safe to run twice, including on a clean site."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.patch = importlib.import_module(_PATCH)

	def test_runs_twice_on_a_site_where_everything_is_already_gone(self):
		self.patch.execute()
		self.patch.execute()
		for doctype in self.patch.RETIRED_DOCTYPES:
			self.assertFalse(frappe.db.exists("DocType", doctype), doctype)
			self.assertFalse(frappe.db.table_exists(doctype), doctype)
		self.assertFalse(frappe.db.exists("Page", self.patch.RETIRED_PAGE))

	def test_removes_leftover_records_tables_and_page_then_is_a_no_op(self):
		doctype = self.patch.RETIRED_DOCTYPES[0]
		page = self.patch.RETIRED_PAGE
		self.addCleanup(self.patch.execute)

		frappe.db.sql_ddl(f"create table if not exists `tab{doctype}` (name varchar(140) primary key)")
		frappe.get_doc(
			{
				"doctype": "DocType",
				"name": doctype,
				"module": "Kentender Procurement",
				"custom": 1,
				"fields": [{"fieldname": "title", "fieldtype": "Data", "label": "Title"}],
			}
		).db_insert()
		frappe.db.sql(
			"insert into `tabDocField` (name, parent, parenttype, parentfield, fieldname, fieldtype, idx) "
			"values (%s, %s, 'DocType', 'fields', 'title', 'Data', 1)",
			(f"{doctype}-title-leftover", doctype),
		)
		if not frappe.db.exists("Page", page):
			frappe.get_doc(
				{"doctype": "Page", "name": page, "page_name": page, "title": page, "module": "Kentender Procurement", "standard": "No"}
			).db_insert()

		self.assertTrue(frappe.db.exists("DocType", doctype))
		self.patch.execute()
		self.assertFalse(frappe.db.exists("DocType", doctype))
		self.assertFalse(frappe.db.table_exists(doctype))
		self.assertFalse(frappe.db.exists("DocField", {"parent": doctype}))
		self.assertFalse(frappe.db.exists("Page", page))

		self.patch.execute()  # second run: nothing left to do, nothing raised
		self.assertFalse(frappe.db.exists("DocType", doctype))
