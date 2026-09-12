# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1 / §5.5.3.3 — schedule derivation, feasibility and
method conditions from a resolved profile (plan Phase 2c, PLN18-206). Pure
functions over profile projections; the DB-backed paths are covered by
`test_plan_workbench`."""

from __future__ import annotations

from datetime import date

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import profiles, schedule


def _schedule(*, applies=None, limits=None, defaults=None, verification="Fixture-verified — not production law"):
	applies = applies or {}
	limits = limits or {}
	defaults = defaults if defaults is not None else {"bid_opening": 21, "evaluation_completion": 30, "award_approval": 5, "award_notification": 2, "contract_signing": 14}
	rows = []
	for index, m in enumerate(schedule.MILESTONES):
		minimum, maximum = limits.get(m, (None, None))
		rows.append({
			"milestone": m, "label": schedule.MILESTONE_LABELS[m], "sequence": index + 1, "applies": applies.get(m, True),
			"counting_rule": "Calendar days", "minimum_days": minimum, "maximum_days": maximum, "default_days": defaults.get(m),
			"basis": "Statutory", "statutory_reference": "s.test", "period_key": profiles.settings.PERIOD_BY_MILESTONE.get(m, ""),
		})
	periods = {r["period_key"]: r for r in rows if r["period_key"] and r["applies"]}
	gaps = [r["milestone"] for r in rows if r["applies"] and r["period_key"] and r["default_days"] is None]
	return {"found": True, "profile": "SPR-TEST-V1", "verification_status": verification, "milestones": rows, "periods": periods, "complete": not gaps, "gaps": gaps, "counting_rule": "Calendar days"}


class TestScheduleFromProfile(IntegrationTestCase):
	def test_baseline_follows_the_profile_order_and_skips_a_non_applicable_milestone(self):
		profile = _schedule(applies={"award_notification": False})
		periods = profiles.validate_period_inputs({"tendering_period_days": 21, "evaluation_period_days": 30, "award_approval_buffer_days": 5, "standstill_period_days": 14}, profile)
		self.assertNotIn("notification_buffer_days", periods)
		baseline = profiles.derive_baseline("2101-09-01", periods, "2102-04-30", profile)
		self.assertEqual(baseline["baseline_bid_opening_date"], date(2101, 9, 22))
		self.assertEqual(baseline["baseline_evaluation_completion_date"], date(2101, 10, 22))
		self.assertEqual(baseline["baseline_award_approval_date"], date(2101, 10, 27))
		self.assertIsNone(baseline["baseline_award_notification_date"])  # Not applicable, never zero
		self.assertEqual(baseline["baseline_contract_signing_date"], date(2101, 11, 10))
		self.assertEqual(baseline["baseline_delivery_completion_date"], date(2102, 4, 30))
		self.assertEqual(profiles.applicable_milestones(profile), ["invitation", "bid_opening", "evaluation_completion", "award_approval", "contract_signing", "delivery_completion"])

	def test_period_limits_come_from_the_profile_with_labelled_parameters(self):
		profile = _schedule(limits={"bid_opening": (7, None), "evaluation_completion": (None, 30), "contract_signing": (14, None)})
		for key, value, rule, limit in (("tendering_period_days", 6, "minimum", 7), ("evaluation_period_days", 31, "maximum", 30), ("standstill_period_days", 13, "minimum", 14)):
			with self.subTest(key=key):
				with self.assertRaises(ProcurementPlanningError) as caught:
					profiles.validate_period_inputs({**profiles.default_period_inputs(profile), key: value}, profile)
				self.assertEqual(caught.exception.code, "PLN_PROFILE_PERIOD_INVALID")
				self.assertEqual(caught.exception.detail["period"], key)
				self.assertEqual(caught.exception.detail["rule"], rule)
				self.assertEqual(caught.exception.detail["limit"], limit)
				self.assertEqual(caught.exception.detail["offered"], value)
				self.assertEqual(caught.exception.detail["statutory_reference"], "s.test")
		# a profile default fills a missing period; no profile → Draft values as offered
		self.assertEqual(profiles.validate_period_inputs({}, profile)["tendering_period_days"], 21)
		self.assertEqual(profiles.validate_period_inputs({k: 1 for k in profiles.PERIOD_KEYS}, dict(profiles.NOT_FOUND))["standstill_period_days"], 1)
		with self.assertRaises(ProcurementPlanningError) as caught:
			profiles.validate_period_inputs({k: 1 for k in profiles.PERIOD_KEYS if k != "standstill_period_days"}, dict(profiles.NOT_FOUND))
		self.assertEqual(caught.exception.code, "PLN_SCHEDULE_INVALID")

	def test_feasibility_is_signing_plus_estimated_delivery_against_the_source_boundary(self):
		profile = _schedule()
		periods = profiles.default_period_inputs(profile)
		baseline = profiles.derive_baseline("2101-09-01", periods, "2101-12-31", profile)
		self.assertEqual(baseline["baseline_contract_signing_date"], date(2101, 11, 12))
		self.assertEqual(profiles.estimated_completion(baseline, 30), date(2101, 12, 12))
		self.assertTrue(profiles.feasible(baseline, 30))
		self.assertTrue(profiles.feasible(baseline, 49))
		self.assertFalse(profiles.feasible(baseline, 50))
		self.assertTrue(profiles.feasible(baseline, 0))  # zero is an explicit same-day estimate
		self.assertIsNone(profiles.feasible(baseline, None))
		self.assertFalse(schedule.delivery_boundary_ok(baseline, None))

	def test_method_conditions_check_known_facts_and_require_declared_evidence(self):
		method = {
			"found": True, "profile": "MPR-TEST-V1", "verification_status": "Fixture-verified — not production law", "category_supported": True,
			"conditions": [
				{"condition_id": "G-VALUE", "kind": "Known fact", "description": "goods limit", "procurement_category": "Goods", "minimum_amount": 0, "maximum_amount": 50000, "cumulative_basis": "Per item", "mandatory": True},
				{"condition_id": "S-VALUE", "kind": "Known fact", "description": "services limit", "procurement_category": "Services", "minimum_amount": 0, "maximum_amount": 0, "cumulative_basis": "Funds allocated", "mandatory": True},
				{"condition_id": "CIRCUMSTANCES", "kind": "Declaration", "description": "circumstances", "procurement_category": "", "mandatory": True, "required_evidence": "Method eligibility record", "authorisation_actor": "Accounting Officer", "authorisation_stage": "Before invitation"},
			],
		}
		over = profiles.method_conditions(method, procurement_category="Goods", planned_value=1_000_000)
		self.assertFalse(over["admissible"])
		self.assertEqual(over["failed"], ["G-VALUE"])
		self.assertEqual(over["missing_evidence"], ["CIRCUMSTANCES"])
		within = profiles.method_conditions(method, procurement_category="Goods", planned_value=40_000, evidence_rows=[{"condition_id": "CIRCUMSTANCES", "evidence_reference": "MER-1"}])
		self.assertTrue(within["admissible"])
		self.assertFalse(within["evidence_complete"])  # the authorising actor's reference is due too
		declared = profiles.method_conditions(method, procurement_category="Goods", planned_value=40_000, evidence_rows=[{"condition_id": "CIRCUMSTANCES", "evidence_reference": "MER-1", "authorisation_reference": "AO/2101/7"}])
		self.assertTrue(declared["evidence_complete"])
		self.assertEqual([r["condition_id"] for r in declared["results"]], ["G-VALUE", "CIRCUMSTANCES"])  # the services row does not apply
		self.assertFalse(profiles.method_conditions(dict(profiles.NOT_FOUND), procurement_category="Goods", planned_value=1)["available"])

	def test_verification_statuses(self):
		self.assertTrue(profiles.is_verified({"verification_status": "Verified"}))
		self.assertTrue(profiles.is_verified({"verification_status": "Fixture-verified — not production law"}))
		self.assertFalse(profiles.is_verified({"verification_status": "Production verification pending"}))
		self.assertFalse(profiles.is_verified({}))
