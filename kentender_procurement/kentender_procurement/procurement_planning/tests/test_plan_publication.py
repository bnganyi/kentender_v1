# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§7.1/§8.2 Publication, Active and successor tests
(Phase 9, Slice G): PublishAnnualPlan (a system action run automatically
inside ApproveAnnualPlan)/RetryPublication, BeginPlanUpdate/
RemovePlanItemInSuccessor/CancelPlanUpdate, and the NeedPlanningUsageChanged.v1
publisher proved against a genuine accepted Need rather than a fabricated
payload — the actual outbound half of the §7.1 Needs handoff."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_publication,
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


class PublicationCase(IntegrationTestCase):
	"""Shared world and builders. `MOCK_NEEDS = False` (only
	`TestNeedOriginUsagePublishing` sets it) lets a real accepted Need
	through instead of the usual empty-source stub every other Planning
	test module uses."""

	MOCK_NEEDS = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		if self.MOCK_NEEDS:
			needs_patch = patch.object(needs_intake, "current_accepted_sources", return_value=[])
			needs_patch.start()
			self.addCleanup(needs_patch.stop)
		eligible_patch = patch.object(
			budget_gateway, "eligible_line_ids", return_value={fx.BUDGET_LINE, fx.BUDGET_LINE_2}
		)
		eligible_patch.start()
		self.addCleanup(eligible_patch.stop)

	# -- shared builders (mirroring GovernanceCase.confirmed_item) -------

	def item_values(self, **overrides) -> dict:
		values = {
			"title": "Direct requirement", "description": "Assess and remediate the direct requirement.",
			"strategic_objective": fx.STRATEGY_OBJECTIVE, "aggregation_reason": "",
			"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
			"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
			"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
			"delivery_completion_date": "2098-10-15",
		}
		values.update(overrides)
		return values

	def complete_and_confirm(self, item_id: str) -> None:
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values=self.item_values(),
			expected_record_version=item["record_version"], idempotency_key=key(),
		)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		requested = plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Plan Finance Task", requested["task"])
		frappe.set_user(fx.BUDGET_OFFICER)
		read = plan_read.get_finance_task(task=task.name)
		plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token, check_token=read["budget_check_token"],
			idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)

	def confirmed_item(self, *, indicative_amount: float = 1000000) -> tuple[dict, str]:
		"""One accepted direct entry, formed, completed and Finance-Confirmed
		— ready for SubmitConsolidatedPlan."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(indicative_amount=indicative_amount),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={added["entry_id"]: "Goods"},
			task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"],
			dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete_and_confirm(item_id)
		return accepted, item_id

	def two_confirmed_items(self) -> tuple[dict, str, str]:
		"""Two accepted direct entries in one DPP, each formed into its own
		item on a different Budget Line, both Finance-Confirmed. Returns
		(acceptance result, item A id, item B id)."""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=fx.OU_ALPHA,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added_a = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Item A requirement", budget_line=fx.BUDGET_LINE),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		added_b = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values=fx.direct_values(title="Item B requirement", budget_line=fx.BUDGET_LINE_2),
			expected_record_version=added_a["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added_b["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name,
			classifications={added_a["entry_id"]: "Goods", added_b["entry_id"]: "Goods"},
			task_token=task.task_token, idempotency_key=key(),
		)
		entry_a = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "entry_id": added_a["entry_id"]}, "name",
		)
		entry_b = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "entry_id": added_b["entry_id"]}, "name",
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[entry_a, entry_b],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		items_by_title = {}
		for item_id in formed["created_items"]:
			read = plan_read.get_plan_item(plan_item_id=item_id)
			items_by_title[read["header"]["title"]] = item_id
		item_a_id = items_by_title["Item A requirement"]
		item_b_id = items_by_title["Item B requirement"]
		self.complete_and_confirm(item_a_id)
		self.complete_and_confirm(item_b_id)
		return accepted, item_a_id, item_b_id

	def submit(self, plan_reference: str):
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		return plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"],
			idempotency_key=key(),
		)

	def activate(self, plan_reference: str) -> dict:
		"""Drive the Draft/open Version through the whole governance chain to
		Active (§5.2) — publication runs automatically inside approval."""
		submitted = self.submit(plan_reference)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		adopted = plan_governance.adopt_and_submit_plan(
			task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key(),
		)
		statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
		frappe.set_user(fx.STATUTORY)
		result = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key(),
		)
		# every caller continues as the Planner — none needs the Statutory
		# Approver's own narrower scope for what comes next.
		frappe.set_user(fx.PLANNER)
		return result


class TestActivationAndRetryPublication(PublicationCase):
	def test_approval_activates_the_plan_and_the_active_view_reflects_it(self):
		accepted, item_id = self.confirmed_item()
		approved = self.activate(accepted["annual_plan"])
		self.assertEqual(approved["publication_result"], "Acknowledged")

		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertIsNotNone(read["active_view"])
		self.assertEqual(read["header"]["badge"], "Active")
		self.assertFalse(read["mutable"])
		self.assertFalse(read["has_open_successor"])
		self.assertEqual(read["active_view"]["summary"]["plan_items"], 1)
		row = read["active_view"]["items"][0]
		self.assertEqual(row["plan_item_id"], item_id)
		self.assertEqual(row["route"], ["procurement-plan-item", item_id])
		self.assertIn("Acknowledged", read["active_view"]["governance_card"]["publication_line"])

		publication = frappe.get_doc(
			"Annual Plan Publication", {"plan_version": read["version_reference"]}
		)
		self.assertEqual(publication.attempt_number, 1)
		self.assertEqual(publication.result, "Acknowledged")
		self.assertTrue(publication.external_reference)

	def test_a_failed_attempt_is_recovered_by_a_system_manager_retry(self):
		accepted, item_id = self.confirmed_item()
		with patch.object(plan_publication, "_transmit", return_value=("Failed", "")):
			approved = self.activate(accepted["annual_plan"])
		self.assertEqual(approved["publication_result"], "Failed")

		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		self.assertFalse(frappe.db.get_value("Annual Plan", plan_name, "active_version"))
		failed_version = frappe.db.get_value("Annual Plan Version", {"annual_plan": plan_name}, "name")
		self.assertEqual(
			frappe.db.get_value("Annual Plan Version", failed_version, "version_status"),
			"Publication failed",
		)
		publication = frappe.get_doc("Annual Plan Publication", {"plan_version": failed_version})
		self.assertEqual(publication.result, "Failed")
		self.assertFalse(publication.external_reference)

		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_publication.retry_publication(publication=publication.name, idempotency_key=key())

		frappe.set_user("Administrator")
		retry_key = key()
		retried = plan_publication.retry_publication(publication=publication.name, idempotency_key=retry_key)
		self.assertEqual(retried["result"], "Acknowledged")
		# §8.2/§12.11 — the retry itself is idempotent: the same key replays
		# the recorded result instead of attempting again (found live: the
		# missing replay guard crashed on the key's second presentation).
		replayed = plan_publication.retry_publication(publication=publication.name, idempotency_key=retry_key)
		self.assertTrue(replayed["idempotent"])
		self.assertEqual(replayed["publication"], retried["publication"])
		self.assertEqual(
			frappe.db.get_value("Annual Plan Version", failed_version, "version_status"), "Active"
		)
		self.assertEqual(
			frappe.db.get_value("Annual Plan", plan_name, "active_version"), failed_version
		)
		self.assertEqual(frappe.db.count("Annual Plan Publication", {"plan_version": failed_version}), 2)


class TestBeginAndCancelPlanUpdate(PublicationCase):
	def test_begin_plan_update_creates_a_draft_successor_copying_the_item_and_is_idempotent(self):
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		active_version = frappe.db.get_value("Annual Plan", plan_name, "active_version")

		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(
			plan_reference=accepted["annual_plan"], idempotency_key=key(),
		)
		self.assertEqual(begun["action"], "created")
		successor = begun["successor_version"]
		self.assertEqual(
			frappe.db.get_value("Annual Plan Version", successor, "based_on_version"), active_version
		)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "version_status"), "Draft")
		self.assertEqual(
			frappe.db.get_value("Annual Plan", plan_name, "open_successor_version"), successor
		)

		# the copied item carries the exact same business id, in its own doc
		copies = frappe.get_all(
			"Annual Plan Item", filters={"plan_item_id": item_id},
			fields=["name", "plan_version", "item_state"],
		)
		self.assertEqual(len(copies), 2)
		by_version = {c.plan_version: c.item_state for c in copies}
		self.assertEqual(by_version[active_version], "Active")
		self.assertEqual(by_version[successor], "Draft")

		# the workbench read now shows the mutable successor, not the Active view
		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertTrue(read["mutable"])
		self.assertIsNone(read["active_view"])

		# the id resolves to the successor's OWN (Draft) copy, not its Active
		# twin — the regression this phase's fix to resolve_item_doc_name
		# guards: before it, a bare plan_item_id lookup could return either
		# doc once two versions legitimately share the same business id.
		item_read = plan_read.get_plan_item(plan_item_id=item_id)
		self.assertEqual(item_read["plan_item_id"], item_id)
		self.assertTrue(item_read["mutable"])
		self.assertEqual(
			frappe.db.get_value(
				"Annual Plan Item", plan_read.resolve_item_doc_name(item_id), "plan_version"
			),
			successor,
		)

		# idempotent reuse: same plan_reference, a fresh key, no second successor
		again = plan_publication.begin_plan_update(
			plan_reference=accepted["annual_plan"], idempotency_key=key(),
		)
		self.assertEqual(again["action"], "reused")
		self.assertEqual(again["successor_version"], successor)
		self.assertEqual(frappe.db.count("Annual Plan Version", {"annual_plan": plan_name}), 2)

	def test_cancel_plan_update_leaves_a_shared_reservation_untouched_and_reopens_cleanly(self):
		accepted, item_id = self.confirmed_item()
		self.activate(accepted["annual_plan"])
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		predecessor_item = frappe.db.get_value(
			"Annual Plan Item", {"plan_item_id": item_id, "item_state": "Active"}, "name"
		)
		predecessor_ref = frappe.get_doc("Plan Reservation Reference", {"plan_item": predecessor_item})
		self.assertFalse(predecessor_ref.release_reference)

		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(
			plan_reference=accepted["annual_plan"], idempotency_key=key(),
		)
		successor = begun["successor_version"]
		open_read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])

		cancelled = plan_publication.cancel_plan_update(
			plan_reference=accepted["annual_plan"],
			expected_record_version=open_read["record_version"], idempotency_key=key(),
		)
		self.assertEqual(cancelled["action"], "cancelled")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "version_status"), "Cancelled")
		self.assertFalse(frappe.db.get_value("Annual Plan", plan_name, "open_successor_version"))

		# the Active predecessor's own reference to the shared reservation
		# still stands — §5.3 invariant 21 never releases what the Active
		# Version still relies on.
		predecessor_ref.reload()
		self.assertFalse(predecessor_ref.release_reference)
		self.assertEqual(
			frappe.db.get_value("Annual Plan Item", predecessor_item, "item_state"), "Active"
		)

		# a fresh update can be prepared right away
		reopened = plan_publication.begin_plan_update(
			plan_reference=accepted["annual_plan"], idempotency_key=key(),
		)
		self.assertEqual(reopened["action"], "created")
		self.assertNotEqual(reopened["successor_version"], successor)


class TestRemoveItemInSuccessorAndReActivation(PublicationCase):
	def test_removal_supersedes_the_predecessor_item_and_releases_its_reservation_on_activation(self):
		accepted, item_a_id, item_b_id = self.two_confirmed_items()
		self.activate(accepted["annual_plan"])
		plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": accepted["annual_plan"]})
		predecessor_version = frappe.db.get_value("Annual Plan", plan_name, "active_version")
		predecessor_item_a = frappe.db.get_value(
			"Annual Plan Item", {"plan_item_id": item_a_id, "plan_version": predecessor_version}, "name"
		)
		predecessor_ref_a = frappe.get_doc("Plan Reservation Reference", {"plan_item": predecessor_item_a})
		self.assertFalse(predecessor_ref_a.release_reference)

		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(
			plan_reference=accepted["annual_plan"], idempotency_key=key(),
		)
		successor = begun["successor_version"]

		item_a_read = plan_read.get_plan_item(plan_item_id=item_a_id)
		self.assertTrue(item_a_read["mutable"])
		removed = plan_publication.remove_plan_item_in_successor(
			plan_item=item_a_id, expected_record_version=item_a_read["record_version"],
			idempotency_key=key(),
		)
		self.assertEqual(removed["action"], "removed")
		successor_item_a = frappe.db.get_value(
			"Annual Plan Item", {"plan_item_id": item_a_id, "plan_version": successor}, "name"
		)
		self.assertEqual(
			frappe.db.get_value("Annual Plan Item", successor_item_a, "item_state"),
			"Removed in successor",
		)
		# removal only marks the item; the predecessor's copy is never touched
		# in place — supersession happens once, on activation.
		self.assertEqual(
			frappe.db.get_value("Annual Plan Item", predecessor_item_a, "item_state"), "Active"
		)

		self.activate(accepted["annual_plan"])

		self.assertEqual(
			frappe.db.get_value("Annual Plan Item", predecessor_item_a, "item_state"), "Superseded"
		)
		# the successor's OWN copy of the allocation — the one whose item is
		# actually "Removed in successor" — is what gets relabelled; the
		# predecessor's now-Superseded item's allocation is left as it was,
		# since the item state already carries its fate.
		self.assertEqual(
			frappe.db.get_value(
				"Plan Source Allocation", {"plan_item": successor_item_a}, "allocation_state"
			),
			"Removed in successor",
		)
		predecessor_ref_a.reload()
		self.assertTrue(predecessor_ref_a.release_reference)
		self.assertEqual(predecessor_ref_a.release_correlation, f"activate:{successor}")

		self.assertEqual(
			frappe.db.get_value("Annual Plan Version", predecessor_version, "version_status"), "Superseded"
		)
		self.assertEqual(frappe.db.get_value("Annual Plan Version", successor, "version_status"), "Active")
		self.assertEqual(frappe.db.get_value("Annual Plan", plan_name, "active_version"), successor)

		read = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		self.assertEqual(read["active_view"]["summary"]["plan_items"], 1)
		self.assertEqual(read["active_view"]["items"][0]["plan_item_id"], item_b_id)


class TestNeedOriginUsagePublishing(PublicationCase):
	"""§7.1's outbound event, proved against a genuine accepted Need created
	through NDS's own real command chain (create_need/submit_need/
	review_need) — not a fabricated payload — so both the Need-origin DPP
	intake (Phase 2's read side) and this phase's new publisher round-trip
	for real."""

	MOCK_NEEDS = False
	NEED_OU = "OU-PLNT-NEEDFX"

	def setUp(self):
		super().setUp()
		self._ensure_need_fixture()
		self._wipe_need_fixture()

	def _ensure_need_fixture(self) -> None:
		ou_type = frappe.db.get_value("Organisation Unit", fx.OU_ALPHA, "unit_type")
		if not frappe.db.exists("Organisation Unit", self.NEED_OU):
			frappe.get_doc(
				{
					"doctype": "Organisation Unit", "unit_code": self.NEED_OU,
					"unit_name": "Need Fixture Department", "unit_type": ou_type,
					"procuring_entity": fx.PE, "status": "Active", "fixture_namespace": fx.NS,
				}
			).insert(ignore_permissions=True)
		for email in (fx.AUTHOR, fx.HOD):
			for allow, value in (("Organisation Unit", self.NEED_OU), ("Financial Year", fx.FY_OPEN)):
				if not frappe.db.exists("User Permission", {"user": email, "allow": allow, "for_value": value}):
					frappe.get_doc(
						{"doctype": "User Permission", "user": email, "allow": allow, "for_value": value}
					).insert(ignore_permissions=True)
		if not frappe.db.exists(
			"Needs Intake Window", {"procuring_entity": fx.PE, "financial_year": fx.FY_OPEN}
		):
			frappe.get_doc(
				{
					"doctype": "Needs Intake Window",
					"needs_intake_window_id": f"NDS-IW-{fx.PE}-{fx.FY_OPEN}",
					"procuring_entity": fx.PE, "financial_year": fx.FY_OPEN,
					"opens_at": "2020-01-01 00:00:00", "closes_at": "2099-01-01 00:00:00",
					"record_version": 1,
				}
			).insert(ignore_permissions=True)

	def _wipe_need_fixture(self) -> None:
		"""Scoped by the dedicated fixture OU, mirroring wipe_planning_rows —
		Needs are real, live-site rows the test runner never rolls back."""
		needs = frappe.get_all("Departmental Need", filters={"organisation_unit": self.NEED_OU}, pluck="name")
		versions = frappe.get_all(
			"Departmental Need Version", filters={"departmental_need": ("in", needs or ("",))}, pluck="name"
		)
		frappe.db.delete("Need Planning Usage Projection", {"name": ("in", versions or ("",))})
		frappe.db.delete("Departmental Need Decision", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Review Task", {"organisation_unit": self.NEED_OU})
		frappe.db.delete("Departmental Need Event", {"departmental_need": ("in", needs or ("",))})
		frappe.db.delete("Departmental Need Version", {"name": ("in", versions or ("",))})
		frappe.db.delete("Departmental Need", {"name": ("in", needs or ("",))})

	def _accepted_need(self, title: str) -> str:
		from kentender_procurement.departmental_needs.services import lifecycle as need_lifecycle

		frappe.set_user(fx.AUTHOR)
		created = need_lifecycle.create_need(
			procuring_entity=fx.PE, organisation_unit=self.NEED_OU, financial_year=fx.FY_OPEN,
			title=title, description="A Phase 9 fixture Need for the usage-publishing round trip.",
			expected_operational_result="Planning can source a real accepted Need end to end.",
			indicative_quantity=5, unit=fx.UNIT, required_by_date="2099-01-01",
			idempotency_key=key(),
		)
		submitted = need_lifecycle.submit_need(
			need=created["need"], expected_version=created["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		token = frappe.db.get_value("Departmental Need Review Task", submitted["task"], "decision_token")
		need_lifecycle.review_need(
			need=created["need"], decision="accept", task=submitted["task"],
			expected_version=submitted["record_version"], decision_token=token, idempotency_key=key(),
		)
		return created["need"]

	def confirmed_need_origin_item(self, need: str, *, indicative_amount: float = 500000) -> tuple[dict, str]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=fx.PE, organisation_unit=self.NEED_OU,
			financial_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS,
		)
		dpp_entry = frappe.db.get_value(
			"Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": need}, "name",
		)
		self.assertTrue(dpp_entry, "the accepted Need was not projected into the Draft DPP Version")
		entry_id = frappe.db.get_value("Departmental Plan Entry", dpp_entry, "entry_id")
		funded = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id,
			budget_line=fx.BUDGET_LINE, indicative_amount=indicative_amount,
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=funded["record_version"], idempotency_key=key(),
		)
		dpp_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
		)
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(
			task=dpp_task.name, classifications={entry_id: "Goods"},
			task_token=dpp_task.task_token, idempotency_key=key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[dpp_entry],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete_and_confirm(item_id)
		return accepted, item_id

	def test_activation_publishes_fully_included_then_removal_publishes_not_included(self):
		need = self._accepted_need("Need-origin fixture requirement")
		accepted_version = frappe.db.get_value("Departmental Need", need, "current_accepted_version")

		accepted, item_id = self.confirmed_need_origin_item(need)
		approved = self.activate(accepted["annual_plan"])
		self.assertEqual(approved["publication_result"], "Acknowledged")

		projection = frappe.db.get_value(
			"Need Planning Usage Projection", accepted_version,
			["usage", "active_plan", "active_plan_item"], as_dict=True,
		)
		self.assertEqual(projection.usage, "Fully included")
		self.assertEqual(projection.active_plan, accepted["annual_plan"])
		self.assertEqual(projection.active_plan_item, item_id)

		from kentender_procurement.departmental_needs.services import usage as needs_usage

		self.assertTrue(needs_usage.is_actively_included(accepted_version))

		# now propose and activate a successor that removes this one item
		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(
			plan_reference=accepted["annual_plan"], idempotency_key=key(),
		)
		item_read = plan_read.get_plan_item(plan_item_id=item_id)
		plan_publication.remove_plan_item_in_successor(
			plan_item=item_id, expected_record_version=item_read["record_version"], idempotency_key=key(),
		)
		self.activate(accepted["annual_plan"])

		projection = frappe.db.get_value(
			"Need Planning Usage Projection", accepted_version,
			["usage", "active_plan", "active_plan_item"], as_dict=True,
		)
		self.assertEqual(projection.usage, "Not included")
		self.assertFalse(projection.active_plan)
		self.assertFalse(needs_usage.is_actively_included(accepted_version))
