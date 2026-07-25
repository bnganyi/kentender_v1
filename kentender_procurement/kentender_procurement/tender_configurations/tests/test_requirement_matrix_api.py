# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A4 Requirement Matrix — domain API contract tests."""

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
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	get_published_tender_overview,
)
from kentender_procurement.tender_configurations.services.requirement_matrix import (
	_normalize_file_list,
	build_groups,
	collect_in_progress_field_errors,
	get_requirement_drawer,
	get_requirement_matrix,
	is_requirement_matrix_section,
	matrix_section_roll_up,
	portal_section_url,
	requirement_display,
	resolve_group_status,
	resolve_requirement_status,
	save_requirement_response,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	get_submission_checklist,
)

MATRIX_FIELDS = [
	{"field_key": "compliant_yes_no", "label": "Compliant (Yes/No)", "type": "text", "required": True},
	{
		"field_key": "compliance_statement",
		"label": "Compliance statement",
		"type": "narrative",
		"required": True,
	},
	{"field_key": "reference_pages", "label": "Reference pages", "type": "text", "required": False},
	{"field_key": "evidence_uploads", "label": "Evidence uploads", "type": "file", "required": False},
]

MATRIX_SCHEMA = {
	"version": 1,
	"sections": [
		{
			"key": "tender_document_acknowledgement",
			"section_type": "document_acknowledgement",
			"title": "Tender Documents & Addenda",
			"required": True,
		},
		{
			"key": "alpha_compliance_matrix",
			"label": "Technical Compliance Matrix",
			"required": True,
			"response_fields_per_requirement": MATRIX_FIELDS,
			"requirements": [
				{
					"requirement_id": "REQ-A1",
					"requirement_title": "Concurrent users",
					"requirement_statement": "Support 50 concurrent users.",
					"category_label": "System Capacity",
					"mandatory": True,
				},
				{
					"requirement_id": "REQ-A2",
					"requirement_title": "Storage capacity",
					"requirement_statement": "Provide 500 GB storage.",
					"category_label": "System Capacity",
					"mandatory": True,
					"bidder_response_type": "compliance_statement_plus_evidence_upload",
				},
				{
					"requirement_id": "REQ-B1",
					"requirement_title": "Role-based access",
					"requirement_statement": "Provide RBAC.",
					"category_label": "Security Controls",
					"mandatory": True,
				},
			],
		},
		{"key": "form_of_tender", "title": "Form of Tender", "required": True},
	],
}


class TestRequirementMatrixHelpers(unittest.TestCase):
	def test_portal_section_url(self):
		self.assertEqual(
			portal_section_url("PUB-TEST-1", "alpha_compliance_matrix"),
			"/tenders/PUB-TEST-1/sections/alpha_compliance_matrix",
		)

	def test_structural_matrix_detection(self):
		self.assertTrue(is_requirement_matrix_section(MATRIX_SCHEMA["sections"][1]))
		self.assertFalse(
			is_requirement_matrix_section({"key": "form_of_tender", "title": "Form of Tender"})
		)
		self.assertTrue(
			is_requirement_matrix_section(
				{
					"key": "x",
					"section_type": "requirement_matrix",
					"requirements": [{"requirement_id": "1"}],
					"response_fields_per_requirement": [{"field_key": "a", "type": "text"}],
				}
			)
		)
		# Do not treat hard-coded key alone as matrix without structure
		self.assertFalse(
			is_requirement_matrix_section({"key": "technical_compliance_matrix", "label": "TCM"})
		)

	def test_groups_from_category_label_order(self):
		sec = MATRIX_SCHEMA["sections"][1]
		groups = build_groups(sec["requirements"], {}, MATRIX_FIELDS)
		self.assertEqual([g["group_key"] for g in groups], ["System Capacity", "Security Controls"])
		# No NSSF mock group names
		blob = json.dumps(groups)
		self.assertNotIn("General Requirements", blob)
		self.assertNotIn("NSSF", blob)

	def test_requirement_status_matrix(self):
		req = MATRIX_SCHEMA["sections"][1]["requirements"][0]
		self.assertEqual(resolve_requirement_status(req, {}, MATRIX_FIELDS), STATUS_NOT_STARTED)
		self.assertEqual(
			resolve_requirement_status(req, {"compliant_yes_no": "Yes"}, MATRIX_FIELDS),
			STATUS_IN_PROGRESS,
		)
		self.assertEqual(
			resolve_requirement_status(
				req,
				{"compliant_yes_no": "Yes", "compliance_statement": "Meets capacity"},
				MATRIX_FIELDS,
			),
			STATUS_COMPLETE,
		)
		evidence_req = MATRIX_SCHEMA["sections"][1]["requirements"][1]
		self.assertEqual(
			resolve_requirement_status(
				evidence_req,
				{"compliant_yes_no": "Yes", "compliance_statement": "OK"},
				MATRIX_FIELDS,
			),
			STATUS_NEEDS_ATTENTION,
		)

	def test_normalize_file_list_accepts_single_and_multi(self):
		self.assertEqual(_normalize_file_list(None), [])
		self.assertEqual(
			_normalize_file_list({"file_name": "a.pdf", "mock": 1}),
			[{"file_name": "a.pdf", "mock": 1}],
		)
		multi = _normalize_file_list(
			[{"file_name": "a.pdf", "mock": 1}, {"file_name": "b.docx", "mock": 1}]
		)
		self.assertEqual(len(multi), 2)

	def test_requirement_display_dedupes_identical_title_statement(self):
		text = (
			"The proposed solution must be accessible to users remotely "
			"and securely through the internet (web-based)"
		)
		disp = requirement_display(
			{
				"requirement_id": "A04",
				"requirement_title": text,
				"requirement_statement": text,
			}
		)
		self.assertEqual(disp["list_title"], text)
		self.assertEqual(disp["list_subtitle"], "")
		self.assertEqual(disp["statement"], "")
		self.assertEqual(disp["header_title"], "A04")
		self.assertEqual(disp["description"], text)

	def test_requirement_display_short_title_stripped_from_description(self):
		# NSSF M1 pattern: short title + statement that starts with the title.
		disp = requirement_display(
			{
				"requirement_id": "M1",
				"requirement_title": "Implementation Methodology and Strategy",
				"requirement_statement": (
					"Implementation Methodology and Strategy. The bidder shall provide "
					"a detailed description of the proposed recognized methodology."
				),
			}
		)
		self.assertEqual(disp["list_title"], "Implementation Methodology and Strategy")
		self.assertEqual(disp["header_title"], "M1: Implementation Methodology and Strategy")
		self.assertTrue(disp["description"].startswith("The bidder shall provide"))
		self.assertNotIn("Implementation Methodology and Strategy", disp["description"])
		self.assertEqual(disp["list_subtitle"], disp["description"])

	def test_requirement_display_keeps_short_title_and_long_description(self):
		disp = requirement_display(
			{
				"requirement_id": "SR-02",
				"requirement_title": "Storage Capacity",
				"requirement_statement": "The proposed solution must provide 500 GB storage.",
			}
		)
		self.assertEqual(disp["list_title"], "Storage Capacity")
		self.assertEqual(disp["header_title"], "SR-02: Storage Capacity")
		self.assertEqual(disp["description"], "The proposed solution must provide 500 GB storage.")
		self.assertEqual(disp["statement"], "The proposed solution must provide 500 GB storage.")

	def test_in_progress_field_errors_only_when_started(self):
		req = {"requirement_id": "X1", "mandatory": True}
		fields = MATRIX_FIELDS
		# Not Started → no field errors
		self.assertEqual(
			collect_in_progress_field_errors(req, {}, fields, status=STATUS_NOT_STARTED),
			{},
		)
		# In Progress with Yes only → compliance statement required
		errs = collect_in_progress_field_errors(
			req,
			{"compliant_yes_no": "Yes"},
			fields,
			status=STATUS_IN_PROGRESS,
		)
		self.assertIn("compliance_statement", errs)
		self.assertNotIn("compliant_yes_no", errs)

	def test_group_status_partial_is_in_progress(self):
		# 9/10 complete → In Progress (Stitch fix)
		self.assertEqual(
			resolve_group_status(complete=9, total=10, needs_attention=0, started=9),
			STATUS_IN_PROGRESS,
		)

	def test_matrix_roll_up(self):
		sec = MATRIX_SCHEMA["sections"][1]
		st, blockers = matrix_section_roll_up(sec, {})
		self.assertEqual(st, STATUS_NOT_STARTED)
		self.assertEqual(blockers, 0)
		st2, _ = matrix_section_roll_up(
			sec,
			{"REQ-A1": {"compliant_yes_no": "Yes", "compliance_statement": "ok"}},
		)
		self.assertEqual(st2, STATUS_IN_PROGRESS)


class TestRequirementMatrixApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"std_version": CANONICAL_PACKAGE_ID,
				"bidder_submission_schema": json.dumps(MATRIX_SCHEMA),
				"short_scope_summary": "A4 matrix scope.",
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
				"tender_notice": "A4 matrix notice.",
				"clarification_deadline": str(add_to_date(now, days=2)),
				"submission_deadline": str(add_to_date(now, days=14)),
				"opening_datetime": str(add_to_date(now, days=15, hours=1)),
				"bidder_visibility": "All Registered Bidders",
				"activate_bidder_workspace": 1,
				"acknowledgement_confirmed": 1,
			},
		)
		published = publish_tender(pub_id)
		ref = cstr(published.get("publication_ref") or "") or cstr(
			frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
		)
		self.assertTrue(ref.startswith("PUB-"), ref)
		return ref

	def _ensure_matrix_schema(self, ref: str) -> None:
		"""Bid schema_snapshot wins over config — pin lightweight matrix fixture for tests."""
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)

		backend = resolve_published_tender_backend(ref)
		draft = create_or_get_draft(cstr(backend.get("configuration_id") or self.cfg_id))
		bid = frappe.get_doc("Electronic Bid Submission", draft["bid_id"])
		bid.db_set("schema_snapshot", json.dumps(MATRIX_SCHEMA), update_modified=False)
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"bidder_submission_schema",
			json.dumps(MATRIX_SCHEMA),
		)
		frappe.db.commit()

	def test_guest_denied(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_requirement_matrix(ref, "alpha_compliance_matrix")

	def test_matrix_dto_schema_driven(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		out = get_requirement_matrix(ref, "alpha_compliance_matrix")
		self.assertEqual(out["section_key"], "alpha_compliance_matrix")
		self.assertEqual(out["section_title"], "Technical Compliance Matrix")
		self.assertIn("requirements complete", out["progress_label"])
		self.assertEqual(len(out["groups"]), 2)
		self.assertEqual(out["groups"][0]["group_key"], "System Capacity")
		self.assertTrue(out["workspace_url"].endswith("/workspace"))
		self.assertEqual(
			portal_section_url(ref, "alpha_compliance_matrix"),
			f"/tenders/{ref}/sections/alpha_compliance_matrix",
		)
		# No ordinal "6" / NSSF hardcodes in DTO labels
		self.assertNotIn("6.", out["section_title"])
		joined = json.dumps(out)
		self.assertNotIn("NSSF", joined)
		self.assertNotIn("General Requirements", joined)

	def test_save_merges_one_requirement(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		# Seed another requirement first so merge doesn't wipe siblings
		save_requirement_response(
			ref,
			"alpha_compliance_matrix",
			"REQ-B1",
			{"compliant_yes_no": "Yes", "compliance_statement": "RBAC provided"},
		)
		out = save_requirement_response(
			ref,
			"alpha_compliance_matrix",
			"REQ-A1",
			{
				"compliant_yes_no": "Yes",
				"compliance_statement": "50 users supported",
				"evidence_uploads": [
					{"file_name": "capacity.pdf", "mock": 1, "byte_size": 1200},
					{"file_name": "diagram.png", "mock": 1, "byte_size": 800},
				],
			},
		)
		self.assertEqual(out["drawer"]["status"], STATUS_COMPLETE)
		row = next(r for r in out["matrix"]["rows"] if r["requirement_id"] == "REQ-A1")
		self.assertEqual(row["status"], STATUS_COMPLETE)
		files = out["drawer"]["response"].get("evidence_uploads") or []
		self.assertEqual(len(files), 2)
		self.assertEqual(files[0]["file_name"], "capacity.pdf")
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)

		self.assertNotIn("bid_id", out["matrix"])
		bid = frappe.get_doc(
			"Electronic Bid Submission", resolve_published_tender_backend(ref)["bid_id"]
		)
		responses = json.loads(bid.responses or "{}")
		section = responses["alpha_compliance_matrix"]
		self.assertIn("REQ-A1", section)
		self.assertIn("REQ-B1", section)
		self.assertNotIn("reference_pages", section["REQ-A1"])
		self.assertEqual(len(section["REQ-A1"]["evidence_uploads"]), 2)

	def test_drawer_suppresses_reference_pages(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		drawer = get_requirement_drawer(ref, "alpha_compliance_matrix", "REQ-A1")
		keys = [f.get("field_key") for f in drawer["fields"]]
		self.assertNotIn("reference_pages", keys)
		self.assertIn("compliant_yes_no", keys)

	def test_matrix_short_title_and_in_progress_attention(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		matrix = get_requirement_matrix(ref, "alpha_compliance_matrix")
		row = next(r for r in matrix["rows"] if r["requirement_id"] == "REQ-A1")
		self.assertEqual(row["title"], "Concurrent users")
		self.assertEqual(row["subtitle"], "Support 50 concurrent users.")
		self.assertEqual(row["has_short_title"], 1)

		fresh = get_requirement_drawer(ref, "alpha_compliance_matrix", "REQ-A1")
		self.assertEqual(fresh["header_title"], "REQ-A1: Concurrent users")
		self.assertEqual(fresh["description"], "Support 50 concurrent users.")
		self.assertEqual(fresh["status"], STATUS_NOT_STARTED)
		self.assertEqual(fresh["show_attention"], 0)
		self.assertEqual(fresh["field_errors"], {})

		out = save_requirement_response(
			ref,
			"alpha_compliance_matrix",
			"REQ-A1",
			{"compliant_yes_no": "Yes"},
		)
		drawer = out["drawer"]
		self.assertEqual(drawer["status"], STATUS_IN_PROGRESS)
		self.assertEqual(drawer["show_attention"], 1)
		self.assertEqual(drawer["header_status"], STATUS_NEEDS_ATTENTION)
		self.assertIn("compliance_statement", drawer["field_errors"])
		stmt_field = next(f for f in drawer["fields"] if f["field_key"] == "compliance_statement")
		self.assertIn("required", (stmt_field.get("error") or "").lower())

		# Evidence-typed requirement: missing file elevates status; still show under-field error.
		out2 = save_requirement_response(
			ref,
			"alpha_compliance_matrix",
			"REQ-A2",
			{"compliant_yes_no": "Yes", "compliance_statement": "500 GB provided"},
		)
		d2 = out2["drawer"]
		self.assertEqual(d2["status"], STATUS_NEEDS_ATTENTION)
		self.assertEqual(d2["show_attention"], 0)  # status already carries the label
		self.assertIn("evidence_uploads", d2["field_errors"])
		self.assertIn("technical evidence", d2["field_errors"]["evidence_uploads"].lower())

	def test_checklist_matrix_action_url_portal(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		checklist = get_submission_checklist(ref)
		matrix_row = next(s for s in checklist["sections"] if s["section_key"] == "alpha_compliance_matrix")
		self.assertEqual(matrix_row["status"], STATUS_NOT_STARTED)
		self.assertEqual(matrix_row["action_label"], "Start")
		self.assertEqual(
			matrix_row["action_url"],
			f"/tenders/{ref}/sections/alpha_compliance_matrix",
		)
		save_requirement_response(
			ref,
			"alpha_compliance_matrix",
			"REQ-A1",
			{"compliant_yes_no": "Yes", "compliance_statement": "ok"},
		)
		checklist2 = get_submission_checklist(ref)
		matrix_row2 = next(s for s in checklist2["sections"] if s["section_key"] == "alpha_compliance_matrix")
		self.assertEqual(matrix_row2["status"], STATUS_IN_PROGRESS)
		self.assertEqual(matrix_row2["action_label"], "Continue")


if __name__ == "__main__":
	unittest.main()
