# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-DESK-SCHED-001/002 — Desk wiring for Implementation Schedule composer."""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class TestItWizardImplementationScheduleDeskWiring(UnitTestCase):
	def test_hooks_register_implementation_schedule_page_js(self) -> None:
		from kentender_procurement.hooks import page_js

		self.assertEqual(
			page_js.get("it-tender-configuration-implementation-schedule"),
			"public/js/it_wizard_implementation_schedule_page.js",
		)

	def test_implementation_schedule_page_js_embeds_static_asset_iframe(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_implementation_schedule_page.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn('frappe.pages["it-tender-configuration-implementation-schedule"]', source)
		self.assertIn(
			"/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_implementation_schedule.html",
			source,
		)
		self.assertIn('testid: "it-wizard-implementation-schedule"', source)
		self.assertIn("kentender.it_wizard.mount_page", source)
		self.assertIn('screen: "implementation_schedule"', source)

	def test_engine_hydrates_implementation_schedule_symbols(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"js",
			"it_wizard_engine.js",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("it-tender-configuration-implementation-schedule", source)
		self.assertIn("STEP_ROUTE_MAP", source)
		self.assertIn("IMPLEMENTATION_SCHEDULE", source)
		self.assertIn("unwrap_envelope_data", source)
		self.assertIn("harmonize_it_schedule_page_layout", source)
		self.assertIn("data-itw-sched-context", source)
		self.assertIn("data-itw-sched-table-host", source)
		self.assertIn("data-itw-sched-drawer", source)
		self.assertIn("data-itw-sched-guidance", source)
		self.assertIn("data-itw-sched-actions", source)
		self.assertIn("[data-itw-sched-actions]", source)
		self.assertIn("hydrate_it_schedule_guidance", source)
		self.assertIn("open_it_schedule_drawer", source)
		self.assertIn("close_it_schedule_drawer", source)
		self.assertIn("fetch_implementation_schedule_data", source)
		self.assertIn("get_implementation_schedule_api", source)
		self.assertIn("save_implementation_schedule_api", source)
		self.assertIn("apply_it_schedule_payload", source)
		self.assertIn("schedule_payload_data", source)
		self.assertIn("strip_it_schedule_fixture_scripts", source)
		self.assertIn("hydrate_it_schedule_context", source)
		# Context strip: Tender Ref uses tender_number (falls back to configuration_id);
		# values write to the value span (last span), never the muted label span.
		self.assertIn("data.tender_number || data.configuration_id", source)
		self.assertIn("spans[spans.length - 1]", source)
		self.assertIn("hydrate_it_schedule_table", source)
		self.assertIn("hydrate_it_schedule_mode", source)
		self.assertIn("collect_single_turnkey_values", source)
		self.assertIn("confirm_single_turnkey_switch", source)
		self.assertIn("data-itw-turnkey-field", source)
		self.assertIn("hydrate_it_schedule_drawer", source)
		self.assertIn("wire_it_schedule_interactions", source)
		self.assertIn("disable_it_schedule_stub_actions", source)
		self.assertIn("hydrate_it_schedule_field_sources", source)
		self.assertIn("data-itw-sched-source", source)
		self.assertIn("data-itw-sched-field-action", source)
		self.assertIn("schedule_field_sources_for_phase", source)
		self.assertIn("SCHEDULE_TEMPLATE_DEFAULTS", source)
		self.assertIn("handle_it_schedule_field_action", source)
		self.assertIn("reset_sched_field_to_template", source)
		self.assertIn("wire_it_schedule_field_actions", source)

	def test_implementation_schedule_page_css_hides_frappe_page_head(self) -> None:
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"public",
			"css",
			"it_wizard_implementation_schedule_page.css",
		)
		source = open(path, encoding="utf-8").read()
		self.assertIn("body.it-wizard-implementation-schedule-shell .page-head", source)
		self.assertIn("display: none !important", source)


class TestItWizardImplementationScheduleDeskWiringSite(IntegrationTestCase):
	def test_implementation_schedule_page_exists_on_site(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "it-tender-configuration-implementation-schedule"))
