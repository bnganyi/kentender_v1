# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §5, §16 — the fail-closed installer
(STI10-AC-001/002/003/014; TPL10-AC-003/009; owner decision OD5: an intact
release installs Available and switched On; checks and decisions are
evidence only)."""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler.canonical import pretty_json
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.release import bundle
from kentender_procurement.std_templates.services import installer
from kentender_procurement.std_templates.tests import support

DOCTYPE = "Installed STD Release"


class InstallerCase(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.release_ids: list[str] = []
		self.addCleanup(lambda: support.purge(self.release_ids))

	def package(self, **kw):
		root, info = support.make_test_package(**kw)
		self.release_ids.append(info["release_id"])
		self.addCleanup(lambda: support.cleanup_tmp(info))
		return root, info

	def install(self, root, **kw):
		# Test releases stay Off so they never compete with the site's own.
		kw.setdefault("site_switch", "Off")
		return installer.install_approved_std_release(str(root), installed_by="test", **kw)

	def assertRefused(self, code, root, **kw):
		files_before = frappe.db.count("File", {"attached_to_doctype": DOCTYPE})
		with self.assertRaises(STDTemplateError) as ctx:
			self.install(root, **kw)
		self.assertEqual(ctx.exception.code, code, ctx.exception)
		frappe.db.rollback()
		self.assertEqual(frappe.db.count("File", {"attached_to_doctype": DOCTYPE}), files_before, "a failed install left files")
		return ctx.exception


class TestInstall(InstallerCase):
	def test_valid_package_without_decision_installs_available_and_switched_on(self):
		root, info = self.package()
		result = self.install(root, site_switch="Off")
		frappe.db.commit()
		self.assertTrue(result["created"])
		self.assertEqual((result["lifecycle_status"], result["site_switch"]), ("Available", "Off"))
		doc = frappe.get_doc(DOCTYPE, info["release_id"])
		self.assertEqual(doc.bundle_digest, info["manifest"]["bundle_digest"])
		self.assertEqual(doc.manifest_digest, info["manifest_digest"])
		self.assertEqual(len(doc.assets), len(info["manifest"]["assets"]))
		for row in doc.assets[:5]:
			f = frappe.get_doc("File", row.private_file_id)
			self.assertTrue(f.is_private)
			self.assertEqual(frappe.utils.cstr(f.content_hash) and len(row.sha256_digest), 64)
		self.assertTrue(frappe.db.exists("Audit Event", {"document_type": DOCTYPE, "document_name": info["release_id"], "action": "Installed"}))
		self.assertEqual(doc.switched_by, "test")
		self.assertNotIn("Owner approval", [r["check"] for r in installer.load_json(doc.verification_results)])
		self.assertFalse([b for b in installer.load_json(doc.blockers) if "APPROVE" in b["summary"]])

	def test_install_switches_on_by_default(self):
		root, info = self.package(template_release="9.8-test")
		result = installer.install_approved_std_release(str(root), installed_by="test")
		frappe.db.commit()
		self.assertEqual((result["lifecycle_status"], result["site_switch"]), ("Available", "On"))
		self.assertEqual(frappe.db.get_value(DOCTYPE, info["release_id"], "site_switch"), "On")

	def test_switch_must_be_on_or_off(self):
		root, _ = self.package()
		with self.assertRaises(ValueError):
			self.install(root, site_switch="Maybe")
		frappe.db.rollback()

	def test_same_bytes_install_idempotently(self):
		root, info = self.package()
		self.install(root)
		frappe.db.commit()
		again = self.install(root)
		self.assertFalse(again["created"])
		self.assertEqual(frappe.db.count(DOCTYPE, {"release_id": info["release_id"]}), 1)

	def test_installed_release_is_immutable(self):
		root, info = self.package()
		self.install(root)
		frappe.db.commit()
		doc = frappe.get_doc(DOCTYPE, info["release_id"])
		doc.display_name = "Edited"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		frappe.db.rollback()
		doc = frappe.get_doc(DOCTYPE, info["release_id"])
		with self.assertRaises(frappe.ValidationError):
			doc.delete(ignore_permissions=True)

	def test_different_bytes_under_an_existing_identity_fail(self):
		root, info = self.package()
		self.install(root)
		frappe.db.commit()

		def mutate(pack: Path):
			path = pack / "04_fixture/package_index.md"
			path.write_text(path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

		other, other_info = support.make_test_package(release_id=info["release_id"], mutate=mutate)
		self.addCleanup(lambda: support.cleanup_tmp(other_info))
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", other)
		self.assertEqual(frappe.db.get_value(DOCTYPE, info["release_id"], "bundle_digest"), info["manifest"]["bundle_digest"])

	def test_same_template_release_under_another_identity_fails(self):
		root, info = self.package(template_release="9.8-test")
		self.install(root)
		frappe.db.commit()
		other, info2 = self.package(template_release="9.8-test")
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", other)


class TestFailClosed(InstallerCase):
	def test_undeclared_file_is_refused(self):
		root, _ = self.package(mutate=lambda p: (p / "04_fixture/extra.txt").write_text("x"), reseal_after_mutate=False)
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)

	def test_missing_declared_file_is_refused(self):
		root, _ = self.package(mutate=lambda p: (p / "04_fixture/package_index.md").unlink(), reseal_after_mutate=False)
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)

	def test_corrupt_asset_is_refused(self):
		def mutate(p: Path):
			path = p / "02_master/print.css"
			path.write_bytes(path.read_bytes() + b"/* tampered */")

		root, _ = self.package(mutate=mutate, reseal_after_mutate=False)
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)

	def test_wrong_bundle_digest_is_refused(self):
		def mutate(p: Path):
			path = p / bundle.MANIFEST_PATH
			data = json.loads(path.read_text(encoding="utf-8"))
			data["bundle_digest"] = "0" * 64
			path.write_text(pretty_json(data), encoding="utf-8")

		root, _ = self.package(mutate=mutate, reseal_after_mutate=False)
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)

	def test_symbolic_link_is_refused(self):
		root, _ = self.package(mutate=lambda p: os.symlink("/etc/hostname", p / "04_fixture/link.txt"), reseal_after_mutate=False)
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)

	def test_path_traversal_in_a_zip_is_refused(self):
		root, info = self.package()
		archive = info["tmp"] / "pack.zip"
		with zipfile.ZipFile(archive, "w") as z:
			for dirpath, _dirs, files in os.walk(root):
				for name in files:
					full = Path(dirpath) / name
					z.write(full, "it_equipment_open_v1/" + str(full.relative_to(root)))
			z.writestr("it_equipment_open_v1/../../escape.txt", "x")
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", archive)

	def test_blocking_validation_report_is_refused(self):
		def mutate(p: Path):
			path = p / "05_review/validation_report.json"
			data = json.loads(path.read_text(encoding="utf-8"))
			data["summary"]["blocking"] = True
			path.write_text(pretty_json(data), encoding="utf-8")

		root, _ = self.package(mutate=mutate)
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)

	def test_unregistered_renderer_is_refused(self):
		def mutate(p: Path):
			for rel in ("06_runtime/product_profile.json", "06_runtime/response_rules.json", "06_runtime/downstream_rules.json", "06_runtime/addendum_identity_rules.json", bundle.MANIFEST_PATH):
				data = json.loads((p / rel).read_text(encoding="utf-8"))
				data["supported_renderer_version"] = "0.9.0"
				(p / rel).write_text(pretty_json(data), encoding="utf-8")

		root, _ = self.package(mutate=mutate)
		self.assertRefused("STD_RENDERER_UNSUPPORTED", root)

	def test_decision_for_another_manifest_is_refused(self):
		root, info = self.package(decision="APPROVE EXACT MANIFEST")
		path = root / bundle.OWNER_DECISION_PATH
		data = json.loads(path.read_text(encoding="utf-8"))
		data["manifest_digest"] = "f" * 64
		path.write_text(pretty_json(data), encoding="utf-8")
		self.assertRefused("STD_RELEASE_INTEGRITY_FAILED", root)


class TestEvidenceOnly(InstallerCase):
	def test_a_decision_is_recorded_as_evidence(self):
		root, info = self.package(decision="APPROVE EXACT MANIFEST", pass_all_gates=True)
		result = self.install(root, site_switch="Off")
		frappe.db.commit()
		self.assertEqual(result["lifecycle_status"], "Available")
		doc = frappe.get_doc(DOCTYPE, info["release_id"])
		self.assertEqual(doc.owner_decision, "APPROVE EXACT MANIFEST")
		self.assertEqual((doc.lifecycle_status, doc.site_switch), ("Available", "Off"))

	def test_pending_gates_never_block_installation_or_use(self):
		root, info = self.package(decision="CORRECT AND RE-REVIEW")
		result = self.install(root, site_switch="Off")
		frappe.db.commit()
		self.assertEqual(result["lifecycle_status"], "Available")
		self.assertTrue(any(g["result"] == "Pending" for g in installer.load_json(frappe.db.get_value(DOCTYPE, info["release_id"], "gate_results"))))

	def test_a_later_decision_is_recorded_against_the_same_bytes(self):
		root, info = self.package(pass_all_gates=True)
		first = self.install(root, site_switch="Off")
		frappe.db.commit()
		self.assertEqual(first["lifecycle_status"], "Available")
		manifest = json.loads((root / bundle.MANIFEST_PATH).read_text(encoding="utf-8"))
		decision = {
			"schema_version": 1, "release_id": info["release_id"], "template_key": manifest["template_key"], "template_release": manifest["template_release"],
			"bundle_digest": manifest["bundle_digest"], "manifest_digest": info["manifest_digest"], "decision": "APPROVE EXACT MANIFEST",
			"decided_by": "test release owner", "decided_at": "2026-09-26", "decision_record": "Later decision.",
		}
		(root / bundle.OWNER_DECISION_PATH).write_text(pretty_json(decision), encoding="utf-8")
		second = self.install(root)
		frappe.db.commit()
		self.assertTrue(second["decision_recorded"])
		self.assertEqual(frappe.db.get_value(DOCTYPE, info["release_id"], "owner_decision"), "APPROVE EXACT MANIFEST")
		self.assertEqual(frappe.db.get_value(DOCTYPE, info["release_id"], "lifecycle_status"), "Available")
		self.assertEqual(frappe.db.get_value(DOCTYPE, info["release_id"], "site_switch"), "Off")
		self.assertEqual(frappe.db.get_value(DOCTYPE, info["release_id"], "bundle_digest"), manifest["bundle_digest"])
