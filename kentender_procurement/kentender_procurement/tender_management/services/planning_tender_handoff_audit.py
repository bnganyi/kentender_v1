# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender handoff audit + snapshot (doc 2 sec. 18, Tracker B8).

Persists ``source_package_snapshot_json`` / ``source_package_hash`` / lineage counts on
``Procurement Tender`` and appends a structured **Comment** for audit evidence.

This module does **not** load ``sample_tender.json``; snapshot content is derived from
``Procurement Package`` / plan / active lines only.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt

from kentender_procurement.tender_management.services.std_template_engine import hash_config


SNAPSHOT_SCHEMA = "kentender.planning_to_tender.handoff_snapshot/v1"
_MAX_LINES = 200


def _sha256_utf8(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_handoff_snapshot_and_hashes(
	pkg: Document,
	plan: Document | None,
	std_template: str,
	std_resolution_path: str,
	xmv_findings: list[dict[str, str]],
	xmv_warnings: list[dict[str, str]],
	configuration_json: str,
	package_status_before: str,
) -> tuple[dict[str, Any], str, str, str, int, int]:
	"""Return snapshot dict, snapshot JSON string, snapshot hash, configuration hash, counts."""
	plan_code = None
	if plan:
		plan_code = frappe.db.get_value("Procurement Plan", plan.name, "plan_code")

	lines_raw = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": pkg.name},
		fields=["name", "demand_id", "budget_line_id", "amount", "is_active"],
		limit=_MAX_LINES,
	)
	lines = [
		{"name": r["name"], "demand_id": r.get("demand_id"), "budget_line_id": r.get("budget_line_id"), "amount": r.get("amount")}
		for r in lines_raw
		if cint(r.get("is_active", 1)) == 1
	]
	demand_ids = {str(r["demand_id"]) for r in lines if r.get("demand_id")}
	budget_ids = {str(r["budget_line_id"]) for r in lines if r.get("budget_line_id")}

	snap: dict[str, Any] = {
		"schema": SNAPSHOT_SCHEMA,
		"package": {
			"name": pkg.name,
			"code": pkg.get("package_code"),
			"title": pkg.get("package_name"),
			"description": (pkg.get("planner_notes") or "")[:4000],
			"status_at_capture": package_status_before or "",
		},
		"plan": {"id": pkg.get("plan_id"), "code": plan_code},
		"lines": lines,
		"demand_ids": sorted(demand_ids),
		"budget_line_ids": sorted(budget_ids),
		"method": {
			"procurement_method": pkg.get("procurement_method"),
			"contract_type": pkg.get("contract_type"),
			"template_id": pkg.get("template_id"),
		},
		"financial": {
			"estimated_value": flt(pkg.get("estimated_value")),
			"currency": (pkg.get("currency") or "").strip(),
		},
		"std": {"template": std_template, "resolution_path": std_resolution_path},
		"xmv": {"findings": xmv_findings, "warnings": xmv_warnings},
	}
	snap_json = json.dumps(snap, ensure_ascii=False, separators=(",", ":"), default=str)
	snap_hash = _sha256_utf8(snap_json)
	cfg_obj = json.loads(configuration_json or "{}")
	cfg_hash = hash_config(cfg_obj)
	return snap, snap_json, snap_hash, cfg_hash, len(demand_ids), len(budget_ids)


def append_handoff_audit_comment(
	tender_name: str,
	*,
	actor: str,
	roles: list[str],
	source_package: str,
	source_plan: str | None,
	package_status_before: str,
	package_status_after: str | None,
	target_tender: str,
	std_template: str,
	xmv_findings: list[dict[str, str]],
	xmv_warnings: list[dict[str, str]],
	snapshot_hash: str,
	configuration_hash: str,
) -> None:
	"""Append a structured audit record as a ``Comment`` on the tender (doc 2 sec. 18.1)."""
	payload = {
		"event": "planning_to_tender_handoff",
		"actor": actor,
		"actor_roles": roles,
		"source_package": source_package,
		"source_plan": source_plan,
		"package_status_before": package_status_before,
		"package_status_after": package_status_after,
		"target_tender": target_tender,
		"std_template": std_template,
		"xmv_findings": xmv_findings,
		"xmv_warnings": xmv_warnings,
		"handoff_snapshot_sha256": snapshot_hash,
		"configuration_hash_after_init": configuration_hash,
	}
	text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
	if len(text) > 12000:
		text = text[:11900] + "…"
	doc = frappe.get_doc("Procurement Tender", tender_name)
	doc.add_comment("Comment", text=text)
