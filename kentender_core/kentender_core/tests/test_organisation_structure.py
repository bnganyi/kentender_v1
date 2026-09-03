"""AUTH-ADR-001 v1.6 §9.2/§14.1 — the Organisation structure section's service.

Covers AUTH-AC-023..025 and the §13.9 states: the tree projection with its
explicit states, server-decided actions, add/rename/deactivate/reactivate,
sibling uniqueness after normalisation, concurrency, and the governed root
repair (owned by site_configuration).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_organisation_structure
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import organisation_structure as structure
from kentender_core.services import site_configuration as configuration
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge


class StructureTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		cls.root = fx.ensure_site_configured()
		cls.directorate = fx.unit("KT Test OS Directorate")
		cls.leaf = fx.unit("KT Test OS Leaf", cls.directorate)
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")


class TestReads(StructureTestCase):
	def test_the_projection_is_ready_with_the_root_first(self):
		out = structure.get_organisation_structure()
		self.assertEqual(out["state"], "ready")
		self.assertEqual(out["root"], self.root)
		self.assertEqual(out["tree"][0]["id"], self.root)
		self.assertTrue(out["tree"][0]["is_root"])

	def test_the_projection_never_exposes_nested_set_internals(self):
		"""AUTH-AC-025 — names, codes, status, hierarchy; never lft/rgt/parent ids."""
		out = structure.get_organisation_structure()

		def walk(nodes):
			for node in nodes:
				for banned in ("lft", "rgt", "old_parent", "parent_organisation_unit", "procuring_entity"):
					self.assertNotIn(banned, node)
				walk(node["children"])

		walk(out["tree"])

	def test_selection_falls_back_to_the_root_for_an_unknown_unit(self):
		out = structure.get_organisation_structure(selected="OU-DOES-NOT-EXIST")
		self.assertEqual(out["selected"]["id"], self.root)

	def test_detail_reports_path_coverage_and_server_decided_actions(self):
		detail = structure.get_unit_detail(self.directorate)
		self.assertEqual(detail["path"][-1], "KT Test OS Directorate")
		self.assertEqual(detail["descendant_count"], 1)
		self.assertEqual(
			detail["actions"],
			{"add_child": True, "rename": True, "deactivate": True, "reactivate": False},
		)

	def test_the_root_detail_offers_no_rename_or_deactivate(self):
		detail = structure.get_unit_detail(self.root)
		self.assertTrue(detail["is_root"])
		self.assertFalse(detail["actions"]["rename"])
		self.assertFalse(detail["actions"]["deactivate"])

	def test_an_ordinary_user_is_refused(self):
		actor = fx.user("os.ordinary")
		frappe.db.commit()
		frappe.set_user(actor)
		try:
			with self.assertRaises(ResponsibilityError) as caught:
				structure.get_organisation_structure()
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(self.code(caught), "AUTH_RESPONSIBILITY_REQUIRED")


class TestAddUnit(StructureTestCase):
	def test_add_creates_beneath_the_selected_parent_with_a_generated_code(self):
		result = structure.add_organisation_unit(parent_id=self.directorate, name="KT Test OS Added")
		self.assertTrue(result["created"])
		self.assertRegex(result["unit"], r"^OU-MOH-\d{5}$")
		row = frappe.db.get_value(
			"Organisation Unit", result["unit"], ["parent_organisation_unit", "status"], as_dict=True
		)
		self.assertEqual(row.parent_organisation_unit, self.directorate)
		self.assertEqual(row.status, "Active")

	def test_add_defaults_to_the_root_when_no_parent_is_selected(self):
		result = structure.add_organisation_unit(name="KT Test OS Rootward")
		parent = frappe.db.get_value("Organisation Unit", result["unit"], "parent_organisation_unit")
		self.assertEqual(parent, self.root)

	def test_a_normalised_duplicate_sibling_returns_the_existing_unit(self):
		"""§4.2 — unique among active siblings after normalised comparison."""
		first = structure.add_organisation_unit(parent_id=self.directorate, name="KT Test OS Dup")
		again = structure.add_organisation_unit(parent_id=self.directorate, name="  kt   test os DUP ")
		self.assertFalse(again["created"])
		self.assertEqual(again["unit"], first["unit"])

	def test_an_inactive_parent_refuses_a_new_child(self):
		inactive = fx.unit("KT Test OS Inactive Parent")
		structure.set_organisation_unit_active(unit_id=inactive, active=False)
		with self.assertRaises(ResponsibilityError) as caught:
			structure.add_organisation_unit(parent_id=inactive, name="KT Test OS Child")
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_a_too_short_name_is_refused(self):
		with self.assertRaises(ResponsibilityError) as caught:
			structure.add_organisation_unit(parent_id=self.directorate, name="K")
		self.assertEqual(self.code(caught), "AUTH_CONFIGURATION_INVALID")


class TestRenameAndActivation(StructureTestCase):
	def test_rename_changes_the_display_name_only(self):
		unit = fx.unit("KT Test OS Rename Me", self.directorate)
		before_code = frappe.db.get_value("Organisation Unit", unit, "unit_code")
		structure.rename_organisation_unit(unit_id=unit, name="KT Test OS Renamed")
		row = frappe.db.get_value("Organisation Unit", unit, ["unit_code", "unit_name"], as_dict=True)
		self.assertEqual(row.unit_code, before_code)
		self.assertEqual(row.unit_name, "KT Test OS Renamed")

	def test_the_root_cannot_be_renamed(self):
		with self.assertRaises(ResponsibilityError) as caught:
			structure.rename_organisation_unit(unit_id=self.root, name="KT Test OS New Root Name")
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_rename_refuses_a_normalised_sibling_clash(self):
		one = fx.unit("KT Test OS Clash One", self.directorate)
		fx.unit("KT Test OS Clash Two", self.directorate)
		with self.assertRaises(ResponsibilityError) as caught:
			structure.rename_organisation_unit(unit_id=one, name="kt test os clash TWO")
		self.assertEqual(self.code(caught), "AUTH_CONFIGURATION_INVALID")

	def test_a_stale_version_is_refused(self):
		unit = fx.unit("KT Test OS Stale", self.directorate)
		with self.assertRaises(ResponsibilityError) as caught:
			structure.rename_organisation_unit(
				unit_id=unit, name="KT Test OS Stale Renamed", expected_version="2000-01-01 00:00:00"
			)
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_deactivate_and_reactivate_round_trip(self):
		unit = fx.unit("KT Test OS Toggle", self.directorate)
		off = structure.set_organisation_unit_active(unit_id=unit, active=False)
		self.assertEqual(off["status"], "Inactive")
		on = structure.set_organisation_unit_active(unit_id=unit, active=True)
		self.assertEqual(on["status"], "Active")

	def test_the_root_cannot_be_deactivated(self):
		with self.assertRaises(ResponsibilityError) as caught:
			structure.set_organisation_unit_active(unit_id=self.root, active=False)
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_a_parent_with_active_children_cannot_be_deactivated(self):
		with self.assertRaises(ResponsibilityError) as caught:
			structure.set_organisation_unit_active(unit_id=self.directorate, active=False)
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_a_child_cannot_be_reactivated_under_an_inactive_parent(self):
		parent = fx.unit("KT Test OS Frozen Parent")
		child = fx.unit("KT Test OS Frozen Child", parent)
		structure.set_organisation_unit_active(unit_id=child, active=False)
		structure.set_organisation_unit_active(unit_id=parent, active=False)
		with self.assertRaises(ResponsibilityError) as caught:
			structure.set_organisation_unit_active(unit_id=child, active=True)
		self.assertEqual(self.code(caught), "AUTH_STATE_CHANGED")

	def test_deactivation_is_never_a_delete(self):
		"""AUTH-AC-023 — the record and its history remain."""
		unit = fx.unit("KT Test OS Keep", self.directorate)
		structure.set_organisation_unit_active(unit_id=unit, active=False)
		self.assertTrue(frappe.db.exists("Organisation Unit", unit))


class TestZRootRepair(StructureTestCase):
	"""Runs last (class name). The destructive case self-heals through the
	governed repair inside the same test, because this runner keeps state
	between tests — a broken tree must never be left for another suite."""

	def test_repair_with_an_existing_root_changes_nothing(self):
		result = configuration.repair_organisation_root()
		self.assertFalse(result["created"])
		self.assertEqual(result["id"], self.root)

	def test_z_missing_root_reports_needs_repair_then_the_governed_repair_heals(self):
		"""§13.9 + CFG-AC-022 — never an empty successful tree; the repair
		recreates the root and adopts every orphaned subtree top."""
		children = frappe.get_all(
			"Organisation Unit",
			filters={"parent_organisation_unit": self.root},
			pluck="name",
		)
		# The realistic corruption: the root row is gone and its children
		# dangle (their parent link points at a missing record).
		frappe.db.sql("delete from `tabOrganisation Unit` where name = %s", self.root)
		frappe.clear_cache(doctype="Organisation Unit")

		out = structure.get_organisation_structure()
		self.assertEqual(out["state"], "needs_repair")
		self.assertEqual(out["tree"], [])

		result = configuration.repair_organisation_root()
		self.assertTrue(result["created"])
		self.assertEqual(result["adopted"], len(children))
		root_row = frappe.db.get_value(
			"Organisation Unit", result["id"], ["unit_code"], as_dict=True
		)
		self.assertEqual(root_row.unit_code, fx.SITE_PE_CODE)
		healed = structure.get_organisation_structure()
		self.assertEqual(healed["state"], "ready")
		frappe.db.commit()
