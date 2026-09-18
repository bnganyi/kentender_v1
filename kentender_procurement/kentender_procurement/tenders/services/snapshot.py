# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.3 — `InheritedRequirementSnapshot`: the handoff
payload copied once into the Version as canonical JSON with its digest
(plan D4). Every row keeps its Requisition identifier; no Tender command
alters it; there is no editable copy. Strategic objective, plan horizon,
authorised value and funding evidence are internal-only context."""

from __future__ import annotations

import json
from typing import Any

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


def build(handoff_doc) -> tuple[dict[str, Any], str]:
	payload = json.loads(handoff_doc.payload_json)
	snapshot = {k: v for k, v in payload.items() if k != "decisions"}
	snapshot["handoff"] = handoff_doc.name
	snapshot["handoff_digest"] = handoff_doc.handoff_digest
	snapshot["decisions"] = payload.get("decisions") or []
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


def total_quantity(snapshot: dict[str, Any]) -> float:
	return float(sum(float(row.get("quantity") or 0) for row in snapshot.get("items") or []))


def total_value(snapshot: dict[str, Any]) -> float:
	return float(sum(float(row.get("requested_value") or 0) for row in snapshot.get("drawdown_lines") or []))


def lead_unit(snapshot: dict[str, Any]) -> str:
	units = snapshot.get("contributing_org_unit_ids") or []
	return units[0] if units else ""
