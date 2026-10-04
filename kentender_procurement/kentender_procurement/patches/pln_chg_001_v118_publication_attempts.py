# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.9 (plan D8) — carry the v1.12 `Annual Plan Publication`
rows into the publication pipeline records: one `Plan Publication` per
(Plan Version, destination) with its `Approved Plan Snapshot`, and one
`Publication Attempt` per historical attempt. post_model_sync, idempotent; the
v1.12 doctype itself is retired by the Phase 2 exit patch.
"""

from __future__ import annotations

import json

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "Annual Plan Publication"):
		return
	rows = frappe.db.get_all(
		"Annual Plan Publication",
		fields=["name", "plan_version", "destination", "attempt_number", "result", "payload_hash", "payload", "legal_character", "external_reference", "attempted_at", "acknowledged_at", "fixture_namespace"],
		order_by="plan_version, destination, attempt_number",
	)
	for row in rows:
		snapshot = _snapshot_for(row)
		publication = frappe.db.get_value("Plan Publication", {"snapshot": snapshot, "destination": row.destination}, "name")
		if not publication:
			publication = f"PUB-{row.plan_version}-{row.destination}"
			frappe.get_doc({
				"doctype": "Plan Publication", "publication_id": publication, "snapshot": snapshot, "plan_version": row.plan_version,
				"destination": row.destination, "schema_version": "KenTenderAnnualPlan.v1", "package_hash": row.payload_hash or "",
				"manifest": json.dumps([{"filename": "annual-procurement-plan.json", "media_type": "application/json", "hash": row.payload_hash or "", "size": len(row.payload or "")}]),
				"publication_state": "Pending", "record_version": 0, "fixture_namespace": row.fixture_namespace,
			}).db_insert()
		if not frappe.db.exists("Publication Attempt", {"publication": publication, "attempt_number": row.attempt_number}):
			frappe.get_doc({
				"doctype": "Publication Attempt", "publication": publication, "attempt_number": row.attempt_number, "result": row.result or "Pending",
				"attempted_at": row.attempted_at, "completed_at": row.acknowledged_at, "external_reference": row.external_reference or "",
				"response_evidence": json.dumps({"legal_character": row.legal_character or "", "migrated_from": row.name}), "fixture_namespace": row.fixture_namespace,
			}).db_insert()
		if row.result == "Acknowledged":
			frappe.db.set_value("Plan Publication", publication, {"publication_state": "Acknowledged", "acknowledged_at": row.acknowledged_at, "external_reference": row.external_reference or ""}, update_modified=False)
		elif row.result in ("Failed", "Indeterminate") and frappe.db.get_value("Plan Publication", publication, "publication_state") == "Pending":
			frappe.db.set_value("Plan Publication", publication, "publication_state", row.result, update_modified=False)
	frappe.db.commit()


def _snapshot_for(row) -> str:
	existing = frappe.db.get_value("Approved Plan Snapshot", {"plan_version": row.plan_version}, "name")
	if existing:
		return existing
	version = frappe.db.get_value("Annual Plan Version", row.plan_version, ["annual_plan", "submitted_snapshot", "snapshot_hash", "modified"], as_dict=True)
	doc = frappe.get_doc({
		"doctype": "Approved Plan Snapshot", "plan_version": row.plan_version, "annual_plan": version.annual_plan,
		"content": row.payload or version.submitted_snapshot or "{}", "evidence_index": "{}",
		"content_digest": row.payload_hash or version.snapshot_hash or frappe.generate_hash(length=16),
		"approved_at": row.attempted_at or version.modified, "fixture_namespace": row.fixture_namespace,
	})
	doc.db_insert()
	return doc.name
