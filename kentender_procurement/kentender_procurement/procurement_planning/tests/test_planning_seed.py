# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §14 seed-contract tests (Phase 11).

Asserts the §14.1/§14.3 prerequisite verification, the §14.2 actors, the
integrated §14.4–14.6 baseline (built through the real commands, validated
through the same domain services), §14.10's idempotent-rerun rule, and that
the isolated profiles rebuild and reset cleanly. Profile tests mutate the
world inside the test transaction only — the runner's rollback restores the
committed baseline."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.seeds import kentender_mvp_v1 as seed


class SeedCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.baseline = seed.upsert_planning_base(commit=False)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")


class TestPrerequisitesAndActors(SeedCase):
	def test_prerequisite_verification_passes_and_resolves_the_authoritative_records(self):
		resolved = seed.verify_prerequisites()
		self.assertTrue(resolved["bl_dhi"])
		self.assertTrue(resolved["bl_hwd"])
		self.assertTrue(resolved["objective"])
		self.assertEqual(
			frappe.db.get_value("Strategy Node", resolved["objective"], "title"),
			seed.OBJECTIVE_TITLE,
		)

	def test_the_submission_window_holds_the_exact_specified_instants(self):
		row = frappe.db.get_value(
			"Departmental Plan Submission Window", {"pe_fy_context": seed.CTX},
			["opens_at", "closes_at"], as_dict=True,
		)
		self.assertEqual(str(row.opens_at), seed.WINDOW_OPENS)
		self.assertEqual(str(row.closes_at), seed.WINDOW_CLOSES)

	def test_the_publication_destination_exists_with_the_specified_identifier(self):
		self.assertTrue(
			frappe.db.exists(
				"Annual Plan Publication Destination", {"destination_id": seed.DESTINATION_ID}
			)
		)

	def test_every_named_actor_exists_enabled_with_their_role_and_scope(self):
		expectations = {
			seed.PLANNER: "Procurement Planner",
			seed.BUDGET_OFFICER: "Budget Officer",
			seed.ACCOUNTING_OFFICER: "Accounting Officer",
			seed.STATUTORY: "Plan Statutory Approver",
			seed.AUDITOR: "Planning Auditor",
		}
		for email, role in expectations.items():
			self.assertTrue(frappe.db.get_value("User", email, "enabled"), email)
			self.assertIn(role, frappe.get_roles(email), email)
			self.assertTrue(
				frappe.db.exists(
					"User Permission",
					{"user": email, "allow": "Procuring Entity", "for_value": seed.PE},
				),
				email,
			)

	def test_the_no_context_actor_has_no_planning_assignment(self):
		self.assertTrue(frappe.db.get_value("User", seed.NO_CONTEXT, "enabled"))
		roles = set(frappe.get_roles(seed.NO_CONTEXT))
		self.assertFalse(
			roles & {"Procurement Planner", "Budget Officer", "Accounting Officer",
			         "Plan Statutory Approver", "Planning Auditor"}
		)
		self.assertFalse(
			frappe.db.exists(
				"User Permission",
				{"user": seed.NO_CONTEXT, "allow": "Procuring Entity", "for_value": seed.PE},
			)
		)


class TestIntegratedBaseline(SeedCase):
	def test_the_annual_plan_is_active_with_one_confirmed_item_at_80m(self):
		for row in seed.validate_planning_seed():
			self.assertTrue(row["ok"], f"{row['check']}: {row.get('detail')}")

	def test_no_business_decision_was_made_by_administrator(self):
		version = frappe.db.get_value("Annual Plan", {"procuring_entity": seed.PE}, "active_version")
		for stage, actor in (
			("Accounting Officer adoption", seed.ACCOUNTING_OFFICER),
			("Statutory approval", seed.STATUTORY),
		):
			decision = frappe.db.get_value(
				"Plan Governance Decision", {"plan_version": version, "stage": stage},
				"actor",
			)
			self.assertEqual(decision, actor, stage)
		finance_actor = frappe.db.get_value(
			"Plan Finance Decision", {"fixture_namespace": seed.NS, "decision": "Confirm funding"},
			"actor",
		)
		self.assertEqual(finance_actor, seed.BUDGET_OFFICER)

	def test_the_design_clock_instants_are_stamped(self):
		version = frappe.db.get_value("Annual Plan", {"procuring_entity": seed.PE}, "active_version")
		self.assertEqual(
			str(frappe.db.get_value("Annual Plan Version", version, "activated_at")),
			seed.CLOCK["publication_acknowledged"],
		)
		publication = frappe.db.get_value(
			"Annual Plan Publication", {"plan_version": version},
			["attempted_at", "acknowledged_at", "result"], as_dict=True,
		)
		self.assertEqual(publication.result, "Acknowledged")
		self.assertEqual(str(publication.attempted_at), seed.CLOCK["publication_attempted"])
		self.assertEqual(str(publication.acknowledged_at), seed.CLOCK["publication_acknowledged"])
		ao = frappe.db.get_value(
			"Plan Governance Decision",
			{"plan_version": version, "stage": "Accounting Officer adoption"},
			"decided_at",
		)
		self.assertEqual(str(ao), seed.CLOCK["ao_adopted"])

	def test_the_auditor_reads_the_plan_but_is_offered_no_command(self):
		"""Found live by this phase's persona browser pass (the NDS-807
		class): the read-only Planning Auditor was offered "Prepare plan
		update" and the whole Draft edit surface. The offer layer now
		matches the command layer per actor."""
		from kentender_procurement.procurement_planning.services import plan_read

		as_auditor = plan_read.get_annual_plan(
			plan_reference="PLN-MOH-2027-001", user=seed.AUDITOR
		)
		self.assertIsNotNone(as_auditor["active_view"])
		self.assertFalse(as_auditor["can_act"])
		self.assertFalse(as_auditor["mutable"])
		as_planner = plan_read.get_annual_plan(
			plan_reference="PLN-MOH-2027-001", user=seed.PLANNER
		)
		self.assertTrue(as_planner["can_act"])
		item_id = as_planner["active_view"]["items"][0]["plan_item_id"]
		self.assertFalse(
			plan_read.get_plan_item(plan_item_id=item_id, user=seed.AUDITOR)["mutable"]
		)

	def test_rerun_is_idempotent_and_creates_nothing_new(self):
		before = {
			doctype: frappe.db.count(doctype, {"fixture_namespace": seed.NS})
			for doctype in ("Annual Plan", "Annual Plan Version", "Annual Plan Item",
			                "Plan Source Allocation", "Plan Reservation Reference",
			                "Annual Plan Publication", "Departmental Plan Entry")
		}
		rerun = seed.upsert_planning_base(commit=False)
		self.assertTrue(rerun["idempotent"])
		after = {
			doctype: frappe.db.count(doctype, {"fixture_namespace": seed.NS})
			for doctype in before
		}
		self.assertEqual(before, after)


class TestIsolatedProfiles(SeedCase):
	def test_kebs_fails_loudly_naming_the_missing_authoritative_fixtures(self):
		with self.assertRaises(frappe.ValidationError) as caught:
			seed.seed_kebs_profiles()
		self.assertIn("KEBS Budget Line", str(caught.exception))
		self.assertIn("never invent", str(caught.exception))

	def test_the_direct_profile_builds_the_exact_mixed_draft_dpp(self):
		result = seed.seed_direct_profile(commit=False)
		self.assertEqual(result["profile"], "direct")
		root = frappe.get_doc("Departmental Plan", result["departmental_plan"])
		self.assertEqual(root.current_state, "Draft")
		self.assertEqual(root.organisation_unit, seed.OU_DHI)
		entries = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": root.current_version},
			fields=["source_origin", "title", "quantity", "unit", "indicative_amount"],
		)
		origins = {e.source_origin for e in entries}
		self.assertEqual(
			origins, {"Accepted Departmental Need", "Direct departmental requirement"}
		)
		direct = next(e for e in entries if e.source_origin == "Direct departmental requirement")
		self.assertEqual(direct.title, seed.DIRECT_FIXTURE["title"])
		self.assertEqual(direct.quantity, 1)
		self.assertEqual(direct.unit, "UNIT-SERVICE")
		self.assertEqual(direct.indicative_amount, 20000000)
		# not loaded into any Plan
		self.assertEqual(frappe.db.count("Annual Plan", {"procuring_entity": seed.PE}), 0)

	def test_the_combined_profile_forms_the_500_each_120m_item(self):
		result = seed.seed_combined_profile(commit=False)
		item_name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": result["plan_item"]})
		allocations = frappe.get_all(
			"Plan Source Allocation", filters={"plan_item": item_name},
			fields=["quantity", "indicative_amount", "organisation_unit"],
		)
		self.assertEqual(len(allocations), 2)
		self.assertEqual(sum(a.quantity for a in allocations), 500)
		self.assertEqual(sum(a.indicative_amount for a in allocations), 120000000)
		self.assertEqual(
			{a.organisation_unit for a in allocations}, {seed.OU_DHI, seed.OU_HRMD}
		)
		item = frappe.get_doc("Annual Plan Item", item_name)
		self.assertEqual(item.title, seed.COMBINED_ITEM_VALUES["title"])
		self.assertEqual(item.aggregation_reason, seed.COMBINED_ITEM_VALUES["aggregation_reason"])
		self.assertEqual(item.finance_state, "Not requested")

	def test_a_profile_resets_back_to_a_rebuildable_baseline(self):
		seed.seed_return_profile(commit=False)
		self.assertTrue(
			frappe.db.exists("Annual Plan Version", {"version_status": "Returned"})
		)
		seed.reset_planning_seed()
		rebuilt = seed.upsert_planning_base(commit=False)
		self.assertFalse(rebuilt["idempotent"])
		self.assertEqual(rebuilt["publication_result"], "Acknowledged")
		for row in seed.validate_planning_seed():
			self.assertTrue(row["ok"], f"{row['check']}: {row.get('detail')}")
