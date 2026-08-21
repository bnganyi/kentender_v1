# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI-01 mockup configurations — one fixture per CFG-01…09 focus state + showcase."""

from __future__ import annotations

from typing import Any

import frappe

def _pp2_pkg_available() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))

from frappe.utils import nowdate

PKG_APPROVED = "Approved"  # PP2 Package DocType retired
from kentender_procurement.tender_configurations.constants import (
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	steps_state_focus_cfg,
	steps_state_showcase_nine_cards,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_IN_PROGRESS,
	STEP_NEEDS_ATTENTION,
	STEP_NOT_AVAILABLE,
	STEP_NOT_STARTED,
)
from kentender_procurement.tender_configurations.services.eligibility import ensure_fixture_std_version

MOCK_PREFIX = "TCFG-MOCK"

# Nine mockups: each CFG step is the visual/next-action focus (C1-M3 §6 cards).
# Plus SHOWCASE: all five allowed step statuses visible on one home.
_MOCK_FOCUS: tuple[tuple[str, str, str, int, int], ...] = (
	# step_id, title suffix, focus status, blockers, warnings
	("CFG-01", "Tender Profile focus", STEP_NOT_STARTED, 0, 0),
	("CFG-02", "Tender Data Sheet focus", STEP_NOT_STARTED, 0, 0),
	("CFG-03", "IT Requirements attention", STEP_NEEDS_ATTENTION, 2, 1),
	("CFG-04", "Implementation Schedule progress", STEP_IN_PROGRESS, 0, 1),
	("CFG-05", "System Inventory focus", STEP_NOT_STARTED, 0, 0),
	("CFG-06", "Price Schedule focus", STEP_NOT_STARTED, 0, 0),
	("CFG-07", "Evaluation Setup focus", STEP_NOT_STARTED, 0, 0),
	("CFG-08", "Forms & Evidence focus", STEP_NOT_STARTED, 0, 0),
	("CFG-09", "Contract Values gated", STEP_NOT_AVAILABLE, 0, 0),
)


def _clear_mock() -> None:
	names = set(
		frappe.get_all(
			"Tender Configuration",
			filters={"configuration_ref": ("like", f"{MOCK_PREFIX}%")},
			pluck="name",
		)
	)
	names |= set(
		frappe.get_all(
			"Tender Configuration",
			filters={"procurement_package": ("like", f"{MOCK_PREFIX}%")},
			pluck="name",
		)
	)
	for name in names:
		frappe.delete_doc("Tender Configuration", name, force=True, ignore_permissions=True)
	pkgs = frappe.get_all(
		"Procurement Package",
		filters={"name": ("like", f"{MOCK_PREFIX}%")},
		pluck="name",
	)
	pkgs += frappe.get_all(
		"Procurement Package",
		filters={"package_code": ("like", f"{MOCK_PREFIX}%")},
		pluck="name",
	)
	for code in set(pkgs):
		if (_pp2_pkg_available() and frappe.db.exists("Procurement Package"), code):
			frappe.delete_doc("Procurement Package", code, force=True, ignore_permissions=True)


def _ensure_pe() -> str:
	code = f"{MOCK_PREFIX}-PE"
	if not frappe.db.exists("Procuring Entity", code):
		try:
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": code,
					"entity_name": "National Treasury",
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)
		except Exception:
			existing = frappe.get_all("Procuring Entity", limit=1, pluck="name")
			return existing[0] if existing else code
	return code


def _insert_package(*, code: str, title: str, entity: str) -> str:
	if (_pp2_pkg_available() and frappe.db.exists("Procurement Package"), code):
		frappe.db.set_value(
			"Procurement Package",
			code,
			{
				"package_name": title,
				"status": PKG_APPROVED,
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
			"procurement_method": "Open Tender",
			"contract_type": "Fixed Price",
			"procuring_entity_code": entity,
			"required_std_category": "Information Technology",
			"procurement_category": "Services",
			"currency": "KES",
			"is_active": 1,
			"approved_at": nowdate(),
			"method_override_flag": 0,
		}
	)
	doc.flags.ignore_validate = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.set_value(
		"Procurement Package",
		doc.name,
		{"status": PKG_APPROVED, "approved_at": nowdate(), "package_code": code, "is_active": 1},
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
	blockers: int,
	warnings: int,
	steps_state: dict[str, Any],
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
			"procurement_method": "Open Tender",
			"std_family_key": "IT",
			"std_family_label": "Information Technology",
			"std_version": std_version,
			"std_document_label": "IT Standard Tender Document — April 2022",
			"blocker_count": blockers,
			"warning_count": warnings,
			"steps_state": steps_state,
			"approval_date": nowdate(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def seed_ui01_mockup_configurations(*, clear: bool = True) -> dict[str, Any]:
	"""
	Load UI-01 visual mockups: SHOWCASE (all step statuses) + CFG-01…09 focus configs.

	Does not clear UI-00 `TCFG-SEED-*` rows. Safe to run alongside `seed_ui00_dashboard`.
	"""
	frappe.set_user("Administrator")
	if clear:
		_clear_mock()

	std_id = ensure_fixture_std_version()
	entity = _ensure_pe()
	entity_name = frappe.db.get_value("Procuring Entity", entity, "entity_name") or "National Treasury"

	configs: list[str] = []
	by_step: dict[str, str] = {}

	# Showcase — design-faithful single home (all five §8 statuses across nine cards)
	pkg_show = _insert_package(
		code=f"{MOCK_PREFIX}-PKG-SHOWCASE",
		title="Data Center Hardware Refresh (UI-01 Showcase)",
		entity=entity,
	)
	show_id = _insert_config(
		ref=f"{MOCK_PREFIX}-SHOWCASE",
		package_name=pkg_show,
		package_ref=f"{MOCK_PREFIX}-PKG-SHOWCASE",
		title="Data Center Hardware Refresh (UI-01 Showcase)",
		status=STATUS_NEEDS_ATTENTION,
		std_version=std_id,
		entity_name=entity_name,
		blockers=2,
		warnings=3,
		steps_state=steps_state_showcase_nine_cards(),
	)
	configs.append(show_id)
	by_step["SHOWCASE"] = show_id

	for step_id, title_suffix, focus_status, blockers, warnings in _MOCK_FOCUS:
		n = step_id.split("-")[1]
		pkg_code = f"{MOCK_PREFIX}-PKG-{n}"
		cfg_ref = f"{MOCK_PREFIX}-{step_id}"
		title = f"Mockup {step_id} — {title_suffix}"
		# CFG-09 gated: keep earlier step incomplete so next-action is not the locked card
		if step_id == "CFG-09":
			state = steps_state_focus_cfg("CFG-08", status_label=STEP_NOT_STARTED)
			state["CFG-09"] = {"status_label": STEP_NOT_AVAILABLE}
			status = STATUS_IN_PROGRESS
			blockers, warnings = 0, 0
		else:
			state = steps_state_focus_cfg(step_id, status_label=focus_status)
			status = STATUS_NEEDS_ATTENTION if focus_status == STEP_NEEDS_ATTENTION else STATUS_IN_PROGRESS
		pkg = _insert_package(code=pkg_code, title=title, entity=entity)
		cfg_id = _insert_config(
			ref=cfg_ref,
			package_name=pkg,
			package_ref=pkg_code,
			title=title,
			status=status,
			std_version=std_id,
			entity_name=entity_name,
			blockers=blockers,
			warnings=warnings,
			steps_state=state,
		)
		configs.append(cfg_id)
		by_step[step_id] = cfg_id

	frappe.db.commit()
	return {
		"std_version": std_id,
		"configurations": configs,
		"by_step": by_step,
		"showcase_id": show_id,
		"entity": entity,
	}


def clear_ui01_mockup_seed() -> None:
	_clear_mock()
	frappe.db.commit()
