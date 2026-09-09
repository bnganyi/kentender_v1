# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.3 — the registry: one row after two installs
(TPR-AC-032), a tampered bundle makes the template unavailable and a new
binding refused (TPR-AC-033, SMOKE-14), and nothing but the installer may
write the row (TPR-AC-034)."""

from __future__ import annotations

import os
import shutil
import tempfile

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_templates import loader, registry


def _copy_bundle() -> str:
	tmp = tempfile.mkdtemp(prefix="tpr-bundle-")
	root = os.path.join(tmp, loader.BUNDLE_DIRNAME)
	shutil.copytree(loader.DEFAULT_BUNDLE_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
	return root


class RegistryCase(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(registry.install)  # leave the site on the shipped bundle


class TestInstall(RegistryCase):
	def test_two_installs_leave_exactly_one_available_row(self):
		first = registry.install()
		second = registry.install()
		self.assertTrue(first["ok"] and second["ok"], (first, second))
		rows = frappe.get_all(registry.REGISTRY_DOCTYPE, filters={"template_key": "IT-EQUIPMENT-OPEN-V1", "template_version": "1.1"}, pluck="name")
		self.assertEqual(rows, [registry.registry_name()])
		doc = frappe.get_doc(registry.REGISTRY_DOCTYPE, rows[0])
		self.assertEqual(doc.availability, registry.AVAILABLE)
		self.assertEqual(doc.official_source_digest, "95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee")
		self.assertEqual(doc.bundle_digest, loader.bundle_digest())
		self.assertFalse(second["created"])

	def test_resolve_returns_the_exact_installed_release(self):
		registry.install()
		resolved = registry.resolve()
		self.assertEqual(resolved["template_key"], "IT-EQUIPMENT-OPEN-V1")
		self.assertEqual(resolved["template_version"], "1.1")
		self.assertEqual(resolved["bundle_digest"], loader.bundle_digest())

	def test_a_tampered_bundle_installs_as_unavailable_and_refuses_binding(self):
		root = _copy_bundle()
		with open(os.path.join(root, "templates", "invitation_to_tender.html"), "a", encoding="utf-8") as fh:
			fh.write("<!-- tampered -->")
		result = registry.install(bundle_root=root)
		self.assertFalse(result["ok"])
		self.assertEqual(result["availability"], registry.UNAVAILABLE)
		with self.assertRaises(TenderPreparationError) as ctx:
			registry.resolve(bundle_root=root)
		self.assertEqual(ctx.exception.code, "TPR_TEMPLATE_UNAVAILABLE")

	def test_a_bundle_altered_after_installation_is_refused_at_resolve(self):
		"""SMOKE-14 — the row still says Available; the live re-verification
		catches the drift before any Tender binds it."""
		registry.install()
		root = _copy_bundle()
		with open(os.path.join(root, "templates", "print.css"), "a", encoding="utf-8") as fh:
			fh.write("/* tampered */")
		with self.assertRaises(TenderPreparationError) as ctx:
			registry.resolve(bundle_root=root)
		self.assertEqual(ctx.exception.code, "TPR_TEMPLATE_UNAVAILABLE")

	def test_nobody_edits_the_row_outside_the_installer(self):
		registry.install()
		doc = frappe.get_doc(registry.REGISTRY_DOCTYPE, registry.registry_name())
		doc.display_name = "Edited by hand"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(registry.REGISTRY_DOCTYPE, registry.registry_name(), ignore_permissions=True)
