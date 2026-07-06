# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Seed fully populated ``package_json.std_config`` for UI / Playwright gates.

Merges mockup-aligned fixture data into the WORKS master STD when the template
is editable (Imported). Idempotent.

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.tender_management.seeds.seed_std_config_ui_fixture.run
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_config_section_schema import (
	ui_fixture_std_config,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

FIXTURE_TEMPLATE_CODE = "STD-CFG-UI-FIXTURE"


def ensure_std_config_ui_fixture_template() -> dict:
	"""Create or refresh a dedicated Imported STD with full std_config for UI gates."""
	code = FIXTURE_TEMPLATE_CODE
	if frappe.db.exists("STD Template", code):
		return seed_std_config_ui_fixture(code)

	fixture = ui_fixture_std_config()
	package = {"std_config": fixture}
	doc = frappe.new_doc("STD Template")
	doc.template_code = code
	doc.template_name = "STD Config UI Fixture"
	doc.template_short_name = "UI-FIXTURE"
	doc.template_title = "Standard Tender Document for Building Works"
	doc.authority = "PPRA"
	doc.country = "KE"
	doc.procurement_category = "WORKS"
	doc.template_family = "Works"
	doc.version_label = "2.1"
	doc.template_version = "2.1"
	doc.package_version = "1"
	doc.source_authority = "PPRA"
	doc.procurement_method_profile = "Open Tender"
	doc.package_json = json.dumps(package, indent=2, ensure_ascii=False)
	doc.package_hash = gov.compute_std_package_hash(package)
	doc.package_hash_algorithm = gov.HASH_ALGORITHM
	doc.canonicalization_version = gov.CANONICALIZATION_VERSION
	doc.lifecycle_status = gov.STATUS_IMPORTED
	doc.latest_validation_status = gov.VALIDATION_NOT_RUN
	doc.critical_finding_count = 0
	doc.warning_finding_count = 0
	doc.info_finding_count = 0
	doc.validation_is_current = 0
	doc.is_governed_version = 1
	doc.tender_usage_count = 0
	doc.locked_due_to_usage = 0
	doc.mutation_blocked = 0
	doc.delete_blocked = 1
	doc.payload_locked = 0
	doc.is_suspended = 0
	doc.is_historical = 0
	doc.approval_override_used = 0
	doc.is_default_active_version = 0
	doc.allowed_for_import = 1
	doc.allowed_for_tender_creation = 0
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ok": True,
		"created": True,
		"template_code": code,
		"sections": list(fixture.keys()),
	}


def seed_std_config_ui_fixture(template_code: str | None = None) -> dict:
	"""Merge UI fixture ``std_config`` sections into an STD Template package."""
	code = template_code or TEMPLATE_CODE
	if not frappe.db.exists("STD Template", code):
		frappe.throw(f"STD Template {code} not found")

	doc = frappe.get_doc("STD Template", code)
	status = (doc.lifecycle_status or "").strip()
	if status == gov.STATUS_ACTIVE:
		return {
			"ok": False,
			"skipped": True,
			"reason": "Active templates cannot receive std_config fixture writes",
			"template_code": code,
		}

	package = json.loads(doc.package_json or "{}")
	if not isinstance(package, dict):
		package = {}
	std_config = package.get("std_config")
	if not isinstance(std_config, dict):
		std_config = {}

	fixture = ui_fixture_std_config()
	for section, payload in fixture.items():
		std_config[section] = payload

	package["std_config"] = std_config
	doc.flags.skip_std_template_guards = True
	doc.package_json = json.dumps(package, indent=2, ensure_ascii=False)
	doc.package_hash = gov.compute_std_package_hash(package)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"ok": True,
		"template_code": code,
		"sections": list(fixture.keys()),
		"package_hash": doc.package_hash,
	}


def run() -> dict:
	ensure = ensure_std_config_ui_fixture_template()
	works = seed_std_config_ui_fixture(TEMPLATE_CODE)
	return {"fixture_template": ensure, "works_master": works}
