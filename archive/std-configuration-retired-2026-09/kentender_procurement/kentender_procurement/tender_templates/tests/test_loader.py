# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.3 — the bundle loader: manifest verification, the
official-source digest, register integrity, and refusal of a missing,
altered or unlisted file (TPR-AC-031/033). Tamper cases copy the bundle to a
temporary root; the shipped bundle is never modified."""

from __future__ import annotations

import os
import shutil
import tempfile

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_templates import loader


def _copy_bundle() -> str:
	tmp = tempfile.mkdtemp(prefix="tpr-bundle-")
	root = os.path.join(tmp, loader.BUNDLE_DIRNAME)
	shutil.copytree(loader.DEFAULT_BUNDLE_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
	return root


class TestShippedBundle(IntegrationTestCase):
	def test_the_shipped_bundle_verifies(self):
		v = loader.verify()
		self.assertTrue(v.ok, v.summary())
		self.assertEqual(v.source_digest, "95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee")
		self.assertTrue(v.bundle_digest)

	def test_metadata_names_the_release(self):
		meta = loader.metadata()
		self.assertEqual(meta["template_key"], "IT-EQUIPMENT-OPEN-V1")
		self.assertEqual(meta["template_version"], "1.1")
		self.assertEqual(meta["handoff_version"], "1.3")
		self.assertEqual(meta["supported_reservation_categories"], ["None", "Youth", "Women", "Persons with disabilities", "Other disadvantaged group"])

	def test_the_manifest_matches_the_files_on_disk(self):
		self.assertEqual(loader.read_manifest(), {line.split("  ", 1)[1].strip(): line.split("  ", 1)[0] for line in loader.compute_manifest_text().splitlines()})

	def test_the_bundle_is_a_byte_copy_of_the_curation_workspace_when_present(self):
		"""Plan D1 — the copy is pinned to the workspace's candidate manifest."""
		workspace = os.path.abspath(os.path.join(loader.DEFAULT_BUNDLE_ROOT, "..", "..", "..", "..", "docs", "mvp-1-r1", "07_tender_templates", "it_equipment_open_v1"))
		if not os.path.isdir(workspace):
			self.skipTest("curation workspace not present on this checkout")
		pairs = (
			("templates/invitation_to_tender.html", "02_master/invitation_to_tender.html"),
			("templates/complete_tender.html", "02_master/complete_tender.html"),
			("templates/print.css", "02_master/print.css"),
			("coverage_register.csv", "03_registers/coverage_register.csv"),
			("insertion_points.csv", "03_registers/insertion_points.csv"),
			("forms_register.csv", "03_registers/forms_register.csv"),
			("fixtures/moh_input.json", "04_fixture/moh_input.json"),
			("fixtures/moh_expected.html", "04_fixture/moh_expected.html"),
			("fixtures/moh_invitation_expected.html", "04_fixture/moh_invitation_expected.html"),
			("source/ppra_goods_std_official.pdf", "01_source/ppra_goods_std_official.pdf"),
		)
		manifest = loader.read_manifest()
		for bundle_rel, workspace_rel in pairs:
			self.assertEqual(manifest[bundle_rel], loader._sha256_file(os.path.join(workspace, workspace_rel)), bundle_rel)


class TestTamper(IntegrationTestCase):
	def test_an_altered_byte_fails_verification(self):
		root = _copy_bundle()
		with open(os.path.join(root, "templates", "complete_tender.html"), "a", encoding="utf-8") as fh:
			fh.write("<!-- tampered -->")
		v = loader.verify(root)
		self.assertFalse(v.ok)
		self.assertIn("templates/complete_tender.html", v.mismatched)

	def test_a_missing_file_fails_verification(self):
		root = _copy_bundle()
		os.remove(os.path.join(root, "fixtures", "moh_input.json"))
		v = loader.verify(root)
		self.assertFalse(v.ok)
		self.assertIn("fixtures/moh_input.json", v.missing)

	def test_an_unlisted_file_fails_verification(self):
		root = _copy_bundle()
		with open(os.path.join(root, "templates", "extra.html"), "w", encoding="utf-8") as fh:
			fh.write("x")
		v = loader.verify(root)
		self.assertFalse(v.ok)
		self.assertIn("templates/extra.html", v.unlisted)

	def test_an_unresolved_register_row_fails_verification(self):
		root = _copy_bundle()
		path = os.path.join(root, "coverage_register.csv")
		text = open(path, encoding="utf-8").read().replace(",Reviewed,", ",Open,", 1)
		open(path, "w", encoding="utf-8").write(text)
		# re-list so the digest itself is not the failure being tested
		open(os.path.join(root, loader.MANIFEST_NAME), "w", encoding="utf-8").write(loader.compute_manifest_text(root))
		v = loader.verify(root)
		self.assertFalse(v.ok)
		self.assertTrue(any("unresolved" in p for p in v.register_problems), v.register_problems)
