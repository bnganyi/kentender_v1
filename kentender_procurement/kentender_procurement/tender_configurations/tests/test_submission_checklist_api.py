# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A2 Submission Checklist — domain API contract tests."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
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
	save_section_responses,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	ACTION_CONTINUE,
	ACTION_FIX_ISSUES,
	ACTION_START_FIRST,
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_LOCKED,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	build_section_last_updated_map,
	format_section_last_updated,
	get_submission_checklist,
	portal_workspace_url,
	resolve_checklist_primary_action,
	resolve_section_status,
)


class TestSubmissionChecklistHelpers(unittest.TestCase):
	def test_last_updated_is_per_section_not_bid_modified(self):
		"""Regression: checklist must not stamp every started row with bid.modified."""
		events = [
			{
				"event": "section_saved",
				"event_at": "2026-07-26 10:00:00",
				"detail_json": json.dumps({"section_key": "form_of_tender"}),
			},
			{
				"event": "section_saved",
				"event_at": "2026-07-26 12:30:00",
				"detail_json": json.dumps({"section_key": "form_of_tender"}),
			},
			{
				"event": "section_saved",
				"event_at": "2026-07-26 11:15:00",
				"detail_json": json.dumps({"section_key": "tender_security"}),
			},
			{
				"event": "section_saved",
				"event_at": "2026-07-26 20:35:59",
				"detail_json": json.dumps({"section_key": "*"}),
			},
			{
				"event": "qualification_category_saved",
				"event_at": "2026-07-26 13:00:00",
				"detail_json": json.dumps({"category_key": "experience"}),
			},
		]
		responses = {
			"tender_documents_and_addenda": {
				"acknowledged": True,
				"acknowledged_at": "2026-07-26 09:05:00",
			},
			"preliminary_requirements_and_evidence": {
				"PRELIM-01": {"saved_at": "2026-07-26 14:00:00", "upload": {"file_name": "a.pdf"}},
			},
		}
		mapped = build_section_last_updated_map(events, responses)
		self.assertEqual(
			format_section_last_updated(mapped["form_of_tender"]),
			format_section_last_updated("2026-07-26 12:30:00"),
		)
		self.assertEqual(
			format_section_last_updated(mapped["tender_security"]),
			format_section_last_updated("2026-07-26 11:15:00"),
		)
		self.assertEqual(
			format_section_last_updated(mapped["tender_documents_and_addenda"]),
			format_section_last_updated("2026-07-26 09:05:00"),
		)
		self.assertEqual(
			format_section_last_updated(mapped["qualification_and_capability"]),
			format_section_last_updated("2026-07-26 13:00:00"),
		)
		self.assertEqual(
			format_section_last_updated(mapped["preliminary_requirements_and_evidence"]),
			format_section_last_updated("2026-07-26 14:00:00"),
		)
		# Wildcard fill/bulk events must not invent a shared stamp for every section.
		self.assertNotIn("*", mapped)
		stamps = {
			format_section_last_updated(mapped["form_of_tender"]),
			format_section_last_updated(mapped["tender_security"]),
			format_section_last_updated(mapped["tender_documents_and_addenda"]),
		}
		self.assertEqual(len(stamps), 3)

	def test_section_status_matrix(self):
		self.assertEqual(
			resolve_section_status(required=True, has_responses=False),
			STATUS_NOT_STARTED,
		)
		self.assertEqual(
			resolve_section_status(required=True, has_responses=True),
			STATUS_COMPLETE,
		)
		self.assertEqual(
			resolve_section_status(
				required=True, has_responses=True, has_validation_blockers=True
			),
			STATUS_NEEDS_ATTENTION,
		)
		self.assertEqual(
			resolve_section_status(required=True, has_responses=True, is_partial=True),
			STATUS_IN_PROGRESS,
		)
		self.assertEqual(
			resolve_section_status(required=True, has_responses=False, is_locked=True),
			STATUS_LOCKED,
		)
		self.assertEqual(
			resolve_section_status(required=False, has_responses=False, not_applicable=True),
			"Not Applicable",
		)

	def test_primary_action_matrix(self):
		self.assertEqual(
			resolve_checklist_primary_action(
				bid_sealed=False, any_started=False, has_blockers=False, all_required_complete=False
			)[0],
			ACTION_START_FIRST,
		)
		self.assertEqual(
			resolve_checklist_primary_action(
				bid_sealed=False, any_started=True, has_blockers=True, all_required_complete=False
			)[0],
			ACTION_FIX_ISSUES,
		)
		self.assertEqual(
			resolve_checklist_primary_action(
				bid_sealed=False, any_started=True, has_blockers=False, all_required_complete=False
			)[0],
			ACTION_CONTINUE,
		)
		self.assertEqual(
			resolve_checklist_primary_action(
				bid_sealed=True, any_started=True, has_blockers=False, all_required_complete=True
			)[0],
			"View Receipt",
		)

	def test_portal_workspace_url(self):
		self.assertEqual(portal_workspace_url("PUB-TEST-1"), "/tenders/PUB-TEST-1/workspace")


class TestSubmissionChecklistApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"std_version": CANONICAL_PACKAGE_ID,
				"bidder_submission_schema": json.dumps(
					{
						"version": 1,
						"sections": [
							{"key": "eligibility", "title": "Eligibility", "required": True},
							{"key": "technical", "title": "Technical Response", "required": True},
							{"key": "notes", "title": "Optional Notes", "required": False},
						],
					}
				),
				"short_scope_summary": "A2 checklist scope.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		for name in frappe.get_all(
			"Electronic Bid Submission",
			filters={"configuration": self.cfg_id},
			pluck="name",
		):
			frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
		frappe.db.commit()

	def _publish(self):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen.get("preview_status"), "Generated", gen.get("render_exception"))
		conf = confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		pub_id = conf["publication_id"]
		now = now_datetime()
		save_publication_setup(
			pub_id,
			{
				"publication_mode": "immediate",
				"publication_datetime": str(now),
				"tender_notice": "A2 checklist notice.",
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
		self.assertTrue(ref.startswith("PUB-"), ref)
		return ref

	def test_guest_denied(self):
		ref = self._publish()
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_submission_checklist(ref)

	def test_checklist_schema_driven_start_first(self):
		ref = self._publish()
		out = get_submission_checklist(ref)
		self.assertEqual(out["published_tender_ref"], ref)
		self.assertTrue(out["workspace_url"].endswith("/workspace"))
		self.assertIn("/tenders/", out["workspace_url"])
		self.assertEqual(out["primary_action"], ACTION_START_FIRST)
		self.assertEqual(len(out["sections"]), 10)
		keys = [s["section_key"] for s in out["sections"]]
		self.assertEqual(keys[0], "tender_documents_and_addenda")
		self.assertEqual(keys[-2], "price_schedule")
		self.assertEqual(keys[-1], "form_of_tender")
		self.assertIn("tender_security", keys)
		for s in out["sections"]:
			if not s["required"]:
				continue
			self.assertIn(s["status"], (STATUS_NOT_STARTED, STATUS_LOCKED), s)
		fot = next(s for s in out["sections"] if s["section_key"] == "form_of_tender")
		self.assertIn("/sections/form_of_tender", fot["action_url"])

	def test_partial_progress_keeps_unstarted_not_attention(self):
		"""Unstarted required sections stay Not Started / Start — not Needs Attention blockers."""
		from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
			acknowledge_tender_documents,
		)

		ref = self._publish()
		out = get_submission_checklist(ref)
		self.assertNotIn("bid_id", out)
		docs_key = "tender_documents_and_addenda"
		other_key = "confidential_business_questionnaire"
		frappe.set_user("Administrator")
		acknowledge_tender_documents(ref)
		out2 = get_submission_checklist(ref)
		self.assertEqual(out2["primary_action"], ACTION_CONTINUE)
		self.assertEqual(out2["has_blockers"], 0)
		self.assertFalse(out2.get("current_issues_summary"))
		first = next(s for s in out2["sections"] if s["section_key"] == docs_key)
		self.assertEqual(first["status"], STATUS_COMPLETE)
		self.assertIn(first["action_label"], ("View", "Review"))
		second = next(s for s in out2["sections"] if s["section_key"] == other_key)
		self.assertEqual(second["status"], STATUS_NOT_STARTED)
		self.assertEqual(second["action_label"], "Start")
		self.assertEqual(second["issues_label"], "—")

	def test_needs_attention_only_for_validation_failures(self):
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)
		from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
			acknowledge_tender_documents,
		)

		ref = self._publish()
		get_submission_checklist(ref)
		bid_id = resolve_published_tender_backend(ref)["bid_id"]
		other_key = "confidential_business_questionnaire"
		acknowledge_tender_documents(ref)
		# Incomplete CBQ entity → specialized derive reports Needs Attention.
		save_section_responses(
			bid_id,
			other_key,
			{
				"entities": [
					{
						"entity_id": "ent-bidder-1",
						"role": "bidder",
						"legal_name": "Partial Bidder Ltd",
						"entity_type": "company",
						"answers": {},
						"certified": 0,
					}
				]
			},
		)
		out2 = get_submission_checklist(ref)
		second = next(s for s in out2["sections"] if s["section_key"] == other_key)
		self.assertEqual(second["status"], STATUS_NEEDS_ATTENTION)
		self.assertEqual(second["action_label"], "Resolve")
		self.assertIn("Blocker", second["issues_label"])
		self.assertEqual(out2["primary_action"], ACTION_FIX_ISSUES)
		self.assertEqual(out2["has_blockers"], 1)

	def test_lean_checklist_has_no_pack10_final_section(self):
		"""Review/Submit are workflow steps — not checklist rows in the lean template."""
		ref = self._publish()
		out = get_submission_checklist(ref)
		keys = {s["section_key"] for s in out["sections"]}
		self.assertNotIn("final_declaration_and_submit", keys)
		# Incomplete lean bid still continues preparation (not Review CTA yet).
		self.assertNotIn(
			out["primary_action"],
			("Submit & Seal Bid", "Review & Validate Bid"),
		)

	def test_contract_conditions_label_override(self):
		ref = self._publish()
		out = get_submission_checklist(ref)
		row = next(
			(s for s in out["sections"] if s["section_key"] == "contract_terms_acknowledgement"),
			None,
		)
		if row is None:
			self.skipTest("lean checklist has no contract_terms_acknowledgement section")
		self.assertIn("Contract Conditions Acknowledgement", row["title"])
		self.assertNotIn("Contract Terms Acknowledgement", row["title"])

	def _cbq_in_progress_payload(self) -> dict:
		"""Valid-enough CBQ body that is started but not certified (In Progress)."""
		from kentender_procurement.tender_configurations.tests.test_lean_s300_confidential_business_questionnaire import (
			_all_conflicts_no,
			_complete_company_entity,
		)

		ent = _complete_company_entity(
			{"entity_id": "ent-bidder-1", "role": "bidder", "legal_name": "Acme Systems Ltd"}
		)
		ent["certified"] = 0
		ent["conflict_rows"] = _all_conflicts_no()
		return {"entities": [ent]}

	def _cbq_needs_attention_payload(self) -> dict:
		return {
			"entities": [
				{
					"entity_id": "ent-bidder-1",
					"role": "bidder",
					"legal_name": "Partial Bidder Ltd",
					"entity_type": "company",
					"answers": {},
					"certified": 0,
				}
			]
		}

	def test_in_progress_resume_action(self):
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)

		ref = self._publish()
		get_submission_checklist(ref)
		bid_id = resolve_published_tender_backend(ref)["bid_id"]
		section_key = "confidential_business_questionnaire"
		save_section_responses(bid_id, section_key, self._cbq_in_progress_payload())
		out2 = get_submission_checklist(ref)
		row = next(s for s in out2["sections"] if s["section_key"] == section_key)
		self.assertEqual(row["status"], STATUS_IN_PROGRESS)
		self.assertEqual(row["action_label"], "Continue")

	def test_progress_percent_complete_only_exposes_in_progress_counters(self):
		"""Blueprint §25.4: % is Complete-only; in-progress is a separate counter."""
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)
		from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
			acknowledge_tender_documents,
		)

		ref = self._publish()
		get_submission_checklist(ref)
		bid_id = resolve_published_tender_backend(ref)["bid_id"]
		acknowledge_tender_documents(ref)
		save_section_responses(
			bid_id,
			"confidential_business_questionnaire",
			self._cbq_in_progress_payload(),
		)
		out = get_submission_checklist(ref)
		self.assertEqual(out["progress_complete"], 1)
		self.assertEqual(out["progress_in_progress"], 1)
		self.assertEqual(out["progress_needs_attention"], 0)
		self.assertGreater(out["progress_total"], 0)
		expected_pct = int(round(100.0 * float(out["progress_complete"]) / float(out["progress_total"])))
		self.assertEqual(out["progress_percent"], expected_pct)
		# In Progress must not inflate the bar (would be 2/total if weighted equally).
		weighted_if_half = int(
			round(100.0 * (float(out["progress_complete"]) + 0.5) / float(out["progress_total"]))
		)
		self.assertNotEqual(out["progress_percent"], weighted_if_half)
		docs = next(s for s in out["sections"] if s["section_key"] == "tender_documents_and_addenda")
		cbq = next(
			s for s in out["sections"] if s["section_key"] == "confidential_business_questionnaire"
		)
		self.assertNotEqual(docs["last_updated"], "—")
		self.assertNotEqual(cbq["last_updated"], "—")

	def test_progress_needs_attention_counter(self):
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)
		from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
			acknowledge_tender_documents,
		)

		ref = self._publish()
		get_submission_checklist(ref)
		bid_id = resolve_published_tender_backend(ref)["bid_id"]
		acknowledge_tender_documents(ref)
		save_section_responses(
			bid_id,
			"confidential_business_questionnaire",
			self._cbq_needs_attention_payload(),
		)
		out = get_submission_checklist(ref)
		self.assertEqual(out["progress_complete"], 1)
		self.assertEqual(out["progress_needs_attention"], 1)
		self.assertEqual(out["progress_in_progress"], 0)
		expected_pct = int(round(100.0 * float(out["progress_complete"]) / float(out["progress_total"])))
		self.assertEqual(out["progress_percent"], expected_pct)

	def test_rc_route_only_snapshot_checklist_matches_matrix_complete(self):
		"""Regression: empty RC snapshot must hydrate before checklist roll-up."""
		from kentender_procurement.tender_configurations.services.requirement_matrix import (
			get_requirement_drawer,
			get_requirement_matrix,
			save_requirement_response,
		)
		from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
			acknowledge_tender_documents,
		)

		ref = self._publish()
		get_submission_checklist(ref)
		acknowledge_tender_documents(ref)
		pub_name = frappe.db.get_value(
			"IT Tender Publication Record", {"publication_ref": ref}, "name"
		)
		raw = frappe.db.get_value(
			"IT Tender Publication Record", pub_name, "electronic_template_snapshot"
		)
		snap = json.loads(raw or "{}")
		for sec in snap.get("sections") or []:
			if cstr(sec.get("section_key")) == "requirements_compliance":
				sec["requirements"] = []
				sec["response_fields_per_requirement"] = []
				sec["slice_status"] = "route_only_not_editable_in_lean_slice"
				sec["section_type"] = "requirement_matrix"
		# Trap that previously made checklist roll up with zero requirement rows.
		snap.setdefault("collections", {})["requirements"] = [{"requirement_id": "stub"}]
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_name,
			"electronic_template_snapshot",
			json.dumps(snap, ensure_ascii=False),
			update_modified=False,
		)
		frappe.db.commit()

		# Pre-fix: matrix hydrates and can complete; checklist used to stay Not Started.
		mx = get_requirement_matrix(ref, "requirements_compliance", page_size=50)
		self.assertGreaterEqual(int(mx.get("progress_total") or 0), 1)
		# Rows are scoped to the selected domain — walk every group.
		for group in mx.get("groups") or []:
			page = get_requirement_matrix(
				ref,
				"requirements_compliance",
				group=cstr(group.get("group_key") or ""),
				page_size=50,
			)
			for row in page.get("rows") or []:
				if not int(row.get("mandatory") or 0):
					continue
				rid = cstr(row.get("requirement_id") or "")
				drawer = get_requirement_drawer(ref, "requirements_compliance", rid)
				payload: dict = {}
				for field in drawer.get("fields") or []:
					fkey = cstr(field.get("field_key") or "")
					ftype = cstr(field.get("type") or "")
					if not fkey or not field.get("required"):
						continue
					if ftype == "file":
						payload[fkey] = [
							{
								"file_name": f"{rid}.pdf",
								"mock": 1,
								"byte_size": 120,
								"uploaded_at": str(now_datetime()),
							}
						]
					elif ftype == "number":
						payload[fkey] = "100"
					elif ftype == "boolean":
						payload[fkey] = 1
					elif ftype == "repeating_table":
						payload[fkey] = [{"activity": "Integration", "timing": "Week 1"}]
					else:
						payload[fkey] = (
							"Yes" if "yes" in fkey.lower() else "Complete for checklist regression."
						)
				save_requirement_response(ref, "requirements_compliance", rid, payload)

		mx2 = get_requirement_matrix(ref, "requirements_compliance", page_size=50)
		self.assertEqual(mx2.get("section_status"), STATUS_COMPLETE, mx2.get("progress_label"))
		self.assertEqual(mx2.get("progress_complete"), mx2.get("progress_total"))

		cl = get_submission_checklist(ref)
		rc = next(s for s in cl["sections"] if s["section_key"] == "requirements_compliance")
		self.assertEqual(rc["status"], STATUS_COMPLETE, rc)
		self.assertIn(rc["action_label"], ("Review", "View"))


if __name__ == "__main__":
	unittest.main()
