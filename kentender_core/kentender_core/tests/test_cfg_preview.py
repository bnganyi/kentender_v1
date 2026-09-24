"""CFG-CHG-002 v0.14 §7.2/§7.3 (CFG-UX-AC-11, -16) — PreviewConfigurationVersion.

One read-only check the Add rule / new version form runs before any write:
schema defects, missing details, overlapping coverage and the replacement's
effect — reported separately, and nothing is written (no set, version,
journal or audit row).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_preview
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import regulatory_reference as register
from kentender_core.tests import v16_fixtures as fx

NS = "KT_TEST_CFG_PREVIEW"
PLAN = {"obligation_code": "AGPO-30", "measure_stage": "PlanningAllocation", "target_percent": 30}


def _counts():
	return {
		doctype: frappe.db.count(doctype)
		for doctype in ("Regulatory Reference Set", "Regulatory Reference", "Reference Data Command Journal", "Audit Event")
	}


class TestPreviewConfigurationVersion(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		fx.ensure_site_configured()
		register.purge_fixture_references(NS)
		cls.set = register.create_regulatory_reference(
			reference_key="KT-TEST-PREVIEW", reference_kind="Reservation rules", display_name="KT Test Preview", fixture_namespace=NS
		)["reference_set"]
		cls.v1 = register.save_regulatory_reference_version(
			reference_set=cls.set, payload=PLAN, effective_from="2097-07-01", effective_until="2098-06-30",
			applicability_basis="FiscalYearStart", verification_status="Verified", fixture_namespace=NS,
		)["reference"]
		frappe.db.commit()
		cls.addClassCleanup(lambda: (register.purge_fixture_references(NS), frappe.db.commit()))

	def preview(self, **kwargs):
		base = {"reference_kind": "Reservation rules", "payload": PLAN, "effective_from": "2099-07-01", "applicability_basis": "FiscalYearStart"}
		return register.preview_configuration_version(**{**base, **kwargs})

	def test_writes_nothing(self):
		before = _counts()
		self.preview(reference_set=self.set, effective_from="2097-07-01")
		self.preview(reference_key="KT-TEST-PREVIEW-NEW")
		self.assertEqual(_counts(), before)

	def test_a_structurally_valid_version_reports_no_schema_defects(self):
		out = self.preview(reference_key="KT-TEST-PREVIEW-NEW")
		self.assertTrue(out["schema"]["ok"], out["schema"])
		self.assertEqual(out["schema"]["errors"], [])

	def test_schema_defects_are_reported_not_raised(self):
		out = self.preview(reference_key="KT-TEST-PREVIEW-NEW", payload={"obligation_code": "X", "target_percent": 30})
		self.assertFalse(out["schema"]["ok"])
		self.assertEqual(out["schema"]["errors"][0]["code"], "CFG_SCHEMA_UNSUPPORTED")
		# Reported as data, so no Frappe pop-up message rides back with it.
		self.assertEqual(frappe.local.message_log or [], [])

	def test_the_api_accepts_the_browser_transport_json(self):
		"""Lists and dicts arrive as JSON strings from `frappe.call`."""
		import json

		from kentender_core.api import procurement_settings_api as api

		out = api.preview_configuration_version(
			reference_kind="Reservation rules",
			payload=json.dumps(PLAN),
			effective_from="2098-01-01",
			applicability_basis="FiscalYearStart",
			reference_set=self.set,
			supersedes_version_ids=json.dumps([self.v1]),
		)
		self.assertTrue(out["coverage"]["overlapping"][0]["declared"])

	def test_a_new_rule_key_already_in_use_or_an_unknown_kind_is_a_schema_defect(self):
		taken = self.preview(reference_key="KT-TEST-PREVIEW")
		self.assertFalse(taken["schema"]["ok"])
		unknown = self.preview(reference_kind="Not a kind", reference_key="KT-TEST-PREVIEW-X")
		self.assertFalse(unknown["schema"]["ok"])

	def test_dates_out_of_order_are_a_schema_defect(self):
		out = self.preview(reference_key="KT-TEST-PREVIEW-NEW", effective_from="2099-07-01", effective_until="2099-01-01")
		self.assertFalse(out["schema"]["ok"])

	def test_missing_legal_details_are_listed_as_incompleteness_not_as_a_refusal(self):
		out = self.preview(reference_key="KT-TEST-PREVIEW-NEW")
		self.assertTrue(out["schema"]["ok"])
		self.assertFalse(out["completeness"]["complete"])
		self.assertIn("Interpretation", out["completeness"]["missing"])
		self.assertIn("Instrument", out["completeness"]["missing"])

	def test_overlapping_coverage_is_named_and_says_whether_the_replacement_was_declared(self):
		undeclared = self.preview(reference_set=self.set, effective_from="2098-01-01")
		self.assertEqual([row["reference"] for row in undeclared["coverage"]["overlapping"]], [self.v1])
		self.assertFalse(undeclared["coverage"]["overlapping"][0]["declared"])
		declared = self.preview(reference_set=self.set, effective_from="2098-01-01", supersedes_version_ids=[self.v1])
		self.assertTrue(declared["coverage"]["overlapping"][0]["declared"])
		clear = self.preview(reference_set=self.set, effective_from="2099-07-01")
		self.assertEqual(clear["coverage"]["overlapping"], [])

	def test_replacing_verified_coverage_with_a_pending_version_warns_it_will_block_new_use(self):
		out = self.preview(reference_set=self.set, effective_from="2098-01-01", supersedes_version_ids=[self.v1])
		self.assertTrue(out["impact"]["blocks_new_use"])
		# No usage counter exists yet: say so rather than report zero (§11.2).
		self.assertFalse(out["impact"]["usage_known"])
