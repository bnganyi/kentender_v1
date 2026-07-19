# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Eligible approved procurement packages for Tender Configuration creation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.constants import (
	ACTIVE_CONFIGURATION_STATUSES,
	ELIGIBLE_PACKAGE_STATUSES,
	FIXTURE_STD_VERSION_ID,
)
from kentender_procurement.tender_configurations.services.std_family_map import (
	resolve_family_from_package,
	resolve_procuring_entity_name,
)


def packages_with_active_configuration() -> set[str]:
	rows = frappe.get_all(
		"Tender Configuration",
		filters={"status": ("in", list(ACTIVE_CONFIGURATION_STATUSES))},
		fields=["procurement_package"],
	)
	return {cstr(r.procurement_package) for r in rows if r.procurement_package}


def resolve_applicable_std_document(
	pkg: Any,
	*,
	std_document_id: str | None = None,
) -> dict[str, Any]:
	"""Resolve ACTIVE STD Version for a package. Returns ids/labels or empty."""
	family = resolve_family_from_package(pkg)
	codes = family["candidate_family_codes"]
	pinned = cstr(
		getattr(pkg, "required_std_template_version_code", None)
		or (pkg.get("required_std_template_version_code") if hasattr(pkg, "get") else None)
		or ""
	).strip()

	if std_document_id:
		doc_id = cstr(std_document_id).strip()
		if not frappe.db.exists("STD Version", doc_id):
			return {"ok": False, "reason": "std_not_found", **family}
		ver = frappe.get_doc("STD Version", doc_id)
		if cstr(ver.lifecycle_state) != "ACTIVE":
			return {"ok": False, "reason": "std_not_active", **family}
		label = cstr(ver.version_label or ver.version_code or ver.name)
		return {
			"ok": True,
			"applicable_std_document_id": ver.name,
			"applicable_std_document_label": label,
			**family,
		}

	filters: dict[str, Any] = {"lifecycle_state": "ACTIVE"}
	if codes:
		filters["family_code"] = ("in", codes)

	versions = frappe.get_all(
		"STD Version",
		filters=filters,
		fields=["name", "version_code", "version_label", "family_code", "package_id"],
		order_by="modified desc",
		limit=20,
	)

	chosen = None
	if pinned and versions:
		for v in versions:
			if pinned in (cstr(v.name), cstr(v.version_code), cstr(v.package_id)):
				chosen = v
				break
	if not chosen and versions:
		chosen = versions[0]

	if not chosen:
		return {"ok": False, "reason": "no_active_std", **family}

	label = cstr(chosen.version_label or chosen.version_code or chosen.name)
	# Prefer Official Library family_name when available
	family_name = frappe.db.get_value("STD Family", chosen.family_code, "family_name")
	if family_name and family["std_family_label"] == "Information Technology":
		# Keep user-facing UI-00 label; store key from map
		pass
	elif family_name and chosen.family_code not in codes:
		family["std_family_label"] = cstr(family_name)

	return {
		"ok": True,
		"applicable_std_document_id": chosen.name,
		"applicable_std_document_label": label,
		**family,
	}


def package_is_eligible(pkg: Any, configured: set[str] | None = None) -> tuple[bool, str | None]:
	status = cstr(getattr(pkg, "status", None) or "").strip()
	if status not in ELIGIBLE_PACKAGE_STATUSES:
		return False, "not_approved"
	name = cstr(getattr(pkg, "name", None) or "")
	configured = configured if configured is not None else packages_with_active_configuration()
	if name in configured:
		return False, "already_configured"
	std = resolve_applicable_std_document(pkg)
	if not std.get("ok"):
		return False, "no_std"
	return True, None


def _approval_date(pkg: Any) -> str | None:
	raw = getattr(pkg, "approved_at", None) or getattr(pkg, "modified", None)
	if not raw:
		return None
	try:
		return str(getdate(raw))
	except Exception:
		return cstr(raw)[:10] or None


def serialize_eligible_package(pkg: Any, configured: set[str] | None = None) -> dict[str, Any]:
	configured = configured if configured is not None else packages_with_active_configuration()
	ok, reason = package_is_eligible(pkg, configured)
	std = resolve_applicable_std_document(pkg)
	entity_code = cstr(getattr(pkg, "procuring_entity_code", None) or "")
	ref = cstr(getattr(pkg, "package_code", None) or pkg.name)
	title = cstr(getattr(pkg, "package_name", None) or "")
	method = cstr(getattr(pkg, "procurement_method", None) or "")
	return {
		"package_id": pkg.name,
		"planning_package_ref": ref,
		"procurement_title": title,
		"procuring_entity_code": entity_code,
		"procuring_entity_name": resolve_procuring_entity_name(entity_code) or entity_code,
		"procurement_method_label": method,
		"std_family_key": std.get("std_family_key"),
		"std_family_label": std.get("std_family_label"),
		"applicable_std_document_id": std.get("applicable_std_document_id"),
		"applicable_std_document_label": std.get("applicable_std_document_label"),
		"approval_date": _approval_date(pkg),
		"can_create_configuration": bool(ok),
		"ineligibility_reason": None if ok else reason,
	}


def list_eligible_procurement_packages(search: str | None = None, *, limit: int = 100) -> list[dict[str, Any]]:
	configured = packages_with_active_configuration()
	filters: dict[str, Any] = {"status": ("in", list(ELIGIBLE_PACKAGE_STATUSES)), "is_active": 1}
	or_filters = None
	q = cstr(search or "").strip()
	if q:
		or_filters = [
			["package_code", "like", f"%{q}%"],
			["package_name", "like", f"%{q}%"],
		]

	packages = frappe.get_all(
		"Procurement Package",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"package_code",
			"package_name",
			"status",
			"procurement_method",
			"procurement_category",
			"required_std_category",
			"required_std_template_version_code",
			"procuring_entity_code",
			"approved_at",
			"modified",
		],
		order_by="approved_at desc, modified desc",
		limit=limit,
	)

	out: list[dict[str, Any]] = []
	for row in packages:
		if row.name in configured:
			continue
		std = resolve_applicable_std_document(row)
		if not std.get("ok"):
			continue
		out.append(serialize_eligible_package(row, configured))
	return out


def get_package_or_throw(package_id: str):
	package_id = cstr(package_id or "").strip()
	if not package_id or not frappe.db.exists("Procurement Package", package_id):
		frappe.throw(_("Procurement package not found."), title="TCFG_PACKAGE_NOT_FOUND")
	return frappe.get_doc("Procurement Package", package_id)


def ensure_fixture_locked_clauses(package_id: str | None = None) -> None:
	"""Minimal locked ITT/GCC clauses so WG-03 preview can render without Official Library."""
	from kentender_procurement.tender_configurations.constants import FIXTURE_STD_FAMILY_CODE

	package_id = package_id or FIXTURE_STD_VERSION_ID
	samples = (
		(
			"itt",
			"Instructions to Tenderers",
			"The tenderer shall prepare the tender in accordance with the Instructions to Tenderers "
			"and the Tender Data Sheet. Clarifications shall be submitted through the channel "
			"specified in the Tender Data Sheet.",
		),
		(
			"gcc",
			"General Conditions of Contract",
			"The General Conditions of Contract shall apply to the Contract. Special Conditions "
			"of Contract, where provided, shall prevail over these General Conditions to the "
			"extent of any inconsistency.",
		),
	)
	for suffix, title, text in samples:
		section_key = f"{package_id}.section.{suffix}"
		if not frappe.db.exists("STD Section", section_key):
			frappe.get_doc(
				{
					"doctype": "STD Section",
					"package_id": package_id,
					"family_code": FIXTURE_STD_FAMILY_CODE,
					"version_code": package_id,
					"section_key": section_key,
					"object_key": section_key,
					"title": title,
				}
			).insert(ignore_permissions=True)
		clause_key = f"{package_id}.clause.{suffix}.preview_001"
		if not frappe.db.exists("STD Clause", clause_key):
			frappe.get_doc(
				{
					"doctype": "STD Clause",
					"package_id": package_id,
					"family_code": FIXTURE_STD_FAMILY_CODE,
					"version_code": package_id,
					"clause_key": clause_key,
					"section": section_key,
					"object_key": clause_key,
					"title": title,
					"clause_text": text,
				}
			).insert(ignore_permissions=True)
		else:
			# Replace legacy debug/fixture wording so preview never emits fixture markers.
			existing = cstr(frappe.db.get_value("STD Clause", clause_key, "clause_text") or "")
			if "fixture" in existing.lower() or "Fixture locked" in existing:
				frappe.db.set_value(
					"STD Clause",
					clause_key,
					"clause_text",
					text,
					update_modified=False,
				)


def ensure_fixture_std_version() -> str:
	"""Ensure an ACTIVE STD Version exists for IT family (tests/seed)."""
	from kentender_procurement.tender_configurations.constants import (
		FIXTURE_STD_FAMILY_CODE,
		FIXTURE_STD_VERSION_LABEL,
	)

	if frappe.db.exists("STD Version", FIXTURE_STD_VERSION_ID):
		frappe.db.set_value("STD Version", FIXTURE_STD_VERSION_ID, "lifecycle_state", "ACTIVE")
		ensure_fixture_locked_clauses(FIXTURE_STD_VERSION_ID)
		return FIXTURE_STD_VERSION_ID

	if not frappe.db.exists("STD Family", FIXTURE_STD_FAMILY_CODE):
		frappe.get_doc(
			{
				"doctype": "STD Family",
				"family_code": FIXTURE_STD_FAMILY_CODE,
				"family_name": "Kenya PPRA Information Technology STD",
				"authority_code": "PPRA",
				"procurement_category": "IT",
			}
		).insert(ignore_permissions=True)

	doc = frappe.get_doc(
		{
			"doctype": "STD Version",
			"package_id": FIXTURE_STD_VERSION_ID,
			"family_code": FIXTURE_STD_FAMILY_CODE,
			"version_code": FIXTURE_STD_VERSION_ID,
			"version_label": FIXTURE_STD_VERSION_LABEL,
			"lifecycle_state": "ACTIVE",
			"activation_allowed": 1,
			"ui_mode": "ACTIVE_TEMPLATE",
			"is_immutable": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	ensure_fixture_locked_clauses(FIXTURE_STD_VERSION_ID)
	return FIXTURE_STD_VERSION_ID
