# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic UI-00 seed: eligible packages + configurations across statuses."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import nowdate

from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
from kentender_procurement.tender_configurations.constants import (
	STATUS_COMPLETED,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_READY_FOR_REVIEW,
)
from kentender_procurement.tender_configurations.services.eligibility import ensure_fixture_std_version

SEED_PREFIX = "TCFG-SEED"
PACKAGE_REFS = (
	f"{SEED_PREFIX}-PKG-READY-001",
	f"{SEED_PREFIX}-PKG-READY-002",
	f"{SEED_PREFIX}-PKG-CFG-IP",
	f"{SEED_PREFIX}-PKG-CFG-NA",
	f"{SEED_PREFIX}-PKG-CFG-RR",
	f"{SEED_PREFIX}-PKG-CFG-RP",
	f"{SEED_PREFIX}-PKG-CFG-DONE",
)


def _clear_seed() -> None:
	# Configs created via API use TCFG-{package_code}; also clear seed-prefixed refs.
	config_names = set(
		frappe.get_all(
			"Tender Configuration",
			filters={"configuration_ref": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
	)
	config_names |= set(
		frappe.get_all(
			"Tender Configuration",
			filters={"procurement_package": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
	)
	config_names |= set(
		frappe.get_all(
			"Tender Configuration",
			filters={"procurement_package_ref": ("like", f"{SEED_PREFIX}%")},
			pluck="name",
		)
	)
	for name in config_names:
		frappe.delete_doc("Tender Configuration", name, force=True, ignore_permissions=True)

	for code in PACKAGE_REFS:
		if frappe.db.exists("Procurement Package", code):
			frappe.delete_doc("Procurement Package", code, force=True, ignore_permissions=True)


def _ensure_pe() -> str:
	code = f"{SEED_PREFIX}-PE"
	if not frappe.db.exists("Procuring Entity", code):
		# Minimal PE — ignore_mandatory if schema is heavy
		try:
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": code,
					"entity_name": "National Treasury",
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)
		except Exception:
			# Fall back to any existing PE
			existing = frappe.get_all("Procuring Entity", limit=1, pluck="name")
			return existing[0] if existing else code
	return code


def _insert_package(
	*,
	code: str,
	title: str,
	method: str,
	entity: str,
	category: str = "Information Technology",
) -> str:
	if frappe.db.exists("Procurement Package", code):
		frappe.db.set_value(
			"Procurement Package",
			code,
			{
				"package_name": title,
				"status": PKG_APPROVED,
				"procurement_method": method,
				"procuring_entity_code": entity,
				"required_std_category": category,
				"procurement_category": "Goods" if category == "Goods" else "Works" if category == "Works" else "Services",
				"is_active": 1,
				"approved_at": nowdate(),
			},
		)
		return code

	doc = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_code": code,
			"package_name": title,
			"status": PKG_APPROVED,
			"procurement_method": method,
			"contract_type": "Fixed Price",
			"procuring_entity_code": entity,
			"required_std_category": category,
			"procurement_category": "Services",
			"currency": "KES",
			"is_active": 1,
			"approved_at": nowdate(),
			"method_override_flag": 0,
		}
	)
	# Seed fixtures intentionally bypass PP2 profile/plan link gates.
	doc.flags.ignore_validate = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.set_value(
		"Procurement Package",
		doc.name,
		{
			"status": PKG_APPROVED,
			"approved_at": nowdate(),
			"package_code": code,
			"is_active": 1,
		},
	)
	return doc.name


def _insert_config(
	*,
	ref: str,
	package_name: str,
	package_ref: str,
	title: str,
	status: str,
	std_version: str,
	entity_name: str,
	method: str,
	blockers: int = 0,
	warnings: int = 0,
) -> str:
	if frappe.db.exists("Tender Configuration", ref):
		frappe.delete_doc("Tender Configuration", ref, force=True, ignore_permissions=True)
	doc = frappe.get_doc(
		{
			"doctype": "Tender Configuration",
			"configuration_ref": ref,
			"tender_title": title,
			"status": status,
			"procurement_package": package_name,
			"procurement_package_ref": package_ref,
			"package_title": title,
			"procuring_entity_name": entity_name,
			"procuring_entity_code": entity_name,
			"procurement_method": method,
			"std_family_key": "IT",
			"std_family_label": "Information Technology",
			"std_version": std_version,
			"std_document_label": "IT Standard Tender Document — April 2022",
			"blocker_count": blockers,
			"warning_count": warnings,
			"approval_date": nowdate(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def seed_ui00_dashboard(*, clear: bool = True) -> dict[str, Any]:
	"""Load deterministic UI-00 queue data. Idempotent when clear=True."""
	frappe.set_user("Administrator")
	if clear:
		_clear_seed()

	std_id = ensure_fixture_std_version()
	entity = _ensure_pe()
	entity_name = frappe.db.get_value("Procuring Entity", entity, "entity_name") or "National Treasury"

	ready_1 = _insert_package(
		code=PACKAGE_REFS[0],
		title="Data Center Hardware Refresh",
		method="Open Tender",
		entity=entity,
		category="Information Technology",
	)
	ready_2 = _insert_package(
		code=PACKAGE_REFS[1],
		title="County Office Renovation Works",
		method="Open Tender",
		entity=entity,
		category="Works",
	)
	# Works may lack ACTIVE STD — force IT category for eligibility of second ready pkg
	frappe.db.set_value("Procurement Package", ready_2, "required_std_category", "Information Technology")

	cfg_pkgs = []
	for code, title in (
		(PACKAGE_REFS[2], "ERP Implementation Services"),
		(PACKAGE_REFS[3], "Network Upgrade Phase 2"),
		(PACKAGE_REFS[4], "Cloud Hosting Services"),
		(PACKAGE_REFS[5], "Helpdesk Platform"),
		(PACKAGE_REFS[6], "Legacy Archive Digitization"),
	):
		cfg_pkgs.append(
			_insert_package(code=code, title=title, method="Open Tender", entity=entity)
		)

	configs = [
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-IP",
			package_name=cfg_pkgs[0],
			package_ref=PACKAGE_REFS[2],
			title="ERP Implementation Services",
			status=STATUS_IN_PROGRESS,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
			warnings=2,
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-NA",
			package_name=cfg_pkgs[1],
			package_ref=PACKAGE_REFS[3],
			title="Network Upgrade Phase 2",
			status=STATUS_NEEDS_ATTENTION,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
			blockers=2,
			warnings=1,
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-RR",
			package_name=cfg_pkgs[2],
			package_ref=PACKAGE_REFS[4],
			title="Cloud Hosting Services",
			status=STATUS_READY_FOR_REVIEW,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-RP",
			package_name=cfg_pkgs[3],
			package_ref=PACKAGE_REFS[5],
			title="Helpdesk Platform",
			status=STATUS_READY_FOR_PUBLICATION,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
		),
		_insert_config(
			ref=f"{SEED_PREFIX}-TCFG-DONE",
			package_name=cfg_pkgs[4],
			package_ref=PACKAGE_REFS[6],
			title="Legacy Archive Digitization",
			status=STATUS_COMPLETED,
			std_version=std_id,
			entity_name=entity_name,
			method="Open Tender",
		),
	]

	frappe.db.commit()
	return {
		"std_version": std_id,
		"ready_packages": [ready_1, ready_2],
		"configurations": configs,
		"entity": entity,
	}


def clear_ui00_seed() -> None:
	_clear_seed()
	frappe.db.commit()
