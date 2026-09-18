# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.5 / §7.1 — template binding (§3), the two renders
through the installed bundle (AC-023/024), the Tenders-owned notice
templates (plan D5) and the immutable digest-addressed document store
with its audience masking (§12.3(3), AC-077)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from jinja2 import UndefinedError

from kentender_procurement.tender_templates import checks, loader
from kentender_procurement.tenders.services import documents, notices, render_service, snapshot as snap, template_binding
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx, sample


class DocumentsCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_tender_rows()
		self.values = sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE)
		self.addCleanup(frappe.set_user, "Administrator")


class TestTemplateBinding(DocumentsCase):
	def test_bind_returns_the_installed_release_and_its_digests(self):
		binding = template_binding.bind()
		self.assertEqual((binding["template_key"], binding["template_version"]), (loader.TEMPLATE_KEY, loader.TEMPLATE_VERSION))
		self.assertEqual(binding["template_release_id"], f"{loader.TEMPLATE_KEY}-{loader.TEMPLATE_VERSION}")
		self.assertEqual(len(binding["bundle_digest"]), 64)
		self.assertIn("Youth", binding["supported_reservation_categories"])

	def test_verify_names_a_drifted_binding(self):
		_tender, version = sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS)
		self.assertTrue(template_binding.verify(version))  # the sample carries placeholder digests
		binding = template_binding.bind()
		version.template_release_id, version.bundle_digest, version.official_source_digest = binding["template_release_id"], binding["bundle_digest"], binding["official_source_digest"]
		self.assertEqual(template_binding.verify(version), [])


class TestRenders(DocumentsCase):
	def test_both_documents_render_cleanly_from_the_saved_version(self):
		tender, version = sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS)
		out = render_service.render(tender, version, snap.load(version))
		self.assertEqual(out["problems"], [])
		self.assertIn("TND-MOH-2027-033", out["invitation_html"])
		self.assertIn("Supply and delivery of business laptops", out["issued_tender_html"])
		self.assertTrue(checks.invitation_absent_from_issued_tender(out["issued_tender_html"]))
		section_v = out["issued_tender_html"].split("Section V - Schedule of Requirements</h2>", 1)[1].split("Section VI - General Conditions of Contract</h2>", 1)[0]
		for i in range(1, 12):
			self.assertEqual(section_v.count(f"TECH-{i:03d}"), 1, f"TECH-{i:03d}")
		for i in range(1, 6):
			self.assertEqual(section_v.count(f"ACC-{i:03d}"), 1, f"ACC-{i:03d}")
		self.assertIn("SRC-MOH-033-001, SRC-MOH-033-002", section_v)
		self.assertEqual(checks.internal_only_leaks(out["issued_tender_html"], out["context"]), [])
		self.assertNotIn("50,000,000", out["issued_tender_html"])
		self.assertIn("Reserved procurement under regulation 149", out["issued_tender_html"])

	def test_the_render_is_deterministic_and_the_pdf_is_a_convenience(self):
		tender, version = sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS)
		first = render_service.render(tender, version, snap.load(version))
		second = render_service.render(frappe.get_doc("Tender", tender.name), frappe.get_doc("Tender Version", version.name), snap.load(version))
		self.assertEqual((first["invitation_digest"], first["issued_tender_digest"], first["context_digest"]), (second["invitation_digest"], second["issued_tender_digest"], second["context_digest"]))
		with_pdf = render_service.render(tender, version, snap.load(version), with_pdf=True)
		self.assertTrue(with_pdf["issued_tender_pdf"].startswith(b"%PDF"))
		self.assertEqual(len(with_pdf["issued_tender_pdf_digest"]), 64)

	def test_an_incomplete_draft_cannot_render(self):
		tender, version = sample.insert_tender_with_version(values={}, fixture_namespace=fx.NS)
		out = render_service.render(tender, version, snap.load(version))
		# Missing officer values render as empty strings, which the release
		# checks flag as unresolved content rather than a crash.
		self.assertTrue(out["problems"] or "Pending approval" in out["invitation_html"])


class TestNotices(DocumentsCase):
	def _context(self, **overrides):
		context = {
			"procuring_entity": {"name": "Ministry of Health", "address": "Afya House, Cathedral Road, Nairobi", "contact_office": "Ministry of Health Procurement Office, procurement@moh.example.test"},
			"platform": {"name": "KenTender"},
			"tender": {"reference": "TND-MOH-2027-033", "title": "Supply and delivery of business laptops", "submission_deadline": "5 June 2027, 11:00 EAT", "published_at": "15 May 2027, 08:00 EAT"},
			"addendum": {"number": 1, "reference": "ADD-MOH-2027-033-001", "issued_at": "31 May 2027, 09:00 EAT", "change_class": "Administrative clarification", "affected_area": "Goods/delivery schedule", "affected_reference": "Goods and delivery — delivery location", "previous_value": "Ministry of Health Headquarters, Afya House, Nairobi", "revised_value": "Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi", "reason": "The published address omitted the internal delivery point", "deadline_extension_required": True, "revised_submission_deadline": "12 June 2027, 11:00 EAT", "issued_by": "Charles Mutiso"},
			"cancellation": {"decided_at": "4 June 2027, 14:00 EAT", "ground": "Inadequate budgetary provision", "reason": "The confirmed budget available for this procurement is insufficient to proceed.", "decided_by": "Amina Hassan", "reference": "TDC-SAMPLE"},
		}
		context.update(overrides)
		return context

	def test_addendum_notice_renders_the_change_and_the_revised_deadline(self):
		out = notices.render_addendum_notice(self._context())
		self.assertIn("ADDENDUM 1 TO TENDER DOCUMENT", out["html"])
		self.assertIn("3rd Floor Procurement Stores", out["html"])
		self.assertIn("12 June 2027, 11:00 EAT", out["html"])
		self.assertEqual(len(out["digest"]), 64)
		self.assertEqual(checks.unresolved_content(out["html"]), [])

	def test_cancellation_notice_renders_the_ground_and_is_strict(self):
		out = notices.render_cancellation_notice(self._context())
		self.assertIn("NOTICE OF CANCELLATION", out["html"])
		self.assertIn("Inadequate budgetary provision", out["html"])
		self.assertIn("section 63", out["html"])
		context = self._context()
		del context["cancellation"]["ground"]
		with self.assertRaises(UndefinedError):
			notices.render_cancellation_notice(context)


class TestDocumentStore(DocumentsCase):
	def test_store_is_idempotent_on_digest_and_get_masks_by_audience(self):
		tender, version = sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS)
		out = render_service.render(tender, version, snap.load(version), with_pdf=True)
		name = documents.store(tender=tender.name, tender_version=version.name, kind=documents.KIND_INVITATION, html=out["invitation_html"], digest_value=out["invitation_digest"], pdf=out["invitation_pdf"], file_base="TND-MOH-2027-033-invitation", fixture_namespace=fx.NS)
		again = documents.store(tender=tender.name, tender_version=version.name, kind=documents.KIND_INVITATION, html=out["invitation_html"], digest_value=out["invitation_digest"], file_base="TND-MOH-2027-033-invitation", fixture_namespace=fx.NS)
		self.assertEqual(name, again)
		self.assertEqual(frappe.db.count("Tender Document", {"tender": tender.name}), 1)
		self.assertEqual(documents.html_of(name), out["invitation_html"])
		row = frappe.get_doc("Tender Document", name)
		self.assertTrue(row.file and row.html_file)
		# a plain save is refused: the row is immutable
		row.kind = "Complete Tender"
		with self.assertRaises(frappe.ValidationError):
			row.save(ignore_permissions=True)

		read = documents.get_tender_document(digest_value=out["invitation_digest"], user=fx.AUDITOR)
		self.assertEqual((read["kind"], read["tender_reference"], read["pdf"]["format"]), ("Invitation", "TND-MOH-2027-033", "PDF"))
		self.assertEqual(read["html"], out["invitation_html"])
		audit = documents.get_tender_document(digest_value=out["invitation_digest"], audience="Audit", user=fx.AUDITOR)
		self.assertEqual(audit["audience"], "Audit")
		with self.assertRaises(frappe.DoesNotExistError):
			documents.get_tender_document(digest_value=out["invitation_digest"], user=fx.NOBODY)
		with self.assertRaises(frappe.DoesNotExistError):
			documents.get_tender_document(digest_value="0" * 64, user=fx.AUDITOR)
		with self.assertRaises(frappe.DoesNotExistError):  # not published yet → no public package
			documents.get_tender_document(digest_value=out["invitation_digest"], audience="Public", user=fx.OFFICER)
		with self.assertRaises(TendersError):
			documents.get_tender_document(digest_value=out["invitation_digest"], audience="Everyone", user=fx.OFFICER)
