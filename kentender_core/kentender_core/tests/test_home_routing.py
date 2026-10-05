"""HOME-CHG-001 v0.6 §9, plan Phase 6 — `/app/home` and the landing page.

Run:
  bench --site kentender-test.local run-tests --app kentender_core \\
    --module kentender_core.tests.test_home_routing
"""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.tests import IntegrationTestCase

from kentender_core import install
from kentender_core.services import my_work
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

ERPNEXT = os.path.join(frappe.get_app_path("erpnext"))
WORKSPACE_JSON = os.path.join(ERPNEXT, "setup", "workspace", "home", "home.json")
ICON_JSON = os.path.join(ERPNEXT, "desktop_icon", "home.json")
SIDEBAR_JSON = os.path.join(ERPNEXT, "workspace_sidebar", "home.json")


class TestLanding(IntegrationTestCase):
	"""Home is the internal landing page (owner decision OD-2) once its Page exists."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		fx.ensure_site_configured()
		cls.internal = fx.user("land.internal", "Land Internal")
		cls.website = frappe.get_doc({"doctype": "User", "email": "kt.test.land.website@example.test", "first_name": "Land Website", "send_welcome_email": 0, "user_type": "Website User", "enabled": 1}).insert(ignore_permissions=True).name
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")

	def landing(self, user, *, page=True, assigned=False):
		frappe.set_user(user)
		boot = frappe._dict(home_page="desktop")
		with patch.object(my_work, "_home_page_exists", return_value=page), patch.object(my_work, "_assignments", return_value=[object()] if assigned else []):
			my_work.patch_bootinfo_home(boot)
		return boot.home_page

	def test_an_internal_user_with_an_operational_assignment_lands_on_home(self):
		self.assertEqual(self.landing(self.internal, assigned=True), "home")

	def test_an_internal_user_with_no_assignment_lands_on_home_too(self):
		self.assertEqual(self.landing(self.internal), "home")

	def test_a_technical_reader_lands_on_home(self):
		# Home shows technical readers the orientation, the Technical record search link and no business action.
		self.assertEqual(self.landing("Administrator"), "home")

	def test_a_website_user_is_left_alone(self):
		self.assertEqual(self.landing(self.website), "desktop")

	def test_a_guest_is_left_alone(self):
		self.assertEqual(self.landing("Guest"), "desktop")

	def test_before_the_page_exists_nobody_is_sent_to_a_page_that_is_not_there(self):
		# My Work is retired (HOME6-0607): with no Home page there is no landing page of ours at all
		self.assertEqual(self.landing(self.internal, page=False, assigned=True), "desktop")
		self.assertEqual(self.landing(self.internal, page=False), "desktop")
		self.assertEqual(self.landing("Administrator", page=False), "desktop")

	def test_the_page_check_is_a_real_lookup_of_the_home_page(self):
		with patch.object(my_work.frappe.db, "exists", return_value=True) as exists:
			self.assertTrue(my_work._home_page_exists())
		exists.assert_called_once_with("Page", "home")


class TestRetireErpnextHome(IntegrationTestCase):
	"""ERPNext's own `Home` workspace takes `/app/home` before any Page and, for Administrator and System Manager,
	hiding it is not enough: Frappe lists hidden workspaces for anyone who can manage workspaces (FU-HOME-34).
	ERPNext re-imports its JSON on every migrate, so removal runs after every migrate and must be idempotent."""

	@staticmethod
	def _insert_from_json(path):
		"""ERPNext's own record, inserted exactly as its JSON states (the flat `workspace_sidebar/` and
		`desktop_icon/` exports are loaded by Frappe's sync, not by `import_file_by_path`)."""
		with open(path, encoding="utf-8") as f:
			doc = frappe.get_doc(json.load(f))
		doc.flags.ignore_permissions = True
		# in_import: a developer-mode save would re-export the record over ERPNext's own file
		frappe.flags.in_import = True
		try:
			doc.insert()
		finally:
			frappe.flags.in_import = False

	def setUp(self):
		frappe.set_user("Administrator")
		# Clear with the retire function, never `frappe.delete_doc`: in developer mode that deletes the exported
		# file, which is ERPNext's, not ours (it did, twice, on 5 Oct 2026).
		install.retire_erpnext_home_workspace()
		import_file_by_path(WORKSPACE_JSON, force=True)  # the real ERPNext records, as a migrate leaves them
		self._insert_from_json(SIDEBAR_JSON)
		self._insert_from_json(ICON_JSON)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		install.retire_erpnext_home_workspace()  # leave the site as the migrate hook leaves it
		frappe.db.commit()
		super().tearDownClass()

	def test_the_records_exist_before_and_are_gone_after(self):
		self.assertTrue(frappe.db.exists("Workspace", "Home"))
		removed = install.retire_erpnext_home_workspace()
		self.assertFalse(frappe.db.exists("Workspace", "Home"))
		self.assertFalse(frappe.db.exists("Workspace Sidebar", "Home"))
		self.assertFalse(frappe.db.exists("Desktop Icon", "Home"))
		self.assertEqual(sorted(removed), ["Desktop Icon", "Workspace", "Workspace Sidebar"])

	def test_it_is_idempotent(self):
		install.retire_erpnext_home_workspace()
		self.assertEqual(install.retire_erpnext_home_workspace(), {})

	def test_a_home_workspace_owned_by_another_app_is_not_touched(self):
		frappe.db.set_value("Workspace", "Home", "app", "kentender_core", update_modified=False)
		self.assertEqual(install.retire_erpnext_home_workspace().get("Workspace"), None)
		self.assertTrue(frappe.db.exists("Workspace", "Home"))

	def test_it_never_deletes_erpnexts_own_exported_files(self):
		"""On a developer-mode site Frappe deletes a standard record's exported JSON when the record is deleted. Run
		on every migrate, that would delete files out of the ERPNext app directory (found 5 Oct 2026: it did)."""
		files = (WORKSPACE_JSON, SIDEBAR_JSON, ICON_JSON)
		for path in files:
			self.assertTrue(os.path.exists(path), path)
		with patch.dict(frappe.conf, {"developer_mode": 1}):
			install.retire_erpnext_home_workspace()
			self.assertEqual(frappe.conf.developer_mode, 1, "developer_mode is put back as it was")
		for path in files:
			self.assertTrue(os.path.exists(path), f"{path} was deleted")

	def test_the_page_named_home_is_not_removed(self):
		self.assertTrue(frappe.db.exists("Page", "home"))
		install.retire_erpnext_home_workspace()
		self.assertTrue(frappe.db.exists("Page", "home"))

	def test_the_home_slug_no_longer_resolves_to_a_workspace_for_a_workspace_manager(self):
		from frappe.desk.desktop import get_workspace_sidebar_items

		install.retire_erpnext_home_workspace()
		frappe.clear_cache()
		names = [page["name"] for page in get_workspace_sidebar_items().get("pages", [])]
		self.assertNotIn("Home", names)

	def test_the_migrate_hook_runs_it(self):
		steps = ["repair_module_defs", "_ensure_user_kt_scope_fields", "_hide_auto_generated_module_desktop_icons", "_ensure_default_pe_types", "_ensure_business_role_projections", "_ensure_fiscal_year_flag_fields"]
		patches = [patch.object(install, step) for step in steps]
		for p in patches:
			p.start()
			self.addCleanup(p.stop)
		with patch.object(install, "retire_erpnext_home_workspace") as retire:
			install.after_migrate()
		retire.assert_called_once_with()
