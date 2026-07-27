# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Security — mode resolver, instrument validation, declaration certify."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

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
from kentender_procurement.tender_configurations.services.electronic_std_template import (
	resolve_tender_security_mode,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	get_submission_checklist,
)
from kentender_procurement.tender_configurations.services.tender_security import (
	MODE_DECLARATION,
	MODE_INSTRUMENT,
	MODE_NONE,
	SECTION_KEY,
	applicant_name_from_responses,
	certify_tender_securing_declaration,
	get_tender_security,
	invalidate_tender_securing_declaration,
	save_tender_security,
	validate_instrument_response,
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
			"tender_notice": "Tender Security notice.",
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


def _set_tds_security(cfg_id: str, **fields) -> None:
	raw = frappe.db.get_value("Tender Configuration", cfg_id, "tds_values")
	tds = _parse_json(raw, {})
	if not isinstance(tds, dict):
		tds = {}
	tds.update(fields)
	frappe.db.set_value(
		"Tender Configuration", cfg_id, "tds_values", json.dumps(tds, ensure_ascii=False)
	)
	frappe.db.commit()


def _seed_cbq(cfg_id: str, *, legal_name: str = "Lean Demo Bidder Ltd") -> None:
	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	responses = _parse_json(doc.responses, {})
	responses["confidential_business_questionnaire"] = {
		"entities": [
			{
				"entity_id": "ent-bidder-1",
				"role": "bidder",
				"legal_name": legal_name,
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
			}
		],
		"history": [],
	}
	doc.responses = json.dumps(responses, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	frappe.db.commit()


class TestTenderSecurityModeResolver(unittest.TestCase):
	def test_modes_mutually_exclusive(self):
		self.assertEqual(
			resolve_tender_security_mode(
				{"tender_security_required": "Yes", "tender_security_type": "Tender Security"}
			),
			MODE_INSTRUMENT,
		)
		self.assertEqual(
			resolve_tender_security_mode(
				{
					"tender_security_required": "Yes",
					"tender_security_type": "Tender-Securing Declaration",
				}
			),
			MODE_DECLARATION,
		)
		self.assertEqual(
			resolve_tender_security_mode(
				{"tender_security_required": "No", "tender_security_type": "Not Required"}
			),
			MODE_NONE,
		)

	def test_none_when_not_required(self):
		self.assertEqual(
			resolve_tender_security_mode({"tender_security_required": "No"}),
			MODE_NONE,
		)

	def test_legacy_required_yes_without_type_is_instrument(self):
		self.assertEqual(
			resolve_tender_security_mode({"tender_security_required": "Yes"}),
			MODE_INSTRUMENT,
		)

	def test_template_has_no_nssf_hardcode(self):
		path = Path(__file__).resolve().parents[1] / "electronic_std_templates" / "ppra_it_std_v1.json"
		text = path.read_text(encoding="utf-8")
		self.assertNotIn("NSSF", text)
		blob = json.loads(text)
		sec = next(s for s in blob["sections"] if s["section_key"] == "tender_security")
		self.assertEqual(sec["slice_status"], "tender_security_implemented")
		self.assertEqual(sec["applicability"]["when"], "tender_security_applicable")


def _prepare_cfg() -> str:
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "Tender Security lean test scope.",
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	return cfg_id


class TestLeanTenderSecurityInstrument(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id = _prepare_cfg()
		_set_tds_security(
			self.cfg_id,
			tender_security_required="Yes",
			tender_security_type="Tender Security",
			tender_security_amount="50000",
			tender_security_currency="KES",
			tender_security_validity_period="14",
			tender_security_validity_unit="days",
		)
		self.ref = _publish_cfg(self.cfg_id)
		_seed_cbq(self.cfg_id)

	def test_checklist_includes_instrument_title(self):
		out = get_submission_checklist(self.ref)
		row = next(s for s in out["sections"] if s["section_key"] == SECTION_KEY)
		self.assertIn("Tender Security", row["title"])
		self.assertIn("/sections/tender_security", row["action_url"])
		self.assertEqual(row["status"], STATUS_NOT_STARTED)

	def test_get_instrument_dto(self):
		dto = get_tender_security(self.ref)
		self.assertEqual(dto["mode"], MODE_INSTRUMENT)
		self.assertEqual(dto["requirements"]["required_amount"], "50000")
		self.assertIn("Bank Guarantee", dto["requirements"]["permitted_instrument_types"])
		self.assertEqual(dto["applicant_name"], "Lean Demo Bidder Ltd")
		html_path = (
			Path(__file__).resolve().parents[2] / "www" / "tenders" / "tender_security.html"
		)
		html = html_path.read_text(encoding="utf-8")
		self.assertIn('data-testid="kt-sec-root"', html)
		self.assertNotIn("Verified", html)
		self.assertNotIn("Approved", html)

	def test_instrument_validation_amount_and_issuer(self):
		section = {
			"default_permitted_instrument_types": ["Bank Guarantee"],
			"default_permitted_electronic_routes": [{"route_key": "upload", "label": "Upload"}],
			"lot_coverage_mode": "tender_level",
		}
		owned = {"required_amount": "50000", "required_currency": "KES"}
		bad = validate_instrument_response(
			section,
			owned,
			{
				"instrument_type": "Bank Guarantee",
				"instrument_number": "BG-1",
				"issuer_legal_name": "Lean Demo Bidder Ltd",
				"issuer_registered_address": "Nairobi",
				"issuer_country": "Kenya",
				"issue_date": "2026-07-01",
				"expiry_date": "2026-12-31",
				"guaranteed_amount": "1000",
				"currency": "KES",
				"electronic_route": "upload",
				"upload_file_url": "/files/bg.pdf",
			},
			applicant_name="Lean Demo Bidder Ltd",
			required_validity_date="2026-08-01",
		)
		msgs = " ".join(i["message"] for i in bad["issues"])
		self.assertIn("cannot be the tenderer", msgs)
		self.assertIn("required amount", msgs.lower())

	def test_save_complete_instrument(self):
		dto = get_tender_security(self.ref)
		req_date = dto["requirements"]["required_validity_date"] or "2026-12-31"
		out = save_tender_security(
			self.ref,
			{
				"instrument": {
					"instrument_type": "Bank Guarantee",
					"instrument_number": "BG-100",
					"issuer_legal_name": "Kenya Commercial Bank",
					"issuer_registered_address": "Nairobi CBD",
					"issuer_country": "Kenya",
					"issue_date": "2026-07-01",
					"expiry_date": req_date,
					"guaranteed_amount": "50000",
					"currency": "KES",
					"electronic_route": "upload",
					"upload_file_url": "/files/bg-electronic.pdf",
					"upload_file_name": "bg-electronic.pdf",
				}
			},
		)
		self.assertEqual(out["section_status"], STATUS_COMPLETE)
		cl = get_submission_checklist(self.ref)
		row = next(s for s in cl["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(row["status"], STATUS_COMPLETE)


class TestLeanTenderSecurityDeclaration(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id = _prepare_cfg()
		_set_tds_security(
			self.cfg_id,
			tender_security_required="Yes",
			tender_security_type="Tender-Securing Declaration",
		)
		self.ref = _publish_cfg(self.cfg_id)
		_seed_cbq(self.cfg_id)

	def test_checklist_declaration_title(self):
		out = get_submission_checklist(self.ref)
		row = next(s for s in out["sections"] if s["section_key"] == SECTION_KEY)
		self.assertIn("Tender-Securing Declaration", row["title"])

	def test_certify_and_invalidate(self):
		dto = get_tender_security(self.ref)
		self.assertEqual(dto["mode"], MODE_DECLARATION)
		self.assertEqual(len(dto["declaration"]["suspension_triggers"]), 3)
		keys = {t["trigger_key"] for t in dto["declaration"]["suspension_triggers"]}
		self.assertEqual(
			keys,
			{
				"withdrawal_during_validity",
				"fail_execute_contract",
				"fail_furnish_performance_security",
			},
		)
		self.assertEqual(dto["can_certify"], 1)
		certified = certify_tender_securing_declaration(self.ref)
		self.assertEqual(certified["certification"]["certified"], 1)
		self.assertEqual(certified["section_status"], STATUS_COMPLETE)
		cl = get_submission_checklist(self.ref)
		row = next(s for s in cl["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(row["status"], STATUS_COMPLETE)

		draft = create_or_get_draft(self.cfg_id)
		doc = _get_bid(cstr(draft.get("bid_id") or ""))
		invalidate_tender_securing_declaration(doc, reason="test")
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		again = get_tender_security(self.ref)
		self.assertEqual(again["certification"]["requires_recertification"], 1)
		self.assertEqual(again["section_status"], STATUS_NEEDS_ATTENTION)


class TestLeanTenderSecurityNone(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id = _prepare_cfg()
		_set_tds_security(
			self.cfg_id,
			tender_security_required="No",
			tender_security_type="Not Required",
		)
		self.ref = _publish_cfg(self.cfg_id)

	def test_none_omits_checklist_row(self):
		out = get_submission_checklist(self.ref)
		keys = [s["section_key"] for s in out["sections"]]
		self.assertNotIn(SECTION_KEY, keys)


class TestApplicantName(unittest.TestCase):
	def test_single_bidder(self):
		name = applicant_name_from_responses(
			{
				"confidential_business_questionnaire": {
					"entities": [{"role": "bidder", "legal_name": "Acme Ltd", "answers": {}}]
				}
			}
		)
		self.assertEqual(name, "Acme Ltd")

	def test_intended_jv_members(self):
		name = applicant_name_from_responses(
			{
				"confidential_business_questionnaire": {
					"entities": [
						{
							"role": "bidder",
							"legal_name": "Lead Co",
							"entity_type": "intended_jv",
							"answers": {
								"jv_mode": "intended",
								"jv_intended_members": [
									{"legal_name": "Member A"},
									{"legal_name": "Member B"},
								],
							},
						}
					]
				}
			}
		)
		self.assertEqual(name, "Member A; Member B")


if __name__ == "__main__":
	unittest.main()
