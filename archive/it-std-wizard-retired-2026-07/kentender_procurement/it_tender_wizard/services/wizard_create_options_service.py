# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Screen 01 create modal — approved Procurement Package options for IT wizard."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.it_tender_wizard.services.std_core_adapter import (
	get_active_it_std_version_id,
	resolve_std_version,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
)

_AUTHORIZED_PACKAGE_STATUSES = frozenset(
	{
		PKG_APPROVED,
		PKG_READY_FOR_RELEASE,
		PKG_RELEASED,
	}
)

_IT_STD_CATEGORY_MARKERS = frozenset(
	{
		"information technology",
		"it",
	}
)


def _package_business_code(pkg: Document) -> str:
	return cstr(pkg.get("package_code") or pkg.name).strip()


def _resolve_procuring_entity_name(entity_code: str) -> str:
	code = cstr(entity_code or "").strip()
	if not code:
		return ""
	if frappe.db.exists("Procuring Entity", code):
		return cstr(frappe.db.get_value("Procuring Entity", code, "entity_name") or code).strip()
	row = frappe.db.get_value(
		"Procuring Entity",
		{"entity_code": code},
		["entity_name", "name"],
		as_dict=True,
	)
	if row:
		return cstr(row.get("entity_name") or row.get("name") or code).strip()
	return code.replace("PE-", "").replace("-", " ").strip().title()


def _is_it_procurement_package(pkg: Document) -> bool:
	category = cstr(pkg.get("required_std_category") or "").strip().lower()
	if category in _IT_STD_CATEGORY_MARKERS or "technology" in category:
		return True
	code = _package_business_code(pkg).upper()
	return code.startswith("PP-ICT")


def _list_active_it_std_versions() -> list[dict[str, Any]]:
	active = frappe.get_all(
		"STD Version",
		filters={"family_code": "KE-PPRA-IT", "lifecycle_state": "ACTIVE"},
		fields=["name", "version_code", "version_label"],
		order_by="modified desc",
	)
	if active:
		return active

	fallback: list[dict[str, Any]] = []
	for row in frappe.get_all(
		"STD Version",
		filters={"family_code": "KE-PPRA-IT"},
		fields=["name", "version_code", "version_label"],
		order_by="modified desc",
		limit=20,
	):
		try:
			resolve_std_version(row.get("name") or "")
		except Exception:
			continue
		fallback.append(row)
	if fallback:
		return fallback
	return frappe.get_all(
		"STD Version",
		filters={"family_code": "KE-PPRA-IT"},
		fields=["name", "version_code", "version_label"],
		order_by="modified desc",
		limit=5,
	)


def _eligible_std_versions_for_package(pkg: Document) -> list[dict[str, Any]]:
	versions = _list_active_it_std_versions()
	required = cstr(pkg.get("required_std_template_version_code") or "").strip()
	if required:
		matched = [
			row
			for row in versions
			if cstr(row.get("version_code") or "").strip() == required
			or cstr(row.get("name") or "").strip() == required
		]
		if matched:
			return matched
	return versions


def _std_option_label(std_row: dict[str, Any]) -> str:
	label = cstr(std_row.get("version_label") or "").strip()
	code = cstr(std_row.get("version_code") or std_row.get("name") or "").strip()
	return label or code


def _has_in_flight_configuration(planning_package_code: str) -> bool:
	code = cstr(planning_package_code or "").strip()
	if not code:
		return False
	rows = frappe.get_all(
		"Tender STD Instance",
		filters={"planning_package_code": code},
		fields=["name", "wizard_state"],
		limit=20,
	)
	terminal = frozenset({"Approved for Tender Creation", "Bound to Tender"})
	return any((row.get("wizard_state") or "") not in terminal for row in rows)


def _build_create_option(pkg: Document, actor: str) -> dict[str, Any] | None:
	if not _is_it_procurement_package(pkg):
		return None
	if cstr(pkg.get("status") or "").strip() not in _AUTHORIZED_PACKAGE_STATUSES:
		return None
	if not frappe.has_permission("Procurement Package", "read", doc=pkg, user=actor):
		return None

	business_code = _package_business_code(pkg)
	if _has_in_flight_configuration(business_code):
		return None

	eligible_std = _eligible_std_versions_for_package(pkg)
	if not eligible_std:
		return None

	default_std = eligible_std[0]
	std_selectable = len(eligible_std) > 1
	entity_code = cstr(pkg.get("procuring_entity_code") or "").strip()
	method_label = cstr(pkg.get("procurement_method") or "").strip()
	package_name = cstr(pkg.get("package_name") or "").strip()
	label = f"{business_code} — {package_name}" if package_name else business_code

	return {
		"procurement_package_id": pkg.name,
		"procurement_package_label": label,
		"planning_package_ref": business_code,
		"planning_package_name": package_name,
		"procuring_entity_id": entity_code,
		"procuring_entity_name": _resolve_procuring_entity_name(entity_code),
		"procurement_method_code": method_label,
		"procurement_method_label": method_label,
		"standard_tender_document_id": default_std.get("name"),
		"standard_tender_document_label": _std_option_label(default_std),
		"standard_tender_document_selectable": std_selectable,
		"standard_tender_document_options": [
			{
				"id": row.get("name"),
				"label": _std_option_label(row),
			}
			for row in eligible_std
		],
	}


def list_create_options_for_it_wizard(actor: str | None = None) -> list[dict[str, Any]]:
	"""Return approved/released IT procurement packages eligible for wizard create."""
	act = cstr(actor or frappe.session.user or "").strip()
	if not act or not frappe.db.exists("User", act):
		return []

	# Do NOT call frappe.set_user() inside a web request: it rewrites
	# frappe.session.sid to the username, which corrupts the response `sid`
	# cookie and silently logs the real user out on their next request. The
	# permission gate is enforced with an explicit `user=act` check instead,
	# and _build_create_option receives `act` directly.
	if not frappe.has_permission("Procurement Package", "read", user=act):
		return []

	rows = frappe.get_all(
		"Procurement Package",
		filters={"status": ["in", list(_AUTHORIZED_PACKAGE_STATUSES)]},
		fields=["name"],
		order_by="modified desc",
		limit=200,
	)
	options: list[dict[str, Any]] = []
	for row in rows:
		name = cstr(row.get("name") or "").strip()
		if not name or not frappe.db.exists("Procurement Package", name):
			continue
		pkg = frappe.get_doc("Procurement Package", name)
		option = _build_create_option(pkg, act)
		if option:
			options.append(option)
	return options


def resolve_create_option(
	procurement_package_id: str,
	*,
	actor: str | None = None,
) -> dict[str, Any] | None:
	"""Return a single create option when the package is eligible."""
	package_id = cstr(procurement_package_id or "").strip()
	if not package_id:
		return None
	if not frappe.db.exists("Procurement Package", package_id):
		alt = frappe.db.get_value("Procurement Package", {"package_code": package_id}, "name")
		if not alt:
			return None
		package_id = alt
	pkg = frappe.get_doc("Procurement Package", package_id)
	act = cstr(actor or frappe.session.user or "").strip()
	return _build_create_option(pkg, act)


def merge_create_payload_from_package(
	procurement_package_id: str,
	payload: dict[str, Any],
	*,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Derive wizard create payload fields from an approved procurement package."""
	option = resolve_create_option(procurement_package_id, actor=actor)
	if not option:
		frappe.throw("Select a valid approved procurement package.")

	std_id = cstr(payload.get("std_template_version_id") or "").strip()
	if not std_id:
		std_id = cstr(option.get("standard_tender_document_id") or "").strip()
	if not std_id:
		std_id = cstr(get_active_it_std_version_id() or "").strip()
	if not std_id:
		frappe.throw("Standard Tender Document is required.")

	if option.get("standard_tender_document_selectable"):
		allowed = {
			cstr(row.get("id") or "").strip()
			for row in (option.get("standard_tender_document_options") or [])
		}
		if std_id not in allowed:
			frappe.throw("Select a valid Standard Tender Document for this package.")

	resolve_std_version(std_id)
	merged = dict(payload)
	merged.update(
		{
			"procurement_package_id": option["procurement_package_id"],
			"title": cstr(payload.get("title") or option.get("planning_package_name") or "").strip()
			or "New IT Tender Configuration",
			"std_template_version_id": std_id,
			"procuring_entity_id": option.get("procuring_entity_id"),
			"procuring_entity_name": option.get("procuring_entity_name"),
			"procurement_method_code": option.get("procurement_method_code"),
			"procurement_method_name": option.get("procurement_method_label"),
			"planning_package_code": option.get("planning_package_ref"),
			"planning_package_name": option.get("planning_package_name"),
		}
	)
	if payload.get("procurement_plan_item_id") or payload.get("plan_item_id"):
		merged["procurement_plan_item_id"] = cstr(
			payload.get("procurement_plan_item_id") or payload.get("plan_item_id") or ""
		).strip()
	return merged
