# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procuring Entity cleanup for the demo platform seed."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds._common import ensure_procuring_entity
from kentender_core.seeds.demo_platform_seed.constants import (
	LEGACY_MOE,
	LEGACY_MOH,
	PE_MOE,
	PE_MOE_NAME,
	PE_MOH,
	PE_MOH_NAME,
	REMOVE_PE_CODES,
)
from kentender_core.seeds.migrate_legacy_moh_entity import run as migrate_legacy_moh


def _rewrite_field(doctype: str, field: str, old: str, new: str) -> int:
	if not frappe.db.exists("DocType", doctype):
		return 0
	if not frappe.db.has_column(doctype, field):
		return 0
	before = frappe.db.count(doctype, {field: old})
	if not before:
		return 0
	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}`
		SET `{field}` = %s, modified = modified
		WHERE `{field}` = %s
		""",
		(new, old),
	)
	return int(before)


def _rewrite_code_fields(old: str, new: str) -> dict[str, int]:
	"""Rewrite procuring_entity_code string fields on known doctypes."""
	out: dict[str, int] = {}
	candidates = (
		("Procurement Package", "procuring_entity_code"),
		("Tender Configuration", "procuring_entity_code"),
		("IT Tender Publication Record", "procuring_entity_code"),
		("TM2 Tender", "procuring_entity_code"),
		("Procurement Journey", "procuring_entity_code"),
	)
	for dt, field in candidates:
		n = _rewrite_field(dt, field, old, new)
		if n:
			out[f"{dt}.{field}"] = n
	return out


def _rewrite_link_fields(old: str, new: str) -> dict[str, int]:
	out: dict[str, int] = {}
	for dt, field in (
		("Demand", "procuring_entity"),
		("Procuring Department", "procuring_entity"),
		("Budget", "procuring_entity"),
		("Budget Line", "procuring_entity"),
		# ("Strategic Plan", "procuring_entity"),  # removed MVP-1 strategy teardown
		("Procurement Plan", "procuring_entity"),
	):
		n = _rewrite_field(dt, field, old, new)
		if n:
			out[f"{dt}.{field}"] = n
	if frappe.db.has_column("User", "kt_procuring_entity"):
		n = _rewrite_field("User", "kt_procuring_entity", old, new)
		if n:
			out["User.kt_procuring_entity"] = n
	if frappe.db.exists("DocType", "User Permission"):
		before = frappe.db.count(
			"User Permission", {"allow": "Procuring Entity", "for_value": old}
		)
		if before:
			frappe.db.sql(
				"""
				UPDATE `tabUser Permission`
				SET for_value = %s, modified = modified
				WHERE allow = 'Procuring Entity' AND for_value = %s
				""",
				(new, old),
			)
			out["User Permission"] = int(before)
	return out


def _delete_pe_if_unused(code: str) -> bool:
	if not frappe.db.exists("Procuring Entity", code):
		return False
	# Still referenced?
	for dt, field in (
		("Demand", "procuring_entity"),
		("Budget", "procuring_entity"),
		("Procurement Package", "procuring_entity_code"),
		("Tender Configuration", "procuring_entity_code"),
	):
		if frappe.db.exists("DocType", dt) and frappe.db.has_column(dt, field):
			if frappe.db.count(dt, {field: code}):
				return False
	frappe.delete_doc("Procuring Entity", code, force=True, ignore_permissions=True)
	return True


def cleanup_procuring_entities() -> dict[str, Any]:
	"""Ensure PE-MOH + PE-MOE, migrate legacy codes, remove demo clutter PEs."""
	ensure_procuring_entity(PE_MOH, PE_MOH_NAME)
	ensure_procuring_entity(PE_MOE, PE_MOE_NAME)

	moh_migrate = migrate_legacy_moh()
	rewrites: dict[str, Any] = {"moh": moh_migrate}
	# Extra code-field rewrites for MOH → PE-MOH
	rewrites["moh_codes"] = _rewrite_code_fields(LEGACY_MOH, PE_MOH)

	# Education: MOE → PE-MOE
	moe_links = _rewrite_link_fields(LEGACY_MOE, PE_MOE)
	moe_codes = _rewrite_code_fields(LEGACY_MOE, PE_MOE)
	rewrites["moe"] = {**moe_links, **moe_codes}

	removed: list[str] = []
	for code in (LEGACY_MOH, LEGACY_MOE, *REMOVE_PE_CODES):
		if code in (PE_MOH, PE_MOE):
			continue
		# Migrate lean/journey PE codes on packages/configs to PE-MOH first
		if code.startswith("TCFG-"):
			_rewrite_code_fields(code, PE_MOH)
			_rewrite_link_fields(code, PE_MOH)
		if _delete_pe_if_unused(code):
			removed.append(code)

	frappe.db.commit()
	return {
		"ok": True,
		"entities": [PE_MOH, PE_MOE],
		"rewrites": rewrites,
		"removed": removed,
	}
