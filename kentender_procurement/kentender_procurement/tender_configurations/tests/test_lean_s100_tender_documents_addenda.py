# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""S100 — Tender Documents & Addenda prove-list."""

from __future__ import annotations

import json
import unittest

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
from kentender_procurement.tender_configurations.services.electronic_bid import _get_bid
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	ACK_STATUS_COMPLETE,
	acknowledge_tender_documents,
	append_issued_addendum,
	get_tender_documents_addenda,
)


def _prep_and_publish() -> tuple[str, str, str]:
	"""Return (cfg_id, pub_id, publication_ref)."""
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "S100 tender documents scope for electronic acknowledgements.",
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
			"tender_notice": "S100 documents notice.",
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


class TestLeanS100DocumentsAddenda(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def test_current_package_display(self):
		out = get_tender_documents_addenda(self.ref)
		# Bidder DTO must not expose binding digests; backend package still has them.
		self.assertNotIn("package_context", out)
		self.assertNotIn("package_display", out)
		self.assertNotIn("package_summary", out)
		backend = resolve_published_tender_backend(self.ref)
		self.assertTrue((backend.get("confirmed_package") or {}).get("document_hash"))
		self.assertEqual(out["published_tender_ref"], self.ref)
		self.assertTrue(out.get("documents") is not None)

	def test_version_bound_acknowledgement(self):
		out = acknowledge_tender_documents(self.ref)
		self.assertEqual(out["documents_acknowledged"], 1)
		self.assertEqual(out["acknowledgement_status"], ACK_STATUS_COMPLETE)
		backend = resolve_published_tender_backend(self.ref)
		bid = frappe.get_doc("Electronic Bid Submission", backend["bid_id"])
		payload = json.loads(bid.responses or "{}").get(out["section_key"]) or {}
		self.assertEqual(payload.get("publication_ref"), self.ref)
		self.assertTrue(payload.get("package_document_hash"))
		self.assertIn("addenda_set_digest", payload)
		self.assertEqual(payload.get("acknowledged_by"), "Administrator")

	def test_missing_acknowledgement_blocker_and_derived_completion(self):
		checklist = get_submission_checklist(self.ref)
		docs = next(s for s in checklist["sections"] if s["section_key"] == "tender_documents_and_addenda")
		self.assertEqual(docs["status"], "Not Started")

		dto = get_tender_documents_addenda(self.ref)
		self.assertEqual(dto["documents_acknowledged"], 0)
		self.assertEqual(dto["continue_enabled"], 0)

		acknowledge_tender_documents(self.ref)
		checklist2 = get_submission_checklist(self.ref)
		docs2 = next(
			s for s in checklist2["sections"] if s["section_key"] == "tender_documents_and_addenda"
		)
		self.assertEqual(docs2["status"], "Complete")

	def test_addendum_invalidation_preserves_history(self):
		ack = acknowledge_tender_documents(self.ref)
		self.assertEqual(ack["documents_acknowledged"], 1)
		backend = resolve_published_tender_backend(self.ref)
		bid_id = backend["bid_id"]
		section_key = ack["section_key"]

		append_issued_addendum(
			self.pub_id,
			{
				"id": "ADD-S100-1",
				"title": "Material schedule change",
				"summary": "Closing date moved.",
				"requires_acknowledgement": True,
				"version": "v1",
				"is_material": True,
			},
		)

		# Read path invalidates stale binding.
		dto = get_tender_documents_addenda(self.ref)
		self.assertEqual(dto["documents_acknowledged"], 0)
		self.assertEqual(dto["acknowledgement_stale"], 1)
		self.assertNotIn("acknowledgement_history_count", dto)
		self.assertEqual(len(dto.get("addenda") or []), 1)
		self.assertEqual(dto["addenda"][0]["id"], "ADD-S100-1")
		self.assertEqual(dto["addenda"][0].get("is_new"), 1)

		bid = frappe.get_doc("Electronic Bid Submission", bid_id)
		payload = json.loads(bid.responses or "{}").get(section_key) or {}
		self.assertFalse(payload.get("acknowledged") in (True, 1, "1"))
		history = payload.get("acknowledgement_history") or []
		self.assertTrue(history)
		self.assertTrue(
			any(cstr(h.get("publication_ref")) == self.ref for h in history),
			history,
		)

		# Re-ack binds new digest including the addendum.
		again = acknowledge_tender_documents(self.ref)
		self.assertEqual(again["documents_acknowledged"], 1)
		self.assertEqual(again["addenda_block_submission"], 0)
		payload2 = json.loads(
			frappe.db.get_value("Electronic Bid Submission", bid_id, "responses") or "{}"
		).get(section_key) or {}
		acked_ids = {
			cstr(x.get("id") if isinstance(x, dict) else x)
			for x in (payload2.get("addenda_acknowledged") or [])
		}
		self.assertIn("ADD-S100-1", acked_ids)

		checklist = get_submission_checklist(self.ref)
		docs = next(s for s in checklist["sections"] if s["section_key"] == "tender_documents_and_addenda")
		self.assertEqual(docs["status"], "Complete")

	def test_bidder_isolation(self):
		acknowledge_tender_documents(self.ref)
		bid_a = resolve_published_tender_backend(self.ref)["bid_id"]
		email = "s100.bidder.b@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "S100",
					"last_name": "BidderB",
					"send_welcome_email": 0,
					"user_type": "Website User",
				}
			)
			user.insert(ignore_permissions=True)
			user.new_password = "S100BidderB1!"
			user.save(ignore_permissions=True)
		frappe.set_user(email)
		dto_b = get_tender_documents_addenda(self.ref)
		self.assertNotIn("bid_id", dto_b)
		self.assertEqual(dto_b.get("documents_acknowledged"), 0)
		bid_b = resolve_published_tender_backend(self.ref)["bid_id"]
		self.assertNotEqual(bid_b, bid_a)
		with self.assertRaises(frappe.PermissionError):
			_get_bid(bid_a)


if __name__ == "__main__":
	unittest.main()
