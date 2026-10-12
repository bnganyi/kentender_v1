# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-04 / RG-05 / AUD-XC-143 / AUD-XC-011 — the retired Tender Configurations module stays deleted.

The legacy module approved and published a tender on write permission alone (no maker-checker,
no Accounting Officer), let a publication record be created already Published, and committed
mid-request. The fix is deletion, not a patch. These tests fail if the package, its Desk pages,
its whitelisted endpoints, its hooks or its module registration come back, and prove the drop
patch removes leftover site records safely, idempotently, and refuses to destroy data.

The retired names are assembled from fragments so this file is not itself a reference to the
retired module.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_APP = Path(__file__).resolve().parents[1]
_PKG = "tender_" + "configurations"
_MODULE = "Tender " + "Configurations"
_PATCH = "kentender_procurement.patches.drop_retired_" + _PKG


class TestRetiredTenderConfigurationsGone(IntegrationTestCase):
	def test_python_package_is_gone(self):
		self.assertIsNone(importlib.util.find_spec(f"kentender_procurement.{_PKG}"))
		self.assertFalse((_APP / _PKG).exists())

	def test_publication_endpoints_are_not_routable(self):
		for method in (
			"publish_tender",
			"approve_tender_configuration_for_preview",
			"return_publication_for_correction",
			"get_tender_configuration_review",
			"confirm_tender_package",
		):
			with self.assertRaises((ImportError, AttributeError, frappe.DoesNotExistError)):
				frappe.get_attr(f"kentender_procurement.{_PKG}.{method}")
			with self.assertRaises((ImportError, AttributeError, frappe.DoesNotExistError)):
				frappe.get_attr(f"kentender_procurement.{_PKG}.api.{method}")

	def test_no_module_registration_remains(self):
		modules = (_APP / "modules.txt").read_text().splitlines()
		self.assertNotIn(_MODULE, [m.strip() for m in modules])
		# the drop patch is the only registered patch that may name the retired package
		for line in (_APP / "patches.txt").read_text().splitlines():
			if _PKG in line or "bw" + "mf" in line.lower():
				self.assertEqual(line.strip(), _PATCH)

	def test_no_page_or_asset_directories_remain(self):
		page_dir = _APP / "kentender_procurement" / "page"
		leftovers = sorted(
			p.name
			for p in page_dir.iterdir()
			if p.is_dir()
			and (
				p.name.startswith(("it_tender_", "it_std_wizard"))
				or p.name in ("publications", "publication_setup")
			)
		)
		self.assertEqual(leftovers, [])
		js_dir = _APP / "public" / "js"
		self.assertEqual(
			sorted(p.name for p in js_dir.glob("it_tender_*")) + sorted(p.name for p in js_dir.glob("it_std_wizard*")),
			[],
		)
		for name in ("publication_setup_page.js", "publications_page.js"):
			self.assertFalse((js_dir / name).exists(), name)

	def test_hooks_register_no_retired_page_asset_or_file_guard(self):
		hooks = (_APP / "hooks.py").read_text().lower()
		for needle in ("it-tender", "it_tender", "it-std-wizard", "publication-setup", "publications_page", _PKG, "bw" + "mf"):
			self.assertNotIn(needle, hooks, needle)
		self.assertNotIn("File", frappe.get_hooks("doc_events", app_name="kentender_procurement", default={}) or {})

	def test_no_retired_doctype_remains_on_this_site(self):
		patch = importlib.import_module(_PATCH)
		for doctype in patch.RETIRED_DOCTYPES:
			self.assertFalse(frappe.db.exists("DocType", doctype), doctype)
		self.assertFalse(frappe.db.exists("Module Def", _MODULE))
		for page in patch.RETIRED_PAGES:
			self.assertFalse(frappe.db.exists("Page", page), page)


class TestDropRetiredTenderConfigurationsPatch(IntegrationTestCase):
	"""The drop patch is guarded and safe to run twice, including on a clean site."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.patch = importlib.import_module(_PATCH)

	def test_names_cover_every_doctype_directory_the_module_had(self):
		# 3 named doctypes + 37 framework doctypes; nothing else may be dropped by this patch.
		self.assertEqual(len(self.patch.RETIRED_DOCTYPES), 40)
		self.assertEqual(len(set(self.patch.RETIRED_DOCTYPES)), 40)
		self.assertEqual(len([d for d in self.patch.RETIRED_DOCTYPES if d.startswith("BW" + "MF ")]), 37)

	def test_runs_twice_on_a_site_where_everything_is_already_gone(self):
		self.patch.execute()
		self.patch.execute()
		for doctype in self.patch.RETIRED_DOCTYPES:
			self.assertFalse(frappe.db.exists("DocType", doctype), doctype)
			self.assertFalse(frappe.db.table_exists(doctype), doctype)
		for page in self.patch.RETIRED_PAGES:
			self.assertFalse(frappe.db.exists("Page", page), page)

	def _leave_empty_records(self, doctype: str, page: str):
		self.addCleanup(self._clean_leftovers, doctype, page)
		frappe.db.sql_ddl(f"create table if not exists `tab{doctype}` (name varchar(140) primary key)")
		if not frappe.db.exists("DocType", doctype):
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
			"values (%s, %s, 'DocType', 'fields', 'title', 'Data', 1) on duplicate key update fieldname = fieldname",
			(f"{doctype}-title-leftover", doctype),
		)
		if not frappe.db.exists("Page", page):
			frappe.get_doc(
				{"doctype": "Page", "name": page, "page_name": page, "title": page, "module": "Kentender Procurement", "standard": "No"}
			).db_insert()

	def _clean_leftovers(self, doctype: str, page: str):
		frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")
		self.patch.execute()

	def test_removes_leftover_records_tables_and_pages_then_is_a_no_op(self):
		doctype = self.patch.RETIRED_DOCTYPES[0]
		page = self.patch.RETIRED_PAGES[0]
		self._leave_empty_records(doctype, page)

		self.assertTrue(frappe.db.exists("DocType", doctype))
		self.patch.execute()
		self.assertFalse(frappe.db.exists("DocType", doctype))
		self.assertFalse(frappe.db.table_exists(doctype))
		self.assertFalse(frappe.db.exists("DocField", {"parent": doctype}))
		self.assertFalse(frappe.db.exists("Page", page))

		self.patch.execute()  # second run: nothing left to do, nothing raised
		self.assertFalse(frappe.db.exists("DocType", doctype))

	def test_refuses_when_a_retired_table_still_holds_rows(self):
		doctype = self.patch.RETIRED_DOCTYPES[-1]
		page = self.patch.RETIRED_PAGES[-1]
		self._leave_empty_records(doctype, page)
		frappe.db.sql(f"insert into `tab{doctype}` (name) values ('keep-me')")

		with self.assertRaises(frappe.ValidationError):
			self.patch.execute()

		# nothing was dropped: the data and its metadata are still there for a human to decide
		self.assertTrue(frappe.db.table_exists(doctype))
		self.assertTrue(frappe.db.sql(f"select 1 from `tab{doctype}` where name = 'keep-me'"))
		self.assertTrue(frappe.db.exists("DocType", doctype))
		self.assertTrue(frappe.db.exists("Page", page))

		frappe.db.sql(f"delete from `tab{doctype}`")  # the cleanup run can now proceed

	def test_refuses_when_the_content_store_folder_holds_files(self):
		folder = self.patch.CAS_FOLDER
		self.addCleanup(self._remove_cas_rows)
		frappe.db.sql(
			"insert into `tabFile` (name, file_name, is_folder, folder, creation, modified) "
			"values (%s, 'BW' 'MF-CAS', 1, 'Home', now(), now()) on duplicate key update is_folder = 1",
			(folder,),
		)
		frappe.db.sql(
			"insert into `tabFile` (name, file_name, is_folder, folder, creation, modified) "
			"values ('tc-guard-test-file', 'tc-guard-test-file', 0, %s, now(), now())",
			(folder,),
		)
		with self.assertRaises(frappe.ValidationError):
			self.patch.execute()
		self.assertTrue(frappe.db.exists("File", "tc-guard-test-file"))

	def _remove_cas_rows(self):
		frappe.db.sql("delete from `tabFile` where name = 'tc-guard-test-file'")
		self.patch.execute()

	def test_leaves_a_role_somebody_holds(self):
		role = self.patch.RETIRED_ROLES[0]
		self.addCleanup(self._remove_role_rows, role)
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
		user = frappe.db.get_value("User", {"name": ["not in", ("Guest",)]}, "name")
		frappe.get_doc({"doctype": "Has Role", "parent": user, "parenttype": "User", "parentfield": "roles", "role": role}).db_insert()
		self.patch.execute()
		self.assertTrue(frappe.db.exists("Role", role))

	def _remove_role_rows(self, role: str):
		frappe.db.delete("Has Role", {"role": role})
		self.patch.execute()
