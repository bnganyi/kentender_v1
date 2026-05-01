# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 4 conditional state.

Tests ``get_officer_conditional_state`` against representative configuration
branches (doc 4 §8).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step4_conditional_field_state
"""

from __future__ import annotations

import json
from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.services.officer_tender_config import (
	get_officer_conditional_state,
)


def _primary_sample_configuration() -> dict:
	repo = Path(__file__).resolve().parents[4]
	path = (
		repo
		/ "kentender_procurement"
		/ "kentender_procurement"
		/ "tender_management"
		/ "std_templates"
		/ "ke_ppra_works_building_2022_04_poc"
		/ "sample_tender.json"
	)
	data = json.loads(path.read_text(encoding="utf-8"))
	return dict(data["configuration"])


class TestOfficerPocStep4ConditionalFieldState(UnitTestCase):
	def test_jv_off_hides_max_members(self) -> None:
		cfg = _primary_sample_configuration()
		cfg["PARTICIPATION.JV_ALLOWED"] = False
		state = get_officer_conditional_state(cfg)
		self.assertIn("PARTICIPATION.MAX_JV_MEMBERS", state["hidden_fields"])

	def test_jv_on_shows_max_members(self) -> None:
		cfg = _primary_sample_configuration()
		cfg["PARTICIPATION.JV_ALLOWED"] = True
		state = get_officer_conditional_state(cfg)
		self.assertNotIn("PARTICIPATION.MAX_JV_MEMBERS", state["hidden_fields"])
		codes = {n["code"] for n in state["notices"]}
		self.assertIn("JV_BRANCH", codes)

	def test_tender_securing_declaration_hides_amount_fields(self) -> None:
		cfg = _primary_sample_configuration()
		cfg["SECURITY.TENDER_SECURITY_MODE"] = "TENDER_SECURING_DECLARATION"
		state = get_officer_conditional_state(cfg)
		for fc in (
			"SECURITY.TENDER_SECURITY_AMOUNT",
			"SECURITY.TENDER_SECURITY_TYPE",
			"SECURITY.TENDER_SECURITY_CURRENCY",
		):
			with self.subTest(fc=fc):
				self.assertIn(fc, state["hidden_fields"])

	def test_international_shows_foreign_tenderer_field(self) -> None:
		cfg = _primary_sample_configuration()
		cfg["METHOD.TENDER_SCOPE"] = "INTERNATIONAL"
		state = get_officer_conditional_state(cfg)
		self.assertNotIn(
			"PARTICIPATION.FOREIGN_TENDERER_LOCAL_INPUT_RULE_APPLICABLE",
			state["hidden_fields"],
		)

	def test_national_hides_foreign_tenderer_field(self) -> None:
		cfg = _primary_sample_configuration()
		cfg["METHOD.TENDER_SCOPE"] = "NATIONAL"
		state = get_officer_conditional_state(cfg)
		self.assertIn(
			"PARTICIPATION.FOREIGN_TENDERER_LOCAL_INPUT_RULE_APPLICABLE",
			state["hidden_fields"],
		)
