# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical Proposal — fixtures, status, work-plan validation, checklist roll-up."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.tender_configurations.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
	FIXTURE_CONDITIONAL,
	FIXTURE_CORE,
	FIXTURE_FULL,
	SUB_ALTERNATIVES,
	SUB_APPROACH,
	SUB_INTEGRATION,
	SUB_ORG,
	SUB_TESTING,
	SUB_TRAINING,
	SUB_TRANSITION,
	SUB_WORK_PLAN,
	lean_technical_proposal_subsections,
	merge_technical_proposal_into_evaluation,
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
	materialize_technical_proposal_subsections,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_APPLICABLE,
	get_submission_checklist,
)
from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
	ACTION_CONTINUE,
	ACTION_REVIEW,
	ACTION_START,
	SECTION_KEY,
	STATUS_NOT_STARTED,
	calculate_completion_week,
	confirm_integration_responsibility,
	derive_subsection_state,
	derive_technical_proposal_section_status,
	get_technical_proposal,
	portal_technical_proposal_url,
	save_technical_proposal_subsection,
	validate_work_plan_activities,
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
			"tender_notice": "Technical proposal notice.",
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


def _apply_tp_fixture(cfg_id: str, fixture: str, *, flags: dict | None = None) -> None:
	raw = frappe.db.get_value("Tender Configuration", cfg_id, "evaluation_setup")
	try:
		ev = json.loads(raw) if raw else {}
	except Exception:
		ev = {}
	if not isinstance(ev, dict):
		ev = {}
	merged = merge_technical_proposal_into_evaluation(ev, fixture=fixture, flags=flags)
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"evaluation_setup": json.dumps(merged),
		},
	)


class TestTechnicalProposalFixtures(unittest.TestCase):
	def test_core_only_mandatory_topics(self):
		subs = lean_technical_proposal_subsections(FIXTURE_CORE)
		keys = {s["subsection_key"] for s in subs if s["requirement_mode"] != "excluded"}
		self.assertEqual(keys, {SUB_ORG, SUB_INTEGRATION})

	def test_full_includes_sub_plans(self):
		subs = materialize_technical_proposal_subsections(
			{"technical_proposal_subsections": lean_technical_proposal_subsections(FIXTURE_FULL)}
		)
		keys = {s["subsection_key"] for s in subs}
		self.assertIn(SUB_ORG, keys)
		self.assertIn(SUB_APPROACH, keys)
		self.assertIn(SUB_WORK_PLAN, keys)
		self.assertIn(SUB_INTEGRATION, keys)

	def test_materialize_falls_back_when_config_rows_are_junk(self):
		"""Regression: empty/invalid subsection config must not yield 0 rows."""
		subs = materialize_technical_proposal_subsections(
			{"technical_proposal_subsections": [{"subsection_key": "x"}, {"title": "No key"}]}
		)
		self.assertGreaterEqual(len(subs), 2)
		self.assertIn(SUB_ORG, {s["subsection_key"] for s in subs})

	def test_conditional_optional_training_excluded_migration(self):
		subs = lean_technical_proposal_subsections(FIXTURE_CONDITIONAL)
		by_key = {s["subsection_key"]: s for s in subs}
		self.assertEqual(by_key[SUB_TRAINING]["requirement_mode"], "optional")
		self.assertEqual(by_key[SUB_TRANSITION]["requirement_mode"], "excluded")
		self.assertEqual(by_key[SUB_ALTERNATIVES]["requirement_mode"], "conditional")

	def test_seed_titles_are_generic(self):
		subs = lean_technical_proposal_subsections(FIXTURE_FULL)
		blob = " ".join(cstr(s.get("title")) + " " + cstr(s.get("description")) for s in subs)
		self.assertNotIn("NSSF", blob)
		self.assertNotIn("Pension", blob)


class TestWorkPlanCalculations(unittest.TestCase):
	def test_completion_week(self):
		self.assertEqual(calculate_completion_week(1, 4), 4)
		self.assertEqual(calculate_completion_week(3, 2), 4)
		self.assertIsNone(calculate_completion_week(0, 2))

	def test_invalid_dependency_and_period(self):
		issues = validate_work_plan_activities(
			[
				{
					"activity_id": "a1",
					"activity": "Design",
					"start_week": 1,
					"duration_weeks": 2,
					"dependency_id": "missing",
				},
				{"activity_id": "a2", "activity": "Cutover", "start_week": 50, "duration_weeks": 10},
			],
			max_completion_weeks=52,
		)
		self.assertTrue(any("Design" in i and "dependency" in i.lower() for i in issues))
		self.assertFalse(any("Activity a1:" in i for i in issues))
		self.assertTrue(any("exceeds the permitted completion period" in i for i in issues))

	def test_none_dependency_is_allowed(self):
		"""Explicit None / empty dependency must not be flagged as missing."""
		for dep in ("", None, "None", "none", "—", "-"):
			issues = validate_work_plan_activities(
				[
					{
						"activity_id": "a1",
						"activity": "Design",
						"start_week": 1,
						"duration_weeks": 2,
						"dependency_id": dep,
						"project_role": "PM",
					}
				],
				max_completion_weeks=52,
			)
			self.assertFalse(
				any("dependency" in i.lower() for i in issues),
				msg=f"dep={dep!r} raised {issues}",
			)

	def test_work_plan_progress_uses_activity_count_not_min_only(self):
		from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
			_derive_work_plan,
		)

		derived = _derive_work_plan(
			{"min_activities": 1, "max_completion_weeks": 52},
			{
				"activities": [
					{
						"activity_id": "a1",
						"activity": "Integration",
						"start_week": 1,
						"duration_weeks": 2,
						"dependency_id": "",
						"project_role": "PM",
					},
					{
						"activity_id": "a2",
						"activity": "Design",
						"start_week": 1,
						"duration_weeks": 2,
						"dependency_id": "None",
						"project_role": "PM",
					},
				]
			},
		)
		self.assertEqual(derived["progress_text"], "2 of 2 activities complete")
		self.assertEqual(derived["contractual_period_label"], "52 Weeks")
		self.assertEqual(derived["status"], "Complete")
		self.assertFalse(derived.get("issue"))

	def test_circular_dependency(self):
		issues = validate_work_plan_activities(
			[
				{"activity_id": "a1", "start_week": 1, "duration_weeks": 1, "dependency_id": "a2"},
				{"activity_id": "a2", "start_week": 2, "duration_weeks": 1, "dependency_id": "a1"},
			]
		)
		self.assertTrue(any("circular" in i.lower() for i in issues))


def _prepare_tp_cfg(fixture: str, *, flags: dict | None = None) -> tuple[str, str]:
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "Lean technical proposal domain tests.",
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	_apply_tp_fixture(cfg_id, fixture, flags=flags)
	for name in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration": cfg_id},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
	frappe.db.commit()
	return cfg_id, _publish_cfg(cfg_id)


def _tp_section_def(fixture: str = FIXTURE_FULL) -> dict:
	subs = lean_technical_proposal_subsections(fixture)
	return {"section_key": SECTION_KEY, "subsections": subs}


def _tp_sub(key: str, fixture: str = FIXTURE_FULL) -> dict:
	return next(s for s in lean_technical_proposal_subsections(fixture) if s["subsection_key"] == key)


class TestSubsectionStatusConsistency(unittest.TestCase):
	"""Progress text, status chip, and action label must agree for every renderer."""

	def test_testing_progress_includes_required_stages(self):
		sub = _tp_sub(SUB_TESTING)
		qids = [q["question_id"] for q in sub["questions"]]
		payload = {
			"subsections": {
				SUB_TESTING: {
					"narratives": {qid: "a" for qid in qids},
					"test_stages": [],
				}
			}
		}
		st = derive_subsection_state(sub, payload, section_def=_tp_section_def())
		self.assertEqual(st["status"], STATUS_IN_PROGRESS)
		self.assertEqual(st["action_label"], ACTION_CONTINUE)
		self.assertLess(st["completed_items"], st["required_items"])
		self.assertIn("complete", st["progress_text"])
		self.assertNotEqual(
			st["progress_text"],
			f"{len(qids)} of {len(qids)} complete",
			msg="Narratives-only progress must not claim complete while stages are required",
		)
		self.assertIn("testing stages", (st.get("issue") or "").lower())

		# With one complete stage, narratives + stage → Complete.
		payload["subsections"][SUB_TESTING]["test_stages"] = [
			{"stage_id": "s1", "test_stage": "UAT", "scope": "Full system"}
		]
		st2 = derive_subsection_state(sub, payload, section_def=_tp_section_def())
		self.assertEqual(st2["status"], STATUS_COMPLETE)
		self.assertEqual(st2["action_label"], ACTION_REVIEW)
		self.assertEqual(st2["completed_items"], st2["required_items"])

	def test_integration_not_started_action_is_start(self):
		sub = _tp_sub(SUB_INTEGRATION)
		st = derive_subsection_state(sub, {}, section_def=_tp_section_def())
		self.assertEqual(st["status"], STATUS_NOT_STARTED)
		self.assertEqual(st["action_label"], ACTION_START)

		st2 = derive_subsection_state(
			sub,
			{"integration_confirmation": {"confirmed": 1}},
			section_def=_tp_section_def(),
		)
		self.assertEqual(st2["status"], STATUS_COMPLETE)
		self.assertEqual(st2["action_label"], ACTION_REVIEW)

	def test_transition_progress_includes_handover(self):
		sub = _tp_sub(SUB_TRANSITION)
		qids = [q["question_id"] for q in sub["questions"]]
		payload = {
			"subsections": {
				SUB_TRANSITION: {
					"narratives": {qid: "done" for qid in qids},
					"handover_deliverables": [
						{"deliverable_id": "hd-ops-manual", "title": "Operations manual", "required": 1, "provided": 0},
						{"deliverable_id": "hd-admin-guide", "title": "Administrator guide", "required": 1, "provided": 0},
						{
							"deliverable_id": "hd-source-access",
							"title": "Source / configuration access credentials",
							"required": 1,
							"provided": 0,
						},
					],
				}
			}
		}
		st = derive_subsection_state(sub, payload, section_def=_tp_section_def())
		self.assertEqual(st["status"], STATUS_IN_PROGRESS)
		self.assertEqual(st["action_label"], ACTION_CONTINUE)
		self.assertLess(st["completed_items"], st["required_items"])

	def test_training_progress_denominator_covers_rows(self):
		sub = _tp_sub(SUB_TRAINING)
		payload = {
			"subsections": {
				SUB_TRAINING: {
					"training_activities": [
						{
							"audience": "End users",
							"topic": "Basics",
							"delivery_method": "Workshop",
						},
						# Partial second row must keep subsection In Progress (not Complete on min only).
						{"audience": "Administrators", "topic": "", "delivery_method": ""},
					]
				}
			}
		}
		st = derive_subsection_state(sub, payload, section_def=_tp_section_def())
		self.assertEqual(st["status"], STATUS_IN_PROGRESS)
		self.assertEqual(st["required_items"], 2)
		self.assertEqual(st["completed_items"], 1)
		self.assertEqual(st["action_label"], ACTION_CONTINUE)


class TestTechnicalProposalPortal(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_empty_published_subsections_healed_on_get(self):
		"""Regression: pre-materialize seals showed 0 of 0 with no Start actions."""
		_cfg_id, pub_ref = _prepare_tp_cfg(FIXTURE_FULL)
		pub_name = frappe.db.get_value(
			"IT Tender Publication Record", {"publication_ref": pub_ref}, "name"
		)
		raw = frappe.db.get_value(
			"IT Tender Publication Record", pub_name, "electronic_template_snapshot"
		)
		snap = json.loads(raw or "{}")
		for sec in snap.get("sections") or []:
			if cstr(sec.get("section_key")) == SECTION_KEY:
				sec["subsections"] = []
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_name,
			"electronic_template_snapshot",
			json.dumps(snap, ensure_ascii=False),
			update_modified=False,
		)
		frappe.db.commit()

		ov = get_technical_proposal(pub_ref)
		self.assertGreaterEqual(len(ov.get("subsections") or []), 2, ov.get("subsections"))
		self.assertGreater(int(ov.get("progress_total") or 0), 0)
		self.assertIn(SUB_ORG, {r["subsection_key"] for r in ov["subsections"]})

		# Persist heal so checklist / reloads see subsections without re-deriving.
		raw2 = frappe.db.get_value(
			"IT Tender Publication Record", pub_name, "electronic_template_snapshot"
		)
		snap2 = json.loads(raw2 or "{}")
		sec2 = next(
			s for s in (snap2.get("sections") or []) if cstr(s.get("section_key")) == SECTION_KEY
		)
		self.assertGreaterEqual(len(sec2.get("subsections") or []), 2)

	def test_core_overview_and_org_save_and_confirm(self):
		_cfg_id, pub_ref = _prepare_tp_cfg(FIXTURE_CORE)
		self.assertTrue(pub_ref)

		ov = get_technical_proposal(pub_ref)
		keys = {r["subsection_key"] for r in ov["subsections"]}
		self.assertIn(SUB_ORG, keys)
		self.assertIn(SUB_INTEGRATION, keys)
		self.assertNotIn(SUB_APPROACH, keys)
		self.assertEqual(ov["progress_total"], 2)
		self.assertIn("required subsections complete", ov["progress_label"])

		narratives = {
			"org-mgmt": "Agile programme management",
			"org-reporting": "Weekly steering reports",
			"org-comms": "Shared channel",
			"org-escalation": "Escalation ladder",
			"org-coord": "Joint PMO",
		}
		save_technical_proposal_subsection(
			pub_ref,
			SUB_ORG,
			{
				"bucket": {
					"narratives": narratives,
					"resource_roles": [
						{
							"project_role": "Project Manager",
							"person_id": "per-1",
							"person_name": "Ada Lovelace",
							"providing_member": "Lead",
							"responsibility": "Delivery",
							"decision_authority": "Yes",
						}
					],
					"coordination_matrix": [
						{
							"activity_or_deliverable": "Kick-off",
							"bidder_responsibility": "Facilitate",
							"pe_responsibility": "Provide venue",
							"third_party_responsibility": "—",
							"coordination_method": "Workshop",
						}
					],
				}
			},
		)
		ov2 = get_technical_proposal(pub_ref)
		org_row = next(r for r in ov2["subsections"] if r["subsection_key"] == SUB_ORG)
		self.assertEqual(org_row["status"], STATUS_COMPLETE)

		out = confirm_integration_responsibility(pub_ref)
		self.assertTrue(out["integration_confirmation"]["confirmed"])
		bid_name = ov2["bid_id"]
		status = frappe.db.get_value("Electronic Bid Submission", bid_name, "status")
		self.assertNotEqual(cstr(status), "Sealed")

		ov3 = get_technical_proposal(pub_ref)
		self.assertEqual(ov3["section_status"], STATUS_COMPLETE)
		self.assertEqual(ov3["progress_complete"], 2)

		checklist = get_submission_checklist(pub_ref)
		tp = next(s for s in checklist["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(tp["status"], STATUS_COMPLETE)

	def test_optional_does_not_block_and_alternatives_hidden(self):
		_cfg_id, pub_ref = _prepare_tp_cfg(
			FIXTURE_CONDITIONAL,
			flags={"technical_alternatives_permitted": 0, "warranty_support_required_by_tds": 0},
		)
		ov = get_technical_proposal(pub_ref)
		keys = {r["subsection_key"]: r for r in ov["subsections"]}
		self.assertNotIn(SUB_TRANSITION, keys)
		if SUB_ALTERNATIVES in keys:
			self.assertEqual(keys[SUB_ALTERNATIVES]["status"], STATUS_NOT_APPLICABLE)
		if SUB_TRAINING in keys:
			self.assertEqual(keys[SUB_TRAINING]["optional"], 1)
		self.assertGreaterEqual(ov["progress_total"], 2)
		for r in ov["subsections"]:
			if r.get("optional"):
				self.assertNotEqual(r["subsection_key"], SUB_ORG)

	def test_checklist_continue_opens_section_overview_not_subsection(self):
		"""Start/Continue must open TP overview — not deep-link into Training (or any subsection)."""
		_cfg_id, pub_ref = _prepare_tp_cfg(FIXTURE_FULL)
		# Seed partial progress so the section is In Progress and first incomplete ≠ overview.
		save_technical_proposal_subsection(
			pub_ref,
			SUB_ORG,
			{
				"bucket": {
					"narratives": {
						"org-mgmt": "Management approach",
						"org-reporting": "Reporting",
						"org-comms": "Comms",
						"org-escalation": "Escalation",
						"org-coord": "Coordination",
					},
					"resource_roles": [
						{
							"project_role": "PM",
							"person_id": "per-1",
							"person_name": "Ada",
							"providing_org": "Lead",
							"delivery_responsibility": "Delivery",
							"decision_authority": "Yes",
						}
					],
					"coordination_matrix": [
						{
							"activity_or_deliverable": "Kick-off",
							"bidder_responsibility": "Facilitate",
							"pe_responsibility": "Venue",
						}
					],
				}
			},
		)
		checklist = get_submission_checklist(pub_ref)
		tp = next(s for s in checklist["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(tp["status"], STATUS_IN_PROGRESS)
		self.assertEqual(tp["action_label"], "Continue")
		overview = portal_technical_proposal_url(pub_ref)
		self.assertEqual(tp["action_url"], overview)
		self.assertNotIn("/training_and_knowledge_transfer", tp["action_url"])
		# Resolve path still deep-links when Needs Attention.
		save_technical_proposal_subsection(
			pub_ref,
			SUB_WORK_PLAN,
			{
				"bucket": {
					"activities": [
						{
							"activity_id": "a1",
							"activity": "Design",
							"start_week": 1,
							"duration_weeks": 2,
							"dependency_id": "missing-dep",
							"project_role": "PM",
						}
					]
				}
			},
		)
		checklist2 = get_submission_checklist(pub_ref)
		tp2 = next(s for s in checklist2["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(tp2["status"], STATUS_NEEDS_ATTENTION)
		self.assertEqual(tp2["action_label"], "Resolve")
		# Resolve deep-links to first incomplete subsection (catalog order), not overview.
		self.assertNotEqual(tp2["action_url"].rstrip("/"), overview.rstrip("/"))
		self.assertIn("/sections/technical_proposal_and_implementation_plan/", tp2["action_url"])
		self.assertTrue(
			any(
				seg in tp2["action_url"]
				for seg in (
					"/technical_approach",
					"/implementation_work_plan",
					"/proposed_organisation",
				)
			),
			msg=tp2["action_url"],
		)

	def test_work_plan_needs_attention_on_bad_deps(self):
		_cfg_id, pub_ref = _prepare_tp_cfg(FIXTURE_FULL)
		out = save_technical_proposal_subsection(
			pub_ref,
			SUB_WORK_PLAN,
			{
				"bucket": {
					"activities": [
						{
							"activity_id": "a1",
							"phase": "1",
							"activity": "Design",
							"start_week": 1,
							"duration_weeks": 2,
							"dependency_id": "nope",
							"project_role": "PM",
						}
					]
				}
			},
		)
		self.assertEqual(out["status"], STATUS_NEEDS_ATTENTION)
		self.assertTrue(out.get("issue"))
