# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.3 — `InheritedRequirementSnapshot`: the handoff
payload copied once into the Version as canonical JSON with its digest
(plan D3). Every row keeps its Requisition identifier; no Tender command
alters it; there is no editable copy."""

from __future__ import annotations

import json
from typing import Any

from kentender_procurement.tender_preparation.services import digest

VISIBLE_TYPES = {
	"Equipment item": ("items", "requisition_item_id"),
	"Technical requirement": ("technical_requirements", "technical_requirement_id"),
	"Related service": ("related_services", "service_requirement_id"),
	"Acceptance requirement": ("acceptance_requirements", "acceptance_requirement_id"),
}

# Internal policy context — visible to the officer and the approver, never
# rendered to a bidder (§4, §7.3, TPR-AC-044).
INTERNAL_ONLY_KEYS = ("strategic_objective", "strategic_objective_path", "plan_horizon", "multi_year_justification")


def build(handoff_doc) -> tuple[dict[str, Any], str]:
	payload = json.loads(handoff_doc.payload_json)
	snapshot = {k: v for k, v in payload.items() if k != "decisions"}
	snapshot["handoff"] = handoff_doc.name
	snapshot["handoff_digest"] = handoff_doc.handoff_digest
	return snapshot, digest.sha256_hex(snapshot)


def load(version) -> dict[str, Any]:
	return json.loads(version.snapshot_json or "{}")


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
		out[label] = {row.get(id_field) for row in (snapshot.get(key) or []) if row.get(id_field)}
	return out


def internal_context(snapshot: dict[str, Any]) -> dict[str, Any]:
	return {k: snapshot.get(k) for k in INTERNAL_ONLY_KEYS}


def total_quantity(snapshot: dict[str, Any]) -> float:
	return float(sum(float(row.get("quantity") or 0) for row in snapshot.get("items") or []))


def total_value(snapshot: dict[str, Any]) -> float:
	return float(sum(float(row.get("requested_value") or 0) for row in snapshot.get("drawdown_lines") or []))
