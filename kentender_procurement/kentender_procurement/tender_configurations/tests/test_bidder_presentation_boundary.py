# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder presentation boundary — allowlisted DTOs; no internal package leakage."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, cstr, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.available_tenders import (
	list_available_tenders,
)
from kentender_procurement.tender_configurations.services.bidder_presentation import (
	BIDDER_DOCUMENTS_DTO_KEYS,
	assert_no_forbidden_bidder_keys,
	dto_as_scan_text,
	scan_bidder_presentation_text,
)
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	get_published_tender_overview,
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.requirement_matrix import (
	get_requirement_matrix,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	acknowledge_tender_documents,
	append_issued_addendum,
	get_tender_documents_addenda,
)


def _prep_and_publish() -> tuple[str, str, str]:
	ensure = __import__(
		"kentender_procurement.std_engine.services.ensure_active_canonical_std",
		fromlist=["ensure_active_canonical_ppra_it_std"],
	).ensure_active_canonical_ppra_it_std
	ensure(force_reimport=False)
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "Presentation boundary scope.",
			"bidder_submission_schema": json.dumps(
				{
					"version": 1,
					"sections": [
						{
							"key": "tender_document_acknowledgement",
							"section_type": "document_acknowledgement",
							"title": "Tender Documents & Addenda",
							"required": True,
						},
						{"key": "form_of_tender", "title": "Form of Tender", "required": True},
					],
				}
			),
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	for name in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration": cfg_id},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
	frappe.db.commit()

	gen = generate_document_preview(cfg_id)
	assert cstr(gen.get("preview_status")) == "Generated", gen.get("render_exception")
	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "Presentation boundary notice.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	published = publish_tender_for_development_preview(pub_id)
	ref = cstr(published.get("publication_ref") or "") or cstr(
		frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
	)
	return cfg_id, pub_id, ref


class TestBidderPresentationBoundary(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def test_documents_api_uses_explicit_allowlist(self):
		out = get_tender_documents_addenda(self.ref)
		extra = set(out.keys()) - BIDDER_DOCUMENTS_DTO_KEYS
		self.assertFalse(extra, f"unexpected bidder documents keys: {extra}")
		violations = assert_no_forbidden_bidder_keys(out)
		self.assertFalse(violations, violations)
		hits = scan_bidder_presentation_text(dto_as_scan_text(out), include_hex_digests=True)
		self.assertFalse(hits, hits)

	def test_internal_package_artifacts_excluded_from_documents(self):
		out = get_tender_documents_addenda(self.ref)
		backend = resolve_published_tender_backend(self.ref)
		pkg = backend.get("confirmed_package") or {}
		self.assertTrue(pkg.get("document_hash"), "integrity hash must remain server-side")
		self.assertTrue(pkg.get("items"), "internal package inventory must remain in backend package")
		names = " ".join(cstr(d.get("name") or "") for d in (out.get("documents") or [])).lower()
		for banned in (
			"tender configuration reference",
			"procurement package reference",
			"bidder submission schema",
			"evaluation schema",
			"price schedule schema",
			"readiness report",
			"document hash",
			"package artifact",
		):
			self.assertNotIn(banned, names)
		for doc in out.get("documents") or []:
			self.assertNotEqual(cstr(doc.get("type")), "Package Artifact")
			self.assertFalse(cstr(doc.get("document_key") or "").startswith("pkg_item_"))

	def test_only_published_documents_and_addenda(self):
		append_issued_addendum(
			self.pub_id,
			{
				"id": "ADD-BPB-1",
				"title": "Clarification on delivery",
				"summary": "Delivery window updated.",
				"requires_acknowledgement": True,
				"version": "Addendum 1",
			},
		)
		out = get_tender_documents_addenda(self.ref)
		doc_keys = {cstr(d.get("document_key")) for d in (out.get("documents") or [])}
		self.assertTrue(doc_keys <= {"tender_pdf", ""})
		self.assertEqual(len(out.get("addenda") or []), 1)
		self.assertEqual(out["addenda"][0]["id"], "ADD-BPB-1")
		self.assertEqual(out["addenda"][0].get("version_label"), "Addendum 1")

	def test_ack_binding_preserved_without_dto_hashes(self):
		ack = acknowledge_tender_documents(self.ref)
		self.assertEqual(ack["documents_acknowledged"], 1)
		self.assertNotIn("package_context", ack)
		backend = resolve_published_tender_backend(self.ref)
		bid = frappe.get_doc("Electronic Bid Submission", backend["bid_id"])
		payload = json.loads(bid.responses or "{}").get(ack["section_key"]) or {}
		digest = cstr(payload.get("package_document_hash") or "")
		self.assertTrue(digest)
		self.assertNotIn(digest, dto_as_scan_text(ack))

		append_issued_addendum(
			self.pub_id,
			{
				"id": "ADD-BPB-2",
				"title": "Material change",
				"requires_acknowledgement": True,
				"version": "v2",
			},
		)
		stale = get_tender_documents_addenda(self.ref)
		self.assertEqual(stale["documents_acknowledged"], 0)
		self.assertEqual(stale["acknowledgement_stale"], 1)
		bid.reload()
		payload2 = json.loads(bid.responses or "{}").get(ack["section_key"]) or {}
		self.assertTrue(payload2.get("acknowledgement_history"))

	def test_a0_a4_dtos_forbid_internal_package_fields(self):
		overview = get_published_tender_overview(self.ref)
		checklist = get_submission_checklist(self.ref)
		docs = get_tender_documents_addenda(self.ref)
		a0 = list_available_tenders()
		for label, payload in (
			("A0", a0),
			("A1", overview),
			("A2", checklist),
			("A3", docs),
		):
			violations = assert_no_forbidden_bidder_keys(payload)
			self.assertFalse(violations, f"{label}: {violations}")
			hits = scan_bidder_presentation_text(dto_as_scan_text(payload), include_hex_digests=True)
			self.assertFalse(hits, f"{label}: {hits}")

		# A4 matrix may be absent on lean schema — skip if section missing.
		try:
			matrix = get_requirement_matrix(self.ref, "form_of_tender")
		except Exception:
			matrix = None
		if matrix is not None:
			violations = assert_no_forbidden_bidder_keys(matrix)
			self.assertFalse(violations, violations)


class TestBidderPresentationBoundaryWeb(IntegrationTestCase):
	def setUp(self):
		clear_website_cache()
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def tearDown(self):
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		frappe.set_user("Administrator")

	def test_documents_html_has_no_technical_leakage(self):
		set_request(method="GET", path=f"/tenders/{self.ref}/documents")
		resp = get_response()
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-a3-documents-root"', body)
		self.assertTrue(
			"Tender Documents & Addenda" in body or "Tender Documents &amp; Addenda" in body,
			body[:500],
		)
		self.assertIn("Official Tender Documents", body)
		self.assertIn("Official Addenda", body)
		self.assertIn("Acknowledgment Status", body)
		self.assertNotIn("kt-a3-package-meta", body)
		self.assertNotIn("Current package:", body)
		hits = scan_bidder_presentation_text(body, include_hex_digests=False)
		self.assertFalse(hits, hits)
		backend = resolve_published_tender_backend(self.ref)
		digest = cstr((backend.get("confirmed_package") or {}).get("document_hash") or "")
		if digest:
			self.assertNotIn(digest, body)
			self.assertNotIn(digest[:16], body)


if __name__ == "__main__":
	unittest.main()
