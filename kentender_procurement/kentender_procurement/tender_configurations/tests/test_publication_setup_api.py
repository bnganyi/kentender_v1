# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Publications A2/A3 domain API contract tests (v7)."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_AWAITING_PUBLICATION_SETUP,
	STATUS_PUBLISHED,
	STATUS_RETURNED_FOR_CORRECTION,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.package_review import (
	get_package_review_summary,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	get_publication_setup,
	list_publications,
	publish_tender,
	return_publication_for_correction,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)


class TestPublicationSetupApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"std_version",
			CANONICAL_PACKAGE_ID,
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		# Publish integrity requires a locked bidder submission schema on the confirmed package.
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"bidder_submission_schema",
			json.dumps({"version": 1, "sections": [{"id": "eligibility", "title": "Eligibility"}]}),
		)
		frappe.db.commit()

	def _confirm(self):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen.get("preview_status"), "Generated", gen.get("render_exception"))
		return confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})

	def test_package_review_summary_after_generate(self):
		generate_document_preview(self.cfg_id)
		summary = get_package_review_summary(self.cfg_id)
		self.assertEqual(summary["configuration_id"], self.cfg_id)
		self.assertTrue(summary.get("package_readiness"))
		self.assertTrue(summary.get("bidder_experience"))
		self.assertIn("document_output", summary)
		self.assertTrue(summary.get("can_confirm_package") or summary.get("package_confirmed"))
		ctx = summary.get("context") or {}
		# Civic Ledger 8-cell strip contract keys (C1-M3 §4).
		for key in (
			"procurement_package_ref",
			"procurement_title",
			"procuring_entity_name",
			"procurement_method_label",
			"std_family_label",
			"standard_tender_document_label",
			"configuration_status_label",
		):
			self.assertIn(key, ctx)
		self.assertTrue(ctx.get("procurement_title") or ctx.get("procurement_package_ref"))

	def test_publication_setup_includes_configuration_context(self):
		conf = self._confirm()
		setup = get_publication_setup(conf["publication_id"])
		ctx = setup.get("context") or {}
		self.assertTrue(ctx.get("procurement_title"), ctx)
		self.assertTrue(ctx.get("procuring_entity_name") or ctx.get("standard_tender_document_label"), ctx)
		self.assertTrue(ctx.get("configuration_status_label"), ctx)

	def test_publication_setup_exposes_business_refs_not_hash_ids(self):
		conf = self._confirm()
		setup = get_publication_setup(conf["publication_id"])
		pub_ctx = setup.get("publication_context") or {}
		pub_ref = cstr(pub_ctx.get("publication_ref") or setup.get("publication_ref") or "")
		doc_pkg = cstr(pub_ctx.get("doc_package_ref") or "")
		self.assertTrue(pub_ref.startswith("PUB-"), pub_ref)
		self.assertNotEqual(pub_ref, setup["publication_id"])
		self.assertTrue(doc_pkg)
		self.assertNotEqual(doc_pkg, setup.get("confirmed_package", {}).get("package_id"))
		# Hash autonames are short alnum without separators.
		self.assertIn("-", pub_ref)
		self.assertIn("-", doc_pkg)

	def test_confirm_lists_in_awaiting_setup(self):
		conf = self._confirm()
		pub_id = conf["publication_id"]
		listed = list_publications(tab="awaiting_setup")
		ids = {r["publication_id"] for r in listed["rows"]}
		self.assertIn(pub_id, ids)
		self.assertGreaterEqual(listed["summary"]["awaiting_setup_count"], 1)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_AWAITING_PUBLICATION_SETUP)

	def test_save_setup_ready_and_publish(self):
		conf = self._confirm()
		pub_id = conf["publication_id"]
		now = now_datetime()
		payload = {
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "Public notice for IT tender publication test.",
			"clarification_deadline": str(add_to_date(now, days=5)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=14, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		}
		saved = save_publication_setup(pub_id, payload)
		self.assertEqual(saved["status"], "Ready to Publish")
		self.assertEqual(saved["fields"]["bidder_visibility"], "All Registered Bidders")
		self.assertEqual(saved["fields"]["publication_mode"], "immediate")

		# Content boundary: setup must not expose editable CFG fields.
		self.assertNotIn("it_requirements", saved)
		self.assertNotIn("evaluation_setup", saved)

		published = publish_tender(pub_id)
		self.assertTrue(published.get("published"))
		self.assertEqual(published["status"], "Published")
		self.assertTrue(published.get("setup_locked"))
		self.assertTrue(published.get("bidder_workspace_activated"))
		# Immediate mode must survive publish even though publication_datetime is set.
		self.assertEqual(published["fields"]["publication_mode"], "immediate")
		# Published immediate tenders must still expose the effective publication stamp.
		self.assertTrue(cstr(published["fields"].get("publication_datetime") or "").strip())
		self.assertTrue(cstr(published.get("published_at") or "").strip())
		reloaded = get_publication_setup(pub_id)
		self.assertEqual(reloaded["fields"]["publication_mode"], "immediate")
		self.assertTrue(cstr(reloaded["fields"].get("publication_datetime") or "").strip())
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_PUBLISHED)

		# Cannot edit after publish.
		with self.assertRaises(Exception):
			save_publication_setup(pub_id, payload)

	def test_save_setup_scheduled_when_future(self):
		conf = self._confirm()
		pub_id = conf["publication_id"]
		future = add_to_date(now_datetime(), days=3)
		payload = {
			"publication_mode": "scheduled",
			"publication_datetime": str(future),
			"tender_notice": "Scheduled notice",
			"submission_deadline": str(add_to_date(future, days=10)),
			"opening_datetime": str(add_to_date(future, days=10, hours=1)),
			"bidder_visibility": "Invited Bidders Only",
			"activate_bidder_workspace": 1,
		}
		saved = save_publication_setup(pub_id, payload)
		self.assertEqual(saved["status"], "Scheduled")
		self.assertEqual(saved["fields"]["publication_mode"], "scheduled")

	def test_publish_blocks_missing_notice(self):
		conf = self._confirm()
		pub_id = conf["publication_id"]
		# Reset any reused publication row so publish must validate required fields.
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_id,
			{
				"tender_notice": "",
				"publication_datetime": None,
				"submission_deadline": None,
				"opening_datetime": None,
				"bidder_visibility": "",
				"activate_bidder_workspace": 0,
				"status": "Awaiting Publication Setup",
				"setup_locked": 0,
			},
		)
		frappe.db.commit()
		with self.assertRaises(Exception):
			publish_tender(pub_id)

	def test_return_from_publication(self):
		conf = self._confirm()
		pub_id = conf["publication_id"]
		out = return_publication_for_correction(pub_id, {"reason": "Dates need PE correction"})
		self.assertTrue(out.get("returned"))
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)
		self.assertFalse(doc.confirmed_document_package)
		setup = get_publication_setup(pub_id)
		self.assertEqual(setup["status"], "Returned")


if __name__ == "__main__":
	unittest.main()
