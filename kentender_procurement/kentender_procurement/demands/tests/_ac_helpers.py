# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared helpers for DEM-AC-* evidence modules."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today

from kentender_procurement.demands.services.demand_lifecycle import (
	approve_and_reserve_demand,
	confirm_demand_funding,
	create_or_update_demand,
	enrich_demand,
	record_business_decision,
	submit_demand,
	suggest_funding_allocations,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUDGET,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_PLANNING,
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
NS = "DEMANDS_AC_TEST"


def ensure_user(
	email: str,
	roles: list[str],
	*,
	pe: str = PE,
	ou: str = OU,
	replace_roles: bool = False,
) -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0][:40],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	if replace_roles:
		user.set("roles", [])
	have = {r.role for r in user.roles}
	changed = replace_roles
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
				"procuring_entity": pe,
				"organisation_unit": ou,
				"role": role,
			},
		):
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": email,
					"role": role,
					"procuring_entity": pe,
					"organisation_unit": ou,
					"include_descendants": 1,
					"fixture_namespace": NS,
				}
			).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


def budget_line() -> str:
	name = frappe.db.get_value(
		"Budget Line", {"generated_reference": "MOH-BL-DHI-2027"}, "name"
	)
	if not name:
		name = frappe.db.get_value(
			"Budget Line", {"fixture_namespace": "KENTENDER_MVP_V1"}, "name"
		)
	if not name:
		raise frappe.ValidationError("No Budget Line fixture for DEM-AC tests")
	return name


def create_draft(
	user: str,
	*,
	estimate: float = 1000,
	title: str = "DEM-AC evidence demand",
	route: str = "Standard",
	route_justification: str | None = None,
	pe: str = PE,
	ou: str = OU,
) -> str:
	values: dict = {
		"procuring_entity": pe,
		"owner_org_unit": ou,
		"title": title,
		"need_statement": "Need connectivity upgrades for clinics",
		"need_rationale": "Service continuity requires resilient links",
		"expected_outcome": "Reliable clinic connectivity",
		"beneficiaries": "County clinics",
		"delivery_location": "Nairobi",
		"required_by_date": add_days(today(), 90),
		"demand_route": route,
		"urgency": "High" if route == "Emergency" else "Medium",
		"requester_estimate": estimate,
		"estimate_confidence": "Medium",
		"estimate_basis": "Market scan",
		"currency": "KES",
		"fixture_namespace": NS,
	}
	if route_justification:
		values["route_justification"] = route_justification
	created = create_or_update_demand(
		values=values,
		items=[
			{
				"description": "Network and compute lot",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": estimate,
			}
		],
		user=user,
	)
	return created["demand"]["name"]


def advance_to_final_approval(
	*,
	req: str,
	ba: str,
	paa: str,
	bo: str,
	estimate: float = 1000,
	route: str = "Standard",
	route_justification: str | None = None,
	title: str = "DEM-AC final-approval demand",
) -> str:
	name = create_draft(
		req,
		estimate=estimate,
		title=title,
		route=route,
		route_justification=route_justification,
	)
	submit_demand(demand=name, user=req)
	record_business_decision(
		demand=name, decision="Support", comment="Aligned", user=ba
	)
	line = budget_line()
	meta = (
		frappe.db.get_value(
			"Budget Line",
			line,
			["primary_target_code", "primary_target_name"],
			as_dict=True,
		)
		or {}
	)
	t_code = (meta.get("primary_target_code") or "T-AC").strip()
	t_name = (meta.get("primary_target_name") or "AC Primary Target").strip()
	enrich_demand(
		demand=name,
		values={
			"confirmed_estimate": estimate,
			"procurement_category": "Works",
			"estimate_basis": "Market check",
			"demand_route": route,
			**({"route_justification": route_justification} if route_justification else {}),
		},
		strategy_references=[
			{
				"reference_type": "Primary",
				"target_code": t_code,
				"target_name": t_name,
				"snapshot_label": f"{t_name} ({t_code})",
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
		raise frappe.ValidationError("Budget line headroom insufficient for DEM-AC amount")
	for exc in frappe.get_all(
		"Funding Exception",
		filters={"demand": name, "status": ["in", ["Open", "In Progress"]]},
		pluck="name",
	):
		frappe.db.set_value("Funding Exception", exc, "status", "Resolved")
	confirm_demand_funding(
		demand=name,
		allocations=[
			{
				"budget_line": line,
				"allocation_amount": estimate,
				"matching_source": "Budget Officer",
			}
		],
		user=bo,
	)
	return name


def advance_to_approved(
	*,
	req: str,
	ba: str,
	paa: str,
	bo: str,
	estimate: float = 1000,
	idempotency_key: str | None = None,
	title: str = "DEM-AC approved demand",
) -> str:
	name = advance_to_final_approval(
		req=req, ba=ba, paa=paa, bo=bo, estimate=estimate, title=title
	)
	approve_and_reserve_demand(
		demand=name, user=paa, idempotency_key=idempotency_key
	)
	return name


def actor_bundle(prefix: str) -> dict[str, str]:
	return {
		"req": ensure_user(f"{prefix}-req@example.com", [ROLE_REQUESTER]),
		"ba": ensure_user(f"{prefix}-ba@example.com", [ROLE_BUSINESS]),
		"paa": ensure_user(f"{prefix}-paa@example.com", [ROLE_PAA]),
		"bo": ensure_user(f"{prefix}-bo@example.com", [ROLE_BUDGET]),
		"planner": ensure_user(f"{prefix}-plan@example.com", [ROLE_PLANNING]),
	}
