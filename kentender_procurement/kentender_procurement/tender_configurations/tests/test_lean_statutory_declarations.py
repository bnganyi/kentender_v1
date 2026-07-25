# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Statutory Declarations Review-and-Certify — domain + web markers."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	_get_bid,
	_parse_json,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.statutory_declarations import (
	SECTION_KEY,
	certify_statutory_declarations,
	get_statutory_declarations,
	save_statutory_declarations,
	validate_statutory_response,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)


def _publish_cfg(cfg_id: str) -> str:
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
			"tender_notice": "Statutory redesign notice.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	published = publish_tender_for_development_preview(pub_id)
	return cstr(published.get("publication_ref") or "") or cstr(
		frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
	)


def _seed_cbq(cfg_id: str, *, with_declarant_address: bool = True) -> None:
	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	responses = _parse_json(doc.responses, {})
	answers = {
		"authorized_signatory_name": "Jane Doe",
		"authorized_signatory_title": "Managing Director",
		"authority_to_bind_confirmed": "yes",
		"state_owned_enterprise": "no",
	}
	if with_declarant_address:
		answers.update(
			{
				"declarant_postal_address": "P.O. Box 12345",
				"declarant_place_of_residence": "Nairobi",
				"declarant_country_of_residence": "Kenya",
			}
		)
	responses["confidential_business_questionnaire"] = {
		"entities": [
			{
				"entity_id": "ent-bidder-1",
				"role": "bidder",
				"legal_name": "Lean Demo Bidder Ltd",
				"entity_type": "company",
				"answers": answers,
				"conflict_rows": {},
				"certified": 1,
				"certified_at": str(now_datetime()),
				"certified_by": "Administrator",
				"certified_for": "Lean Demo Bidder Ltd",
				"certifier_name": "Jane Doe",
				"certifier_title": "Managing Director",
				"authority_affirmed": 1,
			}
		],
		"history": [],
	}
	doc.responses = json.dumps(responses, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	frappe.db.commit()


class TestLeanStatutoryDeclarations(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_active_canonical_ppra_it_std(force_reimport=False)
		seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"std_version": CANONICAL_PACKAGE_ID,
				"short_scope_summary": "Statutory redesign tender scope.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		self.ref = _publish_cfg(self.cfg_id)

	def test_checklist_statutory_after_cbq(self):
		out = get_submission_checklist(self.ref)
		keys = [s["section_key"] for s in out["sections"]]
		self.assertIn("confidential_business_questionnaire", keys)
		self.assertIn("statutory_declarations", keys)
		self.assertEqual(
			keys.index("statutory_declarations"),
			keys.index("confidential_business_questionnaire") + 1,
		)

	def test_dto_sourced_from_cbq_no_duplicate_inputs(self):
		_seed_cbq(self.cfg_id)
		dto = get_statutory_declarations(self.ref)
		self.assertEqual(dto["declarant"]["name"], "Jane Doe")
		self.assertEqual(dto["declarant"]["postal_address"], "P.O. Box 12345")
		self.assertEqual(len(dto.get("records") or []), 4)
		src = frappe.get_app_path(
			"kentender_procurement", "www", "tenders", "statutory_declarations.html"
		)
		text = open(src, encoding="utf-8").read()
		self.assertNotIn('name="declarant_name"', text)
		self.assertNotIn('name="witness_name"', text)
		self.assertNotIn("cdn.tailwindcss.com", text)

	def test_missing_declarant_blocks_certify(self):
		_seed_cbq(self.cfg_id, with_declarant_address=False)
		save_statutory_declarations(self.ref, {"independent_tender_choice": "independent"})
		dto = get_statutory_declarations(self.ref)
		self.assertFalse(dto.get("can_certify"))
		with self.assertRaises(frappe.ValidationError):
			certify_statutory_declarations(self.ref)

	def test_independent_choice_no_default(self):
		dto = get_statutory_declarations(self.ref)
		self.assertEqual(dto["independent_tender"].get("choice"), "")

	def test_disclosed_requires_row(self):
		result = validate_statutory_response(
			{}, {"independent_tender_choice": "disclosed", "competitor_disclosures": []}
		)
		self.assertFalse(result["ok"])
		ok = validate_statutory_response(
			{},
			{
				"independent_tender_choice": "disclosed",
				"competitor_disclosures": [
					{
						"competitor_name": "Rival Co",
						"nature_of_interaction": "Consultation",
						"reason": "JV discussion",
						"complete_details": "Discussed packaging only",
					}
				],
			},
		)
		self.assertTrue(ok["ok"])

	def test_certify_creates_four_legal_records(self):
		_seed_cbq(self.cfg_id)
		save_statutory_declarations(self.ref, {"independent_tender_choice": "independent"})
		certified = certify_statutory_declarations(self.ref)
		self.assertTrue(certified["certification"]["certified"])
		records = certified.get("records") or []
		self.assertEqual(len(records), 4)
		keys = {r["record_key"] for r in records}
		self.assertEqual(
			keys,
			{
				"independent_tender_determination",
				"sd1_not_debarred",
				"sd2_no_corruption",
				"code_of_ethics",
			},
		)
		for rec in records:
			self.assertIn("Lean Demo Bidder Ltd", rec.get("legal_text") or "")
			self.assertIn("Jane Doe", rec.get("legal_text") or "")
			self.assertNotIn("nssf", cstr(rec.get("legal_text")).lower())
		ethics = next(r for r in records if r["record_key"] == "code_of_ethics")
		self.assertTrue(ethics.get("appendix_text"))

		checklist = get_submission_checklist(self.ref)
		row = next(s for s in checklist["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(row["status"], "Complete")

	def test_cbq_change_invalidates_bundle(self):
		_seed_cbq(self.cfg_id)
		save_statutory_declarations(self.ref, {"independent_tender_choice": "independent"})
		certify_statutory_declarations(self.ref)
		dto = get_statutory_declarations(self.ref)
		self.assertTrue(dto["certification"]["certified"])

		from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
			_load_response,
			_store_response,
		)

		draft = create_or_get_draft(self.cfg_id)
		doc = _get_bid(cstr(draft.get("bid_id") or ""))
		payload = _load_response(doc)
		payload["entities"][0]["answers"]["authorized_signatory_name"] = "John Smith"
		payload["entities"][0]["certifier_name"] = "John Smith"
		_store_response(doc, payload, event="section_saved")

		after = get_statutory_declarations(self.ref)
		self.assertFalse(after["certification"]["certified"])
		self.assertTrue(
			after["certification"]["requires_recertification"]
			or after["section_status"]
			in ("Requires Recertification", "Needs Attention", "In Progress")
		)

	def test_save_twice_refreshes_concurrency_token(self):
		"""Certify→cancel→Certify: client must reuse bid_modified from prior save."""
		_seed_cbq(self.cfg_id)
		first = save_statutory_declarations(
			self.ref, {"independent_tender_choice": "independent"}
		)
		mod1 = cstr(first.get("bid_modified") or "")
		self.assertTrue(mod1)
		second = save_statutory_declarations(
			self.ref,
			{"independent_tender_choice": "independent"},
			expected_modified=mod1,
		)
		self.assertTrue(second.get("saved"))
		mod2 = cstr(second.get("bid_modified") or "")
		self.assertTrue(mod2)
		self.assertNotEqual(mod1, mod2)
		with self.assertRaises(frappe.ValidationError) as ctx:
			save_statutory_declarations(
				self.ref,
				{"independent_tender_choice": "independent"},
				expected_modified=mod1,
			)
		self.assertIn("updated elsewhere", cstr(ctx.exception).lower())

	def test_template_markers(self):
		src = frappe.get_app_path(
			"kentender_procurement", "www", "tenders", "statutory_declarations.html"
		)
		text = open(src, encoding="utf-8").read()
		self.assertIn('data-testid="kt-stat-certify-dialog"', text)
		self.assertIn('data-testid="kt-stat-independent-choice"', text)
		self.assertIn('data-testid="kt-stat-footer"', text)
		self.assertIn('data-testid="kt-stat-declarant"', text)
		self.assertIn("applyBidModified", text)
		self.assertIn("{ silent: true }", text)
		self.assertEqual(text.count('data-testid="kt-stat-certify"'), 1)


class TestLeanStatutoryWebRender(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_active_canonical_ppra_it_std(force_reimport=False)
		seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{"std_version": CANONICAL_PACKAGE_ID, "short_scope_summary": "Statutory web."},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		self.ref = _publish_cfg(self.cfg_id)

	def test_page_renders(self):
		from frappe.tests.test_website import set_request
		from frappe.website.serve import get_response
		from kentender_procurement.tender_configurations.services.statutory_declarations import (
			portal_statutory_url,
		)

		path = portal_statutory_url(self.ref)
		set_request(method="GET", path=path)
		resp = get_response()
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-stat-root"', body)
		self.assertIn("Review & Certify", body)
		self.assertIn('data-testid="kt-stat-independent-choice"', body)
		self.assertIn('data-testid="kt-stat-footer"', body)
		self.assertNotIn("witness_name", body)


if __name__ == "__main__":
	unittest.main()
