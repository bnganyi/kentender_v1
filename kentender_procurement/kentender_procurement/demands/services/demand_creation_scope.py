# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demand create ownership — Contract v2.2 §4.5 #11 / §7.5 creation-scope states.

Eligible pairs come only from active Demand Requester User Scope Assignments.
Administrator status, assignment order and list filters must not supply a default.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services.org_scope_access import user_scope_rows
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
	throw_demand_error,
)

ERR_VALIDATION = "DEMAND_VALIDATION_ERROR"
MODE_SINGLE = "single_readonly"
MODE_MULTI = "multi_required"
MODE_BLOCKED = "blocked"


def _entity_ref(pe: str) -> dict[str, str]:
	name = pe
	code = pe
	if pe and frappe.db.exists("Procuring Entity", pe):
		name = str(
			frappe.db.get_value("Procuring Entity", pe, "entity_name")
			or frappe.db.get_value("Procuring Entity", pe, "procuring_entity_name")
			or pe
		)
		code = str(frappe.db.get_value("Procuring Entity", pe, "entity_code") or pe)
	return {"id": pe, "code": code, "name": name}


def _unit_ref(ou: str) -> dict[str, str]:
	name = ou
	code = ou
	if ou and frappe.db.exists("Organisation Unit", ou):
		name = str(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)
		code = str(frappe.db.get_value("Organisation Unit", ou, "unit_code") or ou)
	return {"id": ou, "code": code, "name": name}


def list_eligible_requester_pairs(user: str | None = None) -> list[dict[str, Any]]:
	"""Distinct PE+OU pairs from Demand Requester User Scope Assignments."""
	user = user or frappe.session.user
	seen: set[tuple[str, str]] = set()
	out: list[dict[str, Any]] = []
	for row in user_scope_rows(user):
		if (row.get("role") or "") != ROLE_REQUESTER:
			continue
		pe = (row.get("procuring_entity") or "").strip()
		ou = (row.get("organisation_unit") or "").strip()
		if not pe or not ou:
			continue
		key = (pe, ou)
		if key in seen:
			continue
		seen.add(key)
		out.append(
			{
				"procuring_entity": _entity_ref(pe),
				"owner_org_unit": _unit_ref(ou),
			}
		)
	# Deterministic order by PE then OU (never used as a silent default).
	out.sort(
		key=lambda p: (
			p["procuring_entity"]["id"],
			p["owner_org_unit"]["id"],
		)
	)
	return out


def resolve_demand_creation_scope(user: str | None = None) -> dict[str, Any]:
	"""Return selection_mode + pairs for Create Demand (Contract §7.5)."""
	user = user or frappe.session.user
	pairs = list_eligible_requester_pairs(user)
	if not pairs:
		return {
			"selection_mode": MODE_BLOCKED,
			"pairs": [],
			"selected_pair": None,
			"procuring_entity": None,
			"owner_org_unit": None,
			"procuring_entity_label": "",
			"owner_org_unit_label": "",
			"blocked_reason": "No operational Demand Requester assignment exists.",
		}
	if len(pairs) == 1:
		pe = pairs[0]["procuring_entity"]["id"]
		ou = pairs[0]["owner_org_unit"]["id"]
		return {
			"selection_mode": MODE_SINGLE,
			"pairs": pairs,
			"selected_pair": {"procuring_entity": pe, "owner_org_unit": ou},
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"procuring_entity_label": pairs[0]["procuring_entity"]["name"],
			"owner_org_unit_label": pairs[0]["owner_org_unit"]["name"],
			"blocked_reason": None,
		}
	return {
		"selection_mode": MODE_MULTI,
		"pairs": pairs,
		"selected_pair": None,
		"procuring_entity": None,
		"owner_org_unit": None,
		"procuring_entity_label": "",
		"owner_org_unit_label": "",
		"blocked_reason": None,
	}


def pair_is_eligible(
	procuring_entity: str | None,
	owner_org_unit: str | None,
	*,
	user: str | None = None,
) -> bool:
	pe = (procuring_entity or "").strip()
	ou = (owner_org_unit or "").strip()
	if not pe or not ou:
		return False
	for p in list_eligible_requester_pairs(user):
		if p["procuring_entity"]["id"] == pe and p["owner_org_unit"]["id"] == ou:
			return True
	return False


def assert_creation_pair_allowed(
	procuring_entity: str | None,
	owner_org_unit: str | None,
	*,
	user: str | None = None,
) -> None:
	"""Reject omitted, mixed, or third pairs on create (Contract §7.5)."""
	scope = resolve_demand_creation_scope(user)
	if scope["selection_mode"] == MODE_BLOCKED:
		throw_demand_error(
			ERR_VALIDATION,
			scope.get("blocked_reason")
			or "No operational Demand Requester assignment exists.",
		)
	pe = (procuring_entity or "").strip()
	ou = (owner_org_unit or "").strip()
	if not pe or not ou:
		throw_demand_error(
			ERR_VALIDATION,
			"procuring_entity and owner_org_unit are required",
		)
	if not pair_is_eligible(pe, ou, user=user):
		throw_demand_error(
			ERR_VALIDATION,
			"Selected Procuring Entity and Organisation Unit are not an eligible Demand Requester pair",
		)
