# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""S300 — Confidential Business Questionnaire prove-list (Stitch-aligned)."""

from __future__ import annotations

import copy
import json
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, cstr, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.tender_configurations.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
	CONFLICT_ROW_KEYS,
	SECTION_KEY,
	add_jv_entity,
	amend_cbq_certification,
	certify_cbq_entity,
	derive_cbq_section_status,
	format_certified_at_display,
	get_confidential_business_questionnaire,
	portal_cbq_url,
	save_confidential_business_questionnaire,
)
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)


def _prep_and_publish() -> tuple[str, str, str]:
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "S300 CBQ foundation scope.",
			"lot_structure": "Single lot",
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
			"tender_notice": "S300 CBQ notice.",
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


def _all_conflicts_no() -> dict:
	return {k: {"answer": "no", "details": ""} for k in CONFLICT_ROW_KEYS}


def _complete_company_entity(entity: dict) -> dict:
	e = copy.deepcopy(entity)
	e["entity_type"] = "company"
	e["legal_name"] = e.get("legal_name") or "Acme Systems Ltd"
	e["answers"] = {
		"submission_type": "single",
		"country": "Kenya",
		"city": "Nairobi",
		"location": "Westlands",
		"building": "Acme Tower",
		"floor": "5",
		"postal_address": "P.O. Box 123",
		"contact_person": "Jane Contact",
		"contact_email": "jane@acme.example",
		"nature_of_business": "ICT systems integration",
		"max_business_value": "50000000",
		"currency": "KES",
		"trade_licence_number": "TL-100",
		"licence_expiry": "2027-12-31",
		"registering_body": {
			"name": "Registrar of Companies",
			"country": "Kenya",
			"physical_address": "Sheria House",
			"postal_address": "P.O. Box 30031",
			"email": "roc@example.go.ke",
			"phone": "+254700000000",
		},
		"stock_exchange_listed": "no",
		"pe_interest_disclosure": "no",
		"company_type": "private_limited",
		"share_capital_nominal": "1000000",
		"share_capital_issued": "1000000",
		"directors": [
			{
				"name": "Jane Director",
				"nationality": "KE",
				"citizenship": "Kenyan",
				"shares_percent": "100",
			}
		],
	}
	e["conflict_rows"] = _all_conflicts_no()
	return e


class TestLeanS300ConfidentialBusinessQuestionnaire(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def test_section_present_lots_omitted(self):
		cl = get_submission_checklist(self.ref)
		keys = [cstr(s.get("section_key")) for s in cl.get("sections") or []]
		self.assertIn(SECTION_KEY, keys)
		self.assertNotIn("lot_and_alternative_selection", keys)
		dto = get_confidential_business_questionnaire(self.ref)
		self.assertEqual(dto.get("section_key"), SECTION_KEY)
		self.assertTrue(dto.get("entities"))
		self.assertIn("tender_info", dto)
		self.assertEqual(len(dto.get("conflict_row_keys") or []), 9)

	def test_jv_entity_repetition(self):
		dto = get_confidential_business_questionnaire(self.ref)
		before = len(dto.get("entities") or [])
		out = add_jv_entity(self.ref, legal_name="JV Partner Co")
		self.assertEqual(len(out.get("entities") or []), before + 1)
		roles = [cstr(e.get("role")) for e in out["entities"]]
		self.assertIn("bidder", roles)
		self.assertIn("jv_member", roles)

	def test_design_fields_persist(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = _complete_company_entity(dto["entities"][0])
		saved = save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		ans = saved["entities"][0]["answers"]
		self.assertEqual(ans.get("country"), "Kenya")
		self.assertEqual(ans.get("contact_email"), "jane@acme.example")
		self.assertEqual((ans.get("registering_body") or {}).get("name"), "Registrar of Companies")
		self.assertEqual(len(saved["entities"][0]["conflict_rows"]), 9)

	def test_entity_type_branching(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = dto["entities"][0]
		sole = _complete_company_entity(ent)
		sole["entity_type"] = "sole_proprietor"
		sole["answers"].pop("directors", None)
		sole["answers"].pop("company_type", None)
		sole["answers"]["proprietor_name"] = "Solo Trader"
		sole["answers"]["proprietor_age"] = "40"
		sole["answers"]["proprietor_citizenship"] = "Kenyan"
		saved = save_confidential_business_questionnaire(self.ref, {"entities": [sole]})
		self.assertEqual(saved["entities"][0]["entity_type"], "sole_proprietor")
		status = derive_cbq_section_status({"entities": saved["entities"]})
		self.assertIn(status, ("In Progress", "Needs Attention", "Complete"))

		part = _complete_company_entity(ent)
		part["entity_type"] = "partnership"
		part["answers"].pop("directors", None)
		part["answers"].pop("company_type", None)
		part["answers"]["partners"] = [{"name": "Partner A", "shares_percent": "50"}]
		saved2 = save_confidential_business_questionnaire(self.ref, {"entities": [part]})
		val = saved2.get("validation") or {}
		self.assertTrue(val.get("issues") or derive_cbq_section_status(saved2) != "Complete")

	def test_disclosure_and_conflict_matrix(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = _complete_company_entity(dto["entities"][0])
		ent["answers"]["pe_interest_disclosure"] = "yes"
		ent["answers"]["pe_interest_details"] = ""
		ent["answers"]["pe_interest_people"] = []
		ent["conflict_rows"]["q1_common_ownership"] = {"answer": "yes", "details": ""}
		saved = save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		self.assertTrue((saved.get("validation") or {}).get("issues"), saved.get("validation"))
		ent["answers"]["pe_interest_people"] = [
			{"name": "Officer A", "designation": "Manager", "interest": "Sibling"}
		]
		ent["conflict_rows"]["q1_common_ownership"] = {"answer": "yes", "details": "Shared holding"}
		saved2 = save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		detail_issues = [
			i
			for i in (saved2.get("validation") or {}).get("issues") or []
			if "detail" in cstr(i.get("code")) or "conditional" in cstr(i.get("code"))
		]
		self.assertFalse(detail_issues, detail_issues)

	def test_forbidden_override_stripped(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = _complete_company_entity(dto["entities"][0])
		ent["answers"]["verified_full_name_override"] = "Hacker Name"
		saved = save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		blob = json.dumps(saved.get("entities"))
		self.assertNotIn("Hacker Name", blob)
		self.assertNotIn("verified_full_name_override", blob)

	def test_certify_requires_payload_and_invalidates(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = _complete_company_entity(dto["entities"][0])
		saved = save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		eid = saved["entities"][0]["entity_id"]
		with self.assertRaises(frappe.ValidationError):
			certify_cbq_entity(self.ref, eid)
		certified = certify_cbq_entity(
			self.ref,
			eid,
			certifier_name="Alice Authorised",
			certifier_title="Director",
			authority_affirmed=1,
		)
		row = next(e for e in certified["entities"] if e["entity_id"] == eid)
		self.assertTrue(row.get("certified"))
		self.assertEqual(row.get("certifier_name"), "Alice Authorised")
		self.assertEqual(row.get("certified_for"), row.get("legal_name"))
		self.assertEqual(row.get("certified_for"), "Acme Systems Ltd")
		self.assertEqual(derive_cbq_section_status(certified), "Complete")
		display = cstr(row.get("certified_at_display") or "")
		self.assertTrue(display, "certified_at_display required for UI")
		self.assertRegex(display, r"^\d{1,2} \w+ \d{4}, \d{1,2}:\d{2} [ap]\.m\. ")
		self.assertNotIn(".", display.split(",")[0])  # no microseconds in date part
		self.assertNotRegex(display, r"\.\d{3,}")
		ent2 = copy.deepcopy(row)
		ent2["answers"]["nature_of_business"] = "Changed business nature"
		after = save_confidential_business_questionnaire(self.ref, {"entities": [ent2]})
		self.assertFalse(after["entities"][0].get("certified"))
		self.assertNotEqual(derive_cbq_section_status(after), "Complete")

	def test_amend_clears_certification_record(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = _complete_company_entity(dto["entities"][0])
		saved = save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		eid = saved["entities"][0]["entity_id"]
		certified = certify_cbq_entity(
			self.ref,
			eid,
			certifier_name="Alice Authorised",
			certifier_title="Director",
			authority_affirmed=1,
		)
		self.assertTrue(certified["entities"][0].get("certified"))
		self.assertEqual(derive_cbq_section_status(certified), "Complete")
		amended = amend_cbq_certification(self.ref, eid)
		row = amended["entities"][0]
		self.assertFalse(row.get("certified"))
		self.assertEqual(cstr(row.get("certified_for") or ""), "")
		self.assertEqual(cstr(row.get("certifier_name") or ""), "")
		self.assertEqual(cstr(row.get("cert_digest") or ""), "")
		self.assertNotEqual(derive_cbq_section_status(amended), "Complete")

	def test_format_certified_at_display_human_readable(self):
		from datetime import datetime
		from zoneinfo import ZoneInfo

		dt = datetime(2026, 7, 25, 13, 47, 12, 345678, tzinfo=ZoneInfo("Africa/Nairobi"))
		self.assertEqual(
			format_certified_at_display(dt),
			"25 July 2026, 1:47 p.m. EAT",
		)
		self.assertEqual(format_certified_at_display(""), "")
		self.assertEqual(format_certified_at_display(None), "")

	def test_bidder_isolation(self):
		dto = get_confidential_business_questionnaire(self.ref)
		ent = _complete_company_entity(dto["entities"][0])
		save_confidential_business_questionnaire(self.ref, {"entities": [ent]})
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_confidential_business_questionnaire(self.ref)
		frappe.set_user("Administrator")


class TestLeanS300CbqWeb(IntegrationTestCase):
	def setUp(self):
		clear_website_cache()
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def tearDown(self):
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		frappe.set_user("Administrator")

	def test_cbq_page_renders(self):
		path = portal_cbq_url(self.ref)
		set_request(method="GET", path=path)
		resp = get_response()
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-s300-cbq-root"', body)
		self.assertIn('data-testid="kt-s300-stepper"', body)
		for n in range(1, 6):
			self.assertIn(f'data-testid="kt-s300-step-btn-{n}"', body)
		self.assertIn('data-testid="kt-s300-save-draft"', body)
		self.assertIn('data-testid="kt-s300-tender-aside"', body)
		self.assertIn("Tender Details", body)
		self.assertIn("Confidential Business Questionnaire", body)
		self.assertIn('data-testid="kt-a2-sidebar"', body)
		self.assertNotIn('data-testid="kt-a2-sidebar-ref"', body)
		self.assertNotIn('data-testid="kt-a2-sidebar-tender"', body)
		self.assertNotIn("kt-s300-tender-bar", body)
		self.assertNotIn("kt-s300-verified-profile", body)
		self.assertNotIn("cdn.tailwindcss.com", body)
		self.assertNotIn("Microsoft partnership", body)
		self.assertIn("Submission Review", body)
		# step_5_3 markers: in-canvas tender meta + review card (hidden when certified via JS).
		self.assertIn('data-testid="kt-s300-step5-tender-meta"', body)
		self.assertIn('data-testid="kt-s300-review-card"', body)
		self.assertIn("kt-s300-step-connector", body)
		self.assertIn("Procuring Entity", body)
		# Stitch footer: fixed bar outside the page canvas (not an inset floating card).
		self.assertIn('data-testid="kt-s300-footer"', body)
		page_end = body.find("<!-- /.kt-s300-page -->")
		footer_idx = body.find('data-testid="kt-s300-footer"')
		self.assertGreater(page_end, 0)
		self.assertGreater(footer_idx, page_end, "footer must sit outside .kt-s300-page")
		self.assertIn('data-testid="kt-s300-certify-dialog"', body)
		self.assertIn("Certify this questionnaire?", body)
		self.assertIn('data-testid="kt-s300-certify-dialog-fields"', body)
		self.assertIn(
			"Changes made after certification will require this questionnaire to be certified again.",
			body,
		)
		# Certifier inputs belong in the dialog only — not an on-page cert form (step_5_1).
		self.assertNotIn('data-testid="kt-s300-cert-form"', body)
		dialog_idx = body.find('data-testid="kt-s300-certify-dialog"')
		fields_idx = body.find('data-cert="certifier_name"')
		step5_idx = body.find('data-testid="kt-s300-step-5"')
		self.assertGreater(dialog_idx, 0)
		self.assertGreater(fields_idx, dialog_idx, "certifier_name must be inside certify dialog")
		self.assertGreater(fields_idx, step5_idx)
		self.assertIn('data-testid="kt-s300-cert-record"', body)
		self.assertIn("Questionnaire certified", body)
		self.assertIn('data-testid="kt-s300-amend"', body)
		self.assertIn('data-testid="kt-s300-amend-dialog"', body)
		self.assertIn("Amend this questionnaire?", body)
		self.assertIn('data-testid="kt-s300-return-checklist"', body)
		self.assertIn("Changing an answer will remove the current certification.", body)
		self.assertNotIn("Questionnaire complete —", body)
		self.assertNotIn('data-testid="kt-s300-cert-done"', body)
		self.assertNotIn("digital signature", body.lower())


if __name__ == "__main__":
	unittest.main()
