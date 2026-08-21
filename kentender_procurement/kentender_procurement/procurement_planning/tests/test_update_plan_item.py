# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-005 / PLN-AC-004 / PLN-AC-012 / PLN-AC-016."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import VERSION_IN_REVIEW
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
	get_plan_item_editor,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item as _update_plan_item,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
from frappe.utils import add_days, cstr

from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
	confirm_included_items_funding,
	create_plan_as_planner,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


def update_plan_item(**kwargs):
	"""Direct-test adapter for the approved editor concurrency/idempotency contract."""
	item = kwargs["plan_item"]
	plan = frappe.db.get_value("Procurement Plan Item", item, "plan")
	focus = frappe.db.get_value("Procurement Plan", plan, "open_draft_version") or frappe.db.get_value("Procurement Plan", plan, "current_approved_version")
	kwargs.setdefault("expected_version_token", frappe.db.get_value("Procurement Plan Version", focus, "concurrency_token"))
	kwargs.setdefault("idempotency_key", f"TEST-UI06-{uuid.uuid4().hex}")
	return _update_plan_item(**kwargs)


def _unique_fy() -> str:
	n = int(uuid.uuid4().hex[:5], 16) % 800 + 100
	y = 2600 + n
	return f"{y}/{str(y + 1)[-2:]}"


def _purge_pe_fy(financial_year: str) -> None:
	scope = ensure_scope()
	pe = scope["pe"]
	for name in frappe.get_all(
		"Procurement Plan",
		filters={"procuring_entity": pe, "financial_year": financial_year},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
	fy_token = financial_year.replace("/", "-")
	for name in frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ("like", f"PLN-%{fy_token}%")},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan Version", name, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestUpdatePlanItem(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def _item(self):
		planner = ensure_planner_user()
		fy = _unique_fy()
		_purge_pe_fy(fy)
		plan = create_plan_as_planner(title="Update item plan", financial_year=fy)
		d = make_approved_demand(title="Editor demand")
		added = add_demand_to_plan(plan=plan["plan"], demand=d["demand"], user=planner)
		return planner, added["plan_item"]

	def test_saves_method_schedule_and_lotting(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"requirement_description": "Upgrade national DHI stack",
				"procurement_category": "Goods",
				"procurement_method": "Open tender",
				"arrangement": "Single year",
				"lotting_decision": "Multiple lots",
				"expected_lot_count": 2,
				"lot_basis": "Split by region for delivery capacity",
				"ms_invitation_published": "2027-09-15",
				"ms_tender_opening": "2027-10-20",
				"ms_evaluation_completed": "2027-11-15",
				"ms_award_approval": "2027-12-15",
				"ms_notification_of_award": "2027-12-20",
				"ms_contract_signature": "2028-01-15",
				"ms_delivery_completion": "2028-03-31",
			},
		)
		self.assertTrue(result["ok"], result)

	@patch(
		"kentender_procurement.procurement_planning.services.update_plan_item.resolve_procurement_methods",
		return_value={
			"methods": ["Open tender", "Restricted tender"], "recommended": "Open tender",
			"source": "catalogue", "degraded": False,
			"recommendation_reason_code": "PROCUREMENT_METHOD_CONFIGURED_DEFAULT",
		},
	)
	def test_catalogue_configured_method_is_persisted(self, _resolver) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item, user=planner,
			fields={"procurement_method": "Restricted tender"},
		)
		self.assertTrue(result["ok"], result)
		iv = frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		self.assertEqual(frappe.db.get_value("Procurement Plan Item Version", iv, "procurement_method"), "Restricted tender")

	@patch(
		"kentender_procurement.procurement_planning.services.update_plan_item.resolve_procurement_methods",
		return_value={"methods": ["Open tender"], "recommended": "Open tender", "source": "fallback", "degraded": True, "recommendation_reason_code": "PROCUREMENT_METHOD_FALLBACK_OPEN_TENDER"},
	)
	def test_method_outside_resolved_catalogue_is_rejected(self, _resolver) -> None:
		planner, item = self._item()
		result = update_plan_item(plan_item=item, user=planner, fields={"procurement_method": "Direct procurement"})
		self.assertFalse(result["ok"], result)
		self.assertEqual(result["error_code"], "PROCUREMENT_METHOD_NOT_CONFIGURED")

	def test_strategy_and_pvc_writes_rejected_by_editor(self) -> None:
		"""PLN-AC-018 — Planning cannot author strategy / PVC / treatment notes."""
		planner, item = self._item()
		iv = frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		before = frappe.db.get_value(
			"Procurement Plan Item Version",
			iv,
			["strategy_snapshot", "pvc_snapshot"],
			as_dict=True,
		)
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"strategy_snapshot": "Planning-authored treatment — must not persist",
				"pvc_snapshot": "Planning-authored PVC — must not persist",
				"value_treatment_note": "Planning treatment note — must not persist",
			},
		)
		self.assertFalse(result["ok"], result)
		self.assertEqual(result.get("error_code"), "PLN_ITEM_FIELDS_NOT_PERMITTED")
		after = frappe.db.get_value(
			"Procurement Plan Item Version",
			iv,
			["strategy_snapshot", "pvc_snapshot"],
			as_dict=True,
		)
		self.assertEqual(after.strategy_snapshot, before.strategy_snapshot)
		self.assertEqual(after.pvc_snapshot, before.pvc_snapshot)
		self.assertNotEqual(
			cstr(after.strategy_snapshot or ""),
			"Planning-authored treatment — must not persist",
		)

	def test_approved_version_rejects_update_plan_item(self) -> None:
		"""PLN-AC-011 — Approved Version / item snapshots are immutable via update_plan_item."""
		from kentender_procurement.procurement_planning.tests._gate01_helpers import (
			approve_plan_via_gate05,
			ensure_approver_user,
		)

		planner, item = self._item()
		complete_plan_item_for_signoff(plan_item=item, user=planner)
		plan = frappe.db.get_value("Procurement Plan Item", item, "plan")
		version = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
		approve_plan_via_gate05(
			plan=plan, version=version, user=ensure_approver_user()
		)
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": item, "plan_version": version},
			"name",
		)
		before = frappe.db.get_value(
			"Procurement Plan Item Version", iv, "requirement_description"
		)
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"requirement_description": "tamper approved item"},
		)
		self.assertFalse(result.get("ok"), result)
		self.assertIn("form", result.get("errors") or {})
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "requirement_description"),
			before,
		)

	def test_preference_writes_rejected_from_editor(self) -> None:
		"""C02: preference keys no longer mutate Plan Item Version via update_plan_item."""
		planner, item = self._item()
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		before = get_plan_item_editor(plan_item=item, user=planner)
		self.assertNotIn("preference_reservation", before)
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"preference_reservation_scheme": "AGPO reservation",
				"reservation_scope": "Reserved lot(s)",
				"eligible_groups": ["Women-owned enterprises"],
				"planned_reserved_value": 9999,
			},
		)
		self.assertFalse(result["ok"], result)
		self.assertEqual(result.get("error_code"), "PLN_ITEM_FIELDS_NOT_PERMITTED")
		after = get_plan_item_editor(plan_item=item, user=planner)
		self.assertNotIn("preference_reservation", after)

	def test_retired_statutory_fields_absent_from_meta(self) -> None:
		meta = frappe.get_meta("Procurement Plan Item Version")
		for fieldname in (
			"statutory_treatment",
			"statutory_target_groups",
			"planned_treatment_value",
			"value_treatment_note",
		):
			self.assertIsNone(meta.get_field(fieldname), fieldname)

	def test_alternative_method_is_not_configured(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"procurement_method": "Uncatalogued method test sentinel"},
		)
		self.assertFalse(result["ok"], result)
		self.assertEqual(result.get("error_code"), "PROCUREMENT_METHOD_NOT_CONFIGURED")

	def test_multi_year_requires_justification_fields(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"arrangement": "Multi-year"},
		)
		self.assertTrue(result["ok"], result)
		self.assertIn("multi_year_justification", result["field_issues"])
		self.assertIn("annual_funding_schedule", result["field_issues"])

	def test_hod_owned_facts_rejected(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"owner_org_unit": "MOH-DIR-HR", "confirmed_estimate": 1},
		)
		self.assertFalse(result.get("ok"))
		self.assertIn("errors", result)
		msg = " ".join(str(v) for v in (result.get("errors") or {}).values())
		self.assertIn("cannot be changed here", msg.lower())
		self.assertIn("Demand", msg)

	def test_request_finance_incomplete_stays_with_attention(self) -> None:
		planner, item = self._item()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"requirement_description": "Partial"},
			request_finance=True,
		)
		self.assertTrue(result["ok"], result)
		self.assertFalse(result.get("complete"))
		self.assertIn("seven-date schedule", result.get("attention_message") or "")

	def test_out_of_order_milestones_save_with_field_issues(self) -> None:
		planner, item = self._item()
		plan = frappe.db.get_value("Procurement Plan Item", item, "plan")
		period_start = frappe.db.get_value("Procurement Plan", plan, "period_start")
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"ms_invitation_published": add_days(period_start, 10),
				"ms_tender_opening": add_days(period_start, 30),
				"ms_evaluation_completed": add_days(period_start, 20),
				"ms_award_approval": add_days(period_start, 35),
				"ms_notification_of_award": add_days(period_start, 37),
				"ms_contract_signature": add_days(period_start, 42),
				"ms_delivery_completion": add_days(period_start, 90),
			},
		)
		self.assertTrue(result["ok"], result)
		self.assertIn("ms_evaluation_completed", result["field_issues"])
		self.assertIn("chronolog", result["field_issues"]["ms_evaluation_completed"].lower())
		iv = frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		saved = frappe.db.get_value(
			"Procurement Plan Item Version",
			iv,
			"ms_evaluation_completed",
		)
		self.assertEqual(str(saved), str(add_days(period_start, 20)))
		from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
			get_plan_item_editor,
		)

		proj = get_plan_item_editor(plan_item=item, user=planner)
		self.assertIn("ms_evaluation_completed", proj["field_issues"])
		self.assertIn("chronolog", proj["attention_message"].lower())

	def test_in_review_version_rejects_save_and_editor_is_read_only(self) -> None:
		"""In review successor must not look editable or swallow Save as a no-op."""
		planner, item = self._item()
		complete_plan_item_for_signoff(plan_item=item, user=planner)
		plan = frappe.db.get_value("Procurement Plan Item", item, "plan")
		confirm_included_items_funding(plan=plan, planner=planner)
		validate_plan(plan=plan, user=planner)
		draft = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
		submitted = submit_plan_for_review(
			plan=plan,
			expected_token=frappe.db.get_value("Procurement Plan Version", draft, "concurrency_token"),
			idempotency_key=f"TEST-UI06-SUBMIT-{draft}",
			user=planner,
		)
		self.assertTrue(submitted.get("ok"), submitted)
		self.assertEqual(
			frappe.db.get_value(
				"Procurement Plan Version",
				frappe.db.get_value("Procurement Plan", plan, "open_draft_version"),
				"status",
			),
			VERSION_IN_REVIEW,
		)
		iv = frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		before = frappe.db.get_value(
			"Procurement Plan Item Version", iv, "requirement_description"
		)
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={"requirement_description": "should not persist while in review"},
		)
		self.assertFalse(result.get("ok"), result)
		self.assertIn("form", result.get("errors") or {})
		self.assertIn("Draft or Returned", result["errors"]["form"])
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "requirement_description"),
			before,
		)
		dto = get_plan_item_editor(plan_item=item, user=planner)
		self.assertFalse(dto["can_edit"])
		self.assertIn("In review", dto.get("attention_message") or "")
		self.assertIn("In review", dto.get("version_label") or "")

	def test_missing_draft_item_version_pointer_still_saves(self) -> None:
		planner, item = self._item()
		frappe.db.set_value(
			"Procurement Plan Item", item, "draft_item_version", None, update_modified=False
		)
		frappe.db.commit()
		result = update_plan_item(
			plan_item=item,
			user=planner,
			fields={
				"requirement_description": "Saved without draft pointer",
				"procurement_category": "Goods",
			},
		)
		self.assertTrue(result["ok"], result)
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{
				"plan_item": item,
				"plan_version": frappe.db.get_value(
					"Procurement Plan",
					frappe.db.get_value("Procurement Plan Item", item, "plan"),
					"open_draft_version",
				),
			},
			"name",
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Item Version", iv, "requirement_description"),
			"Saved without draft pointer",
		)
