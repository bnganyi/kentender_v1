# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F1: bidder_submission_schema is system-compiled at package confirm (not a PE CFG step)."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import cstr

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	build_confirmed_package_from_doc,
)


class TestF1BidderSubmissionSchemaOnConfirm(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_active_canonical_ppra_it_std(force_reimport=False)
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
		# Clear the fixture stub — PE never fills this field in the wizard.
		frappe.db.set_value("Tender Configuration", self.cfg_id, "bidder_submission_schema", "")
		frappe.db.commit()

	def test_build_package_compiles_bidder_submission_schema(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertFalse(cstr(doc.bidder_submission_schema or "").strip())
		payload = build_confirmed_package_from_doc(
			doc,
			preview_blob={
				"preview_html": "<html><body>Package confirm fixture</body></html>",
				"std_version": CANONICAL_PACKAGE_ID,
			},
		)
		blob = cstr(payload.get("bidder_submission_schema") or "").strip()
		self.assertTrue(blob, "Confirm payload must include compiled bidder_submission_schema")
		parsed = json.loads(blob)
		self.assertIsInstance(parsed.get("sections"), list)
		self.assertTrue(parsed.get("schema_hash"))
		# persist_compiled_schema also writes the configuration field.
		doc.reload()
		self.assertTrue(cstr(doc.bidder_submission_schema or "").strip())
