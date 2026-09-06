"""AUTH-ADR-001 v1.6 §4.2–§4.3 — the site-local Organisation Unit tree.

Covers the acceptance rows that depend on the hierarchy itself:

- AUTH-AC-005 one parent-OU assignment covers its descendants and never a
  sibling outside that subtree;
- AUTH-AC-006 assignment to a leaf covers only that leaf;
- AUTH-AC-020 exactly one root exists and the tree carries no
  `procuring_entity` contract.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_organisation_unit_tree
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.authorization import descendants_of
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge


class TestOrganisationUnitTree(IntegrationTestCase):
	"""One directorate with two branches, plus an unrelated sibling — all
	beneath the site's single root."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Project Owner rule: test data never stays in the database. Runs
		# after tearDownClass, and deletes only by the KT Test / kt.test
		# patterns this module's fixtures construct.
		cls.addClassCleanup(purge)
		cls.root = fx.ensure_site_configured()
		cls.directorate = fx.unit("KT Test Directorate")
		cls.branch_one = fx.unit("KT Test Branch One", cls.directorate)
		cls.branch_two = fx.unit("KT Test Branch Two", cls.directorate)
		cls.sibling = fx.unit("KT Test Sibling")
		frappe.db.commit()

	def test_the_doctype_is_a_nested_set_keyed_on_parent_organisation_unit(self):
		meta = frappe.get_meta("Organisation Unit")
		self.assertTrue(meta.is_tree)
		self.assertEqual(meta.nsm_parent_field, "parent_organisation_unit")
		for fieldname in ("lft", "rgt", "old_parent"):
			self.assertTrue(meta.has_field(fieldname), f"{fieldname} is required by the nested set")

	def test_every_node_has_a_stamped_range(self):
		for name in (self.root, self.directorate, self.branch_one, self.branch_two, self.sibling):
			bounds = frappe.db.get_value("Organisation Unit", name, ["lft", "rgt"], as_dict=True)
			self.assertTrue(bounds.lft, f"{name} has no lft")
			self.assertGreater(bounds.rgt, bounds.lft, f"{name} range is not well formed")

	def test_exactly_one_root_exists(self):
		"""AUTH-AC-020 — a second parentless unit is refused."""
		roots = frappe.get_all(
			"Organisation Unit",
			filters={"parent_organisation_unit": ("is", "not set")},
			pluck="name",
		)
		self.assertEqual(roots, [self.root])
		doc = frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": "KT-TEST-SECOND-ROOT",
				"unit_name": "KT Test Second Root",
				"status": "Active",
				"fixture_namespace": "KT_TEST",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_a_directorate_covers_its_branches(self):
		"""AUTH-AC-005 — one assignment at the directorate reaches both branches."""
		self.assertEqual(
			descendants_of({self.directorate}),
			{self.directorate, self.branch_one, self.branch_two},
		)

	def test_a_leaf_covers_only_itself(self):
		"""AUTH-AC-006 — a leaf assignment never widens to its parent or sibling."""
		self.assertEqual(descendants_of({self.branch_one}), {self.branch_one})

	def test_a_subtree_never_reaches_a_sibling_subtree(self):
		self.assertNotIn(self.sibling, descendants_of({self.directorate}))

	def test_the_root_covers_the_whole_site(self):
		covered = descendants_of({self.root})
		for name in (self.directorate, self.branch_one, self.branch_two, self.sibling):
			self.assertIn(name, covered)

	def test_the_contract_has_no_required_procuring_entity(self):
		"""§1.1 — the PE field is deprecated: hidden, read-only, never required.

		The physical column survives for pre-cutover module readers (tracker
		D2) and is dropped in the removal phase."""
		meta = frappe.get_meta("Organisation Unit")
		field = meta.get_field("procuring_entity")
		if field is not None:
			self.assertFalse(field.reqd)
			self.assertTrue(field.hidden)
			self.assertTrue(field.read_only)

	def test_a_unit_cannot_be_its_own_parent(self):
		doc = frappe.get_doc("Organisation Unit", self.branch_two)
		doc.parent_organisation_unit = doc.name
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_reparenting_restamps_the_ranges(self):
		"""Framework behaviour the descendant rule depends on; the product UI
		offers no reparent (AUTH-AC-023), but the ranges must stay truthful."""
		moved = fx.unit("KT Test Moved", self.directorate)
		self.assertIn(moved, descendants_of({self.directorate}))

		doc = frappe.get_doc("Organisation Unit", moved)
		doc.parent_organisation_unit = self.sibling
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		self.assertNotIn(moved, descendants_of({self.directorate}))
		self.assertIn(moved, descendants_of({self.sibling}))

	def test_unit_codes_are_generated_from_the_site_code(self):
		"""CFG v0.6 §4.3 — `OU-{pe_code_suffix}-{sequence}`."""
		self.assertRegex(self.directorate, r"^OU-MOH-\d{5}$")
