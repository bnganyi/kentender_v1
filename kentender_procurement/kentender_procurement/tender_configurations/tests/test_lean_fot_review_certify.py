# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FoT Review-and-Certify redesign — order, commissions, certify, invalidate."""

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
from kentender_procurement.tender_configurations.services.form_of_tender import (
	SECTION_KEY,
	certify_form_of_tender,
	get_form_of_tender,
	save_form_of_tender,
	seed_price_schedule_for_tests,
	validate_form_of_tender_response,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	acknowledge_tender_documents,
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
			"tender_notice": "FoT redesign notice.",
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


def _seed_prereqs(ref: str, cfg_id: str) -> None:
	"""Make FoT ready except commissions (caller sets commissions)."""
	get_form_of_tender(ref)  # ensure draft
	acknowledge_tender_documents(ref)
	seed_price_schedule_for_tests(ref, grand_total=450000000, currency="KES", discounts_offered="no")

	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	responses = _parse_json(doc.responses, {})
	# Merge — do not wipe docs/price already seeded above.
	responses["statutory_declarations"] = {"complete": True, "section_status": "Complete"}
	responses["confidential_business_questionnaire"] = {
		"entities": [
			{
				"entity_id": "ent-bidder-1",
				"role": "bidder",
				"legal_name": "Lean Demo Bidder Ltd",
				"entity_type": "company",
				"answers": {
					"authorized_signatory_name": "Jane Doe",
					"authorized_signatory_title": "Managing Director",
					"authority_to_bind_confirmed": "yes",
					"state_owned_enterprise": "no",
				},
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


class TestLeanFotReviewCertify(unittest.TestCase):
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
				"short_scope_summary": "FoT redesign tender scope.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		self.ref = _publish_cfg(self.cfg_id)

	def test_checklist_fot_after_price_schedule(self):
		out = get_submission_checklist(self.ref)
		keys = [s["section_key"] for s in out["sections"]]
		self.assertEqual(keys[0], "tender_documents_and_addenda")
		self.assertEqual(keys[-2], "price_schedule")
		self.assertEqual(keys[-1], "form_of_tender")

	def test_dto_has_no_duplicate_bidder_inputs(self):
		dto = get_form_of_tender(self.ref)
		self.assertEqual(dto.get("bidder_owned_fields"), [])
		self.assertEqual(dto.get("declarations"), [])
		self.assertIn("material_offer", dto)
		self.assertIn("readiness", dto)
		self.assertIn("commissions", dto)
		self.assertIn("legal_terms", dto)

	def test_commissions_no_default_and_none_declared(self):
		# Wipe any FoT payload so choice has no default (Yes/No must be explicit).
		draft = create_or_get_draft(self.cfg_id)
		bid_id = cstr(draft.get("bid_id") or "")
		doc = _get_bid(bid_id)
		responses = _parse_json(doc.responses, {})
		responses[SECTION_KEY] = {}
		doc.responses = json.dumps(responses, ensure_ascii=False)
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		dto = get_form_of_tender(self.ref)
		self.assertEqual(dto["commissions"].get("choice"), "")
		saved = save_form_of_tender(self.ref, {"commissions_choice": "no", "commissions_rows": []})
		self.assertEqual(saved["commissions"]["choice"], "no")
		self.assertEqual(saved["commissions"]["summary"], "None declared.")
		self.assertEqual(saved["section_status"], "In Progress")

	def test_commissions_yes_requires_row(self):
		section_def = {"repeatable_tables": []}
		result = validate_form_of_tender_response(
			section_def, {"commissions_choice": "yes", "commissions_rows": []}
		)
		self.assertFalse(result["ok"])
		self.assertTrue(any(i["field_key"] == "commissions_rows" for i in result["issues"]))

		ok = validate_form_of_tender_response(
			section_def,
			{
				"commissions_choice": "yes",
				"commissions_rows": [
					{
						"recipient_name": "Agent",
						"recipient_address": "Nairobi",
						"reason": "Intro",
						"amount": "1000",
						"currency": "KES",
					}
				],
			},
		)
		self.assertTrue(ok["ok"])

	def test_certify_blocked_when_prerequisites_incomplete(self):
		save_form_of_tender(self.ref, {"commissions_choice": "no"})
		with self.assertRaises(frappe.ValidationError):
			certify_form_of_tender(self.ref)

	def test_certify_stores_legal_record_and_completes_checklist(self):
		_seed_prereqs(self.ref, self.cfg_id)
		save_form_of_tender(self.ref, {"commissions_choice": "no"})
		dto = get_form_of_tender(self.ref)
		self.assertTrue(dto.get("can_certify"), dto.get("readiness"))
		certified = certify_form_of_tender(self.ref)
		self.assertTrue(certified["certification"]["certified"])
		self.assertTrue(certified["certification"]["certified_at"])
		record = (certified["instances"][0] or {}).get("legal_record") or {}
		self.assertTrue(record.get("legal_text"))
		self.assertEqual(record.get("commissions_choice"), "no")
		self.assertEqual(record.get("signatory_name"), "Jane Doe")
		self.assertNotIn("nssf", cstr(record.get("legal_text")).lower())

		checklist = get_submission_checklist(self.ref)
		fot_row = next(s for s in checklist["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(fot_row["status"], "Complete")

	def test_source_change_invalidates_certification(self):
		_seed_prereqs(self.ref, self.cfg_id)
		save_form_of_tender(self.ref, {"commissions_choice": "no"})
		certify_form_of_tender(self.ref)
		# Price change withdraws FoT cert
		seed_price_schedule_for_tests(self.ref, grand_total=999, currency="KES", discounts_offered="no")
		dto = get_form_of_tender(self.ref)
		self.assertFalse(dto["certification"]["certified"])
		self.assertTrue(dto["certification"]["requires_recertification"] or dto["section_status"] in (
			"Requires Recertification",
			"Needs Attention",
			"In Progress",
		))

	def test_template_has_review_certify_markers(self):
		src = frappe.get_app_path("kentender_procurement", "www", "tenders", "form_of_tender.html")
		text = open(src, encoding="utf-8").read()
		self.assertIn('data-testid="kt-fot-material-summary"', text)
		self.assertIn('data-testid="kt-fot-certify-dialog"', text)
		self.assertIn('data-testid="kt-fot-incomplete-banner"', text)
		self.assertIn('data-testid="kt-fot-footer"', text)
		self.assertNotIn('name="bidder_legal_name"', text)
		self.assertNotIn("cdn.tailwindcss.com", text)


class TestLeanFotWebRender(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_active_canonical_ppra_it_std(force_reimport=False)
		seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{"std_version": CANONICAL_PACKAGE_ID, "short_scope_summary": "FoT web render."},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		self.ref = _publish_cfg(self.cfg_id)

	def test_page_renders_review_certify(self):
		from frappe.tests.test_website import set_request
		from frappe.website.serve import get_response
		from kentender_procurement.tender_configurations.services.form_of_tender import (
			portal_fot_url,
		)

		path = portal_fot_url(self.ref)
		set_request(method="GET", path=path)
		resp = get_response()
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-fot-root"', body)
		self.assertIn("Review & Certify", body)
		self.assertIn('data-testid="kt-fot-material-summary"', body)
		self.assertIn('data-testid="kt-fot-incomplete-banner"', body)
		self.assertIn('data-testid="kt-fot-commissions-choice"', body)
		self.assertIn('data-testid="kt-fot-footer"', body)
		self.assertNotIn('name="bidder_legal_name"', body)
		self.assertNotIn("bidder_business_address", body)


if __name__ == "__main__":
	unittest.main()
