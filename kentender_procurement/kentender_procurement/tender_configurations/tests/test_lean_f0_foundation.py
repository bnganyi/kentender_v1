# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F0 — Lean Template and Workspace Foundation prove-list."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.electronic_std_templates import (
	ALLOWED_RENDERERS,
	CANONICAL_SECTION_KEYS,
	PPRA_IT_STD_V1_PATH,
)
from kentender_procurement.tender_configurations.electronic_std_templates.validator import (
	assert_valid_ppra_it_std_v1,
	validate_template,
)
from kentender_procurement.tender_configurations.seed.e1_nssf_seed import (
	publish_e1_nssf_with_electronic_template,
)
from kentender_procurement.tender_configurations.seed.lean_synthetic_it_seed import (
	seed_lean_synthetic_it_published,
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
	build_electronic_submission_template,
	require_approved_template,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender,
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.schema_compiler import SECTION_KEYS
from kentender_procurement.tender_configurations.services.section_response_envelope import (
	normalize_section_response_envelope,
	read_section_response,
	write_section_response,
)
from kentender_procurement.tender_configurations.services.section_status import (
	STATUS_COMPLETE,
	STATUS_NOT_STARTED,
	derive_generic_section_status,
	to_display_status,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)


def _prep_cfg() -> str:
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "F0 foundation tender scope for electronic template tests.",
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	frappe.db.commit()
	return cfg_id


def _confirm_and_setup(cfg_id: str) -> str:
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
			"tender_notice": "F0 foundation notice.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	return pub_id


class TestLeanF0TemplateValidity(unittest.TestCase):
	def test_template_validity_and_registry_order(self):
		bundle = assert_valid_ppra_it_std_v1(require_approved=False)
		self.assertEqual(bundle["approval"]["status"], "Draft")
		self.assertEqual(bundle["template"]["template_id"], "PPRA-IT-STD")
		keys = [s["section_key"] for s in bundle["template"]["sections"]]
		self.assertEqual(tuple(keys), CANONICAL_SECTION_KEYS)
		self.assertIn("lot_and_alternative_selection", keys)
		self.assertEqual(validate_template(bundle["template"]), [])

	def test_no_nssf_constants_in_canonical_template(self):
		raw = Path(PPRA_IT_STD_V1_PATH).read_text(encoding="utf-8")
		upper = raw.upper()
		for needle in ("NSSF", "NSSFSPS", "E1-NSSF", "TCFG-E1-NSSF"):
			self.assertNotIn(needle, upper)

	def test_unsupported_renderer_fails_closed(self):
		bundle = assert_valid_ppra_it_std_v1(require_approved=False)
		bad = copy.deepcopy(bundle["template"])
		bad["sections"][0]["renderer"] = "unknown_renderer_xyz"
		errors = validate_template(bad)
		self.assertTrue(any("unsupported renderer" in e for e in errors), errors)
		self.assertNotIn("unknown_renderer_xyz", ALLOWED_RENDERERS)


class TestLeanF0LifecycleAndPublishGates(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id = _prep_cfg()

	def test_maker_checker_approved_only_ordinary_publish(self):
		approval = {
			"status": "Draft",
			"prepared_by": "preparer@example.com",
			"approved_by": "approver@example.com",
			"template_file_hash": "abc",
		}
		with self.assertRaises(frappe.ValidationError) as ctx:
			require_approved_template(
				template={"template_id": "PPRA-IT-STD", "sections": []},
				approval=approval,
			)
		title = cstr(getattr(ctx.exception, "title", None) or "")
		msg = cstr(ctx.exception)
		self.assertTrue(
			"KT_ELECTRONIC_TEMPLATE_UNAPPROVED" in title or "Approved electronic STD" in msg,
			msg,
		)

		pub_id = _confirm_and_setup(self.cfg_id)
		with self.assertRaises(frappe.ValidationError) as ctx2:
			publish_tender(pub_id)
		title2 = cstr(getattr(ctx2.exception, "title", None) or "")
		msg2 = cstr(ctx2.exception)
		self.assertTrue(
			"KT_ELECTRONIC_TEMPLATE_UNAPPROVED" in title2 or "Approved" in msg2,
			msg2,
		)

	def test_development_preview_seal_while_draft(self):
		pub_id = _confirm_and_setup(self.cfg_id)
		published = publish_tender_for_development_preview(pub_id)
		self.assertTrue(published.get("published"))
		self.assertTrue(published.get("development_preview"))
		hash_val = frappe.db.get_value(
			"IT Tender Publication Record", pub_id, "electronic_template_hash"
		)
		self.assertTrue(hash_val)
		snap = json.loads(
			frappe.db.get_value(
				"IT Tender Publication Record", pub_id, "electronic_template_snapshot"
			)
		)
		self.assertEqual(snap.get("approval_status"), "Draft")
		self.assertTrue(snap.get("sections"))


class TestLeanF0InstantiateAndApplicability(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id = _prep_cfg()
		_confirm_and_setup(self.cfg_id)

	def test_deterministic_snapshot_hash(self):
		a = build_electronic_submission_template(self.cfg_id)
		b = build_electronic_submission_template(self.cfg_id)
		self.assertEqual(a["hash"], b["hash"])
		self.assertEqual(len(a["hash"]), 64)

	def test_ui00_applicable_set_has_security_not_lots(self):
		built = build_electronic_submission_template(self.cfg_id)
		keys = [s["section_key"] for s in built["snapshot"]["sections"]]
		self.assertNotIn("lot_and_alternative_selection", keys)
		self.assertIn("tender_security", keys)
		self.assertIn("form_of_tender", keys)
		self.assertEqual(keys[0], "tender_documents_and_addenda")
		# Redesign: FoT after Price Schedule (not early Section IV paper order).
		self.assertEqual(keys[-2], "price_schedule")
		self.assertEqual(keys[-1], "form_of_tender")

	def test_nssf_resolves_applicable_section_set(self):
		out = publish_e1_nssf_with_electronic_template(clear=True)
		counts = out.get("calibration_counts") or {}
		keys = tuple(counts.get("section_keys") or ())
		# Lean NSSF publish forces security Yes (no lots) — registry minus lots only.
		self.assertFalse(counts.get("has_lot_and_alternative_selection"))
		self.assertTrue(counts.get("has_tender_security_section"))
		self.assertNotIn("lot_and_alternative_selection", keys)
		self.assertIn("tender_security", keys)
		for required in (
			"tender_documents_and_addenda",
			"form_of_tender",
			"tender_security",
			"price_schedule",
		):
			self.assertIn(required, keys)
		self.assertEqual(len(keys), len(CANONICAL_SECTION_KEYS) - 1)
		# Tender-owned values may mention the entity; NSSF constants must not be in the template file.
		template_raw = Path(PPRA_IT_STD_V1_PATH).read_text(encoding="utf-8").upper()
		self.assertNotIn("NSSFSPS", template_raw)

	def test_second_it_tender_reuses_same_template(self):
		out = seed_lean_synthetic_it_published(clear=True)
		self.assertEqual(out.get("electronic_template_id"), "PPRA-IT-STD")
		self.assertTrue(out.get("electronic_template_hash"))
		self.assertNotIn("NSSF", cstr(out.get("tender_title") or "").upper())


class TestLeanF0SharedInterfacesAndChecklist(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id = _prep_cfg()
		self.pub_id = _confirm_and_setup(self.cfg_id)
		published = publish_tender_for_development_preview(self.pub_id)
		self.ref = cstr(published.get("publication_ref") or "") or cstr(
			frappe.db.get_value("IT Tender Publication Record", self.pub_id, "publication_ref")
			or ""
		)

	def test_section_response_envelope(self):
		env = normalize_section_response_envelope(
			"form_of_tender", {"bidder_legal_name": "Acme"}, {"source": "test"}
		)
		self.assertEqual(env["section_key"], "form_of_tender")
		self.assertEqual(env["payload"]["bidder_legal_name"], "Acme")
		stored = write_section_response({}, "form_of_tender", env["payload"], env["meta"])
		read = read_section_response(stored, "form_of_tender")
		self.assertEqual(read["payload"]["bidder_legal_name"], "Acme")

	def test_shared_status_snake_case_and_a2_display(self):
		result = derive_generic_section_status(has_responses=False)
		self.assertEqual(result["section_status"], STATUS_NOT_STARTED)
		self.assertEqual(to_display_status(result["section_status"]), "Not Started")
		done = derive_generic_section_status(has_responses=True, is_partial=False)
		self.assertEqual(done["section_status"], STATUS_COMPLETE)
		self.assertEqual(to_display_status(done["section_status"]), "Complete")

	def test_checklist_from_snapshot_not_section_keys(self):
		out = get_submission_checklist(self.ref)
		keys = [s["section_key"] for s in out["sections"]]
		titles = [s["title"] for s in out["sections"]]
		self.assertEqual(keys[0], "tender_documents_and_addenda")
		self.assertIn("form_of_tender", keys)
		self.assertNotEqual(tuple(keys), SECTION_KEYS)
		self.assertTrue(any("Form of Tender" in t or "Tender" in t for t in titles))
		# Snapshot titles win — documents section present.
		docs = next(s for s in out["sections"] if s["section_key"] == "tender_documents_and_addenda")
		self.assertTrue(docs.get("title"))


if __name__ == "__main__":
	unittest.main()
