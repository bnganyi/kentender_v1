# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Qualification and Capability — fixtures, EXP-1 years, status, checklist roll-up."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.lean_qualification_criteria import (
	CATEGORY_EXPERIENCE,
	CATEGORY_FINANCIAL,
	CATEGORY_PARTNERS,
	CATEGORY_PERSONNEL,
	FIXTURE_CONDITIONAL,
	FIXTURE_FULL,
	FIXTURE_REDUCED,
	lean_qualification_categories,
	merge_qualification_into_evaluation,
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
from kentender_procurement.tender_configurations.services.electronic_std_template import (
	materialize_qualification_categories,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.qualification_and_capability import (
	SECTION_KEY,
	derive_category_state,
	derive_qualification_section_status,
	get_qualification_and_capability,
	get_qualification_category,
	qualification_blocker_messages,
	qualifying_calendar_years,
	save_qualification_category,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NOT_APPLICABLE,
	STATUS_NOT_STARTED,
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
			"tender_notice": "Qualification notice.",
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


def _apply_fixture(cfg_id: str, fixture: str) -> None:
	raw = frappe.db.get_value("Tender Configuration", cfg_id, "evaluation_setup")
	try:
		ev = json.loads(raw) if raw else {}
	except Exception:
		ev = {}
	if not isinstance(ev, dict):
		ev = {}
	merged = merge_qualification_into_evaluation(ev, fixture=fixture)
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"evaluation_setup": json.dumps(merged),
		},
	)


class TestQualifyingCalendarYears(unittest.TestCase):
	def test_nine_month_rule_not_project_count(self):
		# One long contract spanning 5+ years with full-year coverage → many years, one project.
		contracts = [
			{
				"start_year": 2018,
				"start_month": 1,
				"end_year": 2023,
				"end_month": 12,
			}
		]
		years = qualifying_calendar_years(contracts, min_months_in_year=9)
		self.assertGreaterEqual(len(years), 5)
		self.assertEqual(len(contracts), 1)

	def test_short_year_does_not_qualify(self):
		contracts = [
			{"start_year": 2022, "start_month": 1, "end_year": 2022, "end_month": 6},
		]
		years = qualifying_calendar_years(contracts, min_months_in_year=9)
		self.assertEqual(years, [])

	def test_union_across_contracts_in_same_year(self):
		contracts = [
			{"start_year": 2021, "start_month": 1, "end_year": 2021, "end_month": 5},
			{"start_year": 2021, "start_month": 4, "end_year": 2021, "end_month": 10},
		]
		years = qualifying_calendar_years(contracts, min_months_in_year=9)
		self.assertEqual(years, [2021])


class TestQualificationFixtures(unittest.TestCase):
	def test_materialize_full_five_categories(self):
		cats = materialize_qualification_categories(
			{"qualification_categories": lean_qualification_categories(FIXTURE_FULL)}
		)
		keys = [c["category_key"] for c in cats]
		self.assertEqual(len(keys), 5)
		self.assertIn(CATEGORY_FINANCIAL, keys)
		self.assertIn(CATEGORY_EXPERIENCE, keys)

	def test_reduced_excludes_non_financial_experience(self):
		cats = materialize_qualification_categories(
			{"qualification_categories": lean_qualification_categories(FIXTURE_REDUCED)}
		)
		visible_modes = {c["category_key"]: c["requirement_mode"] for c in cats}
		# Excluded categories still materialize with mode excluded (for config audit) —
		# materialize keeps excluded rows; overview filters them.
		self.assertEqual(visible_modes.get(CATEGORY_FINANCIAL), "required")
		self.assertEqual(visible_modes.get(CATEGORY_EXPERIENCE), "required")

	def test_conditional_personnel_optional_partners_conditional(self):
		cats = lean_qualification_categories(FIXTURE_CONDITIONAL)
		by = {c["category_key"]: c for c in cats}
		self.assertEqual(by[CATEGORY_PERSONNEL]["requirement_mode"], "optional")
		self.assertEqual(by[CATEGORY_PARTNERS]["requirement_mode"], "conditional")


class TestQualificationApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"std_version": CANONICAL_PACKAGE_ID,
				"short_scope_summary": "Lean qualification and capability domain tests.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		# Apply after seed helper (it rewrites evaluation_setup to the full fixture).
		_apply_fixture(self.cfg_id, FIXTURE_FULL)
		for name in frappe.get_all(
			"Electronic Bid Submission",
			filters={"configuration": self.cfg_id},
			pluck="name",
		):
			frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
		frappe.db.commit()
		self.ref = _publish_cfg(self.cfg_id)

	def test_overview_full_fixture_lists_required_categories(self):
		out = get_qualification_and_capability(self.ref)
		self.assertEqual(out["section_key"], SECTION_KEY)
		keys = [r["category_key"] for r in out["categories"]]
		self.assertEqual(len(keys), 5)
		self.assertEqual(out["progress_total"], 5)
		self.assertEqual(out["progress_complete"], 0)
		self.assertIn("required categories complete", out["progress_label"])
		blob = json.dumps(out).lower()
		self.assertNotIn('"score"', blob)
		self.assertNotIn("passed", blob)
		self.assertNotIn("failed", blob)

	def test_financial_status_transition(self):
		out = get_qualification_and_capability(self.ref)
		self.assertEqual(out["section_status"], STATUS_NOT_STARTED)
		saved = save_qualification_category(
			self.ref,
			CATEGORY_FINANCIAL,
			{
				"bucket": {
					"financial_years": [
						{"year": "2023", "statement_attached": 1, "file_name": "fs-2023.pdf"},
						{"year": "2024", "statement_attached": 1, "file_name": "fs-2024.pdf"},
						{"year": "2025", "statement_attached": 1, "file_name": "fs-2025.pdf"},
					],
					"turnover": {"average_amount": 15000000, "currency": "KES"},
					"resources": {"amount": 5000000, "currency": "KES", "evidence_id": "ev-1"},
				}
			},
		)
		self.assertEqual(saved["status"], STATUS_COMPLETE)
		overview = get_qualification_and_capability(self.ref)
		self.assertEqual(overview["section_status"], STATUS_IN_PROGRESS)
		self.assertEqual(overview["progress_complete"], 1)
		fin = next(r for r in overview["categories"] if r["category_key"] == CATEGORY_FINANCIAL)
		self.assertEqual(fin["status"], STATUS_COMPLETE)

	def test_experience_years_not_project_counts_on_save(self):
		save_qualification_category(
			self.ref,
			CATEGORY_EXPERIENCE,
			{
				"projects": [
					{
						"project_id": "proj-long",
						"contract_id": "C-1",
						"start_year": 2018,
						"start_month": 1,
						"end_year": 2023,
						"end_month": 12,
						"use_for_general": 1,
						"use_for_specific": 1,
						"description": "ERP rollout",
						"procuring_entity": "Public Entity A",
						"amount": 20000000,
						"currency": "KES",
					},
					{
						"project_id": "proj-b",
						"contract_id": "C-2",
						"start_year": 2020,
						"start_month": 1,
						"end_year": 2021,
						"end_month": 12,
						"use_for_general": 0,
						"use_for_specific": 1,
						"description": "Integration",
						"procuring_entity": "Public Entity B",
						"amount": 8000000,
						"currency": "KES",
					},
				],
				"bucket": {
					"general_project_ids": ["proj-long"],
					"specific_project_ids": ["proj-long", "proj-b"],
				},
			},
		)
		detail = get_qualification_category(self.ref, CATEGORY_EXPERIENCE)
		self.assertGreaterEqual(int(detail.get("qualifying_year_count") or 0), 5)
		self.assertEqual(detail["status"], STATUS_COMPLETE)
		self.assertEqual(int(detail.get("min_qualifying_years") or 0), 5)
		self.assertEqual(int(detail.get("min_months_in_year") or 0), 9)
		self.assertEqual(int(detail.get("min_specific_projects") or 0), 2)
		self.assertEqual(int(detail.get("specific_count") or 0), 2)

	def test_checklist_links_to_qualification_overview(self):
		cl = get_submission_checklist(self.ref)
		row = next(s for s in cl["sections"] if s["section_key"] == SECTION_KEY)
		self.assertTrue(
			row["action_url"].endswith("/sections/qualification_and_capability"),
			row["action_url"],
		)

class TestQualificationFixtureApplicability(unittest.TestCase):
	def test_reduced_fixture_excludes_non_core_from_required_progress(self):
		cats = materialize_qualification_categories(
			{"qualification_categories": lean_qualification_categories(FIXTURE_REDUCED)}
		)
		payload = {"categories": {}, "projects": [], "personnel": [], "organizations": [], "flags": {}}
		visible = []
		req_total = 0
		for cat in cats:
			st = derive_category_state(cat, payload, responses={})
			if st.get("display_mode") == "excluded":
				continue
			visible.append(st["category_key"])
			if st.get("applicable") and st.get("display_mode") == "required":
				req_total += 1
		self.assertEqual(set(visible), {CATEGORY_FINANCIAL, CATEGORY_EXPERIENCE})
		self.assertEqual(req_total, 2)

	def test_conditional_partners_na_until_external_flag(self):
		cats = materialize_qualification_categories(
			{"qualification_categories": lean_qualification_categories(FIXTURE_CONDITIONAL)}
		)
		section = {"categories": cats}
		payload = {"categories": {}, "projects": [], "personnel": [], "organizations": [], "flags": {}}
		partners_cat = next(c for c in cats if c["category_key"] == CATEGORY_PARTNERS)
		personnel_cat = next(c for c in cats if c["category_key"] == CATEGORY_PERSONNEL)
		partners = derive_category_state(partners_cat, payload, responses={})
		self.assertEqual(partners["status"], STATUS_NOT_APPLICABLE)
		personnel = derive_category_state(personnel_cat, payload, responses={})
		self.assertEqual(personnel.get("optional"), 1)
		# required denominator excludes optional + N/A partners
		req_total = sum(
			1
			for c in cats
			if (
				(st := derive_category_state(c, payload, responses={})).get("applicable")
				and st.get("display_mode") == "required"
			)
		)
		self.assertEqual(req_total, 3)
		payload2 = {
			"categories": {CATEGORY_PARTNERS: {"items": {}}},
			"projects": [],
			"personnel": [],
			"organizations": [],
			"flags": {"external_provider_selected": 1},
		}
		partners2 = derive_category_state(partners_cat, payload2, responses={})
		self.assertNotEqual(partners2["status"], STATUS_NOT_APPLICABLE)
		self.assertEqual(partners2["status"], STATUS_NOT_STARTED)
		msgs = qualification_blocker_messages(section, payload2, responses={})
		self.assertTrue(any("Delivery partners" in m for m in msgs), msgs)


class TestQualificationSectionDerive(unittest.TestCase):
	def test_empty_section_not_applicable(self):
		status = derive_qualification_section_status({"categories": []}, {})
		self.assertEqual(status, STATUS_NOT_APPLICABLE)


if __name__ == "__main__":
	unittest.main()
