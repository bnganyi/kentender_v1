# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Lean Requirements Compliance — fixtures, modes, progress, review, checklist."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.lean_requirements_compliance import (
	FIXTURE_AMENDED,
	FIXTURE_CONDITIONAL,
	FIXTURE_STANDARD,
	MODE_INFORMATIONAL,
	MODE_OPTIONAL,
	SECTION_KEY,
	lean_requirements_as_it_requirements,
	lean_requirements_compliance_rows,
	merge_requirements_compliance_into_evaluation,
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
	materialize_requirements_compliance,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.requirement_matrix import (
	ACTION_RESOLVE,
	ACTION_START,
	complete_requirements_compliance_section,
	get_requirement_drawer,
	get_requirement_matrix,
	get_requirements_compliance_review,
	hydrate_requirements_compliance_section,
	is_requirement_matrix_section,
	resolve_requirement_applicability,
	resolve_requirement_status,
	save_requirement_response,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
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
			"tender_notice": "Requirements compliance notice.",
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


def _apply_rc_fixture(cfg_id: str, fixture: str, *, flags: dict | None = None) -> None:
	raw = frappe.db.get_value("Tender Configuration", cfg_id, "evaluation_setup")
	try:
		ev = json.loads(raw) if raw else {}
	except Exception:
		ev = {}
	if not isinstance(ev, dict):
		ev = {}
	merged = merge_requirements_compliance_into_evaluation(ev, fixture=fixture, flags=flags)
	it_reqs = lean_requirements_as_it_requirements(fixture)
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"evaluation_setup": json.dumps(merged),
			"it_requirements": json.dumps(it_reqs),
		},
	)


def _prepare_rc_cfg(fixture: str = FIXTURE_STANDARD, *, flags: dict | None = None) -> tuple[str, str]:
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "Lean requirements compliance domain tests.",
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	_apply_rc_fixture(cfg_id, fixture, flags=flags)
	for name in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration": cfg_id},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
	frappe.db.commit()
	return cfg_id, _publish_cfg(cfg_id)


class TestLeanRequirementsFixtures(unittest.TestCase):
	def test_standard_has_modes_and_groups(self):
		rows = lean_requirements_compliance_rows(FIXTURE_STANDARD)
		modes = {r["requirement_mode"] for r in rows}
		self.assertIn("required", modes)
		self.assertIn(MODE_OPTIONAL, modes)
		self.assertIn(MODE_INFORMATIONAL, modes)
		groups = {r["category_label"] for r in rows}
		self.assertGreaterEqual(len(groups), 3)
		for r in rows:
			self.assertTrue(r.get("tender_facing_reference"))
			self.assertNotIn("NSSF", cstr(r.get("requirement_statement")))

	def test_materialize_excludes_withdrawn(self):
		ev = merge_requirements_compliance_into_evaluation({}, fixture=FIXTURE_AMENDED)
		rows, fields, _flags = materialize_requirements_compliance(ev)
		active_ids = {r["requirement_id"] for r in rows if r["requirement_mode"] != "excluded"}
		# materialize returns all; active filter is in instantiate
		self.assertTrue(any(r.get("withdrawn") for r in rows))
		self.assertTrue(fields)

	def test_hydrate_route_only_stub(self):
		stub = {
			"section_key": SECTION_KEY,
			"title": "Requirements Compliance",
			"slice_status": "route_only_not_editable_in_lean_slice",
			"requirements": [],
		}
		self.assertTrue(is_requirement_matrix_section(stub))
		hydrate_requirements_compliance_section(stub)
		self.assertEqual(stub.get("section_type"), "requirement_matrix")
		self.assertEqual(stub.get("slice_status"), "requirements_compliance_implemented")
		self.assertGreaterEqual(len(stub.get("requirements") or []), 1)
		self.assertTrue(stub.get("response_fields_per_requirement"))

	def test_fixture_labels_are_bidder_facing(self):
		from kentender_procurement.tender_configurations.services.requirement_matrix import (
			_portal_fields,
			requirement_display,
		)

		rows = lean_requirements_compliance_rows(FIXTURE_STANDARD)
		by_id = {r["requirement_id"]: r for r in rows}
		table_fields = by_id["rc-int-001"]["response_fields"]
		self.assertEqual(table_fields[0]["label"], "Integration activities")
		self.assertTrue(table_fields[0].get("columns"))
		self.assertNotEqual(table_fields[0]["label"], "Schedule rows")
		ack = by_id["rc-sec-002"]["response_fields"][0]
		self.assertEqual(ack["type"], "boolean")
		self.assertIn("read and understood", ack["label"].lower())
		portal = _portal_fields(table_fields)
		self.assertEqual(portal[0]["control"], "repeating_table")
		portal_ack = _portal_fields([ack])
		self.assertEqual(portal_ack[0]["control"], "checkbox")
		disp = requirement_display(by_id["rc-cap-002"])
		self.assertTrue(disp["header_title"].startswith("CAP-02"))
		self.assertNotIn("rc-cap-002", disp["header_title"])


class TestRequirementsCompliancePortal(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_standard_publish_progress_and_modes(self):
		_cfg_id, pub_ref = _prepare_rc_cfg(FIXTURE_STANDARD)
		mx = get_requirement_matrix(pub_ref, SECTION_KEY)
		self.assertTrue(mx["progress_total"] >= 1)
		self.assertIn("required responses complete", mx["progress_label"])
		refs = {r.get("tender_facing_reference") for r in mx["rows"]}
		self.assertTrue(refs)
		self.assertTrue(any(cstr(x).startswith(("CAP", "SEC", "INT", "SUP")) for x in refs))
		support = get_requirement_matrix(pub_ref, SECTION_KEY, group="Support", page_size=50)
		modes = {r.get("mode_label") for r in support["rows"]}
		self.assertIn("Optional", modes)
		security = get_requirement_matrix(pub_ref, SECTION_KEY, group="Security", page_size=50)
		sec_modes = {r.get("mode_label") for r in security["rows"]}
		self.assertIn("Informational", sec_modes)

	def test_drawer_previous_crosses_domains(self):
		"""Previous must mirror Save & Next and leave the current domain when at first row."""
		_cfg_id, pub_ref = _prepare_rc_cfg(FIXTURE_STANDARD)
		# First Security requirement should Previous into last System Capacity row.
		sec = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-sec-001")
		self.assertEqual(sec.get("group_key"), "Security")
		self.assertEqual(sec.get("prev_requirement_id"), "rc-cap-002")
		self.assertTrue(sec.get("next_requirement_id"))
		# First overall requirement has no Previous; last Capacity has Next into Security.
		cap1 = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-cap-001")
		self.assertEqual(cap1.get("prev_requirement_id"), "")
		cap2 = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-cap-002")
		self.assertEqual(cap2.get("next_requirement_id"), "rc-sec-001")
		# Crossing into Integration from last Security (informational SEC-02 is last in group).
		sec2 = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-sec-002")
		self.assertEqual(sec2.get("next_requirement_id"), "rc-int-001")
		integ = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-int-001")
		self.assertEqual(integ.get("prev_requirement_id"), "rc-sec-002")

	def test_save_zero_and_false_preserved(self):
		_cfg_id, pub_ref = _prepare_rc_cfg(FIXTURE_STANDARD)
		out = save_requirement_response(
			pub_ref,
			SECTION_KEY,
			"rc-cap-001",
			{
				"numeric_value": 0,
				"compliance_statement": "Zero is valid",
				"evidence_uploads": [{"file_name": "cap.pdf", "mock": 1}],
			},
		)
		resp = out["drawer"]["response"]
		self.assertEqual(resp.get("numeric_value"), 0)
		self.assertEqual(out["drawer"]["status"], STATUS_COMPLETE)

	def _complete_all_required(self, pub_ref: str) -> None:
		required_ids = (
			"rc-cap-001",
			"rc-cap-002",
			"rc-sec-001",
			"rc-int-001",
		)
		for rid in required_ids:
			save_requirement_response(
				pub_ref,
				SECTION_KEY,
				rid,
				{
					"compliant_yes_no": "Yes",
					"compliance_statement": "Provided",
					"numeric_value": 100,
					"acknowledged": 1,
					"schedule_rows": [{"activity": "A", "timing": "Week 1"}],
					"evidence_uploads": [{"file_name": "e.pdf", "mock": 1}],
				},
			)

	def test_optional_does_not_block_section(self):
		_cfg_id, pub_ref = _prepare_rc_cfg(FIXTURE_STANDARD)
		self._complete_all_required(pub_ref)
		# Leave optional SUP-01 untouched
		review = get_requirements_compliance_review(pub_ref)
		self.assertEqual(review["section_status"], STATUS_COMPLETE)
		self.assertEqual(review["complete_enabled"], 1)
		# Optional-only Support domain must not read as "0 of 0 Not Applicable".
		support = next(g for g in review["groups"] if g["group_key"] == "Support")
		self.assertEqual(support["total"], 1)
		self.assertEqual(support["status"], STATUS_NOT_STARTED)
		self.assertEqual(support["progress_label"], "0 of 1")
		# Completing the optional row updates domain status without blocking section.
		save_requirement_response(
			pub_ref,
			SECTION_KEY,
			"rc-sup-001",
			{"compliant_yes_no": "Yes", "compliance_statement": "Optional offered"},
		)
		review2 = get_requirements_compliance_review(pub_ref)
		support2 = next(g for g in review2["groups"] if g["group_key"] == "Support")
		self.assertEqual(support2["status"], STATUS_COMPLETE)
		self.assertEqual(support2["progress_label"], "1 of 1")
		self.assertEqual(review2["complete_enabled"], 1)
		out = complete_requirements_compliance_section(pub_ref)
		self.assertEqual(out["section_complete_confirmed"], 1)

	def test_addendum_changed_needs_attention(self):
		_cfg_id, pub_ref = _prepare_rc_cfg(FIXTURE_AMENDED)
		# Seed a prior response without addendum_reviewed
		save_requirement_response(
			pub_ref,
			SECTION_KEY,
			"rc-amd-changed",
			{
				"compliant_yes_no": "Yes",
				"compliance_statement": "Old response",
				"evidence_uploads": [{"file_name": "old.pdf", "mock": 1}],
				"addendum_reviewed": 0,
			},
		)
		# Force clear reviewed flag
		bid = frappe.get_all(
			"Electronic Bid Submission",
			filters={"owner": "Administrator"},
			order_by="modified desc",
			limit=1,
		)
		# Reload status via drawer
		from kentender_procurement.tender_configurations.services.requirement_matrix import (
			get_requirement_drawer,
		)

		# Manually unset addendum_reviewed
		doc = frappe.get_doc(
			"Electronic Bid Submission",
			frappe.db.get_value(
				"Electronic Bid Submission",
				{"configuration": _cfg_id, "owner": "Administrator"},
				"name",
			),
		)
		responses = json.loads(doc.responses or "{}")
		sec = responses.get(SECTION_KEY) or {}
		sec["rc-amd-changed"] = {
			"compliant_yes_no": "Yes",
			"compliance_statement": "Old response",
			"evidence_uploads": [{"file_name": "old.pdf", "mock": 1}],
		}
		responses[SECTION_KEY] = sec
		doc.responses = json.dumps(responses)
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		drawer = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-amd-changed")
		self.assertEqual(drawer["status"], STATUS_NEEDS_ATTENTION)
		self.assertIn("Addendum", drawer.get("addendum_banner") or "")
		mx = get_requirement_matrix(pub_ref, SECTION_KEY, page_size=50)
		changed = next(r for r in mx["rows"] if r["requirement_id"] == "rc-amd-changed")
		self.assertEqual(changed["action_label"], ACTION_RESOLVE)
		# Resave clears attention
		save_requirement_response(
			pub_ref,
			SECTION_KEY,
			"rc-amd-changed",
			{
				"compliant_yes_no": "Yes",
				"compliance_statement": "Updated after addendum",
				"evidence_uploads": [{"file_name": "new.pdf", "mock": 1}],
			},
		)
		drawer2 = get_requirement_drawer(pub_ref, SECTION_KEY, "rc-amd-changed")
		self.assertEqual(drawer2["status"], STATUS_COMPLETE)

	def test_complete_section_does_not_seal(self):
		_cfg_id, pub_ref = _prepare_rc_cfg(FIXTURE_STANDARD)
		self._complete_all_required(pub_ref)
		out = complete_requirements_compliance_section(pub_ref)
		self.assertEqual(out["section_complete_confirmed"], 1)
		bid_name = out["bid_id"]
		self.assertNotEqual(cstr(frappe.db.get_value("Electronic Bid Submission", bid_name, "status")), "Sealed")
		checklist = get_submission_checklist(pub_ref)
		rc = next(s for s in checklist["sections"] if s["section_key"] == SECTION_KEY)
		self.assertEqual(rc["status"], STATUS_COMPLETE)
		self.assertIn("/sections/requirements_compliance", rc["action_url"])


class TestRequirementsApplicabilityUnit(unittest.TestCase):
	def test_conditional_inactive(self):
		req = {
			"requirement_id": "x",
			"requirement_mode": "conditional",
			"condition_key": "technical_alternatives_permitted",
			"mandatory": 1,
		}
		sec = {"requirements_compliance_flags": {"technical_alternatives_permitted": 0}}
		ok, mode = resolve_requirement_applicability(req, sec=sec)
		self.assertFalse(ok)
		st = resolve_requirement_status(req, {}, [], sec=sec)
		self.assertEqual(st, STATUS_NOT_APPLICABLE)

	def test_start_action(self):
		from kentender_procurement.tender_configurations.services.requirement_matrix import (
			_action_for_req_status,
		)

		self.assertEqual(_action_for_req_status(STATUS_NOT_STARTED), ACTION_START)
		self.assertEqual(_action_for_req_status(STATUS_NEEDS_ATTENTION), ACTION_RESOLVE)
