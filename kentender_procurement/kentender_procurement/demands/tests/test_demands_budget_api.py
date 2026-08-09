# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-06 Routine Budget confirmation API — projection, confirm, return, adjust."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today

from kentender_procurement.demands.api import (
	_action_for,
	adjust_funding_allocation_form,
	confirm_demand_funding_form,
	enrich_demand_form,
	get_demand_review,
	prepare_budget_confirmation_ui06,
	prepare_budget_exception_multiple_matches_ui07,
	prepare_budget_exception_ui07,
	record_business_decision_form,
	resolve_funding_exception_form,
	return_budget_confirmation_form,
	save_funding_exception_note_form,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	create_or_update_demand,
	enrich_demand,
	submit_demand,
	suggest_funding_allocations,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUDGET,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"


def _ensure_user(email: str, roles: list[str], ns: str = "DEMANDS_UI06_TEST") -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DemBudget",
				"last_name": email.split("@")[0][:20],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	changed = False
	for role in roles:
		if role not in have:
			user.append("roles", {"role": role})
			changed = True
	if changed:
		user.save(ignore_permissions=True)
	for role in roles:
		if not frappe.db.exists(
			"User Scope Assignment",
			{
				"user": email,
				"procuring_entity": PE,
				"organisation_unit": OU,
				"role": role,
			},
		):
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": email,
					"role": role,
					"procuring_entity": PE,
					"organisation_unit": OU,
					"include_descendants": 1,
					"fixture_namespace": ns,
				}
			).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


def _budget_line() -> str:
	name = frappe.db.get_value(
		"Budget Line", {"generated_reference": "MOH-BL-DHI-2027"}, "name"
	)
	if not name:
		name = frappe.db.get_value(
			"Budget Line", {"fixture_namespace": "KENTENDER_MVP_V1"}, "name"
		)
	if not name:
		raise frappe.ValidationError("No Budget Line fixture for DEM-UI-06 tests")
	return name


def _to_budget_confirmation(req: str, ba: str, paa: str, *, estimate: float = 1000) -> str:
	created = create_or_update_demand(
		values={
			"procuring_entity": PE,
			"owner_org_unit": OU,
			"title": "UI06 budget confirmation API demand",
			"need_statement": "Need resilient clinic connectivity",
			"need_rationale": "Service continuity requires upgrades",
			"expected_outcome": "Stable clinic links",
			"beneficiaries": "County clinics",
			"delivery_location": "Nairobi",
			"required_by_date": add_days(today(), 90),
			"demand_route": "Standard",
			"urgency": "Medium",
			"estimate_confidence": "Medium",
			"estimate_basis": "Market scan",
			"currency": "KES",
			"fixture_namespace": "DEMANDS_UI06_TEST",
		},
		items=[
			{
				"description": "Resilient compute capacity",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": estimate,
			}
		],
		user=req,
	)
	name = created["demand"]["name"]
	submit_demand(demand=name, user=req)
	frappe.set_user(ba)
	record_business_decision_form(demand=name, decision="Support", comment="Supported")
	line = _budget_line()
	line_meta = frappe.db.get_value(
		"Budget Line",
		line,
		["primary_target_code", "primary_target_name"],
		as_dict=True,
	) or {}
	t_code = (line_meta.get("primary_target_code") or "T-UI06").strip()
	t_name = (line_meta.get("primary_target_name") or "UI06 Primary Target").strip()
	frappe.set_user(paa)
	enrich_demand(
		demand=name,
		values={
			"confirmed_estimate": estimate,
			"procurement_category": "ICT infrastructure and services",
			"estimate_basis": "Market check",
		},
		strategy_references=[
			{
				"reference_type": "Primary",
				"target_code": t_code,
				"target_name": t_name,
				"snapshot_label": f"{t_name} ({t_code})" if t_code else t_name,
				"hierarchy_path": "Outcome > Target",
				"selection_source": "Manual",
				"confirmation_reason": "Best fit",
			}
		],
		value_treatments=[],
		send_for_budget=True,
		user=paa,
	)
	suggestion = suggest_funding_allocations(demand=name, budget_line=line, user=paa)
	if suggestion.get("exception_type") == "Insufficient Funding":
		raise frappe.ValidationError(
			"Budget line insufficient for DEM-UI-06 test estimate; use a smaller amount"
		)
	# Clear Multiple Matches noise when a Pending allocation exists.
	for exc in frappe.get_all(
		"Funding Exception",
		filters={"demand": name, "status": ["in", ["Open", "In Progress"]]},
		pluck="name",
	):
		frappe.db.set_value("Funding Exception", exc, "status", "Resolved")
	return name


class TestDemandsBudgetApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()
		if not frappe.db.exists("Procuring Entity", PE):
			raise frappe.ValidationError("PE-MOH required for DEM-UI-06 API tests")
		if not frappe.db.exists("Organisation Unit", OU):
			raise frappe.ValidationError("MOH-DIR-DHP required for DEM-UI-06 API tests")

	def test_funding_projection_after_send(self) -> None:
		req = _ensure_user("dem-budget-req@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		bo = _ensure_user("dem-budget-bo@example.com", [ROLE_BUDGET])
		name = _to_budget_confirmation(req, ba, paa, estimate=1000)

		frappe.set_user(bo)
		loaded = get_demand_review(demand=name)
		self.assertTrue(loaded["ok"])
		self.assertEqual(loaded["stage"], "Budget Confirmation")
		self.assertTrue(loaded["can_confirm_funding"])
		self.assertFalse(loaded["can_decide"])
		self.assertFalse(loaded["can_enrich"])
		self.assertIn("Confirm funding", loaded["allowed_actions"])
		self.assertIn("Return", loaded["allowed_actions"])
		self.assertIn("Adjust", loaded["allowed_actions"])
		funding = loaded["funding"]
		self.assertIsNotNone(funding)
		self.assertAlmostEqual(flt(funding["estimate"]), 1000)
		self.assertAlmostEqual(flt(funding["proposed_total"]), 1000)
		self.assertAlmostEqual(flt(funding["difference"]), 0)
		self.assertIn("KES", funding["estimate_display"])
		self.assertIn("1,000", funding["estimate_display"])
		self.assertTrue(funding["confirm_ready"])
		self.assertIn("does not reserve", (funding["no_reserve_disclaimer"] or "").lower())
		rec = funding["recommendation"]
		self.assertIsNotNone(rec)
		self.assertTrue(rec["budget_display"])
		self.assertTrue(rec["budget_line_display"])
		self.assertNotEqual(rec["budget_display"], rec["budget"])
		self.assertNotEqual(rec["budget_line_display"], rec["budget_line"])
		self.assertNotIn(rec["budget"], rec["budget_display"])
		self.assertNotIn(rec["budget_line"], rec["budget_line_display"])
		stages = {s["key"]: s["state"] for s in loaded["stage_indicator"]}
		self.assertEqual(stages["Budget Confirmation"], "Current")

	def test_bo_confirm_moves_to_final_approval_without_reservation(self) -> None:
		req = _ensure_user("dem-budget-req2@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		bo = _ensure_user("dem-budget-bo@example.com", [ROLE_BUDGET])
		name = _to_budget_confirmation(req, ba, paa, estimate=1000)
		code = frappe.db.get_value("Demand", name, "demand_code")

		frappe.set_user(bo)
		confirmed = confirm_demand_funding_form(demand=name)
		self.assertTrue(confirmed["ok"])
		self.assertEqual(confirmed["stage"], "Final Approval")
		self.assertEqual(confirmed["demand"]["current_stage"], "Final Approval")
		# No reservation side-effect at BO confirm.
		alloc_rsv = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": name},
			fields=["funding_reservation", "bo_confirmation_status"],
		)
		self.assertTrue(alloc_rsv)
		self.assertTrue(
			all((a.bo_confirmation_status or "") == "Confirmed" for a in alloc_rsv)
		)
		self.assertTrue(all(not a.funding_reservation for a in alloc_rsv))
		rsv = frappe.get_all(
			"Funding Reservation",
			filters={"demand_code": code},
			pluck="name",
		)
		self.assertEqual(rsv, [])

	def test_non_bo_cannot_confirm(self) -> None:
		req = _ensure_user("dem-budget-req3@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		name = _to_budget_confirmation(req, ba, paa, estimate=1000)
		frappe.set_user(paa)
		with self.assertRaises(Exception):
			confirm_demand_funding_form(demand=name)

	def test_confirm_blocked_when_totals_mismatch(self) -> None:
		req = _ensure_user("dem-budget-req4@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		bo = _ensure_user("dem-budget-bo@example.com", [ROLE_BUDGET])
		name = _to_budget_confirmation(req, ba, paa, estimate=1000)

		frappe.set_user(bo)
		adjusted = adjust_funding_allocation_form(
			demand=name, allocation_amount=900
		)
		self.assertTrue(adjusted["ok"])
		loaded = get_demand_review(demand=name)
		self.assertFalse(loaded["funding"]["confirm_ready"])
		self.assertNotAlmostEqual(flt(loaded["funding"]["difference"]), 0)
		with self.assertRaises(Exception):
			confirm_demand_funding_form(demand=name)

	def test_return_to_procurement_enrichment(self) -> None:
		req = _ensure_user("dem-budget-req5@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		bo = _ensure_user("dem-budget-bo@example.com", [ROLE_BUDGET])
		name = _to_budget_confirmation(req, ba, paa, estimate=1000)

		frappe.set_user(bo)
		with self.assertRaises(Exception):
			return_budget_confirmation_form(demand=name, reason="")
		returned = return_budget_confirmation_form(
			demand=name,
			reason="Strategy/funding mismatch — revise enrichment",
		)
		self.assertTrue(returned["ok"])
		self.assertEqual(returned["demand"]["status"], "Returned")
		self.assertEqual(returned["stage"], "Procurement Enrichment")
		decision = frappe.get_all(
			"Demand Decision",
			filters={"demand": name, "decision": "Return"},
			fields=["stage", "reason"],
			order_by="decided_at desc",
			limit=1,
		)[0]
		self.assertEqual(decision.stage, "Budget Confirmation")
		self.assertIn("mismatch", (decision.reason or "").lower())

		# Workspace must open demand-review (not demand-form) so Save/Resubmit are not dead.
		label, route = _action_for(
			{"status": "Returned", "current_stage": "Procurement Enrichment"}
		)
		self.assertEqual(route, "demand-review")
		self.assertEqual(label, "Review")

		frappe.set_user(paa)
		review = get_demand_review(demand=name)
		self.assertTrue(review["can_enrich"])
		self.assertEqual(review["stage"], "Procurement Enrichment")
		# PAA can save enrichment while Returned from Budget.
		saved = enrich_demand_form(
			demand=name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "ICT infrastructure and services",
				"estimate_basis": "Revised after Budget return",
			},
			send_for_budget=0,
		)
		self.assertTrue(saved["ok"])

	def test_prepare_budget_confirmation_ui06_factory(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_budget_confirmation_ui06(
			requester=_ensure_user("dem-budget-factory-req@example.com", [ROLE_REQUESTER])
		)
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["current_stage"], "Budget Confirmation")
		self.assertTrue(payload["budget_officer"])
		self.assertTrue(payload.get("funding"))
		frappe.set_user(payload["budget_officer"])
		loaded = get_demand_review(demand=payload["demand"])
		self.assertTrue(loaded["can_confirm_funding"])
		self.assertEqual(loaded["stage"], "Budget Confirmation")

	def test_auto_suggest_picks_unique_strategy_target_line(self) -> None:
		"""Send-for-budget auto-match uses Primary Strategy target when PE has many lines."""
		req = _ensure_user("dem-budget-req-auto@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		line = _budget_line()
		line_meta = frappe.db.get_value(
			"Budget Line",
			line,
			["primary_target_code", "primary_target_name", "generated_reference"],
			as_dict=True,
		)
		self.assertTrue(line_meta and line_meta.primary_target_code)

		created = create_or_update_demand(
			values={
				"procuring_entity": PE,
				"owner_org_unit": OU,
				"title": "UI06 strategy auto-match demand",
				"need_statement": "Need infrastructure linked to the DHI target",
				"need_rationale": "Strategy-driven match",
				"expected_outcome": "Matched funding line",
				"beneficiaries": "Clinics",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 90),
				"demand_route": "Standard",
				"urgency": "Medium",
				"estimate_confidence": "Medium",
				"estimate_basis": "Market scan",
				"currency": "KES",
				"fixture_namespace": "DEMANDS_UI06_TEST",
			},
			items=[
				{
					"description": "Compute",
					"quantity": 1,
					"uom": "Lot",
					"requester_estimate": 1000,
				}
			],
			user=req,
		)
		name = created["demand"]["name"]
		submit_demand(demand=name, user=req)
		frappe.set_user(ba)
		record_business_decision_form(demand=name, decision="Support", comment="ok")
		frappe.set_user(paa)
		# No explicit budget_line — matcher must resolve via Strategy alone.
		enrich_demand(
			demand=name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "ICT infrastructure and services",
				"estimate_basis": "Market check",
			},
			strategy_references=[
				{
					"reference_type": "Primary",
					"target_code": line_meta.primary_target_code,
					"target_name": line_meta.primary_target_name,
					"snapshot_label": (
						f"{line_meta.primary_target_name} ({line_meta.primary_target_code})"
					),
					"hierarchy_path": "Outcome > Target",
					"selection_source": "Manual",
					"confirmation_reason": "Unique strategy match",
				}
			],
			value_treatments=[],
			send_for_budget=True,
			user=paa,
		)
		pending = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": name, "bo_confirmation_status": "Pending"},
			fields=["budget_line", "matching_source"],
		)
		self.assertEqual(len(pending), 1, "Strategy-unique line must auto-create Pending allocation")
		self.assertEqual(pending[0].budget_line, line)
		self.assertEqual(pending[0].matching_source, "Automatic")
		open_multi = frappe.get_all(
			"Funding Exception",
			filters={
				"demand": name,
				"status": ["in", ["Open", "In Progress"]],
				"exception_type": "Multiple Matches",
			},
			pluck="name",
		)
		self.assertEqual(open_multi, [])

		bo = _ensure_user("dem-budget-bo@example.com", [ROLE_BUDGET])
		frappe.set_user(bo)
		loaded = get_demand_review(demand=name)
		self.assertIsNotNone(loaded["funding"]["recommendation"])
		self.assertNotEqual(loaded["funding"]["condition"], "Exception")

	def test_multiple_matches_exception_explains_and_lists_candidates(self) -> None:
		req = _ensure_user("dem-budget-req-multi@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-budget-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-budget-paa@example.com", [ROLE_PAA])
		created = create_or_update_demand(
			values={
				"procuring_entity": PE,
				"owner_org_unit": OU,
				"title": "UI06 ambiguous funding demand",
				"need_statement": "Need without a unique Budget Line Strategy link",
				"need_rationale": "Force Multiple Matches",
				"expected_outcome": "Exception path",
				"beneficiaries": "Clinics",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 90),
				"demand_route": "Standard",
				"urgency": "Medium",
				"estimate_confidence": "Medium",
				"estimate_basis": "Market scan",
				"currency": "KES",
				"fixture_namespace": "DEMANDS_UI06_TEST",
			},
			items=[
				{
					"description": "Ambiguous item",
					"quantity": 1,
					"uom": "Lot",
					"requester_estimate": 1000,
				}
			],
			user=req,
		)
		name = created["demand"]["name"]
		submit_demand(demand=name, user=req)
		frappe.set_user(ba)
		record_business_decision_form(demand=name, decision="Support", comment="ok")
		frappe.set_user(paa)
		enrich_demand(
			demand=name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "ICT infrastructure and services",
			},
			strategy_references=[
				{
					"reference_type": "Primary",
					"target_code": "T-NO-BUDGET-LINE",
					"target_name": "Unlinked target for ambiguity",
					"snapshot_label": "Unlinked target for ambiguity (T-NO-BUDGET-LINE)",
					"hierarchy_path": "Outcome > Target",
					"confirmation_reason": "No Budget Line shares this target",
				}
			],
			value_treatments=[],
			send_for_budget=True,
			user=paa,
		)
		suggestion = suggest_funding_allocations(demand=name, user=paa)
		# If PE still has >1 line and no strategy hit, expect Multiple Matches.
		if suggestion.get("exception_type") != "Multiple Matches":
			self.skipTest("PE-MOH fixture no longer has ambiguous multi-line match case")
		self.assertIsNone(suggestion.get("allocation"))

		bo = _ensure_user("dem-budget-bo@example.com", [ROLE_BUDGET])
		frappe.set_user(bo)
		loaded = get_demand_review(demand=name)
		exc = loaded["funding"]["exception"]
		self.assertIsNotNone(exc)
		self.assertEqual(exc["type"], "Multiple Matches")
		self.assertIn("could not auto-select", (exc.get("summary") or "").lower())
		self.assertGreaterEqual(len(loaded["funding"]["candidates"]), 2)
		self.assertIsNone(loaded["funding"]["recommendation"])
		self.assertFalse(loaded["funding"]["confirm_ready"])

	def test_manual_adjust_clears_insufficient_funding_errors(self) -> None:
		"""BO adjust to a sufficient line must clear exception banner + allow Active status."""
		frappe.set_user("Administrator")
		payload = prepare_budget_confirmation_ui06(
			requester=_ensure_user("dem-budget-adj-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		bo = payload["budget_officer"]
		small = frappe.db.get_value(
			"Budget Line", {"generated_reference": "MOH-BL-HWD-2027"}, "name"
		)
		large = frappe.db.get_value(
			"Budget Line", {"generated_reference": "MOH-BL-DHI-2027"}, "name"
		)
		if not small or not large:
			self.skipTest("MOH budget line fixtures missing for adjust clear test")

		frappe.set_user(bo)
		# Force shortfall on the small Workforce line (~80M available vs ~455M estimate).
		short = adjust_funding_allocation_form(demand=name, budget_line=small)
		self.assertTrue(short["ok"])
		loaded = get_demand_review(demand=name)
		self.assertIsNotNone(loaded["funding"]["exception"])
		self.assertEqual(loaded["funding"]["condition"], "Exception")
		rec = loaded["funding"]["recommendation"]
		self.assertIsNotNone(rec)
		self.assertFalse(rec.get("sufficient"))
		self.assertNotEqual(rec.get("display_status"), "Active")

		# Manual adjust to the sufficient Digital clinical systems line.
		fixed = adjust_funding_allocation_form(demand=name, budget_line=large)
		self.assertTrue(fixed["ok"])
		loaded2 = get_demand_review(demand=name)
		self.assertIsNone(loaded2["funding"]["exception"])
		self.assertNotEqual(loaded2["funding"]["condition"], "Exception")
		rec2 = loaded2["funding"]["recommendation"]
		self.assertIsNotNone(rec2)
		self.assertTrue(rec2.get("sufficient"))
		self.assertEqual(rec2.get("display_status"), "Active")
		self.assertTrue(loaded2["funding"]["confirm_ready"])
		open_exc = frappe.get_all(
			"Funding Exception",
			filters={"demand": name, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		)
		self.assertEqual(open_exc, [])


class TestDemandsBudgetExceptionUi07(IntegrationTestCase):
	"""DEM-UI-07 — Insufficient Funding exception DTO + resolve/save-note."""

	def test_exception_dto_shortfall_and_confirm_blocked(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_budget_exception_ui07(
			requester=_ensure_user("dem-budget-ui07-req@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		bo = payload["budget_officer"]
		self.assertEqual(payload["current_stage"], "Budget Confirmation")
		self.assertEqual(payload.get("exception_type"), "Insufficient Funding")

		frappe.set_user(bo)
		loaded = get_demand_review(demand=name)
		funding = loaded["funding"]
		self.assertIsNotNone(funding)
		exc = funding["exception"]
		self.assertIsNotNone(exc)
		self.assertEqual(exc["type"], "Insufficient Funding")
		self.assertEqual(exc.get("title"), "Funding Shortfall Detected")
		self.assertIn("cannot be confirmed", (exc.get("summary") or "").lower())
		self.assertFalse(funding["confirm_ready"])
		self.assertEqual(funding["condition"], "Exception")
		self.assertGreater(flt(funding.get("shortfall")), 0)
		self.assertGreater(flt(funding.get("unfunded_amount")), 0)
		self.assertTrue(funding.get("shortfall_display"))
		self.assertTrue(funding.get("available_funding_display"))
		self.assertIn("KES", funding["shortfall_display"])
		self.assertIn(",", funding["shortfall_display"])
		rec = funding["recommendation"]
		self.assertIsNotNone(rec)
		self.assertFalse(rec.get("sufficient"))
		self.assertNotEqual(rec.get("display_status"), "Active")
		# Reference display must not expose internal ids.
		self.assertNotEqual(rec.get("budget_display"), rec.get("budget"))
		self.assertNotIn(rec.get("budget") or "___", rec.get("budget_display") or "")

		with self.assertRaises(Exception):
			confirm_demand_funding_form(demand=name)

	def test_save_note_keeps_exception_and_blocks_confirm(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_budget_exception_ui07(
			requester=_ensure_user("dem-budget-ui07-note@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		bo = payload["budget_officer"]
		frappe.set_user(bo)
		note = "Phased delivery required — shortfall exceeds available line capacity."
		saved = save_funding_exception_note_form(demand=name, reason=note)
		self.assertTrue(saved["ok"])
		self.assertEqual(saved.get("exception_status"), "In Progress")
		funding = saved["funding"]
		self.assertIsNotNone(funding["exception"])
		self.assertEqual(funding["exception"].get("status"), "In Progress")
		self.assertEqual(funding["exception"].get("resolution_reason"), note)
		self.assertFalse(funding["confirm_ready"])
		loaded = get_demand_review(demand=name)
		self.assertEqual(loaded["demand"]["current_stage"], "Budget Confirmation")
		self.assertFalse(loaded["funding"]["confirm_ready"])

	def test_return_resolve_requires_note_and_leaves_budget(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_budget_exception_ui07(
			requester=_ensure_user("dem-budget-ui07-ret@example.com", [ROLE_REQUESTER])
		)
		name = payload["demand"]
		bo = payload["budget_officer"]
		frappe.set_user(bo)
		with self.assertRaises(Exception):
			resolve_funding_exception_form(demand=name, resolution="Return", reason="")
		result = resolve_funding_exception_form(
			demand=name,
			resolution="Return",
			reason="Revise scope — shortfall of available funding.",
		)
		self.assertTrue(result["ok"])
		fresh = get_demand_review(demand=name)
		# Returned out of Budget Confirmation.
		self.assertNotEqual(fresh["demand"]["current_stage"], "Budget Confirmation")
		open_exc = frappe.get_all(
			"Funding Exception",
			filters={"demand": name, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		)
		self.assertEqual(open_exc, [])

	def test_multiple_matches_factory_dto_and_candidates(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_budget_exception_multiple_matches_ui07(
			requester=_ensure_user(
				"dem-budget-ui07-mm-req@example.com", [ROLE_REQUESTER]
			)
		)
		name = payload["demand"]
		bo = payload["budget_officer"]
		self.assertEqual(payload["current_stage"], "Budget Confirmation")
		self.assertEqual(payload.get("exception_type"), "Multiple Matches")
		self.assertGreaterEqual(int(payload.get("candidate_count") or 0), 2)

		frappe.set_user(bo)
		loaded = get_demand_review(demand=name)
		funding = loaded["funding"]
		exc = funding["exception"]
		self.assertIsNotNone(exc)
		self.assertEqual(exc["type"], "Multiple Matches")
		self.assertEqual(exc.get("title"), "Multiple Funding Matches")
		self.assertIn("could not auto-select", (exc.get("summary") or "").lower())
		self.assertFalse(funding["confirm_ready"])
		self.assertIsNone(funding["recommendation"])
		self.assertGreaterEqual(len(funding["candidates"]), 2)
		for cand in funding["candidates"][:3]:
			self.assertTrue(cand.get("display") or cand.get("name") or cand.get("code"))
			if cand.get("id"):
				self.assertNotEqual(cand.get("display"), cand.get("id"))
