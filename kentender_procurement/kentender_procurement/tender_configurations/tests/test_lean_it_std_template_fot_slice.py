# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Lean IT STD template + Form of Tender vertical slice (§16 directive tests)."""

from __future__ import annotations

import copy
import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.tender_configurations.electronic_std_templates import (
	CANONICAL_SECTION_KEYS,
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
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
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
from kentender_procurement.tender_configurations.services.form_of_tender import (
	get_form_of_tender,
	save_form_of_tender,
	validate_form_of_tender_response,
)

# Full Review-and-Certify certify/invalidate coverage lives in test_lean_fot_review_certify.py.
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.schema_compiler import SECTION_KEYS
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)


def _publish_cfg(cfg_id: str) -> tuple[str, str]:
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
			"tender_notice": "Lean slice notice.",
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
	return pub_id, ref


class TestLeanTemplateValidator(unittest.TestCase):
	def test_manual_template_passes_validation(self):
		bundle = assert_valid_ppra_it_std_v1()
		self.assertEqual(bundle["template"]["template_id"], "PPRA-IT-STD")
		self.assertEqual(len(bundle["template"]["sections"]), len(CANONICAL_SECTION_KEYS))
		errors = validate_template(bundle["template"])
		self.assertEqual(errors, [])

	def test_slice_obligations_have_source_refs(self):
		bundle = assert_valid_ppra_it_std_v1()
		fot = next(s for s in bundle["template"]["sections"] if s["section_key"] == "form_of_tender")
		self.assertTrue(fot.get("source_refs"))
		for d in fot.get("declarations") or []:
			self.assertTrue(d.get("source_ref"), d)


class TestLeanInstantiatePublish(unittest.TestCase):
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
				"short_scope_summary": "Lean slice tender scope for electronic template tests.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		frappe.db.commit()

	def test_unapproved_template_cannot_publish(self):
		approval = {"status": "Draft", "prepared_by": "a", "approved_by": "b"}
		with self.assertRaises(frappe.ValidationError) as ctx:
			require_approved_template(template={"template_id": "PPRA-IT-STD"}, approval=approval)
		title = cstr(getattr(ctx.exception, "title", None) or "")
		msg = cstr(ctx.exception)
		self.assertTrue(
			"KT_ELECTRONIC_TEMPLATE_UNAPPROVED" in title or "Approved electronic STD" in msg,
			msg,
		)

	def test_missing_bindings_block_build(self):
		frappe.db.set_value("Tender Configuration", self.cfg_id, {"short_scope_summary": ""})
		# Need confirmed package first — confirm after clearing scope should fail at build.
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen.get("preview_status"), "Generated", gen.get("render_exception"))
		conf = confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		with self.assertRaises(frappe.ValidationError) as ctx:
			build_electronic_submission_template(self.cfg_id)
		title = cstr(getattr(ctx.exception, "title", None) or "")
		self.assertTrue(
			"KT_ELECTRONIC_TEMPLATE_BINDINGS" in title or "Missing mandatory" in cstr(ctx.exception)
		)
		_ = conf

	def test_identical_inputs_same_hash(self):
		_publish_cfg(self.cfg_id)
		a = build_electronic_submission_template(self.cfg_id)
		b = build_electronic_submission_template(self.cfg_id)
		self.assertEqual(a["hash"], b["hash"])
		snap_keys = [s["section_key"] for s in a["snapshot"]["sections"]]
		self.assertEqual(snap_keys[-2], "price_schedule")
		self.assertEqual(snap_keys[-1], "form_of_tender")

	def test_published_snapshot_immutable(self):
		pub_id, _ref = _publish_cfg(self.cfg_id)
		pub = frappe.get_doc("IT Tender Publication Record", pub_id)
		self.assertTrue(pub.electronic_template_hash)
		self.assertTrue(pub.electronic_template_snapshot)
		original = cstr(pub.electronic_template_hash)
		pub.electronic_template_hash = "tampered"
		with self.assertRaises(frappe.ValidationError):
			pub.save(ignore_permissions=True)
		# DB value must remain sealed.
		self.assertEqual(
			cstr(frappe.db.get_value("IT Tender Publication Record", pub_id, "electronic_template_hash")),
			original,
		)


class TestLeanNssfAndSynthetic(unittest.TestCase):
	def test_nssf_expected_counts(self):
		frappe.set_user("Administrator")
		out = publish_e1_nssf_with_electronic_template(clear=True)
		counts = out.get("calibration_counts") or {}
		# F0: no NSSF overlay — lean publish applicable set (no lots; security required).
		keys = tuple(counts.get("section_keys") or ())
		self.assertEqual(counts.get("sections"), len(keys))
		self.assertFalse(counts.get("has_lot_and_alternative_selection"))
		self.assertTrue(counts.get("has_tender_security_section"))
		self.assertNotIn("lot_and_alternative_selection", keys)
		self.assertIn("tender_security", keys)
		self.assertIn("form_of_tender", keys)
		self.assertEqual(len(keys), len(CANONICAL_SECTION_KEYS) - 1)
		# Observed collection counts (no NSSF overlay) — stable fixture anchors only.
		self.assertEqual(counts.get("requirement_groups"), 23, counts)
		self.assertEqual(counts.get("requirements"), 190, counts)
		self.assertEqual(counts.get("technical_scoring_criteria"), 7, counts)
		self.assertEqual(counts.get("technical_scoring_total"), 100, counts)
		self.assertEqual(counts.get("technical_pass_mark"), 75, counts)
		self.assertEqual(counts.get("price_lines"), 22, counts)
		self.assertGreaterEqual(int(counts.get("preliminary_criteria") or 0), 9)
		self.assertGreaterEqual(int(counts.get("qualification_criteria") or 0), 9)

	def test_synthetic_it_reuses_template_without_nssf(self):
		frappe.set_user("Administrator")
		out = seed_lean_synthetic_it_published(clear=True)
		self.assertEqual(out.get("electronic_template_id"), "PPRA-IT-STD")
		self.assertTrue(out.get("electronic_template_hash"))
		title = cstr(out.get("tender_title") or "")
		self.assertNotIn("NSSF", title.upper())
		snap = json.loads(
			frappe.db.get_value(
				"IT Tender Publication Record", out["publication_id"], "electronic_template_snapshot"
			)
		)
		blob = json.dumps(snap)
		self.assertNotIn("NSSFSPS", blob)
		# Synthetic seed: security Yes, no lots → registry minus lots.
		keys = [s.get("section_key") for s in (snap.get("sections") or [])]
		self.assertNotIn("lot_and_alternative_selection", keys)
		self.assertIn("tender_security", keys)
		self.assertIn("form_of_tender", keys)
		self.assertEqual(len(keys), len(CANONICAL_SECTION_KEYS) - 1)


class TestLeanChecklistCutover(unittest.TestCase):
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
				"short_scope_summary": "Lean slice tender scope for electronic template tests.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		frappe.db.commit()

	def test_checklist_reads_published_snapshot_not_pack10(self):
		_pub_id, ref = _publish_cfg(self.cfg_id)
		out = get_submission_checklist(ref)
		keys = [s["section_key"] for s in out["sections"]]
		# Applicable snapshot order (ui00: security Yes, no lots) — not pack-10 SECTION_KEYS.
		self.assertNotIn("lot_and_alternative_selection", keys)
		self.assertIn("form_of_tender", keys)
		self.assertIn("tender_security", keys)
		self.assertNotEqual(tuple(keys), SECTION_KEYS)
		fot = next(s for s in out["sections"] if s["section_key"] == "form_of_tender")
		self.assertIn("/sections/form_of_tender", fot["action_url"])
		docs = next(s for s in out["sections"] if s["section_key"] == "tender_documents_and_addenda")
		self.assertIn("/documents", docs["action_url"])


class TestLeanFormOfTender(unittest.TestCase):
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
				"short_scope_summary": "Lean slice tender scope for electronic template tests.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		_, self.ref = _publish_cfg(self.cfg_id)

	def test_save_reload_commissions_only(self):
		saved = save_form_of_tender(
			self.ref, {"commissions_choice": "no", "commissions_rows": []}
		)
		self.assertTrue(saved.get("saved"))
		self.assertEqual(saved["commissions"]["choice"], "no")
		self.assertEqual(saved["section_status"], "In Progress")
		# Save alone does not Complete — certification required.
		self.assertNotEqual(saved["section_status"], "Complete")

		reloaded = get_form_of_tender(self.ref)
		self.assertEqual(reloaded["commissions"]["choice"], "no")
		self.assertEqual(reloaded.get("bidder_owned_fields"), [])

	def test_validation_yes_requires_rows(self):
		fot = get_form_of_tender(self.ref)
		section_def = {"repeatable_tables": fot.get("repeatable_tables") or []}
		result = validate_form_of_tender_response(
			section_def, {"commissions_choice": "yes", "commissions_rows": []}
		)
		self.assertFalse(result["ok"])
		self.assertGreater(result["issue_count"], 0)

	def test_bidder_isolation(self):
		save_form_of_tender(self.ref, {"commissions_choice": "no"})
		email = "lean.bidder.b@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Lean",
					"last_name": "BidderB",
					"send_welcome_email": 0,
					"user_type": "Website User",
				}
			)
			user.insert(ignore_permissions=True)
			user.new_password = "LeanBidderB1!"
			user.save(ignore_permissions=True)
		frappe.set_user(email)
		fot_b = get_form_of_tender(self.ref)
		self.assertNotEqual(fot_b.get("commissions", {}).get("choice"), "no")
		bid_a = frappe.db.get_value(
			"Electronic Bid Submission",
			{"configuration": self.cfg_id, "owner": "Administrator", "status": "Draft"},
			"name",
		)
		self.assertTrue(bid_a)
		from kentender_procurement.tender_configurations.services.electronic_bid import _get_bid

		with self.assertRaises(frappe.PermissionError):
			_get_bid(bid_a)


if __name__ == "__main__":
	unittest.main()
