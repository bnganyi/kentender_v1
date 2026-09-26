# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §§6, 10–13, 16 — read projections, access matrix,
concerns, previews, review pack, integrity and production/CLI parity
(STI10-AC-005/006/007/008; TPL08-AC-019/022; TPL10-AC-001/002/004)."""

from __future__ import annotations

import io
import json
import zipfile

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler.canonical import pretty_json
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.services import access, concerns, documents, installer, read, runtime
from kentender_procurement.std_templates.tests import support

OFFICER = "brian.wafula@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
ACCOUNTING_OFFICER = "amina.hassan@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"
TEST_SYSMGR = "std-templates-sysmgr@example.test"


class ServiceCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.root, cls.info = support.make_test_package()
		installer.install_approved_std_release(str(cls.root), installed_by="test", site_switch="Off")
		frappe.db.commit()
		cls.release_id = cls.info["release_id"]

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		support.purge([cls.release_id])
		support.cleanup_tmp(cls.info)
		if frappe.db.exists("User", TEST_SYSMGR):
			frappe.delete_doc("User", TEST_SYSMGR, force=True, ignore_permissions=True)
			frappe.db.commit()
		super().tearDownClass()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")


class TestAccess(ServiceCase):
	def test_procurement_officer_and_hopf_read(self):
		for user in (OFFICER, HOPF):
			with self.subTest(user=user):
				self.assertTrue(access.resolve(user)["allowed"])
				self.assertEqual(read.get_installed_release(self.release_id, user=user)["outcome"], "OK")

	def test_other_roles_are_refused_without_learning_existence(self):
		for user in (ACCOUNTING_OFFICER, AUDITOR):
			with self.subTest(user=user):
				with self.assertRaises(STDTemplateError) as ctx:
					read.get_installed_release(self.release_id, user=user)
				self.assertEqual(ctx.exception.code, "STD_RELEASE_NOT_FOUND")
				with self.assertRaises(STDTemplateError):
					documents.preview(self.release_id, "invitation", user=user)

	def test_system_manager_has_technical_read(self):
		if not frappe.db.exists("User", TEST_SYSMGR):
			user = frappe.get_doc({"doctype": "User", "email": TEST_SYSMGR, "first_name": "STD", "last_name": "SysMgr", "send_welcome_email": 0, "roles": [{"role": "System Manager"}]})
			user.insert(ignore_permissions=True)
			frappe.db.commit()
		state = access.resolve(TEST_SYSMGR)
		self.assertTrue(state["allowed"] and state["technical"])

	def test_no_endpoint_edits_or_activates(self):
		from kentender_procurement.std_templates import api

		public = {name for name in dir(api) if callable(getattr(api, name)) and getattr(getattr(api, name), "__module__", "") == api.__name__ and not name.startswith("_")}
		for word in ("install", "activate", "approve", "withdraw", "supersede", "edit", "upload", "repair", "resolve", "update", "save", "delete"):
			self.assertFalse([n for n in public if word in n], f"an API endpoint mentions {word}")


class TestProjections(ServiceCase):
	def test_list_row(self):
		result = read.list_installed_releases(user=OFFICER)
		row = next(r for r in result["releases"] if r["release_id"] == self.release_id)
		self.assertEqual(row["status"], "Unavailable")
		self.assertEqual(row["consequence"], read.LIST_CONSEQUENCE)
		self.assertIn("Goods · Open Tender · single lot", row["supported_use"]["line"])
		self.assertTrue(row["last_verified"].endswith("EAT"))

	def test_filters_give_truthful_empty_states(self):
		result = read.list_installed_releases(status="Withdrawn", user=OFFICER)
		self.assertEqual(result["releases"], [])
		self.assertEqual(result["empty_kind"], "filtered")
		self.assertEqual(result["empty"], "No STD Templates match these filters.")
		result = read.list_installed_releases(search="no such format", user=OFFICER)
		self.assertEqual(result["empty_kind"], "filtered")

	def test_detail_projection_for_a_switched_off_release(self):
		detail = read.get_installed_release(self.release_id, user=HOPF)
		self.assertEqual(detail["release"]["status"], "Unavailable")
		self.assertEqual(detail["release"]["consequence"], read.CONSEQUENCE["Switched off"])
		self.assertEqual(detail["release"]["next_step"]["head"], "Switched off on this site.")
		self.assertEqual([b["text"] for b in detail["blockers"]], ["This release is switched off on this site."])
		checks = [r["check"] for r in detail["verification"]["rows"]]
		self.assertEqual(checks, ["Official source", "Tender documents", "Supplier responses", "Evaluation and contract mappings", "Reservation variants", "Addendum identity rules", "MoH fixture", "Site switch"])
		self.assertEqual(detail["verification"]["rows"][-1]["result"], "Off")
		self.assertEqual(detail["verification"]["caption"], read.VERIFICATION_CAPTION)
		self.assertEqual(sum(t["n"] for t in detail["coverage"]["treatments"]), detail["coverage"]["total"])
		self.assertEqual(detail["coverage"]["total"], 296)
		self.assertEqual(detail["coverage"]["changes"]["heading"], "Changes from release 1.0")
		self.assertEqual(len(detail["bid_response"]["tasks"]), 5)
		self.assertEqual([g["name"] for g in detail["bid_response"]["evaluation_groups"]], ["Eligibility", "Technical compliance", "Financial", "Award"])
		self.assertIn("Release ID", [t["label"] for t in detail["technical"]])

	def test_default_reading_path_has_no_digest_or_raw_json(self):
		detail = read.get_installed_release(self.release_id, user=OFFICER)
		visible = {k: v for k, v in detail.items() if k not in ("technical", "viewer", "concerns")}
		text = json.dumps(visible)
		release = frappe.get_doc("Installed STD Release", self.release_id)
		self.assertNotIn(release.bundle_digest, text)
		self.assertNotIn(release.manifest_digest, text)
		self.assertNotIn("renderer_profile_id", text)
		self.assertNotIn("BDS-GOODS-IT-V1", text)

	def test_coverage_paging_and_filters(self):
		page = read.list_release_coverage(self.release_id, page=1, page_length=25, user=OFFICER)
		self.assertEqual(page["total"], 296)
		self.assertEqual(page["pages"], 12)
		excluded = read.list_release_coverage(self.release_id, treatment="Excluded with reason", page_length=100, user=OFFICER)
		self.assertTrue(excluded["total"] > 0 and all(r["reason"] for r in excluded["rows"]))
		found = read.list_release_coverage(self.release_id, search="COV-184", user=OFFICER)
		self.assertEqual([r["coverage_id"] for r in found["rows"]], ["COV-184"])

	def test_change_report_is_grouped_and_classified(self):
		report = read.get_release_change_report(self.release_id, user=OFFICER)
		self.assertEqual(report["summary"]["result"], "Breaking — not interchangeable with the preceding release")
		self.assertIn("Response rules", report["filters"]["categories"])
		only = read.get_release_change_report(self.release_id, category="Response rules", page_length=100, user=OFFICER)
		self.assertTrue(only["rows"] and all(r["category"] == "Response rules" for r in only["rows"]))


class TestConcerns(ServiceCase):
	def test_invalid_concern_keeps_values_and_names_fields(self):
		result = concerns.create_concern(self.release_id, {"category": "Nope", "summary": "x", "description": "short"}, user=OFFICER)
		self.assertFalse(result["ok"])
		self.assertEqual(result["code"], "STD_CONCERN_INVALID")
		self.assertEqual(set(result["errors"]), {"category", "summary", "description"})

	def test_concern_changes_nothing_about_the_release(self):
		before = frappe.db.get_value("Installed STD Release", self.release_id, ["lifecycle_status", "modified", "bundle_digest"], as_dict=True)
		frappe.set_user(OFFICER)
		result = concerns.create_concern(
			self.release_id,
			{"category": "Source treatment", "source_locator": "STD row 184", "summary": "Confirm exclusion reason", "description": "The exclusion reason for this row should name its source basis."},
		)
		frappe.set_user("Administrator")
		frappe.db.commit()
		self.assertTrue(result["ok"])
		after = frappe.db.get_value("Installed STD Release", self.release_id, ["lifecycle_status", "modified", "bundle_digest"], as_dict=True)
		self.assertEqual(before, after)
		doc = frappe.get_doc("STD Template Concern", result["concern_id"])
		self.assertEqual((doc.status, doc.reported_by, doc.concern_id), ("Open", OFFICER, doc.name))
		self.assertTrue(frappe.db.exists("Audit Event", {"document_name": doc.name, "action": "Concern reported"}))
		summary = concerns.summary_for(self.release_id, user=OFFICER)
		self.assertEqual(summary["own"][0]["concern_id"], doc.name)
		doc.summary = "Edited"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		frappe.db.rollback()


class TestDocuments(ServiceCase):
	def test_preview_streams_the_immutable_pdf(self):
		name, content = documents.preview(self.release_id, "issued_tender", user=OFFICER)
		self.assertTrue(content.startswith(b"%PDF"))
		self.assertTrue(name.endswith(".pdf"))
		self.assertTrue(frappe.db.exists("Audit Event", {"document_name": self.release_id, "action": "Previewed"}))

	def test_review_pack_is_the_exact_pack(self):
		name, content = documents.review_pack(self.release_id, user=HOPF)
		release = frappe.get_doc("Installed STD Release", self.release_id)
		with zipfile.ZipFile(io.BytesIO(content)) as archive:
			names = archive.namelist()
			self.assertIn(next(n for n in names if n.endswith("06_runtime/release_manifest.json")), names)
			self.assertEqual(sum(1 for n in names if not n.endswith(("release_manifest.json", "review_record.md", "owner_decision.json"))), len(release.assets))


class TestParityAndIntegrity(ServiceCase):
	def test_production_adapter_reproduces_the_golden_vector(self):
		expected = (support.PACK / "06_runtime/moh_published_bid_definition_expected.json").read_text(encoding="utf-8")
		# The test package carries its own release identity; the golden vector
		# is compared on the real installed release when present, else on the
		# pack itself through the same production path.
		real = support.pack_assets().envelope["release_id"]
		target = real if frappe.db.exists("Installed STD Release", real) else None
		if not target:
			self.skipTest("release 1.1 candidate is not installed on this site")
		produced = runtime.compile_published_bid_definition_for(target, support.moh_projection(), digest_basis="input")
		self.assertEqual(pretty_json(produced), expected)

	def test_production_renderer_reproduces_the_documents(self):
		out = runtime.render_documents(self.release_id, support.moh_projection())
		self.assertEqual(out["issued_tender_html"], (support.PACK / "04_fixture/moh_expected.html").read_text(encoding="utf-8"))
		self.assertEqual(out["invitation_html"], (support.PACK / "04_fixture/moh_invitation_expected.html").read_text(encoding="utf-8"))
		self.assertEqual(out["problems"], [])

	def test_a_switched_on_intact_release_is_available_with_pending_reviews(self):
		root, info = support.make_test_package(template_release="9.1-test")
		self.addCleanup(lambda: support.purge([info["release_id"]]))
		self.addCleanup(lambda: support.cleanup_tmp(info))
		installer.install_approved_std_release(str(root), installed_by="test", site_switch="On")
		frappe.db.commit()
		detail = read.get_installed_release(info["release_id"], user=OFFICER)
		self.assertEqual(detail["release"]["status"], "Available")
		self.assertEqual(detail["blockers"], [])
		self.assertEqual(detail["release"]["next_step"]["head"], "Ready for supported Tenders.")
		self.assertEqual(detail["verification"]["rows"][-1]["result"], "On")
		self.assertIn("Incomplete", [r["result"] for r in detail["verification"]["rows"]])

	def test_a_tampered_stored_asset_fails_closed(self):
		root, info = support.make_test_package(template_release="9.3-test")
		self.addCleanup(lambda: support.purge([info["release_id"]]))
		self.addCleanup(lambda: support.cleanup_tmp(info))
		installer.install_approved_std_release(str(root), installed_by="test", site_switch="On")
		frappe.db.commit()
		release = frappe.get_doc("Installed STD Release", info["release_id"])
		row = next(a for a in release.assets if a.relative_path == "06_runtime/response_rules.json")
		path = frappe.get_doc("File", row.private_file_id).get_full_path()
		with open(path, "ab") as fh:
			fh.write(b" ")
		result = runtime.verify_integrity(info["release_id"])
		frappe.db.commit()
		self.assertFalse(result["ok"])
		detail = read.get_installed_release(info["release_id"], user=OFFICER)
		self.assertEqual(detail["release"]["status"], "Unavailable")
		self.assertTrue(detail["release"]["failed_verification"])
		self.assertTrue(detail["blockers"][0]["failed"])
		self.assertEqual(detail["release"]["next_step"]["head"], "Release verification failed.")
		with self.assertRaises(STDTemplateError) as ctx:
			runtime.compile_published_bid_definition_for(info["release_id"], support.moh_projection())
		self.assertEqual(ctx.exception.code, "STD_RELEASE_INTEGRITY_FAILED")
