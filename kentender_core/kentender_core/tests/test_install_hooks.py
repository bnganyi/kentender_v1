# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Frappe's create_desktop_icons() emits one Desk tile per public Workspace.

KenTender ships its own tiles as fixtures (Procurement, Tenders); the module
Workspaces behind them are reached from inside that shell, so an
auto-generated tile for one is duplicate navigation scattered across the
Desk. These tests hold both halves of that line: the auto-generated tiles
stay hidden, and the shipped fixtures are never touched by the sweep.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.install import (
	_ensure_default_pe_types,
	_hide_auto_generated_module_desktop_icons,
	after_migrate,
)


def _kentender_workspaces() -> list[str]:
	modules = frappe.get_all(
		"Module Def", filters={"app_name": ("like", "kentender%")}, pluck="name"
	)
	if not modules:
		return []
	return frappe.get_all("Workspace", filters={"module": ("in", modules)}, pluck="name")


class TestDesktopIconHygiene(IntegrationTestCase):
	def test_no_auto_generated_kentender_workspace_tile_is_visible(self):
		_hide_auto_generated_module_desktop_icons()
		workspaces = _kentender_workspaces()
		self.assertTrue(workspaces, "expected at least one KenTender Workspace on site")
		visible = frappe.get_all(
			"Desktop Icon",
			filters={"link_to": ("in", workspaces), "standard": 0, "hidden": 0},
			pluck="label",
		)
		self.assertEqual(visible, [], f"auto-generated Desk tiles left visible: {visible}")

	def test_shipped_procurement_tile_survives_the_sweep(self):
		"""The sweep must key off standard=0, never a label list — hiding the
		shipped entry tile would strand every user on an empty Desk."""
		if not frappe.db.exists("Desktop Icon", "Procurement"):
			self.skipTest("Procurement Desktop Icon not on site")
		_hide_auto_generated_module_desktop_icons()
		self.assertEqual(
			int(frappe.db.get_value("Desktop Icon", "Procurement", "hidden") or 0), 0
		)

	def test_sweep_is_idempotent_and_creates_nothing(self):
		before = frappe.db.count("Desktop Icon")
		_hide_auto_generated_module_desktop_icons()
		_hide_auto_generated_module_desktop_icons()
		self.assertEqual(frappe.db.count("Desktop Icon"), before)


class TestInstallHooksAreRerunnable(IntegrationTestCase):
	"""after_migrate runs on *every* `bench migrate`, so anything that is not
	idempotent aborts the migrate on the second run. An earlier guard used the
	single-argument `frappe.db.exists("PE Type")`, which asks whether a DocType
	of that name exists rather than whether the table holds rows — it stayed
	falsy against a populated catalogue and re-inserted, raising
	DuplicateEntryError."""

	def test_default_pe_types_do_not_reinsert_when_catalogue_is_populated(self):
		_ensure_default_pe_types()
		self.assertTrue(frappe.db.count("PE Type"), "expected a seeded PE Type catalogue")
		before = frappe.db.count("PE Type")
		_ensure_default_pe_types()  # must not raise DuplicateEntryError
		self.assertEqual(frappe.db.count("PE Type"), before)

	def test_after_migrate_survives_being_run_twice(self):
		after_migrate()
		after_migrate()
