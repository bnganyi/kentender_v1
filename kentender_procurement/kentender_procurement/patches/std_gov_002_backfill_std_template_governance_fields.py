# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-002 — backfill governance columns on existing ``STD Template`` rows.

Maps POC ``status`` to ``lifecycle_status``, normalizes ``template_family`` to
pack Select values, and applies static defaults for counters and hash metadata.
"""

from __future__ import annotations

import frappe

STATUS_TO_LIFECYCLE: dict[str, str] = {
	"Draft Package": "Imported",
	"Imported": "Imported",
	"POC Approved": "Approved",
	"Suspended": "Suspended",
	"Superseded": "Superseded",
	"Retired": "Retired",
}


def _normalize_template_family(raw: str | None) -> str:
	if not raw:
		return "Other"
	u = str(raw).strip().upper()
	if u in (
		"BUILDING_AND_ASSOCIATED_CIVIL_ENGINEERING_WORKS",
		"WORKS",
		"WORK",
	):
		return "Works"
	if u in ("GOODS", "GOOD"):
		return "Goods"
	if u in ("SERVICES", "SERVICE"):
		return "Services"
	if u in ("CONSULTING", "CONSULTANCY"):
		return "Consultancy"
	if u in ("ICT",):
		return "ICT"
	if "WORKS" in u or ("BUILDING" in u and "CIVIL" in u):
		return "Works"
	return "Other"


def execute() -> None:
	if not frappe.db.has_table("tabSTD Template"):
		return

	defaults: dict = {
		"import_source_type": "Seed",
		"package_hash_algorithm": "SHA-256",
		"canonicalization_version": "V1",
		"latest_validation_status": "Not Run",
		"critical_finding_count": 0,
		"warning_finding_count": 0,
		"info_finding_count": 0,
		"validation_is_current": 0,
		"tender_usage_count": 0,
		"locked_due_to_usage": 0,
		"mutation_blocked": 0,
		"delete_blocked": 1,
		"payload_locked": 0,
		"is_suspended": 0,
		"is_historical": 0,
		"approval_override_used": 0,
		"is_default_active_version": 0,
		"is_governed_version": 1,
	}

	for row in frappe.get_all(
		"STD Template",
		fields=["name", "status", "template_family", "version_label", "package_version", "template_version"],
	):
		name = row.name
		lifecycle = STATUS_TO_LIFECYCLE.get(row.get("status") or "", "Imported")
		family = _normalize_template_family(row.get("template_family"))
		tpl_ver = (row.get("template_version") or "").strip()
		if not tpl_ver:
			tpl_ver = (row.get("version_label") or "").strip() or (row.get("package_version") or "").strip()

		updates: dict = {
			"lifecycle_status": lifecycle,
			"template_family": family,
			"template_version": tpl_ver or "POC",
		}
		for key, val in defaults.items():
			updates[key] = val

		frappe.db.set_value("STD Template", name, updates, update_modified=False)
