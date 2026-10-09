# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.3 — `InheritedRequirementSnapshot`: the handoff
payload copied once into the Version as canonical JSON with its digest
(plan D4). Every row keeps its Requisition identifier; no Tender command
alters it; there is no editable copy. Strategic objective, plan horizon,
authorised value and funding evidence are internal-only context."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from frappe.utils import cstr

from kentender_procurement.tenders.services import digest

# §4.4 `linked_requirement_type` → (snapshot key, identity field). Warranty/
# support is one inherited block, addressed by a fixed identity.
WARRANTY_ID = "WARRANTY-SUPPORT"
VISIBLE_TYPES: dict[str, tuple[str, str]] = {
	"Item": ("items", "requisition_item_id"),
	"Technical requirement": ("technical_requirements", "technical_requirement_id"),
	"Service": ("related_services", "service_requirement_id"),
	"Warranty/support": ("", ""),
}

# Internal policy context — visible to authorised internal readers only,
# never rendered to a bidder (§4.3).
INTERNAL_ONLY_KEYS = ("strategic_objective", "strategic_objective_path", "plan_horizon", "multi_year_justification")


WARRANTY_FIELDS: tuple[str, ...] = (
	"minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours",
	"manufacturer_support_required", "service_location_constraint", "support_description",
)


def _handoff_v14_names(payload: dict[str, Any]) -> dict[str, Any]:
	"""Requisitions handoff v1.4 (REQ-CHG-001 v1.11/v1.12) renamed or grouped
	fields Tenders reads: `reservation_category` (was `reservation_category_value`),
	`strategic_objective_id` (was `strategic_objective`), the six warranty facts
	under `warranty_support`, and `departmental_certification` /
	`procurement_authorisation` (was `decisions`). Translate once here, at the
	seam, keeping the owner's own fields exactly as sent."""
	out: dict[str, Any] = {}
	if "reservation_category_value" not in payload:
		out["reservation_category_value"] = payload.get("reservation_category") or "None"
	if "strategic_objective" not in payload and "strategic_objective_id" in payload:
		out["strategic_objective"] = payload.get("strategic_objective_id")
	warranty = payload.get("warranty_support") or {}
	for field in WARRANTY_FIELDS:
		if field not in payload and field in warranty:
			out[field] = warranty[field]
	if "decisions" not in payload:
		out["decisions"] = [
			{"actor": d.get("actor"), "capacity": d.get("capacity"), "decided_at": d.get("decided_at"), "decision": d.get("decision")}
			for d in (payload.get("departmental_certification") or {}, payload.get("procurement_authorisation") or {})
			if d.get("decision")
		]
	return out


def with_item_ids(snapshot: dict[str, Any]) -> dict[str, Any]:
	"""REQ-CHG-001 v1.18 §5.7A — every requirement row names the exact items it covers. A handoff 1.5 already
	does; one made before (1.4) is read from the row's scope: `All items` is every item, `Item` the one named."""
	all_ids = [i.get("requisition_item_id") for i in snapshot.get("items") or []]
	for family in ("technical_requirements", "related_services", "acceptance_requirements"):
		rows = []
		for row in snapshot.get(family) or []:
			if "applies_to_item_ids" not in row:
				scope = row.get("applies_to_scope")
				row = {**row, "applies_to_item_ids": all_ids if scope == "All items" or not scope else ([row.get("applies_to_id")] if scope == "Item" else [])}
			rows.append(row)
		if family in snapshot:
			snapshot[family] = rows
	return snapshot


def build(handoff_doc) -> tuple[dict[str, Any], str]:
	payload = json.loads(handoff_doc.payload_json)
	snapshot = {k: v for k, v in payload.items() if k != "decisions"}
	snapshot.update(_handoff_v14_names(payload))
	with_item_ids(snapshot)
	snapshot["handoff"] = handoff_doc.name
	snapshot["handoff_digest"] = handoff_doc.handoff_digest
	snapshot["decisions"] = payload.get("decisions") or snapshot.get("decisions") or []
	return snapshot, digest.sha256_hex(snapshot)


def load(version) -> dict[str, Any]:
	return json.loads(version.requisition_snapshot_json or "{}")


def recompute_digest(snapshot: dict[str, Any]) -> str:
	return digest.sha256_hex(snapshot)


def counts(snapshot: dict[str, Any]) -> dict[str, int]:
	return {
		"items": len(snapshot.get("items") or []),
		"technical_requirements": len(snapshot.get("technical_requirements") or []),
		"related_services": len(snapshot.get("related_services") or []),
		"acceptance_requirements": len(snapshot.get("acceptance_requirements") or []),
		"supporting_materials": len(snapshot.get("supporting_materials") or []),
	}


def visible_ids(snapshot: dict[str, Any]) -> dict[str, set[str]]:
	out: dict[str, set[str]] = {}
	for label, (key, id_field) in VISIBLE_TYPES.items():
		if not key:
			out[label] = {WARRANTY_ID} if snapshot.get("minimum_warranty_months") else set()
			continue
		out[label] = {row.get(id_field) for row in (snapshot.get(key) or []) if row.get(id_field)}
	return out


def internal_context(snapshot: dict[str, Any]) -> dict[str, Any]:
	out = {k: snapshot.get(k) for k in INTERNAL_ONLY_KEYS}
	out["authorised_value"] = total_value(snapshot)
	out["reservation_ids"] = sorted({line.get("reservation_id") for line in snapshot.get("drawdown_lines") or [] if line.get("reservation_id")})
	return out


def total_quantity_exact(snapshot: dict[str, Any]) -> Decimal:
	"""The inherited items' quantities added in exact decimal arithmetic (RG-24); `total_quantity` is for display."""
	return sum((Decimal(cstr(row.get("quantity") or 0)) for row in snapshot.get("items") or []), Decimal(0))


def total_quantity(snapshot: dict[str, Any]) -> float:
	return float(sum(float(row.get("quantity") or 0) for row in snapshot.get("items") or []))


def total_value(snapshot: dict[str, Any]) -> float:
	return float(sum(float(row.get("requested_value") or 0) for row in snapshot.get("drawdown_lines") or []))


def lead_unit(snapshot: dict[str, Any]) -> str:
	"""The Tender's lead department: the certified lead of the exact consumed
	Requisition Version (REQ-CHG-001 v1.14 §5.1, `lead_org_unit_id`; OVS-CHG-001
	v0.6 §4.1, plan D15). The handoff lists contributors alphabetically, so the
	first of them is not the lead; it stands only when no certification is carried."""
	certified = (snapshot.get("departmental_certification") or {}).get("lead_org_unit_id")
	if certified:
		return str(certified)
	units = snapshot.get("contributing_org_unit_ids") or []
	return units[0] if units else ""
