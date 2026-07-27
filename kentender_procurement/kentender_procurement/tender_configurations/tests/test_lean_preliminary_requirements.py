# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Preliminary Requirements and Evidence — dynamic criteria, validity, linked status."""

from __future__ import annotations

import base64
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
	build_electronic_submission_template,
	materialize_preliminary_criteria,
)
from kentender_procurement.tender_configurations.services.preliminary_requirements import (
	SECTION_KEY,
	bidder_is_jv,
	derive_criterion_status,
	evaluate_validity,
	get_preliminary_requirements,
	save_preliminary_response,
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
			"tender_notice": "Preliminary requirements notice.",
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


def _pdf_b64(size: int = 64) -> str:
	"""Valid minimal PDF — Frappe File.before_insert runs pypdf on application/pdf."""
	from io import BytesIO

	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=72 + (size % 20), height=72)
	writer.add_metadata({"/Title": f"prelim-evidence-{size}"})
	buf = BytesIO()
	writer.write(buf)
	return base64.b64encode(buf.getvalue()).decode("ascii")


def _seed_cbq(cfg_id: str, *, entity_type: str = "company", jv_mode: str = "") -> None:
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
	if jv_mode:
		answers["jv_mode"] = jv_mode
	responses["confidential_business_questionnaire"] = {
		"entities": [
			{
				"entity_id": "ent-bidder-1",
				"role": "bidder",
				"legal_name": "Lean Demo Bidder Ltd",
				"entity_type": entity_type,
				"answers": answers,
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


class TestPreliminaryCriteriaMaterialization(unittest.TestCase):
	def test_materialize_from_cfg_not_nssf_hardcode(self):
		rows = materialize_preliminary_criteria(
			[
				{
					"criterion_name": "Custom PE certificate",
					"stage": "Preliminary",
					"evidence_instruction": "Upload the PE-configured certificate.",
					"response_method": "upload",
					"bidder_evidence": "Required",
				},
				{
					"criterion_name": "Technical scored",
					"stage": "Technical",
					"evaluation_basis": "Scored",
				},
			]
		)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["title"], "Custom PE certificate")
		self.assertEqual(rows[0]["response_method"], "upload")
		blob = json.dumps(rows)
		self.assertNotIn("NSSF", blob.upper())
		self.assertNotIn("NSSFSPS", blob)

	def test_template_slice_status_and_renderer(self):
		path = (
			Path(__file__).resolve().parents[1]
			/ "electronic_std_templates"
			/ "ppra_it_std_v1.json"
		)
		template = json.loads(path.read_text(encoding="utf-8"))
		sec = next(
			s
			for s in template["sections"]
			if s.get("section_key") == "preliminary_requirements_and_evidence"
		)
		self.assertEqual(sec.get("slice_status"), "preliminary_implemented")
		self.assertEqual(sec.get("renderer"), "eligibility_checklist")


class TestPreliminaryRequirementsDomain(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_active_canonical_ppra_it_std(force_reimport=False)
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"std_version": CANONICAL_PACKAGE_ID,
				"short_scope_summary": "Lean preliminary requirements domain tests.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		frappe.db.commit()
		self.ref = _publish_cfg(self.cfg_id)
		_seed_cbq(self.cfg_id)

	def test_get_dynamic_two_groups_and_progress(self):
		out = get_preliminary_requirements(self.ref)
		self.assertEqual(out["section_key"], SECTION_KEY)
		self.assertGreaterEqual(len(out["evidence_group"]), 3)
		self.assertGreaterEqual(len(out["linked_group"]), 2)
		titles = [r["title"] for r in out["evidence_group"] + out["linked_group"]]
		self.assertIn("Tax compliance certificate", titles)
		self.assertIn("Form of Tender", titles)
		# JV-only excluded for single bidder
		self.assertNotIn("Joint Venture agreement", titles)
		self.assertEqual(out["progress_complete"], 0)
		self.assertGreater(out["progress_total"], 0)
		self.assertEqual(out["show_completion_banner"], 0)
		blob = json.dumps(out)
		self.assertNotIn("Passed", blob)
		self.assertNotIn("Failed", blob)
		self.assertNotIn("NSSFSPS", blob)

	def test_jv_applicability(self):
		_seed_cbq(self.cfg_id, entity_type="jv", jv_mode="constituted")
		out = get_preliminary_requirements(self.ref)
		titles = [r["title"] for r in out["evidence_group"]]
		self.assertIn("Joint Venture agreement", titles)

	def test_upload_response_and_checklist_url(self):
		out = get_preliminary_requirements(self.ref)
		crit = next(r for r in out["evidence_group"] if r["response_method"] == "upload")
		saved = save_preliminary_response(
			self.ref,
			crit["criterion_id"],
			{
				"action": "upload",
				"filename": "business-reg.pdf",
				"content_b64": _pdf_b64(70),
				"content_type": "application/pdf",
			},
		)
		row = next(
			r for r in saved["evidence_group"] if r["criterion_id"] == crit["criterion_id"]
		)
		self.assertEqual(row["status"], STATUS_COMPLETE)
		self.assertTrue(cstr(row["response"].get("file_name") or "").startswith("business-reg"))

		checklist = get_submission_checklist(self.ref)
		prelim = next(
			s for s in checklist["sections"] if s["section_key"] == SECTION_KEY
		)
		self.assertIn("/sections/preliminary_requirements_and_evidence", prelim["action_url"])
		self.assertIn(prelim["status"], (STATUS_IN_PROGRESS, STATUS_NEEDS_ATTENTION))
		self.assertEqual(prelim["action_label"], "Continue")

	def test_tax_compliance_expired_regression(self):
		"""Needs attention + Expired saved cert not preselected + banner hidden."""
		from kentender_procurement.tender_configurations.services.bid_evidence import (
			upload_evidence,
		)

		out = get_preliminary_requirements(self.ref)
		tax = next(r for r in out["evidence_group"] if "Tax compliance" in r["title"])
		past = str(add_to_date(now_datetime(), days=-30).date())
		uploaded = upload_evidence(
			self.ref,
			title="Expired tax certificate",
			evidence_type="tax_clearance",
			filename="tax-expired.pdf",
			content_b64=_pdf_b64(71),
			content_type="application/pdf",
			metadata={
				"issuer": "KRA",
				"reference_number": "TCC-EXPIRED-001",
				"issue_date": str(add_to_date(now_datetime(), days=-400).date()),
				"expiry_or_validity": past,
			},
		)
		eid = uploaded["item"]["evidence_id"]

		# Selecting expired must be rejected by save.
		with self.assertRaises(frappe.ValidationError):
			save_preliminary_response(
				self.ref,
				tax["criterion_id"],
				{"action": "select", "evidence_id": eid},
			)

		# Persist an expired response via register linkage bypass for status projection.
		draft = create_or_get_draft(self.cfg_id)
		doc = _get_bid(cstr(draft.get("bid_id") or ""))
		responses = _parse_json(doc.responses, {})
		sec = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
		cmap = sec.get("criterion_responses") if isinstance(sec.get("criterion_responses"), dict) else {}
		cmap[tax["criterion_id"]] = {
			"criterion_id": tax["criterion_id"],
			"response_method": "select_or_upload",
			"evidence_id": eid,
			"file_name": "tax-expired.pdf",
			"expiry_or_validity": past,
			"issuer": "KRA",
			"reference_number": "TCC-EXPIRED-001",
			"source": "selected",
		}
		sec["criterion_responses"] = cmap
		responses[SECTION_KEY] = sec
		doc.responses = json.dumps(responses, ensure_ascii=False)
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		again = get_preliminary_requirements(self.ref)
		tax_row = next(r for r in again["evidence_group"] if r["criterion_id"] == tax["criterion_id"])
		self.assertEqual(tax_row["status"], STATUS_NEEDS_ATTENTION)
		self.assertEqual(again["show_completion_banner"], 0)
		expired_opts = [
			i for i in again["saved_evidence"] if i.get("evidence_id") == eid
		]
		self.assertTrue(expired_opts)
		self.assertEqual(expired_opts[0].get("eligibility_label"), "Expired")
		# Must not be preselected in response sense for a fresh drawer — response exists but
		# saved_evidence list never marks a default selection flag.
		self.assertNotIn("preselected", json.dumps(again["saved_evidence"]).lower())
		self.assertNotIn("selected_by_default", json.dumps(again).lower())

	def test_seal_lock(self):
		out = get_preliminary_requirements(self.ref)
		crit = next(r for r in out["evidence_group"] if r["response_method"] == "upload")
		save_preliminary_response(
			self.ref,
			crit["criterion_id"],
			{
				"action": "upload",
				"filename": "seal.pdf",
				"content_b64": _pdf_b64(72),
				"content_type": "application/pdf",
			},
		)
		draft = create_or_get_draft(self.cfg_id)
		doc = _get_bid(cstr(draft.get("bid_id") or ""))
		doc.status = "Sealed"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		locked = get_preliminary_requirements(self.ref)
		self.assertEqual(locked["read_only"], 1)
		with self.assertRaises(frappe.ValidationError):
			save_preliminary_response(
				self.ref,
				crit["criterion_id"],
				{
					"action": "upload",
					"filename": "again.pdf",
					"content_b64": _pdf_b64(73),
					"content_type": "application/pdf",
				},
			)

	def test_instantiate_puts_criteria_on_section(self):
		built = build_electronic_submission_template(self.cfg_id)
		sec = next(
			s
			for s in built["snapshot"]["sections"]
			if s.get("section_key") == SECTION_KEY
		)
		self.assertGreaterEqual(len(sec.get("criteria") or []), 5)
		methods = {c.get("response_method") for c in sec["criteria"]}
		self.assertIn("upload", methods)
		self.assertIn("select_or_upload", methods)
		self.assertIn("linked_section", methods)


class TestPreliminaryHelpers(unittest.TestCase):
	def test_validity_and_jv_helpers(self):
		deadline = add_to_date(now_datetime(), days=10).date()
		ok, _ = evaluate_validity(
			validity_rule="valid_on_submission_deadline",
			evidence_item={"expiry_or_validity": str(add_to_date(now_datetime(), days=20).date())},
			submission_deadline=deadline,
			opening_date=None,
		)
		self.assertTrue(ok)
		bad, msg = evaluate_validity(
			validity_rule="valid_on_submission_deadline",
			evidence_item={"expiry_or_validity": str(add_to_date(now_datetime(), days=-1).date())},
			submission_deadline=deadline,
			opening_date=None,
		)
		self.assertFalse(bad)
		self.assertIn("expires", msg.lower())

		self.assertFalse(bidder_is_jv({}))
		self.assertTrue(
			bidder_is_jv(
				{
					"confidential_business_questionnaire": {
						"entities": [{"role": "bidder", "entity_type": "jv", "answers": {}}]
					}
				}
			)
		)

		na = derive_criterion_status(
			{
				"criterion_id": "x",
				"applicability": "jv_only",
				"response_method": "upload",
			},
			None,
			is_jv=False,
			register_items=[],
			submission_deadline=None,
			opening_date=None,
		)
		self.assertEqual(na["status"], STATUS_NOT_APPLICABLE)


if __name__ == "__main__":
	unittest.main()
